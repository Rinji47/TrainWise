# classes/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import PrivateClass
from accounts.models import User  # Your custom User model
from django.contrib.auth.decorators import login_required
from membership.models import Payment 
from django.db.models import Sum, Q
from datetime import date
from django_esewa import EsewaPayment
import uuid




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

    if request.method == "POST":
        duration_hours = int(request.POST.get('duration_hours', 1))
        duration_months = int(request.POST.get('duration_months', 1))
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')

        # Calculate price
        temp_class = PrivateClass(
            member=request.user,
            trainer=trainer,
            start_date=start_date,
            start_time=start_time,
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
                start_date=start_date,
                start_time=start_time,
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
        from datetime import datetime, timedelta
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        start_datetime = datetime.combine(datetime.today(), start_time_obj)
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        end_time = end_datetime.time().strftime('%H:%M')
        
        # Store private class details in session
        request.session['pending_private_class'] = {
            'trainer_id': trainer.id,
            'start_date': start_date,
            'start_time': start_time,
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
            'form': paymentEsewa.generate_form()
        }
        return render(request, 'classes/private_class_checkout.html', context)

    # Pass trainer info to template for JS price calculation
    trainer_experience = getattr(trainer, 'experience_level', 0)
    base_rate = 500 

    context = {
        'trainer': trainer,
        'trainer_experience': trainer_experience,
        'base_rate': base_rate,
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
        messages.success(request, f'Your session with {session.trainer.get_full_name} has been canceled.')
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
    payments = Payment.objects.filter(private_class__trainer=trainer, payment_status='Paid')
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
        # NOW create the private class and payment records
        private_class = PrivateClass.objects.create(
            member=request.user,
            trainer=trainer,
            start_date=pending_data['start_date'],
            start_time=pending_data['start_time'],
            end_time=pending_data['end_time'],
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