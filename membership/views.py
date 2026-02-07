from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import MembershipPlan, MemberSubscription, Payment
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_http_methods
from django_esewa import EsewaPayment
import uuid

# ===============================
# Membership Plans
# ===============================
def admin_memberships(request):
    memberships = MembershipPlan.objects.all()
    return render(request, 'admin/memberships.html', {'memberships': memberships})

def admin_membership_add(request):
    if request.method == 'POST':
        plan = MembershipPlan(
            plan_name=request.POST.get('plan_name'),
            duration_months=request.POST.get('duration_months'),
            price=request.POST.get('price'),
            description=request.POST.get('description')
        )
        plan.save()
        messages.success(request, 'Membership plan added successfully.')
        return redirect('admin-memberships')
    return render(request, 'admin/membership_form.html')

def admin_membership_edit(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)
    if request.method == 'POST':
        plan.plan_name = request.POST.get('plan_name')
        plan.duration_months = request.POST.get('duration_months')
        plan.price = request.POST.get('price')
        plan.description = request.POST.get('description')
        plan.save()
        messages.success(request, 'Membership plan updated successfully.')
        return redirect('admin-memberships')
    return render(request, 'admin/membership_form.html', {'plan': plan})

def admin_membership_delete(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)
    plan.delete()
    messages.success(request, 'Membership plan deleted successfully.')
    return redirect('admin-memberships')


# ===============================
# Payments Admin
# ===============================
def admin_payments(request):
    status_filter = request.GET.get('status', '')
    method_filter = request.GET.get('method', '')
    
    payments = Payment.objects.select_related(
        'member_subscription__member', 
        'private_class__member'
    ).all().order_by('-payment_date')

    # Totals
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
    paid_amount = payments.filter(payment_status='Paid').aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = payments.filter(payment_status='Pending').aggregate(total=Sum('amount'))['total'] or 0
    failed_amount = payments.filter(payment_status='Failed').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'payments': payments,
        'total_payments': total_payments,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'failed_amount': failed_amount,
        'status_filter': status_filter,
        'method_filter': method_filter,
    }
    return render(request, 'admin/payments.html', context)



# Optional: View single payment details (for modal or detail page)
def admin_payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'admin/payment_detail.html', {'payment': payment})


def membership_plans(request):
    plans = MembershipPlan.objects.all()
    
    # Optional: check if user already subscribed
    user_subscription = None
    if request.user.is_authenticated:
        user_subscription = MemberSubscription.objects.filter(
            member=request.user, is_active=True
        ).first()
    
    return render(request, 'membership/membership_plans.html', {
        'plans': plans,
        'user_subscription': user_subscription
    })

