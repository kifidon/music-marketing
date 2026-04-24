"""
When ``settings.CSRF_TRUST_ALL_ORIGINS`` is True (env ``DJANGO_CSRF_TRUSTED_ORIGINS=*``),
skip strict Origin / Referer checks. Insecure — use only temporarily.
"""

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class RelaxedCsrfViewMiddleware(CsrfViewMiddleware):
    def _origin_verified(self, request):
        if getattr(settings, "CSRF_TRUST_ALL_ORIGINS", False):
            return True
        return super()._origin_verified(request)

    def _check_referer(self, request):
        if getattr(settings, "CSRF_TRUST_ALL_ORIGINS", False):
            return
        return super()._check_referer(request)
