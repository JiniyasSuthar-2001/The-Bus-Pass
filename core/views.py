from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm, RefillForm
from .models import CustomUser, Pass, Payment
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from datetime import timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum

# --- Helper Functions ---

def is_admin(user):
    return user.role == 'ADMIN' or user.is_superuser

def is_conductor(user):
    return user.role == 'CONDUCTOR'

def get_barcode_image(data):
    rv = BytesIO()
    code = barcode.get('code128', data, writer=ImageWriter())
    code.write(rv)
    encoded = base64.b64encode(rv.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

# --- Views ---

def home(request):
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_dashboard')
        elif is_conductor(request.user):
            return redirect('conductor_dashboard')
        else:
            return redirect('user_dashboard')
    return render(request, 'registration/login.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = 'USER'
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def user_dashboard(request):
    if is_admin(request.user):
        return redirect('admin_dashboard')
    if is_conductor(request.user):
        return redirect('conductor_dashboard')

    user_pass, created = Pass.objects.get_or_create(
        user=request.user,
        defaults={'valid_until': timezone.now().date() - timedelta(days=1)}
    )
    
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

    context = {
        'pass': user_pass,
        'barcode_img': barcode_img,
        'form': form,
        'is_valid': user_pass.is_valid
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def payment_page(request):
    import razorpay
    from django.conf import settings
    
    # Use environment variables or placeholders
    KEY_ID = "rzp_test_placeholder" # Replace with os.environ.get('RAZORPAY_KEY_ID')
    KEY_SECRET = "secret_placeholder" # Replace with os.environ.get('RAZORPAY_KEY_SECRET')
    
    # Initialize Razorpay Client
    # client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
            
            # Razorpay expects amount in paise (100 paise = 1 INR)
            amount_paise = int(amount_val * 100)
            
            # Create Order (Mocking the API call if no valid key)
            # order = client.order.create(data=data)
            # For demonstration without keys, we pass dummy data
            order_id = f"order_{base64.b64encode(str(timezone.now()).encode()).decode()[:10]}"
            
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
    """Handle success callback from Razorpay."""
    if request.method == "POST":
        # In real scenario, verify signature here using client.utility.verify_payment_signature()
        
        # Taking data from POST (razorpay sends these)
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Assume amount was passed in session or recalculate (here we just create record)
        # Getting amount from a hidden field or similar is risky, better to verify order_id API
        # For this mock flow:
        amount = 500.00 # Placeholder default if not tracked in session
        
        Payment.objects.create(
            user=request.user,
            amount=amount,
            transaction_type='REFILL',
            description=f'Razorpay Refill: {razorpay_payment_id}'
        )
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
    users = CustomUser.objects.filter(role='USER')
    conductors = CustomUser.objects.filter(role='CONDUCTOR')
    
    # Graphs Data
    payments = Payment.objects.all().order_by('-timestamp')
    
    # Simple aggregation for charts (by date)
    # in real app, use annotate/truncMonth etc.
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
        'payment_data': json.dumps(payment_data)
    })

@login_required
@user_passes_test(is_admin)
def create_conductor(request):
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
    Scanner/Verification view for Conductors.
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
    # Admins can also scan
    return conductor_dashboard(request)
