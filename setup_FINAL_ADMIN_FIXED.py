import os
import sys

# Safety check
if not os.path.exists('manage.py'):
    print("ERROR: manage.py not found! Run this script from inside your leave_management folder.")
    sys.exit(1)

print("Found manage.py - running setup in correct folder...")
os.makedirs('employees/templates', exist_ok=True)

files = {}

# ─── MODELS ───────────────────────────────────────────────────────────────────
files['employees/models.py'] = """from django.db import models
from django.utils import timezone

class Employee(models.Model):
    ROLE_CHOICES = [('EMPLOYEE', 'Employee'), ('MANAGER', 'Manager')]
    DEPT_CHOICES = [
        ('IT', 'IT'), ('HR', 'HR'), ('Finance', 'Finance'),
        ('Operations', 'Operations'), ('Marketing', 'Marketing'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.CharField(max_length=20, choices=DEPT_CHOICES, default='IT')
    attendance_percent = models.FloatField(default=95.0)
    leave_balance = models.IntegerField(default=20)
    joined_date = models.DateField(default=timezone.now)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')]
    LEAVE_TYPES = [
        ('SICK', 'Sick Leave'), ('CASUAL', 'Casual Leave'),
        ('ANNUAL', 'Annual Leave'), ('EMERGENCY', 'Emergency'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPES, default='CASUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_on = models.DateField(default=timezone.now)

    def days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return self.employee.name + ' - ' + self.status
"""

# ─── ADMIN  (fixed: no f-strings in list_display callables) ──────────────────
files['employees/admin.py'] = """from django.contrib import admin
from django.utils.html import format_html
from .models import Employee, LeaveRequest

admin.site.site_header  = 'LeaveFlow Administration'
admin.site.site_title   = 'LeaveFlow Admin'
admin.site.index_title  = 'Leave Management Control Panel'

# ── custom CSS injected via Media ────────────────────────────────────────────
class AdminGlobalCSS(admin.ModelAdmin):
    class Media:
        css = {'all': []}   # placeholder so the class exists

# ── Employee Admin ────────────────────────────────────────────────────────────
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'role_badge', 'department',
                     'attendance_bar', 'leave_balance', 'joined_date')
    list_filter   = ('role', 'department')
    search_fields = ('name', 'email')
    ordering      = ('name',)

    # ── attendance bar ──────────────────────────────────────────────────────
    @admin.display(description='Attendance %')
    def attendance_bar(self, obj):
        pct   = obj.attendance_percent
        color = '#10b981' if pct >= 90 else ('#f59e0b' if pct >= 75 else '#ef4444')
        label = 'Excellent' if pct >= 90 else ('Average' if pct >= 75 else 'Poor')
        html = (
            '<div style="min-width:160px">'
            '<div style="display:flex;justify-content:space-between;'
            'font-size:12px;margin-bottom:3px">'
            '<span style="font-weight:600;color:{color}">{pct}%</span>'
            '<span style="color:#888">{label}</span>'
            '</div>'
            '<div style="background:#e5e7eb;border-radius:4px;height:7px">'
            '<div style="width:{pct}%;background:{color};'
            'border-radius:4px;height:7px"></div>'
            '</div></div>'
        ).format(color=color, pct=pct, label=label)
        return format_html(html)

    # ── role badge ──────────────────────────────────────────────────────────
    @admin.display(description='Role')
    def role_badge(self, obj):
        if obj.role == 'MANAGER':
            return format_html(
                '<span style="background:#f3e8ff;color:#7c3aed;padding:3px 10px;'
                'border-radius:12px;font-size:11px;font-weight:600">Manager</span>'
            )
        return format_html(
            '<span style="background:#dbeafe;color:#1d4ed8;padding:3px 10px;'
            'border-radius:12px;font-size:11px;font-weight:600">Employee</span>'
        )

    class Media:
        css = {'all': []}


# ── Leave Request Admin ───────────────────────────────────────────────────────
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee_name', 'leave_type', 'start_date', 'end_date',
                     'duration', 'status_badge', 'applied_on')
    list_filter   = ('status', 'leave_type', 'employee__department')
    search_fields = ('employee__name', 'reason')
    ordering      = ('-applied_on',)
    actions       = ['approve_leaves', 'reject_leaves']

    @admin.display(description='Employee')
    def employee_name(self, obj):
        return obj.employee.name

    @admin.display(description='Duration')
    def duration(self, obj):
        d = obj.days()
        return format_html(
            '<span style="font-weight:600">{}</span> day{}',
            d, '' if d == 1 else 's'
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        styles = {
            'PENDING':  ('background:#fef3c7;color:#d97706', 'Pending'),
            'APPROVED': ('background:#d1fae5;color:#065f46', 'Approved'),
            'REJECTED': ('background:#fee2e2;color:#991b1b', 'Rejected'),
        }
        style, text = styles.get(obj.status, ('', obj.status))
        return format_html(
            '<span style="{};padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:600">{}</span>',
            style, text
        )

    @admin.action(description='Approve selected leave requests')
    def approve_leaves(self, request, queryset):
        queryset.update(status='APPROVED')
        self.message_user(request, 'Selected leave requests have been approved.')

    @admin.action(description='Reject selected leave requests')
    def reject_leaves(self, request, queryset):
        queryset.update(status='REJECTED')
        self.message_user(request, 'Selected leave requests have been rejected.')

    class Media:
        css = {'all': []}
"""

