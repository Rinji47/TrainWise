# classes/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import PrivateClass
from accounts.models import User  # Your custom User model
from django.contrib.auth.decorators import login_required
from membership.models import Payment 
from django.db.models import Sum, Q
from datetime import date
from dateutil.relativedelta import relativedelta
from django_esewa import EsewaPayment
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import requests
import uuid
from django.urls import reverse




# Helper to restrict admin views
def admin_required(user):
    return user.is_authenticated and user.role == 'Admin'


@user_passes_test(admin_required)
def admin_private_classes_list(request):
    """
    Admin view to list all member-created private classes.
    Admin can edit or delete, but not create new classes.
    """
    private_classes = PrivateClass.objects.select_related('member', 'trainer').all().order_by('start_date', 'start_time')

    context = {
        'private_classes': private_classes
    }
    return render(request, 'admin/private_classes_list.html', context)


@user_passes_test(admin_required)
def admin_private_class_edit(request, pk):
    """
    Admin can edit a private class: assign trainer, update duration hours or months.
    User cannot be changed.
    """
    private_class = get_object_or_404(PrivateClass, id=pk)

    if request.method == 'POST':
        trainer_id = request.POST.get('trainer')
        duration_hours = request.POST.get('duration_hours')
        duration_months = request.POST.get('duration_months')

        # Update trainer
        if trainer_id:
            trainer = User.objects.filter(id=trainer_id, role='Trainer').first()
            private_class.trainer = trainer

        # Update duration hours (max 3)
        if duration_hours:
            try:
                hours = int(duration_hours)
                private_class.duration_hours = min(hours, 3)
            except ValueError:
                messages.error(request, "Duration hours must be a number.")

        # Update duration months
        if duration_months:
            try:
                months = int(duration_months)
                private_class.duration_months = months
            except ValueError:
                messages.error(request, "Duration months must be a number.")

        private_class.save()
        messages.success(request, f"Private class for '{private_class.member.get_full_name()}' updated successfully.")
        return redirect('admin-private-classes-list')

    # Get all trainers for dropdown
    trainers = User.objects.filter(role='Trainer')
    context = {
        'private_class': private_class,
        'trainers': trainers,
    }
    return render(request, 'admin/private_class_edit.html', context)


@user_passes_test(admin_required)
def admin_private_class_toggle(request, pk):
    private_class = get_object_or_404(PrivateClass, id=pk)
    private_class.is_active = not private_class.is_active
    private_class.save()
    messages.success(request, f"Private class has been {'activated' if private_class.is_active else 'deactivated'}.")
    return redirect('admin-private-classes-list')





def book_private_class_select_trainer(request):
    """
    Show all available trainers to the user.
    Clicking a trainer will go to the login page if not logged in.
    """
    trainers = User.objects.filter(role='Trainer', is_active=True)

    context = {
        'trainers': trainers
    }
    return render(request, 'classes/book_private_class_select_trainer.html', context)

