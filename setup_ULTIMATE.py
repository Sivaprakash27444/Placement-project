import os, sys

if not os.path.exists('manage.py'):
    print("ERROR: Run this from inside leave_management folder (where manage.py is).")
    sys.exit(1)

os.makedirs('employees/templates', exist_ok=True)
os.makedirs('employees/templates/admin', exist_ok=True)
os.makedirs('employees/static/employees/css', exist_ok=True)
print("Writing all files...")

# ── models.py ─────────────────────────────────────────────────────────────────
with open('employees/models.py','w',encoding='utf-8') as f:
    f.write("""from django.db import models

class Employee(models.Model):
    ROLE_CHOICES  = [('EMPLOYEE','Employee'),('MANAGER','Manager')]
    DEPT_CHOICES  = [('IT','IT'),('HR','HR'),('Finance','Finance'),
                     ('Operations','Operations'),('Marketing','Marketing')]
    name               = models.CharField(max_length=100)
    email              = models.EmailField(unique=True)
    password           = models.CharField(max_length=100)
    role               = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department         = models.CharField(max_length=20, choices=DEPT_CHOICES, default='IT')
    attendance_percent = models.FloatField(default=95.0)
    leave_balance      = models.IntegerField(default=20)
    joined_date        = models.DateField(null=True, blank=True)
    def __str__(self): return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected')]
    LEAVE_TYPES    = [('SICK','Sick Leave'),('CASUAL','Casual Leave'),
                      ('ANNUAL','Annual Leave'),('EMERGENCY','Emergency')]
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPES, default='CASUAL')
    start_date = models.DateField()
    end_date   = models.DateField()
    reason     = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_on = models.DateField(null=True, blank=True, auto_now_add=True)
    def days(self):
        return (self.end_date - self.start_date).days + 1
    def __str__(self): return f"{self.employee.name} - {self.status}"
""")
print("  employees/models.py")

# ── views.py ──────────────────────────────────────────────────────────────────
with open('employees/views.py','w',encoding='utf-8') as f:
    f.write("""from django.shortcuts import render, redirect
from .models import Employee, LeaveRequest

def login_view(request):
    if request.method == 'POST':
        try:
            user = Employee.objects.get(
                email=request.POST['email'],
                password=request.POST['password'])
            request.session['user_id'] = user.id
            request.session['role']    = user.role
            request.session['name']    = user.name
            if user.role == 'MANAGER':
                return redirect('manager_dashboard')
            return redirect('employee_dashboard')
        except:
            return render(request, 'login.html', {'error': 'Invalid email or password'})
    return render(request, 'login.html')

def employee_dashboard(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    uid      = request.session.get('user_id')
    employee = Employee.objects.get(id=uid)
    leaves   = LeaveRequest.objects.filter(employee_id=uid).order_by('-id')
    approved = leaves.filter(status='APPROVED').count()
    pending  = leaves.filter(status='PENDING').count()
    rejected = leaves.filter(status='REJECTED').count()
    att_gap  = round(100 - employee.attendance_percent, 1)
    used     = 20 - employee.leave_balance
    return render(request, 'employee_dashboard.html', {
        'employee': employee, 'leaves': leaves,
        'approved': approved, 'pending': pending, 'rejected': rejected,
        'att_gap': att_gap, 'leave_used': used,
    })

def attendance_view(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    uid      = request.session.get('user_id')
    employee = Employee.objects.get(id=uid)
    leaves   = LeaveRequest.objects.filter(employee_id=uid)
    approved = leaves.filter(status='APPROVED').count()
    att_gap  = round(100 - employee.attendance_percent, 1)
    used     = 20 - employee.leave_balance
    return render(request, 'attendance.html', {
        'employee': employee, 'att_gap': att_gap,
        'leave_used': used, 'approved': approved,
        'leaves': leaves,
    })

def manager_dashboard(request):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leaves         = LeaveRequest.objects.all().select_related('employee').order_by('-id')
    employees      = Employee.objects.filter(role='EMPLOYEE')
    pending_count  = leaves.filter(status='PENDING').count()
    approved_count = leaves.filter(status='APPROVED').count()
    rejected_count = leaves.filter(status='REJECTED').count()
    return render(request, 'manager_dashboard.html', {
        'leaves': leaves, 'employees': employees,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_leaves': leaves.count(),
        'total_emp': employees.count(),
        'name': request.session.get('name'),
    })

def apply_leave(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    uid      = request.session.get('user_id')
    employee = Employee.objects.get(id=uid)
    if request.method == 'POST':
        LeaveRequest.objects.create(
            employee_id=uid,
            leave_type=request.POST.get('leave_type','CASUAL'),
            start_date=request.POST['start'],
            end_date=request.POST['end'],
            reason=request.POST['reason'])
        return redirect('employee_dashboard')
    return render(request, 'apply_leave.html', {'employee': employee})

def update_status(request, id, status):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leave = LeaveRequest.objects.get(id=id)
    leave.status = status
    leave.save()
    if status == 'APPROVED':
        emp  = leave.employee
        days = leave.days()
        emp.attendance_percent = max(0, round(emp.attendance_percent - days * 0.5, 1))
        emp.leave_balance      = max(0, emp.leave_balance - days)
        emp.save()
    return redirect('manager_dashboard')

def logout_view(request):
    request.session.flush()
    return redirect('login')
""")
print("  employees/views.py")

# ── urls.py (app) ─────────────────────────────────────────────────────────────
with open('employees/urls.py','w',encoding='utf-8') as f:
    f.write("""from django.urls import path
from . import views
urlpatterns = [
    path('',                              views.login_view,         name='login'),
    path('employee/',                     views.employee_dashboard, name='employee_dashboard'),
    path('attendance/',                   views.attendance_view,    name='attendance'),
    path('manager/',                      views.manager_dashboard,  name='manager_dashboard'),
    path('apply/',                        views.apply_leave,        name='apply_leave'),
    path('update/<int:id>/<str:status>/', views.update_status,      name='update_status'),
    path('logout/',                       views.logout_view,        name='logout'),
]
""")
print("  employees/urls.py")

# ── main urls.py ──────────────────────────────────────────────────────────────
with open('leave_management/urls.py','w',encoding='utf-8') as f:
    f.write("""from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',       include('employees.urls')),
]
""")
print("  leave_management/urls.py")

