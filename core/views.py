from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm, RefillForm
from .models import CustomUser, Pass, Payment, Ticket, City, Route
import barcode
# from barcode.writer import ImageWriter # Removed for performance
from io import BytesIO
import base64
from datetime import timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
import requests
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from urllib.parse import urlencode

# --- Helper Functions ---

def is_admin(user):
    """
    Check if the user has Admin privileges.
    """
    return user.role == 'ADMIN' or user.is_superuser

def is_conductor(user):
    """
    Check if the user is a Conductor.
    """
    return user.role == 'CONDUCTOR'

def get_barcode_image(data):
    """
    Generate a helper function to create a Barcode image (Code128).
    Returns a base64 encoded string for embedding in HTML.
    """
    rv = BytesIO()
    code = barcode.get('code128', data) # Defaults to SVGWriter which is faster
    code.write(rv)
    encoded = base64.b64encode(rv.getvalue()).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"

    encoded = base64.b64encode(rv.getvalue()).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"

# --- Authentication Views ---

def custom_login(request):
    """
    Custom Login View.
    - RESTRICTS Admistrators and Conductors from logging in here.
    - Allows only 'USER' role (or standard users).
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Security Check: Prevent Admin/Conductor login on public form
            if is_admin(user) or is_conductor(user):
                messages.error(request, "Admins and Conductors must use the restricted portal.")
                return redirect('login')
            
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def google_login(request):
    """
    Initiates the Google OAuth2 flow.
    """
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "access_type": "online",
    }
    url = f"{base_url}?{urlencode(params)}"
    return redirect(url)

def google_callback(request):
    """
    Callback from Google.
    Exchanges code for token, gets user info, creates/logs in user.
    """
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error or not code:
        messages.error(request, "Google Login failed or cancelled.")
        return redirect('login')
        
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    try:
        res = requests.post(token_url, data=token_data)
        res_json = res.json()
        access_token = res_json.get('access_token')
        
        if not access_token:
            messages.error(request, "Failed to obtain access token from Google.")
            return redirect('login')
            
        # Get User Info
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_res = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_res.json()
        
        email = user_info.get('email')
        if not email:
            messages.error(request, "Could not retrieve email from Google.")
            return redirect('login')
            
        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
            if is_admin(user) or is_conductor(user):
                messages.error(request, "Admins/Conductors cannot use Google Login.")
                return redirect('login')
        except CustomUser.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = CustomUser.objects.create(
                username=username,
                email=email,
                role='USER'
            )
            # Set unusable password (social login only) or random
            user.set_unusable_password()
            user.save()
            
        # Login
        auth_login(request, user)
        messages.success(request, f"Welcome back, {user.username}!")
        return redirect('home')
        
    except Exception as e:
        print(f"Google Auth Error: {e}")
        messages.error(request, "Something went wrong during Google Login.")
        return redirect('login')

# --- Views ---

def home(request):
    """
    Landing page logic:
    - If user is logged in, redirect to their respective dashboard based on role.
    - If user is guest, show the login page.
    """
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_dashboard')
        elif is_conductor(request.user):
            return redirect('conductor_dashboard')
        else:
            return redirect('user_dashboard')
    return render(request, 'registration/login.html')

def register(request):
    """
    User Registration View.
    Handles creation of new users using CustomUserCreationForm.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = 'USER' # Default role
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def user_dashboard(request):
    """
    Main dashboard for standard Users.
    Display:
    - Wallet balance
    - Current Pass status (Valid/Expired)
    - Barcode for scanning
    
    Actions:
    - Refill Wallet (Redirects to payment)
    - Buy/Extend Pass (Deducts balance)
    """
    if is_admin(request.user):
        return redirect('admin_dashboard')
    if is_conductor(request.user):
        return redirect('conductor_dashboard')

    # Get or create a pass for the user
    user_pass, created = Pass.objects.get_or_create(
        user=request.user,
        defaults={'valid_until': timezone.now().date() - timedelta(days=1)}
    )
    
    # Generate barcode if pass is valid
    barcode_img = None
    if user_pass.is_valid:
        barcode_img = get_barcode_image(user_pass.barcode_data)

    if request.method == 'POST':
        if 'refill' in request.POST:
            return redirect('payment_page') # Redirect to new payment page
        elif 'buy_pass' in request.POST:
            COST = 50
            if request.user.balance >= COST:
                request.user.balance -= COST
                # Extend pass from today or current validity
                start_date = max(user_pass.valid_until, timezone.now().date())
                user_pass.valid_until = start_date + timedelta(days=30)
                user_pass.save()
                request.user.save()
                
                # Record Payment (Use 'PURCHASE' type even though internal)
                Payment.objects.create(
                    user=request.user,
                    amount=COST,
                    transaction_type='PURCHASE',
                    description='Monthly Pass Purchase'
                )
                
                messages.success(request, "Pass purchased/extended successfully!")
                return redirect('user_dashboard')
            else:
                messages.error(request, "Insufficient balance.")
    else:
        form = RefillForm()

    # Fetch Payment History & Active Tickets
    payments = Payment.objects.filter(user=request.user).order_by('-timestamp')
    active_tickets = Ticket.objects.filter(user=request.user, is_used=False).order_by('-purchase_time')
    cities_data = list(City.objects.all().values('id', 'name', 'state'))
    routes_data = list(routes.values(
        'id', 
        'source__id', 'source__name', 'source__state',
        'destination__id', 'destination__name', 'destination__state',
        'cost',
        'cost',
        'bus_number', 'gate', 'date', 'departure_time', 'arrival_time'
    ))
    
    # Get Unique States
    states = City.STATE_CHOICES

    context = {
        'pass': user_pass, 
        'payments': payments,
        'active_tickets': active_tickets,
        'states': [s[0] for s in states],
        'cities_json': json.dumps(cities_data),
        'routes_json': json.dumps(routes_data, cls=DjangoJSONEncoder),
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def recharge_wallet(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            val = float(amount)
            if val > 0:
                request.user.balance += _decimal(val)
                request.user.save()
                Payment.objects.create(user=request.user, amount=val, transaction_type='REFILL', description='Manual Refill')
                messages.success(request, f"Recharged ₹{val} successfully.")
        except ValueError:
            messages.error(request, "Invalid Amount")
    return redirect('user_dashboard')

@login_required
def buy_ticket(request):
    """
    User buys a ticket for a specific route.
    """
    if request.method == 'POST':
        route_id = request.POST.get('route_id')
        try:
            route = Route.objects.get(id=route_id)
            if request.user.balance >= route.cost:
                request.user.balance -= route.cost
                request.user.save()
                
                # Create Ticket
                Ticket.objects.create(user=request.user, route=route)
                
                # Record Payment
                Payment.objects.create(
                    user=request.user,
                    amount=route.cost,
                    transaction_type='TICKET',
                    description=f"Ticket: {route.source.name} to {route.destination.name}"
                )
                messages.success(request, "Ticket Purchased!")
            else:
                messages.error(request, "Insufficient Balance.")
        except Route.DoesNotExist:
            messages.error(request, "Invalid Route.")
            
    return redirect('user_dashboard')

    return render(request, 'user_dashboard.html', context)

def conductor_login(request):
    """
    Dedicated Login View for Conductors and Admins.
    - RESTRICTS standard Users.
    - Redirects to respective dashboards.
    """
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_dashboard')
        elif is_conductor(request.user):
            return redirect('conductor_dashboard')
        else:
             messages.error(request, "Users must use the main login page.")
             return redirect('home') # or logout and show error

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Security Check: Prevent Standard User login on staff portal
            if not (is_admin(user) or is_conductor(user)):
                messages.error(request, "Access Denied: innovative users are not allowed here.")
                return redirect('conductor_login')
            
            auth_login(request, user)
            if is_admin(user):
                return redirect('admin_dashboard')
            return redirect('conductor_dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/conductor_login.html', {'form': form})

@login_required
def get_routes(request):
    """API for Conductor to get routes"""
    routes = Route.objects.all().values('id', 'source__name', 'destination__name', 'cost')
    return JsonResponse(list(routes), safe=False)

@login_required
def validate_ticket(request):
    """
    Conductor scans a ticket to validate and mark it as used.
    """
    if not (is_conductor(request.user) or is_admin(request.user)):
        return redirect('home')

    if request.method == 'POST':
        barcode_data = request.POST.get('barcode_data')
        
        try:
            ticket = Ticket.objects.get(barcode_data=barcode_data)
            
            if ticket.is_used:
                messages.error(request, f"TICKET USED! Travelled on: {ticket.used_time}")
            else:
                # MARK AS USED
                ticket.is_used = True
                ticket.used_time = timezone.now()
                ticket.save()
                messages.success(request, f"VALID TICKET! {ticket.route.source.name} -> {ticket.route.destination.name} | Date: {ticket.route.date} | Time: {ticket.route.departure_time}")
                
        except Ticket.DoesNotExist:
            messages.error(request, "INVALID TICKET! Ticket not found.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return redirect('conductor_dashboard')

@login_required
def payment_page(request):
    """
    Payment Gateway Integration (Razorpay).
    Initiates payment order and renders payment page.
    Includes fallback mock logic if API keys are missing.
    """
    # Razorpay Test Keys (Provided by User)
    KEY_ID = "rzp_test_S5hYqp6DgfqELU" 
    KEY_SECRET = "VM3nLon1Kt4yveBEfi1rdQ4e" 
    
    # Initialize Razorpay Client
    client = None
    try:
        import razorpay
        client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
    except (ImportError, Exception) as e:
        print(f"Razorpay Client/Import Error: {e}")
        client = None

    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
            
            # Razorpay expects amount in paise (100 paise = 1 INR)
            amount_paise = int(amount_val * 100)
            
            order_id = None
            if client:
                try:
                    data = { "amount": amount_paise, "currency": "INR", "receipt": f"rcpt_{request.user.id}" }
                    order = client.order.create(data=data)
                    order_id = order['id']
                except Exception as e:
                    print(f"Order Creation Error: {e}")
                    # Fallback if API fails
                    order_id = f"order_{base64.b64encode(str(timezone.now()).encode()).decode()[:10]}"
            else:
                 # Fallback if Client not initialized (or import failed)
                 order_id = f"order_{base64.b64encode(str(timezone.now()).encode()).decode()[:10]}"
            
            # Store amount in session for verification step
            request.session['payment_amount'] = str(amount_val)
            
            context = {
                'key_id': KEY_ID,
                'amount': amount_val,
                'amount_paise': amount_paise,
                'order_id': order_id,
                'user_email': request.user.email,
                'user_phone': "+917779082347" # Hardcoded per request or user profile
            }
            return render(request, 'payment_confirm.html', context)
            
        except ValueError:
            messages.error(request, "Invalid amount.")
            
    return render(request, 'payment.html')

@login_required
@csrf_exempt
def payment_success(request):
    """
    Handle success callback from Razorpay.
    Verifies payment (mock verification here) and updates user balance.
    """
    if request.method == "POST":
        # In real scenario, verify signature here using client.utility.verify_payment_signature()
        
        # Taking data from POST (razorpay sends these)
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Assume amount was passed in session or recalculate (here we just create record)
        amount_str = request.session.get('payment_amount', '0.00')
        try:
            amount = float(amount_str)
        except ValueError:
            amount = 0.00
            
        if amount <= 0:
             messages.error(request, "Payment verification failed: Invalid amount.")
             return redirect('user_dashboard')
        
        # Log successful payment
        Payment.objects.create(
            user=request.user,
            amount=amount,
            transaction_type='REFILL',
            description=f'Razorpay Refill: {razorpay_payment_id}'
        )
        # Update Balance
        request.user.balance += _decimal(amount)
        request.user.save()
        
        messages.success(request, f"Payment Successful! Ref: {razorpay_payment_id}")
        return redirect('user_dashboard')
        
    return redirect('user_dashboard')

def _decimal(val):
    from decimal import Decimal
    return Decimal(val)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Admin Dashboard View.
    Displays:
    - User Stats
    - List of Conductors
    - Payment History Chart
    """
    users = CustomUser.objects.filter(role='USER')
    conductors = CustomUser.objects.filter(role='CONDUCTOR')
    
    # Graphs Data
    payments = Payment.objects.all().order_by('-timestamp')
    
    # Simple aggregation for charts (by date)
    payment_data = []
    for p in payments:
        payment_data.append({
            'date': p.timestamp.strftime('%Y-%m-%d'),
            'amount': float(p.amount),
            'user': p.user.username,
            'type': p.transaction_type
        })

    return render(request, 'admin_dashboard.html', {
        'users': users, 
        'conductors': conductors,
        'payment_data': json.dumps(payment_data),
        'cities': City.objects.all(),
        'routes': Route.objects.all(),
    })

@login_required
@user_passes_test(is_admin)
def add_city(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        state = request.POST.get('state')
        if name and state:
            City.objects.get_or_create(name=name, state=state)
            messages.success(request, f"City '{name}, {state}' added.")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def delete_city(request, city_id):
    City.objects.filter(id=city_id).delete()
    messages.success(request, "City deleted.")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def add_route(request):
    if request.method == 'POST':
        source_id = request.POST.get('source')
        dest_id = request.POST.get('destination')
        cost = request.POST.get('cost')
        bus_number = request.POST.get('bus_number')
        gate = request.POST.get('gate')
        date = request.POST.get('date')
        departure = request.POST.get('departure')
        arrival = request.POST.get('arrival')

        if source_id and dest_id and cost:
            Route.objects.create(
                source_id=source_id, 
                destination_id=dest_id, 
                cost=cost,
                bus_number=bus_number,
                gate=gate,
                date=date,
                departure_time=departure,
                arrival_time=arrival
            )
            messages.success(request, "Route created.")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def delete_route(request, route_id):
    Route.objects.filter(id=route_id).delete()
    messages.success(request, "Route deleted.")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def create_conductor(request):
    """
    Admin View to create a new Conductor account.
    Using CustomUserCreationForm but forcing role='CONDUCTOR'.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = 'CONDUCTOR'
            user.save()
            messages.success(request, "Conductor created successfully.")
            return redirect('admin_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_conductor.html', {'form': form})

@login_required
@user_passes_test(is_conductor)
def conductor_dashboard(request):
    """
    Conductor Dashboard / Scanner View.
    Allows conductors to verify passes by entering barcode data (simulated scan).
    """
    result = None
    if request.method == 'POST':
        barcode_input = request.POST.get('barcode_data')
        try:
            found_pass = Pass.objects.get(barcode_data=barcode_input)
            if found_pass.is_valid:
                result = {'status': 'success', 'msg': f"VALID PASS. User: {found_pass.user.username}", 'detail': f"Expires: {found_pass.valid_until}"}
            else:
                result = {'status': 'error', 'msg': f"EXPIRED PASS. User: {found_pass.user.username}", 'detail': f"Expired on: {found_pass.valid_until}"}
        except Pass.DoesNotExist:
            result = {'status': 'error', 'msg': "INVALID BARCODE", 'detail': "No pass found."}

    return render(request, 'conductor_dashboard.html', {'result': result})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """
    Admin View to delete a user/conductor.
    """
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "User deleted.")
    return redirect('admin_dashboard')

# Using existing verify_pass for legacy admin if needed, 
# or redirecting to conductor view could be an option.
# Keeping it for now but aliasing functionality if admin wants to scan too.
@login_required
@user_passes_test(is_admin)
def verify_pass(request):
    """
    Scanner view alias for Admins.
    """
    return conductor_dashboard(request)
