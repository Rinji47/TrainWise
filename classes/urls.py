from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/private-classes-list/', views.admin_private_classes_list, name='admin-private-classes-list'),
    path('admin-dashboard/private-classes/<int:pk>/edit/', views.admin_private_class_edit, name='admin-private-class-edit'),
    path('admin-dashboard/private-classes/<int:pk>/toggle/', views.admin_private_class_toggle, name='admin-private-class-toggle'),

    # Show all trainers (public)
    path('book-private-class/', views.book_private_class_select_trainer, name='book-private-class'),

    # Booking form for selected trainer (login required)
    path('book-private-class/<int:trainer_id>/details/', 
         views.book_private_class_details, 
         name='book-private-class-details'),

    
    # # Payment page for booked class (to be implemented)
    # path('book-private-class/<int:private_class_id>/payment/', 
    #      views.payment_for_private_class, 
    #      name='payment-for-private-class'),


    # Memeber dashboard stuff
    path('my-booked-sessions/', views.my_booked_sessions, name='my-booked-sessions'),
    path('cancel-private-class/<int:pk>/', views.cancel_private_class, name='cancel-private-class'),

    # Trainer private class schedule
    path('trainer-classes/', views.trainer_private_classes, name='trainer-private-classes'),

    # Private class payment handlers
    path('private-class/success/<uid>/', views.private_class_success, name='private-class-success'),
    path('private-class/failure/<uid>/', views.private_class_failure, name='private-class-failure'),

    # Khalti placeholders
    path('khalti/initiate/private-class/', views.khalti_initiate_private_class, name='khalti-initiate-private-class'),
    path('khalti/return/private-class/<uid>/', views.khalti_return_private_class, name='khalti-return-private-class'),

]