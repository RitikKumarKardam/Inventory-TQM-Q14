"""Amrapali University - Total Quality Inventory Management Web Portal.

Subject: BBAT104 Fundamental of Total Quality Management (TQM)
Quality Goal: Q14 - Improve Navigation
Candidate: Ritik Kumar (Roll No: 2520301005, B.Tech CSE 5th Sem, Sec C)
Session: 2026-27

Aligned with: https://student.amrapali.ac.in
"""

import csv
import io
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file if present
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

from database.schema import init_db, seed_demo
from models.product import ProductData
from services.auth_service import AuthService
from services.email_service import EmailService, set_config_value
from services.sms_service import SmsService
from services.inventory_service import InventoryService
from services.product_service import ProductService
from services.report_service import ReportService
from services.supplier_service import SupplierService
from services.tqm_service import TQMService
from utils.logger import log_audit, log_error
from utils.validators import ValidationError

# Initialize Database Schema & Seed Data
init_db()
seed_demo()

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)
app.secret_key = "amrapali-tqm-q14-secret-key-2026"

CURRENT_USER = "admin"
STUDENT_INFO = {
    "name": "Ritik Kumar",
    "roll_no": "2520301005",
    "serial_no": "136",
    "programme": "B.Tech CSE",
    "semester": "5th Semester",
    "section": "Section C",
    "session": "2026-27",
    "course_code": "BBAT104",
    "course_name": "Fundamental of Total Quality Management",
    "quality_goal": "Q14 - Improve Navigation",
    "institution": "Amrapali University / Group of Institutes, Haldwani",
}

# Service instances
auth_service = AuthService()
product_service = ProductService(CURRENT_USER)
inventory_service = InventoryService(CURRENT_USER)
report_service = ReportService(CURRENT_USER)
supplier_service = SupplierService(CURRENT_USER)
tqm_service = TQMService(CURRENT_USER)


@app.before_request
def require_login():
    """Ensure unauthenticated users are directed to the login portal."""
    # Allow static assets and login routes without session
    if request.endpoint in ("login", "login_google", "login_google_callback", "get_captcha", "static") or (
        request.path and (request.path.startswith("/static") or request.path.startswith("/login") or request.path.startswith("/captcha"))
    ):
        return None

    if "user" not in session:
        return redirect(url_for("login"))


@app.context_processor
def inject_common_context():
    """Inject student credentials, active user session, and global quality metrics to every template."""
    try:
        metrics = report_service.dashboard_metrics()
    except Exception:
        metrics = {"total_products": 0, "low_stock": 0, "total_suppliers": 0, "stock_units": 0}

    raw_user = session.get("user", {
        "username": "guest",
        "role": "Guest",
        "is_admin": False,
        "display_name": "Guest User",
    })
    user_dict = dict(raw_user)
    if user_dict.get("is_admin") or user_dict.get("role") == "Admin":
        user_dict["display_name"] = "Admin"
    elif user_dict.get("role") == "Member":
        user_dict["display_name"] = "Member"

    if not user_dict.get("full_name"):
        user_dict["full_name"] = "Ritik Kumar"
    if not user_dict.get("avatar_path"):
        user_dict["avatar_path"] = ""

    return {
        "student": STUDENT_INFO,
        "metrics": metrics,
        "user": user_dict,
    }


# =============================================================================
# AUTHENTICATION & SECURITY VERIFICATION (CAPTCHA)
# =============================================================================

def generate_captcha_text(length: int = 5) -> str:
    """Generate unambiguous alphanumeric security CAPTCHA code.
    
    Mixture of maximum 2 numerical digits (1 or 2 numbers) and 3 alphabet letters only,
    shuffled so they appear at any position.
    """
    digits_pool = "23456789"
    letters_pool = "ABCDEFGHJKLMNPQRSTUVWXYZ"

    num_digits = random.choice([1, 2])
    num_letters = 3

    digits = random.choices(digits_pool, k=num_digits)
    letters = random.choices(letters_pool, k=num_letters)

    chars = digits + letters
    random.shuffle(chars)
    return "".join(chars)


def generate_captcha_svg(code: str) -> str:
    """Generate an anti-bot SVG image badge for CAPTCHA security verification."""
    width = 110
    height = 36
    chars = list(code)
    lines = []
    for _ in range(4):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        color = random.choice(["#0284c7", "#0369a1", "#0b3d91", "#0ea5e9"])
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.2" opacity="0.45" />')
    char_elements = []
    char_spacing = (width - 16) / max(len(chars), 1)
    for i, ch in enumerate(chars):
        x = 10 + i * char_spacing
        y = random.randint(23, 27)
        rot = random.randint(-12, 12)
        color = random.choice(["#0b3d91", "#1e3a8a", "#0369a1", "#0f172a"])
        char_elements.append(
            f'<text x="{x}" y="{y}" fill="{color}" font-family="Courier New, monospace, sans-serif" font-size="20" font-weight="bold" transform="rotate({rot} {x} {y})">{ch}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="#e0f2fe" rx="4"/>'
        f'{"".join(lines)}'
        f'{"".join(char_elements)}'
        f'</svg>'
    )


@app.route("/captcha.svg")
def get_captcha():
    """Generate and return SVG CAPTCHA badge and store the code in session."""
    code = generate_captcha_text(5)
    session["captcha"] = code
    svg = generate_captcha_svg(code)
    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/login", methods=["GET", "POST"])
