from .utils import log_action


class AuditMiddleware:
    """
    Optionally logs all POST/PUT/DELETE requests automatically.
    Add to MIDDLEWARE in settings.py for blanket coverage.
    Supplement with specific log_action() calls for business logic.
    """
    MONITORED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    SKIP_PATHS = ['/api/auth/refresh/', '/admin/jsi18n/']

    def __init__(self, get_response):
        self.get_response = get_response

    def get_friendly_description(self, method, path):
        if 'documents' in path:
            return "Uploaded a document"
        elif 'risk-assess' in path:
            return "Triggered AI Risk Assessment"
        elif 'recommend' in path:
            return "Triggered AI Recommendation"
        elif 'submit' in path:
            return "Submitted Loan Application"
        elif 'applications' in path and method == 'POST':
            return "Created Loan Application"
        elif 'applications' in path and method in ['PUT', 'PATCH']:
            return "Updated Loan Application"
        elif 'decision' in path or 'approve' in path or 'reject' in path:
            return "Made an approval decision"
        elif 'users' in path and method == 'POST':
            return "Created a new user account"
        elif 'users' in path and method in ['PUT', 'PATCH']:
            return "Updated User Profile"
        
        parts = [p for p in path.strip('/').split('/') if p and not p.isdigit()]
        resource = parts[-1] if parts else 'resource'
        return f"Modified {resource} data"

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method in self.MONITORED_METHODS
            and request.path not in self.SKIP_PATHS
            and hasattr(request, 'user')
            and request.user.is_authenticated
            and response.status_code < 400
        ):
            desc = self.get_friendly_description(request.method, request.path)
            log_action(
                user=request.user,
                action_type='SYSTEM',
                model_name='HTTP',
                object_id='',
                description=desc,
                request=request,
                extra_data={"status_code": response.status_code, "path": request.path},
            )

        return response