# ── admin.py ──────────────────────────────────────────────────────────────────
with open('employees/admin.py','w',encoding='utf-8') as f:
    f.write("""from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Employee, LeaveRequest

admin.site.site_header  = 'S4 Limited — Administration'
admin.site.site_title   = 'S4 Limited Admin'
admin.site.index_title  = 'Leave Management Control Panel'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('name','email','role_badge','department',
                     'attendance_bar','leave_balance')
    list_filter   = ('role','department')
    search_fields = ('name','email')
    ordering      = ('name',)

    @admin.display(description='Attendance')
    def attendance_bar(self, obj):
        pct   = obj.attendance_percent
        color = '#10b981' if pct >= 90 else ('#f59e0b' if pct >= 75 else '#ef4444')
        label = 'Excellent' if pct >= 90 else ('Average' if pct >= 75 else 'Poor')
        return format_html(
            '<div style="min-width:180px">'
            '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">'
            '<span style="font-weight:700;color:{}">{:.1f}%</span>'
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{}</span>'
            '</div>'
            '<div style="background:#2d3148;border-radius:4px;height:8px">'
            '<div style="width:{:.0f}%;background:{};border-radius:4px;height:8px"></div>'
            '</div></div>',
            color, pct, color, label, pct, color
        )

    @admin.display(description='Role')
    def role_badge(self, obj):
        if obj.role == 'MANAGER':
            return format_html(
                '<span style="background:#3b0764;color:#c084fc;padding:4px 12px;'
                'border-radius:20px;font-size:11px;font-weight:700;'
                'border:1px solid #7c3aed">&#128737; Manager</span>'
            )
        return format_html(
            '<span style="background:#1e3a5f;color:#60a5fa;padding:4px 12px;'
            'border-radius:20px;font-size:11px;font-weight:700;'
            'border:1px solid #1d4ed8">&#128100; Employee</span>'
        )


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee_info','leave_type_badge','date_range',
                     'duration','reason_short','status_badge','quick_actions')
    list_filter   = ('status','leave_type','employee__department')
    search_fields = ('employee__name','reason')
    ordering      = ('-id',)
    actions       = ['approve_leaves','reject_leaves']
    list_per_page = 25

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/approve/',
                 self.admin_site.admin_view(self.approve_view),
                 name='leaverequest_approve'),
            path('<int:pk>/reject/',
                 self.admin_site.admin_view(self.reject_view),
                 name='leaverequest_reject'),
        ]
        return custom + urls

    def approve_view(self, request, pk):
        obj = get_object_or_404(LeaveRequest, pk=pk)
        obj.status = 'APPROVED'
        obj.save()
        emp  = obj.employee
        days = obj.days()
        emp.attendance_percent = max(0, round(emp.attendance_percent - days * 0.5, 1))
        emp.leave_balance      = max(0, emp.leave_balance - days)
        emp.save()
        messages.success(request,
            '{} leave for {} APPROVED. Attendance updated.'.format(
                obj.get_leave_type_display(), obj.employee.name))
        return redirect('../../')

    def reject_view(self, request, pk):
        obj = get_object_or_404(LeaveRequest, pk=pk)
        obj.status = 'REJECTED'
        obj.save()
        messages.error(request,
            '{} leave for {} REJECTED.'.format(
                obj.get_leave_type_display(), obj.employee.name))
        return redirect('../../')

    @admin.display(description='Employee')
    def employee_info(self, obj):
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px">'
            '<div style="width:36px;height:36px;border-radius:10px;'
            'background:linear-gradient(135deg,#4f46e5,#7c3aed);'
            'display:flex;align-items:center;justify-content:center;'
            'color:white;font-weight:800;font-size:15px;flex-shrink:0">{}</div>'
            '<div><div style="font-weight:700;font-size:13px;color:#e2e8f0">{}</div>'
            '<div style="font-size:11px;color:#8892b0">{}</div></div></div>',
            obj.employee.name[0].upper(), obj.employee.name, obj.employee.department
        )

    @admin.display(description='Leave Type')
    def leave_type_badge(self, obj):
        colors = {
            'SICK':      ('#1e3a5f','#60a5fa'),
            'CASUAL':    ('#1a2e1a','#4ade80'),
            'ANNUAL':    ('#3b2a00','#fbbf24'),
            'EMERGENCY': ('#3b0a0a','#f87171'),
        }
        bg, fg = colors.get(obj.leave_type, ('#1e293b','#94a3b8'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:6px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.get_leave_type_display()
        )

    @admin.display(description='Dates')
    def date_range(self, obj):
        return format_html(
            '<span style="font-size:12px;color:#a5b4fc;font-weight:600">'
            '{}<br>{}</span>', obj.start_date, obj.end_date)

    @admin.display(description='Days')
    def duration(self, obj):
        d = obj.days()
        return format_html(
            '<span style="background:#1e293b;color:#e2e8f0;padding:4px 10px;'
            'border-radius:6px;font-weight:800;font-size:14px">{}</span>', d)

    @admin.display(description='Reason')
    def reason_short(self, obj):
        r = obj.reason[:35] + '...' if len(obj.reason) > 35 else obj.reason
        return format_html('<span style="color:#8892b0;font-size:12px">{}</span>', r)

    @admin.display(description='Status')
    def status_badge(self, obj):
        cfg = {
            'PENDING':  ('#3b2a00','#fbbf24','&#9203; Pending'),
            'APPROVED': ('#052e16','#4ade80','&#9989; Approved'),
            'REJECTED': ('#3b0a0a','#f87171','&#10060; Rejected'),
        }
        bg, fg, label = cfg.get(obj.status, ('#1e293b','#94a3b8', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:5px 12px;'
            'border-radius:20px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, label)

    @admin.display(description='Action')
    def quick_actions(self, obj):
        if obj.status == 'PENDING':
            return format_html(
                '<a href="{}/approve/" style="display:inline-block;background:'
                'linear-gradient(135deg,#10b981,#059669);color:white;border-radius:7px;'
                'padding:6px 13px;font-size:11px;font-weight:700;text-decoration:none;'
                'margin-right:5px;box-shadow:0 3px 8px rgba(16,185,129,.4)">'
                '&#10003; Approve</a>'
                '<a href="{}/reject/" style="display:inline-block;background:'
                'linear-gradient(135deg,#ef4444,#dc2626);color:white;border-radius:7px;'
                'padding:6px 13px;font-size:11px;font-weight:700;text-decoration:none;'
                'box-shadow:0 3px 8px rgba(239,68,68,.4)">'
                '&#10007; Reject</a>',
                obj.pk, obj.pk)
        elif obj.status == 'APPROVED':
            return format_html(
                '<a href="{}/reject/" style="display:inline-block;background:#1e293b;'
                'color:#f87171;border-radius:7px;padding:6px 13px;font-size:11px;'
                'font-weight:700;text-decoration:none;border:1px solid #3b0a0a">Revoke</a>',
                obj.pk)
        return format_html(
            '<a href="{}/approve/" style="display:inline-block;background:#1e293b;'
            'color:#4ade80;border-radius:7px;padding:6px 13px;font-size:11px;'
            'font-weight:700;text-decoration:none;border:1px solid #052e16">Re-approve</a>',
            obj.pk)

    @admin.action(description='Approve selected leave requests')
    def approve_leaves(self, request, queryset):
        count = queryset.update(status='APPROVED')
        self.message_user(request, '{} request(s) approved.'.format(count))

    @admin.action(description='Reject selected leave requests')
    def reject_leaves(self, request, queryset):
        count = queryset.update(status='REJECTED')
        self.message_user(request, '{} request(s) rejected.'.format(count), messages.ERROR)
""")
print("  employees/admin.py")

