"""
Dual-provider email backend with automatic fallback.

Primary:  Brevo SMTP  (300 emails/day free, port 587 — works on Render now,
                       sends from smartlibrarysupport@gmail.com to ALL users)
Fallback: Resend      (3,000 emails/month free, HTTP API — becomes primary
                       once a custom domain is verified on resend.com)

How it works:
  1. Every send attempt goes to Brevo SMTP first.
  2. If Brevo fails for any reason, automatically retries via Resend API.
  3. If both fail, the error is logged and re-raised.
  4. All fallback events are logged at WARNING level.

Configuration (set in Render environment variables):
  BREVO_SMTP_USER       — your Brevo login (aa0f2d001@smtp-brevo.com)
  BREVO_SMTP_PASSWORD   — your Brevo SMTP key
  RESEND_API_KEY        — from resend.com dashboard (fallback)
  DEFAULT_FROM_EMAIL    — Smart Library <smartlibrarysupport@gmail.com>

The backend is selected via:
  EMAIL_BACKEND = library_system.email_backends.BrevoWithResendFallbackBackend
"""

import logging
import threading

from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class BrevoWithResendFallbackBackend(BaseEmailBackend):
    """
    Tries Brevo SMTP first (sends to ALL users from your Gmail address).
    Falls back to Resend API if Brevo fails.
    Thread-safe.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._lock = threading.RLock()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_brevo_backend(self):
        import os
        from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
        user = os.environ.get('BREVO_SMTP_USER', '')
        password = os.environ.get('BREVO_SMTP_PASSWORD', '')
        if not user or not password:
            raise RuntimeError(
                'Brevo not configured — '
                'set BREVO_SMTP_USER and BREVO_SMTP_PASSWORD env vars.'
            )
        return SmtpBackend(
            host='smtp-relay.brevo.com',
            port=587,
            username=user,
            password=password,
            use_tls=True,
            use_ssl=False,
            fail_silently=False,
        )

    def _get_resend_backend(self):
        import os
        from django.conf import settings
        from anymail.backends.resend import EmailBackend as ResendBackend
        # Inject API key at runtime
        api_key = os.environ.get('RESEND_API_KEY', '')
        if not api_key:
            raise RuntimeError(
                'Resend not configured — set RESEND_API_KEY env var.'
            )
        if not hasattr(settings, 'ANYMAIL'):
            settings.ANYMAIL = {}
        settings.ANYMAIL['RESEND_API_KEY'] = api_key
        return ResendBackend(fail_silently=False)

    # ── main interface ────────────────────────────────────────────────────────

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        with self._lock:
            # ── Attempt 1: Brevo SMTP (primary) ──────────────────────────
            try:
                backend = self._get_brevo_backend()
                backend.open()
                sent = backend.send_messages(email_messages)
                backend.close()
                logger.info(f'[Email] Brevo sent {sent} message(s)')
                return sent
            except Exception as brevo_exc:
                logger.warning(
                    f'[Email] Brevo failed ({type(brevo_exc).__name__}: {brevo_exc}), '
                    f'falling back to Resend…'
                )

            # ── Attempt 2: Resend API (fallback) ─────────────────────────
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
