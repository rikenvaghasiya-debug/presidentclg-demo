from django.contrib import admin
from .models import (
    PG,
    Room,
    Bed,
    Tenant,
    Payment,
    Complaint,
    Notice,
    Attendance
)


@admin.register(PG)
class PGAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'city',
        'contact_number',
        'email',
        'created_at'
    )

    search_fields = (
        'name',
        'city',
        'contact_number',
        'email'
    )

    list_filter = (
        'city',
        'created_at'
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number',
        'pg',
        'floor',
        'room_type',
        'total_beds',
        'available_beds'
    )

    search_fields = (
        'room_number',
        'pg__name'
    )

    list_filter = (
        'pg',
        'floor',
        'room_type'
    )


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = (
        'bed_number',
        'room',
        'is_available'
    )

    search_fields = (
        'bed_number',
        'room__room_number'
    )

    list_filter = (
        'is_available',
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'phone',
        'gender',
        'bed',
        'joining_date',
        'rent_amount',
        'is_active'
    )

    search_fields = (
        'full_name',
        'email',
        'phone'
    )

    list_filter = (
        'gender',
        'is_active',
        'joining_date'
    )

    list_editable = (
        'is_active',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'tenant',
        'amount',
        'payment_date',
        'payment_method',
        'status',
        'transaction_id'
    )

    search_fields = (
        'tenant__full_name',
        'transaction_id'
    )

    list_filter = (
        'payment_method',
        'status',
        'payment_date'
    )


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'subject',
        'tenant',
        'priority',
        'status',
        'created_at'
    )

    search_fields = (
        'subject',
        'tenant__full_name',
        'description'
    )

    list_filter = (
        'priority',
        'status',
        'created_at'
    )


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'created_at',
        'is_active'
    )

    search_fields = (
        'title',
        'message'
    )

    list_filter = (
        'is_active',
        'created_at'
    )

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'tenant',
        'date',
        'check_in',
        'check_out',
        'status',
    )

    list_filter = (
        'status',
        'date',
    )

    search_fields = (
        'tenant__full_name',
        'tenant__email',
    )

    ordering = (
        '-date',
        '-check_in',
    )