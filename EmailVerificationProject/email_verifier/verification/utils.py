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
    # Your friend's API URL
    api_url = "http://cmailapi-env.eba-vg3mwdtr.us-east-1.elasticbeanstalk.com/api/send/"
    
    # We use 'data' instead of 'json' because your friend's API 
    # uses Form Data (-F in curl) rather than a JSON body.
    payload = {
        "to_email": email,
        "subject": "Verify Your Email - Action Required",
        "message": f"Please verify your email by clicking the link: {verification_link}",
        "from_name": "CloudMail AWS",
        "reply_to": "admin@cloudmail.com"
    }
    
    try:
        # Note: We use data=payload for multipart/form-data compatibility
        response = requests.post(api_url, data=payload, timeout=10)
        
        # Check if the API accepted it (status codes in 200 range)
        if response.status_code == 200 or response.status_code == 201:
            return True
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"Connection Error: {e}")
        return False
        
# ✅ Typo Detection
def get_domain_suggestion(domain):
    domain = domain.lower().strip()
    # Find the closest match from COMMON_DOMAINS
    # cutoff=0.8 means it must be 80% similar to be suggested
    matches = difflib.get_close_matches(domain, COMMON_DOMAINS, n=1, cutoff=0.8)
    
    if matches and matches[0] != domain:
        return matches[0]  # Returns 'gmail.com' for 'gmil.com'
    return None