# ─── VIEWS ────────────────────────────────────────────────────────────────────
files['employees/views.py'] = """from django.shortcuts import render, redirect
from .models import Employee, LeaveRequest

def login_view(request):
    if request.method == 'POST':
        try:
            user = Employee.objects.get(
                email=request.POST['email'],
                password=request.POST['password']
            )
            request.session['user_id'] = user.id
            request.session['role']    = user.role
            request.session['name']    = user.name
            if user.role == 'MANAGER':
                return redirect('manager_dashboard')
            return redirect('employee_dashboard')
        except Employee.DoesNotExist:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def employee_dashboard(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    uid      = request.session.get('user_id')
    employee = Employee.objects.get(id=uid)
    leaves   = LeaveRequest.objects.filter(employee_id=uid)
    approved = leaves.filter(status='APPROVED').count()
    pending  = leaves.filter(status='PENDING').count()
    rejected = leaves.filter(status='REJECTED').count()
    att_gap  = round(100 - employee.attendance_percent, 1)
    return render(request, 'employee_dashboard.html', {
        'employee':      employee,
        'leaves':        leaves,
        'approved':      approved,
        'pending':       pending,
        'rejected':      rejected,
        'attendance_gap': att_gap,
    })

def manager_dashboard(request):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leaves   = LeaveRequest.objects.all().select_related('employee')
    employees = Employee.objects.filter(role='EMPLOYEE')
    return render(request, 'manager_dashboard.html', {
        'leaves':          leaves,
        'employees':       employees,
        'pending_count':   leaves.filter(status='PENDING').count(),
        'approved_count':  leaves.filter(status='APPROVED').count(),
        'rejected_count':  leaves.filter(status='REJECTED').count(),
        'total_emp':       employees.count(),
        'name':            request.session.get('name'),
    })

def apply_leave(request):
    uid = request.session.get('user_id')
    if not uid:
        return redirect('login')
    if request.method == 'POST':
        LeaveRequest.objects.create(
            employee_id=uid,
            leave_type=request.POST.get('leave_type', 'CASUAL'),
            start_date=request.POST['start'],
            end_date=request.POST['end'],
            reason=request.POST['reason'],
        )
        role = request.session.get('role')
        return redirect('manager_dashboard' if role == 'MANAGER' else 'employee_dashboard')
    return render(request, 'apply_leave.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')
"""

# ─── URLs ─────────────────────────────────────────────────────────────────────
files['employees/urls.py'] = """from django.urls import path
from . import views

urlpatterns = [
    path('',                               views.login_view,          name='login'),
    path('employee/',                      views.employee_dashboard,   name='employee_dashboard'),
    path('manager/',                       views.manager_dashboard,    name='manager_dashboard'),
    path('apply/',                         views.apply_leave,          name='apply_leave'),
    path('logout/',                        views.logout_view,          name='logout'),
]
"""

files['leave_management/urls.py'] = """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',       include('employees.urls')),
]
"""

# ─── TEMPLATES ────────────────────────────────────────────────────────────────

