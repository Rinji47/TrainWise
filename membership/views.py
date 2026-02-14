from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import MembershipPlan, MemberSubscription, Payment
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.conf import settings
from django_esewa import EsewaPayment
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dodopayments import DodoPayments
import os
import uuid
import json
import requests
from datetime import date, timedelta, datetime

# ===============================
# Membership Plans
# ===============================
def admin_memberships(request):
    memberships = MembershipPlan.objects.all()
    return render(request, 'admin/memberships.html', {'memberships': memberships})

def admin_membership_add(request):
    if request.method == 'POST':
        dodo_product_id = request.POST.get('dodo_product_id')
        if not dodo_product_id:
            messages.error(request, 'Dodo product ID is required.')
            return render(request, 'admin/membership_form.html')
        plan = MembershipPlan(
            plan_name=request.POST.get('plan_name'),
            duration_months=request.POST.get('duration_months'),
            price=request.POST.get('price'),
            description=request.POST.get('description'),
            dodo_product_id=dodo_product_id
        )
        plan.save()
        messages.success(request, 'Membership plan added successfully.')
        return redirect('admin-memberships')
    return render(request, 'admin/membership_form.html')

def admin_membership_edit(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)
    if request.method == 'POST':
        dodo_product_id = request.POST.get('dodo_product_id')
        if not dodo_product_id:
            messages.error(request, 'Dodo product ID is required.')
            return render(request, 'admin/membership_form.html', {'plan': plan})
        plan.plan_name = request.POST.get('plan_name')
        plan.duration_months = request.POST.get('duration_months')
        plan.price = request.POST.get('price')
        plan.description = request.POST.get('description')
        plan.dodo_product_id = dodo_product_id
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
    paid_amount = payments.filter(payment_status='Completed').aggregate(total=Sum('amount'))['total'] or 0
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
            'form': paymentEsewa.generate_form(),
            'khalti_amount': int(float(plan.price) * 100),
            'khalti_order_id': str(transaction_uuid),
            'khalti_order_name': plan.plan_name,
            'khalti_website_url': getattr(settings, 'KHALTI_WEBSITE_URL', '') or request.build_absolute_uri('/'),
            'khalti_return_url': request.build_absolute_uri(
                reverse('khalti-return-membership', args=[transaction_uuid])
            ),
        }
        return render(request, 'membership/membership_checkout.html', context)

    return render(request, 'membership/purchase_membership.html', {'plan': plan})

def success(request, uid):    
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
        'pending_data': pending_data,
        'provider': request.GET.get('provider')
    }
    messages.error(request, f"Payment failed: {uid}")
    return render(request, "membership/payment_failure.html", context)


@login_required
@require_http_methods(["POST"])
def khalti_initiate_membership(request):
    return_url = request.POST.get('return_url')
    if not return_url:
        messages.error(request, "Missing Khalti return URL.")
        return redirect('membership-plans')

    base_url = (
        "https://khalti.com/api/v2/"
        if getattr(settings, 'KHALTI_ENV', 'sandbox') == 'production'
        else "https://dev.khalti.com/api/v2/"
    )
    url = f"{base_url}epayment/initiate/"
    website_url = request.POST.get('website_url') or request.build_absolute_uri('/')
    amount = request.POST.get('amount')
    purchase_order_id = request.POST.get('purchase_order_id')
    purchase_order_name = request.POST.get('purchase_order_name') or 'Membership'

    if not getattr(settings, 'KHALTI_SECRET_KEY', ''):
        messages.error(request, "Khalti secret key is not configured.")
        return redirect('membership-plans')

    try:
        amount_value = int(amount)
    except (TypeError, ValueError):
        messages.error(request, "Invalid Khalti amount.")
        return redirect('membership-plans')

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

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code != 200:
        messages.error(request, "Khalti initiate failed. Please try again.")
        return redirect('membership-plans')

    new_res = json.loads(response.text)
    payment_url = new_res.get('payment_url')
    if not payment_url:
        messages.error(request, "Khalti response missing payment URL.")
        return redirect('membership-plans')

    return redirect(payment_url)


