import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

async def send_status_change_email(user: User, station_name: str, old_status: str, new_status: str):
    """
    Sends an email notification to a user about a station status change.
    Uses aiosmtplib directly for flexibility and better logging.
    Handles both local MailHog and production SMTP servers.
    """
    # 1. Check if the essential SMTP settings are present.
    if not all([settings.smtp_server, settings.smtp_port]):
        logger.warning("SMTP server or port not configured. Email sending is skipped.")
        return

    from_email = settings.smtp_username or "noreply@ev-charging-app.com"
    to_email = user.email

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Station Status Update: {station_name}"
    message["From"] = from_email
    message["To"] = to_email

    # Simple HTML template for the email
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px; }}
            .header {{ font-size: 24px; font-weight: bold; color: #0056b3; }}
            .content {{ margin-top: 20px; font-size: 16px; line-height: 1.6; }}
            .status-change {{ padding: 10px; border-left: 4px solid #0056b3; background-color: #f0f8ff; margin: 20px 0; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                EV Station Status Update
            </div>
            <div class="content">
                <p>Hello {user.first_name},</p>
                <p>This is a notification regarding a station you are monitoring:</p>
                <div class="status-change">
                    <strong>Station:</strong> {station_name}<br>
                    <strong>Status changed from:</strong> {old_status.title()} <br>
                    <strong>New Status:</strong> {new_status.title()}
                </div>
                <p>You can check the latest details in the app.</p>
            </div>
            <div class="footer">
                <p>You are receiving this email because you subscribed to notifications for this station.</p>
                <p>&copy; 2024 EV Charging Stations App</p>
            </div>
        </div>
    </body>
    </html>
    """
    message.attach(MIMEText(html_body, "html"))

    # Determine if we should use TLS. MailHog doesn't use it.
    # A simple check for 'localhost' is a good indicator for local testing.
    use_tls = settings.smtp_server != "localhost"

    try:
        logger.info(f"Connecting to SMTP server: {settings.smtp_server}:{settings.smtp_port} (TLS: {use_tls})")
        async with aiosmtplib.SMTP(
            hostname=settings.smtp_server,
            port=settings.smtp_port,
            use_tls=use_tls
        ) as smtp:
            logger.info("Connection successful.")
            
            # Only login if a username is provided
            if settings.smtp_username:
                logger.info(f"Attempting to login as '{settings.smtp_username}'...")
                await smtp.login(settings.smtp_username, settings.smtp_password)
                logger.info("Login successful.")

            logger.info(f"Sending email to {to_email}...")
            await smtp.send_message(message)
            logger.info(f"Successfully sent email to {to_email}")

    except aiosmtplib.SMTPException as e:
        logger.error(f"An SMTP error occurred: {e.code} - {e.message}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}")

# No singleton instance needed, the function is imported directly. 