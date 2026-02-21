import dns.resolver
from email_validator import validate_email, EmailNotValidError
import difflib
import smtplib
import socket
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
    "10minutemail.com"
]


# =========================================================
# 📌 3️⃣ Role-based prefixes
# =========================================================
ROLE_PREFIXES = [
    "admin",
    "info",
    "support",
    "contact",
    "sales"
]


# =========================================================
# ✅ Syntax validation
# =========================================================
def validate_syntax(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


# =========================================================
# ✅ MX record check
# =========================================================
def check_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except (dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.Timeout,
            dns.exception.DNSException):
        return False


# =========================================================
# ✅ Disposable detection
# =========================================================
def check_disposable(domain):
    return domain.lower() in DISPOSABLE_DOMAINS


# =========================================================
# ✅ Role-based detection
# =========================================================
def check_role_based(email):
    prefix = email.split("@")[0].lower()
    return prefix in ROLE_PREFIXES


# =========================================================
# ✅ Typo suggestion
# =========================================================
def suggest_domain(domain):
    suggestion = difflib.get_close_matches(
        domain,
        COMMON_DOMAINS,
        n=1,
        cutoff=0.7
    )

    if suggestion and suggestion[0] != domain:
        return suggestion[0]

    return None


# =========================================================
# ✅ Confidence Score
# =========================================================
def calculate_score(format_valid, mx_valid, disposable, role_based):
    score = 0

    if format_valid:
        score += 30

    if mx_valid:
        score += 30

    if not disposable:
        score += 20

    if not role_based:
        score += 20

    return score


# =========================================================
# ✅ SMTP Mailbox Check
# =========================================================
def smtp_check(email):
    domain = email.split("@")[1]

    try:
        # Get MX record
        records = dns.resolver.resolve(domain, "MX")
        mx_record = str(records[0].exchange).rstrip(".")

        # Connect to mail server
        server = smtplib.SMTP(mx_record, 25, timeout=5)
        server.set_debuglevel(0)

        server.helo("example.com")
        server.mail("test@example.com")

        code, _ = server.rcpt(email)
        server.quit()

        # 250 = mailbox accepted
        if code == 250:
            return True
        else:
            return False

    except (
        smtplib.SMTPException,
        socket.error,
        dns.resolver.NoAnswer,
        dns.resolver.NXDOMAIN,
        dns.resolver.Timeout,
        dns.exception.DNSException
    ):
        return False
    

def send_verification_email(email, verification_link):
    api_url = "https://your-friends-api.com/send"  # Replace with real API

    payload = {
        "to": email,
        "subject": "Verify Your Email",
        "body": f"""
Hello,

Please verify your email by clicking the link below:

{verification_link}

If you did not request this, ignore this email.
"""
    }

    try:
        response = requests.post(api_url, json=payload, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False
