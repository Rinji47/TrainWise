from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, WeightLog
from django.utils import timezone
from functools import wraps
from membership.models import MemberSubscription, Payment
from classes.models import PrivateClass
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from datetime import date, timedelta, datetime
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from xhtml2pdf import pisa

# Admin-only decorator
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role == 'Admin' or request.user.is_staff):
            return view_func(request, *args, **kwargs)
        return redirect('user-dashboard')
    return wrapper

def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        # Required fields
        username = request.POST.get('username').strip()
        first_name = request.POST.get('first_name').strip()
        last_name = request.POST.get('last_name').strip()
        email = request.POST.get('email').strip()
        phone = request.POST.get('phone').strip()
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Optional fields
        gender = request.POST.get('gender') or None
        age = request.POST.get('age') or None
        height = request.POST.get('height') or None
        weight = request.POST.get('weight') or None
        fitness_goal = request.POST.get('fitness_goal') or None

        # Validate password match
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/register.html', request.POST)

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'auth/register.html', request.POST)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'auth/register.html', request.POST)

        # Convert numeric fields
        age = int(age) if age else None
        height = float(height) if height else None
        weight = float(weight) if weight else None

        # Create user
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
            role='Member',
            gender=gender,
            age=age,
            height=height,
            weight=weight,
            fitness_goal=fitness_goal
        )

        login(request, user)
        messages.success(request, f"Welcome {user.full_name}! Your account has been created.")
        return redirect('home')

    return render(request, 'auth/register.html')


# in views.py
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()  # changed to username
        password = request.POST.get('password')

        auth_user = authenticate(request, username=username, password=password)
        if auth_user:
            login(request, auth_user)

            # Redirect based on role
            if auth_user.role == 'Admin' or auth_user.is_staff:
                return redirect('admin-dashboard')
            elif auth_user.role == 'Trainer':
                return redirect('trainer-dashboard')
            else:
                return redirect('user-dashboard')

        # If admin created the account, send to first-time setup flow
        pending_user = User.objects.filter(username=username, must_set_password=True).first()
        if pending_user:
            messages.info(request, "Your account was created by an admin. Please set your password first.")
            return redirect('first-time-email')

        messages.error(request, "Invalid username or password.")
        return render(request, 'auth/login.html')

    return render(request, 'auth/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')


def password_reset(request):
    return render(request, 'auth/password_reset.html')


class FirstTimeSetPasswordForm(SetPasswordForm):
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError(self.error_messages['password_mismatch'], code='password_mismatch')

        try:
            validate_password(password2, self.user)
        except ValidationError as error:
            custom_messages = []
            for err in error.error_list:
                if err.code == 'password_too_common':
                    custom_messages.append(
                        "Password is too weak. Use a longer, unique passphrase with mixed letters, numbers, and symbols."
                    )
                else:
                    custom_messages.append(err.message)
            raise ValidationError(custom_messages)

        return password2


def first_time_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()

        user = User.objects.filter(email=email, username=username, must_set_password=True).first()
        if not user:
            if User.objects.filter(email=email, username=username, must_set_password=False).first():
                messages.error(request, "This account already has a password.")
                return render(request, 'auth/first_time_email.html')
            messages.error(request, "No admin-created account found for that email and username.")
            return render(request, 'auth/first_time_email.html')

        request.session['first_time_user_id'] = user.id
        return redirect('first-time-set-password')

    return render(request, 'auth/first_time_email.html')


def first_time_set_password(request):
    user_id = request.session.get('first_time_user_id')
    if not user_id:
        messages.error(request, "Please enter your email to start password setup.")
        return redirect('first-time-email')

    user = get_object_or_404(User, id=user_id, must_set_password=True)

    if request.method == 'POST':
        form = FirstTimeSetPasswordForm(user, request.POST)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        if form.is_valid():
            form.save()
            user.must_set_password = False
            user.save(update_fields=['must_set_password'])
            request.session.pop('first_time_user_id', None)
            login(request, user)

            if user.role == 'Admin' or user.is_staff:
                return redirect('admin-dashboard')
            elif user.role == 'Trainer':
                return redirect('trainer-dashboard')
            return redirect('user-dashboard')
    else:
        form = FirstTimeSetPasswordForm(user)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    return render(request, 'auth/first_time_set_password.html', {'form': form})



