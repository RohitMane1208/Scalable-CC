import dns.resolver
from email_validator import validate_email, EmailNotValidError
import difflib
import requests

# Constants
COMMON_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"]
DISPOSABLE_DOMAINS = ["mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com"]
ROLE_PREFIXES = ["admin", "info", "support", "contact", "sales", "help", "billing"]

def validate_syntax(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def check_mx_record(domain):
    try:
        return len(dns.resolver.resolve(domain, "MX")) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout, dns.exception.DNSException):
        return False

def check_disposable(domain):
    return domain.lower().strip() in DISPOSABLE_DOMAINS

def check_role_based(email):
    return email.split("@")[0].lower().strip() in ROLE_PREFIXES

def get_domain_suggestion(domain):
    domain = domain.lower().strip()
    matches = difflib.get_close_matches(domain, COMMON_DOMAINS, n=1, cutoff=0.8)
    return matches[0] if matches and matches[0] != domain else None

def send_verification_email(email, verification_link):
    api_url = "https://dfz5aavjml.execute-api.us-east-1.amazonaws.com/prod/api/send/"
    payload = {
        "to_email": email,
        "subject": "Verify Your Email - Action Required",
        "message": f"Please verify your email by clicking the link: {verification_link}",
        "from_name": "CloudMail AWS",
        "reply_to": "admin@cloudmail.com"
    }
    try:
        response = requests.post(api_url, data=payload, timeout=10)
        return response.status_code in [200, 201]
    except requests.RequestException:
        return False