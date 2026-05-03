"""
Dual-provider email backend with automatic fallback.

Primary:  Resend  (3,000 emails/month free, HTTP API — no SMTP port issues)
Fallback: Brevo   (300 emails/day free, SMTP port 587 — also works on Render)

How it works:
  1. Every send attempt goes to Resend first.
  2. If Resend raises ANY exception (API error, network issue, rate limit),
     the backend immediately retries via Brevo SMTP.
  3. If Brevo also fails, the original Resend exception is re-raised so
     the caller sees a real error (not a silent swallow).
  4. All fallback events are logged at WARNING level so you can monitor them.

Configuration (set in environment variables / .env):
  RESEND_API_KEY        — from resend.com dashboard
  BREVO_SMTP_USER       — your Brevo login email
  BREVO_SMTP_PASSWORD   — your Brevo SMTP key (not account password)
  DEFAULT_FROM_EMAIL    — e.g. "Smart Library <noreply@yourdomain.com>"

The backend is selected via:
  EMAIL_BACKEND = library_system.email_backends.ResendWithBrevoFallbackBackend
"""

import logging
import threading

from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendWithBrevoFallbackBackend(BaseEmailBackend):
    """
    Tries Resend (HTTP API) first; falls back to Brevo SMTP on any failure.
    Thread-safe — each send_messages() call creates its own backend instances.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._lock = threading.RLock()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_resend_backend(self):
        from django.conf import settings
        from anymail.backends.resend import EmailBackend as ResendBackend
        backend = ResendBackend(fail_silently=False)
        # Inject API key at runtime so we don't need it in ANYMAIL settings
        if not getattr(settings, 'ANYMAIL', {}).get('RESEND_API_KEY'):
            import os
            api_key = os.environ.get('RESEND_API_KEY', '')
            if not hasattr(settings, 'ANYMAIL'):
                settings.ANYMAIL = {}
            settings.ANYMAIL['RESEND_API_KEY'] = api_key
        return backend

    def _get_brevo_backend(self):
        import os
        from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
        user = os.environ.get('BREVO_SMTP_USER', '')
        password = os.environ.get('BREVO_SMTP_PASSWORD', '')
        if not user or not password:
            raise RuntimeError(
                'Brevo fallback not configured — '
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

    # ── main interface ────────────────────────────────────────────────────────

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        with self._lock:
            # ── Attempt 1: Resend ─────────────────────────────────────────
            try:
                backend = self._get_resend_backend()
                backend.open()
                sent = backend.send_messages(email_messages)
                backend.close()
                logger.debug(f'[Email] Resend sent {sent} message(s)')
                return sent
            except Exception as resend_exc:
                logger.warning(
                    f'[Email] Resend failed ({type(resend_exc).__name__}: {resend_exc}), '
                    f'falling back to Brevo…'
                )

            # ── Attempt 2: Brevo SMTP fallback ───────────────────────────
            try:
                backend = self._get_brevo_backend()
                backend.open()
                sent = backend.send_messages(email_messages)
                backend.close()
                logger.info(f'[Email] Brevo fallback sent {sent} message(s)')
                return sent
            except Exception as brevo_exc:
                logger.error(
                    f'[Email] Both providers failed. '
                    f'Brevo error: {type(brevo_exc).__name__}: {brevo_exc}'
                )
                if not self.fail_silently:
                    raise brevo_exc
                return 0
