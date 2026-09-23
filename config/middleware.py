class SecurityHeadersMiddleware:
    """Set safe default HTTP security headers on every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('X-Frame-Options', 'DENY')
        response.setdefault('Referrer-Policy', 'same-origin')
        response.setdefault('X-XSS-Protection', '0')
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        return response
