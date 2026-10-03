
import uuid

from django.db import models
from django.contrib.auth.models import User


class PG(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    ROOM_TYPES = [
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Triple', 'Triple'),
        ('Shared', 'Shared'),
    ]

    pg = models.ForeignKey(
        PG,
        on_delete=models.CASCADE,
        related_name='rooms'
    )
    room_number = models.CharField(max_length=20)
    floor = models.PositiveIntegerField()
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPES
    )
    total_beds = models.PositiveIntegerField(default=1)
    available_beds = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.pg.name} - Room {self.room_number}"


class Bed(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='beds'
    )
    bed_number = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room.room_number} - Bed {self.bed_number}"


class Tenant(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=100)

    profile_photo = models.ImageField(
        upload_to='tenant_profiles/',
        blank=True,
        null=True
    )

    email = models.EmailField()
    phone = models.CharField(max_length=10)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )
    address = models.TextField()

    bed = models.OneToOneField(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    joining_date = models.DateField()

    rent_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Card', 'Card'),
    ]

    PAYMENT_STATUS = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_date = models.DateField(
        auto_now_add=True
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='Paid'
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        editable=False,
        default=None
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = (
                f"PGTXN-{uuid.uuid4().hex[:12].upper()}"
            )

        super().save(*args, **kwargs)
    def __str__(self):
        return (
            f"{self.tenant.full_name} - ₹{self.amount}"
        )


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='complaints'
    )

    subject = models.CharField(max_length=200)
    description = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Medium'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.subject


class Notice(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='attendance'
    )

    date = models.DateField(auto_now_add=True)

    check_in = models.DateTimeField(
        null=True,
        blank=True
    )

    check_out = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Present'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.full_name} - {self.date}"