@login_required
def user_dashboard(request):
    user = request.user
    today = date.today()  # Use date.today() instead of timezone.now().date()

    # -------------------------
    # Active subscription
    # -------------------------
    active_subscription = MemberSubscription.objects.filter(
        member=user,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).order_by('-end_date').first()
    
    if active_subscription:
        days_remaining = (active_subscription.end_date - today).days
        membership_status = "Active"
    else:
        days_remaining = 0
        membership_status = "Inactive"

    # -------------------------
    # Upcoming private classes
    # -------------------------
    upcoming_classes = PrivateClass.objects.filter(
        member=user,
        is_active=True,
        start_date__gte=today
    ).order_by('start_date', 'start_time')

    upcoming_bookings_count = upcoming_classes.count()

    # -------------------------
    # Completed private classes
    # -------------------------
    classes_attended = PrivateClass.objects.filter(
        member=user,
        is_active=True,
        start_date__lt=today
    ).count()

    # -------------------------
    # Payments (subscriptions + private classes)
    # -------------------------
    payments = Payment.objects.filter(
        Q(member_subscription__member=user) |
        Q(private_class__member=user)
    ).order_by('-payment_date')

    # Payment stats (NO template sum filter ❌)
    total_payments = sum(p.amount for p in payments)
    paid_amount = sum(p.amount for p in payments if p.payment_status == 'Paid')
    pending_amount = sum(p.amount for p in payments if p.payment_status == 'Pending')
    failed_amount = sum(p.amount for p in payments if p.payment_status == 'Failed')

    context = {
        'user': user,
        'active_subscription': active_subscription,
        'membership_status': membership_status,
        'days_remaining': days_remaining,

        'upcoming_bookings': upcoming_classes,
        'upcoming_bookings_count': upcoming_bookings_count,
        'classes_attended': classes_attended,

        'payments': payments,
        'total_payments': total_payments,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'failed_amount': failed_amount,
    }

    return render(request, 'user/dashboard.html', context)

@login_required
def profile_settings(request):
    user = request.user

    if request.method == "POST":
        # -----------------------------
        # Personal Info (and Trainer info)
        # -----------------------------
        if 'first_name' in request.POST:
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            user.gender = request.POST.get('gender', '').strip() or None

            # Only update trainer-specific fields if user is a trainer
            if user.role == "Trainer":
                user.specialization = request.POST.get('specialization', '').strip() or None
                exp_years = request.POST.get('experience_years')
                user.experience_years = int(exp_years) if exp_years else None

            try:
                user.save()
                messages.success(request, "Personal information updated successfully.")
            except Exception as e:
                messages.error(request, f"Error updating personal info: {str(e)}")

        # -----------------------------
        # Fitness Info
        # -----------------------------
        elif 'age' in request.POST:
            age = request.POST.get('age')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
            fitness_goal = request.POST.get('fitness_goal', '').strip()

            user.age = int(age) if age else None
            user.height = float(height) if height else None
            user.weight = float(weight) if weight else None
            user.fitness_goal = fitness_goal or None

            try:
                user.save()
                messages.success(request, "Fitness profile updated successfully.")
            except Exception as e:
                messages.error(request, f"Error updating fitness profile: {str(e)}")

        # -----------------------------
        # Password change could go here (if handled in same view)
        # -----------------------------

    context = {
        'user': user,
    }

    if user.role == "Member":
        return render(request, 'user/profile_settings.html', context)
    elif user.role == "Trainer":
        return render(request, 'trainer/profile_settings.html', context)
    elif user.role == "Admin":
        return render(request, 'admin/profile_settings.html', context)
    



@login_required
@admin_required
def admin_dashboard(request):
    # --- Users ---
    total_users = User.objects.count()
    active_members = User.objects.filter(role='Member', is_active=True).count()
    total_trainers = User.objects.filter(role='Trainer', is_active=True).count()

    # --- Membership / Subscriptions ---
    active_subscriptions = MemberSubscription.objects.filter(is_active=True).count()

    # --- Payments / Revenue ---
    total_revenue = Payment.objects.filter(payment_status='Paid').aggregate(
        total=Sum('amount')
    )['total'] or 0

    pending_payments = Payment.objects.filter(payment_status='Pending').count()

    # --- Recent activities ---
    recent_bookings = PrivateClass.objects.select_related('member', 'trainer').order_by('-created_at')[:5]

    recent_payments = Payment.objects.select_related(
        'member_subscription__member', 'private_class'
    ).order_by('-payment_date')[:5]

    context = {
        'total_users': total_users,
        'active_members': active_members,
        'total_trainers': total_trainers,
        'active_subscriptions': active_subscriptions,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
    }

    return render(request, 'admin/dashboard.html', context)

