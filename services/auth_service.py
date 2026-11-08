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

        full_name = row["full_name"] if "full_name" in row.keys() and row["full_name"] else "Ritik Kumar"
        age = row["age"] if "age" in row.keys() and row["age"] else 21
        mobile_no = row["mobile_no"] if "mobile_no" in row.keys() and row["mobile_no"] else "+91 9876543210"
        email_verified = row["email_verified"] if "email_verified" in row.keys() else 1
        mobile_verified = row["mobile_verified"] if "mobile_verified" in row.keys() else 1
        avatar_path = row["avatar_path"] if "avatar_path" in row.keys() and row["avatar_path"] else ""

        log_audit(row["username"], "LOGIN_SUCCESS", "Auth", f"Role: {role} (Portal: {required_role or 'Generic'})")
        return {
            "id": row["id"],
            "username": row["username"],
            "role": role,
            "email": row["email"] if "email" in row.keys() else "",
            "provider": "local",  # Direct login via ID & Password has no Google badge
            "display_name": display_name,
            "is_admin": role == "Admin",
            "full_name": full_name,
            "age": age,
            "mobile_no": mobile_no,
            "email_verified": email_verified,
            "mobile_verified": mobile_verified,
            "avatar_path": avatar_path,
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
            "full_name": row["full_name"] if "full_name" in row.keys() and row["full_name"] else (full_name or "Ritik Kumar"),
            "age": row["age"] if "age" in row.keys() and row["age"] else 21,
            "mobile_no": row["mobile_no"] if "mobile_no" in row.keys() and row["mobile_no"] else "+91 9876543210",
            "email_verified": 1,
            "avatar_path": row["avatar_path"] if "avatar_path" in row.keys() and row["avatar_path"] else "",
        }

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        conn = get_conn()
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        conn = get_conn()
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT id, username, role, email, provider, 
                   COALESCE(full_name, 'Ritik Kumar') as full_name,
                   COALESCE(age, 21) as age,
                   COALESCE(mobile_no, '+91 9876543210') as mobile_no,
                   COALESCE(email_verified, 1) as email_verified,
                   COALESCE(mobile_verified, 1) as mobile_verified,
                   COALESCE(avatar_path, '') as avatar_path
            FROM users 
            WHERE LOWER(username) = LOWER(?)
            """,
            (username.strip(),),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_profile(
        self,
        username: str,
        full_name: str,
        age: Optional[int],
        mobile_no: str,
        role: str,
        avatar_path: Optional[str] = None,
    ) -> bool:
        conn = get_conn()
        cur = conn.cursor()
        if avatar_path:
            cur.execute(
                """
                UPDATE users 
                SET full_name = ?, age = ?, mobile_no = ?, role = ?, avatar_path = ?
                WHERE LOWER(username) = LOWER(?)
                """,
                (full_name.strip(), age, mobile_no.strip(), role, avatar_path, username.strip()),
            )
        else:
            cur.execute(
                """
                UPDATE users 
                SET full_name = ?, age = ?, mobile_no = ?, role = ?
                WHERE LOWER(username) = LOWER(?)
                """,
                (full_name.strip(), age, mobile_no.strip(), role, username.strip()),
            )
        conn.commit()
        conn.close()
        log_audit(username, "PROFILE_UPDATED", "Auth", f"Full Name: {full_name}, Role: {role}")
        return True

    def update_user_email(self, username: str, email: str, email_verified: int = 1) -> bool:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET email = ?, email_verified = ? WHERE LOWER(username) = LOWER(?)",
            (email.strip().lower(), email_verified, username.strip()),
        )
        conn.commit()
        conn.close()
        log_audit(username, "EMAIL_VERIFIED_UPDATED", "Auth", f"New Email: {email}")
        return True

    def update_user_mobile(self, username: str, mobile_no: str, mobile_verified: int = 1) -> bool:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET mobile_no = ?, mobile_verified = ? WHERE LOWER(username) = LOWER(?)",
            (mobile_no.strip(), mobile_verified, username.strip()),
        )
        conn.commit()
        conn.close()
        log_audit(username, "MOBILE_VERIFIED_UPDATED", "Auth", f"New Mobile: {mobile_no}")
        return True
