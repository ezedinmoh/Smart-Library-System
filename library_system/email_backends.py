"""
Dual-provider email backend with automatic fallback.

Primary:  Brevo API   (HTTP API over port 443 — works on Render free tier,
                       sends from smartlibrarysupport@gmail.com to ALL users,
                       300 emails/day free)
Fallback: Resend API  (HTTP API over port 443 — 3,000 emails/month free,
                       becomes primary once a custom domain is verified)

Both use HTTP APIs — no SMTP ports (25/465/587) needed at all.
Render free tier blocks all SMTP ports but never blocks HTTPS.

Configuration (set in Render environment variables):
  BREVO_API_KEY      — from brevo.com -> SMTP & API -> API Keys tab
  RESEND_API_KEY     — from resend.com dashboard (optional fallback)
  DEFAULT_FROM_EMAIL — Smart Library <smartlibrarysupport@gmail.com>

The backend is selected via:
  EMAIL_BACKEND = library_system.email_backends.BrevoWithResendFallbackBackend
"""

import logging
import threading

from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class BrevoWithResendFallbackBackend(BaseEmailBackend):
    """
    Tries Brevo HTTP API first (works on Render free tier — no SMTP ports).
    Falls back to Resend HTTP API if Brevo fails.
    Thread-safe.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._lock = threading.RLock()

    def _get_brevo_backend(self):
        import os
        from django.conf import settings
        from anymail.backends.brevo import EmailBackend as BrevoBackend

        api_key = os.environ.get('BREVO_API_KEY', '')
        if not api_key:
            raise RuntimeError(
                'Brevo not configured — set BREVO_API_KEY env var '
                '(from brevo.com -> SMTP & API -> API Keys tab).'
            )
        if not hasattr(settings, 'ANYMAIL'):
            settings.ANYMAIL = {}
        settings.ANYMAIL['BREVO_API_KEY'] = api_key
        return BrevoBackend(fail_silently=False)

    def _get_resend_backend(self):
        import os
        from django.conf import settings
        from anymail.backends.resend import EmailBackend as ResendBackend

        api_key = os.environ.get('RESEND_API_KEY', '')
        if not api_key:
            raise RuntimeError(
                'Resend not configured — set RESEND_API_KEY env var.'
            )
        if not hasattr(settings, 'ANYMAIL'):
            settings.ANYMAIL = {}
        settings.ANYMAIL['RESEND_API_KEY'] = api_key
        return ResendBackend(fail_silently=False)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        with self._lock:
            # Attempt 1: Brevo HTTP API (primary)
            try:
                backend = self._get_brevo_backend()
                backend.open()
                sent = backend.send_messages(email_messages)
                backend.close()
                logger.info(f'[Email] Brevo API sent {sent} message(s)')
                return sent
            except Exception as brevo_exc:
                logger.warning(
                    f'[Email] Brevo API failed ({type(brevo_exc).__name__}: {brevo_exc}), '
                    f'falling back to Resend...'
                )

            # Attempt 2: Resend HTTP API (fallback)
            try:
                backend = self._get_resend_backend()
                backend.open()
                sent = backend.send_messages(email_messages)
                backend.close()
                logger.info(f'[Email] Resend fallback sent {sent} message(s)')
                return sent
            except Exception as resend_exc:
                logger.error(
                    f'[Email] Both providers failed. '
                    f'Resend error: {type(resend_exc).__name__}: {resend_exc}'
                )
                if not self.fail_silently:
                    raise resend_exc
                return 0
