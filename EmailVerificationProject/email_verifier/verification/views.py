from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse
import uuid

from .models import EmailVerification
from .utils import (
    send_verification_email,
    validate_syntax,
    check_mx_record,
    check_disposable,
    check_role_based
)

def verify_email(request):
    context = {}
    details = {}

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if "@" not in email:
            context["result"] = "❌ Invalid Email Format"
            return render(request, "verify.html", context)

        domain = email.split("@")[1].lower()

        # 🔍 Run validations
        format_valid = validate_syntax(email)
        mx_valid = check_mx_record(domain)
        is_disposable = check_disposable(domain)
        is_role_based = check_role_based(email)

        # 🛠️ Calculate "Is Common Domain"
        common_providers = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "aol.com"]
        is_common = domain in common_providers

        # 📈 Calculate Confidence Score
        score = 0
        if format_valid: score += 30
        if mx_valid: score += 40
        if not is_disposable: score += 15
        if not is_role_based: score += 15
        
        if is_disposable: score -= 50
        if not format_valid: score = 0

        final_score = max(0, min(100, score))

        # 📊 Prepare metrics output for verify.html
        details = {
            "email": email,
            "format_valid": format_valid,
            "mx_record_exists": mx_valid,
            "disposable_email": is_disposable,
            "role_based_email": is_role_based,
            "is_common_domain": is_common,
            "confidence_score": f"{final_score}%"
        }

        context["details"] = details

        # 🚨 STRICT CONDITION
        if (
            format_valid 
            and mx_valid 
            and not is_disposable 
            and not is_role_based
        ):
            verification_obj, created = EmailVerification.objects.get_or_create(email=email)
            if verification_obj.is_verified:
                context["result"] = "✅ Email already verified."
            else:
                verification_obj.token = uuid.uuid4()
                verification_obj.save()
                verification_link = request.build_absolute_uri(
                    reverse('verify_token', args=[verification_obj.token])
                )
                if send_verification_email(email, verification_link):
                    context["result"] = "📩 Verification email sent successfully."
                else:
                    context["result"] = "⚠️ Validation passed, but email service failed to send."
        else:
            context["result"] = "❌ Email failed authenticity checks (Disposable or Role-based)."

    return render(request, "verify.html", context)

def verify_token(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        if verification.is_verified:
            message = "✅ Email already verified."
        else:
            verification.is_verified = True
            verification.verified_at = timezone.now()
            verification.save()
            message = "🎉 Email successfully verified!"
    except EmailVerification.DoesNotExist:
        message = "❌ Invalid or expired verification link."
    return render(request, "verification_result.html", {"message": message})