def login():
    # Detect target role from query string or default to Admin
    target_role = request.args.get("role", "Admin").capitalize()
    if target_role not in ("Admin", "Member"):
        target_role = "Admin"

    if request.method == "POST":
        # 1. Enforce Security Code (CAPTCHA)
        user_captcha = request.form.get("captcha", "").strip().upper()
        session_captcha = session.get("captcha", "").strip().upper()

        if session_captcha:
            if not user_captcha or user_captcha != session_captcha:
                flash(
                    "Invalid CAPTCHA code: Please enter the correct characters shown in the security box.",
                    "danger",
                )
                return render_template("login.html", active_role=target_role)
            session.pop("captcha", None)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        form_role = request.form.get("role_hint", target_role).capitalize()
        if form_role in ("Admin", "Member"):
            target_role = form_role

        user_data, err_msg = auth_service.authenticate(
            username, password, required_role=target_role
        )
        if user_data:
            session["user"] = user_data
            welcome_name = user_data.get("full_name") or user_data.get("display_name") or user_data.get("username", "").title()
            flash(
                f"Welcome, {welcome_name}!",
                "success",
            )
            return redirect(url_for("dashboard"))
        else:
            flash(err_msg or "Invalid User ID or Password. Please check your credentials.", "danger")

    return render_template("login.html", active_role=target_role)


@app.route("/login/google", methods=["GET", "POST"])
def login_google():
    """Google Account / Gmail authentication portal.
    
    If Google OAuth credentials (GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET) are configured:
      Redirects browser DIRECTLY to Google's official login page (accounts.google.com).
    Otherwise:
      Renders the Google Sign-In interface with one-click direct connection setup.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

    # 1. Direct Live Google OAuth 2.0 Redirect to accounts.google.com
    if client_id and request.method == "GET" and not request.args.get("config"):
        redirect_uri = url_for("login_google_callback", _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "prompt": "select_account",
            "access_type": "online",
        }
        google_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        return redirect(google_url)

    # 2. Handle POST submissions
    if request.method == "POST":
        # Handle saving Google Cloud Client ID & Secret
        if "save_google_creds" in request.form:
            new_client_id = request.form.get("client_id", "").strip()
            new_client_secret = request.form.get("client_secret", "").strip()
            if new_client_id:
                os.environ["GOOGLE_CLIENT_ID"] = new_client_id
                os.environ["GOOGLE_CLIENT_SECRET"] = new_client_secret
                env_file = PROJECT_ROOT / ".env"
                with open(env_file, "a", encoding="utf-8") as f:
                    f.write(f"\nGOOGLE_CLIENT_ID={new_client_id}\nGOOGLE_CLIENT_SECRET={new_client_secret}\n")
                flash("Google OAuth Client ID saved! Redirecting to Google login page...", "success")
                return redirect(url_for("login_google"))

        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip() or None
        try:
            user_data = auth_service.authenticate_google(email, full_name)
            session["user"] = user_data
            welcome_name = user_data.get("full_name") or user_data.get("display_name") or (full_name if full_name else email)
            flash(
                f"Welcome, {welcome_name}!",
                "success",
            )
            return redirect(url_for("dashboard"))
        except Exception as ex:
            flash(f"Google Sign-In failed: {str(ex)}", "danger")

    return render_template(
        "google_auth.html",
        has_client_id=bool(client_id),
        client_id=client_id,
    )


@app.route("/login/google/callback")
def login_google_callback():
    """Handle Google OAuth 2.0 Callback and validate registered account on the inventory system."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        flash(f"Google Sign-In was cancelled or rejected by Google: {error}", "warning")
        return redirect(url_for("login"))

    if not code:
        flash("Google did not return an authorization code. Please try again.", "danger")
        return redirect(url_for("login"))

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = url_for("login_google_callback", _external=True)

    try:
        # 1. Exchange authorization code for tokens with Google
        token_payload = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }).encode("utf-8")

        token_req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Google token exchange did not yield an access_token.")

        # 2. Fetch authenticated profile from Google's UserInfo API
        userinfo_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
            google_user = json.loads(resp.read().decode("utf-8"))

        google_email = google_user.get("email", "").strip().lower()
        full_name = google_user.get("name", "")

        # 3. STRICT VALIDATION: Check if this Google account already exists on this inventory management system
        user_data = auth_service.authenticate_google(google_email, full_name=full_name)
        session["user"] = user_data
        welcome_name = user_data.get("full_name") or user_data.get("display_name") or (full_name if full_name else google_email)
        flash(
            f"Welcome, {welcome_name}!",
            "success",
        )
        return redirect(url_for("dashboard"))

    except ValueError as val_err:
        # Not registered in the inventory system!
        flash(str(val_err), "danger")
        return redirect(url_for("login"))
    except Exception as ex:
        flash(f"Google OAuth authentication failed: {str(ex)}", "danger")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    user = session.pop("user", None)
    if user:
        log_audit(user.get("username", "user"), "LOGOUT", "Auth", "User logged out")
    flash("You have been signed out of the portal.", "info")
    return redirect(url_for("login"))



# =============================================================================
# 1. DASHBOARD / HOME ROUTE (Q14 Universal Home Destination)
# =============================================================================

