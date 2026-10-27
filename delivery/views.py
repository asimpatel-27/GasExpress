
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Sum, Q

from .models import (
    CylinderBooking,
    Payment,
    Cylinder,
    Complaint,
    DeliveryStaff,
)


def home(request):
    cylinders = Cylinder.objects.filter(is_active=True)

    return render(
        request,
        "delivery/home.html",
        {"cylinders": cylinders}
    )


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "delivery/register.html", {"form": form})


def customer_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("dashboard")
    else:
        form = AuthenticationForm(request)

    return render(request, "delivery/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("home")


customer_logout = user_logout


@login_required(login_url="login")
def customer_dashboard(request):
    bookings = CylinderBooking.objects.filter(
        user=request.user
    ).order_by("-booking_date")

    return render(
        request,
        "delivery/dashboard.html",
        {"bookings": bookings}
    )


@login_required(login_url="login")
def book_cylinder(request):
    cylinders = Cylinder.objects.filter(is_active=True)

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        cylinder_type = request.POST.get("cylinder_type", "").strip()

        try:
            quantity = int(request.POST.get("quantity", "1"))
        except (TypeError, ValueError):
            quantity = 0

        if not customer_name or not phone or not address:
            messages.error(
                request,
                "Please fill in all required fields."
            )

        elif cylinder_type not in ["Domestic", "Commercial"]:
            messages.error(
                request,
                "Please select a valid cylinder type."
            )

        elif quantity < 1:
            messages.error(
                request,
                "Quantity must be at least 1."
            )

        else:
            try:
                with transaction.atomic():
                    cylinder = Cylinder.objects.select_for_update().get(
                        cylinder_type=cylinder_type,
                        is_active=True
                    )

                    if cylinder.available_stock < quantity:
                        messages.error(
                            request,
                            "Not enough cylinders in stock."
                        )
                    else:
                        booking = CylinderBooking.objects.create(
                            user=request.user,
                            customer_name=customer_name,
                            phone=phone,
                            address=address,
                            cylinder_type=cylinder_type,
                            quantity=quantity
                        )

                        cylinder.available_stock -= quantity
                        cylinder.save(
                            update_fields=["available_stock"]
                        )

                        messages.success(
                            request,
                            "Cylinder booking created successfully!"
                        )

                        return redirect(
                            "payment",
                            booking_id=booking.id
                        )

            except Cylinder.DoesNotExist:
                messages.error(
                    request,
                    "This cylinder type is currently unavailable."
                )

        return render(
            request,
            "delivery/booking.html",
            {"cylinders": cylinders}
        )

    return render(
        request,
        "delivery/booking.html",
        {"cylinders": cylinders}
    )


@login_required(login_url="login")
def booking_list(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "")
    cylinder_type = request.GET.get("cylinder_type", "")

    bookings = CylinderBooking.objects.filter(
        user=request.user
    ).select_related(
        "delivery_staff"
    ).order_by("-booking_date")

    # Search by booking ID or customer name
    if search:
        if search.isdigit():
            bookings = bookings.filter(
                Q(customer_name__icontains=search)
                | Q(id=int(search))
            )
        else:
            bookings = bookings.filter(
                customer_name__icontains=search
            )

    # Filter by booking status
    if status in ["Pending", "Confirmed", "Delivered"]:
        bookings = bookings.filter(status=status)

    # Filter by cylinder type
    if cylinder_type in ["Domestic", "Commercial"]:
        bookings = bookings.filter(
            cylinder_type=cylinder_type
        )

    context = {
        "bookings": bookings,
        "search": search,
        "selected_status": status,
        "selected_cylinder": cylinder_type,
    }

    return render(
        request,
        "delivery/booking_list.html",
        context
    )


@login_required(login_url="login")
def payment_page(request, booking_id):
    booking = get_object_or_404(
        CylinderBooking,
        id=booking_id,
        user=request.user
    )

    cylinder = Cylinder.objects.filter(
        cylinder_type=booking.cylinder_type
    ).first()

    if cylinder is None:
        messages.error(
            request,
            "Cylinder price is unavailable."
        )
        return redirect("booking_list")

    amount = cylinder.price * booking.quantity

    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            "amount": amount,
            "payment_method": "COD",
            "status": "Pending"
        }
    )

    if not created:
        payment.amount = amount
        payment.save(update_fields=["amount"])

    if request.method == "POST":
        payment_method = request.POST.get(
            "payment_method",
            "COD"
        )

        if payment_method not in ["COD", "UPI"]:
            messages.error(
                request,
                "Please select a valid payment method."
            )
        else:
            payment.payment_method = payment_method

            # Demo payment only; no real money transfer occurs.
            payment.status = "Pending"
            payment.save()

            messages.success(
                request,
                "Payment method saved."
            )

            return redirect(
                "payment_receipt",
                payment_id=payment.id
            )

    return render(
        request,
        "delivery/payment.html",
        {
            "booking": booking,
            "payment": payment,
            "amount": amount
        }
    )


