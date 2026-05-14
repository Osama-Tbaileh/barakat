import frappe
import requests
from urllib.parse import urlparse as _urlparse

no_cache = True


def get_context(context):
    token = frappe.form_dict.get("token")
    if not token:
        frappe.throw("Missing token", frappe.ValidationError)

    _login_with_token(token)

    frappe.local.flags.redirect_location = "/desk"
    raise frappe.Redirect


def _login_with_token(token):
    master_url = frappe.conf.get("master_url")
    api_key = frappe.conf.get("master_api_key")
    api_secret = frappe.conf.get("master_api_secret")

    if not master_url or not api_key or not api_secret:
        frappe.throw(
            "This site is not configured to authenticate with a master site.",
            frappe.ValidationError,
        )

    site_url = frappe.conf.get("site_url") or frappe.local.site
    master_host = (
        frappe.conf.get("master_hostname")
        or _urlparse(master_url).hostname
        or "master.localhost"
    )

    try:
        resp = requests.post(
            f"{master_url}/api/method/barakat_master.api.verify_client_token",
            headers={
                "Authorization": f"token {api_key}:{api_secret}",
                "Content-Type": "application/json",
                "Host": master_host,
            },
            json={"token": token, "site_url": site_url},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        body = e.response.text if e.response is not None else str(e)
        frappe.throw(f"Token verification failed: {body}", frappe.AuthenticationError)
    except Exception as e:
        frappe.throw(
            f"Could not reach master site to verify token: {e}",
            frappe.AuthenticationError,
        )

    data = resp.json()
    message = data.get("message") or {}
    user_email = message.get("user") if isinstance(message, dict) else None

    if not user_email:
        frappe.throw(
            "Invalid response from master site — no user returned.",
            frappe.AuthenticationError,
        )

    user_exists = frappe.db.sql(
        "SELECT `name` FROM `tabUser` WHERE `name` = %s LIMIT 1", (user_email,)
    )
    if not user_exists:
        user_doc = frappe.new_doc("User")
        user_doc.email = user_email
        user_doc.first_name = user_email.split("@")[0]
        user_doc.send_welcome_email = 0
        user_doc.user_type = "System User"
        user_doc.insert(ignore_permissions=True)
        frappe.db.commit()

    login_manager = frappe.auth.LoginManager()
    login_manager.user = user_email
    login_manager.post_login()