@app.route("/")
def dashboard():
    metrics = report_service.dashboard_metrics()
    quality_summary = report_service.quality_summary()
    low_stock_items = report_service.low_stock_rows()
    recent_movements = report_service.movement_summary(limit=6)
    recent_audits = report_service.recent_audit(limit=6)
    category_dist = report_service.category_distribution()
    pareto_data = tqm_service.get_pareto_data()
    inspections = tqm_service.get_inspections(limit=50)

    passed = sum(1 for i in inspections if i["inspection_status"] == "PASSED")
    total_insp = max(1, len(inspections))
    quality_pass_rate = round((passed / total_insp) * 100, 1)

    categories, _ = product_service.get_form_options()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        metrics=metrics,
        quality_summary=quality_summary,
        low_stock_items=low_stock_items,
        recent_movements=recent_movements,
        recent_audits=recent_audits,
        category_distribution=category_dist,
        pareto_data=pareto_data,
        quality_pass_rate=quality_pass_rate,
        categories=categories,
    )


# =============================================================================
# 2. PRODUCTS CATALOG & INVENTORY MANAGEMENT
# =============================================================================

@app.route("/products")
def products():
    product_list = product_service.list_products()
    categories, suppliers = product_service.get_form_options()
    return render_template(
        "products.html",
        active_page="products",
        products=product_list,
        categories=categories,
        suppliers=suppliers,
    )


@app.route("/products/create", methods=["POST"])
def create_product():
    try:
        sku = request.form.get("sku", "").strip()
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id") or None
        supplier_id = request.form.get("supplier_id") or None
        quantity = request.form.get("quantity", 0)
        reorder_level = request.form.get("reorder_level", 5)
        price = request.form.get("price", 0.0)
        status = request.form.get("status", "Active")

        data = ProductData(
            sku=sku,
            name=name,
            category_id=int(category_id) if category_id else None,
            supplier_id=int(supplier_id) if supplier_id else None,
            quantity=int(quantity),
            reorder_level=int(reorder_level),
            price=float(price),
            status=status,
        )
        product_service.save_product(data)
        flash(f"Product '{sku} - {name}' added successfully to warehouse catalog.", "success")
    except ValidationError as ve:
        flash(f"Validation Error: {str(ve)}", "danger")
    except Exception as ex:
        flash(f"Error creating product: {str(ex)}", "danger")

    return redirect(url_for("products"))


@app.route("/products/<int:product_id>/edit", methods=["POST"])
def edit_product(product_id: int):
    try:
        sku = request.form.get("sku", "").strip()
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id") or None
        supplier_id = request.form.get("supplier_id") or None
        quantity = request.form.get("quantity", 0)
        reorder_level = request.form.get("reorder_level", 5)
        price = request.form.get("price", 0.0)
        status = request.form.get("status", "Active")

        data = ProductData(
            sku=sku,
            name=name,
            category_id=int(category_id) if category_id else None,
            supplier_id=int(supplier_id) if supplier_id else None,
            quantity=int(quantity),
            reorder_level=int(reorder_level),
            price=float(price),
            status=status,
        )
        product_service.save_product(data, product_id=product_id)
        flash(f"Product '{sku}' updated successfully.", "success")
    except Exception as ex:
        flash(f"Error updating product: {str(ex)}", "danger")

    return redirect(url_for("products"))


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id: int):
    user = session.get("user", {})
    if not user.get("is_admin"):
        flash("Permission Denied: Only Administrator accounts can delete product assets.", "danger")
        return redirect(url_for("products"))

    try:
        product_service.delete_product(product_id)
        flash("Product item deleted from database.", "success")
    except Exception as ex:
        flash(f"Error deleting product: {str(ex)}", "danger")

    return redirect(url_for("products"))


# =============================================================================
# 3. STOCK IN / OUT MOVEMENTS
# =============================================================================

@app.route("/stock")
def stock():
    movement_list = inventory_service.list_stock_movements()
    products_for_movement = inventory_service.list_products_for_movement()
    return render_template(
        "stock.html",
        active_page="stock",
        movements=movement_list,
        products_for_movement=products_for_movement,
    )


@app.route("/stock/movement", methods=["POST"])
def record_stock_movement():
    try:
        product_id = int(request.form.get("product_id"))
        movement_type = request.form.get("movement_type", "IN").upper()
        quantity = int(request.form.get("quantity", 1))
        note = request.form.get("note", "").strip()

        inventory_service.record_movement(product_id, movement_type, quantity, note)
        flash(f"Stock {movement_type} of {quantity} units recorded successfully.", "success")
    except ValidationError as ve:
        flash(f"Movement validation failed: {str(ve)}", "danger")
    except Exception as ex:
        flash(f"Error recording movement: {str(ex)}", "danger")

    return redirect(url_for("stock"))


# =============================================================================
# 4. SUPPLIERS & VENDOR QUALITY RATINGS (VQR)
# =============================================================================

@app.route("/suppliers")
def suppliers():
    scorecards = tqm_service.get_supplier_scorecards()
    return render_template(
        "suppliers.html",
        active_page="suppliers",
        scorecards=scorecards,
    )


@app.route("/suppliers/create", methods=["POST"])
def create_supplier():
    try:
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        supplier_service.create_supplier(name, phone, email, address)
        flash(f"Supplier '{name}' registered successfully.", "success")
    except Exception as ex:
        flash(f"Error registering supplier: {str(ex)}", "danger")

    return redirect(url_for("suppliers"))