# ── Admin CSS theme ───────────────────────────────────────────────────────────
with open('employees/static/employees/css/admin_theme.css','w',encoding='utf-8') as f:
    f.write("""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{font-family:'Inter',sans-serif!important}
:root{--p:#4f46e5;--a:#6366f1;--bg:#0f1117;--s:#1a1d2e;--s2:#232640;--b:rgba(255,255,255,.08);--t:#e2e8f0;--m:#8892b0}
body{background:var(--bg)!important;color:var(--t)!important}
#header{background:linear-gradient(135deg,#0f0c29,#302b63)!important;border-bottom:1px solid var(--b)!important;padding:0 28px!important;height:62px!important;display:flex!important;align-items:center!important;box-shadow:0 4px 24px rgba(0,0,0,.5)!important}
#branding h1,#branding h1 a{font-size:20px!important;font-weight:800!important;color:#fff!important;letter-spacing:-.5px!important}
#user-tools{color:rgba(255,255,255,.55)!important;font-size:12px!important}
#user-tools a{color:#a5b4fc!important;font-weight:600!important}
#nav-sidebar{background:var(--s)!important;border-right:1px solid var(--b)!important}
.module{background:var(--s)!important;border:1px solid var(--b)!important;border-radius:12px!important;overflow:hidden!important;margin-bottom:20px!important;box-shadow:0 4px 20px rgba(0,0,0,.3)!important}
.module h2,.module caption{background:linear-gradient(135deg,var(--p),var(--a))!important;color:#fff!important;font-weight:700!important;padding:12px 18px!important;font-size:12px!important;letter-spacing:.06em!important;text-transform:uppercase!important}
#content,#content-main{background:var(--bg)!important}
#content h1{font-size:22px!important;font-weight:800!important;color:#fff!important;margin-bottom:20px!important}
#result_list{background:var(--s)!important;border-radius:12px!important;overflow:hidden!important;border:1px solid var(--b)!important;width:100%!important}
#result_list thead th{background:var(--s2)!important;color:var(--m)!important;font-size:11px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.08em!important;padding:13px 16px!important;border-bottom:1px solid var(--b)!important}
#result_list thead th a{color:var(--m)!important}
#result_list thead th.sorted a{color:#a5b4fc!important}
#result_list tbody tr{border-bottom:1px solid var(--b)!important;transition:background .15s!important}
#result_list tbody tr:hover{background:rgba(99,102,241,.09)!important}
#result_list tbody td{padding:13px 16px!important;color:var(--t)!important;font-size:13px!important;vertical-align:middle!important;border:none!important}
#result_list tbody tr.selected{background:rgba(99,102,241,.16)!important}
input[type=checkbox]{accent-color:var(--p)!important;width:15px!important;height:15px!important}
.actions{background:var(--s2)!important;border:1px solid var(--b)!important;border-radius:10px!important;padding:12px 16px!important;margin-bottom:16px!important;display:flex!important;align-items:center!important;gap:12px!important}
.actions select{background:var(--s)!important;color:#fff!important;border:1px solid var(--b)!important;border-radius:8px!important;padding:8px 12px!important;font-size:13px!important;font-weight:600!important}
.actions button[type=submit],.actions input[type=submit]{background:linear-gradient(135deg,var(--p),var(--a))!important;color:#fff!important;border:none!important;border-radius:8px!important;padding:8px 18px!important;font-size:13px!important;font-weight:700!important;cursor:pointer!important;box-shadow:0 4px 12px rgba(79,70,229,.4)!important}
#searchbar,input[name=q]{background:var(--s2)!important;border:1px solid var(--b)!important;border-radius:8px!important;color:#fff!important;padding:9px 14px!important;font-size:13px!important;width:260px!important}
#searchbar:focus,input[name=q]:focus{border-color:var(--p)!important;box-shadow:0 0 0 3px rgba(99,102,241,.2)!important;outline:none!important}
input[type=submit][value=Search]{background:var(--p)!important;color:#fff!important;border:none!important;border-radius:8px!important;padding:9px 16px!important;font-weight:600!important;cursor:pointer!important}
#changelist-filter{background:var(--s)!important;border-left:1px solid var(--b)!important;padding:16px!important}
#changelist-filter h2{background:linear-gradient(135deg,var(--p),var(--a))!important;color:#fff!important;font-size:11px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.08em!important;padding:10px 14px!important;border-radius:8px!important;margin-bottom:12px!important}
#changelist-filter h3{color:var(--m)!important;font-size:10px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.08em!important;margin:14px 0 6px!important}
#changelist-filter ul{padding:0!important;list-style:none!important}
#changelist-filter ul li a{color:rgba(255,255,255,.6)!important;font-size:13px!important;padding:6px 10px!important;border-radius:6px!important;display:block!important;transition:all .15s!important}
#changelist-filter ul li a:hover,#changelist-filter ul li.selected a{background:rgba(99,102,241,.15)!important;color:#a5b4fc!important}
.submit-row{background:var(--s2)!important;border-top:1px solid var(--b)!important;border-radius:0 0 12px 12px!important;padding:14px 18px!important;display:flex!important;gap:10px!important}
.submit-row input[type=submit]{background:linear-gradient(135deg,var(--p),var(--a))!important;color:#fff!important;border:none!important;border-radius:8px!important;padding:10px 20px!important;font-size:13px!important;font-weight:700!important;cursor:pointer!important}
.form-row{border-bottom:1px solid var(--b)!important;padding:14px 18px!important}
.form-row label{color:var(--m)!important;font-size:12px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:.05em!important}
input[type=text],input[type=email],input[type=password],input[type=number],select,textarea{background:var(--s2)!important;border:1px solid var(--b)!important;border-radius:8px!important;color:#fff!important;padding:9px 12px!important;font-size:13px!important}
.messagelist li{border-radius:10px!important;font-weight:600!important;font-size:13px!important;padding:12px 18px!important;margin-bottom:10px!important}
.messagelist li.success{background:rgba(16,185,129,.15)!important;border:1px solid rgba(16,185,129,.3)!important;color:#6ee7b7!important}
.messagelist li.error{background:rgba(239,68,68,.15)!important;border:1px solid rgba(239,68,68,.3)!important;color:#fca5a5!important}
.messagelist li.warning{background:rgba(245,158,11,.15)!important;border:1px solid rgba(245,158,11,.3)!important;color:#fcd34d!important}
.breadcrumbs{background:var(--s)!important;border-bottom:1px solid var(--b)!important;padding:10px 24px!important;font-size:12px!important}
.breadcrumbs a{color:#a5b4fc!important}
.paginator{color:var(--m)!important;font-size:13px!important}
.paginator a{background:var(--s2)!important;color:#fff!important;border-radius:6px!important;padding:4px 10px!important;border:1px solid var(--b)!important}
.object-tools a{background:linear-gradient(135deg,var(--p),var(--a))!important;color:#fff!important;border-radius:8px!important;padding:8px 16px!important;font-size:12px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.05em!important;box-shadow:0 4px 12px rgba(79,70,229,.35)!important}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--s2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--p)}
""")
print("  employees/static/employees/css/admin_theme.css")

# ── Admin base_site.html ──────────────────────────────────────────────────────
with open('employees/templates/admin/base_site.html','w',encoding='utf-8') as f:
    f.write("""{% extends "admin/base.html" %}
{% block title %}{% if subtitle %}{{ subtitle }} | {% endif %}{{ title }} | S4 Limited Admin{% endblock %}
{% block extrastyle %}{{ block.super }}
<link rel="stylesheet" href="/static/employees/css/admin_theme.css">
{% endblock %}
{% block branding %}
<h1 id="site-name"><a href="{% url 'admin:index' %}">&#128197; S4 Limited &mdash; Administration</a></h1>
{% endblock %}
{% block nav-global %}{% endblock %}
""")
print("  employees/templates/admin/base_site.html")