# Trainer dashboard
@login_required
def trainer_dashboard(request):
    trainer = request.user
    today = date.today()

    # --- Fetch all classes for this trainer (like your working view) ---
    trainer_classes = PrivateClass.objects.filter(trainer=trainer).order_by('start_date', 'start_time')

    # --- Stats ---
    total_classes = trainer_classes.count()
    classes_today_qs = trainer_classes.filter(start_date=today)
    classes_today = classes_today_qs.count()
    unique_members = trainer_classes.values('member').distinct().count()

    upcoming_classes_qs = trainer_classes.filter(start_date__gte=today, start_date__lte=today + timedelta(days=7))

    # --- Revenue ---
    total_revenue = Payment.objects.filter(private_class__trainer=trainer, payment_status='Paid').aggregate(total=Sum('amount'))['total'] or 0

    # --- Prepare classes for template safely ---
    def prepare_session(session):
        return {
            'member': session.member or type('obj', (), {'full_name': 'Unknown Member'})(),
            'start_date': session.start_date,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'duration_hours': session.duration_hours,
            'duration_months': session.duration_months,
            'price': session.price or 0,
            'is_active': session.is_active,
        }

    today_classes = [prepare_session(s) for s in classes_today_qs]
    upcoming_classes = [prepare_session(s) for s in upcoming_classes_qs]

    context = {
        'user': trainer,
        'today_classes': today_classes,
        'upcoming_classes': upcoming_classes,
        'classes_today': classes_today,
        'total_classes': total_classes,
        'unique_members': unique_members,
        'total_revenue': total_revenue,
    }

    return render(request, 'trainer/dashboard.html', context)

#admin trainer

def trainer_list(request):
    trainers = User.objects.filter(role='Trainer').order_by('-created_at')
    return render(request, 'admin/trainer.html', {'trainers': trainers})

def trainer_add(request):
    """Add a new trainer"""
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        specialization = request.POST.get('specialization')
        experience_years = request.POST.get('experience_years')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender') or None
        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        is_active = request.POST.get('is_active') == 'on'

        # Convert numeric fields
        experience_years = int(experience_years) if experience_years else 0
        age = int(age) if age else None
        height = float(height) if height else None
        weight = float(weight) if weight else None

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'admin/trainer_add.html', request.POST)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'admin/trainer_add.html', request.POST)

        # Create trainer
        trainer = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='Trainer',
            specialization=specialization,
            experience_years=experience_years,
            phone=phone,
            gender=gender,
            age=age,
            height=height,
            weight=weight,
            is_active=is_active,
            must_set_password=True
        )

        # Admin-created accounts must set password on first login
        trainer.set_unusable_password()
        trainer.save()

        messages.success(request, f"Trainer {trainer.full_name} added successfully!")
        return redirect('admin-trainers')

    return render(request, 'admin/trainer_add.html')


def trainer_edit(request, trainer_id):
    """Edit existing trainer"""
    trainer = get_object_or_404(User, id=trainer_id, role='Trainer')

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        specialization = request.POST.get('specialization')
        experience_years = request.POST.get('experience_years')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender') or None
        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        is_active = request.POST.get('is_active') == 'on'

        # Convert numeric fields
        experience_years = int(experience_years) if experience_years else 0
        age = int(age) if age else None
        height = float(height) if height else None
        weight = float(weight) if weight else None

        # Check if username or email already exists (excluding current trainer)
        if User.objects.filter(username=username).exclude(id=trainer.id).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'admin/trainer_edit.html', {'trainer': trainer})

        if User.objects.filter(email=email).exclude(id=trainer.id).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'admin/trainer_edit.html', {'trainer': trainer})

        # Update fields
        trainer.username = username
        trainer.first_name = first_name
        trainer.last_name = last_name
        trainer.email = email
        trainer.specialization = specialization
        trainer.experience_years = experience_years
        trainer.phone = phone
        trainer.gender = gender
        trainer.age = age
        trainer.height = height
        trainer.weight = weight
        trainer.is_active = is_active

        # Only set new password if provided
        if password:
            trainer.set_password(password)
            trainer.must_set_password = False

        trainer.save()
        messages.success(request, f"Trainer {trainer.full_name} updated successfully!")
        return redirect('admin-trainers')

    return render(request, 'admin/trainer_edit.html', {'trainer': trainer})