@login_required
@login_required
def purchase_membership(request, plan_id):
    """
    Create transaction and show eSawa payment form
    Stack subscriptions: new subscription starts after the last ACTIVE one ends
    """
    plan = get_object_or_404(MembershipPlan, id=plan_id)

    if request.method == 'POST':
        from datetime import date, timedelta
        
        today = date.today()  # Use local date, not timezone-aware
        
        # Calculate duration in days from plan's duration_months
        duration_days = 30 * plan.duration_months
        
        # ONLY look at active subscriptions - cancelled ones should be ignored completely
        active_subs = MemberSubscription.objects.filter(
            member=request.user,
            is_active=True
        ).order_by('start_date')
        
        # Default: start from today
        start_date = today
        
        if active_subs.exists():
            # We have active subscriptions, try to find a gap
            found_gap = False
            
            for i, sub in enumerate(active_subs):
                if i == 0:
                    # Check gap before first active subscription
                    if sub.start_date > today:
                        gap_size = (sub.start_date - today).days
                        if gap_size >= duration_days:
                            # Found a gap big enough at the beginning
                            start_date = today
                            found_gap = True
                            break
                
                # Check gap between this subscription and the next
                if i < len(active_subs) - 1:
                    next_sub = active_subs[i + 1]
                    potential_start = sub.end_date + timedelta(days=1)
                    gap_size = (next_sub.start_date - potential_start).days
                    
                    if gap_size >= duration_days:
                        # Found a gap big enough between subscriptions
                        start_date = potential_start
                        found_gap = True
                        break
            
            if not found_gap:
                # No gap found, stack after the last active subscription
                last_sub = active_subs.last()
                start_date = last_sub.end_date + timedelta(days=1)
        # else: start_date remains today (no active subscriptions)

        # Check if this is a demo/test payment
        if request.POST.get('demo_payment') == 'true':
            subscription = MemberSubscription(
                member=request.user,
                plan=plan,
                start_date=start_date
            )
            subscription.save()

            payment = Payment.objects.create(
                member_subscription=subscription,
                amount=plan.price,
                tax_amount=0,
                service_charge=0,
                delivery_charge=0,
                payment_method='Demo',
                payment_status='Completed'
            )
            
            subscription.is_active = True
            subscription.save()
            
            messages.success(request, f"Demo payment successful! Your subscription to '{plan.plan_name}' is now active.")
            return redirect('my-memberships')

        # Normal eSewa flow - store data in session, don't create DB records yet
        transaction_uuid = uuid.uuid4()
        
        # Store subscription details in session for later creation
        request.session['pending_subscription'] = {
            'plan_id': plan.id,
            'start_date': start_date.isoformat(),
            'transaction_uuid': str(transaction_uuid),
            'amount': float(plan.price)
        }

        paymentEsewa = EsewaPayment(
            product_code="EPAYTEST",
            success_url=f"http://localhost:8000/success/{transaction_uuid}/",
            failure_url=f"http://localhost:8000/failure/{transaction_uuid}/",
            amount=float(plan.price),
            tax_amount=0,
            total_amount=float(plan.price),
            product_service_charge=0,
            product_delivery_charge=0,
            transaction_uuid=str(transaction_uuid),
        )
        
        signature = paymentEsewa.create_signature()

        context = {
            'plan': plan,
            'form': paymentEsewa.generate_form()
        }
        return render(request, 'membership/esewa_checkout.html', context)

    return render(request, 'membership/purchase_membership.html', {'plan': plan})

def success(request, uid):
    from datetime import datetime
    
    # Get pending subscription data from session
    pending_data = request.session.get('pending_subscription')
    if not pending_data or pending_data.get('transaction_uuid') != str(uid):
        messages.error(request, "Invalid or expired payment session.")
        return redirect('membership-plans')
    
    # Get plan
    plan = get_object_or_404(MembershipPlan, id=pending_data['plan_id'])
    start_date = datetime.fromisoformat(pending_data['start_date']).date()
    
    paymentEsewa = EsewaPayment(
        product_code="EPAYTEST",
        success_url=f"http://localhost:8000/success/{uid}/",
        failure_url=f"http://localhost:8000/failure/{uid}/",
        amount=float(pending_data['amount']),
        tax_amount=0,
        total_amount=float(pending_data['amount']),
        product_service_charge=0,
        product_delivery_charge=0,
        transaction_uuid=str(uid),
    )
    signature = paymentEsewa.create_signature()
    
    if paymentEsewa.is_completed(dev=True):
        # NOW create the subscription and payment records
        subscription = MemberSubscription.objects.create(
            member=request.user,
            plan=plan,
            start_date=start_date,
            is_active=True
        )
        
        payment = Payment.objects.create(
            uid=uid,
            member_subscription=subscription,
            amount=pending_data['amount'],
            tax_amount=0,
            service_charge=0,
            delivery_charge=0,
            payment_method='Esewa',
            payment_status='Completed'
        )
        
        # Clear session data
        del request.session['pending_subscription']
        
        context = {
            'payment': payment,
            'subscription': subscription,
        }
        messages.success(request, f"Payment completed: {payment.uid}")
        return render(request, 'membership/payment_success.html', context)
    
    return redirect('failure', uid)

