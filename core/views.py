import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from .services import RailService
from .models import Ticket

# Full station and track data for Irish Rail routes
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
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        train_id = request.POST.get("train_id")
        carriage = request.POST.get("carriage")

        # API Check: Is user already verified?
        status_check = RailService.get_verification_status(email)

        if status_check.get("is_verified"):
            user, _ = User.objects.get_or_create(username=email, email=email)
            ticket = Ticket.objects.create(
                passenger=user, train_id=train_id, carriage_no=carriage, is_active=True
            )
            request.session['ticket_id'] = ticket.id
            return redirect('dashboard')
        
        else:
            # API Check: Send verification email
            api_response = RailService.validate_and_send(email)
            if api_response.get("status") == "fail":
                messages.error(request, "Identity verification failed. Please check your email address.")
            else:
                messages.info(request, f"Identity check initiated. Please click the link sent to {email}.")
            
            return render(request, 'booking.html', {"station_data": STATION_DATA})

    return render(request, 'booking.html', {"station_data": STATION_DATA})

def dashboard(request):
    ticket_id = request.session.get('ticket_id')
    active_ticket = Ticket.objects.filter(id=ticket_id).first()
    
    if not active_ticket:
        messages.warning(request, "Access Denied. Please verify your identity first.")
        return redirect('booking')
    
    route_info = STATION_DATA.get(active_ticket.train_id)
    
    context = {
        "ticket": active_ticket,
        "route": route_info
    }
    
    if request.method == "POST":
        category = request.POST.get("emergency_type")
        # Trigger real-time emergency alert via RailService
        success = RailService.trigger_emergency(
            active_ticket.train_id, active_ticket.carriage_no, category
        )
        context["alert_sent"] = success
        if success:
            messages.success(request, f"Emergency {category} alert has been dispatched to Irish Rail Control.")

    return render(request, 'dashboard.html', context)

def api_check_typo(request):
    email = request.GET.get('email', '')
    if email:
        data = RailService.get_verification_status(email)
        return JsonResponse({"suggestion": data.get("suggestion")})
    return JsonResponse({"suggestion": None})

def verify_ticket_token(request, token):
    return render(request, 'verification_result.html', {"message": "Identity Confirmed. You can now return to the booking page."})

def trigger_emergency_action(request):
    return JsonResponse({"status": "received"})