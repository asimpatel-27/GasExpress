from django.contrib import admin
from .models import CylinderBooking, Payment, Cylinder, Complaint, DeliveryStaff

admin.site.register(CylinderBooking)
admin.site.register(Payment)
admin.site.register(Cylinder)
admin.site.register(Complaint)
admin.site.register(DeliveryStaff)