@login_required(login_url="login")
def payment_history(request):
    payments = Payment.objects.filter(
        booking__user=request.user
    ).select_related(
        "booking"
    ).order_by("-created_at")

    return render(
        request,
        "delivery/payment_history.html",
        {"payments": payments}
    )


@login_required(login_url="login")
def payment_receipt(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related("booking"),
        id=payment_id,
        booking__user=request.user
    )

    return render(
        request,
        "delivery/payment_receipt.html",
        {"payment": payment}
    )


@login_required(login_url="login")
def complaint_create(request):
    if request.method == "POST":
        customer_name = request.POST.get(
            "customer_name", ""
        ).strip()

        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        complaint_type = request.POST.get(
            "complaint_type", ""
        ).strip()

        description = request.POST.get(
            "description", ""
        ).strip()

        valid_types = [
            "Gas Leakage",
            "Safety Inspection",
            "Other"
        ]

        if not all([
            customer_name,
            phone,
            address,
            complaint_type,
            description
        ]):
            messages.error(
                request,
                "Please fill in all fields."
            )

        elif complaint_type not in valid_types:
            messages.error(
                request,
                "Please select a valid complaint type."
            )

        else:
            Complaint.objects.create(
                user=request.user,
                customer_name=customer_name,
                phone=phone,
                address=address,
                complaint_type=complaint_type,
                description=description
            )

            messages.success(
                request,
                "Complaint submitted successfully!"
            )

            return redirect("complaint_list")

    return render(
        request,
        "delivery/complaints.html"
    )


@login_required(login_url="login")
def complaint_list(request):
    complaints = Complaint.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "delivery/complaint_list.html",
        {"complaints": complaints}
    )


