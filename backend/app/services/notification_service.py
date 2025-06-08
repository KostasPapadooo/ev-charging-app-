import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings
from app.models.user import User
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

logger = logging.getLogger(__name__)

async def send_email(subject: str, recipient_email: str, body: str):
    """
    Sends an email using the configured SMTP settings.
    It automatically disables TLS for local development with MailHog.
    """
    # Only check for server and port, as username/password can be empty for MailHog
    if not settings.smtp_server or not settings.smtp_port:
        logger.warning("SMTP server or port not configured. Skipping email notification.")
        return

    # Dynamically adjust TLS settings for MailHog
    use_tls = True
    if settings.smtp_server.lower() == 'mailhog':
        use_tls = False
        logger.info("MailHog detected, disabling TLS for SMTP connection.")

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.smtp_username,
        MAIL_PASSWORD=settings.smtp_password,
        MAIL_FROM=settings.smtp_from_email or settings.smtp_username,
        MAIL_PORT=settings.smtp_port,
        MAIL_SERVER=settings.smtp_server,
        MAIL_STARTTLS=use_tls,
        MAIL_SSL_TLS=False,  # Usually False when STARTTLS is used
        USE_CREDENTIALS=True if use_tls else False,
        VALIDATE_CERTS=True if use_tls else False
    )

    message = MessageSchema(
        subject=subject,
        recipients=[recipient_email],
        body=body,
        subtype="html"
    )

    try:
        logger.info(f"Connecting to SMTP server: {settings.smtp_server}:{settings.smtp_port} (TLS: {use_tls})")
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Email notification successfully sent to {recipient_email}")
        
    except Exception as e:
        # The original exception might be wrapped, so we log the full error
        logger.error(f"Failed to send email to {recipient_email}: {e}", exc_info=True)

async def send_status_change_email(user: User, station_name: str, old_status: str, new_status: str):
    """
    Constructs and sends an email to a user about a favorite station's status change.
    """
    subject = f"🔔 Status Change for Favorite Station: {station_name}"
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
            .header {{ font-size: 24px; color: #444; margin-bottom: 20px; text-align: center; }}
            .content {{ font-size: 16px; }}
            .status-change {{ margin: 20px 0; padding: 15px; border-left: 5px solid; }}
            .status-old {{ border-color: #dc3545; }} /* Red for old status */
            .status-new {{ border-color: #28a745; }} /* Green for new status */
            .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Station Status Update</div>
            <div class="content">
                <p>Hello {user.first_name},</p>
                <p>There has been a status change for one of your favorite charging stations, <strong>{station_name}</strong>.</p>
                
                <div class="status-change status-old">
                    <strong>Previous Status:</strong> {old_status}
                </div>
                
                <div class="status-change status-new">
                    <strong>New Status:</strong> {new_status}
                </div>
                
                <p>You can view the station and plan your trip accordingly via our app.</p>
                <p>Thank you for using our service!</p>
            </div>
            <div class="footer">
                <p>This is an automated notification. You are receiving this because you marked this station as a favorite.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    await send_email(subject, user.email, body)

# No singleton instance needed, the function is imported directly. 