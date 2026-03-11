import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from .services import RailService
from .models import Ticket

def booking_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        train_id = request.POST.get("train_id")
        carriage = request.POST.get("carriage")

        # 1. Check Identity Status
        status_check = RailService.get_verification_status(email)

        if status_check.get("is_verified"):
            user, _ = User.objects.get_or_create(username=email, email=email)
            ticket = Ticket.objects.create(
                passenger=user, train_id=train_id, carriage_no=carriage, is_active=True
            )
            request.session['ticket_id'] = ticket.id
            return redirect('dashboard')
        
        else:
            # 2. Call Validation API
            api_response = RailService.validate_and_send(email)
            
            # Extract the specific metrics from your API output
            metrics = api_response.get("details", {})
            mx_exists = metrics.get("mx_record_exists", True) # Default to True unless API says No
            format_valid = metrics.get("format_valid", True)

            # THE GATEKEEPER LOGIC:
            # If MX record is No OR Format is Invalid OR API status is 'fail'
            if api_response.get("status") == "fail" or mx_exists is False or format_valid is False:
                
                # Create a specific error message based on the API metrics
                if mx_exists is False:
                    error_msg = f"Invalid Email: The domain for '{email}' does not have a valid mail server (MX record)."
                elif format_valid is False:
                    error_msg = "Invalid Email: The format of this email is incorrect."
                else:
                    error_msg = api_response.get("message", "Email verification failed.")

                messages.error(request, error_msg)
                return render(request, 'booking.html', {"email": email})

            # 3. Only if everything is valid, say the mail was sent
            messages.info(request, "Identity check initiated. Please verify your email via the link sent to your inbox.")
            return render(request, 'booking.html')

    return render(request, 'booking.html')

# 2. THE PASSENGER DASHBOARD (The missing attribute)
def dashboard(request):
    # Retrieve the ticket from session
    ticket_id = request.session.get('ticket_id')
    active_ticket = Ticket.objects.filter(id=ticket_id).first()
    
    # Security: Kick out unverified users
    if not active_ticket:
        messages.warning(request, "Access Denied. Please verify your identity first.")
        return redirect('booking')
    
    context = {"ticket": active_ticket}
    
    if request.method == "POST":
        category = request.POST.get("emergency_type")
        success = RailService.trigger_emergency(
            active_ticket.train_id, 
            active_ticket.carriage_no, 
            category
        )
        context["alert_sent"] = success
        if success:
            messages.info(request, f"Emergency alert ({category}) has been dispatched.")

    return render(request, 'dashboard.html', context)

# 3. TYPO CHECK (For JavaScript AJAX)
def api_check_typo(request):
    email = request.GET.get('email', '')
    if email:
        data = RailService.get_verification_status(email)
        return JsonResponse({"suggestion": data.get("suggestion")})
    return JsonResponse({"suggestion": None})

# 4. TOKEN VERIFICATION (Landing page for email link)
def verify_ticket_token(request, token):
    return render(request, 'verification_result.html', {"message": "Identity Confirmed. You may now book your journey."})

# 5. EMERGENCY ACTION (AJAX Placeholder)
def trigger_emergency_action(request):
    return JsonResponse({"status": "received"})