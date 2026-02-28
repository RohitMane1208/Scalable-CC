import json
import uuid
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .models import EmailVerification
from .utils import (
    send_verification_email, validate_syntax, check_mx_record,
    check_disposable, check_role_based, get_domain_suggestion, COMMON_DOMAINS
)

@csrf_exempt
def verify_email(request):
    # 1. Standardize Email Extraction
    if request.method == "POST":
        if request.content_type == 'application/json':
            data = json.loads(request.body) if request.body else {}
            email = data.get("email", "").strip()
        else:
            email = request.POST.get("email", "").strip()

        if not email or "@" not in email:
            return _render_or_json(request, {"result": "❌ Invalid Email Format"}, {})

        # 2. Validation Logic
        domain = email.split("@")[1].lower()
        results = {
            "format_valid": validate_syntax(email),
            "mx_record_exists": check_mx_record(domain),
            "disposable_email": check_disposable(domain),
            "role_based_email": check_role_based(email),
        }

        # 3. Metrics and Scoring
        score = (30 if results["format_valid"] else 0) + \
                (40 if results["mx_record_exists"] else 0) + \
                (15 if not results["disposable_email"] else 0) + \
                (15 if not results["role_based_email"] else 0)
        
        if results["disposable_email"]: score -= 50
        
        details = {
            **results,
            "email": email,
            "is_common_domain": domain in COMMON_DOMAINS,
            "suggestion": get_domain_suggestion(domain),
            "confidence_score": f"{max(0, min(100, score))}%"
        }

        # 4. Verification Link Logic
        if all([results["format_valid"], results["mx_record_exists"], 
                not results["disposable_email"], not results["role_based_email"]]):
            
            obj, _ = EmailVerification.objects.get_or_create(email=email)
            if obj.is_verified:
                msg = "✅ Email already verified."
            else:
                obj.token = uuid.uuid4()
                obj.save()
                link = request.build_absolute_uri(reverse('verify_token', args=[obj.token]))
                msg = "📩 Verification email sent." if send_verification_email(email, link) else "⚠️ Email service failed."
        else:
            msg = "❌ Email failed authenticity checks."

        return _render_or_json(request, {"result": msg, "details": details}, details)

    return render(request, "verify.html")

def _render_or_json(request, context, details):
    """Helper to return JSON for API calls and HTML for browser."""
    if request.content_type == 'application/json':
        return JsonResponse({"result": context.get("result"), "details": details})
    return render(request, "verify.html", context)

def verify_token(request, token):
    verification = get_object_or_404(EmailVerification, token=token)
    if not verification.is_verified:
        verification.is_verified = True
        verification.verified_at = timezone.now()
        verification.save()
        msg = "🎉 Email successfully verified!"
    else:
        msg = "✅ Email already verified."
    return render(request, "verification_result.html", {"message": msg})

@csrf_exempt
def check_verification_status(request):
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({"error": "Email required"}, status=400)

    try:
        record = EmailVerification.objects.get(email=email)
        return JsonResponse({
            "email": email,
            "is_verified": record.is_verified,
            "details": {"confidence_score": "100%" if record.is_verified else "85%"}
        })
    except EmailVerification.DoesNotExist:
        return JsonResponse({"is_verified": False, "result": "Not found"}, status=404)