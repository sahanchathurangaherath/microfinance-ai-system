import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.kyc.models import KYCDocument
qs = KYCDocument.objects.order_by('-uploaded_at')[:20]
for d in qs:
    print(d.id, d.client_id, d.document_type, d.file.name, d.status, d.uploaded_at)
