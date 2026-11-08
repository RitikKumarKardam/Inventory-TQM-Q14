"""Web application, role-based authentication, and TQM integration test suite."""

from web_app import app
from services.tqm_service import TQMService


def test_login_and_roles():
    client = app.test_client()

    # 1. Unauthenticated users are redirected to /login
    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]

    # 2. Login page loads successfully
    res = client.get("/login")
    assert res.status_code == 200

    # 3. Invalid credentials fail
    res = client.post("/login", data={"username": "wrong", "password": "bad", "role_hint": "Admin"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Invalid User ID" in res.data.decode("utf-8")

    # 4. Role Differentiation Test: Admin account blocked on Member login tab
    res_block_admin = client.post("/login", data={"username": "admin", "password": "admin123", "role_hint": "Member"}, follow_redirects=True)
    assert res_block_admin.status_code == 200
    assert "Access Denied" in res_block_admin.data.decode("utf-8")
    assert "Administrator account" in res_block_admin.data.decode("utf-8")

    # 5. Role Differentiation Test: Member account blocked on Admin login tab
    res_block_member = client.post("/login", data={"username": "member", "password": "member123", "role_hint": "Admin"}, follow_redirects=True)
    assert res_block_member.status_code == 200
    assert "Access Denied" in res_block_member.data.decode("utf-8")
    assert "registered as a Member" in res_block_member.data.decode("utf-8")

    # 6. Member login succeeds on Member tab
    res = client.post("/login", data={"username": "member", "password": "member123", "role_hint": "Member"}, follow_redirects=True)
    assert res.status_code == 200
    assert "MEMBER" in res.data.decode("utf-8")
    assert "GMAIL" not in res.data.decode("utf-8")
    assert "GMAIL" not in res.data.decode("utf-8")

    # 7. Admin login succeeds on Admin tab
    client.get("/logout")
    res = client.post("/login", data={"username": "admin", "password": "admin123", "role_hint": "Admin"}, follow_redirects=True)
    assert res.status_code == 200
    assert "ADMIN" in res.data.decode("utf-8")
    assert "GMAIL" not in res.data.decode("utf-8")


def test_authenticated_web_routes():
    client = app.test_client()
    # Sign in as Admin
    client.post("/login", data={"username": "admin", "password": "admin123"})

    routes = [
        "/",
        "/products",
        "/stock",
        "/suppliers",
        "/inspections",
        "/tqm",
        "/calculators",
        "/reports",
        "/viva-guide",
        "/profile",
        "/api/metrics",
        "/api/pareto",
        "/api/abc",
        "/export/products",
        "/export/movements",
        "/export/fmea",
        "/export/audit",
    ]
    for r in routes:
        res = client.get(r)
        assert res.status_code == 200, f"Route {r} failed with status {res.status_code}"


def test_q14_navigation_compliance():
    tqm = TQMService("test_auditor")
    scorecard = tqm.get_navigation_audit_scorecard()
    assert scorecard["overall_score"] == "100%"
    assert len(scorecard["targets"]) == 5
    for target in scorecard["targets"]:
        assert "PASSED" in target["status"]


def test_abc_analysis_calculation():
    tqm = TQMService("test_auditor")
    abc = tqm.calculate_abc_analysis()
    assert abc["total_value"] > 0
    assert "A" in abc["summary"]
    assert "B" in abc["summary"]
    assert "C" in abc["summary"]
    assert len(abc["products"]) > 0


def test_eoq_calculation():
    result = TQMService.calculate_eoq(
        annual_demand=1200,
        ordering_cost=250,
        holding_cost_unit=15,
        lead_time_days=7,
        service_level_pct=95.0,
    )
    assert result["eoq"] == 200
    assert result["reorder_point"] > 0
    assert result["safety_stock"] > 0


def test_google_login():
    client = app.test_client()

    # 1. Google Auth Page Loads
    res = client.get("/login/google")
    assert res.status_code == 200
    assert "Sign in" in res.data.decode("utf-8")
    assert "Email or phone" in res.data.decode("utf-8")

    # 2. Login with student Ritik Kumar's Gmail
    res = client.post(
        "/login/google",
        data={"email": "ritikkumar2520301005@gmail.com", "full_name": "Ritik Kumar"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    assert "ritikkumar2520301005@gmail.com" in body
    assert "MEMBER" in body

    # 3. Login with Admin Gmail
    client.get("/logout")
    res = client.post(
        "/login/google",
        data={"email": "admin@amrapali.ac.in", "full_name": "Faculty Administrator"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    assert "admin@amrapali.ac.in" in body
    assert "ADMIN" in body

    # 4. Login with student's personal Gmail (ritikkumarhempur5@gmail.com)
    client.get("/logout")
    res = client.post(
        "/login/google",
        data={"email": "ritikkumarhempur5@gmail.com", "full_name": "Ritik Kumar"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    assert "ritikkumarhempur5@gmail.com" in body
    assert "MEMBER" in body

    # 5. Strict rejection: Unregistered Gmail address is NOT allowed to sign in
    client.get("/logout")
    res = client.post(
        "/login/google",
        data={"email": "unregistered.stranger@gmail.com"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    assert "No registered account found" in body

    # 6. Direct Login: Sign in directly using Gmail as Username + Password
    client.get("/logout")
    res = client.post(
        "/login",
        data={"username": "ritikkumarhempur5@gmail.com", "password": "ritik123", "role_hint": "Member"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "MEMBER" in res.data.decode("utf-8")
    assert "GMAIL" not in res.data.decode("utf-8")

    # 7. OAuth Callback route handles missing/cancelled authorization safely
    client.get("/logout")
    res = client.get("/login/google/callback?error=access_denied", follow_redirects=True)
    assert res.status_code == 200
    assert "cancelled or rejected" in res.data.decode("utf-8")


def test_captcha_security():
    client = app.test_client()

    # 1. /captcha.svg returns SVG image
    res = client.get("/captcha.svg")
    assert res.status_code == 200
    assert "image/svg+xml" in res.headers["Content-Type"]
    assert "<svg" in res.data.decode("utf-8")

    # 2. Invalid CAPTCHA is rejected
    with client.session_transaction() as sess:
        sess["captcha"] = "SEC88"

    res = client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "captcha": "WRONG1", "role_hint": "Admin"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Invalid CAPTCHA code: Please enter the correct characters shown in the security box." in res.data.decode("utf-8")

    # 3. Valid CAPTCHA succeeds
    with client.session_transaction() as sess:
        sess["captcha"] = "SEC88"

    res = client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "captcha": "SEC88", "role_hint": "Admin"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "ADMIN" in res.data.decode("utf-8")


def test_user_profile_and_otp():
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Login as Member
    with client.session_transaction() as sess:
        sess["captcha"] = "SEC99"
    client.post(
        "/login",
        data={"username": "member", "password": "member123", "captcha": "SEC99", "role_hint": "Member"},
        follow_redirects=True,
    )

    # 2. GET /profile as Member: Role section is READ-ONLY for members
    res = client.get("/profile")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "User Profile &amp; Account Customization" in html
    assert "Full Name" in html
    assert "Mobile Number" in html
    assert "Age" in html
    assert "Role in This System" in html
    assert "Read-Only for Members" in html
    assert "System roles can only be decided and assigned by the" in html

    # 3. Security Test: Member tries to escalate role to Admin -> SERVER REJECTS ROLE CHANGE
    res_post = client.post(
        "/profile",
        data={
            "full_name": "Ritik Kumar Kardam",
            "age": "22",
            "mobile_no": "+91 9999888877",
            "role": "Admin",  # Member attempts to self-assign Admin
        },
        follow_redirects=True,
    )
    assert res_post.status_code == 200
    assert "Profile information updated successfully!" in res_post.data.decode("utf-8")
    with client.session_transaction() as sess:
        # STRICTLY REMAINS MEMBER! Members cannot decide or change their own role.
        assert sess["user"]["role"] == "Member"
        assert sess["user"]["is_admin"] is False

    # 4. OTP Email Verification Flow: Request Genuine OTP
    res_otp_send = client.post(
        "/profile/send-otp",
        json={"email": "verified.ritik@amrapali.ac.in"},
    )
    assert res_otp_send.status_code == 200
    send_data = res_otp_send.get_json()
    assert send_data["success"] is True
    assert "otp" not in send_data  # Public JSON response contains NO spoof OTP!
    generated_otp = send_data["_test_otp"]  # Retrieved strictly from unit test harness

    # 5. Verify with WRONG OTP fails
    res_bad_verify = client.post(
        "/profile/verify-otp",
        json={"email": "verified.ritik@amrapali.ac.in", "otp": "000000"},
    )
    assert res_bad_verify.status_code == 400
    assert res_bad_verify.get_json()["success"] is False

    # 6. Verify with CORRECT OTP succeeds
    res_good_verify = client.post(
        "/profile/verify-otp",
        json={"email": "verified.ritik@amrapali.ac.in", "otp": generated_otp},
    )
    assert res_good_verify.status_code == 200
    good_data = res_good_verify.get_json()
    assert good_data["success"] is True
    assert "verified.ritik@amrapali.ac.in" in good_data["message"]

    # 7. Mobile Number Genuine OTP Verification Flow
    res_mob_send = client.post(
        "/profile/send-mobile-otp",
        json={"mobile_no": "9368039108"},
    )
    assert res_mob_send.status_code == 200
    mob_data = res_mob_send.get_json()
    assert mob_data["success"] is True
    assert "otp" not in mob_data  # Public response never exposes spoof OTP
    mob_otp = mob_data["_test_otp"]

    # Save SMS Gateway endpoint test
    res_gw = client.post(
        "/profile/save-sms-gateway",
        json={"provider": "fast2sms", "api_key": "test_fast2sms_api_key_12345"},
    )
    assert res_gw.status_code == 200
    assert res_gw.get_json()["success"] is True

    # Verify mobile with wrong OTP fails
    res_bad_mob = client.post(
        "/profile/verify-mobile-otp",
        json={"mobile_no": "9368039108", "otp": "000000"},
    )
    assert res_bad_mob.status_code == 400
    assert res_bad_mob.get_json()["success"] is False

    # Verify mobile with correct OTP succeeds
    res_good_mob = client.post(
        "/profile/verify-mobile-otp",
        json={"mobile_no": "9368039108", "otp": mob_otp},
    )
    assert res_good_mob.status_code == 200
    assert res_good_mob.get_json()["success"] is True
    assert "9368039108" in res_good_mob.get_json()["message"]

    # 8. Admin Authority Test: Admin user CAN decide and change role
    client.get("/logout")
    with client.session_transaction() as sess:
        sess["captcha"] = "SEC88"
    client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "captcha": "SEC88", "role_hint": "Admin"},
        follow_redirects=True,
    )
    res_admin_profile = client.get("/profile")
    assert res_admin_profile.status_code == 200
    assert "Admin Authority Active" in res_admin_profile.data.decode("utf-8")



