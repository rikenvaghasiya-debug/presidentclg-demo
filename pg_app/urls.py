from django.urls import path
from . import views


urlpatterns = [

    # =========================
    # HOME / AUTHENTICATION
    # =========================

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),
path(
    'forgot-password/',
    views.CustomPasswordResetView.as_view(
        template_name='registration/password_reset_form.html'
    ),
    name='password_reset'
),
path(
    'forgot-password/done/',
    views.CustomPasswordResetDoneView.as_view(),
    name='password_reset_done'
),

path(
    'reset-password/<uidb64>/<token>/',
    views.CustomPasswordResetConfirmView.as_view(),
    name='password_reset_confirm'
),

path(
    'forgot-password/complete/',
    views.CustomPasswordResetCompleteView.as_view(),
    name='password_reset_complete'
),
    # =========================
    # TENANT DASHBOARD
    # =========================

    path(
        'tenant-dashboard/',
        views.tenant_dashboard,
        name='tenant_dashboard'
    ),

    path(
        'tenant/profile/edit/',
        views.tenant_profile_edit,
        name='tenant_profile_edit'
    ),

    path(
        'tenant/change-password/',
        views.tenant_change_password,
        name='tenant_change_password'
    ),

    path(
        'tenant/check-in/',
        views.tenant_check_in,
        name='tenant_check_in'
    ),

    path(
        'tenant/check-out/',
        views.tenant_check_out,
        name='tenant_check_out'
    ),

    path(
        'tenant/attendance/',
         views.tenant_attendance_history,
         name='tenant_attendance_history'
    ),

    path(
        'tenant/complaint/add/',
        views.tenant_complaint_add,
        name='tenant_complaint_add'
    ),


    # =========================
    # ADMIN DASHBOARD
    # =========================

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

path(
    'attendance/add/',
    views.attendance_add,
    name='attendance_add'
),

    # =========================
    # PG MANAGEMENT
    # =========================

    path(
        'pg/',
        views.pg_list,
        name='pg_list'
    ),

    path(
        'pg/add/',
        views.pg_add,
        name='pg_add'
    ),

    path(
        'pg/<int:pk>/edit/',
        views.pg_edit,
        name='pg_edit'
    ),

    path(
        'pg/<int:pk>/delete/',
        views.pg_delete,
        name='pg_delete'
    ),


    # =========================
    # ROOM MANAGEMENT
    # =========================

    path(
        'rooms/',
        views.room_list,
        name='room_list'
    ),

    path(
        'rooms/add/',
        views.room_add,
        name='room_add'
    ),

    path(
        'rooms/<int:pk>/edit/',
        views.room_edit,
        name='room_edit'
    ),

    path(
        'rooms/<int:pk>/delete/',
        views.room_delete,
        name='room_delete'
    ),


    # =========================
    # BED MANAGEMENT
    # =========================

    path(
        'beds/',
        views.bed_list,
        name='bed_list'
    ),

    path(
        'beds/add/',
        views.bed_add,
        name='bed_add'
    ),

    path(
        'beds/<int:pk>/edit/',
        views.bed_edit,
        name='bed_edit'
    ),

    path(
        'beds/<int:pk>/delete/',
        views.bed_delete,
        name='bed_delete'
    ),


    # =========================
    # TENANT MANAGEMENT
    # =========================

    path(
        'tenants/',
        views.tenant_list,
        name='tenant_list'
    ),

    path(
        'tenants/add/',
        views.tenant_add,
        name='tenant_add'
    ),

    path(
        'tenants/<int:pk>/edit/',
        views.tenant_edit,
        name='tenant_edit'
    ),

    path(
        'tenants/<int:pk>/delete/',
        views.tenant_delete,
        name='tenant_delete'
    ),


    # =========================
    # PAYMENT MANAGEMENT
    # =========================

    path(
        'payments/',
        views.payment_list,
        name='payment_list'
    ),

    path(
        'payments/add/',
        views.payment_add,
        name='payment_add'
    ),

    path(
        'payments/<int:pk>/edit/',
        views.payment_edit,
        name='payment_edit'
    ),

    path(
        'payments/<int:pk>/delete/',
        views.payment_delete,
        name='payment_delete'
    ),

    path(
        'payments/<int:pk>/mark-paid/',
        views.payment_mark_paid,
        name='payment_mark_paid'
    ),

    path(
        'payment/<int:pk>/receipt/',
        views.payment_receipt,
        name='payment_receipt'
    ),


    # =========================
    # COMPLAINT MANAGEMENT
    # =========================

    path(
        'complaints/',
        views.complaint_list,
        name='complaint_list'
    ),

    path(
        'complaints/add/',
        views.complaint_add,
        name='complaint_add'
    ),

    path(
        'complaints/<int:pk>/edit/',
        views.complaint_edit,
        name='complaint_edit'
    ),

    path(
        'complaints/<int:pk>/delete/',
        views.complaint_delete,
        name='complaint_delete'
    ),


    # =========================
    # NOTICE MANAGEMENT
    # =========================

    path(
        'notices/',
        views.notice_list,
        name='notice_list'
    ),

    path(
        'notices/add/',
        views.notice_add,
        name='notice_add'
    ),

    path(
        'notices/<int:pk>/edit/',
        views.notice_edit,
        name='notice_edit'
    ),

    path(
        'notices/<int:pk>/delete/',
        views.notice_delete,
        name='notice_delete'
    ),


    # =========================
    # TENANT ONLINE PAYMENT
    # =========================

    path(
        'tenant-payment/',
        views.tenant_payment,
        name='tenant_payment'
    ),

]