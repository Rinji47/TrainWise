from django.urls import path
from . import views

urlpatterns = [
    # ---------------------------------
    # Admin Membership Plans management
    # ---------------------------------
    path('admin-dashboard/memberships/', views.admin_memberships, name='admin-memberships'),
    path('admin-dashboard/memberships/add/', views.admin_membership_add, name='admin-membership-add'),
    path('admin-dashboard/memberships/edit/<int:pk>/', views.admin_membership_edit, name='admin-membership-edit'),
    path('admin-dashboard/memberships/delete/<int:pk>/', views.admin_membership_delete, name='admin-membership-delete'),

    # -------------------------
    # Payments Admin
    # -------------------------
    path('admin-dashboard/payments/', views.admin_payments, name='admin-payments'),
    path('admin-dashboard/payments/<int:pk>/', views.admin_payment_detail, name='admin-payment-detail'),


    # ---------------------------------
    # Membership Plans
    # ---------------------------------
    path('membership-plans/', views.membership_plans, name='membership-plans'),
    path('membership/purchase/<int:plan_id>/', views.purchase_membership, name='purchase-membership'),


    # ---------------------------------
    # My Memberships
    # ---------------------------------
    path('my-memberships/', views.my_memberships, name='my-memberships'),

    # Cancel a membership subscription
    path('my-memberships/cancel/<int:subscription_id>/', views.cancel_membership, name='cancel-membership'),

    path('my-payments/', views.my_payments, name='my-payments'),

    path('success/<uid>/', views.success, name='success'),
    path('failure/<uid>/', views.failure, name='failure'),

    # Khalti placeholders
    path('khalti/initiate/membership/', views.khalti_initiate_membership, name='khalti-initiate-membership'),
    path('khalti/return/membership/<uid>/', views.khalti_return_membership, name='khalti-return-membership'),
]