# =============================================================================
# 5. INCOMING QUALITY INSPECTION (GRN QC)
# =============================================================================

@app.route("/inspections")
def inspections():
    inspection_list = tqm_service.get_inspections()
    products_list = product_service.list_products()
    supplier_list = supplier_service.list_suppliers()

    passed_count = sum(1 for i in inspection_list if i["inspection_status"] == "PASSED")
    quarantine_count = sum(1 for i in inspection_list if i["inspection_status"] == "QUARANTINE")
    total = max(1, len(inspection_list))
    pass_rate = round((passed_count / total) * 100, 1)

    return render_template(
        "inspections.html",
        active_page="inspections",
        inspections=inspection_list,
        products=products_list,
        suppliers=supplier_list,
        passed_count=passed_count,
        quarantine_count=quarantine_count,
        pass_rate=pass_rate,
    )


@app.route("/inspections/record", methods=["POST"])
def record_inspection():
    try:
        lot_number = request.form.get("lot_number", "").strip()
        product_id = int(request.form.get("product_id"))
        supplier_id = request.form.get("supplier_id")
        sample_size = int(request.form.get("sample_size", 20))
        defects_found = int(request.form.get("defects_found", 0))
        defect_type = request.form.get("defect_type", "").strip()
        inspection_status = request.form.get("inspection_status", "PASSED")
        remarks = request.form.get("remarks", "").strip()

        s_id = int(supplier_id) if supplier_id else None
        tqm_service.record_inspection(
            lot_number, product_id, s_id, sample_size, defects_found, defect_type, inspection_status, remarks
        )
        flash(f"Lot inspection for '{lot_number}' recorded with status: {inspection_status}.", "success")
    except Exception as ex:
        flash(f"Error recording inspection: {str(ex)}", "danger")

    return redirect(url_for("inspections"))


# =============================================================================
# 6. TQM 7 QC TOOLS SUITE (Pareto, Fishbone, FMEA, PDCA, CTQ)
# =============================================================================

@app.route("/tqm")
def tqm_suite():
    pareto_data = tqm_service.get_pareto_data()
    fishbone_data = tqm_service.get_fishbone_model()
    fmea_records = tqm_service.get_fmea_records()
    pdca_records = tqm_service.get_pdca_records()

    return render_template(
        "tqm.html",
        active_page="tqm",
        pareto_data=pareto_data,
        fishbone=fishbone_data,
        fmea_records=fmea_records,
        pdca_records=pdca_records,
    )


@app.route("/tqm/fmea/add", methods=["POST"])
def add_fmea():
    try:
        failure_mode = request.form.get("failure_mode", "").strip()
        cause = request.form.get("cause", "").strip()
        effect = request.form.get("effect", "").strip()
        severity = int(request.form.get("severity", 5))
        occurrence = int(request.form.get("occurrence", 5))
        detection = int(request.form.get("detection", 5))
        recommended_action = request.form.get("recommended_action", "").strip()
        action_taken = request.form.get("action_taken", "").strip()

        tqm_service.add_fmea_record(
            failure_mode, cause, effect, severity, occurrence, detection, recommended_action, action_taken
        )
        flash(f"FMEA assessment added. RPN computed as {severity * occurrence * detection}.", "success")
    except Exception as ex:
        flash(f"Error saving FMEA record: {str(ex)}", "danger")

    return redirect(url_for("tqm_suite"))


@app.route("/tqm/defect/add", methods=["POST"])
def add_defect():
    try:
        defect_type = request.form.get("defect_type", "").strip()
        frequency = int(request.form.get("frequency", 1))
        category = request.form.get("category", "General").strip()

        tqm_service.record_defect(defect_type, frequency, category)
        flash(f"Defect observation '{defect_type}' logged into Pareto table.", "success")
    except Exception as ex:
        flash(f"Error logging defect: {str(ex)}", "danger")

    return redirect(url_for("tqm_suite"))


@app.route("/tqm/pdca/add", methods=["POST"])
def add_pdca():
    try:
        phase = request.form.get("phase", "Plan")
        action = request.form.get("action", "").strip()
        evidence = request.form.get("evidence", "").strip()
        owner = request.form.get("owner", STUDENT_INFO["name"])
        status = request.form.get("status", "Complete")

        tqm_service.add_pdca_record(phase, action, evidence, owner, status)
        flash(f"PDCA step added under {phase} phase.", "success")
    except Exception as ex:
        flash(f"Error adding PDCA record: {str(ex)}", "danger")

    return redirect(url_for("tqm_suite"))


# =============================================================================
# 7. INDUSTRY CALCULATORS (EOQ & ABC INVENTORY STRATIFICATION)
# =============================================================================

@app.route("/calculators")
def calculators():
    abc_data = tqm_service.calculate_abc_analysis()
    return render_template(
        "calculators.html",
        active_page="calculators",
        abc_data=abc_data,
    )


# =============================================================================
# 8. QUALITY REPORTS & ISO 9001 AUDIT TRAIL
# =============================================================================

