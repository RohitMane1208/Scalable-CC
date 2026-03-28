import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from .services import RailService
from .models import Ticket, EmergencyRequest

logger = logging.getLogger(__name__)

STATION_DATA = {
    'DART_HOWTH': {
        'city': 'Dublin', 'start_name': 'Dublin Connolly', 'end_name': 'Howth',
        'stations': [{'name': 'Clontarf Road', 'coords': [53.3632, -6.2178]}, {'name': 'Killester', 'coords': [53.3725, -6.2045]}, {'name': 'Raheny', 'coords': [53.3813, -6.1764]}, {'name': 'Sutton', 'coords': [53.3892, -6.1082]}],
        'track': [[53.3533, -6.2491], [53.3632, -6.2178], [53.3725, -6.2045], [53.3813, -6.1764], [53.3931, -6.1555], [53.3892, -6.1082], [53.3885, -6.0746]]
    },
    'DART_MALAHIDE': {
        'city': 'Dublin', 'start_name': 'Dublin Connolly', 'end_name': 'Malahide',
        'stations': [{'name': 'Harmonstown', 'coords': [53.3789, -6.1895]}, {'name': 'Kilbarrack', 'coords': [53.3912, -6.1661]}, {'name': 'Howth Junction', 'coords': [53.3963, -6.1555]}, {'name': 'Clongriffin', 'coords': [53.4035, -6.1481]}],
        'track': [[53.3533, -6.2491], [53.3725, -6.2045], [53.3789, -6.1895], [53.3912, -6.1661], [53.3963, -6.1555], [53.4035, -6.1481], [53.4503, -6.1539]]
    },
    'DART_SOUTH': {
        'city': 'Dublin', 'start_name': 'Dublin Connolly', 'end_name': 'Bray / Greystones',
        'stations': [{'name': 'Tara Street', 'coords': [53.3470, -6.2542]}, {'name': 'Dublin Pearse', 'coords': [53.3433, -6.2491]}, {'name': 'Lansdowne Road', 'coords': [53.3347, -6.2289]}, {'name': 'Dun Laoghaire', 'coords': [53.2952, -6.1345]}, {'name': 'Bray', 'coords': [53.2044, -6.1052]}],
        'track': [[53.3473, -6.2591], [53.3433, -6.2391], [53.3323, -6.2263], [53.3031, -6.1772], [53.2965, -6.1332], [53.2758, -6.1118], [53.2205, -6.1075], [53.2044, -6.1052], [53.1444, -6.0644]]
    },
    'MUMBAI_WESTERN': {
        'city': 'Mumbai', 'start_name': 'Churchgate', 'end_name': 'Virar',
        'stations': [{'name': 'Mumbai Central', 'coords': [18.9696, 72.8193]}, {'name': 'Dadar', 'coords': [19.0178, 72.8436]}, {'name': 'Bandra', 'coords': [19.0544, 72.8406]}, {'name': 'Andheri', 'coords': [19.1197, 72.8464]}, {'name': 'Borivali', 'coords': [19.2290, 72.8574]}],
        'track': [[18.9322, 72.8264], [18.9696, 72.8193], [19.0178, 72.8436], [19.0544, 72.8406], [19.1197, 72.8464], [19.2290, 72.8574], [19.4544, 72.8111]]
    },
    'MUMBAI_CENTRAL': {
        'city': 'Mumbai', 'start_name': 'CSMT', 'end_name': 'Kalyan',
        'stations': [{'name': 'Byculla', 'coords': [18.9775, 72.8336]}, {'name': 'Dadar', 'coords': [19.0178, 72.8436]}, {'name': 'Kurla', 'coords': [19.0652, 72.8793]}, {'name': 'Ghatkopar', 'coords': [19.0860, 72.9082]}, {'name': 'Thane', 'coords': [19.1860, 72.9759]}],
        'track': [[18.9400, 72.8353], [18.9775, 72.8336], [19.0178, 72.8436], [19.0652, 72.8793], [19.0860, 72.9082], [19.1860, 72.9759], [19.2348, 73.1298]]
    },
}

