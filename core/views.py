import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from .services import RailService
from .models import Ticket

# Logger for SonarQube traceability
logger = logging.getLogger(__name__)

# Irish Rail Route Configuration
STATION_DATA = {
    'DART_102': {
        'start_name': 'Dublin Connolly',
        'end_name': 'Greystones',
        'stations': [
            {'name': 'Tara Street', 'coords': [53.3470, -6.2542]},
            {'name': 'Dublin Pearse', 'coords': [53.3433, -6.2491]},
            {'name': 'Lansdowne Road', 'coords': [53.3347, -6.2289]},
            {'name': 'Dun Laoghaire', 'coords': [53.2952, -6.1345]},
            {'name': 'Bray', 'coords': [53.2044, -6.1052]},
        ],
        'track': [
            [53.3473, -6.2591], [53.3433, -6.2391], [53.3323, -6.2263], 
            [53.3031, -6.1772], [53.2965, -6.1332], [53.2758, -6.1118], 
            [53.2205, -6.1075], [53.2044, -6.1052], [53.1444, -6.0644]
        ]
    },
    'IC_772': {
        'start_name': 'Dublin Heuston',
        'end_name': 'Galway Ceannt',
        'stations': [
            {'name': 'Tullamore', 'coords': [53.2750, -7.4942]},
            {'name': 'Athlone', 'coords': [53.4251, -7.9351]},
            {'name': 'Ballinasloe', 'coords': [53.3283, -8.2215]},
            {'name': 'Athenry', 'coords': [53.2989, -8.7441]},
        ],
        'track': [
            [53.3464, -6.2945], [53.3364, -6.6133], [53.3102, -7.0655], 
            [53.2750, -7.4942], [53.4241, -7.9333], [53.3281, -8.2215], 
            [53.2989, -8.7441], [53.2743, -9.0477]
        ]
    },
    'IC_884': {
        'start_name': 'Dublin Heuston',
        'end_name': 'Cork Kent',
        'stations': [
            {'name': 'Kildare', 'coords': [53.1581, -6.9115]},
            {'name': 'Portlaoise', 'coords': [53.0345, -7.2991]},
            {'name': 'Thurles', 'coords': [52.6801, -7.8188]},
            {'name': 'Limerick Junction', 'coords': [52.5015, -8.2721]},
            {'name': 'Mallow', 'coords': [52.1391, -8.6545]},
        ],
        'track': [
            [53.3464, -6.2945], [53.2428, -6.6578], [53.1581, -6.9115], 
            [53.0345, -7.2991], [52.6801, -7.8188], [52.5015, -8.2721], 
            [52.1391, -8.6545], [51.9018, -8.4681]
        ]
    },
}

def booking_page(request):
    """Handles passenger registration and identity verification trigger."""
    if request.method != "POST":
        return render(request, 'booking.html', {"station_data": STATION_DATA})

    email = request.POST.get("email", "").strip().lower()
    train_id = request.POST.get("train_id")
    carriage = request.POST.get("carriage")

    # 1. API Check: Verify if identity is already confirmed
    status_check = RailService.get_verification_status(email)

    if status_check.get("is_verified"):
        # Success: Fetch/Create user and generate active ticket
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(username=email, email=email)
        
        ticket = Ticket.objects.create(
            passenger=user, 
            train_id=train_id, 
            carriage_no=carriage, 
            is_active=True
        )
        # Store ticket ID in session for dashboard access control
        request.session['ticket_id'] = str(ticket.id)
        return redirect('dashboard')
    
    # 2. Failure/Pending: Trigger the Verification API suite
    api_response = RailService.validate_and_send(email)
    if api_response.get("status") == "fail":
        messages.error(request, "Safety Check Failed: Invalid or disposable email detected.")
    else:
        messages.info(request, f"Identity link sent to {email}. Please verify to activate your ticket.")
    
    return render(request, 'booking.html', {"station_data": STATION_DATA})

def dashboard(request):
    """Passenger emergency dashboard - Restricted to verified active tickets."""
    ticket_id = request.session.get('ticket_id')
    active_ticket = Ticket.objects.filter(id=ticket_id, is_active=True).first()
    
    if not active_ticket:
        messages.warning(request, "Secure Access Required. Please verify your identity.")
        return redirect('booking')
    
    route_info = STATION_DATA.get(active_ticket.train_id)
    context = {"ticket": active_ticket, "route": route_info}
    
    if request.method == "POST":
        category = request.POST.get("emergency_type")
        # Direct dispatch via Service Layer
        success = RailService.trigger_emergency(
            active_ticket.train_id, 
            active_ticket.carriage_no, 
            category
        )
        if success:
            messages.success(request, f" {category.upper()} Alert dispatched to Control Center.")
            context["alert_sent"] = True
        else:
            messages.error(request, "Communication Failure. Use physical alarm if necessary.")

    return render(request, 'dashboard.html', context)

@require_POST
def cancel_ticket(request, ticket_id):
    """
    Securely ends a journey. 
    Matches session ID against ticket ID to prevent unauthorized cancellations.
    """
    session_ticket_id = request.session.get('ticket_id')
    
    # Security Check: Ensure the person cancelling owns the ticket in this session
    if str(ticket_id) == session_ticket_id:
        ticket = Ticket.objects.filter(id=ticket_id, is_active=True).first()
        if ticket:
            ticket.is_active = False
            ticket.save()
            messages.success(request, "Journey ended. Your safety link has been deactivated.")
    
    # Flush session to prevent any further access to dashboard
    request.session.flush()
    return redirect('booking')

def api_check_typo(request):
    """Async endpoint for real-time domain suggestions."""
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({"suggestion": None})
        
    data = RailService.get_verification_status(email)
    return JsonResponse({"suggestion": data.get("suggestion")})

def verify_ticket_token(request, token):
    """Static landing page after email verification."""
    return render(request, 'verification_result.html', {
        "message": "Identity Confirmed. Your RailGuard profile is now active."
    })