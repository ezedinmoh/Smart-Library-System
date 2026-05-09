"""
Custom middleware for handling iframe embedding and security headers.

This middleware allows the Django application to be embedded in iframes
from specified domains while maintaining security.
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class IframeEmbeddingMiddleware(MiddlewareMixin):
    """
    Middleware to control iframe embedding through Content-Security-Policy
    and X-Frame-Options headers.
    
    This allows the site to be embedded in iframes from trusted domains
    while blocking embedding from untrusted sources.
    """
    
    def process_response(self, request, response):
        """
        Add or modify security headers to allow iframe embedding from
        specified domains.
        """
        # Get allowed iframe domains from settings
        allowed_iframe_domains = getattr(
            settings, 
            'ALLOWED_IFRAME_DOMAINS', 
            []
        )
        
        # If no domains specified, use default restrictive policy
        if not allowed_iframe_domains:
            # Default: only allow same origin
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response
        
        # Remove X-Frame-Options header (CSP will handle it)
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
        
        # Build Content-Security-Policy frame-ancestors directive
        if '*' in allowed_iframe_domains:
            # Allow embedding from any domain
            frame_ancestors = "frame-ancestors *"
        else:
            # Allow embedding from specific domains
            domains = ' '.join(allowed_iframe_domains)
            frame_ancestors = f"frame-ancestors 'self' {domains}"
        
        # Get existing CSP header if present
        existing_csp = response.get('Content-Security-Policy', '')
        
        if existing_csp:
            # Append to existing CSP
            if 'frame-ancestors' not in existing_csp:
                response['Content-Security-Policy'] = f"{existing_csp}; {frame_ancestors}"
        else:
            # Create new CSP header
            response['Content-Security-Policy'] = frame_ancestors
        
        return response


class CORSIframeMiddleware(MiddlewareMixin):
    """
    Additional middleware to handle CORS headers for iframe embedding.
    
    This ensures that resources can be loaded properly when the site
    is embedded in an iframe on a different domain.
    """
    
    def process_response(self, request, response):
        """
        Add CORS headers to allow cross-origin iframe embedding.
        """
        # Get allowed iframe domains from settings
        allowed_iframe_domains = getattr(
            settings, 
            'ALLOWED_IFRAME_DOMAINS', 
            []
        )
        
        if not allowed_iframe_domains:
            return response
        
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # Check if origin is in allowed domains
        if origin and (
            '*' in allowed_iframe_domains or 
            any(domain in origin for domain in allowed_iframe_domains)
        ):
            # Allow credentials for authenticated requests
            response['Access-Control-Allow-Credentials'] = 'true'
            
            # Set specific origin (required when using credentials)
            if '*' not in allowed_iframe_domains:
                response['Access-Control-Allow-Origin'] = origin
        
        return response