# LOGIN
files['employees/templates/login.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Sign In</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;display:flex;font-family:'Segoe UI',sans-serif}
.left{flex:1;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px 50px;position:relative;overflow:hidden}
.left::before{content:'';position:absolute;width:400px;height:400px;background:rgba(102,126,234,.15);border-radius:50%;top:-100px;right:-100px}
.left::after{content:'';position:absolute;width:300px;height:300px;background:rgba(240,147,251,.1);border-radius:50%;bottom:-80px;left:-80px}
.logo-big{width:90px;height:90px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:26px;display:flex;align-items:center;justify-content:center;box-shadow:0 20px 50px rgba(102,126,234,.5);margin-bottom:28px;z-index:1}
.logo-big i{font-size:44px;color:white}
.brand-name{font-size:36px;font-weight:800;color:white;z-index:1;letter-spacing:-1px}
.brand-tagline{color:rgba(255,255,255,.4);font-size:15px;margin-top:8px;z-index:1;text-align:center;max-width:260px;line-height:1.5}
.features{margin-top:44px;z-index:1;width:100%;max-width:320px}
.feat-item{display:flex;align-items:center;gap:14px;padding:14px 18px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);border-radius:13px;margin-bottom:10px}
.feat-icon{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.feat-icon i{color:white;font-size:15px}
.feat-text{color:rgba(255,255,255,.75);font-size:13px;font-weight:500}
.right{width:480px;background:white;display:flex;flex-direction:column;justify-content:center;padding:60px 52px}
.sign-title{font-size:26px;font-weight:800;color:#1a1d2e;margin-bottom:6px}
.sign-sub{color:#8a8ea8;font-size:14px;margin-bottom:36px}
.field-label{font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:7px;display:block}
.input-wrap{position:relative;margin-bottom:18px}
.input-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#aaa;font-size:14px}
.form-control{border:1.5px solid #e8eaf0;border-radius:12px;padding:12px 14px 12px 40px;font-size:14px;width:100%;transition:all .2s;background:#fafbff;color:#3a3d4e}
.form-control:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.12);background:white}
.btn-login{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;padding:14px;font-size:15px;font-weight:600;color:white;width:100%;cursor:pointer;transition:all .3s;box-shadow:0 8px 20px rgba(102,126,234,.35)}
.btn-login:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(102,126,234,.5)}
.err{background:#fff0f0;border:1px solid #ffcdd2;border-radius:11px;color:#e53935;font-size:13px;padding:11px 15px;margin-bottom:20px;display:flex;align-items:center;gap:8px}
.footer-note{color:#c0c4d4;font-size:11px;text-align:center;margin-top:28px}
@media(max-width:768px){.left{display:none}.right{width:100%;padding:40px 30px}}
</style>
</head>
<body>
<div class="left">
  <div class="logo-big"><i class="fas fa-calendar-check"></i></div>
  <div class="brand-name">LeaveFlow</div>
  <div class="brand-tagline">Smart leave management for modern organisations</div>
  <div class="features">
    <div class="feat-item"><div class="feat-icon"><i class="fas fa-file-alt"></i></div><div class="feat-text">Apply and track leave requests instantly</div></div>
    <div class="feat-item"><div class="feat-icon"><i class="fas fa-chart-line"></i></div><div class="feat-text">Real-time attendance percentage tracking</div></div>
    <div class="feat-item"><div class="feat-icon"><i class="fas fa-shield-alt"></i></div><div class="feat-text">Admin approvals with full audit trail</div></div>
  </div>
</div>
<div class="right">
  <div class="sign-title">Welcome back</div>
  <div class="sign-sub">Sign in to your LeaveFlow account</div>
  {% if error %}<div class="err"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
  <form method="POST">{% csrf_token %}
    <label class="field-label">Email Address</label>
    <div class="input-wrap"><i class="input-icon fas fa-envelope"></i><input type="email" name="email" class="form-control" placeholder="you@company.com" required></div>
    <label class="field-label">Password</label>
    <div class="input-wrap"><i class="input-icon fas fa-lock"></i><input type="password" name="password" class="form-control" placeholder="Your password" required></div>
    <button type="submit" class="btn-login"><i class="fas fa-sign-in-alt me-2"></i>Sign In to LeaveFlow</button>
  </form>
  <div class="footer-note">© 2026 LeaveFlow &middot; All rights reserved</div>
</div>
</body>
</html>
"""

# EMPLOYEE DASHBOARD
files['employees/templates/employee_dashboard.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - My Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box}body{background:#f0f2f8;font-family:'Segoe UI',sans-serif;margin:0}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:240px;background:linear-gradient(180deg,#0f0c29,#302b63);z-index:100;box-shadow:4px 0 24px rgba(0,0,0,.35);display:flex;flex-direction:column}
.sl{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:12px}
.lb{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:11px;display:flex;align-items:center;justify-content:center}
.lb i{color:white;font-size:17px}
.lt{color:white;font-size:17px;font-weight:700}.ls{color:rgba(255,255,255,.35);font-size:10px}
.sn{padding:14px 10px;flex:1}
.nl{color:rgba(255,255,255,.25);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 14px 5px}
.ni{display:flex;align-items:center;gap:11px;padding:10px 14px;border-radius:9px;color:rgba(255,255,255,.55);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all .2s}
.ni:hover,.ni.act{background:rgba(102,126,234,.2);color:white}
.ni i{width:17px;text-align:center;font-size:13px}
.sf{padding:14px 10px;border-top:1px solid rgba(255,255,255,.08)}
.uc{display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:9px;background:rgba(255,255,255,.06)}
.av{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-size:14px;font-weight:700;flex-shrink:0}
.un{color:white;font-size:12px;font-weight:600}.ur{color:rgba(255,255,255,.4);font-size:10px}
.main{margin-left:240px;padding:28px 32px;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:26px}
.pt{font-size:22px;font-weight:800;color:#1a1d2e}.ps{font-size:13px;color:#8a8ea8;margin-top:3px}
.btn-apply{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:11px;padding:11px 20px;font-size:13px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:7px;box-shadow:0 6px 16px rgba(102,126,234,.35);transition:all .2s}
.btn-apply:hover{transform:translateY(-2px);color:white;box-shadow:0 10px 24px rgba(102,126,234,.5)}
.chips{display:flex;gap:10px;margin-bottom:22px;flex-wrap:wrap}
.chip{background:white;border-radius:8px;padding:7px 13px;font-size:12px;color:#5a5f7a;display:flex;align-items:center;gap:6px;box-shadow:0 1px 6px rgba(0,0,0,.06)}
.chip i{color:#667eea}
.sgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:22px}
.sc{background:white;border-radius:15px;padding:20px 22px;box-shadow:0 2px 10px rgba(0,0,0,.05);position:relative;overflow:hidden}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.c1::before{background:linear-gradient(90deg,#667eea,#764ba2)}
.c2::before{background:linear-gradient(90deg,#11998e,#38ef7d)}
.c3::before{background:linear-gradient(90deg,#f7971e,#ffd200)}
.c4::before{background:linear-gradient(90deg,#eb3349,#f45c43)}
.sn2{font-size:30px;font-weight:800;color:#1a1d2e}.sl2{font-size:11px;color:#8a8ea8;margin-top:3px;font-weight:500}
.si{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:36px;opacity:.07}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
.cb{background:white;border-radius:15px;padding:22px 24px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
.ct{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.ct i{color:#667eea}
.an{font-size:52px;font-weight:800;background:linear-gradient(135deg,#11998e,#38ef7d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center}
.al{font-size:12px;color:#8a8ea8;text-align:center;margin-bottom:18px}
.pl{display:flex;justify-content:space-between;font-size:11px;color:#8a8ea8;margin-bottom:4px}
.progress{height:7px;border-radius:4px;background:#f0f2f8;margin-bottom:13px}
.progress-bar{border-radius:4px}
table{width:100%;border-collapse:collapse}
thead th{font-size:11px;font-weight:600;color:#8a8ea8;text-transform:uppercase;letter-spacing:.05em;padding:10px 12px;border-bottom:1px solid #f0f2f8}
tbody td{padding:12px 12px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9fe;vertical-align:middle}
tbody tr:hover td{background:#fafbff}
.bs{display:inline-block;padding:4px 10px;border-radius:18px;font-size:11px;font-weight:600}
.bp{background:#fff8e1;color:#f59e0b}.ba{background:#e8faf0;color:#10b981}.br{background:#fee8e8;color:#ef4444}
.ltb{font-size:10px;padding:3px 8px;border-radius:5px;font-weight:600;background:#eef0ff;color:#667eea}
.note{background:#f0f4ff;border:1px solid #dce4ff;border-radius:11px;padding:12px 16px;font-size:13px;color:#4a5568;margin-bottom:20px;display:flex;align-items:center;gap:10px}
.note i{color:#667eea;font-size:16px}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sl"><div class="lb"><i class="fas fa-calendar-check"></i></div><div><div class="lt">LeaveFlow</div><div class="ls">Leave Management</div></div></div>
  <div class="sn">
    <div class="nl">Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="ni act"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="ni"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="nl">Account</div>
    <a href="{% url 'logout' %}" class="ni"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sf"><div class="uc"><div class="av">{{ employee.name|first }}</div><div><div class="un">{{ employee.name }}</div><div class="ur">{{ employee.department }}</div></div></div></div>
</div>
<div class="main">
  <div class="topbar">
    <div><div class="pt">Welcome back, {{ employee.name }} &#x1F44B;</div><div class="ps">Here's your leave overview for this year</div></div>
    <a href="{% url 'apply_leave' %}" class="btn-apply"><i class="fas fa-plus"></i>Apply for Leave</a>
  </div>
  <div class="chips">
    <div class="chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="chip"><i class="fas fa-suitcase"></i>{{ employee.leave_balance }} days balance left</div>
    <div class="chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
  </div>
  <div class="note"><i class="fas fa-info-circle"></i>Leave requests are reviewed and approved by the admin. You can track your request status below.</div>
  <div class="sgrid">
    <div class="sc c1"><div class="sn2">{{ leaves.count }}</div><div class="sl2">Total Requests</div><i class="fas fa-file-alt si"></i></div>
    <div class="sc c2"><div class="sn2">{{ approved }}</div><div class="sl2">Approved</div><i class="fas fa-check-circle si"></i></div>
    <div class="sc c3"><div class="sn2">{{ pending }}</div><div class="sl2">Pending Review</div><i class="fas fa-clock si"></i></div>
    <div class="sc c4"><div class="sn2">{{ rejected }}</div><div class="sl2">Rejected</div><i class="fas fa-times-circle si"></i></div>
  </div>
  <div class="g2">
    <div class="cb">
      <div class="ct"><i class="fas fa-chart-line"></i>Attendance Overview</div>
      <div class="an">{{ employee.attendance_percent }}%</div>
      <div class="al">Overall Attendance Rate</div>
      <div class="pl"><span>Present</span><span>{{ employee.attendance_percent }}%</span></div>
      <div class="progress"><div class="progress-bar bg-success" style="width:{{ employee.attendance_percent }}%"></div></div>
      <div class="pl"><span>Absent / Leave taken</span><span>{{ attendance_gap }}%</span></div>
      <div class="progress"><div class="progress-bar bg-danger" style="width:{{ attendance_gap }}%"></div></div>
      <div class="pl"><span>Leave balance remaining</span><span>{{ employee.leave_balance }} / 20 days</span></div>
      <div class="progress"><div class="progress-bar" style="width:{{ employee.leave_balance }}%;background:linear-gradient(90deg,#667eea,#764ba2)"></div></div>
    </div>
    <div class="cb">
      <div class="ct"><i class="fas fa-chart-pie"></i>Leave Status Breakdown</div>
      <canvas id="leaveChart" height="220"></canvas>
    </div>
  </div>
  <div class="cb">
    <div class="ct"><i class="fas fa-history"></i>Leave Request History</div>
    <table>
      <thead><tr><th>#</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Reason</th><th>Applied On</th><th>Status</th></tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td>{{ forloop.counter }}</td>
        <td><span class="ltb">{{ leave.leave_type }}</span></td>
        <td>{{ leave.start_date }}</td>
        <td>{{ leave.end_date }}</td>
        <td><strong>{{ leave.days }}</strong></td>
        <td>{{ leave.reason }}</td>
        <td>{{ leave.applied_on }}</td>
        <td>{% if leave.status == 'APPROVED' %}<span class="bs ba"><i class="fas fa-check me-1"></i>Approved</span>{% elif leave.status == 'REJECTED' %}<span class="bs br"><i class="fas fa-times me-1"></i>Rejected</span>{% else %}<span class="bs bp"><i class="fas fa-clock me-1"></i>Pending</span>{% endif %}</td>
      </tr>
      {% empty %}
      <tr><td colspan="8" class="text-center py-4" style="color:#aaa">No requests yet. Click Apply for Leave to get started.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<script>
new Chart(document.getElementById('leaveChart').getContext('2d'),{
  type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved }},{{ pending }},{{ rejected }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:8}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:18,font:{size:12}}}},cutout:'65%'}
});
</script>
</body>
</html>
"""

# MANAGER DASHBOARD
files['employees/templates/manager_dashboard.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Manager Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box}body{background:#f0f2f8;font-family:'Segoe UI',sans-serif;margin:0}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:240px;background:linear-gradient(180deg,#1a0533,#2d1b69);z-index:100;box-shadow:4px 0 24px rgba(0,0,0,.35);display:flex;flex-direction:column}
.sl{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:12px}
.lb{width:40px;height:40px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:11px;display:flex;align-items:center;justify-content:center}
.lb i{color:white;font-size:17px}
.lt{color:white;font-size:17px;font-weight:700}.ls{color:rgba(255,255,255,.35);font-size:10px}
.sn{padding:14px 10px;flex:1}
.nl{color:rgba(255,255,255,.25);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 14px 5px}
.ni{display:flex;align-items:center;gap:11px;padding:10px 14px;border-radius:9px;color:rgba(255,255,255,.55);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all .2s}
.ni:hover,.ni.act{background:rgba(240,147,251,.15);color:white}
.ni i{width:17px;text-align:center;font-size:13px}
.sf{padding:14px 10px;border-top:1px solid rgba(255,255,255,.08)}
.uc{display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:9px;background:rgba(255,255,255,.06)}
.av{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#f093fb,#f5576c);display:flex;align-items:center;justify-content:center;color:white;font-size:14px;font-weight:700;flex-shrink:0}
.un{color:white;font-size:12px;font-weight:600}.ur{color:rgba(255,255,255,.4);font-size:10px}
.main{margin-left:240px;padding:28px 32px;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:26px}
.pt{font-size:22px;font-weight:800;color:#1a1d2e}.ps{font-size:13px;color:#8a8ea8;margin-top:3px}
.btn-apply{background:linear-gradient(135deg,#f093fb,#f5576c);color:white;border:none;border-radius:11px;padding:11px 20px;font-size:13px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:7px;box-shadow:0 6px 16px rgba(240,147,251,.35);transition:all .2s}
.btn-apply:hover{transform:translateY(-2px);color:white;box-shadow:0 10px 24px rgba(240,147,251,.5)}
.sgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:22px}
.sc{background:white;border-radius:15px;padding:20px 22px;box-shadow:0 2px 10px rgba(0,0,0,.05);position:relative;overflow:hidden}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.c1::before{background:linear-gradient(90deg,#f093fb,#f5576c)}
.c2::before{background:linear-gradient(90deg,#667eea,#764ba2)}
.c3::before{background:linear-gradient(90deg,#11998e,#38ef7d)}
.c4::before{background:linear-gradient(90deg,#f7971e,#ffd200)}
.sn2{font-size:30px;font-weight:800;color:#1a1d2e}.sl2{font-size:11px;color:#8a8ea8;margin-top:3px;font-weight:500}
.si{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:36px;opacity:.07}
.g2{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.cb{background:white;border-radius:15px;padding:22px 24px;box-shadow:0 2px 10px rgba(0,0,0,.05);margin-bottom:20px}
.ct{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.ct i{color:#f093fb}
table{width:100%;border-collapse:collapse}
thead th{font-size:11px;font-weight:600;color:#8a8ea8;text-transform:uppercase;letter-spacing:.05em;padding:10px 12px;border-bottom:1px solid #f0f2f8}
tbody td{padding:12px 12px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9fe;vertical-align:middle}
tbody tr:hover td{background:#fafbff}
.bs{display:inline-block;padding:4px 10px;border-radius:18px;font-size:11px;font-weight:600}
.bp{background:#fff8e1;color:#f59e0b}.ba{background:#e8faf0;color:#10b981}.br{background:#fee8e8;color:#ef4444}
.att-bar{height:6px;border-radius:3px;background:#f0f2f8;margin-top:5px}
.att-fill{height:100%;border-radius:3px}
.ea{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#667eea,#764ba2);display:inline-flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:12px;margin-right:8px;flex-shrink:0}
.note{background:#f5f0ff;border:1px solid #e0d4ff;border-radius:11px;padding:12px 16px;font-size:13px;color:#4a5568;margin-bottom:20px;display:flex;align-items:center;gap:10px}
.note i{color:#7c3aed;font-size:16px}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sl"><div class="lb"><i class="fas fa-shield-alt"></i></div><div><div class="lt">LeaveFlow</div><div class="ls">Manager Panel</div></div></div>
  <div class="sn">
    <div class="nl">Menu</div>
    <a href="{% url 'manager_dashboard' %}" class="ni act"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="ni"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="nl">Account</div>
    <a href="{% url 'logout' %}" class="ni"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sf"><div class="uc"><div class="av">M</div><div><div class="un">{{ name }}</div><div class="ur">Manager</div></div></div></div>
</div>
<div class="main">
  <div class="topbar">
    <div><div class="pt">Manager Dashboard &#x1F6E1;&#xFE0F;</div><div class="ps">Monitor team attendance and leave requests</div></div>
    <a href="{% url 'apply_leave' %}" class="btn-apply"><i class="fas fa-plus"></i>Apply for Leave</a>
  </div>
  <div class="note"><i class="fas fa-info-circle"></i>All leave approvals are handled through the <strong>&nbsp;Admin Portal</strong>. This dashboard is for monitoring only.</div>
  <div class="sgrid">
    <div class="sc c1"><div class="sn2">{{ total_emp }}</div><div class="sl2">Total Employees</div><i class="fas fa-users si"></i></div>
    <div class="sc c2"><div class="sn2">{{ pending_count }}</div><div class="sl2">Pending Approvals</div><i class="fas fa-hourglass-half si"></i></div>
    <div class="sc c3"><div class="sn2">{{ approved_count }}</div><div class="sl2">Approved</div><i class="fas fa-check-double si"></i></div>
    <div class="sc c4"><div class="sn2">{{ rejected_count }}</div><div class="sl2">Rejected</div><i class="fas fa-times si"></i></div>
  </div>
  <div class="g2">
    <div class="cb" style="margin-bottom:0">
      <div class="ct"><i class="fas fa-list-check"></i>All Leave Requests (Read-only — approve via Admin)</div>
      <table>
        <thead><tr><th>Employee</th><th>Dept</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Status</th></tr></thead>
        <tbody>
        {% for leave in leaves %}
        <tr>
          <td><div style="display:flex;align-items:center"><span class="ea">{{ leave.employee.name|first }}</span><div><div style="font-weight:600;font-size:13px">{{ leave.employee.name }}</div></div></div></td>
          <td style="font-size:12px;color:#888">{{ leave.employee.department }}</td>
          <td><span style="font-size:10px;background:#eef0ff;color:#667eea;padding:3px 7px;border-radius:5px;font-weight:600">{{ leave.leave_type }}</span></td>
          <td>{{ leave.start_date }}</td>
          <td>{{ leave.end_date }}</td>
          <td><strong>{{ leave.days }}</strong></td>
          <td>{% if leave.status == 'APPROVED' %}<span class="bs ba">Approved</span>{% elif leave.status == 'REJECTED' %}<span class="bs br">Rejected</span>{% else %}<span class="bs bp">Pending</span>{% endif %}</td>
        </tr>
        {% empty %}
        <tr><td colspan="7" class="text-center py-4" style="color:#aaa">No leave requests found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="cb" style="margin-bottom:0">
      <div class="ct"><i class="fas fa-chart-pie"></i>Leave Overview</div>
      <canvas id="leaveChart" height="240"></canvas>
    </div>
  </div>
  <div class="cb">
    <div class="ct"><i class="fas fa-users"></i>Employee Attendance Tracker</div>
    <table>
      <thead><tr><th>Employee</th><th>Department</th><th>Email</th><th>Balance</th><th>Attendance %</th><th>Rating</th></tr></thead>
      <tbody>
      {% for emp in employees %}
      <tr>
        <td><div style="display:flex;align-items:center"><span class="ea">{{ emp.name|first }}</span><strong>{{ emp.name }}</strong></div></td>
        <td>{{ emp.department }}</td>
        <td style="font-size:12px;color:#888">{{ emp.email }}</td>
        <td><strong>{{ emp.leave_balance }}</strong> days</td>
        <td>
          <strong>{{ emp.attendance_percent }}%</strong>
          <div class="att-bar">
            <div class="att-fill" style="width:{{ emp.attendance_percent }}%;background:{% if emp.attendance_percent >= 90 %}#10b981{% elif emp.attendance_percent >= 75 %}#f59e0b{% else %}#ef4444{% endif %}"></div>
          </div>
        </td>
        <td>
          {% if emp.attendance_percent >= 90 %}<span style="color:#10b981;font-size:12px;font-weight:600"><i class="fas fa-circle-check me-1"></i>Excellent</span>
          {% elif emp.attendance_percent >= 75 %}<span style="color:#f59e0b;font-size:12px;font-weight:600"><i class="fas fa-exclamation-circle me-1"></i>Average</span>
          {% else %}<span style="color:#ef4444;font-size:12px;font-weight:600"><i class="fas fa-times-circle me-1"></i>Poor</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="6" class="text-center py-4" style="color:#aaa">No employees found.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<script>
new Chart(document.getElementById('leaveChart').getContext('2d'),{
  type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved_count }},{{ pending_count }},{{ rejected_count }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:8}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:18,font:{size:12}}}},cutout:'65%'}
});
</script>
</body>
</html>
"""

# APPLY LEAVE
files['employees/templates/apply_leave.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Apply Leave</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box}body{background:#f0f2f8;font-family:'Segoe UI',sans-serif;margin:0}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:240px;background:linear-gradient(180deg,#0f0c29,#302b63);z-index:100;display:flex;flex-direction:column}
.sl{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:12px}
.lb{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:11px;display:flex;align-items:center;justify-content:center}
.lb i{color:white;font-size:17px}
.lt{color:white;font-size:17px;font-weight:700}.ls{color:rgba(255,255,255,.35);font-size:10px}
.sn{padding:14px 10px;flex:1}
.nl{color:rgba(255,255,255,.25);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 14px 5px}
.ni{display:flex;align-items:center;gap:11px;padding:10px 14px;border-radius:9px;color:rgba(255,255,255,.55);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all .2s}
.ni:hover,.ni.act{background:rgba(102,126,234,.2);color:white}
.ni i{width:17px;text-align:center;font-size:13px}
.main{margin-left:240px;padding:40px 70px;min-height:100vh}
.pt{font-size:22px;font-weight:800;color:#1a1d2e;margin-bottom:4px}
.ps{font-size:13px;color:#8a8ea8;margin-bottom:28px}
.fc{background:white;border-radius:18px;padding:36px 40px;box-shadow:0 4px 22px rgba(0,0,0,.07);max-width:580px}
.fg{margin-bottom:20px}
.fl{font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:7px;display:block}
.fl i{color:#667eea;margin-right:6px}
.form-control,.form-select{border:1.5px solid #e8eaf0;border-radius:11px;padding:12px 14px;font-size:14px;color:#3a3d4e;transition:all .2s;background:#fafbff;width:100%}
.form-control:focus,.form-select:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.1);background:white}
.dr{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.btn-sub{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:11px;padding:13px 28px;font-size:14px;font-weight:600;color:white;cursor:pointer;transition:all .2s;box-shadow:0 6px 16px rgba(102,126,234,.35)}
.btn-sub:hover{transform:translateY(-2px);box-shadow:0 10px 22px rgba(102,126,234,.5)}
.btn-back{background:#f0f2f8;border:none;border-radius:11px;padding:13px 22px;font-size:14px;font-weight:600;color:#5a5f7a;text-decoration:none;display:inline-flex;align-items:center;gap:6px;margin-right:10px;transition:all .2s}
.btn-back:hover{background:#e4e7f0;color:#3a3d4e}
.note{background:#f0f4ff;border:1px solid #dce4ff;border-radius:11px;padding:12px 16px;font-size:13px;color:#4a5568;margin-bottom:24px;display:flex;align-items:center;gap:10px}
.note i{color:#667eea}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sl"><div class="lb"><i class="fas fa-calendar-check"></i></div><div><div class="lt">LeaveFlow</div><div class="ls">Leave Management</div></div></div>
  <div class="sn">
    <div class="nl">Menu</div>
    <a href="javascript:history.back()" class="ni"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="ni act"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="nl">Account</div>
    <a href="{% url 'logout' %}" class="ni"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
</div>
<div class="main">
  <div class="pt">Apply for Leave</div>
  <div class="ps">Fill in the details below — your request will be reviewed by the admin</div>
  <div class="note"><i class="fas fa-info-circle"></i>Your request will be submitted for admin approval. You can track the status on your dashboard.</div>
  <div class="fc">
    <form method="POST">{% csrf_token %}
      <div class="fg">
        <label class="fl"><i class="fas fa-tag"></i>Leave Type</label>
        <select name="leave_type" class="form-select" required>
          <option value="CASUAL">Casual Leave</option>
          <option value="SICK">Sick Leave</option>
          <option value="ANNUAL">Annual Leave</option>
          <option value="EMERGENCY">Emergency Leave</option>
        </select>
      </div>
      <div class="dr">
        <div class="fg"><label class="fl"><i class="fas fa-calendar-day"></i>Start Date</label><input type="date" name="start" class="form-control" required></div>
        <div class="fg"><label class="fl"><i class="fas fa-calendar-day"></i>End Date</label><input type="date" name="end" class="form-control" required></div>
      </div>
      <div class="fg">
        <label class="fl"><i class="fas fa-comment-alt"></i>Reason</label>
        <textarea name="reason" class="form-control" rows="4" placeholder="Briefly describe the reason for your leave..." required></textarea>
      </div>
      <div style="margin-top:8px">
        <a href="javascript:history.back()" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
        <button type="submit" class="btn-sub"><i class="fas fa-paper-plane me-2"></i>Submit Request</button>
      </div>
    </form>
  </div>
</div>
</body>
</html>
"""

# Write all files
for filepath, content in files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Created:', filepath)

# Patch settings.py
settings_path = 'leave_management/settings.py'
if os.path.exists(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = f.read()
    if "'employees'" not in settings and '"employees"' not in settings:
        settings = settings.replace(
            "'django.contrib.staticfiles',",
            "'django.contrib.staticfiles',\n    'employees',"
        )
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(settings)
        print("Patched: leave_management/settings.py (added 'employees' to INSTALLED_APPS)")
    else:
        print("OK: 'employees' already in INSTALLED_APPS")

print()
print("=" * 55)
print("  ALL FILES CREATED SUCCESSFULLY!")
print("=" * 55)
print()
print("Next steps — run these commands:")
print("  python manage.py makemigrations")
print("  python manage.py migrate")
print("  python manage.py runserver")
print()
print("Then open: http://127.0.0.1:8000/admin/")
print("  -> Approve/Reject leaves from Leave Requests section")
print("Then open: http://127.0.0.1:8000/")
print("  -> Login as Employee or Manager")
