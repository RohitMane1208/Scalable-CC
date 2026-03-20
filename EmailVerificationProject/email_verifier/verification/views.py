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
    check_disposable, check_role_based
)

@csrf_exempt
def verify_email(request):
    if request.method != "POST":
        return render(request, "verify.html")

    # Unified Email Extraction
    if request.content_type == 'application/json':
        data = json.loads(request.body) if request.body else {}
        email = data.get("email", "").strip()
    else:
        email = request.POST.get("email", "").strip()

    if not email or "@" not in email:
        return JsonResponse({"result": "Invalid Email Format"}, status=400)

    domain = email.split("@")[1].lower()
    
    # 1. Validation logic (reduced redundancy)
    is_valid_syntax = validate_syntax(email)
    mx_exists = check_mx_record(domain)
    is_disposable = check_disposable(domain)
    is_role = check_role_based(email)

    if not is_valid_syntax or is_disposable:
        return JsonResponse({"result": "Email failed authenticity checks."}, status=400)

    # 2. Database & Token generation
    obj, _ = EmailVerification.objects.get_or_create(email=email)
    if obj.is_verified:
        return JsonResponse({"result": "Email already verified."})

    obj.token = uuid.uuid4()
    obj.save()

    # 3. Use your preferred uri method
    link = request.build_absolute_uri(reverse('verify_token', args=[obj.token]))

    if send_verification_email(email, link):
        return JsonResponse({"result": "Verification email sent."})
    
    return JsonResponse({"result": "Email service failed."}, status=500)

def verify_token(request, token):
    verification = get_object_or_404(EmailVerification, token=token)
    if not verification.is_verified:
        verification.is_verified = True
        verification.verified_at = timezone.now()
        verification.save()
        return render(request, "verification_result.html", {"message": "Email successfully verified!"})
    
    return render(request, "verification_result.html", {"message": "Email already verified."})

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