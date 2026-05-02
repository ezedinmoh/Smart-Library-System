"""Custom console email backend that prints emails in a readable format for development"""
import sys
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    """
    Email backend that prints emails to console in a readable format
    without encoding, making it easy to copy verification links during development.
    Only shows the plain text version, not the HTML.
    """
    
    def write_message(self, message):
        """Write the email message to the console in a readable format"""
        msg = message.message()
        
        # Print separator
        self.stream.write('\n' + '='*100 + '\n')
        self.stream.write('EMAIL SENT (Plain Text Only - HTML version hidden)\n')
        self.stream.write('='*100 + '\n')
        
        # Print headers
        self.stream.write(f'From: {msg.get("From", "")}\n')
        self.stream.write(f'To: {msg.get("To", "")}\n')
        self.stream.write(f'Subject: {msg.get("Subject", "")}\n')
        self.stream.write('-'*100 + '\n\n')
        
        # Extract and display ONLY the plain text body from multipart message
        plain_text_found = False
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    # Get the plain text content
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            text = payload.decode('utf-8')
                            self.stream.write(text)
                            self.stream.write('\n')
                            plain_text_found = True
                        except Exception as e:
                            self.stream.write(f'Error decoding plain text: {e}\n')
                    break  # Stop after finding plain text
        else:
            # Single part message
            if message.body:
                self.stream.write(message.body)
                self.stream.write('\n')
                plain_text_found = True
        
        if not plain_text_found:
            self.stream.write('[No plain text content found]\n')
        
        # Print separator
        self.stream.write('='*100 + '\n\n')
        self.stream.flush()