def trainer_delete(request, trainer_id):
    """Delete a trainer"""
    trainer = get_object_or_404(User, id=trainer_id, role='Trainer')
    trainer.delete()
    messages.success(request, f"{trainer.full_name} deleted successfully!")
    return redirect('admin-trainers')


# =========================
# User Payment - Pay Pending Payments
# =========================
@login_required
def pay_pending_payment(request, payment_id):
    """Handle payment for a pending payment record"""
    from django_esewa import EsewaPayment
    
    # Get the payment record
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Verify the payment belongs to the current user and check if payment is pending
    if payment.payment_status != 'Pending':
        messages.error(request, "This payment is not pending.")
        return redirect('my-payments')
    
    # Create eSewa payment
    transaction_uuid = payment.uid
    paymentEsewa = EsewaPayment(
        product_code="EPAYTEST",
        success_url=f"http://localhost:8000/payment/success/{transaction_uuid}/",
        failure_url=f"http://localhost:8000/payment/failure/{transaction_uuid}/",
        amount=float(payment.amount),
        tax_amount=0,
        total_amount=float(payment.amount),
        product_service_charge=0,
        product_delivery_charge=0,
        transaction_uuid=str(transaction_uuid),
    )
    
    signature = paymentEsewa.create_signature()
    
    # If membership payment, use membership checkout template
    if payment.member_subscription:
        if payment.member_subscription.member != request.user:
            messages.error(request, "You don't have permission to access this payment.")
            return redirect('my-payments')
        
        plan = payment.member_subscription.plan
        context = {
            'plan': plan,
            'subscription': payment.member_subscription,
            'payment': payment,
            'form': paymentEsewa.generate_form()
        }
        return render(request, 'membership/esewa_checkout.html', context)
    
    # If private class payment, use private class checkout template
    elif payment.private_class:
        if payment.private_class.member != request.user:
            messages.error(request, "You don't have permission to access this payment.")
            return redirect('my-payments')
        
        trainer = payment.private_class.trainer
        context = {
            'trainer': trainer,
            'private_class': payment.private_class,
            'payment': payment,
            'form': paymentEsewa.generate_form()
        }
        return render(request, 'classes/private_class_checkout.html', context)
    
    messages.error(request, "Invalid payment record.")
    return redirect('my-payments')