@login_required
def book_private_class_details(request, trainer_id):
    trainer = get_object_or_404(User, id=trainer_id, role='Trainer')
    today = date.today()
    max_start_date = today + relativedelta(months=3)

    if request.method == "POST":
        duration_hours = int(request.POST.get('duration_hours', 1))
        duration_months = int(request.POST.get('duration_months', 1))
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')

        # Validate date range (today through next 3 months, inclusive)
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            messages.error(request, "Please choose a valid start date.")
            return render(request, 'classes/book_private_class_details.html', {
                'trainer': trainer,
                'trainer_experience': getattr(trainer, 'experience_level', 0),
                'base_rate': 500,
                'start_date_min': today.isoformat(),
                'start_date_max': max_start_date.isoformat(),
            })

        if start_date_obj < today or start_date_obj > max_start_date:
            messages.error(request, "Start date must be between today and the next 3 months.")
            return render(request, 'classes/book_private_class_details.html', {
                'trainer': trainer,
                'trainer_experience': getattr(trainer, 'experience_level', 0),
                'base_rate': 500,
                'start_date_min': today.isoformat(),
                'start_date_max': max_start_date.isoformat(),
            })

        # Validate time format and booking overlap for this trainer/date
        try:
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        except (TypeError, ValueError):
            messages.error(request, "Please choose a valid start time.")
            return render(request, 'classes/book_private_class_details.html', {
                'trainer': trainer,
                'trainer_experience': getattr(trainer, 'experience_level', 0),
                'base_rate': 500,
                'start_date_min': today.isoformat(),
                'start_date_max': max_start_date.isoformat(),
            })

        requested_start = datetime.combine(start_date_obj, start_time_obj)
        requested_end = requested_start + timedelta(hours=duration_hours)

        existing_sessions = PrivateClass.objects.filter(
            trainer=trainer,
            start_date=start_date_obj,
            is_active=True
        )

        for session in existing_sessions:
            existing_start = datetime.combine(session.start_date, session.start_time)
            existing_end = existing_start + timedelta(hours=session.duration_hours)
            if requested_start < existing_end and requested_end > existing_start:
                messages.error(
                    request,
                    "Trainer is already booked for that time range. Please pick a different time."
                )
                return render(request, 'classes/book_private_class_details.html', {
                    'trainer': trainer,
                    'trainer_experience': getattr(trainer, 'experience_level', 0),
                    'base_rate': 500,
                    'start_date_min': today.isoformat(),
                    'start_date_max': max_start_date.isoformat(),
                })

        # Calculate price
        temp_class = PrivateClass(
            member=request.user,
            trainer=trainer,
            start_date=start_date_obj,
            start_time=start_time_obj,
            duration_hours=duration_hours,
            duration_months=duration_months,
        )
        calculated_price = temp_class.calculate_price()

        # Check if this is a demo payment
        if request.POST.get('demo_payment') == 'true':
            # For demo, create immediately
            private_class = PrivateClass.objects.create(
                member=request.user,
                trainer=trainer,
                start_date=start_date_obj,
                start_time=start_time_obj,
                duration_hours=duration_hours,
                duration_months=duration_months,
                price=calculated_price,
                is_active=True
            )
            payment = Payment.objects.create(
                private_class=private_class,
                amount=calculated_price,
                tax_amount=0,
                service_charge=0,
                delivery_charge=0,
                payment_method='Demo',
                payment_status='Completed'
            )
            messages.success(request, f"Demo payment successful! Your private class booking is confirmed.")
            return redirect('my-booked-sessions')

        # Normal eSewa flow - store in session, don't create DB records yet
        transaction_uuid = uuid.uuid4()
        
        # Calculate end time
        start_datetime = datetime.combine(start_date_obj, start_time_obj)
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        end_time = end_datetime.time().strftime('%H:%M')
        
        # Store private class details in session
        request.session['pending_private_class'] = {
            'trainer_id': trainer.id,
            'start_date': start_date_obj.isoformat(),
            'start_time': start_time_obj.strftime('%H:%M'),
            'end_time': end_time,
            'duration_hours': duration_hours,
            'duration_months': duration_months,
            'price': float(calculated_price),
            'transaction_uuid': str(transaction_uuid)
        }

        paymentEsewa = EsewaPayment(
            product_code="EPAYTEST",
            success_url=f"http://localhost:8000/private-class/success/{transaction_uuid}/",
            failure_url=f"http://localhost:8000/private-class/failure/{transaction_uuid}/",
            amount=float(calculated_price),
            tax_amount=0,
            total_amount=float(calculated_price),
            product_service_charge=0,
            product_delivery_charge=0,
            transaction_uuid=str(transaction_uuid),
        )
        
        signature = paymentEsewa.create_signature()
        
        # Get the session data for display
        pending_data = request.session['pending_private_class']

        context = {
            'trainer': trainer,
            'price': calculated_price,
            'pending_data': pending_data,
            'form': paymentEsewa.generate_form(),
            'khalti_amount': int(float(calculated_price) * 100),
            'khalti_order_id': str(transaction_uuid),
            'khalti_order_name': f"Private class with {trainer.get_full_name()}",
            'khalti_website_url': request.build_absolute_uri('/'),
            'khalti_return_url': request.build_absolute_uri(
                reverse('khalti-return-private-class', args=[transaction_uuid])
            ),
        }
        return render(request, 'classes/private_class_checkout.html', context)

    # Pass trainer info to template for JS price calculation
    trainer_experience = getattr(trainer, 'experience_level', 0)
    base_rate = 500 

    context = {
        'trainer': trainer,
        'trainer_experience': trainer_experience,
        'base_rate': base_rate,
        'start_date_min': today.isoformat(),
        'start_date_max': max_start_date.isoformat(),
    }
    return render(request, 'classes/book_private_class_details.html', context)


