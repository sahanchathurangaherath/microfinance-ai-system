from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
import httpx
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .models import NotificationQueue, NotificationLog, NotificationTemplate
from .serializers import NotificationQueueSerializer, NotificationLogSerializer
from apps.users.permissions import IsLoanOfficer, IsCollectionsOfficer


class DraftNotificationView(APIView):
    """
    Calls A6 to draft a message. Creates a NotificationQueue entry for officer review.
    Does NOT send anything.
    """
    permission_classes = [IsLoanOfficer]

    def post(self, request):
        comm_type = request.data.get("comm_type")
        context = request.data.get("context", {})
        channels = request.data.get("channels", ["SMS", "EMAIL"])
        client_id = request.data.get("client_id")
        reference_type = request.data.get("reference_type", "")
        reference_id = request.data.get("reference_id")

        if client_id:
            try:
                from apps.clients.models import Client
                client_obj = Client.objects.get(pk=client_id)
                context["preferred_language"] = client_obj.preferred_language
                
                # BUG-BE-13: Break unsafe method chain into guarded steps
                missed_payments_count = 0
                active_loan = client_obj.loans.filter(status='ACTIVE').prefetch_related('schedule__installments').first()
                if active_loan is not None and hasattr(active_loan, 'schedule'):
                    schedule = active_loan.schedule
                    if schedule is not None:
                        missed_payments_count = schedule.installments.filter(
                            status__in=['OVERDUE', 'PARTIAL']
                        ).count()
                context["missed_payments_count"] = missed_payments_count
            except Exception:
                pass

        # Call A6
        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/api/a6/draft-message",
                json={"comm_type": comm_type, "context": context, "channels": channels},
                headers={"x-api-key": settings.AI_SERVICE_API_KEY},
                timeout=10.0
            )
            ai_result = response.json()
        except Exception as e:
            return Response(
                {"error": f"AI service unavailable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        output = ai_result.get("output", {})
        drafts = output.get("drafts", [])
        created_ids = []

        for draft in drafts:
            channel = draft.get("channel")
            notif = NotificationQueue.objects.create(
                client_id=client_id,
                recipient_phone=context.get("client_phone", ""),
                recipient_email=context.get("client_email", ""),
                channel=channel,
                comm_type=comm_type,
                subject=draft.get("subject", ""),
                body=draft.get("body", ""),
                ai_drafted=True,
                ai_rationale=ai_result.get("rationale", ""),
                status='PENDING_APPROVAL',
                reference_type=reference_type,
                reference_id=reference_id,
            )
            created_ids.append(notif.id)

        return Response({
            "message": f"{len(created_ids)} draft(s) created. Pending officer approval.",
            "notification_ids": created_ids,
            "drafts": drafts
        }, status=status.HTTP_201_CREATED)


class PendingApprovalView(generics.ListAPIView):
    """Officer sees all notifications pending their approval."""
    serializer_class = NotificationQueueSerializer
    permission_classes = [IsLoanOfficer]

    def get_queryset(self):
        return NotificationQueue.objects.filter(status='PENDING_APPROVAL')


class ApproveNotificationView(APIView):
    """Officer approves a draft message — marks it ready to send."""
    permission_classes = [IsLoanOfficer]

    def post(self, request, notif_id):
        try:
            notif = NotificationQueue.objects.get(pk=notif_id)
        except NotificationQueue.DoesNotExist:
            return Response({"error": "Notification not found."}, status=404)

        if notif.status != 'PENDING_APPROVAL':
            return Response(
                {"error": f"Cannot approve a notification with status '{notif.status}'."},
                status=400
            )

        notif.status = 'APPROVED'
        notif.approved_by = request.user
        notif.approved_at = timezone.now()
        notif.save()

        return Response({
            "message": "Notification approved. Use /send/ to dispatch.",
            "notification_id": notif.id
        })


class RejectNotificationView(APIView):
    """Officer rejects a draft message with a reason."""
    permission_classes = [IsLoanOfficer]

    def post(self, request, notif_id):
        try:
            notif = NotificationQueue.objects.get(pk=notif_id)
        except NotificationQueue.DoesNotExist:
            return Response({"error": "Notification not found."}, status=404)

        reason = request.data.get("reason", "")
        notif.status = 'REJECTED'
        notif.rejection_reason = reason
        notif.save()

        return Response({"message": "Notification rejected.", "reason": reason})


class SendNotificationView(APIView):
    """
    Sends an APPROVED notification via SMS or Email.
  
    """
    permission_classes = [IsLoanOfficer]

    def post(self, request, notif_id):
        try:
            notif = NotificationQueue.objects.get(pk=notif_id)
        except NotificationQueue.DoesNotExist:
            return Response({"error": "Notification not found."}, status=404)

        if notif.status != 'APPROVED':
            return Response(
                {"error": "Only APPROVED notifications can be sent."},
                status=400
            )

        delivered = False
        error_message = ""
        provider_ref = ""

        try:
            if notif.channel == 'SMS':
                delivered, provider_ref, error_message = self._send_sms(notif)
            elif notif.channel == 'EMAIL':
                delivered, provider_ref, error_message = self._send_email(notif)
        except Exception as e:
            error_message = str(e)

        notif.status = 'SENT' if delivered else 'FAILED'
        notif.sent_at = timezone.now() if delivered else None
        notif.save()

        NotificationLog.objects.create(
            notification=notif,
            delivered=delivered,
            delivery_timestamp=notif.sent_at,
            error_message=error_message,
            provider_reference=provider_ref
        )

        return Response({
            "delivered": delivered,
            "channel": notif.channel,
            "status": notif.status,
            "error": error_message or None
        })

    def _send_sms(self, notif):
        """
        SMS via Twilio. Replace with your credentials.
        Install: pip install twilio
        """
        try:
            from twilio.rest import Client as TwilioClient
            twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            message = twilio_client.messages.create(
                body=notif.body,
                from_=settings.TWILIO_FROM_NUMBER,
                to=notif.recipient_phone
            )
            return True, message.sid, ""
        except Exception as e:
            return False, "", str(e)

    def _send_email(self, notif):
        """Email via Gmail SMTP."""
        try:
            smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            smtp_port = getattr(settings, 'EMAIL_PORT', 587)
            smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
            smtp_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', '')

            msg = MIMEMultipart('alternative')
            msg['Subject'] = notif.subject
            msg['From'] = smtp_user
            msg['To'] = notif.recipient_email

            msg.attach(MIMEText(notif.body, 'plain'))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, notif.recipient_email, msg.as_string())

            return True, f"email-{notif.id}", ""
        except Exception as e:
            return False, "", str(e)


class NotificationLogListView(generics.ListAPIView):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsLoanOfficer]

    def get_queryset(self):
        return NotificationLog.objects.all().select_related('notification')
