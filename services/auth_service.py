"""Authentication and Role-Based Access Control Service.

Provides authentication, session management, and strict role differentiation for:
- Administrator (Faculty / Store Lead Auditor / Admin)
- Member (Student / Store Quality Operator)
"""

from typing import Optional, Dict, Any, Tuple
from database.db import get_conn
from utils.logger import log_audit, log_error


class AuthService:
    def __init__(self):
        pass

    def authenticate(
        self, username: str, password: str, required_role: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Validate credentials against database users table and enforce strict role boundaries.
        
        Returns:
            (user_dict, None) on success
            (None, error_message) on failure
        """
        username = (username or "").strip()
        password = (password or "").strip()
        if not username or not password:
            return None, "Please enter both User ID and Password."

        conn = get_conn()
        row = conn.execute(
            "SELECT id, username, password, role, email, provider FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
            (username, username),
        ).fetchone()
        conn.close()

        if not row:
            log_audit(username, "LOGIN_FAILED", "Auth", f"User account '{username}' not found")
            return None, f"Invalid User ID '{username}'. Account not registered in system."

        if row["password"] != password:
            log_audit(username, "LOGIN_FAILED", "Auth", "Incorrect password attempt")
            return None, "Incorrect password. Please verify your credentials and try again."

        role = row["role"]

        # Enforce strict role differentiation between Admin and Member
        if required_role:
            req = required_role.strip().capitalize()
            if req == "Admin" and role != "Admin":
                log_audit(
                    row["username"],
                    "LOGIN_REJECTED",
                    "Auth",
                    f"Member '{username}' attempted login on Admin Portal",
                )
                return (
                    None,
                    f"Access Denied: Account '{username}' is registered as a Member, not an Administrator. "
                    "Please switch to the 'Member Login' tab to sign in.",
                )
            elif req == "Member" and role != "Member":
                log_audit(
                    row["username"],
                    "LOGIN_REJECTED",
                    "Auth",
                    f"Admin '{username}' attempted login on Member Portal",
                )
                return (
                    None,
                    f"Access Denied: Account '{username}' is an Administrator account. "
                    "Administrator accounts cannot sign in through the Member Login screen. "
                    "Please switch to the 'Admin Login' tab.",
                )

        display_name = "Admin" if role == "Admin" else "Member"

        log_audit(row["username"], "LOGIN_SUCCESS", "Auth", f"Role: {role} (Portal: {required_role or 'Generic'})")
        return {
            "id": row["id"],
            "username": row["username"],
            "role": role,
            "email": row["email"] if "email" in row.keys() else "",
            "provider": "local",  # Direct login via ID & Password has no Google badge
            "display_name": display_name,
            "is_admin": role == "Admin",
        }, None

    def authenticate_google(
        self, email: str, full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate a user via Google / Gmail ID.
        
        Strict Security Policy: Only genuine registered accounts in the system can sign in.
        Unregistered emails are rejected with an explicit error.
        """
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            raise ValueError("A valid Gmail or Google Workspace email address is required.")

        conn = get_conn()
        cur = conn.cursor()

        # Check if a genuine registered account exists with this email or username
        row = cur.execute(
            """
            SELECT id, username, role, email, provider, password 
            FROM users 
            WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)
            """,
            (email, email),
        ).fetchone()

        if not row:
            conn.close()
            log_audit(
                email,
                "LOGIN_GOOGLE_REJECTED",
                "Auth",
                f"Unregistered email '{email}' attempted Google sign-in",
            )
            raise ValueError(
                f"No registered account found for '{email}'. "
                "Only genuine registered accounts can sign in. "
                "Please verify your email or sign in directly using your User ID and Password."
            )

        user_id = row["id"]
        username = row["username"]
        role = row["role"]
        conn.close()

        if full_name:
            display_name = full_name
        elif "ritik" in email or "2520301005" in email or username.lower() == "ritik":
            display_name = "Ritik Kumar"
        elif role == "Admin":
            display_name = "System Admin"
        else:
            display_name = username.title()

        log_audit(username, "LOGIN_GOOGLE_SUCCESS", "Auth", f"Email: {email}, Role: {role}")
        return {
            "id": user_id,
            "username": username,
            "role": role,
            "email": email,
            "display_name": display_name,
            "provider": "google",
            "is_admin": role == "Admin",
        }

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        conn = get_conn()
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