@staff_member_required
def reports_dashboard(request):
    # Booking counts
    total_bookings = CylinderBooking.objects.count()

    pending_bookings = CylinderBooking.objects.filter(
        status="Pending"
    ).count()

    confirmed_bookings = CylinderBooking.objects.filter(
        status="Confirmed"
    ).count()

    delivered_bookings = CylinderBooking.objects.filter(
        status="Delivered"
    ).count()

    # Count all Django user accounts
    total_customers = get_user_model().objects.count()

    # Complaint counts
    total_complaints = Complaint.objects.count()

    pending_complaints = Complaint.objects.filter(
        status="Pending"
    ).count()

    in_progress_complaints = Complaint.objects.filter(
        status="In Progress"
    ).count()

    resolved_complaints = Complaint.objects.filter(
        status="Resolved"
    ).count()

    # Payment counts and paid amount
    total_payments = Payment.objects.count()

    paid_amount = Payment.objects.filter(
        status="Paid"
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Prevent division by zero
    booking_total = max(total_bookings, 1)
    complaint_total = max(total_complaints, 1)

    # Booking chart percentages
    pending_percent = round(
        pending_bookings * 100 / booking_total
    )

    confirmed_percent = round(
        confirmed_bookings * 100 / booking_total
    )

    delivered_percent = round(
        delivered_bookings * 100 / booking_total
    )

    # Complaint chart percentages
    pending_complaint_percent = round(
        pending_complaints * 100 / complaint_total
    )

    in_progress_complaint_percent = round(
        in_progress_complaints * 100 / complaint_total
    )

    resolved_complaint_percent = round(
        resolved_complaints * 100 / complaint_total
    )

    # Send data to reports.html
    context = {
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "delivered_bookings": delivered_bookings,

        "total_customers": total_customers,

        "total_complaints": total_complaints,
        "pending_complaints": pending_complaints,
        "in_progress_complaints": in_progress_complaints,
        "resolved_complaints": resolved_complaints,

        "total_payments": total_payments,
        "paid_amount": paid_amount,

        "pending_percent": pending_percent,
        "confirmed_percent": confirmed_percent,
        "delivered_percent": delivered_percent,

        "pending_complaint_percent": pending_complaint_percent,
        "in_progress_complaint_percent": in_progress_complaint_percent,
        "resolved_complaint_percent": resolved_complaint_percent,
    }

    return render(
        request,
        "delivery/reports.html",
        context
    )


@login_required(login_url="login")
def staff_dashboard(request):
    delivery_staff = DeliveryStaff.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if delivery_staff is None:
        messages.error(
            request,
            "No active delivery staff profile is linked to this account."
        )

        return render(
            request,
            "delivery/staff_dashboard.html",
            {
                "delivery_staff": None,
                "bookings": []
            }
        )

    bookings = CylinderBooking.objects.filter(
        delivery_staff=delivery_staff
    ).order_by("-booking_date")

    return render(
        request,
        "delivery/staff_dashboard.html",
        {
            "delivery_staff": delivery_staff,
            "bookings": bookings
        }
    )


@login_required(login_url="login")
@require_POST
def staff_update_booking_status(request, booking_id):
    delivery_staff = DeliveryStaff.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if delivery_staff is None:
        messages.error(
            request,
            "Delivery staff account not found."
        )
        return redirect("home")

    booking = get_object_or_404(
        CylinderBooking,
        id=booking_id,
        delivery_staff=delivery_staff
    )

    if booking.status == "Pending":
        booking.status = "Confirmed"
        booking.save(update_fields=["status"])

        messages.success(
            request,
            "Booking confirmed."
        )

    elif booking.status == "Confirmed":
        booking.status = "Delivered"
        booking.save(update_fields=["status"])

        messages.success(
            request,
            "Booking marked as delivered."
        )

    else:
        messages.info(
            request,
            "This booking is already delivered."
        )

    return redirect("staff_dashboard")
    
@staff_member_required
def admin_manage_bookings(request):
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "")
    cylinder_type = request.GET.get("cylinder_type", "")

    bookings = CylinderBooking.objects.select_related(
        "user", "delivery_staff"
    ).order_by("-booking_date")

    if search:
        if search.isdigit():
            bookings = bookings.filter(
                Q(customer_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(id=int(search))
            )
        else:
            bookings = bookings.filter(
                Q(customer_name__icontains=search)
                | Q(phone__icontains=search)
            )

    if status in ["Pending", "Confirmed", "Delivered"]:
        bookings = bookings.filter(status=status)

    if cylinder_type in ["Domestic", "Commercial"]:
        bookings = bookings.filter(cylinder_type=cylinder_type)

    staff_members = DeliveryStaff.objects.filter(
        is_active=True
    ).order_by("name")

    context = {
        "bookings": bookings,
        "staff_members": staff_members,
        "search": search,
        "selected_status": status,
        "selected_cylinder": cylinder_type,
    }

    return render(
        request,
        "delivery/admin_bookings.html",
        context
    )


@staff_member_required
@require_POST
def admin_update_booking(request, booking_id):
    booking = get_object_or_404(
        CylinderBooking,
        id=booking_id
    )

    new_status = request.POST.get("status", "")
    staff_id = request.POST.get("delivery_staff", "")

    valid_statuses = ["Pending", "Confirmed", "Delivered"]

    if new_status not in valid_statuses:
        messages.error(request, "Please select a valid booking status.")
        return redirect("admin_bookings")

    booking.status = new_status

    if not staff_id:
        booking.delivery_staff = None
    else:
        try:
            staff = DeliveryStaff.objects.get(id=staff_id)
        except (DeliveryStaff.DoesNotExist, ValueError):
            messages.error(request, "Selected delivery staff was not found.")
            return redirect("admin_bookings")

        if not staff.is_active and booking.delivery_staff_id != staff.id:
            messages.error(
                request,
                "Please assign an active delivery staff member."
            )
            return redirect("admin_bookings")

        booking.delivery_staff = staff

    booking.save(update_fields=["status", "delivery_staff"])

    messages.success(
        request,
        f"Booking #{booking.id} updated successfully."
    )

    return redirect("admin_bookings")