def booking_page(request):
    if request.method != "POST":
        return render(request, 'booking.html', {"station_data": STATION_DATA})

    email = request.POST.get("email", "").strip().lower()
    train_id = request.POST.get("train_id")
    carriage = request.POST.get("carriage")

    def process_login(user_email):
        user, _ = User.objects.get_or_create(username=user_email, email=user_email)
        ticket = Ticket.objects.create(
            passenger=user, train_id=train_id, carriage_no=carriage, is_active=True
        )
        request.session['ticket_id'] = str(ticket.id)
        return redirect('dashboard')

    status_check = RailService.get_verification_status(email)
    if status_check.get("is_verified"):
        return process_login(email)

    api_response = RailService.validate_and_send(email)
    status = api_response.get("status")

    if status == "already_verified":
        return process_login(email)
    elif status == "sent":
        messages.info(request, f"Identity link sent to {email}. Please verify to activate your ticket.")
    else:
        messages.error(request, "Safety Check Failed: Invalid or disposable email detected.")
    
    return render(request, 'booking.html', {"station_data": STATION_DATA})

def dashboard(request):
    ticket_id = request.session.get('ticket_id')
    active_ticket = Ticket.objects.filter(id=ticket_id, is_active=True).first()
    
    if not active_ticket:
        messages.warning(request, "Secure Access Required. Please verify your identity.")
        return redirect('booking')
    
    # Sort history so newest requests appear at the top
    history = EmergencyRequest.objects.filter(user=active_ticket.passenger).order_by('-timestamp')

    route_info = STATION_DATA.get(active_ticket.train_id)
    city_context = route_info.get('city', 'Dublin') if route_info else 'Dublin'
    nearby_services = RailService.trigger_emergency(city=city_context)

    if request.method == "POST":
        service_name = request.POST.get("service_name")
        service_type = request.POST.get("service_type")

        if service_name and service_type:
            EmergencyRequest.objects.create(
                user=active_ticket.passenger,
                service_name=service_name,
                service_type=service_type,
                status="Active"
            )

            ADMIN_EMAIL = "rohitmane556@gmail.com"
            RailService.send_admin_alert(
                admin_email=ADMIN_EMAIL,
                user_email=active_ticket.passenger.email,
                service_details=f"{service_type}: {service_name} (City: {city_context})"
            )

            messages.success(request, f"Security alert for {service_name} has been sent to the Admin.")
            return redirect('dashboard')
        
        category = request.POST.get("emergency_type")
        if category:
            RailService.trigger_emergency(city=city_context) 
            messages.success(request, f"{category.upper()} Alert dispatched to Control Center in {city_context}.")
            return redirect('dashboard')

    context = {
        "ticket": active_ticket, 
        "route": route_info,
        "emergency_services": nearby_services, 
        "city": city_context,
        "history": history
    }
    return render(request, 'dashboard.html', context)

@require_POST
def cancel_emergency_request(request, request_id):
    """
    Cancels an active security request and notifies admin via the CloudMail API.
    """
    ticket_id = request.session.get('ticket_id')
    active_ticket = Ticket.objects.filter(id=ticket_id, is_active=True).first()
    
    if not active_ticket:
        return redirect('booking')

    # Ensure the request belongs to the current passenger
    emergency_req = get_object_or_404(EmergencyRequest, id=request_id, user=active_ticket.passenger)
    
    if emergency_req.status == "Active":
        emergency_req.status = "Cancelled"
        emergency_req.save()

        # Notify Admin of the cancellation
        ADMIN_EMAIL = "rohitmane556@gmail.com"
        RailService.send_admin_alert(
            admin_email=ADMIN_EMAIL,
            user_email=active_ticket.passenger.email,
            service_details=f"CANCELLED - {emergency_req.service_type}: {emergency_req.service_name}"
        )
        
        messages.info(request, f"Emergency request for {emergency_req.service_name} has been cancelled.")
    
    return redirect('dashboard')

@require_POST
def cancel_ticket(request, ticket_id):
    if str(ticket_id) == request.session.get('ticket_id'):
        ticket = Ticket.objects.filter(id=ticket_id, is_active=True).first()
        if ticket:
            ticket.is_active = False
            ticket.save()
            messages.success(request, "Journey ended. Your safety link has been deactivated.")
    request.session.flush()
    return redirect('booking')

def api_check_typo(request):
    email = request.GET.get('email', '').strip()
    if not email: return JsonResponse({"suggestion": None})
    data = RailService.get_verification_status(email)
    return JsonResponse({"suggestion": data.get("suggestion")})

def verify_ticket_token(request, token):
    return render(request, 'verification_result.html', {
        "message": "Identity Confirmed. Your RailGuard profile is now active."
    })