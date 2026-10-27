
from django.conf import settings
from django.db import models


class DeliveryStaff(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivery_staff_profile"
    )

    employee_id = models.CharField(
        max_length=20,
        unique=True
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class CylinderBooking(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Delivered", "Delivered"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    delivery_staff = models.ForeignKey(
        "DeliveryStaff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    cylinder_type = models.CharField(
        max_length=20,
        default="Domestic"
    )

    quantity = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return self.customer_name


class Payment(models.Model):
    PAYMENT_METHODS = [
        ("COD", "Cash on Delivery"),
        ("UPI", "UPI"),
    ]

    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
    ]

    booking = models.OneToOneField(
        CylinderBooking,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=500
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        default="COD"
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending"
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id}"


class Cylinder(models.Model):
    CYLINDER_TYPES = [
        ("Domestic", "Domestic"),
        ("Commercial", "Commercial"),
    ]

    cylinder_type = models.CharField(
        max_length=20,
        choices=CYLINDER_TYPES,
        unique=True
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=500
    )

    total_stock = models.PositiveIntegerField(default=0)
    available_stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cylinder_type


class Complaint(models.Model):
    COMPLAINT_TYPES = [
        ("Gas Leakage", "Gas Leakage"),
        ("Safety Inspection", "Safety Inspection"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    complaint_type = models.CharField(
        max_length=30,
        choices=COMPLAINT_TYPES
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.complaint_type} - {self.customer_name}"

