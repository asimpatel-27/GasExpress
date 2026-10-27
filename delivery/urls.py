from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("dashboard/", views.customer_dashboard, name="dashboard"),

    path("booking/", views.book_cylinder, name="booking"),
    path("bookings/", views.booking_list, name="booking_list"),

    path("register/", views.register, name="register"),
    path("login/", views.customer_login, name="login"),
    path("logout/", views.user_logout, name="logout"),

    path("payment/<int:booking_id>/", views.payment_page, name="payment"),
    path("payment-history/", views.payment_history, name="payment_history"),
    path(
        "payment-receipt/<int:payment_id>/",
        views.payment_receipt,
        name="payment_receipt"
    ),

    path("complaint/", views.complaint_create, name="complaint"),
    path("complaints/", views.complaint_list, name="complaint_list"),

    path("reports/", views.reports_dashboard, name="reports"),

    path(
        "staff-dashboard/",
        views.staff_dashboard,
        name="staff_dashboard"
    ),
    path(
        "staff-booking/<int:booking_id>/status/",
        views.staff_update_booking_status,
        name="staff_update_booking_status"
    ),
    path("admin-bookings/", views.admin_manage_bookings, name="admin_bookings"),
path("admin-booking/<int:booking_id>/update/", views.admin_update_booking, name="admin_update_booking"),
]