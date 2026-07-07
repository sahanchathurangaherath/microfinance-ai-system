from django.urls import path
from .views import UserListCreateView, UserDetailView, RoleListView, UserActivityLogView

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user_list_create'),
    path('<int:pk>', UserDetailView.as_view(), name='user_detail'),
    path('roles', RoleListView.as_view(), name='role_list'),
    path('<int:user_id>/activity', UserActivityLogView.as_view(), name='user_activity'),
]