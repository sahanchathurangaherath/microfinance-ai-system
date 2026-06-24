from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .models import User, UserActivityLog
from .serializers import (
    UserSerializer, CreateUserSerializer,
    UpdateUserSerializer, UserActivityLogSerializer
)
from .permissions import IsAdmin
from apps.audit.utils import log_action, get_client_ip
from apps.audit.models import LoginAttempt, PermissionChangeLog


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            # Log failed attempt to LoginAttempt table
            LoginAttempt.objects.create(
                username_attempted=username,
                ip_address=get_client_ip(request),
                success=False,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                failure_reason="Invalid credentials"
            )
            
            # Log failed attempt to AuditLog if user exists
            if User.objects.filter(username=username).exists():
                user_obj = User.objects.get(username=username)
                UserActivityLog.objects.create(
                    user=user_obj,
                    action='FAILED_LOGIN',
                    ip_address=get_client_ip(request),
                    detail=f"Failed login attempt for username: {username}"
                )

            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "Account is disabled"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Log successful login to LoginAttempt table
        LoginAttempt.objects.create(
            username_attempted=username,
            ip_address=get_client_ip(request),
            success=True,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Log successful login to audit trail
        UserActivityLog.objects.create(
            user=user,
            action='LOGIN',
            ip_address=get_client_ip(request),
            detail="Successful login"
        )
        
        # Log to audit log with structured data
        log_action(
            user=user,
            action_type='LOGIN',
            model_name='User',
            object_id=str(user.id),
            description=f"User {user.username} logged in",
            request=request
        )

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "role_display": user.get_role_display(),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Requires simplejwt blacklist app

            UserActivityLog.objects.create(
                user=request.user,
                action='LOGOUT',
                ip_address=get_client_ip(request),
            )
            
            # Log logout to audit trail
            log_action(
                user=request.user,
                action_type='LOGOUT',
                model_name='User',
                object_id=str(request.user.id),
                description=f"User {request.user.username} logged out",
                request=request
            )

            return Response({"message": "Logged out successfully"})
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateUserSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        old_role = user.role
        
        # Perform the update
        response = super().update(request, *args, **kwargs)
        
        # Log role changes
        if 'role' in request.data and old_role != request.data['role']:
            PermissionChangeLog.objects.create(
                changed_by=request.user,
                target_user=user,
                old_role=old_role,
                new_role=request.data['role'],
                reason=request.data.get('change_reason', '')
            )
            
            # Also log to main audit trail
            log_action(
                user=request.user,
                action_type='PERMISSION_CHANGE',
                model_name='User',
                object_id=str(user.id),
                description=f"Role changed from {old_role} to {request.data['role']} for user {user.username}",
                request=request,
                extra_data={
                    'old_role': old_role,
                    'new_role': request.data['role'],
                    'reason': request.data.get('change_reason', '')
                }
            )
        
        return response

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False  # Soft delete — never hard delete users
        user.save()
        
        # Log user deactivation
        log_action(
            user=request.user,
            action_type='DELETE',
            model_name='User',
            object_id=str(user.id),
            description=f"User {user.username} deactivated",
            request=request
        )
        
        return Response({"message": "User deactivated"}, status=status.HTTP_200_OK)


class RoleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = [
            {"key": key, "label": label}
            for key, label in User.ROLE_CHOICES
        ]
        return Response(roles)


class UserActivityLogView(generics.ListAPIView):
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return UserActivityLog.objects.filter(user_id=user_id)
        return UserActivityLog.objects.all()