# =========================
# Cancel Payment
# =========================
@login_required
def cancel_payment(request, payment_id):
    """Cancel a pending payment and deactivate associated subscription or private class"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Verify the payment belongs to the current user
    if payment.member_subscription and payment.member_subscription.member != request.user:
        messages.error(request, "You don't have permission to cancel this payment.")
        return redirect('my-payments')
    elif payment.private_class and payment.private_class.member != request.user:
        messages.error(request, "You don't have permission to cancel this payment.")
        return redirect('my-payments')
    
    # Check if payment is pending
    if payment.payment_status != 'Pending':
        messages.error(request, "Only pending payments can be cancelled.")
        return redirect('my-payments')
    
    # Cancel the payment
    payment.payment_status = 'Cancelled'
    payment.save()
    
    # If this payment is for a subscription, deactivate the subscription
    if payment.member_subscription:
        subscription = payment.member_subscription
        subscription.is_active = False
        subscription.save()
        messages.success(request, "Payment and subscription have been cancelled successfully.")
    # If this payment is for a private class, deactivate the class booking
    elif payment.private_class:
        private_class = payment.private_class
        private_class.is_active = False
        private_class.save()
        messages.success(request, "Payment and private class booking have been cancelled successfully.")
    else:
        messages.success(request, "Payment has been cancelled successfully.")
    
    return redirect('my-payments')






# admin member's management
@login_required
@admin_required
def member_list(request):
    """List all members"""
    members = User.objects.filter(role='Member').order_by('-created_at')
    return render(request, 'admin/members_list.html', {'members': members})


@login_required
@admin_required
def member_add(request):
    """Add a new member"""
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender') or None
        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        fitness_goal = request.POST.get('fitness_goal')
        membership_start_date = request.POST.get('membership_start_date')
        is_active = request.POST.get('is_active') == 'on'

        # Convert numeric fields
        age = int(age) if age else None
        height = float(height) if height else None
        weight = float(weight) if weight else None

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'admin/member_add.html', request.POST)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'admin/member_add.html', request.POST)

        # Create member
        member = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='Member',
            phone=phone,
            gender=gender,
            age=age,
            height=height,
            weight=weight,
            fitness_goal=fitness_goal,
            membership_start_date=membership_start_date,
            is_active=is_active,
            must_set_password=True
        )

        # Admin-created accounts must set password on first login
        member.set_unusable_password()
        member.save()

        messages.success(request, f"Member {member.full_name} added successfully!")
        return redirect('admin-members')

    return render(request, 'admin/member_add.html')


@login_required
@admin_required
def member_edit(request, member_id):
    """Edit existing member"""
    member = get_object_or_404(User, id=member_id, role='Member')

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender') or None
        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        fitness_goal = request.POST.get('fitness_goal')
        membership_start_date = request.POST.get('membership_start_date')
        is_active = request.POST.get('is_active') == 'on'

        # Convert numeric fields
        age = int(age) if age else None
        height = float(height) if height else None
        weight = float(weight) if weight else None

        # Check if username or email already exists (excluding current member)
        if User.objects.filter(username=username).exclude(id=member.id).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'admin/member_edit.html', {'member': member})

        if User.objects.filter(email=email).exclude(id=member.id).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'admin/member_edit.html', {'member': member})

        # Update member
        member.username = username
        member.first_name = first_name
        member.last_name = last_name
        member.email = email
        member.phone = phone
        member.gender = gender
        member.age = age
        member.height = height
        member.weight = weight
        member.fitness_goal = fitness_goal
        member.membership_start_date = membership_start_date
        member.is_active = is_active

        if password:
            member.set_password(password)
            member.must_set_password = False

        member.save()
        messages.success(request, f"Member {member.full_name} updated successfully!")
        return redirect('admin-members')

    return render(request, 'admin/member_edit.html', {'member': member})


@login_required
@admin_required
def member_delete(request, member_id):
    """Delete a member"""
    member = get_object_or_404(User, id=member_id, role='Member')
    member.delete()
    messages.success(request, f"{member.full_name} deleted successfully!")
    return redirect('admin-members')


# =========================
@admin_required
@login_required
def admin_reports(request):
    today = date.today()

    total_users = User.objects.count()
    active_members = User.objects.filter(role='Member', is_active=True).count()
    total_trainers = User.objects.filter(role='Trainer', is_active=True).count()
    active_subscriptions = MemberSubscription.objects.filter(is_active=True).count()
    expired_subscriptions = MemberSubscription.objects.filter(is_active=False).count()
    total_classes = PrivateClass.objects.count()
    active_sessions_today = PrivateClass.objects.filter(start_date=today, is_active=True).count()
    upcoming_classes = PrivateClass.objects.filter(start_date__gte=today, start_date__lte=today + timedelta(days=7))
    total_revenue = Payment.objects.filter(payment_status='Paid').aggregate(total=Sum('amount'))['total'] or 0
    pending_payments = Payment.objects.filter(payment_status='Pending').count()
    failed_payments = Payment.objects.filter(payment_status='Failed').count()
    recent_bookings = PrivateClass.objects.select_related('member', 'trainer').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('member_subscription__member', 'private_class').order_by('-payment_date')[:5]

    context = {
        'today': today,
        'total_users': total_users,
        'active_members': active_members,
        'total_trainers': total_trainers,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'total_classes': total_classes,
        'active_sessions_today': active_sessions_today,
        'upcoming_classes': upcoming_classes,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
    }

    return render(request, 'admin/admin_reports.html', context)


# =========================
# Admin Reports PDF (xhtml2pdf)
# =========================
@login_required
@admin_required
def admin_reports_pdf(request):
    today = date.today()
    now = datetime.now()

    # Queries
    total_users = User.objects.count()
    active_members = User.objects.filter(role='Member', is_active=True).count()
    total_trainers = User.objects.filter(role='Trainer', is_active=True).count()
    active_subscriptions = MemberSubscription.objects.filter(is_active=True).count()
    expired_subscriptions = MemberSubscription.objects.filter(is_active=False).count()
    total_classes = PrivateClass.objects.count()
    active_sessions_today = PrivateClass.objects.filter(start_date=today, is_active=True).count()
    upcoming_classes = PrivateClass.objects.filter(start_date__gte=today, start_date__lte=today + timedelta(days=7))
    total_revenue = Payment.objects.filter(payment_status__iexact='Paid').aggregate(total=Sum('amount'))['total'] or 0
    pending_payments = Payment.objects.filter(payment_status__iexact='Pending').count()
    failed_payments = Payment.objects.filter(payment_status__iexact='Failed').count()
    recent_bookings = PrivateClass.objects.select_related('member', 'trainer').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('member_subscription__member', 'private_class').order_by('-payment_date')[:5]

    context = {
        'today': today,
        'now': now,
        'total_users': total_users,
        'active_members': active_members,
        'total_trainers': total_trainers,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'total_classes': total_classes,
        'active_sessions_today': active_sessions_today,
        'upcoming_classes': upcoming_classes,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
    }

    html_string = render_to_string('admin/admin_reports_pdf.html', context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="admin_report.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF <pre>' + html_string + '</pre>')

    return response


# ==========================================
# Weight Tracking Views
# ==========================================

@login_required
def track_progress(request):
    """
    Weight tracking page with chart and log history
    """
    user = request.user
    today = date.today()
    
    # Get weight logs for the last 90 days
    ninety_days_ago = today - timedelta(days=90)
    weight_logs = WeightLog.objects.filter(
        user=user,
        date__gte=ninety_days_ago
    ).order_by('date')
    
    # Calculate stats
    stats = {
        'first_weight': None,
        'latest_weight': None,
        'latest_bmi': None,
        'weight_change': None,
    }
    
    if weight_logs.exists():
        first_log = weight_logs.first()
        latest_log = weight_logs.last()
        
        stats['first_weight'] = first_log.weight
        stats['latest_weight'] = latest_log.weight
        stats['latest_bmi'] = latest_log.bmi
        stats['weight_change'] = float(latest_log.weight) - float(first_log.weight)
    
    context = {
        'weight_logs': weight_logs,
        'stats': stats,
        'today': today,
    }
    
    return render(request, 'user/track_progress.html', context)


@login_required
def log_weight(request):
    """
    Add or update weight log entry
    """
    if request.method == 'POST':
        weight = request.POST.get('weight')
        log_date = request.POST.get('date', date.today())
        notes = request.POST.get('notes', '')
        
        if weight:
            try:
                # Create or update weight log for this date
                weight_log, created = WeightLog.objects.update_or_create(
                    user=request.user,
                    date=log_date,
                    defaults={
                        'weight': weight,
                        'notes': notes
                    }
                )
                
                if created:
                    messages.success(request, f'Weight logged: {weight}kg on {log_date}')
                else:
                    messages.success(request, f'Weight updated: {weight}kg on {log_date}')
                    
            except Exception as e:
                messages.error(request, f'Error logging weight: {str(e)}')
        else:
            messages.error(request, 'Please enter a valid weight')
    
    return redirect('track-progress')


@login_required
def delete_weight_log(request, log_id):
    """
    Delete a weight log entry
    """
    weight_log = get_object_or_404(WeightLog, id=log_id, user=request.user)
    weight_log.delete()
    messages.success(request, 'Weight log deleted')
    return redirect('track-progress')


@login_required
def weight_chart_data(request):
    """
    API endpoint for chart data (JSON)
    """
    days = int(request.GET.get('days', 30))
    today = date.today()
    start_date = today - timedelta(days=days)
    
    weight_logs = WeightLog.objects.filter(
        user=request.user,
        date__gte=start_date
    ).order_by('date')
    
    data = {
        'labels': [log.date.strftime('%b %d') for log in weight_logs],
        'weights': [float(log.weight) for log in weight_logs],
    }
    
    return JsonResponse(data)