# ── Shared sidebar CSS (reused in all employee/manager pages) ─────────────────
SIDEBAR_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f0f4f8;min-height:100vh;display:flex}
.sb{width:256px;background:linear-gradient(180deg,#0f172a,#1e1b4b);position:fixed;
  top:0;left:0;bottom:0;display:flex;flex-direction:column;
  box-shadow:4px 0 24px rgba(0,0,0,.3);z-index:50}
.sb-hd{padding:20px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:11px}
.sb-logo{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);
  border-radius:11px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sb-logo i{color:#fff;font-size:18px}
.sb-co{font-size:13px;font-weight:800;color:#fff;letter-spacing:-.3px}
.sb-tag{font-size:10px;color:rgba(255,255,255,.35)}
.sb-user{padding:13px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:10px}
.sb-av{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;
  font-size:15px;flex-shrink:0}
.sb-un{font-size:13px;font-weight:600;color:#fff}
.sb-ud{font-size:11px;color:rgba(255,255,255,.4)}
.sb-badge{display:inline-block;background:rgba(102,126,234,.25);color:#a5b4fc;
  font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;margin-top:2px}
.sb-nav{padding:12px 10px;flex:1;overflow-y:auto}
.sb-lbl{font-size:10px;color:rgba(255,255,255,.25);font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;padding:8px 12px 4px}
.sb-a{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:10px;
  color:rgba(255,255,255,.5);text-decoration:none;font-size:13px;font-weight:500;
  margin-bottom:2px;transition:all .2s}
.sb-a:hover{background:rgba(255,255,255,.06);color:rgba(255,255,255,.85)}
.sb-a.on{background:rgba(102,126,234,.22);color:#fff;box-shadow:inset 2px 0 0 #667eea}
.sb-a i{width:15px;text-align:center;font-size:14px}
.sb-ft{padding:13px 18px;border-top:1px solid rgba(255,255,255,.07)}
.sb-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
  color:rgba(255,255,255,.38);text-decoration:none;font-size:13px;font-weight:500;transition:all .2s}
.sb-out:hover{background:rgba(239,68,68,.12);color:#f87171}
.main{margin-left:256px;flex:1;padding:26px 30px}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
.pg-title{font-size:22px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.pg-sub{font-size:13px;color:#64748b;margin-top:3px}
.card{background:#fff;border-radius:15px;padding:20px 22px;
  box-shadow:0 1px 6px rgba(0,0,0,.05);border:1px solid #f0f4f8;margin-bottom:20px}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.card-title{font-size:13px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:7px}
.card-title i{color:#667eea}
.cnt{background:#f1f5f9;color:#64748b;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
.chip{display:inline-flex;align-items:center;gap:6px;background:#fff;
  border:1px solid #e8edf2;border-radius:8px;padding:5px 11px;
  font-size:12px;color:#475569;font-weight:500;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.chip i{color:#667eea;font-size:11px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.kpi{background:#fff;border-radius:14px;padding:18px 20px;
  box-shadow:0 1px 6px rgba(0,0,0,.05);border:1px solid #f0f4f8;position:relative;overflow:hidden}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.k1::before{background:linear-gradient(90deg,#667eea,#764ba2)}
.k2::before{background:linear-gradient(90deg,#10b981,#059669)}
.k3::before{background:linear-gradient(90deg,#f59e0b,#d97706)}
.k4::before{background:linear-gradient(90deg,#ef4444,#dc2626)}
.kpi-ic{width:42px;height:42px;border-radius:11px;display:flex;align-items:center;
  justify-content:center;font-size:17px;margin-bottom:12px}
.ki1{background:#ede9fe;color:#7c3aed}.ki2{background:#dcfce7;color:#16a34a}
.ki3{background:#fef3c7;color:#d97706}.ki4{background:#fee2e2;color:#dc2626}
.kpi-v{font-size:30px;font-weight:800;color:#0f172a;letter-spacing:-1px}
.kpi-l{font-size:12px;color:#64748b;font-weight:500;margin-top:2px}
table{width:100%;border-collapse:collapse}
.th{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.06em;padding:10px 12px;border-bottom:1px solid #f1f5f9;white-space:nowrap}
.td{padding:12px 12px;font-size:13px;color:#334155;border-bottom:1px solid #f8fafc;vertical-align:middle}
tr:last-child .td{border:none}
tr:hover .td{background:#fafbff}
.st{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.st-a{background:#f0fdf4;color:#16a34a}.st-p{background:#fffbeb;color:#d97706}.st-r{background:#fef2f2;color:#dc2626}
.lt{background:#ede9fe;color:#7c3aed;font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600}
.empty{text-align:center;padding:40px;color:#94a3b8;font-size:13px}
.empty i{font-size:38px;display:block;margin-bottom:10px;opacity:.35}
.prog{margin-bottom:13px}
.prog-top{display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px}
.prog-lbl{color:#64748b;font-weight:500;display:flex;align-items:center;gap:6px}
.prog-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.prog-val{color:#0f172a;font-weight:600}
.prog-bar{height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.prog-fill{height:100%;border-radius:4px}
.pg{background:linear-gradient(90deg,#10b981,#059669)}
.pr{background:linear-gradient(90deg,#ef4444,#dc2626)}
.pp{background:linear-gradient(90deg,#667eea,#764ba2)}
.py{background:linear-gradient(90deg,#f59e0b,#d97706)}
"""

# ── login.html ────────────────────────────────────────────────────────────────
with open('employees/templates/login.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>S4 Limited &mdash; LeaveFlow Sign In</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;min-height:100vh;display:flex;background:#0d0d1a}
.left{flex:1;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
  display:flex;flex-direction:column;justify-content:center;align-items:center;
  padding:60px;position:relative;overflow:hidden}
.left::before{content:'';position:absolute;top:-20%;left:-10%;width:500px;height:500px;
  background:radial-gradient(circle,rgba(102,126,234,.18),transparent 70%);border-radius:50%}
.left::after{content:'';position:absolute;bottom:-15%;right:-5%;width:400px;height:400px;
  background:radial-gradient(circle,rgba(118,75,162,.14),transparent 70%);border-radius:50%}
.brand-wrap{position:relative;z-index:1;text-align:center}
.co-badge{display:inline-block;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);
  border-radius:30px;padding:6px 18px;font-size:12px;font-weight:700;color:rgba(255,255,255,.7);
  letter-spacing:.08em;text-transform:uppercase;margin-bottom:22px}
.brand-icon{width:84px;height:84px;background:linear-gradient(135deg,#667eea,#764ba2);
  border-radius:24px;display:inline-flex;align-items:center;justify-content:center;
  box-shadow:0 20px 60px rgba(102,126,234,.45);margin-bottom:20px}
.brand-icon i{font-size:40px;color:#fff}
.brand-name{font-size:44px;font-weight:900;color:#fff;letter-spacing:-2px;line-height:1}
.brand-name span{background:linear-gradient(135deg,#a78bfa,#60a5fa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-tag{font-size:14px;color:rgba(255,255,255,.4);margin-top:10px}
.features{margin-top:44px;width:100%;max-width:370px;position:relative;z-index:1}
.feat{display:flex;align-items:center;gap:13px;padding:14px 17px;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  border-radius:13px;margin-bottom:9px}
.feat-ic{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;
  justify-content:center;font-size:15px;flex-shrink:0}
.f1{background:rgba(102,126,234,.25);color:#a5b4fc}
.f2{background:rgba(16,185,129,.25);color:#6ee7b7}
.f3{background:rgba(245,158,11,.25);color:#fcd34d}
.feat-txt{color:rgba(255,255,255,.7);font-size:13px;font-weight:500}
.right{width:480px;background:#fff;display:flex;align-items:center;
  justify-content:center;padding:56px 46px;box-shadow:-30px 0 80px rgba(0,0,0,.35)}
.login-box{width:100%}
.login-title{font-size:28px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.login-sub{font-size:14px;color:#94a3b8;margin-top:5px;margin-bottom:32px}
.field-group{margin-bottom:18px}
.field-label{font-size:11px;font-weight:700;color:#374151;margin-bottom:7px;display:block;
  text-transform:uppercase;letter-spacing:.07em}
.input-wrap{position:relative}
.input-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#94a3b8;font-size:13px}
.form-field{width:100%;padding:13px 13px 13px 40px;border:1.5px solid #e2e8f0;
  border-radius:12px;font-size:14px;color:#0f172a;background:#f8fafc;
  transition:all .2s;outline:none;font-family:'Inter',sans-serif}
.form-field:focus{border-color:#667eea;background:#fff;box-shadow:0 0 0 4px rgba(102,126,234,.1)}
.form-field::placeholder{color:#cbd5e1}
.btn-login{width:100%;padding:14px;background:linear-gradient(135deg,#667eea,#764ba2);
  border:none;border-radius:12px;color:#fff;font-size:15px;font-weight:700;cursor:pointer;
  font-family:'Inter',sans-serif;box-shadow:0 8px 24px rgba(102,126,234,.4);
  transition:all .25s;margin-top:4px}
.btn-login:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(102,126,234,.55)}
.error-box{background:#fff1f2;border:1.5px solid #fecdd3;border-radius:11px;
  padding:11px 15px;margin-bottom:20px;display:flex;align-items:center;gap:10px;
  font-size:13px;color:#e11d48;font-weight:500}
.divider{display:flex;align-items:center;gap:12px;margin:20px 0;color:#e2e8f0;font-size:11px}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:#e2e8f0}
.demo-row{display:flex;gap:10px}
.demo-chip{flex:1;padding:10px;border:1.5px solid #e2e8f0;border-radius:10px;
  text-align:center;font-size:11px;color:#64748b;font-weight:600;background:#f8fafc;line-height:1.7}
.demo-chip i{display:block;font-size:18px;margin-bottom:4px;color:#94a3b8}
.footer-note{text-align:center;font-size:11px;color:#cbd5e1;margin-top:22px}
</style>
</head>
<body>
<div class="left">
  <div class="brand-wrap">
    <div class="co-badge">S4 Limited</div>
    <div class="brand-icon"><i class="fas fa-calendar-check"></i></div>
    <div class="brand-name">Leave<span>Flow</span></div>
    <div class="brand-tag">Employee Leave Management System</div>
  </div>
  <div class="features">
    <div class="feat"><div class="feat-ic f1"><i class="fas fa-users-cog"></i></div>
      <div class="feat-txt">Role-based Employee &amp; Manager Portals</div></div>
    <div class="feat"><div class="feat-ic f2"><i class="fas fa-chart-pie"></i></div>
      <div class="feat-txt">Live Attendance Tracking &amp; Analytics</div></div>
    <div class="feat"><div class="feat-ic f3"><i class="fas fa-bolt"></i></div>
      <div class="feat-txt">One-click Leave Approvals via Admin Panel</div></div>
  </div>
</div>
<div class="right">
  <div class="login-box">
    <div class="login-title">Welcome back</div>
    <div class="login-sub">Sign in to your S4 Limited LeaveFlow account</div>
    {% if error %}<div class="error-box"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
    <form method="POST">
      {% csrf_token %}
      <div class="field-group">
        <label class="field-label">Email Address</label>
        <div class="input-wrap">
          <i class="fas fa-envelope input-icon"></i>
          <input type="email" name="email" class="form-field" placeholder="you@s4limited.com" required>
        </div>
      </div>
      <div class="field-group">
        <label class="field-label">Password</label>
        <div class="input-wrap">
          <i class="fas fa-lock input-icon"></i>
          <input type="password" name="password" class="form-field" placeholder="Enter your password" required>
        </div>
      </div>
      <button type="submit" class="btn-login"><i class="fas fa-sign-in-alt" style="margin-right:8px"></i>Sign In to LeaveFlow</button>
    </form>
    <div class="divider">Demo Credentials</div>
    <div class="demo-row">
      <div class="demo-chip"><i class="fas fa-user"></i>Employee<br>john@test.com<br><span style="color:#94a3b8;font-weight:400">test123</span></div>
      <div class="demo-chip"><i class="fas fa-user-shield"></i>Manager<br>sarah@test.com<br><span style="color:#94a3b8;font-weight:400">test123</span></div>
    </div>
    <div class="footer-note">S4 Limited &copy; 2025 &middot; LeaveFlow &middot; All rights reserved</div>
  </div>
</div>
</body>
</html>
""")
print("  employees/templates/login.html")

# ── employee_dashboard.html ───────────────────────────────────────────────────
with open('employees/templates/employee_dashboard.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>S4 Limited &mdash; My Dashboard</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
""" + SIDEBAR_STYLE + """
.new-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;
  background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;
  border-radius:11px;font-size:13px;font-weight:700;
  box-shadow:0 6px 18px rgba(102,126,234,.38);transition:all .2s;white-space:nowrap}
.new-btn:hover{transform:translateY(-2px);color:#fff;box-shadow:0 10px 28px rgba(102,126,234,.55)}
.two-col{display:grid;grid-template-columns:1.3fr .7fr;gap:18px;margin-bottom:20px}
.att-score{font-size:58px;font-weight:900;letter-spacing:-3px;text-align:center;line-height:1;margin:6px 0 2px}
.att-g{background:linear-gradient(135deg,#10b981,#059669);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-o{background:linear-gradient(135deg,#f59e0b,#d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-r{background:linear-gradient(135deg,#ef4444,#dc2626);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-lbl{font-size:12px;color:#94a3b8;text-align:center;margin-bottom:16px}
.att-status{display:flex;align-items:center;justify-content:center;gap:6px;
  padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:14px}
.s-good{background:#f0fdf4;color:#16a34a}.s-avg{background:#fffbeb;color:#d97706}.s-poor{background:#fef2f2;color:#dc2626}
.att-notice{background:linear-gradient(135deg,#ede9fe,#e0e7ff);border:1px solid #c4b5fd;
  border-radius:10px;padding:11px 14px;margin-bottom:18px;font-size:12px;
  color:#5b21b6;font-weight:500;display:flex;align-items:center;gap:8px}
.emp-cell{display:flex;align-items:center;gap:9px}
.emp-av{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;flex-shrink:0}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sb-co">S4 Limited</div><div class="sb-tag">LeaveFlow &middot; Employee</div></div>
  </div>
  <div class="sb-user">
    <div class="sb-av">{{ employee.name|first }}</div>
    <div><div class="sb-un">{{ employee.name }}</div><div class="sb-ud">{{ employee.department }}</div>
    <div class="sb-badge">Employee</div></div>
  </div>
  <div class="sb-nav">
    <div class="sb-lbl">Main Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="sb-a on"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}"        class="sb-a"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="sb-lbl">My Records</div>
    <a href="{% url 'attendance' %}"         class="sb-a"><i class="fas fa-chart-bar"></i>Attendance</a>
    <a href="#history"                       class="sb-a"><i class="fas fa-history"></i>Leave History</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Welcome, {{ employee.name }} &#128075;</div>
      <div class="pg-sub">S4 Limited &mdash; Leave Management Dashboard</div>
    </div>
    <a href="{% url 'apply_leave' %}" class="new-btn"><i class="fas fa-plus"></i>New Leave Request</a>
  </div>

  <div class="chips">
    <div class="chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
    <div class="chip"><i class="fas fa-umbrella-beach"></i>{{ employee.leave_balance }} days remaining</div>
  </div>

  <div class="kpis">
    <div class="kpi k1"><div class="kpi-ic ki1"><i class="fas fa-file-alt"></i></div>
      <div class="kpi-v">{{ leaves.count }}</div><div class="kpi-l">Total Requests</div></div>
    <div class="kpi k2"><div class="kpi-ic ki2"><i class="fas fa-check-circle"></i></div>
      <div class="kpi-v">{{ approved }}</div><div class="kpi-l">Approved</div></div>
    <div class="kpi k3"><div class="kpi-ic ki3"><i class="fas fa-clock"></i></div>
      <div class="kpi-v">{{ pending }}</div><div class="kpi-l">Pending</div></div>
    <div class="kpi k4"><div class="kpi-ic ki4"><i class="fas fa-times-circle"></i></div>
      <div class="kpi-v">{{ rejected }}</div><div class="kpi-l">Rejected</div></div>
  </div>

  <div class="att-notice">
    <i class="fas fa-info-circle"></i>
    Attendance is updated automatically when a manager approves your leave.
    View full attendance details in the <a href="{% url 'attendance' %}" style="color:#5b21b6;font-weight:700;margin:0 3px">Attendance</a> section.
  </div>

  <div class="two-col">
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-line"></i>Quick Attendance Summary</div>
        <a href="{% url 'attendance' %}" style="font-size:12px;color:#667eea;font-weight:600;text-decoration:none">View Full &rarr;</a></div>
      <div class="prog">
        <div class="prog-top">
          <span class="prog-lbl"><span class="prog-dot" style="background:#10b981"></span>Attendance Rate</span>
          <span class="prog-val">{{ employee.attendance_percent }}%</span>
        </div>
        <div class="prog-bar"><div class="prog-fill pg" style="width:{{ employee.attendance_percent }}%"></div></div>
      </div>
      <div class="prog">
        <div class="prog-top">
          <span class="prog-lbl"><span class="prog-dot" style="background:#ef4444"></span>Absent / Leave</span>
          <span class="prog-val">{{ att_gap }}%</span>
        </div>
        <div class="prog-bar"><div class="prog-fill pr" style="width:{{ att_gap }}%"></div></div>
      </div>
      <div class="prog">
        <div class="prog-top">
          <span class="prog-lbl"><span class="prog-dot" style="background:#667eea"></span>Leave Days Used</span>
          <span class="prog-val">{{ leave_used }} of 20</span>
        </div>
        <div class="prog-bar"><div class="prog-fill pp" style="width:{% widthratio leave_used 20 100 %}%"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-tachometer-alt"></i>Score</div></div>
      <div class="att-score {% if employee.attendance_percent >= 90 %}att-g{% elif employee.attendance_percent >= 75 %}att-o{% else %}att-r{% endif %}">{{ employee.attendance_percent }}%</div>
      <div class="att-lbl">Overall Attendance Rate</div>
      <div class="att-status {% if employee.attendance_percent >= 90 %}s-good{% elif employee.attendance_percent >= 75 %}s-avg{% else %}s-poor{% endif %}">
        {% if employee.attendance_percent >= 90 %}<i class="fas fa-check-circle"></i>Excellent
        {% elif employee.attendance_percent >= 75 %}<i class="fas fa-exclamation-circle"></i>Average
        {% else %}<i class="fas fa-times-circle"></i>Poor{% endif %}
      </div>
      <canvas id="attChart" height="150"></canvas>
    </div>
  </div>

  <div class="card" id="history">
    <div class="card-hd">
      <div class="card-title"><i class="fas fa-history"></i>Leave Request History</div>
      <span class="cnt">{{ leaves.count }} records</span>
    </div>
    <table>
      <thead><tr>
        <th class="th">#</th><th class="th">Type</th><th class="th">From</th>
        <th class="th">To</th><th class="th">Days</th><th class="th">Reason</th><th class="th">Status</th>
      </tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td class="td" style="color:#94a3b8;font-size:12px">{{ forloop.counter }}</td>
        <td class="td"><span class="lt">{{ leave.leave_type }}</span></td>
        <td class="td">{{ leave.start_date }}</td>
        <td class="td">{{ leave.end_date }}</td>
        <td class="td"><strong>{{ leave.days }}d</strong></td>
        <td class="td" style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#64748b">{{ leave.reason }}</td>
        <td class="td">
          {% if leave.status == 'APPROVED' %}<span class="st st-a"><i class="fas fa-check"></i>Approved</span>
          {% elif leave.status == 'REJECTED' %}<span class="st st-r"><i class="fas fa-times"></i>Rejected</span>
          {% else %}<span class="st st-p"><i class="fas fa-clock"></i>Pending</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="7"><div class="empty"><i class="fas fa-folder-open"></i>No requests yet. Click New Leave Request to get started.</div></td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
new Chart(document.getElementById('attChart'),{
  type:'doughnut',
  data:{labels:['Present','Absent'],
    datasets:[{data:[{{ employee.attendance_percent }},{{ att_gap }}],
      backgroundColor:['#10b981','#fee2e2'],borderColor:['#059669','#fca5a5'],
      borderWidth:2,hoverOffset:5}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',
    labels:{padding:14,font:{size:11},boxWidth:10}}},cutout:'72%'}
});
</script>
</body>
</html>
""")
print("  employees/templates/employee_dashboard.html")

# ── attendance.html ───────────────────────────────────────────────────────────
with open('employees/templates/attendance.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>S4 Limited &mdash; My Attendance</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
""" + SIDEBAR_STYLE + """
.att-hero{background:linear-gradient(135deg,#0f172a,#1e1b4b);border-radius:18px;
  padding:36px 40px;margin-bottom:22px;display:flex;align-items:center;gap:40px;
  box-shadow:0 8px 32px rgba(15,23,42,.15)}
.att-big-num{font-size:80px;font-weight:900;letter-spacing:-4px;line-height:1}
.att-big-g{background:linear-gradient(135deg,#10b981,#6ee7b7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-big-o{background:linear-gradient(135deg,#f59e0b,#fcd34d);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-big-r{background:linear-gradient(135deg,#ef4444,#fca5a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-hero-info{flex:1}
.att-hero-title{font-size:22px;font-weight:800;color:#fff;margin-bottom:8px}
.att-hero-sub{font-size:14px;color:rgba(255,255,255,.5);margin-bottom:20px}
.hero-pills{display:flex;gap:10px;flex-wrap:wrap}
.hero-pill{padding:8px 16px;border-radius:20px;font-size:12px;font-weight:700}
.hp-g{background:rgba(16,185,129,.2);color:#6ee7b7;border:1px solid rgba(16,185,129,.3)}
.hp-r{background:rgba(239,68,68,.2);color:#fca5a5;border:1px solid rgba(239,68,68,.3)}
.hp-p{background:rgba(102,126,234,.2);color:#a5b4fc;border:1px solid rgba(102,126,234,.3)}
.hp-y{background:rgba(245,158,11,.2);color:#fcd34d;border:1px solid rgba(245,158,11,.3)}
.three-col{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.stat-box{background:#fff;border-radius:14px;padding:20px;box-shadow:0 1px 6px rgba(0,0,0,.05);
  border:1px solid #f0f4f8;text-align:center}
.stat-box-v{font-size:36px;font-weight:800;color:#0f172a;letter-spacing:-1px}
.stat-box-l{font-size:12px;color:#64748b;margin-top:4px;font-weight:500}
.two-charts{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
.month-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:10px}
.month-box{padding:10px 6px;border-radius:9px;text-align:center;font-size:11px;font-weight:600}
.mb-g{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0}
.mb-y{background:#fffbeb;color:#d97706;border:1px solid #fde68a}
.mb-r{background:#fef2f2;color:#dc2626;border:1px solid #fecaca}
.month-pct{font-size:14px;font-weight:800;display:block;margin-top:3px}
.timeline{display:flex;flex-direction:column;gap:0}
.tl-row{display:flex;align-items:center;gap:14px;padding:12px 0;border-bottom:1px solid #f8fafc}
.tl-row:last-child{border:none}
.tl-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.tl-date{font-size:12px;color:#64748b;min-width:90px;font-weight:500}
.tl-type{font-size:11px;padding:3px 9px;border-radius:6px;font-weight:700;flex-shrink:0}
.tl-reason{font-size:12px;color:#94a3b8;flex:1}
.tl-days{font-size:13px;font-weight:700;color:#0f172a;min-width:36px;text-align:right}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sb-co">S4 Limited</div><div class="sb-tag">LeaveFlow &middot; Employee</div></div>
  </div>
  <div class="sb-user">
    <div class="sb-av">{{ employee.name|first }}</div>
    <div><div class="sb-un">{{ employee.name }}</div><div class="sb-ud">{{ employee.department }}</div>
    <div class="sb-badge">Employee</div></div>
  </div>
  <div class="sb-nav">
    <div class="sb-lbl">Main Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="sb-a"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}"        class="sb-a"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="sb-lbl">My Records</div>
    <a href="{% url 'attendance' %}"         class="sb-a on"><i class="fas fa-chart-bar"></i>Attendance</a>
    <a href="{% url 'employee_dashboard' %}#history" class="sb-a"><i class="fas fa-history"></i>Leave History</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Attendance Report &#128202;</div>
      <div class="pg-sub">S4 Limited &mdash; Your complete attendance analysis</div>
    </div>
  </div>

  <div class="att-hero">
    <div class="att-big-num {% if employee.attendance_percent >= 90 %}att-big-g{% elif employee.attendance_percent >= 75 %}att-big-o{% else %}att-big-r{% endif %}">
      {{ employee.attendance_percent }}%
    </div>
    <div class="att-hero-info">
      <div class="att-hero-title">
        {% if employee.attendance_percent >= 90 %}Excellent Attendance &#127881;
        {% elif employee.attendance_percent >= 75 %}Average Attendance &#9888;
        {% else %}Poor Attendance &#128680;{% endif %}
      </div>
      <div class="att-hero-sub">{{ employee.name }} &middot; {{ employee.department }} &middot; S4 Limited</div>
      <div class="hero-pills">
        <div class="hero-pill hp-g"><i class="fas fa-check-circle" style="margin-right:5px"></i>{{ employee.attendance_percent }}% Present</div>
        <div class="hero-pill hp-r"><i class="fas fa-times-circle" style="margin-right:5px"></i>{{ att_gap }}% Absent</div>
        <div class="hero-pill hp-p"><i class="fas fa-umbrella-beach" style="margin-right:5px"></i>{{ leave_used }} Days Used</div>
        <div class="hero-pill hp-y"><i class="fas fa-calendar-plus" style="margin-right:5px"></i>{{ employee.leave_balance }} Days Left</div>
      </div>
    </div>
  </div>

  <div class="three-col">
    <div class="stat-box">
      <div class="stat-box-v" style="color:#10b981">{{ employee.attendance_percent }}%</div>
      <div class="stat-box-l">Attendance Rate</div>
    </div>
    <div class="stat-box">
      <div class="stat-box-v" style="color:#667eea">{{ employee.leave_balance }}</div>
      <div class="stat-box-l">Leave Days Remaining</div>
    </div>
    <div class="stat-box">
      <div class="stat-box-v" style="color:#f59e0b">{{ approved }}</div>
      <div class="stat-box-l">Approved Leaves Taken</div>
    </div>
  </div>

  <div class="two-charts">
    <div class="card" style="margin-bottom:0">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-donut"></i>Attendance vs Absence</div></div>
      <canvas id="attPie" height="230"></canvas>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-bar"></i>Leave Balance Tracker</div></div>
      <canvas id="balBar" height="230"></canvas>
    </div>
  </div>

  <div class="card" style="margin-top:20px">
    <div class="card-hd">
      <div class="card-title"><i class="fas fa-list-alt"></i>Leave History Timeline</div>
      <span class="cnt">{{ leaves.count }} records</span>
    </div>
    <div class="timeline">
    {% for leave in leaves %}
    <div class="tl-row">
      <div class="tl-dot" style="background:{% if leave.status == 'APPROVED' %}#10b981{% elif leave.status == 'REJECTED' %}#ef4444{% else %}#f59e0b{% endif %}"></div>
      <div class="tl-date">{{ leave.start_date }}</div>
      <span class="tl-type" style="background:{% if leave.leave_type == 'SICK' %}#dbeafe;color:#2563eb{% elif leave.leave_type == 'ANNUAL' %}#fef3c7;color:#d97706{% elif leave.leave_type == 'EMERGENCY' %}#fee2e2;color:#dc2626{% else %}#dcfce7;color:#16a34a{% endif %}">{{ leave.leave_type }}</span>
      <div class="tl-reason">{{ leave.reason|truncatechars:50 }}</div>
      <div class="tl-days">{{ leave.days }}d</div>
      <span class="st {% if leave.status == 'APPROVED' %}st-a{% elif leave.status == 'REJECTED' %}st-r{% else %}st-p{% endif %}">{{ leave.status }}</span>
    </div>
    {% empty %}
    <div class="empty"><i class="fas fa-calendar-times"></i>No leave history found.</div>
    {% endfor %}
    </div>
  </div>
</div>

<script>
new Chart(document.getElementById('attPie'),{
  type:'doughnut',
  data:{labels:['Present','Absent/Leave'],
    datasets:[{data:[{{ employee.attendance_percent }},{{ att_gap }}],
      backgroundColor:['#10b981','#ef4444'],borderColor:['#d1fae5','#fee2e2'],
      borderWidth:2,hoverOffset:6}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:16,font:{size:12},boxWidth:12}}},cutout:'65%'}
});
new Chart(document.getElementById('balBar'),{
  type:'bar',
  data:{labels:['Total Leave','Used','Remaining'],
    datasets:[{data:[20,{{ leave_used }},{{ employee.leave_balance }}],
      backgroundColor:['#667eea','#ef4444','#10b981'],borderRadius:8,borderSkipped:false}]},
  options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:25,grid:{color:'rgba(0,0,0,.04)'},ticks:{font:{size:11}}}}}
});
</script>
</body>
</html>
""")
print("  employees/templates/attendance.html")

# ── manager_dashboard.html ────────────────────────────────────────────────────
with open('employees/templates/manager_dashboard.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>S4 Limited &mdash; Manager Dashboard</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
""" + SIDEBAR_STYLE.replace(
    'background:linear-gradient(180deg,#0f172a,#1e1b4b)',
    'background:linear-gradient(180deg,#0f0c29,#1a0533,#2d1b69)'
).replace(
    'background:linear-gradient(135deg,#667eea,#764ba2)',
    'background:linear-gradient(135deg,#f093fb,#f5576c)'
) + """
.sb-badge{background:rgba(240,147,251,.2)!important;color:#f9a8d4!important}
.sb-a.on{background:rgba(240,147,251,.15)!important;box-shadow:inset 2px 0 0 #f093fb!important}
.pend-pill{background:#f59e0b;color:#fff;font-size:10px;padding:2px 7px;border-radius:10px;margin-left:auto;font-weight:600}
.two-grid{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.emp-cell{display:flex;align-items:center;gap:9px}
.emp-av{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;flex-shrink:0}
.emp-nm{font-size:13px;font-weight:600;color:#0f172a}
.emp-dep{font-size:11px;color:#94a3b8}
.btn-app{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;
  background:linear-gradient(135deg,#10b981,#059669);border:none;border-radius:7px;
  color:#fff;font-size:11px;font-weight:600;text-decoration:none;transition:all .15s}
.btn-app:hover{transform:translateY(-1px);color:#fff;box-shadow:0 4px 10px rgba(16,185,129,.3)}
.btn-rej{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;
  background:linear-gradient(135deg,#ef4444,#dc2626);border:none;border-radius:7px;
  color:#fff;font-size:11px;font-weight:600;text-decoration:none;margin-left:5px;transition:all .15s}
.btn-rej:hover{transform:translateY(-1px);color:#fff;box-shadow:0 4px 10px rgba(239,68,68,.3)}
.att-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #f8fafc}
.att-row:last-child{border:none}
.att-av{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;flex-shrink:0}
.att-info{min-width:130px}
.att-nm{font-size:13px;font-weight:600;color:#0f172a}
.att-dp{font-size:11px;color:#94a3b8}
.att-bw{flex:1}
.att-bt{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px}
.att-bar{height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.att-fill{height:100%;border-radius:4px}
.ag{background:linear-gradient(90deg,#10b981,#059669)}
.ay{background:linear-gradient(90deg,#f59e0b,#d97706)}
.ar{background:linear-gradient(90deg,#ef4444,#dc2626)}
.att-tag{font-size:10px;padding:3px 9px;border-radius:10px;font-weight:600;white-space:nowrap;min-width:66px;text-align:center}
.tg{background:#f0fdf4;color:#16a34a}.ty{background:#fffbeb;color:#d97706}.tr{background:#fef2f2;color:#dc2626}
.admin-notice{background:linear-gradient(135deg,#fef3c7,#fde68a);border:1px solid #f59e0b;
  border-radius:11px;padding:12px 16px;margin-bottom:20px;font-size:13px;
  color:#92400e;font-weight:500;display:flex;align-items:center;gap:9px}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-shield-alt"></i></div>
    <div><div class="sb-co">S4 Limited</div><div class="sb-tag">LeaveFlow &middot; Manager</div></div>
  </div>
  <div class="sb-user">
    <div class="sb-av">M</div>
    <div><div class="sb-un">{{ name }}</div><div class="sb-badge">Manager</div></div>
  </div>
  <div class="sb-nav">
    <div class="sb-lbl">Management</div>
    <a href="{% url 'manager_dashboard' %}" class="sb-a on"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="#requests"    class="sb-a"><i class="fas fa-inbox"></i>Leave Requests
      {% if pending_count > 0 %}<span class="pend-pill">{{ pending_count }}</span>{% endif %}</a>
    <a href="#attendance"  class="sb-a"><i class="fas fa-chart-bar"></i>Team Attendance</a>
    <a href="#team"        class="sb-a"><i class="fas fa-users"></i>Team Overview</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Manager Dashboard &#128737;</div>
      <div class="pg-sub">S4 Limited &mdash; Team leave management &amp; attendance monitoring</div>
    </div>
  </div>

  <div class="kpis">
    <div class="kpi k1"><div class="kpi-ic ki1"><i class="fas fa-users"></i></div>
      <div class="kpi-v">{{ total_emp }}</div><div class="kpi-l">Total Employees</div></div>
    <div class="kpi k3"><div class="kpi-ic ki3"><i class="fas fa-hourglass-half"></i></div>
      <div class="kpi-v">{{ pending_count }}</div><div class="kpi-l">Pending Approvals</div></div>
    <div class="kpi k2"><div class="kpi-ic ki2"><i class="fas fa-check-double"></i></div>
      <div class="kpi-v">{{ approved_count }}</div><div class="kpi-l">Approved</div></div>
    <div class="kpi k4"><div class="kpi-ic ki4"><i class="fas fa-file-alt"></i></div>
      <div class="kpi-v">{{ total_leaves }}</div><div class="kpi-l">Total Requests</div></div>
  </div>

  <div class="admin-notice">
    <i class="fas fa-lock"></i>
    To <strong style="margin:0 3px">Approve or Reject</strong> leave requests, use the
    <a href="/admin/employees/leaverequest/" style="color:#92400e;font-weight:700;margin:0 4px">Admin Panel &rarr;</a>
    where you can approve/reject with one click.
  </div>

  <div class="two-grid" id="requests">
    <div class="card" style="margin-bottom:0">
      <div class="card-hd">
        <div class="card-title"><i class="fas fa-inbox"></i>All Leave Requests</div>
        {% if pending_count > 0 %}<span style="background:#fffbeb;color:#d97706;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600">{{ pending_count }} pending</span>
        {% else %}<span class="cnt">{{ total_leaves }} total</span>{% endif %}
      </div>
      <table>
        <thead><tr>
          <th class="th">Employee</th><th class="th">Type</th>
          <th class="th">From</th><th class="th">To</th>
          <th class="th">Days</th><th class="th">Status</th>
        </tr></thead>
        <tbody>
        {% for leave in leaves %}
        <tr>
          <td class="td">
            <div class="emp-cell">
              <div class="emp-av">{{ leave.employee.name|first }}</div>
              <div><div class="emp-nm">{{ leave.employee.name }}</div><div class="emp-dep">{{ leave.employee.department }}</div></div>
            </div>
          </td>
          <td class="td"><span class="lt">{{ leave.leave_type }}</span></td>
          <td class="td" style="font-size:12px">{{ leave.start_date }}</td>
          <td class="td" style="font-size:12px">{{ leave.end_date }}</td>
          <td class="td"><strong>{{ leave.days }}d</strong></td>
          <td class="td">
            {% if leave.status == 'APPROVED' %}<span class="st st-a"><i class="fas fa-check"></i>Approved</span>
            {% elif leave.status == 'REJECTED' %}<span class="st st-r"><i class="fas fa-times"></i>Rejected</span>
            {% else %}<span class="st st-p"><i class="fas fa-clock"></i>Pending</span>{% endif %}
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="6"><div class="empty"><i class="fas fa-inbox"></i>No requests found.</div></td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-pie"></i>Overview</div></div>
      <canvas id="donut" height="210"></canvas>
      <div style="margin-top:14px">
        <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f8fafc;font-size:12px"><span style="color:#64748b">Approved</span><strong style="color:#16a34a">{{ approved_count }}</strong></div>
        <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f8fafc;font-size:12px"><span style="color:#64748b">Pending</span><strong style="color:#d97706">{{ pending_count }}</strong></div>
        <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:12px"><span style="color:#64748b">Rejected</span><strong style="color:#dc2626">{{ rejected_count }}</strong></div>
      </div>
    </div>
  </div>

  <div class="card" id="attendance" style="margin-top:20px">
    <div class="card-hd">
      <div class="card-title"><i class="fas fa-chart-bar"></i>Team Attendance Tracker</div>
      <span class="cnt">{{ total_emp }} employees</span>
    </div>
    {% for emp in employees %}
    <div class="att-row">
      <div class="att-av">{{ emp.name|first }}</div>
      <div class="att-info"><div class="att-nm">{{ emp.name }}</div><div class="att-dp">{{ emp.department }} &middot; {{ emp.leave_balance }}d left</div></div>
      <div class="att-bw">
        <div class="att-bt"><span style="color:#64748b">Attendance</span><span style="font-weight:700;color:#0f172a">{{ emp.attendance_percent }}%</span></div>
        <div class="att-bar"><div class="att-fill {% if emp.attendance_percent >= 90 %}ag{% elif emp.attendance_percent >= 75 %}ay{% else %}ar{% endif %}" style="width:{{ emp.attendance_percent }}%"></div></div>
      </div>
      <div class="att-tag {% if emp.attendance_percent >= 90 %}tg{% elif emp.attendance_percent >= 75 %}ty{% else %}tr{% endif %}">
        {% if emp.attendance_percent >= 90 %}Excellent{% elif emp.attendance_percent >= 75 %}Average{% else %}Poor{% endif %}
      </div>
    </div>
    {% empty %}
    <div class="empty"><i class="fas fa-users"></i>No employees found.</div>
    {% endfor %}
  </div>
</div>

<script>
new Chart(document.getElementById('donut'),{
  type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],
    datasets:[{data:[{{ approved_count }},{{ pending_count }},{{ rejected_count }}],
      backgroundColor:['#10b981','#f59e0b','#ef4444'],
      borderColor:['#d1fae5','#fef3c7','#fee2e2'],borderWidth:2,hoverOffset:6}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:14,font:{size:11},boxWidth:10}}},cutout:'68%'}
});
</script>
</body>
</html>
""")
print("  employees/templates/manager_dashboard.html")

# ── apply_leave.html ──────────────────────────────────────────────────────────
with open('employees/templates/apply_leave.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>S4 Limited &mdash; Apply Leave</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
""" + SIDEBAR_STYLE + """
.main{margin-left:256px;flex:1;display:flex;justify-content:center;padding:40px 60px;align-items:flex-start}
.form-wrap{width:100%;max-width:600px}
.bal-info{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:11px;
  padding:12px 16px;margin-bottom:22px;display:flex;align-items:center;gap:10px;
  font-size:13px;color:#166534;font-weight:500}
.form-card{background:#fff;border-radius:18px;padding:34px 36px;
  box-shadow:0 4px 24px rgba(0,0,0,.07);border:1px solid #f0f4f8}
.section-hd{font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.08em;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #f1f5f9}
.lt-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px}
.lt-opt{position:relative}
.lt-opt input{position:absolute;opacity:0;width:0}
.lt-card{display:flex;align-items:center;gap:10px;padding:12px 14px;
  border:1.5px solid #e2e8f0;border-radius:11px;cursor:pointer;transition:all .2s;background:#fafafa}
.lt-card:hover{border-color:#a5b4fc;background:#f5f3ff}
.lt-opt input:checked + .lt-card{border-color:#667eea;background:#ede9fe;box-shadow:0 0 0 3px rgba(102,126,234,.12)}
.lt-ic{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.li1{background:#dbeafe;color:#2563eb}.li2{background:#fce7f3;color:#db2777}
.li3{background:#dcfce7;color:#16a34a}.li4{background:#fee2e2;color:#dc2626}
.lt-nm{font-size:13px;font-weight:600;color:#0f172a}
.lt-sb{font-size:11px;color:#94a3b8}
.date-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}
.field-group{margin-bottom:20px}
.field-lbl{font-size:11px;font-weight:700;color:#374151;margin-bottom:7px;display:block;
  text-transform:uppercase;letter-spacing:.05em}
.field-lbl i{color:#667eea;margin-right:4px}
.form-input{width:100%;padding:12px 14px;border:1.5px solid #e2e8f0;border-radius:11px;
  font-size:14px;color:#0f172a;background:#fafafa;transition:all .2s;outline:none;
  font-family:'Inter',sans-serif}
.form-input:focus{border-color:#667eea;background:#fff;box-shadow:0 0 0 4px rgba(102,126,234,.1)}
.btn-row{display:flex;gap:12px;margin-top:8px}
.btn-submit{flex:1;padding:13px;background:linear-gradient(135deg,#667eea,#764ba2);
  border:none;border-radius:11px;color:#fff;font-size:14px;font-weight:700;cursor:pointer;
  font-family:'Inter',sans-serif;box-shadow:0 6px 18px rgba(102,126,234,.35);transition:all .2s}
.btn-submit:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(102,126,234,.5)}
.btn-back{padding:13px 20px;background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:11px;
  color:#64748b;font-size:14px;font-weight:600;text-decoration:none;
  display:inline-flex;align-items:center;gap:7px;transition:all .2s}
.btn-back:hover{background:#f1f5f9;color:#334155}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sb-co">S4 Limited</div><div class="sb-tag">LeaveFlow &middot; Employee</div></div>
  </div>
  <div class="sb-user">
    <div class="sb-av">{{ employee.name|first }}</div>
    <div><div class="sb-un">{{ employee.name }}</div><div class="sb-ud">{{ employee.department }}</div></div>
  </div>
  <div class="sb-nav">
    <div class="sb-lbl">Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="sb-a"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}"        class="sb-a on"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <a href="{% url 'attendance' %}"         class="sb-a"><i class="fas fa-chart-bar"></i>Attendance</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="form-wrap">
    <div class="pg-title">Apply for Leave</div>
    <div class="pg-sub">S4 Limited &mdash; Submit your leave request for approval</div>
    <div class="bal-info">
      <i class="fas fa-info-circle"></i>
      You have <strong style="margin:0 4px">{{ employee.leave_balance }} days</strong> of leave balance remaining.
    </div>
    <div class="form-card">
      <form method="POST">
        {% csrf_token %}
        <div class="section-hd">Select Leave Type</div>
        <div class="lt-grid">
          <label class="lt-opt"><input type="radio" name="leave_type" value="CASUAL" checked>
            <div class="lt-card"><div class="lt-ic li1"><i class="fas fa-coffee"></i></div>
            <div><div class="lt-nm">Casual Leave</div><div class="lt-sb">Personal errands</div></div></div></label>
          <label class="lt-opt"><input type="radio" name="leave_type" value="SICK">
            <div class="lt-card"><div class="lt-ic li2"><i class="fas fa-heartbeat"></i></div>
            <div><div class="lt-nm">Sick Leave</div><div class="lt-sb">Health &amp; medical</div></div></div></label>
          <label class="lt-opt"><input type="radio" name="leave_type" value="ANNUAL">
            <div class="lt-card"><div class="lt-ic li3"><i class="fas fa-umbrella-beach"></i></div>
            <div><div class="lt-nm">Annual Leave</div><div class="lt-sb">Vacation &amp; holiday</div></div></div></label>
          <label class="lt-opt"><input type="radio" name="leave_type" value="EMERGENCY">
            <div class="lt-card"><div class="lt-ic li4"><i class="fas fa-exclamation-triangle"></i></div>
            <div><div class="lt-nm">Emergency</div><div class="lt-sb">Urgent situation</div></div></div></label>
        </div>
        <div class="section-hd">Leave Duration</div>
        <div class="date-row">
          <div><label class="field-lbl"><i class="fas fa-calendar-day"></i>Start Date</label>
            <input type="date" name="start" class="form-input" required></div>
          <div><label class="field-lbl"><i class="fas fa-calendar-day"></i>End Date</label>
            <input type="date" name="end" class="form-input" required></div>
        </div>
        <div class="section-hd">Details</div>
        <div class="field-group">
          <label class="field-lbl"><i class="fas fa-comment-alt"></i>Reason</label>
          <textarea name="reason" class="form-input" rows="4" placeholder="Describe your reason..." required style="resize:vertical"></textarea>
        </div>
        <div class="btn-row">
          <a href="{% url 'employee_dashboard' %}" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
          <button type="submit" class="btn-submit"><i class="fas fa-paper-plane" style="margin-right:8px"></i>Submit Leave Request</button>
        </div>
      </form>
    </div>
  </div>
</div>
</body>
</html>
""")
print("  employees/templates/apply_leave.html")

# ── Patch settings.py ─────────────────────────────────────────────────────────
settings_path = 'leave_management/settings.py'
with open(settings_path,'r',encoding='utf-8') as f:
    s = f.read()

changed = False
if "'employees'" not in s and '"employees"' not in s:
    s = s.replace("'django.contrib.staticfiles',",
                  "'django.contrib.staticfiles',\n    'employees',")
    changed = True

if 'STATIC_ROOT' not in s:
    s += "\nSTATIC_ROOT = BASE_DIR / 'staticfiles'\n"
    changed = True

if changed:
    with open(settings_path,'w',encoding='utf-8') as f:
        f.write(s)
    print("  leave_management/settings.py (patched)")

print()
print("=" * 55)
print("  ALL FILES CREATED SUCCESSFULLY!")
print("=" * 55)
print()
print("Now run:")
print("  python manage.py makemigrations")
print("  python manage.py migrate")
print("  python manage.py collectstatic --noinput")
print("  python manage.py runserver")
print()
print("URLs:")
print("  http://127.0.0.1:8000/         -> Login")
print("  http://127.0.0.1:8000/admin/   -> Admin Panel (S4 Limited)")