@login_required
def my_booked_sessions(request):
    # Fetch all private classes booked by this user, ordered by date and time
    sessions = PrivateClass.objects.filter(member=request.user).order_by('start_date', 'start_time')
    return render(request, 'user/my_booked_sessions.html', {'sessions': sessions})




# --------------------------
# Cancel Private Class
# --------------------------
@login_required
def cancel_private_class(request, pk):
    session = get_object_or_404(PrivateClass, pk=pk, member=request.user, is_active=True)

    if request.method == 'POST':
        session.is_active = False
        session.save()
        messages.success(request, f'Your session with {session.trainer.get_full_name()} has been canceled.')
        return redirect('my-booked-sessions')

    messages.error(request, 'Invalid request for canceling session.')
    return redirect('my-booked-sessions')

def trainer_private_classes(request):
    trainer = request.user

    # All classes for this trainer
    trainer_classes = PrivateClass.objects.filter(trainer=trainer).order_by('start_date', 'start_time')

    # Stats
    total_sessions = trainer_classes.count()
    active_sessions = trainer_classes.filter(is_active=True).count()
    upcoming_classes = trainer_classes.filter(start_date__gte=date.today())

    # Revenue from payments for this trainer's private classes
    payments = Payment.objects.filter(private_class__trainer=trainer, payment_status='Completed')
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'trainer_classes': trainer_classes,
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'upcoming_sessions': upcoming_classes.count(),
        'upcoming_classes': upcoming_classes,
        'total_revenue': total_revenue,
    }
    return render(request, 'trainer/trainer_private_classes.html', context)


# ===============================
# Private Class Payment Handlers
# ===============================

def private_class_success(request, uid):
    """Handle successful private class payment via eSewa"""
    # Get pending private class data from session
    pending_data = request.session.get('pending_private_class')
    if not pending_data or pending_data.get('transaction_uuid') != str(uid):
        messages.error(request, "Invalid or expired payment session.")
        return redirect('book-private-class')
    
    # Get trainer
    trainer = get_object_or_404(User, id=pending_data['trainer_id'], role='Trainer')
    
    paymentEsewa = EsewaPayment(
        product_code="EPAYTEST",
        success_url=f"http://localhost:8000/private-class/success/{uid}/",
        failure_url=f"http://localhost:8000/private-class/failure/{uid}/",
        amount=float(pending_data['price']),
        tax_amount=0,
        total_amount=float(pending_data['price']),
        product_service_charge=0,
        product_delivery_charge=0,
        transaction_uuid=str(uid),
    )
    signature = paymentEsewa.create_signature()
    
    if paymentEsewa.is_completed(dev=True):
        start_date_obj = datetime.strptime(pending_data['start_date'], '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(pending_data['start_time'], '%H:%M').time()

        # NOW create the private class and payment records
        private_class = PrivateClass.objects.create(
            member=request.user,
            trainer=trainer,
            start_date=start_date_obj,
            start_time=start_time_obj,
            duration_hours=pending_data['duration_hours'],
            duration_months=pending_data['duration_months'],
            price=pending_data['price'],
            is_active=True
        )
        
        payment = Payment.objects.create(
            uid=uid,
            private_class=private_class,
            amount=pending_data['price'],
            tax_amount=0,
            service_charge=0,
            delivery_charge=0,
            payment_method='Esewa',
            payment_status='Completed'
        )
        
        # Clear session data
        del request.session['pending_private_class']
        
        context = {
            'payment': payment,
            'private_class': private_class,
        }
        messages.success(request, f"Private class booking confirmed: {private_class.trainer.get_full_name()}")
        return render(request, "classes/private_class_success.html", context)
    
    return redirect('private-class-failure', uid)


def private_class_failure(request, uid):
    """Handle failed private class payment"""
    # Clear pending private class from session
    if 'pending_private_class' in request.session:
        del request.session['pending_private_class']
    
    context = {
        'uid': uid,
    }
    messages.error(request, "Private class payment failed. Please try again.")
    return render(request, "classes/private_class_failure.html", context)


@login_required
@require_http_methods(["POST"])
def khalti_initiate_private_class(request):
    return_url = request.POST.get('return_url')
    if not return_url:
        messages.error(request, "Missing Khalti return URL.")
        return redirect('book-private-class')

    base_url = (
        "https://khalti.com/api/v2/"
        if getattr(settings, 'KHALTI_ENV', 'sandbox') == 'production'
        else "https://dev.khalti.com/api/v2/"
    )
    url = f"{base_url}epayment/initiate/"
    website_url = request.POST.get('website_url') or request.build_absolute_uri('/')
    amount = request.POST.get('amount')
    purchase_order_id = request.POST.get('purchase_order_id')
    purchase_order_name = request.POST.get('purchase_order_name') or 'Private Class'

    if not getattr(settings, 'KHALTI_SECRET_KEY', ''):
        messages.error(request, "Khalti secret key is not configured.")
        return redirect('book-private-class')

    try:
        amount_value = int(amount)
    except (TypeError, ValueError):
        messages.error(request, "Invalid Khalti amount.")
        return redirect('book-private-class')

    payload = json.dumps({
        "return_url": return_url,
        "website_url": website_url,
        "amount": amount_value,
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": purchase_order_name,
        "customer_info": {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email or "",
            "phone": getattr(request.user, 'phone', '') or ""
        }
    })

    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type': 'application/json',
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=15)
    except requests.RequestException:
        messages.error(request, "Khalti initiate failed. Please try again.")
        return redirect('book-private-class')

    if response.status_code != 200:
        messages.error(request, "Khalti initiate failed. Please try again.")
        return redirect('book-private-class')

    try:
        new_res = response.json()
    except ValueError:
        messages.error(request, "Khalti initiate failed. Please try again.")
        return redirect('book-private-class')

    payment_url = new_res.get('payment_url')
    if not payment_url:
        messages.error(request, "Khalti response missing payment URL.")
        return redirect('book-private-class')

    return redirect(payment_url)


