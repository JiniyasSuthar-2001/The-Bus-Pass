from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm, RefillForm
from .models import CustomUser, Pass
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from datetime import timedelta

# --- Helper Functions ---

def is_admin(user):
    """Check if the user is an admin."""
    return user.role == 'ADMIN' or user.is_superuser

def get_barcode_image(data):
    """
    Uses python-barcode library.
    """
    rv = BytesIO()
    code = barcode.get('code128', data, writer=ImageWriter())
    code.write(rv)
    encoded = base64.b64encode(rv.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

# --- Views ---

def home(request):
    """Landing page. Redirects based on role."""
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')
    return render(request, 'registration/login.html') # Show login as home for now

def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Assign 'USER' role by default
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
    """
    Dashboard for regular users.
    Shows balance, existing pass (with barcode), and refill options.
    """
    if is_admin(request.user):
        return redirect('admin_dashboard')

    user_pass, created = Pass.objects.get_or_create(
        user=request.user,
        defaults={'valid_until': timezone.now().date() - timedelta(days=1)} # Start expired
    )
    
    barcode_img = None
    if user_pass.is_valid:
        barcode_img = get_barcode_image(user_pass.barcode_data)

    if request.method == 'POST':
        if 'refill' in request.POST:
            form = RefillForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data['amount']
                request.user.balance += amount
                request.user.save()
                messages.success(request, f"Added ₹{amount} to wallet.")
                return redirect('user_dashboard')
        elif 'buy_pass' in request.POST:
            # Simple logic: 1 Month pass costs $50
            COST = 50
            if request.user.balance >= COST:
                request.user.balance -= COST
                # Extend validity by 30 days from today (or from current validity if active)
                start_date = max(user_pass.valid_until, timezone.now().date())
                user_pass.valid_until = start_date + timedelta(days=30)
                user_pass.save()
                request.user.save()
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
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Dashboard for Admins.
    Lists all users and provides management actions.
    """
    users = CustomUser.objects.filter(role='USER')
    return render(request, 'admin_dashboard.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def verify_pass(request):
    """
    Scanner/Verification view for Admins.
    Simulates scanning by taking a barcode string input.
    """
    result = None
    if request.method == 'POST':
        barcode_input = request.POST.get('barcode_data')
        try:
            found_pass = Pass.objects.get(barcode_data=barcode_input)
            if found_pass.is_valid:
                result = {'status': 'success', 'msg': f"VALID PASS. User: {found_pass.user.username}, Expires: {found_pass.valid_until}"}
            else:
                result = {'status': 'error', 'msg': f"EXPIRED PASS. User: {found_pass.user.username}, Expired on: {found_pass.valid_until}"}
        except Pass.DoesNotExist:
            result = {'status': 'error', 'msg': "INVALID BARCODE. No pass found."}

    return render(request, 'verify_pass.html', {'result': result})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "User deleted.")
    return redirect('admin_dashboard')
