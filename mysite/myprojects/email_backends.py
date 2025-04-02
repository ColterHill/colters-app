# myapp/email_backends.py

import smtplib
import ssl
import certifi
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend

class CustomEmailBackend(DjangoEmailBackend):
    def open(self):
        """
        Open a network connection and authenticate if necessary.
        """
        if self.connection:
            return False
        connection = None
        try:
            connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            # Use the debug attribute if available; default to 0 if not set.
            debug_level = getattr(self, 'debug', 0)
            connection.set_debuglevel(debug_level)
            connection.ehlo()
            if self.use_tls:
                # Create an SSL context that uses certifi's CA bundle
                context = ssl.create_default_context(cafile=certifi.where())
                connection.starttls(context=context)
                connection.ehlo()
            if self.username and self.password:
                connection.login(self.username, self.password)
            self.connection = connection
            return True
        except Exception:
            if connection:
                connection.close()
            if not self.fail_silently:
                raise
        return False