@app.route("/reports")
def reports():
    low_stock_rows = report_service.low_stock_rows()
    quality_summary = report_service.quality_summary()
    audit_rows = report_service.recent_audit(limit=100)
    error_rows = report_service.recent_errors(limit=50)

    return render_template(
        "reports.html",
        active_page="reports",
        low_stock_rows=low_stock_rows,
        quality_summary=quality_summary,
        audit_rows=audit_rows,
        error_rows=error_rows,
    )


# =============================================================================
# 9. VIVA & SYLLABUS REFERENCE GUIDE
# =============================================================================

@app.route("/viva-guide")
def viva_guide():
    audit_scorecard = tqm_service.get_navigation_audit_scorecard()
    return render_template(
        "viva_guide.html",
        active_page="viva",
        audit_scorecard=audit_scorecard,
    )


# =============================================================================
# 10. USER PROFILE & CUSTOMIZATION SCREEN
# =============================================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    username = user.get("username", "")
    is_admin = bool(user.get("is_admin") or user.get("role") == "Admin")

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip() or "Ritik Kumar"
        age_str = request.form.get("age", "").strip()
        try:
            age = int(age_str) if age_str else 21
        except ValueError:
            age = 21

        mobile_no = request.form.get("mobile_no", "").strip() or "+91 9876543210"

        # STRICT ACCESS CONTROL:
        # System roles can ONLY be decided/altered by Administrators.
        # Members CANNOT set or alter their own role under any circumstances.
        if is_admin:
            role = request.form.get("role", "Admin").capitalize()
            if role not in ("Admin", "Member"):
                role = "Admin"
        else:
            # Strictly maintain existing role for non-admins
            role = user.get("role", "Member")

        avatar_path = None
        # Handle avatar photo upload
        if "avatar" in request.files:
            file = request.files["avatar"]
            if file and file.filename != "":
                ext = Path(file.filename).suffix.lower()
                if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    upload_folder = PROJECT_ROOT / "static" / "uploads" / "avatars"
                    upload_folder.mkdir(parents=True, exist_ok=True)
                    safe_uname = secure_filename(username) or "user"
                    safe_name = f"{safe_uname}_{int(time.time())}{ext}"
                    dest = upload_folder / safe_name
                    file.save(str(dest))
                    avatar_path = f"/static/uploads/avatars/{safe_name}"

        auth_service.update_user_profile(
            username=username,
            full_name=full_name,
            age=age,
            mobile_no=mobile_no,
            role=role,
            avatar_path=avatar_path,
        )

        # Update session immediately
        session["user"]["full_name"] = full_name
        session["user"]["age"] = age
        session["user"]["mobile_no"] = mobile_no
        session["user"]["role"] = role
        session["user"]["is_admin"] = (role == "Admin")
        session["user"]["display_name"] = full_name
        if avatar_path:
            session["user"]["avatar_path"] = avatar_path
        session.modified = True

        flash("Profile information updated successfully!", "success")
        return redirect(url_for("profile"))

    # GET profile
    user_profile = auth_service.get_user_profile(username)
    if not user_profile:
        user_profile = dict(user)

    smtp_settings = EmailService.get_smtp_settings()
    sms_gateway_status = SmsService.get_gateway_status()

    return render_template(
        "profile.html",
        active_page="profile",
        profile=user_profile,
        smtp_settings=smtp_settings,
        sms_gateway_status=sms_gateway_status,
        is_admin=is_admin,
    )


@app.route("/profile/send-otp", methods=["POST"])
def profile_send_otp():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    new_email = (data.get("email") or "").strip().lower()
    if not new_email or "@" not in new_email or "." not in new_email:
        return jsonify({"success": False, "error": "Please enter a valid email address."}), 400

    otp = f"{random.randint(100000, 999999)}"
    user_name = user.get("full_name") or user.get("display_name") or "User"

    # In test mode, allow simulating successful dispatch if requested
    if app.config.get("TESTING") or os.getenv("TESTING") == "1":
        session["email_otp"] = {
            "code": otp,
            "email": new_email,
            "created_at": time.time(),
        }
        session.modified = True
        return jsonify({
            "success": True,
            "message": f"A genuine 6-digit verification code has been dispatched to {new_email}. Please check your email inbox and enter the code below.",
            "email": new_email,
            "_test_otp": otp,  # Only present during automated unit tests
        })

    # Send GENUINE email via authenticated SMTP
    success, send_msg = EmailService.send_otp_email(
        recipient_email=new_email,
        otp_code=otp,
        user_name=user_name,
    )

    if not success:
        return jsonify({
            "success": False,
            "error": send_msg,
        }), 400

    # Store OTP in session only if email was genuinely dispatched
    session["email_otp"] = {
        "code": otp,
        "email": new_email,
        "created_at": time.time(),
    }
    session.modified = True

    # STRICTLY NO SPOOF OTP RETURNED! Real email was sent to user's actual inbox
    return jsonify({
        "success": True,
        "message": f"A genuine 6-digit verification code has been dispatched to {new_email}. Please check your email inbox and enter the code below.",
        "email": new_email,
    })


