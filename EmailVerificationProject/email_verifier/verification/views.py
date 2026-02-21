from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse
import uuid

from .models import EmailVerification
from .utils import send_verification_email
from .utils import (
    validate_syntax,
    check_mx_record,
    check_disposable,
    check_role_based,
    smtp_check
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

        # 🔍 Run all validations
        format_valid = validate_syntax(email)
        mx_valid = check_mx_record(domain)
        disposable = check_disposable(domain)
        role_based = check_role_based(email)
        smtp_valid = smtp_check(email)

        # 🛠️ Calculate "Is Common Domain"
        common_providers = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "aol.com"]
        is_common = domain in common_providers

        # 📈 Calculate Confidence Score
        # We start at 0 and add weight based on importance
        score = 0
        if format_valid: score += 20
        if mx_valid: score += 20
        if smtp_valid: score += 50
        if not disposable: score += 10
        
        # Penalize heavily if it's definitely a bad sign
        if disposable: score -= 50
        if not format_valid: score = 0

        # Ensure score stays between 0-100
        final_score = max(0, min(100, score))

        # 📊 Prepare metrics output (Keys MUST match verify.html)
        details = {
            "email": email,
            "format_valid": format_valid,
            "mx_record_exists": mx_valid,
            "smtp_mailbox_exists": smtp_valid,
            "disposable_email": disposable,
            "role_based_email": role_based,
            "is_common_domain": is_common,
            "confidence_score": f"{final_score}%"
        }

        context["details"] = details

        # 🚨 STRICT CONDITION FOR SENDING EMAIL
        if (
            format_valid
            and mx_valid
            and not disposable
            and not role_based
            and smtp_valid
        ):
            verification_obj, created = EmailVerification.objects.get_or_create(
                email=email
            )

            if verification_obj.is_verified:
                context["result"] = "✅ Email already verified."
            else:
                verification_obj.token = uuid.uuid4()
                verification_obj.save()

                verification_link = request.build_absolute_uri(
                    reverse('verify_token', args=[verification_obj.token])
                )

                send_verification_email(email, verification_link)
                context["result"] = "📩 Verification email sent successfully."
        else:
            context["result"] = "❌ Email failed validation checks. See details below."

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

    return render(request, "verification_result.html", {
        "message": message
    })