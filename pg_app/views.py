from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import PG, Room, Bed, Tenant, Payment, Complaint, Notice, Attendance
from .forms import RegisterForm
from django.db import models
from django.utils import timezone
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
import re
from decimal import Decimal, InvalidOperation
from datetime import date




# ============================================================
# FORGOT PASSWORD / PASSWORD RESET
# ============================================================

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/forgot-password/done/'


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = '/forgot-password/complete/'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'



# =========================================================
# VALIDATION HELPERS
# =========================================================

def validate_required(value, field_name):
    value = (value or '').strip()

    if not value:
        return f'{field_name} is required.'

    return None


def validate_name(value, field_name='Name'):
    value = (value or '').strip()

    if not value:
        return f'{field_name} is required.'

    if len(value) < 2:
        return f'{field_name} must contain at least 2 characters.'

    if len(value) > 100:
        return f'{field_name} cannot exceed 100 characters.'

    if not re.fullmatch(
        r"[A-Za-zÀ-ÖØ-öø-ÿ\s.'-]+",
        value
    ):
        return (
            f'{field_name} can contain letters, spaces, '
            f'dots, apostrophes and hyphens only.'
        )

    return None


def validate_phone(value):
    value = (value or '').strip()

    if not re.fullmatch(r'\d{10}', value):
        return 'Phone number must contain exactly 10 digits.'

    if value[0] not in '6789':
        return 'Phone number must start with 6, 7, 8 or 9.'

    return None


def validate_email(value):
    value = (value or '').strip()

    if not value:
        return 'Email is required.'

    if not re.fullmatch(
        r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',
        value
    ):
        return 'Please enter a valid email address.'

    return None


def validate_positive_decimal(value, field_name='Amount'):
    value = (value or '').strip()

    if not value:
        return f'{field_name} is required.'

    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        return f'{field_name} must be a valid number.'

    if amount <= 0:
        return f'{field_name} must be greater than 0.'

    return None


def validate_non_negative_decimal(value, field_name='Amount'):
    value = (value or '').strip()

    if not value:
        return f'{field_name} is required.'

    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        return f'{field_name} must be a valid number.'

    if amount < 0:
        return f'{field_name} cannot be negative.'

    return None


def validate_positive_integer(value, field_name='Value'):
    value = (value or '').strip()

    if not value:
        return f'{field_name} is required.'

    if not value.isdigit():
        return f'{field_name} must be a whole number.'

    if int(value) <= 0:
        return f'{field_name} must be greater than 0.'

    return None


def validate_date_not_future(value, field_name='Date'):
    value = (value or '').strip()

    if not value:
        return f'{field_name} is required.'

    try:
        entered_date = date.fromisoformat(value)
    except ValueError:
        return f'Please enter a valid {field_name.lower()}.'

    if entered_date > date.today():
        return f'{field_name} cannot be in the future.'

    return None


# =========================================================
# HOME
# =========================================================

def home(request):
    return render(
        request,
        'home.html'
    )


# =========================================================
# TENANT DASHBOARD
# =========================================================

@login_required
def tenant_dashboard(request):

    tenant = Tenant.objects.filter(
        user=request.user
    ).select_related(
        'bed__room__pg'
    ).first()

    payments = (
        Payment.objects.filter(
            tenant=tenant
        ).order_by(
            '-payment_date'
        )
        if tenant
        else Payment.objects.none()
    )

    complaints = (
        Complaint.objects.filter(
            tenant=tenant
        ).order_by(
            '-created_at'
        )
        if tenant
        else Complaint.objects.none()
    )

    notices = Notice.objects.filter(
        is_active=True
    ).order_by(
        '-created_at'
    )

    today = timezone.localdate()

    today_attendance = (
        Attendance.objects.filter(
            tenant=tenant,
            date=today
        ).first()
        if tenant
        else None
    )

    return render(
        request,
        'tenant_dashboard.html',
        {
            'tenant': tenant,
            'payments': payments,
            'complaints': complaints,
            'notices': notices,
            'today_attendance': today_attendance,
        }
    )


# =========================================================
# TENANT PROFILE EDIT
# =========================================================

@login_required
def tenant_profile_edit(request):

    tenant = Tenant.objects.filter(
        user=request.user
    ).first()

    if not tenant:
        messages.error(
            request,
            'Tenant profile not found.'
        )
        return redirect(
            'tenant_dashboard'
        )

    if request.method == 'POST':

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        phone = request.POST.get(
            'phone',
            ''
        ).strip()

        date_of_birth = request.POST.get(
            'date_of_birth',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        # =========================================
        # PROFILE PHOTO
        # =========================================

        profile_photo = request.FILES.get(
            'profile_photo'
        )

        # =========================================
        # NAME VALIDATION
        # =========================================

        error = validate_name(
            full_name,
            'Full name'
        )

        if error:
            messages.error(
                request,
                error
            )
            return redirect(
                'tenant_profile_edit'
            )

        # =========================================
        # EMAIL VALIDATION
        # =========================================

        error = validate_email(
            email
        )

        if error:
            messages.error(
                request,
                error
            )
            return redirect(
                'tenant_profile_edit'
            )

        # =========================================
        # PHONE VALIDATION
        # =========================================

        error = validate_phone(
            phone
        )

        if error:
            messages.error(
                request,
                error
            )
            return redirect(
                'tenant_profile_edit'
            )

        # =========================================
        # ADDRESS VALIDATION
        # =========================================

        error = validate_required(
            address,
            'Address'
        )

        if error:
            messages.error(
                request,
                error
            )
            return redirect(
                'tenant_profile_edit'
            )

        # =========================================
        # DOB VALIDATION
        # =========================================

        if date_of_birth:

            try:

                dob = date.fromisoformat(
                    date_of_birth
                )

                if dob > date.today():

                    messages.error(
                        request,
                        'Date of birth cannot be in the future.'
                    )

                    return redirect(
                        'tenant_profile_edit'
                    )

            except ValueError:

                messages.error(
                    request,
                    'Please enter a valid date of birth.'
                )

                return redirect(
                    'tenant_profile_edit'
                )

        # =========================================
        # UPDATE TENANT INFORMATION
        # =========================================

        tenant.full_name = full_name

        tenant.email = email

        tenant.phone = phone

        tenant.address = address


        # =========================================
        # DATE OF BIRTH
        # =========================================

        if date_of_birth:

            tenant.date_of_birth = date_of_birth

        else:

            tenant.date_of_birth = None


        # =========================================
        # SAVE PROFILE PHOTO
        # =========================================

        if profile_photo:

            tenant.profile_photo = profile_photo


        # =========================================
        # SAVE EVERYTHING
        # =========================================

        tenant.save()


        # =========================================
        # SUCCESS MESSAGE
        # =========================================

        messages.success(
            request,
            'Profile updated successfully!'
        )

        return redirect(
            'tenant_dashboard'
        )


    # =========================================
    # GET REQUEST
    # =========================================

    return render(
        request,
        'tenant_profile_edit.html',
        {
            'tenant': tenant
        }
    )
# =========================================================
# TENANT CHANGE PASSWORD
# =========================================================

@login_required
def tenant_change_password(request):

    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm

    if request.method == 'POST':

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                'Password changed successfully!'
            )

            return redirect(
                'tenant_dashboard'
            )

    else:

        form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        'tenant_change_password.html',
        {
            'form': form
        }
    )


# =========================================================
# TENANT PAYMENT
# =========================================================

