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
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
            (username, username),
        ).fetchone()
        conn.close()

        if not row:
            log_audit(username, "LOGIN_FAILED", "Auth", f"User account '{username}' not found")
            return None, f"Invalid User ID '{username}'. Account not registered in system."

        if row["password"] != password:
            log_audit(username, "LOGIN_FAILED", "Auth", "Incorrect password attempt")
            return None, "Incorrect password. Please verify your credentials and try again."

        status = row["status"] if "status" in row.keys() and row["status"] else "Active"
        status_reason = row["status_reason"] if "status_reason" in row.keys() and row["status_reason"] else ""

        if status == "Suspended":
            reason_str = f" Reason: {status_reason}" if status_reason else ""
            log_audit(username, "LOGIN_BLOCKED_SUSPENDED", "Auth", f"Suspended account attempted login.{reason_str}")
            return (
                None,
                f"Access Denied: Your account '{username}' has been temporarily suspended by the Administrator.{reason_str} Please contact support.",
            )

        if status == "Banned":
            reason_str = f" Reason: {status_reason}" if status_reason else ""
            log_audit(username, "LOGIN_BLOCKED_BANNED", "Auth", f"Banned account attempted login.{reason_str}")
            return (
                None,
                f"Access Denied: Your account '{username}' has been permanently banned by the Administrator.{reason_str}",
            )

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

        full_name = row["full_name"] if "full_name" in row.keys() and row["full_name"] else ("Ritik Kumar" if "ritik" in row["username"].lower() or row["username"] in ("admin", "member") else row["username"].title())
        display_name = full_name
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
            SELECT * 
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

        status = row["status"] if "status" in row.keys() and row["status"] else "Active"
        status_reason = row["status_reason"] if "status_reason" in row.keys() and row["status_reason"] else ""

        if status == "Suspended":
            conn.close()
            reason_str = f" Reason: {status_reason}" if status_reason else ""
            log_audit(row["username"], "LOGIN_GOOGLE_SUSPENDED", "Auth", f"Suspended account attempted Google login.{reason_str}")
            raise ValueError(f"Access Denied: Your account has been temporarily suspended by the Administrator.{reason_str}")

        if status == "Banned":
            conn.close()
            reason_str = f" Reason: {status_reason}" if status_reason else ""
            log_audit(row["username"], "LOGIN_GOOGLE_BANNED", "Auth", f"Banned account attempted Google login.{reason_str}")
            raise ValueError(f"Access Denied: Your account has been permanently banned by the Administrator.{reason_str}")

        user_id = row["id"]
        username = row["username"]
        role = row["role"]
        conn.close()

        db_full_name = row["full_name"] if "full_name" in row.keys() and row["full_name"] else ""
        if db_full_name:
            display_name = db_full_name
        elif full_name:
            display_name = full_name
        elif "ritik" in email or "2520301005" in email or username.lower() == "ritik":
            display_name = "Ritik Kumar"
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

    # =========================================================================
    # MEMBER & USER ACCOUNT MANAGEMENT (ADMIN ONLY)
    # =========================================================================

    def get_all_users(self) -> list:
        """Fetch all registered users with complete profile and status details."""
        conn = get_conn()
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT id, username, role, email, provider,
                   COALESCE(full_name, 'Ritik Kumar') as full_name,
                   COALESCE(age, 21) as age,
                   COALESCE(mobile_no, '+91 9368039108') as mobile_no,
                   COALESCE(email_verified, 1) as email_verified,
                   COALESCE(mobile_verified, 1) as mobile_verified,
                   COALESCE(avatar_path, '') as avatar_path,
                   COALESCE(status, 'Active') as status,
                   COALESCE(status_reason, '') as status_reason,
                   COALESCE(created_at, '2026-11-09') as created_at
            FROM users
            ORDER BY 
                CASE WHEN role = 'Admin' THEN 1 ELSE 2 END,
                id ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_user_status(
        self, user_id: int, new_status: str, reason: str = "", current_admin_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Suspend, Ban, or Reactivate a user account."""
        valid_statuses = ["Active", "Suspended", "Banned"]
        if new_status not in valid_statuses:
            return False, f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}."

        if current_admin_id and int(user_id) == int(current_admin_id):
            return False, "Security Policy: You cannot suspend or ban your own active administrator account."

        conn = get_conn()
        cur = conn.cursor()
        user_row = cur.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            conn.close()
            return False, f"User with ID {user_id} not found."

        cur.execute(
            "UPDATE users SET status = ?, status_reason = ? WHERE id = ?",
            (new_status, reason.strip(), user_id),
        )
        conn.commit()
        conn.close()

        action_name = "REACTIVATED" if new_status == "Active" else new_status.upper()
        log_audit(
            "Admin",
            f"USER_{action_name}",
            "UserManagement",
            f"User @{user_row['username']} (ID: {user_id}) marked as '{new_status}'. Reason: {reason}",
        )
        return True, f"Account for @{user_row['username']} has been set to '{new_status}' successfully."

    def update_user_role(
        self, user_id: int, new_role: str, current_admin_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Promote to Admin or Demote to Member."""
        valid_roles = ["Admin", "Member"]
        new_role = new_role.strip().capitalize()
        if new_role not in valid_roles:
            return False, f"Invalid role '{new_role}'. Must be Admin or Member."

        conn = get_conn()
        cur = conn.cursor()
        user_row = cur.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            conn.close()
            return False, f"User with ID {user_id} not found."

        # Prevent demoting the last active administrator
        if new_role == "Member" and user_row["role"] == "Admin":
            admin_count_row = cur.execute("SELECT count(*) as c FROM users WHERE role = 'Admin' AND id != ?", (user_id,)).fetchone()
            if admin_count_row and admin_count_row["c"] == 0:
                conn.close()
                return False, "Security Policy: Cannot demote the only remaining Administrator account in the system."

        cur.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
        conn.close()

        log_audit(
            "Admin",
            "USER_ROLE_CHANGED",
            "UserManagement",
            f"User @{user_row['username']} (ID: {user_id}) role changed to '{new_role}'",
        )
        return True, f"Role for @{user_row['username']} changed to '{new_role}' successfully."

    def delete_user(self, user_id: int, current_admin_id: Optional[int] = None) -> Tuple[bool, str]:
        """Permanently delete a member account."""
        if current_admin_id and int(user_id) == int(current_admin_id):
            return False, "Security Policy: You cannot delete your own currently active administrator account."

        conn = get_conn()
        cur = conn.cursor()
        user_row = cur.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            conn.close()
            return False, f"User with ID {user_id} not found."

        if user_row["role"] == "Admin":
            admin_count_row = cur.execute("SELECT count(*) as c FROM users WHERE role = 'Admin' AND id != ?", (user_id,)).fetchone()
            if admin_count_row and admin_count_row["c"] == 0:
                conn.close()
                return False, "Security Policy: Cannot delete the only remaining Administrator in the system."

        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_audit(
            "Admin",
            "USER_DELETED",
            "UserManagement",
            f"Permanently deleted user @{user_row['username']} (ID: {user_id})",
        )
        return True, f"User @{user_row['username']} has been permanently deleted from the system."

    def create_member(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        role: str = "Member",
        mobile_no: str = "+91 9368039108",
        age: int = 21,
    ) -> Tuple[bool, str]:
        """Register a new member or administrator account."""
        username = (username or "").strip()
        password = (password or "").strip()
        full_name = (full_name or "").strip()
        email = (email or "").strip().lower()
        role = role.strip().capitalize() if role else "Member"

        if not username:
            return False, "Username is required."
        if not password:
            return False, "Password is required."
        if role not in ["Admin", "Member"]:
            role = "Member"

        conn = get_conn()
        cur = conn.cursor()
        existing = cur.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?) OR (email != '' AND LOWER(email) = LOWER(?))",
            (username, email),
        ).fetchone()
        if existing:
            conn.close()
            return False, f"An account with username '{username}' or email '{email}' already exists."

        cur.execute(
            """
            INSERT INTO users (username, password, role, email, provider, full_name, age, mobile_no, status, email_verified, mobile_verified)
            VALUES (?, ?, ?, ?, 'local', ?, ?, ?, 'Active', 1, 1)
            """,
            (username, password, role, email, full_name or username.title(), age, mobile_no),
        )
        conn.commit()
        conn.close()

        log_audit("Admin", "USER_CREATED", "UserManagement", f"Created @{username} with role '{role}'")
        return True, f"Account for @{username} successfully created with role '{role}'."
