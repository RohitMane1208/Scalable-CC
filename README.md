# Email Verification API

A scalable, RESTful Email Verification API built with Django and deployed on AWS Elastic Beanstalk. It validates email addresses through syntax checks, MX record lookups, and disposable-domain detection, then sends a verification link to confirm real ownership.

Infrastructure Note: This API is served via AWS Elastic Beanstalk and is fully TLS-capable. CORS is enabled, so it can be called from any frontend.

The API is currently hosted at: http://email-api-env.eba-i8pnmynr.us-east-1.elasticbeanstalk.com

---

## Features

- Email syntax validation
- MX (Mail Exchange) DNS record check
- Disposable/temporary email domain detection
- Role-based email detection (admin@, support@, etc.)
- UUID token-based email ownership verification
- Verification status lookup
- JSON and HTML form request support

---

## API Endpoints

### 1. POST /api/email/ — Verify an Email

Validates the email and sends a verification link to the inbox if it passes all checks.

Method: POST
Content-Type: application/json or multipart/form-data

Parameters:

    email (string, required) — The email address to verify.

Responses:

    200 — {"result": "Verification email sent."}
    200 — {"result": "Email already verified."}
    400 — {"result": "Invalid Email Format"}
    400 — {"result": "Email failed authenticity checks."}
    500 — {"result": "Email service failed."}

**Example — cURL**

```bash
curl -X POST http://email-api-env.eba-i8pnmynr.us-east-1.elasticbeanstalk.com/api/email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

**Example — Python**

```python
import requests

response = requests.post(
    "http://email-api-env.eba-i8pnmynr.us-east-1.elasticbeanstalk.com/api/email/",
    json={"email": "user@example.com"}
)
print(response.json())
```

**Example — JavaScript (fetch)**

```javascript
const formData = new FormData();
formData.append("email", "user@example.com");

fetch("http://email-api-env.eba-i8pnmynr.us-east-1.elasticbeanstalk.com/api/email/", {
    method: "POST",
    body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error("Error:", error));
```

---

### 2. GET /api/verify/\<token\>/ — Confirm Ownership (via Email Link)

This endpoint is called automatically when the user clicks the verification link in their email. It marks the email as verified in the database.

Note: This is handled automatically — you do not need to call this manually.

URL: GET /api/verify/{uuid-token}/

Response: Returns an HTML page confirming verification success or indicating it was already verified.

---

### 3. GET /api/status/ — Check Verification Status

Check whether an email address has already been verified.

Method: GET
Query Parameter:

    email (string, required) — The email address to look up.

Responses:

    200 — {"email": "...", "is_verified": true}
    200 — {"email": "...", "is_verified": false}
    400 — {"error": "Email required"}
    404 — {"is_verified": false, "result": "Not found"}

**Example — cURL**

```bash
curl "http://email-api-env.eba-i8pnmynr.us-east-1.elasticbeanstalk.com/api/status/?email=user@example.com"
```

**Example — Python**

```python
import requests

response = requests.get(
    "http://email-api-env.eba-i8pnmynr.us-east-1.elasticbeanstalk.com/api/status/",
    params={"email": "user@example.com"}
)
print(response.json())
```

---

## Validation Logic

When you POST to /api/email/, the following checks run in order:

1. Syntax check — email must be RFC-compliant (via email-validator)
2. Disposable domain check — domains like mailinator.com, tempmail.com are rejected
3. MX record check — confirms the domain actually receives email (via DNS lookup)
4. Role-based detection — flags addresses like admin@, support@, info@ (does not block, informational)

If checks 1 or 2 fail, a 400 response is returned and no email is sent.

---

## Running Locally

Prerequisites:

- Python 3.10+
- pip

Setup:

```bash
git clone https://github.com/RohitMane1208/Scalable-CC.git
cd Scalable-CC/email_verifier

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

The API will be available at http://127.0.0.1:8000/

---

## Tech Stack

- Framework: Django 4.2 + Django REST Framework
- Server: Gunicorn
- Database: SQLite (dev) / configurable
- DNS Lookup: dnspython
- Email Validation: email-validator
- Email Sending: AWS API Gateway
- Deployment: AWS Elastic Beanstalk
- CORS: django-cors-headers
