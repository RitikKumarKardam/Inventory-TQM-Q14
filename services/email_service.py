"""Genuine Email & OTP Dispatch Service for My Inventory Management System.

Supports genuine SMTP dispatch via Gmail, Outlook, Brevo, SendGrid, or custom SMTP servers.
Enforces SSL/TLS security and HTML email formatting.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Optional
from database.db import get_conn
from utils.logger import log_audit, log_error


def get_config_value(key: str, default: str = "") -> str:
    """Retrieve configuration from environment variable, falling back to database."""
    val = os.getenv(key)
    if val:
        return val.strip()
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)")
        row = cur.execute("SELECT value FROM system_config WHERE key = ?", (key,)).fetchone()
        conn.close()
        if row and row[0]:
            return str(row[0]).strip()
    except Exception:
        pass
    return default


def set_config_value(key: str, value: str) -> None:
    """Save configuration to system_config table and os.environ."""
    os.environ[key] = value.strip()
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS system_config (key TEXT PRIMARY KEY, value TEXT)")
        cur.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", (key, value.strip()))
        conn.commit()
        conn.close()
    except Exception as e:
        log_error(f"Error saving config key {key}: {e}")


class EmailService:
    @staticmethod
    def get_smtp_settings() -> dict:
        host = get_config_value("SMTP_HOST", "smtp.gmail.com")
        port = int(get_config_value("SMTP_PORT", "587"))
        user = get_config_value("SMTP_USER", "")
        password = get_config_value("SMTP_PASSWORD", "")
        from_email = get_config_value("SMTP_FROM", user or "noreply@amrapali.ac.in")
        return {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "from_email": from_email,
            "is_configured": bool(user and password),
        }

    @staticmethod
    def send_otp_email(recipient_email: str, otp_code: str, user_name: str = "User") -> Tuple[bool, str]:
        """Send a genuine 6-digit OTP verification code via authenticated SMTP."""
        settings = EmailService.get_smtp_settings()
        
        if not settings["is_configured"]:
            return (
                False,
                "SMTP Email Server is not yet configured. Please configure your SMTP User and App Password in Mailer Settings to dispatch live emails to inboxes.",
            )

        host = settings["host"]
        port = settings["port"]
        user = settings["user"]
        password = settings["password"]
        from_email = settings["from_email"]

        # Build genuine MIME multipart message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Security Verification OTP: {otp_code} - My Inventory System"
        msg["From"] = f"My Inventory System <{from_email}>"
        msg["To"] = recipient_email

        text_content = f"""Hello {user_name},

Your security verification code for My Inventory System is:

    {otp_code}

This OTP is valid for 10 minutes. Enter this code to verify and link your email address.
If you did not request this verification, please ignore this email.

Total Quality Inventory Management System
Amrapali University, Haldwani
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 24px; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
    .header {{ background: #0b3d91; padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }}
    .header p {{ margin: 6px 0 0 0; font-size: 13px; color: #bae6fd; }}
    .body {{ padding: 32px 28px; color: #1e293b; line-height: 1.6; font-size: 14.5px; }}
    .otp-box {{ background: #eff6ff; border: 2px dashed #0284c7; border-radius: 10px; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #0b3d91; margin: 0; }}
    .otp-validity {{ font-size: 12px; color: #64748b; margin-top: 8px; }}
    .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; text-align: center; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>My Inventory System</h1>
      <p>Security Verification &amp; Email Confirmation</p>
    </div>
    <div class="body">
      <p>Hello <strong>{user_name}</strong>,</p>
      <p>You requested to verify and link this email address to your account. Use the genuine one-time verification code below to complete the verification:</p>
      
      <div class="otp-box">
        <div class="otp-code">{otp_code}</div>
        <div class="otp-validity"><i style="color: #0284c7;">&#9201;</i> Valid for 10 minutes &bull; Do not share this code</div>
      </div>

      <p style="font-size: 13px; color: #475569;">
        If you did not initiate this email verification request, no changes will be made to your account.
      </p>
    </div>
    <div class="footer">
      Amrapali University &bull; BBAT104: Total Quality Management &bull; Quality Goal Q14
    </div>
  </div>
</body>
</html>
"""

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=12)
            else:
                server = smtplib.SMTP(host, port, timeout=12)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(user, password)
            server.send_message(msg)
            server.quit()

            log_audit("system", "GENUINE_OTP_DISPATCHED", "EmailService", f"Sent live OTP to {recipient_email}")
            return (True, f"A genuine 6-digit verification code has been dispatched to {recipient_email}. Please check your inbox.")
        except smtplib.SMTPAuthenticationError as e:
            err = f"SMTP Authentication failed. Please check your username and App Password: {e}"
            log_error(err)
            return (False, err)
        except Exception as e:
            err = f"Failed to deliver email: {e}"
            log_error(err)
            return (False, err)
