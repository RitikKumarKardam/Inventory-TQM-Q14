"""Genuine SMS & OTP Dispatch Service for My Inventory Management System.

Integrates with genuine telecom SMS gateways:
1. Fast2SMS (Primary for Indian +91 mobile numbers, zero DLT required for testing via Quick route, instant delivery)
2. Twilio (Global SMS delivery)

Stores and retrieves API credentials securely in environment variables and SQLite system_config table.
"""

import os
import re
import json
import requests
from typing import Tuple, Dict, Any
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


class SmsService:
    @staticmethod
    def get_gateway_status() -> Dict[str, Any]:
        """Check whether any SMS gateway is configured and active."""
        fast2sms_key = get_config_value("FAST2SMS_API_KEY", "")
        twilio_sid = get_config_value("TWILIO_ACCOUNT_SID", "")
        twilio_token = get_config_value("TWILIO_AUTH_TOKEN", "")
        twilio_from = get_config_value("TWILIO_PHONE_NUMBER", "")

        if fast2sms_key:
            masked = fast2sms_key[:4] + "..." + fast2sms_key[-4:] if len(fast2sms_key) > 8 else "***"
            return {
                "is_configured": True,
                "provider": "Fast2SMS (India +91)",
                "key_masked": masked,
                "fast2sms_key": fast2sms_key,
            }
        elif twilio_sid and twilio_token and twilio_from:
            masked = twilio_sid[:4] + "..." + twilio_sid[-4:] if len(twilio_sid) > 8 else "***"
            return {
                "is_configured": True,
                "provider": "Twilio",
                "key_masked": masked,
                "twilio_sid": twilio_sid,
                "twilio_from": twilio_from,
            }
        return {
            "is_configured": False,
            "provider": "None",
            "key_masked": "",
        }

    @staticmethod
    def clean_indian_phone(phone_input: str) -> str:
        """Extract a 10-digit Indian phone number from any formatted input."""
        digits = re.sub(r"\D", "", phone_input or "")
        if digits.startswith("91") and len(digits) == 12:
            return digits[2:]
        if len(digits) > 10:
            return digits[-10:]
        return digits

    @staticmethod
    def send_fast2sms(api_key: str, mobile_10_digit: str, otp_code: str) -> Tuple[bool, str]:
        """Dispatch real SMS using Fast2SMS Quick / OTP route."""
        url = "https://www.fast2sms.com/dev/bulkV2"

        # Attempt 1: Try the Quick route ('q') which bypasses DLT template requirements
        payload_quick = {
            "route": "q",
            "message": f"Your verification code for My Inventory System is {otp_code}. Valid for 10 minutes. Do not share with anyone.",
            "language": "english",
            "flash": 0,
            "numbers": mobile_10_digit,
        }
        headers = {
            "authorization": api_key,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        try:
            res = requests.post(url, json=payload_quick, headers=headers, timeout=12)
            data = res.json()
            if data.get("return") is True:
                req_id = data.get("request_id", "")
                log_audit("system", "SMS_DISPATCH_SUCCESS", f"Sent SMS to {mobile_10_digit} (req: {req_id})")
                return True, f"Genuine SMS successfully dispatched to +91 {mobile_10_digit} via Fast2SMS! Please check your mobile phone's Messages app."
            
            # If quick route returns an error, attempt the OTP route
            payload_otp = {
                "variables_values": otp_code,
                "route": "otp",
                "numbers": mobile_10_digit,
            }
            res_otp = requests.post(url, json=payload_otp, headers=headers, timeout=12)
            data_otp = res_otp.json()
            if data_otp.get("return") is True:
                log_audit("system", "SMS_DISPATCH_SUCCESS", f"Sent OTP SMS to {mobile_10_digit}")
                return True, f"Genuine SMS successfully dispatched to +91 {mobile_10_digit}! Please check your phone Messages."
            
            error_msg = data.get("message") or data_otp.get("message") or "Fast2SMS gateway rejected message"
            if isinstance(error_msg, list):
                error_msg = ", ".join(error_msg)
            return False, f"Fast2SMS Gateway Error: {error_msg}"
        except Exception as e:
            log_error(f"Fast2SMS request failed: {e}")
            return False, f"SMS Gateway Connection Error: {str(e)}"

    @staticmethod
    def send_twilio(account_sid: str, auth_token: str, from_number: str, mobile_10_digit: str, otp_code: str) -> Tuple[bool, str]:
        """Dispatch real SMS using Twilio."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        to_number = f"+91{mobile_10_digit}"
        payload = {
            "From": from_number,
            "To": to_number,
            "Body": f"Your My Inventory System verification OTP is {otp_code}. Valid for 10 minutes.",
        }
        try:
            res = requests.post(url, data=payload, auth=(account_sid, auth_token), timeout=12)
            if res.status_code in [200, 201]:
                return True, f"Genuine SMS dispatched to {to_number} via Twilio! Please check your phone Messages."
            data = res.json()
            return False, f"Twilio Error: {data.get('message', 'SMS dispatch failed')}"
        except Exception as e:
            return False, f"Twilio Gateway Connection Error: {str(e)}"

    @staticmethod
    def send_otp_sms(mobile_input: str, otp_code: str) -> Tuple[bool, str]:
        """Primary method: Dispatches a genuine SMS to the recipient's physical phone.
        
        Returns (success: bool, message: str).
        """
        mobile_10_digit = SmsService.clean_indian_phone(mobile_input)
        if len(mobile_10_digit) != 10:
            return False, f"Invalid mobile number '{mobile_input}'. Please enter a valid 10-digit Indian phone number."

        status = SmsService.get_gateway_status()
        if not status["is_configured"]:
            return (
                False,
                "SMS Gateway is not yet configured. To send a genuine SMS to your mobile phone (+91 "
                + mobile_10_digit
                + "), please enter your Fast2SMS API Key below (sign up free at fast2sms.com for ₹50 test credit, no credit card required).",
            )

        if "Fast2SMS" in status["provider"]:
            return SmsService.send_fast2sms(status["fast2sms_key"], mobile_10_digit, otp_code)
        elif "Twilio" in status["provider"]:
            auth_token = get_config_value("TWILIO_AUTH_TOKEN", "")
            return SmsService.send_twilio(
                status["twilio_sid"], auth_token, status["twilio_from"], mobile_10_digit, otp_code
            )

        return False, "Unknown SMS Gateway provider."