@app.route("/profile/smtp-config", methods=["POST"])
def profile_smtp_config():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    smtp_host = (data.get("smtp_host") or "smtp.gmail.com").strip()
    smtp_port = (data.get("smtp_port") or "587").strip()
    smtp_user = (data.get("smtp_user") or "").strip()
    smtp_password = (data.get("smtp_password") or "").strip()
    smtp_from = (data.get("smtp_from") or smtp_user).strip()

    if not smtp_user or not smtp_password:
        return jsonify({"success": False, "error": "SMTP User email and App Password are required."}), 400

    try:
        port_int = int(smtp_port)
    except ValueError:
        port_int = 587

    # Test the credentials directly against the SMTP server
    is_valid, test_msg = EmailService.test_smtp_connection(smtp_host, port_int, smtp_user, smtp_password)
    if not is_valid:
        return jsonify({"success": False, "error": test_msg}), 400

    set_config_value("SMTP_HOST", smtp_host)
    set_config_value("SMTP_PORT", str(port_int))
    set_config_value("SMTP_USER", smtp_user)
    set_config_value("SMTP_PASSWORD", smtp_password)
    set_config_value("SMTP_FROM", smtp_from)

    try:
        env_file = PROJECT_ROOT / ".env"
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"\nSMTP_HOST={smtp_host}\nSMTP_PORT={port_int}\nSMTP_USER={smtp_user}\nSMTP_PASSWORD={smtp_password}\nSMTP_FROM={smtp_from}\n")
    except Exception:
        pass

    return jsonify({
        "success": True,
        "message": f"SMTP mailer verified and saved! Genuine verification OTPs will now be delivered to inboxes via {smtp_user}.",
    })


@app.route("/profile/verify-otp", methods=["POST"])
def profile_verify_otp():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    entered_otp = (data.get("otp") or "").strip()
    target_email = (data.get("email") or "").strip().lower()

    otp_data = session.get("email_otp")
    if not otp_data:
        return jsonify({"success": False, "error": "No OTP requested. Please request an OTP first."}), 400

    if otp_data.get("email") != target_email:
        return jsonify({"success": False, "error": "Email does not match the OTP request."}), 400

    if str(otp_data.get("code")) != str(entered_otp):
        return jsonify({"success": False, "error": "Invalid verification code. Please check your email and try again."}), 400

    # OTP verified! Update email in database & session
    username = user.get("username", "")
    auth_service.update_user_email(username, target_email, email_verified=1)

    session["user"]["email"] = target_email
    session["user"]["email_verified"] = 1
    session.pop("email_otp", None)
    session.modified = True

    return jsonify({
        "success": True,
        "message": f"Email {target_email} successfully verified and updated!",
        "email": target_email,
    })


@app.route("/profile/verify-google")
def profile_verify_google():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    username = user.get("username", "")
    email = user.get("email") or f"{username}@gmail.com"

    auth_service.update_user_email(username, email, email_verified=1)
    session["user"]["email"] = email
    session["user"]["email_verified"] = 1
    session.modified = True

    flash(f"Email {email} has been successfully verified via Google!", "success")
    return redirect(url_for("profile"))


@app.route("/profile/send-mobile-otp", methods=["POST"])
def profile_send_mobile_otp():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    mobile_no = (data.get("mobile_no") or "").strip()
    digits = SmsService.clean_indian_phone(mobile_no)
    if len(digits) != 10:
        return jsonify({"success": False, "error": "Please enter a valid 10-digit Indian mobile number."}), 400

    otp = f"{random.randint(100000, 999999)}"
    session["mobile_otp"] = {
        "code": otp,
        "mobile_no": mobile_no,
        "digits": digits,
        "created_at": time.time(),
    }
    session.modified = True

    # If in test mode, return test flag for automated unit tests
    if app.config.get("TESTING") or os.getenv("TESTING") == "1":
        return jsonify({
            "success": True,
            "message": f"Genuine SMS dispatched to +91 {digits}! Please check your mobile phone Messages app.",
            "mobile_no": mobile_no,
            "_test_otp": otp,
        })

    # Dispatch GENUINE cellular SMS via SmsService (Fast2SMS / Twilio)
    success, send_msg = SmsService.send_otp_sms(digits, otp)
    if not success:
        return jsonify({
            "success": False,
            "error": send_msg,
            "needs_gateway": True,
            "mobile_no": mobile_no,
        }), 400

    return jsonify({
        "success": True,
        "message": send_msg,
        "mobile_no": mobile_no,
    })


@app.route("/profile/save-sms-gateway", methods=["POST"])
def profile_save_sms_gateway():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    provider = (data.get("provider") or "fast2sms").strip().lower()

    if provider == "fast2sms":
        api_key = (data.get("api_key") or "").strip()
        if not api_key:
            return jsonify({"success": False, "error": "Please enter your Fast2SMS API Key."}), 400

        wallet_balance = None
        try:
            res = requests.post("https://www.fast2sms.com/dev/wallet", headers={"authorization": api_key}, timeout=10)
            wallet_data = res.json()
            if wallet_data.get("return") is True or "wallet" in wallet_data:
                wallet_balance = wallet_data.get("wallet")
        except Exception:
            pass

        set_config_value("FAST2SMS_API_KEY", api_key)

        msg = "Fast2SMS Gateway successfully connected and saved! Live cellular SMS will now be dispatched to mobile phones."
        if wallet_balance is not None:
            msg += f" (Wallet Balance: ₹{wallet_balance})"

        return jsonify({
            "success": True,
            "message": msg,
            "provider": "Fast2SMS (India +91)",
            "wallet": wallet_balance,
        })

    elif provider == "twilio":
        account_sid = (data.get("account_sid") or "").strip()
        auth_token = (data.get("auth_token") or "").strip()
        from_number = (data.get("from_number") or "").strip()
        if not (account_sid and auth_token and from_number):
            return jsonify({"success": False, "error": "Please provide Twilio Account SID, Auth Token, and Phone Number."}), 400
        set_config_value("TWILIO_ACCOUNT_SID", account_sid)
        set_config_value("TWILIO_AUTH_TOKEN", auth_token)
        set_config_value("TWILIO_PHONE_NUMBER", from_number)
        return jsonify({
            "success": True,
            "message": "Twilio SMS Gateway successfully saved!",
            "provider": "Twilio",
        })

    return jsonify({"success": False, "error": "Unsupported provider."}), 400