@login_required
@require_http_methods(["GET"])
def khalti_return_private_class(request, uid):
    pending_data = request.session.get('pending_private_class')
    if not pending_data or pending_data.get('transaction_uuid') != str(uid):
        messages.error(request, "Invalid or expired payment session.")
        return redirect('book-private-class')

    pidx = request.GET.get('pidx')
    if not pidx:
        messages.error(request, "Missing Khalti payment reference. Please try again.")
        return redirect('private-class-failure', uid)

    url = "https://a.khalti.com/api/v2/epayment/lookup/"
    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type': 'application/json',
    }
    data = json.dumps({'pidx': pidx})

    try:
        res = requests.request('POST', url, headers=headers, data=data, timeout=15)
    except requests.RequestException:
        messages.error(request, "Khalti verification failed. Please try again.")
        return redirect('private-class-failure', uid)

    if res.status_code != 200:
        messages.error(request, "Khalti verification failed. Please try again.")
        return redirect('private-class-failure', uid)

    try:
        new_res = res.json()
    except ValueError:
        messages.error(request, "Khalti verification failed. Please try again.")
        return redirect('private-class-failure', uid)

    status = (new_res.get('status') or '').lower()
    if status != 'completed':
        messages.error(request, "Khalti payment verification failed. Please try again.")
        return redirect('private-class-failure', uid)

    expected_amount = int(float(pending_data['price']) * 100)
    if 'total_amount' in new_res and int(new_res.get('total_amount') or 0) != expected_amount:
        messages.error(request, "Khalti payment amount mismatch. Please contact support.")
        return redirect('private-class-failure', uid)

    if 'purchase_order_id' in new_res and str(new_res.get('purchase_order_id')) != str(uid):
        messages.error(request, "Khalti payment reference mismatch. Please contact support.")
        return redirect('private-class-failure', uid)

    trainer = get_object_or_404(User, id=pending_data['trainer_id'], role='Trainer')
    start_date_obj = datetime.strptime(pending_data['start_date'], '%Y-%m-%d').date()
    start_time_obj = datetime.strptime(pending_data['start_time'], '%H:%M').time()

    private_class = PrivateClass.objects.create(
        member=request.user,
        trainer=trainer,
        start_date=start_date_obj,
        start_time=start_time_obj,
        duration_hours=pending_data['duration_hours'],
        duration_months=pending_data['duration_months'],
        price=pending_data['price'],
        is_active=True
    )
    payment = Payment.objects.create(
        uid=uid,
        private_class=private_class,
        amount=pending_data['price'],
        tax_amount=0,
        service_charge=0,
        delivery_charge=0,
        payment_method='Khalti',
        payment_status='Completed'
    )
    del request.session['pending_private_class']

    context = {
        'payment': payment,
        'private_class': private_class,
    }
    messages.success(request, f"Private class booking confirmed: {private_class.trainer.get_full_name()}")
    return render(request, "classes/private_class_success.html", context)