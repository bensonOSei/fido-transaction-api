from typing import Dict, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic import BaseModel, EmailStr
import logging
from datetime import datetime

class EmailConfig(BaseModel):
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-specific-password"
    FROM_EMAIL: str = "noreply@yourdomain.com"
    ENABLE_NOTIFICATIONS: bool = True

class TransactionEmailContext(BaseModel):
    user_id: str
    full_name: str
    transaction_amount: float
    transaction_type: str
    transaction_date: datetime
    transaction_id: str

class EmailNotificationService:
    def __init__(self, config: EmailConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Jinja2 environment for email templates
        self.jinja_env = Environment(
            loader=PackageLoader('app', 'templates/email'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send email using aiosmtplib"""
        if not self.config.ENABLE_NOTIFICATIONS:
            self.logger.info("Email notifications are disabled")
            return False

        message = MIMEMultipart("alternative")
        message["From"] = self.config.FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        
        message.attach(MIMEText(html_content, "html"))

        try:
            async with aiosmtplib.SMTP(
                hostname=self.config.SMTP_HOST,
                port=self.config.SMTP_PORT,
                use_tls=True
            ) as smtp:
                await smtp.login(
                    self.config.SMTP_USER,
                    self.config.SMTP_PASSWORD
                )
                await smtp.send_message(message)
                
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False

    async def send_transaction_notification(
        self,
        to_email: str,
        context: TransactionEmailContext
    ) -> bool:
        """Send transaction notification email"""
        template = self.jinja_env.get_template("transaction_notification.html")
        
        # Format amount for display
        formatted_amount = "{:,.2f}".format(abs(context.transaction_amount))
        
        html_content = template.render(
            full_name=context.full_name,
            transaction_type=context.transaction_type.title(),
            amount=formatted_amount,
            transaction_date=context.transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
            transaction_id=context.transaction_id,
            current_year=datetime.now().year
        )
        
        subject = f"Transaction Notification: {context.transaction_type.title()} - ${formatted_amount}"
        
        return await self._send_email(to_email, subject, html_content)