@login_required
def tenant_payment(request):

    import qrcode
    import os
    from django.conf import settings

    tenant = Tenant.objects.filter(
        user=request.user
    ).first()

    if not tenant:
        messages.error(
            request,
            'Tenant profile not found.'
        )
        return redirect(
            'tenant_dashboard'
        )

    upi_id = "yourupi@upi"

    if request.method == 'POST':

        transaction_id = request.POST.get(
            'transaction_id',
            ''
        ).strip()

        if not transaction_id:

            messages.error(
                request,
                'Please enter Transaction ID.'
            )

            return redirect(
                'tenant_payment'
            )

        if len(transaction_id) > 100:

            messages.error(
                request,
                'Transaction ID cannot exceed 100 characters.'
            )

            return redirect(
                'tenant_payment'
            )

        Payment.objects.create(
            tenant=tenant,
            amount=tenant.rent_amount,
            payment_method='UPI',
            status='Pending',
            transaction_id=transaction_id,
            description='Rent payment submitted by tenant.'
        )

        messages.success(
            request,
            'Payment details submitted successfully. '
            'Waiting for admin verification.'
        )

        return redirect(
            'tenant_dashboard'
        )

    amount = tenant.rent_amount

    upi_url = (
        f"upi://pay?"
        f"pa={upi_id}"
        f"&pn=PG%20Management"
        f"&am={amount}"
        f"&cu=INR"
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(
        upi_url
    )

    qr.make(
        fit=True
    )

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    qr_folder = os.path.join(
        settings.MEDIA_ROOT,
        'qr_codes'
    )

    os.makedirs(
        qr_folder,
        exist_ok=True
    )

    qr_filename = (
        f"tenant_{tenant.id}_rent.png"
    )

    qr_path = os.path.join(
        qr_folder,
        qr_filename
    )

    qr_image.save(
        qr_path
    )

    qr_url = (
        settings.MEDIA_URL
        + 'qr_codes/'
        + qr_filename
    )

    return render(
        request,
        'tenant_payment.html',
        {
            'tenant': tenant,
            'upi_id': upi_id,
            'qr_url': qr_url,
        }
    )


# =========================================================
# TENANT COMPLAINT
# =========================================================

@login_required
def tenant_complaint_add(request):

    tenant = Tenant.objects.filter(
        user=request.user
    ).first()

    if not tenant:

        messages.error(
            request,
            'Tenant profile not found.'
        )

        return redirect(
            'tenant_dashboard'
        )

    if request.method == 'POST':

        subject = request.POST.get(
            'subject',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        priority = request.POST.get(
            'priority',
            ''
        ).strip()

        if not subject:

            messages.error(
                request,
                'Complaint subject is required.'
            )

            return redirect(
                'tenant_complaint_add'
            )

        if len(subject) > 200:

            messages.error(
                request,
                'Complaint subject cannot exceed 200 characters.'
            )

            return redirect(
                'tenant_complaint_add'
            )

        if not description:

            messages.error(
                request,
                'Complaint description is required.'
            )

            return redirect(
                'tenant_complaint_add'
            )

        if priority not in [
            'Low',
            'Medium',
            'High'
        ]:

            priority = 'Medium'

        Complaint.objects.create(
            tenant=tenant,
            subject=subject,
            description=description,
            priority=priority,
            status='Pending'
        )

        messages.success(
            request,
            'Complaint submitted successfully!'
        )

        return redirect(
            'tenant_dashboard'
        )

    return render(
        request,
        'tenant_complaint_add.html',
        {
            'tenant': tenant
        }
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@login_required
def admin_dashboard(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to access Admin Dashboard.'
        )

        return redirect(
            'tenant_dashboard'
        )

    today = timezone.localdate()

    active_tenants = Tenant.objects.filter(
        is_active=True
    )

    total_tenants = active_tenants.count()

    today_attendance = Attendance.objects.filter(
        date=today
    )

    attendance_records = today_attendance.select_related(
        'tenant'
    ).order_by(
        'tenant__full_name'
    )

    present_today = today_attendance.filter(
        status='Present'
    ).count()

    checked_in_today = today_attendance.filter(
        check_in__isnull=False
    ).count()

    checked_out_today = today_attendance.filter(
        check_out__isnull=False
    ).count()

    marked_tenant_ids = today_attendance.values_list(
        'tenant_id',
        flat=True
    )

    absent_tenants = active_tenants.exclude(
        id__in=marked_tenant_ids
    ).order_by(
        'full_name'
    )

    absent_count = absent_tenants.count()

    return render(
        request,
        'admin_dashboard.html',
        {
            'total_tenants': total_tenants,
            'present_today': present_today,
            'checked_in_today': checked_in_today,
            'checked_out_today': checked_out_today,
            'attendance_records': attendance_records,
            'absent_tenants': absent_tenants,
            'absent_count': absent_count,
        }
    )


# =========================================================
# PG MANAGEMENT
# =========================================================

@login_required
def pg_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to access PG Management.'
        )

        return redirect(
            'tenant_dashboard'
        )

    pgs = PG.objects.all().order_by(
        '-created_at'
    )

    return render(
        request,
        'pg_list.html',
        {
            'pgs': pgs
        }
    )


@login_required
def pg_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add PG.'
        )

        return redirect(
            'tenant_dashboard'
        )

    if request.method == 'POST':

        name = request.POST.get(
            'name',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        city = request.POST.get(
            'city',
            ''
        ).strip()

        contact_number = request.POST.get(
            'contact_number',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        # PG Name
        error = validate_name(
            name,
            'PG name'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_add.html'
            )

        # Address
        error = validate_required(
            address,
            'Address'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_add.html'
            )

        # City
        error = validate_name(
            city,
            'City'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_add.html'
            )

        # Phone
        error = validate_phone(
            contact_number
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_add.html'
            )

        # Email
        if email:

            error = validate_email(
                email
            )

            if error:

                messages.error(
                    request,
                    error
                )

                return render(
                    request,
                    'pg_add.html'
                )

        # Duplicate PG
        if PG.objects.filter(
            name__iexact=name
        ).exists():

            messages.error(
                request,
                'A PG with this name already exists.'
            )

            return render(
                request,
                'pg_add.html'
            )

        PG.objects.create(
            name=name,
            address=address,
            city=city,
            contact_number=contact_number,
            email=email if email else None,
            description=description if description else None
        )

        messages.success(
            request,
            'PG added successfully!'
        )

        return redirect(
            'pg_list'
        )

    return render(
        request,
        'pg_add.html'
    )


@login_required
def pg_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit PG.'
        )

        return redirect(
            'tenant_dashboard'
        )

    pg = PG.objects.filter(
        id=pk
    ).first()

    if not pg:

        messages.error(
            request,
            'PG not found.'
        )

        return redirect(
            'pg_list'
        )

    if request.method == 'POST':

        name = request.POST.get(
            'name',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        city = request.POST.get(
            'city',
            ''
        ).strip()

        contact_number = request.POST.get(
            'contact_number',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        # PG Name
        error = validate_name(
            name,
            'PG name'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_edit.html',
                {
                    'pg': pg
                }
            )

        # Address
        error = validate_required(
            address,
            'Address'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_edit.html',
                {
                    'pg': pg
                }
            )

        # City
        error = validate_name(
            city,
            'City'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_edit.html',
                {
                    'pg': pg
                }
            )

        # Phone
        error = validate_phone(
            contact_number
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'pg_edit.html',
                {
                    'pg': pg
                }
            )

        # Email
        if email:

            error = validate_email(
                email
            )

            if error:

                messages.error(
                    request,
                    error
                )

                return render(
                    request,
                    'pg_edit.html',
                    {
                        'pg': pg
                    }
                )

        # Duplicate PG
        duplicate_pg = PG.objects.filter(
            name__iexact=name
        ).exclude(
            id=pg.id
        ).exists()

        if duplicate_pg:

            messages.error(
                request,
                'Another PG with this name already exists.'
            )

            return render(
                request,
                'pg_edit.html',
                {
                    'pg': pg
                }
            )

        pg.name = name
        pg.address = address
        pg.city = city
        pg.contact_number = contact_number
        pg.email = email if email else None
        pg.description = description if description else None

        pg.save()

        messages.success(
            request,
            'PG updated successfully!'
        )

        return redirect(
            'pg_list'
        )

    return render(
        request,
        'pg_edit.html',
        {
            'pg': pg
        }
    )


@login_required
def pg_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete PG.'
        )

        return redirect(
            'tenant_dashboard'
        )

    pg = PG.objects.filter(
        id=pk
    ).first()

    if not pg:

        messages.error(
            request,
            'PG not found.'
        )

        return redirect(
            'pg_list'
        )

    if request.method == 'POST':

        pg.delete()

        messages.success(
            request,
            'PG deleted successfully!'
        )

        return redirect(
            'pg_list'
        )

    return render(
        request,
        'pg_delete.html',
        {
            'pg': pg
        }
    )


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect(
            'home'
        )

    if request.method == 'POST':

        form = RegisterForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Registration successful! You can now login.'
            )

            return redirect(
                'login'
            )

    else:

        form = RegisterForm()

    return render(
        request,
        'register.html',
        {
            'form': form
        }
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect(
            'home'
        )

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        if not username:

            messages.error(
                request,
                'Username is required.'
            )

            return render(
                request,
                'login.html'
            )

        if not password:

            messages.error(
                request,
                'Password is required.'
            )

            return render(
                request,
                'login.html'
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            messages.success(
                request,
                f'Welcome, {user.first_name or user.username}!'
            )

            if user.is_staff:
                return redirect(
                    'admin_dashboard'
                )

            return redirect(
                'tenant_dashboard'
            )

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(
        request,
        'login.html'
    )


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect(
        'home'
    )


# =========================================================
# ROOM MANAGEMENT
# =========================================================

@login_required
def room_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to access Room Management.'
        )

        return redirect(
            'tenant_dashboard'
        )

    rooms = Room.objects.all().order_by(
        'pg',
        'room_number'
    )

    return render(
        request,
        'room_list.html',
        {
            'rooms': rooms
        }
    )


# =========================================================
# ROOM ADD - VALIDATED
# =========================================================

@login_required
def room_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add Room.'
        )

        return redirect(
            'tenant_dashboard'
        )

    pgs = PG.objects.all().order_by(
        'name'
    )

    if request.method == 'POST':

        pg_id = request.POST.get(
            'pg',
            ''
        ).strip()

        room_number = request.POST.get(
            'room_number',
            ''
        ).strip()

        floor = request.POST.get(
            'floor',
            ''
        ).strip()

        room_type = request.POST.get(
            'room_type',
            ''
        ).strip()

        total_beds = request.POST.get(
            'total_beds',
            ''
        ).strip()

        available_beds = request.POST.get(
            'available_beds',
            ''
        ).strip()

        # =====================================================
        # PG VALIDATION
        # =====================================================

        if not pg_id:

            messages.error(
                request,
                'Please select a PG.'
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        pg = PG.objects.filter(
            id=pg_id
        ).first()

        if not pg:

            messages.error(
                request,
                'Invalid PG selected.'
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # ROOM NUMBER VALIDATION
        # =====================================================

        error = validate_required(
            room_number,
            'Room number'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        if len(room_number) > 20:

            messages.error(
                request,
                'Room number cannot exceed 20 characters.'
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # DUPLICATE ROOM VALIDATION
        # =====================================================

        if Room.objects.filter(
            pg=pg,
            room_number__iexact=room_number
        ).exists():

            messages.error(
                request,
                'This room number already exists in the selected PG.'
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # FLOOR VALIDATION
        # =====================================================

        error = validate_positive_integer(
            floor,
            'Floor'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # ROOM TYPE VALIDATION
        # =====================================================

        valid_room_types = [
            choice[0]
            for choice in Room.ROOM_TYPES
        ]

        if room_type not in valid_room_types:

            messages.error(
                request,
                'Please select a valid room type.'
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # TOTAL BEDS VALIDATION
        # =====================================================

        error = validate_positive_integer(
            total_beds,
            'Total beds'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # AVAILABLE BEDS VALIDATION
        # =====================================================

        error = validate_positive_integer(
            available_beds,
            'Available beds'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        total_beds_int = int(
            total_beds
        )

        available_beds_int = int(
            available_beds
        )

        # =====================================================
        # AVAILABLE BEDS <= TOTAL BEDS
        # =====================================================

        if available_beds_int > total_beds_int:

            messages.error(
                request,
                'Available beds cannot be greater than total beds.'
            )

            return render(
                request,
                'room_add.html',
                {
                    'pgs': pgs
                }
            )

        # =====================================================
        # CREATE ROOM
        # =====================================================

        Room.objects.create(
            pg=pg,
            room_number=room_number,
            floor=int(floor),
            room_type=room_type,
            total_beds=total_beds_int,
            available_beds=available_beds_int
        )

        messages.success(
            request,
            'Room added successfully!'
        )

        return redirect(
            'room_list'
        )

    return render(
        request,
        'room_add.html',
        {
            'pgs': pgs
        }
    )


# =========================================================
# ROOM EDIT - VALIDATED
# =========================================================

@login_required
def room_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit Room.'
        )

        return redirect(
            'tenant_dashboard'
        )

    room = Room.objects.filter(
        id=pk
    ).first()

    if not room:

        messages.error(
            request,
            'Room not found.'
        )

        return redirect(
            'room_list'
        )

    pgs = PG.objects.all().order_by(
        'name'
    )

    if request.method == 'POST':

        pg_id = request.POST.get(
            'pg',
            ''
        ).strip()

        room_number = request.POST.get(
            'room_number',
            ''
        ).strip()

        floor = request.POST.get(
            'floor',
            ''
        ).strip()

        room_type = request.POST.get(
            'room_type',
            ''
        ).strip()

        total_beds = request.POST.get(
            'total_beds',
            ''
        ).strip()

        available_beds = request.POST.get(
            'available_beds',
            ''
        ).strip()

        # =====================================================
        # PG VALIDATION
        # =====================================================

        if not pg_id:

            messages.error(
                request,
                'Please select a PG.'
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        pg = PG.objects.filter(
            id=pg_id
        ).first()

        if not pg:

            messages.error(
                request,
                'Invalid PG selected.'
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # ROOM NUMBER VALIDATION
        # =====================================================

        error = validate_required(
            room_number,
            'Room number'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        if len(room_number) > 20:

            messages.error(
                request,
                'Room number cannot exceed 20 characters.'
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # DUPLICATE ROOM VALIDATION
        # =====================================================

        duplicate_room = Room.objects.filter(
            pg=pg,
            room_number__iexact=room_number
        ).exclude(
            id=room.id
        ).exists()

        if duplicate_room:

            messages.error(
                request,
                'Another room with this room number already exists in the selected PG.'
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # FLOOR VALIDATION
        # =====================================================

        error = validate_positive_integer(
            floor,
            'Floor'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # ROOM TYPE VALIDATION
        # =====================================================

        valid_room_types = [
            choice[0]
            for choice in Room.ROOM_TYPES
        ]

        if room_type not in valid_room_types:

            messages.error(
                request,
                'Please select a valid room type.'
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # TOTAL BEDS VALIDATION
        # =====================================================

        error = validate_positive_integer(
            total_beds,
            'Total beds'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # AVAILABLE BEDS VALIDATION
        # =====================================================

        error = validate_positive_integer(
            available_beds,
            'Available beds'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        total_beds_int = int(
            total_beds
        )

        available_beds_int = int(
            available_beds
        )

        # =====================================================
        # AVAILABLE BEDS <= TOTAL BEDS
        # =====================================================

        if available_beds_int > total_beds_int:

            messages.error(
                request,
                'Available beds cannot be greater than total beds.'
            )

            return render(
                request,
                'room_edit.html',
                {
                    'room': room,
                    'pgs': pgs
                }
            )

        # =====================================================
        # UPDATE ROOM
        # =====================================================

        room.pg = pg
        room.room_number = room_number
        room.floor = int(floor)
        room.room_type = room_type
        room.total_beds = total_beds_int
        room.available_beds = available_beds_int

        room.save()

        messages.success(
            request,
            'Room updated successfully!'
        )

        return redirect(
            'room_list'
        )

    return render(
        request,
        'room_edit.html',
        {
            'room': room,
            'pgs': pgs
        }
    )


@login_required
def room_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete Room.'
        )

        return redirect(
            'tenant_dashboard'
        )

    room = Room.objects.filter(
        id=pk
    ).first()

    if not room:

        messages.error(
            request,
            'Room not found.'
        )

        return redirect(
            'room_list'
        )

    if request.method == 'POST':

        room.delete()

        messages.success(
            request,
            'Room deleted successfully!'
        )

        return redirect(
            'room_list'
        )

    return render(
        request,
        'room_delete.html',
        {
            'room': room
        }
    )


# =========================================================
# BED MANAGEMENT
# =========================================================

@login_required
def bed_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to access Bed Management.'
        )

        return redirect(
            'tenant_dashboard'
        )

    beds = Bed.objects.all().order_by(
        'room__pg',
        'room__room_number',
        'bed_number'
    )

    return render(
        request,
        'bed_list.html',
        {
            'beds': beds
        }
    )


@login_required
def bed_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add Bed.'
        )

        return redirect(
            'tenant_dashboard'
        )

    rooms = Room.objects.all().order_by(
        'pg__name',
        'room_number'
    )

    if request.method == 'POST':

        room_id = request.POST.get(
            'room',
            ''
        ).strip()

        bed_number = request.POST.get(
            'bed_number',
            ''
        ).strip()

        is_available = (
            request.POST.get(
                'is_available'
            ) == 'True'
        )

        if not room_id:

            messages.error(
                request,
                'Please select a room.'
            )

            return render(
                request,
                'bed_add.html',
                {
                    'rooms': rooms
                }
            )

        room = Room.objects.filter(
            id=room_id
        ).first()

        if not room:

            messages.error(
                request,
                'Invalid room selected.'
            )

            return render(
                request,
                'bed_add.html',
                {
                    'rooms': rooms
                }
            )

        error = validate_required(
            bed_number,
            'Bed number'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'bed_add.html',
                {
                    'rooms': rooms
                }
            )

        if len(bed_number) > 20:

            messages.error(
                request,
                'Bed number cannot exceed 20 characters.'
            )

            return render(
                request,
                'bed_add.html',
                {
                    'rooms': rooms
                }
            )

        if Bed.objects.filter(
            room=room,
            bed_number__iexact=bed_number
        ).exists():

            messages.error(
                request,
                'This bed number already exists in the selected room.'
            )

            return render(
                request,
                'bed_add.html',
                {
                    'rooms': rooms
                }
            )

        Bed.objects.create(
            room=room,
            bed_number=bed_number,
            is_available=is_available
        )

        messages.success(
            request,
            'Bed added successfully!'
        )

        return redirect(
            'bed_list'
        )

    return render(
        request,
        'bed_add.html',
        {
            'rooms': rooms
        }
    )


@login_required
def bed_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit Bed.'
        )

        return redirect(
            'tenant_dashboard'
        )

    bed = Bed.objects.filter(
        id=pk
    ).first()

    if not bed:

        messages.error(
            request,
            'Bed not found.'
        )

        return redirect(
            'bed_list'
        )

    rooms = Room.objects.all().order_by(
        'pg__name',
        'room_number'
    )

    if request.method == 'POST':

        room_id = request.POST.get(
            'room',
            ''
        ).strip()

        bed_number = request.POST.get(
            'bed_number',
            ''
        ).strip()

        is_available = (
            request.POST.get(
                'is_available'
            ) == 'True'
        )

        if not room_id:

            messages.error(
                request,
                'Please select a room.'
            )

            return render(
                request,
                'bed_edit.html',
                {
                    'bed': bed,
                    'rooms': rooms
                }
            )

        room = Room.objects.filter(
            id=room_id
        ).first()

        if not room:

            messages.error(
                request,
                'Invalid room selected.'
            )

            return render(
                request,
                'bed_edit.html',
                {
                    'bed': bed,
                    'rooms': rooms
                }
            )

        error = validate_required(
            bed_number,
            'Bed number'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'bed_edit.html',
                {
                    'bed': bed,
                    'rooms': rooms
                }
            )

        if len(bed_number) > 20:

            messages.error(
                request,
                'Bed number cannot exceed 20 characters.'
            )

            return render(
                request,
                'bed_edit.html',
                {
                    'bed': bed,
                    'rooms': rooms
                }
            )

        duplicate_bed = Bed.objects.filter(
            room=room,
            bed_number__iexact=bed_number
        ).exclude(
            id=bed.id
        ).exists()

        if duplicate_bed:

            messages.error(
                request,
                'Another bed with this number already exists in the selected room.'
            )

            return render(
                request,
                'bed_edit.html',
                {
                    'bed': bed,
                    'rooms': rooms
                }
            )

        bed.room = room
        bed.bed_number = bed_number
        bed.is_available = is_available

        bed.save()

        messages.success(
            request,
            'Bed updated successfully!'
        )

        return redirect(
            'bed_list'
        )

    return render(
        request,
        'bed_edit.html',
        {
            'bed': bed,
            'rooms': rooms
        }
    )


@login_required
def bed_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete Bed.'
        )

        return redirect(
            'tenant_dashboard'
        )

    bed = Bed.objects.filter(
        id=pk
    ).first()

    if not bed:

        messages.error(
            request,
            'Bed not found.'
        )

        return redirect(
            'bed_list'
        )

    if request.method == 'POST':

        bed.delete()

        messages.success(
            request,
            'Bed deleted successfully!'
        )

        return redirect(
            'bed_list'
        )

    return render(
        request,
        'bed_delete.html',
        {
            'bed': bed
        }
    )


# =========================================================
# TENANT MANAGEMENT
# =========================================================

@login_required
def tenant_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to access Tenant Management.'
        )

        return redirect(
            'tenant_dashboard'
        )

    tenants = Tenant.objects.select_related(
        'user',
        'bed',
        'bed__room',
        'bed__room__pg'
    ).all().order_by(
        '-created_at'
    )

    return render(
        request,
        'tenant_list.html',
        {
            'tenants': tenants
        }
    )


@login_required
def tenant_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add Tenant.'
        )

        return redirect(
            'tenant_dashboard'
        )

    from django.contrib.auth.models import User

    users = User.objects.filter(
        is_staff=False,
        is_active=True
    ).order_by(
        'username'
    )

    beds = Bed.objects.filter(
        is_available=True
    ).select_related(
        'room',
        'room__pg'
    ).order_by(
        'room__pg__name',
        'room__room_number',
        'bed_number'
    )

    if request.method == 'POST':

        user_id = request.POST.get(
            'user'
        )

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        phone = request.POST.get(
            'phone',
            ''
        ).strip()

        gender = request.POST.get(
            'gender',
            ''
        ).strip()

        date_of_birth = request.POST.get(
            'date_of_birth',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        bed_id = request.POST.get(
            'bed'
        ) or None

        joining_date = request.POST.get(
            'joining_date',
            ''
        ).strip()

        rent_amount = request.POST.get(
            'rent_amount',
            ''
        ).strip()

        security_deposit = request.POST.get(
            'security_deposit',
            ''
        ).strip()

        # User validation
        if not user_id:

            messages.error(
                request,
                'Please select a user.'
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        if not User.objects.filter(
            id=user_id,
            is_staff=False,
            is_active=True
        ).exists():

            messages.error(
                request,
                'Invalid user selected.'
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Name validation
        error = validate_name(
            full_name,
            'Full name'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Email validation
        error = validate_email(
            email
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Phone validation
        error = validate_phone(
            phone
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Gender validation
        valid_genders = [
            choice[0]
            for choice in Tenant.GENDER_CHOICES
        ]

        if gender not in valid_genders:

            messages.error(
                request,
                'Please select a valid gender.'
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Address validation
        error = validate_required(
            address,
            'Address'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # DOB validation
        if date_of_birth:

            try:

                dob = date.fromisoformat(
                    date_of_birth
                )

                if dob > date.today():

                    messages.error(
                        request,
                        'Date of birth cannot be in the future.'
                    )

                    return render(
                        request,
                        'tenant_add.html',
                        {
                            'users': users,
                            'beds': beds
                        }
                    )

            except ValueError:

                messages.error(
                    request,
                    'Please enter a valid date of birth.'
                )

                return render(
                    request,
                    'tenant_add.html',
                    {
                        'users': users,
                        'beds': beds
                    }
                )

        # Joining date validation
        error = validate_date_not_future(
            joining_date,
            'Joining date'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Rent validation
        error = validate_positive_decimal(
            rent_amount,
            'Rent amount'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Security deposit validation
        if not security_deposit:
            security_deposit = '0'

        error = validate_non_negative_decimal(
            security_deposit,
            'Security deposit'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # User already linked to Tenant
        if Tenant.objects.filter(
            user_id=user_id
        ).exists():

            messages.error(
                request,
                'This user already has a tenant profile.'
            )

            return render(
                request,
                'tenant_add.html',
                {
                    'users': users,
                    'beds': beds
                }
            )

        # Bed validation
        bed = None

        if bed_id:

            bed = Bed.objects.filter(
                id=bed_id,
                is_available=True
            ).first()

            if not bed:

                messages.error(
                    request,
                    'Selected bed is not available.'
                )

                return render(
                    request,
                    'tenant_add.html',
                    {
                        'users': users,
                        'beds': beds
                    }
                )

            if Tenant.objects.filter(
                bed_id=bed.id
            ).exists():

                messages.error(
                    request,
                    'This bed is already assigned to another tenant.'
                )

                return render(
                    request,
                    'tenant_add.html',
                    {
                        'users': users,
                        'beds': beds
                    }
                )

        Tenant.objects.create(
            user_id=user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            gender=gender,
            date_of_birth=date_of_birth or None,
            address=address,
            bed=bed,
            joining_date=joining_date,
            rent_amount=rent_amount,
            security_deposit=security_deposit,
            is_active=True
        )

        if bed:

            bed.is_available = False
            bed.save()

        messages.success(
            request,
            'Tenant added successfully!'
        )

        return redirect(
            'tenant_list'
        )

    return render(
        request,
        'tenant_add.html',
        {
            'users': users,
            'beds': beds
        }
    )


@login_required
def tenant_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit Tenant.'
        )

        return redirect(
            'tenant_dashboard'
        )

    tenant = Tenant.objects.filter(
        id=pk
    ).first()

    if not tenant:

        messages.error(
            request,
            'Tenant not found.'
        )

        return redirect(
            'tenant_list'
        )

    beds = Bed.objects.filter(
        is_available=True
    ).select_related(
        'room',
        'room__pg'
    )

    if tenant.bed:

        beds = Bed.objects.filter(
            models.Q(is_available=True)
            | models.Q(id=tenant.bed.id)
        ).select_related(
            'room',
            'room__pg'
        )

    if request.method == 'POST':

        old_bed = tenant.bed

        new_bed_id = request.POST.get(
            'bed'
        ) or None

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        phone = request.POST.get(
            'phone',
            ''
        ).strip()

        gender = request.POST.get(
            'gender',
            ''
        ).strip()

        date_of_birth = request.POST.get(
            'date_of_birth',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        joining_date = request.POST.get(
            'joining_date',
            ''
        ).strip()

        rent_amount = request.POST.get(
            'rent_amount',
            ''
        ).strip()

        security_deposit = request.POST.get(
            'security_deposit',
            ''
        ).strip()

        # Name
        error = validate_name(
            full_name,
            'Full name'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # Email
        error = validate_email(
            email
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # Phone
        error = validate_phone(
            phone
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # Gender
        valid_genders = [
            choice[0]
            for choice in Tenant.GENDER_CHOICES
        ]

        if gender not in valid_genders:

            messages.error(
                request,
                'Please select a valid gender.'
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # Address
        error = validate_required(
            address,
            'Address'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # DOB
        if date_of_birth:

            try:

                dob = date.fromisoformat(
                    date_of_birth
                )

                if dob > date.today():

                    messages.error(
                        request,
                        'Date of birth cannot be in the future.'
                    )

                    return render(
                        request,
                        'tenant_edit.html',
                        {
                            'tenant': tenant,
                            'beds': beds
                        }
                    )

            except ValueError:

                messages.error(
                    request,
                    'Please enter a valid date of birth.'
                )

                return render(
                    request,
                    'tenant_edit.html',
                    {
                        'tenant': tenant,
                        'beds': beds
                    }
                )

        # Joining date
        error = validate_date_not_future(
            joining_date,
            'Joining date'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # Rent
        error = validate_positive_decimal(
            rent_amount,
            'Rent amount'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # Security deposit
        if not security_deposit:
            security_deposit = '0'

        error = validate_non_negative_decimal(
            security_deposit,
            'Security deposit'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'tenant_edit.html',
                {
                    'tenant': tenant,
                    'beds': beds
                }
            )

        # New bed validation
        new_bed = None

        if new_bed_id:

            new_bed = Bed.objects.filter(
                id=new_bed_id
            ).first()

            if not new_bed:

                messages.error(
                    request,
                    'Invalid bed selected.'
                )

                return render(
                    request,
                    'tenant_edit.html',
                    {
                        'tenant': tenant,
                        'beds': beds
                    }
                )

            if (
                new_bed.id !=
                (old_bed.id if old_bed else None)
                and not new_bed.is_available
            ):

                messages.error(
                    request,
                    'Selected bed is already occupied.'
                )

                return render(
                    request,
                    'tenant_edit.html',
                    {
                        'tenant': tenant,
                        'beds': beds
                    }
                )

            if Tenant.objects.filter(
                bed_id=new_bed.id
            ).exclude(
                id=tenant.id
            ).exists():

                messages.error(
                    request,
                    'This bed is already assigned to another tenant.'
                )

                return render(
                    request,
                    'tenant_edit.html',
                    {
                        'tenant': tenant,
                        'beds': beds
                    }
                )

        tenant.full_name = full_name
        tenant.email = email
        tenant.phone = phone
        tenant.gender = gender
        tenant.date_of_birth = date_of_birth or None
        tenant.address = address
        tenant.bed = new_bed
        tenant.joining_date = joining_date
        tenant.rent_amount = rent_amount
        tenant.security_deposit = security_deposit
        tenant.is_active = True

        tenant.save()

        # Old bed available
        if old_bed and (
            not new_bed
            or old_bed.id != new_bed.id
        ):

            old_bed.is_available = True
            old_bed.save()

        # New bed occupied
        if new_bed:

            new_bed.is_available = False
            new_bed.save()

        messages.success(
            request,
            'Tenant updated successfully!'
        )

        return redirect(
            'tenant_list'
        )

    return render(
        request,
        'tenant_edit.html',
        {
            'tenant': tenant,
            'beds': beds
        }
    )


@login_required
def tenant_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete Tenant.'
        )

        return redirect(
            'tenant_dashboard'
        )

    tenant = Tenant.objects.filter(
        id=pk
    ).first()

    if not tenant:

        messages.error(
            request,
            'Tenant not found.'
        )

        return redirect(
            'tenant_list'
        )

    if request.method == 'POST':

        if tenant.bed:

            bed = tenant.bed
            bed.is_available = True
            bed.save()

        tenant.delete()

        messages.success(
            request,
            'Tenant deleted successfully!'
        )

        return redirect(
            'tenant_list'
        )

    return render(
        request,
        'tenant_delete.html',
        {
            'tenant': tenant
        }
    )


# =========================================================
# PAYMENT MANAGEMENT
# =========================================================

@login_required
def payment_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to view payments.'
        )

        return redirect(
            'tenant_dashboard'
        )

    payments = Payment.objects.select_related(
        'tenant'
    ).order_by(
        '-payment_date'
    )

    return render(
        request,
        'payment_list.html',
        {
            'payments': payments
        }
    )


@login_required
def payment_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add Payment.'
        )

        return redirect(
            'tenant_dashboard'
        )

    tenants = Tenant.objects.filter(
        is_active=True
    ).order_by(
        'full_name'
    )

    if request.method == 'POST':

        tenant_id = request.POST.get(
            'tenant'
        )

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        payment_method = request.POST.get(
            'payment_method',
            ''
        ).strip()

        status = request.POST.get(
            'status',
            ''
        ).strip()

        transaction_id = request.POST.get(
            'transaction_id',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        if not tenant_id:

            messages.error(
                request,
                'Please select a tenant.'
            )

            return render(
                request,
                'payment_add.html',
                {
                    'tenants': tenants
                }
            )

        tenant = Tenant.objects.filter(
            id=tenant_id,
            is_active=True
        ).first()

        if not tenant:

            messages.error(
                request,
                'Invalid tenant selected.'
            )

            return render(
                request,
                'payment_add.html',
                {
                    'tenants': tenants
                }
            )

        error = validate_positive_decimal(
            amount,
            'Payment amount'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'payment_add.html',
                {
                    'tenants': tenants
                }
            )

        if payment_method not in [
            'Cash',
            'UPI',
            'Card'
        ]:

            messages.error(
                request,
                'Please select a valid payment method.'
            )

            return render(
                request,
                'payment_add.html',
                {
                    'tenants': tenants
                }
            )

        if status not in [
            'Paid',
            'Pending'
        ]:

            messages.error(
                request,
                'Please select a valid payment status.'
            )

            return render(
                request,
                'payment_add.html',
                {
                    'tenants': tenants
                }
            )

        if transaction_id and len(transaction_id) > 100:

            messages.error(
                request,
                'Transaction ID cannot exceed 100 characters.'
            )

            return render(
                request,
                'payment_add.html',
                {
                    'tenants': tenants
                }
            )

        Payment.objects.create(
            tenant=tenant,
            amount=amount,
            payment_method=payment_method,
            status=status,
            transaction_id=transaction_id or None,
            description=description or None
        )

        messages.success(
            request,
            'Payment added successfully!'
        )

        return redirect(
            'payment_list'
        )

    return render(
        request,
        'payment_add.html',
        {
            'tenants': tenants
        }
    )


@login_required
def payment_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit Payment.'
        )

        return redirect(
            'tenant_dashboard'
        )

    payment = Payment.objects.filter(
        id=pk
    ).first()

    if not payment:

        messages.error(
            request,
            'Payment not found.'
        )

        return redirect(
            'payment_list'
        )

    tenants = Tenant.objects.filter(
        is_active=True
    ).order_by(
        'full_name'
    )

    if request.method == 'POST':

        tenant_id = request.POST.get(
            'tenant'
        )

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        payment_method = request.POST.get(
            'payment_method',
            ''
        ).strip()

        status = request.POST.get(
            'status',
            ''
        ).strip()

        transaction_id = request.POST.get(
            'transaction_id',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        tenant = Tenant.objects.filter(
            id=tenant_id,
            is_active=True
        ).first()

        if not tenant:

            messages.error(
                request,
                'Invalid tenant selected.'
            )

            return render(
                request,
                'payment_edit.html',
                {
                    'payment': payment,
                    'tenants': tenants
                }
            )

        error = validate_positive_decimal(
            amount,
            'Payment amount'
        )

        if error:

            messages.error(
                request,
                error
            )

            return render(
                request,
                'payment_edit.html',
                {
                    'payment': payment,
                    'tenants': tenants
                }
            )

        if payment_method not in [
            'Cash',
            'UPI',
            'Card'
        ]:

            messages.error(
                request,
                'Please select a valid payment method.'
            )

            return render(
                request,
                'payment_edit.html',
                {
                    'payment': payment,
                    'tenants': tenants
                }
            )

        if status not in [
            'Paid',
            'Pending'
        ]:

            messages.error(
                request,
                'Please select a valid payment status.'
            )

            return render(
                request,
                'payment_edit.html',
                {
                    'payment': payment,
                    'tenants': tenants
                }
            )

        if transaction_id and len(transaction_id) > 100:

            messages.error(
                request,
                'Transaction ID cannot exceed 100 characters.'
            )

            return render(
                request,
                'payment_edit.html',
                {
                    'payment': payment,
                    'tenants': tenants
                }
            )

        payment.tenant = tenant
        payment.amount = amount
        payment.payment_method = payment_method
        payment.status = status
        payment.transaction_id = transaction_id or None
        payment.description = description or None

        payment.save()

        messages.success(
            request,
            'Payment updated successfully!'
        )

        return redirect(
            'payment_list'
        )

    return render(
        request,
        'payment_edit.html',
        {
            'payment': payment,
            'tenants': tenants
        }
    )


@login_required
def payment_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete Payment.'
        )

        return redirect(
            'tenant_dashboard'
        )

    payment = Payment.objects.filter(
        id=pk
    ).first()

    if not payment:

        messages.error(
            request,
            'Payment not found.'
        )

        return redirect(
            'payment_list'
        )

    if request.method == 'POST':

        payment.delete()

        messages.success(
            request,
            'Payment deleted successfully!'
        )

        return redirect(
            'payment_list'
        )

    return render(
        request,
        'payment_delete.html',
        {
            'payment': payment
        }
    )


@login_required
def payment_mark_paid(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to verify payments.'
        )

        return redirect(
            'tenant_dashboard'
        )

    payment = Payment.objects.filter(
        pk=pk
    ).first()

    if not payment:

        messages.error(
            request,
            'Payment not found.'
        )

        return redirect(
            'payment_list'
        )

    payment.status = 'Paid'

    payment.save()

    messages.success(
        request,
        'Payment marked as Paid successfully!'
    )

    return redirect(
        'payment_list'
    )


# =========================================================
# PAYMENT RECEIPT
# =========================================================

@login_required
def payment_receipt(request, pk):

    payment = Payment.objects.select_related(
        'tenant'
    ).filter(
        pk=pk,
        tenant__user=request.user
    ).first()

    if not payment:

        messages.error(
            request,
            'Payment receipt not found.'
        )

        return redirect(
            'tenant_dashboard'
        )

    return render(
        request,
        'payment_receipt.html',
        {
            'payment': payment
        }
    )
# =========================================================
# TENANT PAYMENT
# =========================================================

@login_required
def tenant_payment(request):

    tenant = Tenant.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not tenant:
        messages.error(
            request,
            'Tenant profile not found.'
        )
        return redirect(
            'tenant_dashboard'
        )

    return render(
        request,
        'tenant_payment.html',
        {
            'tenant': tenant
        }
    )


@login_required
def tenant_make_payment(request):

    tenant = Tenant.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not tenant:
        messages.error(
            request,
            'Tenant profile not found.'
        )
        return redirect(
            'tenant_dashboard'
        )

    if request.method != 'POST':
        return redirect(
            'tenant_payment'
        )

    amount = request.POST.get(
        'amount',
        ''
    ).strip()

    payment_method = request.POST.get(
        'payment_method',
        ''
    ).strip()

    error = validate_positive_decimal(
        amount,
        'Payment amount'
    )

    if error:
        messages.error(
            request,
            error
        )
        return redirect(
            'tenant_payment'
        )

    if payment_method not in [
        'Cash',
        'UPI',
        'Card'
    ]:
        messages.error(
            request,
            'Please select a valid payment method.'
        )
        return redirect(
            'tenant_payment'
        )

    payment = Payment.objects.create(
        tenant=tenant,
        amount=amount,
        payment_method=payment_method,
        status='Paid',
        description='Online payment'
    )

    return render(
        request,
        'payment_success.html',
        {
            'payment': payment
        }
    )

# =========================================================
# COMPLAINT MANAGEMENT
# =========================================================

@login_required
def complaint_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to view complaints.'
        )

        return redirect(
            'tenant_dashboard'
        )

    complaints = Complaint.objects.select_related(
        'tenant'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'complaint_list.html',
        {
            'complaints': complaints
        }
    )


@login_required
def complaint_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add Complaint.'
        )

        return redirect(
            'tenant_dashboard'
        )

    tenants = Tenant.objects.filter(
        is_active=True
    ).order_by(
        'full_name'
    )

    if request.method == 'POST':

        tenant_id = request.POST.get(
            'tenant'
        )

        subject = request.POST.get(
            'subject',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        priority = request.POST.get(
            'priority',
            ''
        ).strip()

        status = request.POST.get(
            'status',
            ''
        ).strip()

        tenant = Tenant.objects.filter(
            id=tenant_id,
            is_active=True
        ).first()

        if not tenant:

            messages.error(
                request,
                'Please select a valid tenant.'
            )

            return render(
                request,
                'complaint_add.html',
                {
                    'tenants': tenants
                }
            )

        if not subject:

            messages.error(
                request,
                'Complaint subject is required.'
            )

            return render(
                request,
                'complaint_add.html',
                {
                    'tenants': tenants
                }
            )

        if len(subject) > 200:

            messages.error(
                request,
                'Complaint subject cannot exceed 200 characters.'
            )

            return render(
                request,
                'complaint_add.html',
                {
                    'tenants': tenants
                }
            )

        if not description:

            messages.error(
                request,
                'Complaint description is required.'
            )

            return render(
                request,
                'complaint_add.html',
                {
                    'tenants': tenants
                }
            )

        if priority not in [
            'Low',
            'Medium',
            'High'
        ]:

            messages.error(
                request,
                'Please select a valid priority.'
            )

            return render(
                request,
                'complaint_add.html',
                {
                    'tenants': tenants
                }
            )

        if status not in [
            'Pending',
            'In Progress',
            'Resolved'
        ]:

            messages.error(
                request,
                'Please select a valid complaint status.'
            )

            return render(
                request,
                'complaint_add.html',
                {
                    'tenants': tenants
                }
            )

        Complaint.objects.create(
            tenant=tenant,
            subject=subject,
            description=description,
            priority=priority,
            status=status
        )

        messages.success(
            request,
            'Complaint added successfully!'
        )

        return redirect(
            'complaint_list'
        )

    return render(
        request,
        'complaint_add.html',
        {
            'tenants': tenants
        }
    )


@login_required
def complaint_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit complaints.'
        )

        return redirect(
            'tenant_dashboard'
        )

    complaint = Complaint.objects.filter(
        pk=pk
    ).select_related(
        'tenant'
    ).first()

    if not complaint:

        messages.error(
            request,
            'Complaint not found.'
        )

        return redirect(
            'complaint_list'
        )

    if request.method == 'POST':

        subject = request.POST.get(
            'subject',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        priority = request.POST.get(
            'priority',
            ''
        ).strip()

        status = request.POST.get(
            'status',
            ''
        ).strip()

        if not subject:

            messages.error(
                request,
                'Complaint subject is required.'
            )

            return redirect(
                'complaint_edit',
                pk=pk
            )

        if len(subject) > 200:

            messages.error(
                request,
                'Complaint subject cannot exceed 200 characters.'
            )

            return redirect(
                'complaint_edit',
                pk=pk
            )

        if not description:

            messages.error(
                request,
                'Complaint description is required.'
            )

            return redirect(
                'complaint_edit',
                pk=pk
            )

        if priority not in [
            'Low',
            'Medium',
            'High'
        ]:

            messages.error(
                request,
                'Please select a valid priority.'
            )

            return redirect(
                'complaint_edit',
                pk=pk
            )

        if status not in [
            'Pending',
            'In Progress',
            'Resolved'
        ]:

            messages.error(
                request,
                'Please select a valid complaint status.'
            )

            return redirect(
                'complaint_edit',
                pk=pk
            )

        complaint.subject = subject
        complaint.description = description
        complaint.priority = priority
        complaint.status = status

        complaint.save()

        messages.success(
            request,
            'Complaint updated successfully!'
        )

        return redirect(
            'complaint_list'
        )

    return render(
        request,
        'complaint_edit.html',
        {
            'complaint': complaint
        }
    )


@login_required
def complaint_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete Complaint.'
        )

        return redirect(
            'tenant_dashboard'
        )

    complaint = Complaint.objects.filter(
        id=pk
    ).first()

    if not complaint:

        messages.error(
            request,
            'Complaint not found.'
        )

        return redirect(
            'complaint_list'
        )

    if request.method == 'POST':

        complaint.delete()

        messages.success(
            request,
            'Complaint deleted successfully!'
        )

        return redirect(
            'complaint_list'
        )

    return render(
        request,
        'complaint_delete.html',
        {
            'complaint': complaint
        }
    )


# =========================================================
# NOTICE MANAGEMENT
# =========================================================

@login_required
def notice_list(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to view notices.'
        )

        return redirect(
            'tenant_dashboard'
        )

    notices = Notice.objects.order_by(
        '-created_at'
    )

    return render(
        request,
        'notice_list.html',
        {
            'notices': notices
        }
    )


@login_required
def notice_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add notices.'
        )

        return redirect(
            'tenant_dashboard'
        )

    if request.method == 'POST':

        title = request.POST.get(
            'title',
            ''
        ).strip()

        message = request.POST.get(
            'message',
            ''
        ).strip()

        is_active = (
            request.POST.get(
                'is_active'
            ) == 'on'
        )

        if not title:

            messages.error(
                request,
                'Notice title is required.'
            )

            return redirect(
                'notice_add'
            )

        if len(title) > 200:

            messages.error(
                request,
                'Notice title cannot exceed 200 characters.'
            )

            return redirect(
                'notice_add'
            )

        if not message:

            messages.error(
                request,
                'Notice message is required.'
            )

            return redirect(
                'notice_add'
            )

        Notice.objects.create(
            title=title,
            message=message,
            is_active=is_active
        )

        messages.success(
            request,
            'Notice created successfully!'
        )

        return redirect(
            'notice_list'
        )

    return render(
        request,
        'notice_add.html'
    )


@login_required
def notice_edit(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to edit notices.'
        )

        return redirect(
            'tenant_dashboard'
        )

    notice = Notice.objects.filter(
        pk=pk
    ).first()

    if not notice:

        messages.error(
            request,
            'Notice not found.'
        )

        return redirect(
            'notice_list'
        )

    if request.method == 'POST':

        title = request.POST.get(
            'title',
            ''
        ).strip()

        message = request.POST.get(
            'message',
            ''
        ).strip()

        is_active = (
            request.POST.get(
                'is_active'
            ) == 'on'
        )

        if not title:

            messages.error(
                request,
                'Notice title is required.'
            )

            return redirect(
                'notice_edit',
                pk=pk
            )

        if len(title) > 200:

            messages.error(
                request,
                'Notice title cannot exceed 200 characters.'
            )

            return redirect(
                'notice_edit',
                pk=pk
            )

        if not message:

            messages.error(
                request,
                'Notice message is required.'
            )

            return redirect(
                'notice_edit',
                pk=pk
            )

        notice.title = title
        notice.message = message
        notice.is_active = is_active

        notice.save()

        messages.success(
            request,
            'Notice updated successfully!'
        )

        return redirect(
            'notice_list'
        )

    return render(
        request,
        'notice_edit.html',
        {
            'notice': notice
        }
    )


@login_required
def notice_delete(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to delete Notice.'
        )

        return redirect(
            'tenant_dashboard'
        )

    notice = Notice.objects.filter(
        id=pk
    ).first()

    if not notice:

        messages.error(
            request,
            'Notice not found.'
        )

        return redirect(
            'notice_list'
        )

    if request.method == 'POST':

        notice.delete()

        messages.success(
            request,
            'Notice deleted successfully!'
        )

        return redirect(
            'notice_list'
        )

    return render(
        request,
        'notice_delete.html',
        {
            'notice': notice
        }
    )


# =========================================================
# TENANT CHECK-IN
# =========================================================

@login_required
def tenant_check_in(request):

    tenant = Tenant.objects.filter(
        user=request.user
    ).first()

    if not tenant:

        messages.error(
            request,
            'Tenant profile not found.'
        )

        return redirect(
            'tenant_dashboard'
        )

    today = timezone.localdate()

    attendance, created = Attendance.objects.get_or_create(
        tenant=tenant,
        date=today,
        defaults={
            'check_in': timezone.now(),
            'status': 'Present'
        }
    )

    if not created and attendance.check_in is None:

        attendance.check_in = timezone.now()
        attendance.status = 'Present'

        attendance.save()

        messages.success(
            request,
            'Check-In successful!'
        )

    elif not created:

        messages.info(
            request,
            'You have already checked in today.'
        )

    else:

        messages.success(
            request,
            'Check-In successful!'
        )

    return redirect(
        'tenant_dashboard'
    )


# =========================================================
# TENANT CHECK-OUT
# =========================================================

@login_required
def tenant_check_out(request):

    tenant = Tenant.objects.filter(
        user=request.user
    ).first()

    if not tenant:

        messages.error(
            request,
            'Tenant profile not found.'
        )

        return redirect(
            'tenant_dashboard'
        )

    today = timezone.localdate()

    attendance = Attendance.objects.filter(
        tenant=tenant,
        date=today
    ).first()

    if not attendance:

        messages.error(
            request,
            'Please Check-In first.'
        )

        return redirect(
            'tenant_dashboard'
        )

    if attendance.check_out:

        messages.info(
            request,
            'You have already checked out today.'
        )

    else:

        attendance.check_out = timezone.now()
        attendance.save()

        messages.success(
            request,
            'Check-Out successful!'
        )

    return redirect(
        'tenant_dashboard'
    )


# =========================================================
# TENANT ATTENDANCE HISTORY
# =========================================================

@login_required
def tenant_attendance_history(request):

    tenant = Tenant.objects.filter(
        user=request.user
    ).first()

    if not tenant:

        messages.error(
            request,
            'Tenant profile not found.'
        )

        return redirect(
            'tenant_dashboard'
        )

    attendance_records = Attendance.objects.filter(
        tenant=tenant
    ).order_by(
        '-date',
        '-check_in'
    )

    return render(
        request,
        'tenant_attendance_history.html',
        {
            'tenant': tenant,
            'attendance_records': attendance_records,
        }
    )


# =========================================================
# ADMIN MANUAL ATTENDANCE
# =========================================================

@login_required
def attendance_add(request):

    if not request.user.is_staff:

        messages.error(
            request,
            'You are not authorized to add attendance.'
        )

        return redirect(
            'tenant_dashboard'
        )

    from datetime import datetime

    tenants = Tenant.objects.filter(
        is_active=True
    ).order_by(
        'full_name'
    )

    if request.method == 'POST':

        tenant_id = request.POST.get(
            'tenant',
            ''
        ).strip()

        attendance_date = request.POST.get(
            'date',
            ''
        ).strip()

        check_in = request.POST.get(
            'check_in',
            ''
        ).strip()

        check_out = request.POST.get(
            'check_out',
            ''
        ).strip()

        status = request.POST.get(
            'status',
            ''
        ).strip()

        # =====================================================
        # REQUIRED VALIDATION
        # =====================================================

        if not tenant_id:

            messages.error(
                request,
                'Please select a tenant.'
            )

            return redirect(
                'attendance_add'
            )

        if not attendance_date:

            messages.error(
                request,
                'Date is required.'
            )

            return redirect(
                'attendance_add'
            )

        if not status:

            messages.error(
                request,
                'Status is required.'
            )

            return redirect(
                'attendance_add'
            )

        # =====================================================
        # TENANT VALIDATION
        # =====================================================

        tenant = Tenant.objects.filter(
            id=tenant_id,
            is_active=True
        ).first()

        if not tenant:

            messages.error(
                request,
                'Invalid tenant selected.'
            )

            return redirect(
                'attendance_add'
            )

        # =====================================================
        # DATE VALIDATION
        # =====================================================

        try:

            attendance_date_obj = date.fromisoformat(
                attendance_date
            )

        except ValueError:

            messages.error(
                request,
                'Please enter a valid attendance date.'
            )

            return redirect(
                'attendance_add'
            )

        if attendance_date_obj > date.today():

            messages.error(
                request,
                'Attendance date cannot be in the future.'
            )

            return redirect(
                'attendance_add'
            )

        # =====================================================
        # STATUS VALIDATION
        # =====================================================

        if status not in [
            'Present',
            'Absent'
        ]:

            messages.error(
                request,
                'Please select a valid attendance status.'
            )

            return redirect(
                'attendance_add'
            )

        # =====================================================
        # DUPLICATE ATTENDANCE
        # =====================================================

        existing_attendance = Attendance.objects.filter(
            tenant=tenant,
            date=attendance_date_obj
        ).first()

        if existing_attendance:

            messages.error(
                request,
                'Attendance for this tenant and date already exists.'
            )

            return redirect(
                'attendance_add'
            )

        # =====================================================
        # PARSE CHECK-IN
        # =====================================================

        check_in_datetime = None

        if check_in:

            try:

                check_in_datetime = datetime.strptime(
                    check_in,
                    '%Y-%m-%dT%H:%M'
                )

            except ValueError:

                messages.error(
                    request,
                    'Please enter a valid Check-In date and time.'
                )

                return redirect(
                    'attendance_add'
                )

        # =====================================================
        # PARSE CHECK-OUT
        # =====================================================

        check_out_datetime = None

        if check_out:

            try:

                check_out_datetime = datetime.strptime(
                    check_out,
                    '%Y-%m-%dT%H:%M'
                )

            except ValueError:

                messages.error(
                    request,
                    'Please enter a valid Check-Out date and time.'
                )

                return redirect(
                    'attendance_add'
                )

        # =====================================================
        # CHECK-OUT MUST BE AFTER CHECK-IN
        # =====================================================

        if (
            check_in_datetime
            and check_out_datetime
            and check_out_datetime <= check_in_datetime
        ):

            messages.error(
                request,
                'Check-Out time must be after Check-In time.'
            )

            return redirect(
                'attendance_add'
            )

        # =====================================================
        # ABSENT VALIDATION
        # =====================================================

        if status == 'Absent':

            if check_in_datetime or check_out_datetime:

                messages.error(
                    request,
                    'Absent attendance should not have Check-In or Check-Out time.'
                )

                return redirect(
                    'attendance_add'
                )

        # =====================================================
        # CREATE ATTENDANCE
        # =====================================================

        attendance = Attendance(
            tenant=tenant,
            date=attendance_date_obj,
            status=status,
            check_in=check_in_datetime,
            check_out=check_out_datetime
        )

        attendance.save()

        messages.success(
            request,
            'Attendance added successfully!'
        )

        return redirect(
            'admin_dashboard'
        )

    return render(
        request,
        'attendance_add.html',
        {
            'tenants': tenants
        }
    )