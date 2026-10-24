"""
email.py
Async email sender using Gmail SMTP (TLS on port 587).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from loguru import logger

from app.config import get_settings


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    *,
    reply_to: str | None = None,
) -> bool:
    """Send an email via Gmail SMTP. Returns True on success."""
    settings = get_settings()

    smtp_host = settings.smtp_host.strip()
    smtp_user = settings.smtp_user.strip()
    # Gmail app passwords are often pasted with spaces for readability.
    # Strip them so SMTP auth works whether the value was pasted grouped or raw.
    smtp_password = settings.smtp_password.replace(" ", "").strip()

    if not smtp_host or not smtp_user or not smtp_password:
        logger.warning(f"[EMAIL] SMTP not configured — skipping email to {to}. Subject: {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Cargo Core <{smtp_user}>"
        msg["To"] = to
        if reply_to:
            msg["Reply-To"] = reply_to.strip()
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, msg.as_string())

        logger.info(f"[EMAIL] Sent '{subject}' to {to}")
        return True
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send email to {to}: {e}")
        return False


def support_contact_reply_email_html(
    *,
    customer_name: str,
    reference_code: str,
    original_subject: str,
    reply_message: str,
    support_agent_name: str,
) -> str:
    safe_name = escape(customer_name or "there")
    safe_reference = escape(reference_code)
    safe_subject = escape(original_subject)
    safe_agent_name = escape(support_agent_name)
    safe_reply_message = escape(reply_message).replace("\n", "<br>")

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Support Reply - Cargo Core</title>
    </head>
    <body style="margin:0;padding:0;background:#0F1419;font-family:Arial,sans-serif;">
        <table role="presentation" style="width:100%;border-collapse:collapse;padding:32px 16px;">
            <tr>
                <td align="center">
                    <table role="presentation" style="width:100%;max-width:620px;background:#111827;border-radius:18px;overflow:hidden;">
                        <tr>
                            <td style="padding:32px;background:linear-gradient(135deg,#1E3A8A 0%,#00C4FF 100%);color:#ffffff;text-align:center;">
                                <h1 style="margin:0;font-size:30px;">Cargo Core</h1>
                                <p style="margin:8px 0 0 0;font-size:14px;opacity:0.92;">Support Team Reply</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:36px 32px;color:#E5E7EB;">
                                <p style="margin:0 0 14px 0;font-size:16px;">Hi {safe_name},</p>
                                <p style="margin:0 0 20px 0;font-size:15px;line-height:1.6;">
                                    We reviewed your contact request <strong>{safe_reference}</strong>
                                    regarding <strong>{safe_subject}</strong>.
                                </p>
                                <div style="margin:0 0 22px 0;padding:20px;border:1px solid rgba(0,196,255,0.35);border-radius:14px;background:#0B1220;">
                                    <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#93C5FD;margin-bottom:12px;">Reply from Support</div>
                                    <div style="font-size:15px;line-height:1.7;color:#F9FAFB;">{safe_reply_message}</div>
                                </div>
                                <p style="margin:0 0 10px 0;font-size:14px;line-height:1.6;color:#CBD5E1;">
                                    Regards,<br>
                                    {safe_agent_name}<br>
                                    Cargo Core Support
                                </p>
                                <p style="margin:18px 0 0 0;font-size:12px;line-height:1.6;color:#94A3B8;">
                                    This email was sent in response to your website contact form submission.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def delivery_otp_email_html(otp: str, customer_name: str, tracking_code: str, delivery_address: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Delivery Verification OTP</title>
    </head>
    <body style="margin:0;padding:0;background:#0F1419;font-family:Arial,sans-serif;">
        <table role="presentation" style="width:100%;border-collapse:collapse;padding:32px 16px;">
            <tr>
                <td align="center">
                    <table role="presentation" style="width:100%;max-width:620px;background:#111827;border-radius:18px;overflow:hidden;">
                        <tr>
                            <td style="padding:32px;background:linear-gradient(135deg,#1E3A8A 0%,#00C4FF 100%);color:#ffffff;text-align:center;">
                                <h1 style="margin:0;font-size:30px;">Cargo Core</h1>
                                <p style="margin:8px 0 0 0;font-size:14px;opacity:0.92;">Delivery Verification Required</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:36px 32px;color:#E5E7EB;">
                                <p style="margin:0 0 14px 0;font-size:16px;">Hi {customer_name},</p>
                                <p style="margin:0 0 20px 0;font-size:15px;line-height:1.6;">
                                    Your driver has reached the delivery step for order <strong>{tracking_code}</strong>.
                                    Share this OTP only after you confirm the handover.
                                </p>
                                <div style="margin:0 0 22px 0;padding:20px;border:2px solid #00C4FF;border-radius:14px;background:#0B1220;text-align:center;">
                                    <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#93C5FD;margin-bottom:10px;">Delivery OTP</div>
                                    <div style="font-size:42px;letter-spacing:12px;font-weight:700;color:#00C4FF;font-family:'Courier New',monospace;">{otp}</div>
                                </div>
                                <div style="margin:0 0 20px 0;padding:16px;border-radius:12px;background:#0B1220;">
                                    <p style="margin:0 0 8px 0;font-size:13px;color:#9CA3AF;text-transform:uppercase;">Delivery Address</p>
                                    <p style="margin:0;font-size:14px;line-height:1.5;color:#F9FAFB;">{delivery_address}</p>
                                </div>
                                <p style="margin:0;font-size:13px;line-height:1.6;color:#FCA5A5;">
                                    Security note: never share this code before the delivery is actually received.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def otp_email_html(otp: str, email: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification - Cargo Core</title>
    </head>
    <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #0F1419 0%, #1a1f2e 100%); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 0; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <!-- Main Container -->
                    <table role="presentation" style="width: 100%; max-width: 600px; background: #0F1115; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 196, 255, 0.15); overflow: hidden;">
                        <!-- Header with gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1E3A8A 0%, #00C4FF 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">
                                    ⚡ Cargo Core
                                </h1>
                                <p style="margin: 8px 0 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;">
                                    Logistics Made Simple
                                </p>
                            </td>
                        </tr>

                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 50px 40px;">
                                <h2 style="margin: 0 0 16px 0; color: #ffffff; font-size: 24px; font-weight: 600; text-align: center;">
                                    Verify Your Email Address
                                </h2>
                                <p style="margin: 0 0 32px 0; color: #9CA3AF; font-size: 15px; line-height: 1.6; text-align: center;">
                                    Welcome to Cargo Core! To complete your registration, please use the verification code below.
                                </p>

                                <!-- OTP Box -->
                                <table role="presentation" style="width: 100%; margin: 0 0 32px 0;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #1a1d24 0%, #252932 100%); border: 2px solid #00C4FF; border-radius: 12px; padding: 32px; text-align: center; box-shadow: 0 8px 24px rgba(0, 196, 255, 0.2);">
                                            <p style="margin: 0 0 12px 0; color: #9CA3AF; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">
                                                Your Verification Code
                                            </p>
                                            <div style="background: rgba(0, 196, 255, 0.1); border-radius: 8px; padding: 20px; margin: 0 0 16px 0;">
                                                <h1 style="margin: 0; color: #00C4FF; font-size: 42px; font-weight: 700; letter-spacing: 16px; font-family: 'Courier New', monospace;">
                                                    {otp}
                                                </h1>
                                            </div>
                                            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                                                <span style="display: inline-block; width: 4px; height: 4px; background: #EF4444; border-radius: 50%;"></span>
                                                <p style="margin: 0; color: #EF4444; font-size: 13px; font-weight: 500;">
                                                    Expires in 10 minutes
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Instructions -->
                                <table role="presentation" style="width: 100%; background: rgba(0, 196, 255, 0.05); border-left: 3px solid #00C4FF; border-radius: 8px; padding: 20px; margin: 0 0 32px 0;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 12px 0; color: #ffffff; font-size: 14px; font-weight: 600;">
                                                📋 Next Steps:
                                            </p>
                                            <ol style="margin: 0; padding-left: 20px; color: #9CA3AF; font-size: 14px; line-height: 1.8;">
                                                <li>Return to the registration page</li>
                                                <li>Enter the 6-digit code above</li>
                                                <li>Complete your account setup</li>
                                            </ol>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Security Notice -->
                                <table role="presentation" style="width: 100%; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0; color: #FCA5A5; font-size: 13px; line-height: 1.6;">
                                                🔒 <strong>Security Notice:</strong> If you didn't request this code, please ignore this email. Your account is safe.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background: #0a0c0f; padding: 30px 40px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                                <table role="presentation" style="width: 100%;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0 0 12px 0; color: #6B7280; font-size: 13px; line-height: 1.6;">
                                                This email was sent to <a href="mailto:{email}" style="color: #00C4FF; text-decoration: none;">{email}</a>
                                            </p>
                                            <p style="margin: 0 0 16px 0; color: #6B7280; font-size: 13px;">
                                                © 2026 Cargo Core. All rights reserved.
                                            </p>
                                            <div style="padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.05);">
                                                <p style="margin: 0; color: #4B5563; font-size: 11px; line-height: 1.6;">
                                                    🔐 Secured with 256-bit encryption | 🌍 Trusted by logistics professionals worldwide
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>

                    <!-- Bottom Spacer -->
                    <table role="presentation" style="width: 100%; max-width: 600px; margin-top: 20px;">
                        <tr>
                            <td style="text-align: center;">
                                <p style="margin: 0; color: #4B5563; font-size: 12px;">
                                    Need help? Contact us at <a href="mailto:support@cargocore.com" style="color: #00C4FF; text-decoration: none;">support@cargocore.com</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def password_reset_email_html(otp: str, email: str, name: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset - Cargo Core</title>
    </head>
    <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #0F1419 0%, #1a1f2e 100%); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 0; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <!-- Main Container -->
                    <table role="presentation" style="width: 100%; max-width: 600px; background: #0F1115; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 196, 255, 0.15); overflow: hidden;">
                        <!-- Header with gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1E3A8A 0%, #00C4FF 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">
                                    ⚡ Cargo Core
                                </h1>
                                <p style="margin: 8px 0 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;">
                                    Logistics Made Simple
                                </p>
                            </td>
                        </tr>

                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 50px 40px;">
                                <h2 style="margin: 0 0 16px 0; color: #ffffff; font-size: 24px; font-weight: 600; text-align: center;">
                                    Password Reset Request
                                </h2>
                                <p style="margin: 0 0 12px 0; color: #9CA3AF; font-size: 15px; line-height: 1.6; text-align: center;">
                                    Hi {name},
                                </p>
                                <p style="margin: 0 0 32px 0; color: #9CA3AF; font-size: 15px; line-height: 1.6; text-align: center;">
                                    We received a request to reset your password. Use the verification code below to complete the process.
                                </p>

                                <!-- OTP Box -->
                                <table role="presentation" style="width: 100%; margin: 0 0 32px 0;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #1a1d24 0%, #252932 100%); border: 2px solid #00C4FF; border-radius: 12px; padding: 32px; text-align: center; box-shadow: 0 8px 24px rgba(0, 196, 255, 0.2);">
                                            <p style="margin: 0 0 12px 0; color: #9CA3AF; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">
                                                Your Reset Code
                                            </p>
                                            <div style="background: rgba(0, 196, 255, 0.1); border-radius: 8px; padding: 20px; margin: 0 0 16px 0;">
                                                <h1 style="margin: 0; color: #00C4FF; font-size: 42px; font-weight: 700; letter-spacing: 16px; font-family: 'Courier New', monospace;">
                                                    {otp}
                                                </h1>
                                            </div>
                                            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                                                <span style="display: inline-block; width: 4px; height: 4px; background: #EF4444; border-radius: 50%;"></span>
                                                <p style="margin: 0; color: #EF4444; font-size: 13px; font-weight: 500;">
                                                    Expires in 10 minutes
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Instructions -->
                                <table role="presentation" style="width: 100%; background: rgba(0, 196, 255, 0.05); border-left: 3px solid #00C4FF; border-radius: 8px; padding: 20px; margin: 0 0 32px 0;">
                                    <tr>
                                        <td>
                                            <p style="margin: 0 0 12px 0; color: #ffffff; font-size: 14px; font-weight: 600;">
                                                📋 Next Steps:
                                            </p>
                                            <ol style="margin: 0; padding-left: 20px; color: #9CA3AF; font-size: 14px; line-height: 1.8;">
                                                <li>Return to the password reset page</li>
                                                <li>Enter the 6-digit code above</li>
                                                <li>Create your new password</li>
                                            </ol>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Security Notice -->
                                <table role="presentation" style="width: 100%; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0; color: #FCA5A5; font-size: 13px; line-height: 1.6;">
                                                🔒 <strong>Security Notice:</strong> If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background: #0a0c0f; padding: 30px 40px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                                <table role="presentation" style="width: 100%;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0 0 12px 0; color: #6B7280; font-size: 13px; line-height: 1.6;">
                                                This email was sent to <a href="mailto:{email}" style="color: #00C4FF; text-decoration: none;">{email}</a>
                                            </p>
                                            <p style="margin: 0 0 16px 0; color: #6B7280; font-size: 13px;">
                                                © 2026 Cargo Core. All rights reserved.
                                            </p>
                                            <div style="padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.05);">
                                                <p style="margin: 0; color: #4B5563; font-size: 11px; line-height: 1.6;">
                                                    🔐 Secured with 256-bit encryption | 🌍 Trusted by logistics professionals worldwide
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>

                    <!-- Bottom Spacer -->
                    <table role="presentation" style="width: 100%; max-width: 600px; margin-top: 20px;">
                        <tr>
                            <td style="text-align: center;">
                                <p style="margin: 0; color: #4B5563; font-size: 12px;">
                                    Need help? Contact us at <a href="mailto:support@cargocore.com" style="color: #00C4FF; text-decoration: none;">support@cargocore.com</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
