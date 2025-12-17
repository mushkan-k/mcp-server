import smtplib
from email.message import EmailMessage
from typing import Optional


class SendMailClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password


    def send_email(self, to: str, subject: str, body: str, html: Optional[str] = None) -> dict:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.user
        msg['To'] = to
        msg.set_content(body)
        if html:
            msg.add_alternative(html, subtype='html')
        with smtplib.SMTP(self.host, self.port, timeout=30) as s:
            s.starttls()
            s.login(self.user, self.password)
            s.send_message(msg)
        return { 'to': to, 'subject': subject }