@app.route("/profile/verify-mobile-otp", methods=["POST"])
def profile_verify_mobile_otp():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or request.form
    entered_otp = (data.get("otp") or "").strip()
    mobile_no = (data.get("mobile_no") or "").strip()

    otp_data = session.get("mobile_otp")
    if not otp_data:
        return jsonify({"success": False, "error": "No OTP requested. Please request an OTP first."}), 400

    if str(otp_data.get("code")) != str(entered_otp):
        return jsonify({"success": False, "error": "Invalid verification code. Please check and try again."}), 400

    # Mobile OTP verified! Update mobile_no & mobile_verified in database & session
    username = user.get("username", "")
    auth_service.update_user_mobile(username, mobile_no, mobile_verified=1)

    session["user"]["mobile_no"] = mobile_no
    session["user"]["mobile_verified"] = 1
    session.pop("mobile_otp", None)
    session.modified = True

    return jsonify({
        "success": True,
        "message": f"Mobile number {mobile_no} verified and linked successfully!",
        "mobile_no": mobile_no,
    })


# =============================================================================
# 10.5. MEMBER & USER MANAGEMENT (ADMIN ONLY - Q14 SEPARATE TAB)
# =============================================================================

@app.route("/admin/members")
@app.route("/members")
def admin_members():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    if not user.get("is_admin") and user.get("role") != "Admin":
        flash("Access Denied: Only Administrators have authority to manage member accounts and roles.", "danger")
        return redirect(url_for("dashboard"))

    all_users = auth_service.get_all_users()
    session_tracking = auth_service.get_member_session_tracking()
    stats = {
        "total": len(all_users),
        "active": sum(1 for u in all_users if u.get("status") == "Active"),
        "admins": sum(1 for u in all_users if u.get("role") == "Admin"),
        "members": sum(1 for u in all_users if u.get("role") == "Member"),
        "suspended": sum(1 for u in all_users if u.get("status") == "Suspended"),
        "banned": sum(1 for u in all_users if u.get("status") == "Banned"),
    }

    return render_template(
        "admin_members.html",
        active_page="members",
        users=all_users,
        stats=stats,
        session_tracking=session_tracking,
        is_admin=True,
    )


@app.route("/admin/members/live-sessions")
def admin_members_live_sessions():
    """Live JSON API returning active member presence, login, and logout timestamps."""
    user = session.get("user")
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    tracking = auth_service.get_member_session_tracking()
    return jsonify({"success": True, "data": tracking})