@login_required
@require_http_methods(["GET"])
def khalti_return_membership(request, uid):
    pending_data = request.session.get('pending_subscription')
    if not pending_data or pending_data.get('transaction_uuid') != str(uid):
        messages.error(request, "Invalid or expired payment session.")
        return redirect('membership-plans')

    pidx = request.GET.get('pidx')
    if not pidx:
        messages.error(request, "Missing Khalti payment reference. Please try again.")
        return redirect('failure', uid)

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
        return redirect('failure', uid)

    if res.status_code != 200:
        messages.error(request, "Khalti verification failed. Please try again.")
        return redirect('failure', uid)

    try:
        new_res = res.json()
    except ValueError:
        messages.error(request, "Khalti verification failed. Please try again.")
        return redirect('failure', uid)

    status = (new_res.get('status') or '').lower()
    if status != 'completed':
        messages.error(request, "Khalti payment verification failed. Please try again.")
        return redirect('failure', uid)

    expected_amount = int(float(pending_data['amount']) * 100)
    if 'total_amount' in new_res and int(new_res.get('total_amount') or 0) != expected_amount:
        messages.error(request, "Khalti payment amount mismatch. Please contact support.")
        return redirect('failure', uid)

    if 'purchase_order_id' in new_res and str(new_res.get('purchase_order_id')) != str(uid):
        messages.error(request, "Khalti payment reference mismatch. Please contact support.")
        return redirect('failure', uid)

    plan = get_object_or_404(MembershipPlan, id=pending_data['plan_id'])
    start_date = datetime.fromisoformat(pending_data['start_date']).date()

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
        payment_method='Khalti',
        payment_status='Completed'
    )
    del request.session['pending_subscription']

    context = {
        'payment': payment,
        'subscription': subscription,
    }
    messages.success(request, f"Payment completed: {payment.uid}")
    return render(request, 'membership/payment_success.html', context)
    


    

@login_required
def my_memberships(request):
    """
    Display all memberships for the logged-in user.
    - Shows history of all subscriptions
    - Shows days left only for subscriptions that have started
    """
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




# DODO Payment
client = DodoPayments(
    bearer_token=os.environ.get("DODO_PAYMENTS_API_KEY"),
    environment="test_mode"
)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def dodo_payment_checkout(request):
    plan_id = request.POST.get('plan_id')
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    today = date.today()

    if not plan.dodo_product_id:
        return JsonResponse({'error': 'Dodo product ID is not configured for this plan.'}, status=400)

    session = client.checkout_sessions.create(
        product_cart=[{
            "product_id": plan.dodo_product_id,
            "quantity": 1,
        }],
        return_url=request.build_absolute_uri(f'/dodo/return/{request.user.id}/')
    )

    start_date = today
    duration_days = 30 * plan.duration_months
        
    # ONLY look at active subscriptions - cancelled ones should be ignored completely
    active_subs = MemberSubscription.objects.filter(
        member=request.user,
        is_active=True
    ).order_by('start_date')
    
    if active_subs.exists():
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
    
    request.session['pending_subscription'] = {
        'plan_id': plan_id,
        'start_date': start_date.isoformat(),
        'transaction_uuid': str(session.session_id),
        'amount': float(plan.price)
    }

    return redirect(session.checkout_url)


def dodo_payment_return(request, user_id):
    pending = request.session.get('pending_subscription')
    if not pending:
        messages.error(request, "No pending payment session found.")
        return redirect('membership-plans')
    
    if str(user_id) != str(request.user.id):
        messages.error(request, "Invalid payment session.")
        return redirect(f"{reverse('failure', args=[pending.get('transaction_uuid')])}?provider=dodo")
    
    session_id = pending.get('transaction_uuid') 
    if not session_id:
        messages.error(request, "Invalid payment session.")
        return redirect(f"{reverse('failure', args=[pending.get('transaction_uuid')])}?provider=dodo")
    
    try:
        session = client.checkout_sessions.retrieve(session_id)
    except Exception as e:
        messages.error(request, "Failed to verify payment with Dodo. Please contact support.")
        return redirect(f"{reverse('failure', args=[pending.get('transaction_uuid')])}?provider=dodo")
    
    status = None
    query_status = request.GET.get('status', '')
    if hasattr(session, 'status'):
        status = session.status
    elif isinstance(session, dict):
        status = session.get('status')
    else:
        status = session

    if hasattr(status, 'value'):
        status_value = str(status.value)
    else:
        status_value = str(status) if status is not None else ''

    if not status_value:
        status_value = query_status

    if query_status.lower() == 'succeeded':
        status_value = 'succeeded'

    if 'succeeded' not in status_value.lower():
        messages.error(request, "Payment not completed. Please try again.")
        return redirect(f"{reverse('failure', args=[pending.get('transaction_uuid')])}?provider=dodo")


     # If payment is completed, create the subscription
    plan = get_object_or_404(MembershipPlan, id=pending.get('plan_id'))
    start_date_value = pending.get('start_date')
    try:
        start_date = datetime.fromisoformat(start_date_value).date()
    except (TypeError, ValueError):
        start_date = date.today()

    subscription = MemberSubscription.objects.create(
        member=request.user,
        plan=plan,
        start_date=start_date,
        is_active=True
    )
    
    # Update payment status to Completed
    payment = Payment.objects.create(
            member_subscription=subscription,
            amount=pending.get('amount'),
            tax_amount=0,
            service_charge=0,
            delivery_charge=0,
            payment_method='Online Payment (Dodo)',
            payment_status='Completed'
        )

    # Clear the pending session from session data
    if 'pending_subscription' in request.session:
        del request.session['pending_subscription']

    context = {
        'payment': payment,
        'subscription': subscription,
    }
    messages.success(request, f"Your subscription for '{plan.plan_name}' has been successfully activated.")
    return render(request, 'membership/payment_success.html', context)