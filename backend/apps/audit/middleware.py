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

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method in self.MONITORED_METHODS
            and request.path not in self.SKIP_PATHS
            and hasattr(request, 'user')
            and request.user.is_authenticated
            and response.status_code < 400
        ):
            log_action(
                user=request.user,
                action_type='SYSTEM',
                model_name='HTTP',
                object_id='',
                description=f"{request.method} {request.path}",
                request=request,
                extra_data={"status_code": response.status_code},
            )

        return response