def failure(request, uid):
    # Get pending subscription from session to show details
    pending_data = request.session.get('pending_subscription')
    
    # Clear pending subscription from session
    if 'pending_subscription' in request.session:
        del request.session['pending_subscription']
    
    context = {
        'uid': uid,
        'pending_data': pending_data
    }
    messages.error(request, f"Payment failed: {uid}")
    return render(request, "membership/payment_failure.html", context)
    

@login_required
def my_memberships(request):
    """
    Display all memberships for the logged-in user.
    - Shows history of all subscriptions
    - Shows days left only for subscriptions that have started
    """
    from datetime import date
    today = date.today()

    # Fetch all subscriptions for the user, ordered by start date
    subscriptions = MemberSubscription.objects.filter(member=request.user).order_by('start_date')

    # Find active subscription that has STARTED (not future subscriptions)
    latest_active = subscriptions.filter(
        is_active=True,
        start_date__lte=today,  # Must have started already
        end_date__gte=today     # Not expired yet
    ).order_by('-end_date').first()

    if latest_active:
        days_left = (latest_active.end_date - today).days
    else:
        days_left = None

    context = {
        'subscriptions': subscriptions,
        'days_left': days_left,
        'today': today,
    }

    return render(request, 'user/my_membership.html', context)


@login_required
def cancel_membership(request, subscription_id):
    """
    Cancel a subscription by marking it as inactive.
    Also cancels any pending payments associated with it.
    """
    subscription = get_object_or_404(
        MemberSubscription,
        id=subscription_id,
        member=request.user,
        is_active=True
    )
    
    if request.method == 'POST':
        subscription.is_active = False
        subscription.save()
        
        # Also cancel any pending payments for this subscription
        pending_payments = Payment.objects.filter(
            member_subscription=subscription,
            payment_status='Pending'
        )
        pending_payments.update(payment_status='Cancelled')
        
        messages.success(
            request,
            f"Your subscription for '{subscription.plan.plan_name}' has been cancelled."
        )
        return redirect('my-memberships')
    
    # If someone tries to access via GET
    messages.warning(request, "Invalid request. Use the Cancel button to cancel a subscription.")
    return redirect('my-memberships')




@login_required
def my_payments(request):
    """
    Show all payments for the logged-in user (memberships + private classes)
    - Includes filters and total amounts per status
    """
    # Fetch all payments related to this user
    payments = Payment.objects.filter(
        member_subscription__member=request.user
    ) | Payment.objects.filter(
        private_class__member=request.user
    )
    payments = payments.order_by('-payment_date')  # latest first

    # Calculate total amounts by status
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
    paid_amount = payments.filter(payment_status='Completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = payments.filter(payment_status='Pending').aggregate(total=Sum('amount'))['total'] or 0
    cancelled_amount = payments.filter(payment_status='Cancelled').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'payments': payments,
        'total_payments': total_payments,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'cancelled_amount': cancelled_amount,
    }

    return render(request, 'user/my_payments.html', context)


# =========================
# Pending Payment Handlers
# =========================
@require_http_methods(['GET', 'POST'])
def payment_success(request, uid):
    """Handle successful payment for pending payments"""
    try:
        payment = Payment.objects.get(uid=uid)
        payment.payment_status = 'Completed'
        payment.save()
        messages.success(request, "Payment completed successfully!")
        return redirect('user-dashboard')
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('user-dashboard')


@require_http_methods(['GET', 'POST'])
def payment_failure(request, uid):
    """Handle failed payment for pending payments"""
    try:
        payment = Payment.objects.get(uid=uid)
        payment.payment_status = 'Failed'
        payment.save()
        messages.error(request, "Payment failed. Please try again.")
        return redirect('user-dashboard')
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('user-dashboard')