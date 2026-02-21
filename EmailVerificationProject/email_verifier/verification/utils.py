import dns.resolver
from email_validator import validate_email, EmailNotValidError
import difflib
import requests

# =========================================================
# 📌 1️⃣ Common trusted domains
# =========================================================
COMMON_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com"
]

# =========================================================
# 📌 2️⃣ Disposable domains sample
# =========================================================
DISPOSABLE_DOMAINS = [
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com"
]

# =========================================================
# 📌 3️⃣ Role-based prefixes
# =========================================================
ROLE_PREFIXES = [
    "admin",
    "info",
    "support",
    "contact",
    "sales",
    "help",
    "billing"
]

# ✅ Syntax validation
def validate_syntax(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

# ✅ MX record check
def check_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except (dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.Timeout,
            dns.exception.DNSException):
        return False

# ✅ Disposable detection (Returns True if it IS disposable)
def check_disposable(domain):
    return domain.lower().strip() in DISPOSABLE_DOMAINS

# ✅ Role-based detection (Returns True if it IS role-based)
def check_role_based(email):
    prefix = email.split("@")[0].lower().strip()
    return prefix in ROLE_PREFIXES

def send_verification_email(email, verification_link):
    api_url = "https://your-friends-api.com/send" 
    payload = {
        "to": email,
        "subject": "Verify Your Email",
        "body": f"Please verify your email: {verification_link}"
    }
    try:
        response = requests.post(api_url, json=payload, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False