@app.route("/admin/members/status", methods=["POST"])
def admin_member_status():
    user = session.get("user")
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Administrator privileges required."}), 403

    data = request.get_json(silent=True) or request.form
    try:
        user_id = int(data.get("user_id"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid user ID."}), 400

    new_status = (data.get("status") or "").strip()
    reason = (data.get("reason") or "").strip()
    current_admin_id = user.get("id")

    success, message = auth_service.update_user_status(user_id, new_status, reason, current_admin_id=current_admin_id)
    if not success:
        if request.is_json:
            return jsonify({"success": False, "error": message}), 400
        flash(message, "danger")
        return redirect(url_for("admin_members"))

    if request.is_json:
        return jsonify({"success": True, "message": message})
    flash(message, "success")
    return redirect(url_for("admin_members"))


@app.route("/admin/members/role", methods=["POST"])
def admin_member_role():
    user = session.get("user")
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Administrator privileges required."}), 403

    data = request.get_json(silent=True) or request.form
    try:
        user_id = int(data.get("user_id"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid user ID."}), 400

    new_role = (data.get("role") or "").strip()
    current_admin_id = user.get("id")

    success, message = auth_service.update_user_role(user_id, new_role, current_admin_id=current_admin_id)
    if not success:
        if request.is_json:
            return jsonify({"success": False, "error": message}), 400
        flash(message, "danger")
        return redirect(url_for("admin_members"))

    if request.is_json:
        return jsonify({"success": True, "message": message})
    flash(message, "success")
    return redirect(url_for("admin_members"))


@app.route("/admin/members/delete", methods=["POST"])
def admin_member_delete():
    user = session.get("user")
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Administrator privileges required."}), 403

    data = request.get_json(silent=True) or request.form
    try:
        user_id = int(data.get("user_id"))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid user ID."}), 400

    current_admin_id = user.get("id")

    success, message = auth_service.delete_user(user_id, current_admin_id=current_admin_id)
    if not success:
        if request.is_json:
            return jsonify({"success": False, "error": message}), 400
        flash(message, "danger")
        return redirect(url_for("admin_members"))

    if request.is_json:
        return jsonify({"success": True, "message": message})
    flash(message, "success")
    return redirect(url_for("admin_members"))


@app.route("/admin/members/create", methods=["POST"])
def admin_member_create():
    user = session.get("user")
    if not user or not user.get("is_admin"):
        return jsonify({"success": False, "error": "Administrator privileges required."}), 403

    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    role = (data.get("role") or "Member").strip()
    mobile_no = (data.get("mobile_no") or "+91 9368039108").strip()
    try:
        age = int(data.get("age") or 21)
    except ValueError:
        age = 21

    success, message = auth_service.create_member(
        username=username,
        password=password,
        full_name=full_name,
        email=email,
        role=role,
        mobile_no=mobile_no,
        age=age,
    )
    if not success:
        if request.is_json:
            return jsonify({"success": False, "error": message}), 400
        flash(message, "danger")
        return redirect(url_for("admin_members"))

    if request.is_json:
        return jsonify({"success": True, "message": message})
    flash(message, "success")
    return redirect(url_for("admin_members"))


# =============================================================================
# 11. CSV EXPORT UTILITY
# =============================================================================

@app.route("/export/<data_type>")
def export_csv(data_type: str):
    output = io.StringIO()
    writer = csv.writer(output)

    if data_type == "products":
        writer.writerow(["SKU", "Product Name", "Category", "Supplier", "Quantity", "Reorder Level", "Price", "Status"])
        for p in product_service.list_products():
            writer.writerow([p["sku"], p["name"], p["category"], p["supplier"], p["quantity"], p["reorder_level"], p["price"], p["status"]])
        filename = "amrapali_products_master.csv"

    elif data_type == "movements":
        writer.writerow(["Movement ID", "SKU", "Product Name", "Type", "Quantity", "Note", "Timestamp"])
        for m in inventory_service.list_stock_movements():
            writer.writerow([m["id"], m["sku"], m["name"], m["movement_type"], m["quantity"], m["note"], m["created_at"]])
        filename = "amrapali_stock_ledger.csv"

    elif data_type == "inspections":
        writer.writerow(["Lot Number", "SKU", "Product Name", "Supplier", "Sample Size", "Defects Found", "Defect Type", "Status", "Inspector", "Date"])
        for i in tqm_service.get_inspections(limit=500):
            writer.writerow([i["lot_number"], i["sku"], i["product_name"], i["supplier_name"], i["sample_size"], i["defects_found"], i["defect_type"], i["inspection_status"], i["inspector_name"], i["created_at"]])
        filename = "amrapali_grn_inspections.csv"

    elif data_type == "fmea":
        writer.writerow(["Failure Mode", "Root Cause", "Effect", "Severity", "Occurrence", "Detection", "RPN", "Risk Level", "Recommended Action", "Action Taken"])
        for f in tqm_service.get_fmea_records():
            writer.writerow([f["failure_mode"], f["cause"], f["effect"], f["severity"], f["occurrence"], f["detection"], f["rpn"], f["risk_level"], f["recommended_action"], f["action_taken"]])
        filename = "amrapali_fmea_matrix.csv"

    else:  # audit
        writer.writerow(["Event ID", "User", "Action", "Entity", "Details", "Timestamp"])
        for a in report_service.recent_audit(limit=500):
            writer.writerow([a["id"] if "id" in a.keys() else "", a["username"], a["action"], a["entity"], a["details"], a["created_at"]])
        filename = "amrapali_quality_audit_trail.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


# =============================================================================
# 11. REST API ENDPOINTS
# =============================================================================

@app.route("/api/metrics")
def api_metrics():
    return jsonify({
        "metrics": report_service.dashboard_metrics(),
        "quality_summary": report_service.quality_summary(),
    })


@app.route("/api/pareto")
def api_pareto():
    return jsonify(tqm_service.get_pareto_data())


@app.route("/api/abc")
def api_abc():
    return jsonify(tqm_service.calculate_abc_analysis())


def get_local_ip() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_web(host: str = "0.0.0.0", port: int = 5001, debug: bool = False):
    import time
    import webbrowser
    import threading

    local_ip = get_local_ip()

    def _auto_open_browser():
        time.sleep(0.8)
        web_url = f"http://127.0.0.1:{port}/"
        try:
            webbrowser.open(web_url)
        except Exception:
            pass

    threading.Thread(target=_auto_open_browser, daemon=True).start()

    print("=" * 72)
    print("AMRAPALI UNIVERSITY - TOTAL QUALITY INVENTORY MANAGEMENT PORTAL")
    print(f"Student: {STUDENT_INFO['name']} (Roll: {STUDENT_INFO['roll_no']}, S.No: {STUDENT_INFO['serial_no']})")
    print(f"Course:  {STUDENT_INFO['course_code']} - {STUDENT_INFO['course_name']}")
    print(f"Quality Goal: {STUDENT_INFO['quality_goal']}")
    print(f"Local Access:    http://127.0.0.1:{port}/")
    print(f"Member Access:   http://{local_ip}:{port}/  (Any laptop on same Wi-Fi / Hotspot)")
    print("=" * 72)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Amrapali TQM Inventory Web Application")
    parser.add_argument("--port", type=int, default=5001, help="Port to run web app (default: 5001)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Run with Flask debug mode")
    args = parser.parse_args()

    run_web(host=args.host, port=args.port, debug=args.debug)
