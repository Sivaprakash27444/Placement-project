"""
LeaveFlow - Admin Fix Setup Script
====================================
- Removes Approve/Reject buttons from Manager Dashboard (view only)
- All leave approvals happen ONLY through /admin/
- Custom beautiful Admin portal
- Run from same folder as manage.py
"""

import os
import sys

if not os.path.exists('manage.py'):
    print("ERROR: Run this from the same folder as manage.py")
    sys.exit(1)

print("Found manage.py - running setup...")
os.makedirs('employees/templates', exist_ok=True)
os.makedirs('employees/templatetags', exist_ok=True)

# ─────────────────────────────────────────────
# models.py
# ─────────────────────────────────────────────
with open('employees/models.py', 'w', encoding='utf-8') as f:
    f.write("""from django.db import models
from django.utils import timezone

class Employee(models.Model):
    ROLE_CHOICES = [('EMPLOYEE','Employee'),('MANAGER','Manager')]
    DEPT_CHOICES = [('IT','IT'),('HR','HR'),('Finance','Finance'),('Operations','Operations'),('Marketing','Marketing')]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.CharField(max_length=20, choices=DEPT_CHOICES, default='IT')
    attendance_percent = models.FloatField(default=95.0)
    leave_balance = models.IntegerField(default=20)
    joined_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.role})"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected')]
    LEAVE_TYPES = [('SICK','Sick Leave'),('CASUAL','Casual Leave'),('ANNUAL','Annual Leave'),('EMERGENCY','Emergency')]
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
        return f"{self.employee.name} | {self.leave_type} | {self.status}"
""")
print("Created: employees/models.py")

# ─────────────────────────────────────────────
# admin.py — Beautiful custom admin
# ─────────────────────────────────────────────
with open('employees/admin.py', 'w', encoding='utf-8') as f:
    f.write("""from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Employee, LeaveRequest

admin.site.site_header = "LeaveFlow Admin"
admin.site.site_title = "LeaveFlow"
admin.site.index_title = "Leave Management Control Panel"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role_badge', 'department', 'attendance_bar', 'leave_balance', 'joined_date')
    list_filter = ('role', 'department')
    search_fields = ('name', 'email')
    ordering = ('name',)
    readonly_fields = ('joined_date',)

    fieldsets = (
        ('Personal Info', {'fields': ('name', 'email', 'password')}),
        ('Role & Department', {'fields': ('role', 'department')}),
        ('Stats', {'fields': ('attendance_percent', 'leave_balance', 'joined_date')}),
    )

    def role_badge(self, obj):
        color = '#764ba2' if obj.role == 'MANAGER' else '#667eea'
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700">{}</span>',
            color, obj.role
        )
    role_badge.short_description = 'Role'

    def attendance_bar(self, obj):
        pct = obj.attendance_percent
        color = '#10b981' if pct >= 90 else '#f59e0b' if pct >= 75 else '#ef4444'
        return format_html(
            '<div style="display:flex;align-items:center;gap:8px">'
            '<div style="width:100px;height:8px;background:#e8eaf0;border-radius:4px;overflow:hidden">'
            '<div style="width:{}%;height:100%;background:{};border-radius:4px"></div></div>'
            '<span style="font-weight:700;color:{}">{:.1f}%</span></div>',
            pct, color, color, pct
        )
    attendance_bar.short_description = 'Attendance'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'leave_type_badge', 'start_date', 'end_date', 'days_count', 'applied_on', 'status_badge', 'approval_actions')
    list_filter = ('status', 'leave_type', 'employee__department')
    search_fields = ('employee__name', 'reason')
    ordering = ('-applied_on',)
    readonly_fields = ('applied_on',)
    actions = ['approve_selected', 'reject_selected']

    fieldsets = (
        ('Request Info', {'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'reason')}),
        ('Status', {'fields': ('status', 'applied_on')}),
    )

    def employee_name(self, obj):
        dept = obj.employee.department
        return format_html(
            '<div style="display:flex;align-items:center;gap:8px">'
            '<div style="width:32px;height:32px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:13px">{}</div>'
            '<div><div style="font-weight:600">{}</div><div style="font-size:11px;color:#999">{}</div></div></div>',
            obj.employee.name[0], obj.employee.name, dept
        )
    employee_name.short_description = 'Employee'

    def leave_type_badge(self, obj):
        colors = {'SICK':'#ef4444','CASUAL':'#667eea','ANNUAL':'#10b981','EMERGENCY':'#f59e0b'}
        c = colors.get(obj.leave_type, '#667eea')
        return format_html(
            '<span style="background:{};color:white;padding:3px 9px;border-radius:6px;font-size:11px;font-weight:700">{}</span>',
            c, obj.leave_type
        )
    leave_type_badge.short_description = 'Type'

    def days_count(self, obj):
        return format_html('<strong>{}</strong> day(s)', obj.days())
    days_count.short_description = 'Duration'

    def status_badge(self, obj):
        configs = {
            'PENDING':  ('#fff8e1', '#f59e0b', '⏳'),
            'APPROVED': ('#e8faf0', '#10b981', '✅'),
            'REJECTED': ('#fee8e8', '#ef4444', '❌'),
        }
        bg, color, icon = configs.get(obj.status, ('#eee','#333',''))
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700">{} {}</span>',
            bg, color, icon, obj.status
        )
    status_badge.short_description = 'Status'

    def approval_actions(self, obj):
        if obj.status == 'PENDING':
            return format_html(
                '<a href="/admin/employees/leaverequest/{}/change/" '
                'style="background:linear-gradient(135deg,#10b981,#34d399);color:white;padding:5px 12px;'
                'border-radius:7px;font-size:11px;font-weight:700;text-decoration:none;margin-right:5px">✓ Review</a>',
                obj.id
            )
        return format_html('<span style="color:#ccc;font-size:12px">Done</span>')
    approval_actions.short_description = 'Action'

    def approve_selected(self, request, queryset):
        for leave in queryset.filter(status='PENDING'):
            leave.status = 'APPROVED'
            leave.save()
            emp = leave.employee
            emp.attendance_percent = max(0, round(emp.attendance_percent - (leave.days() * 0.5), 1))
            emp.leave_balance = max(0, emp.leave_balance - leave.days())
            emp.save()
        self.message_user(request, f"Selected requests approved successfully.")
    approve_selected.short_description = "✅ Approve selected requests"

    def reject_selected(self, request, queryset):
        queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, f"Selected requests rejected.")
    reject_selected.short_description = "❌ Reject selected requests"
""")
print("Created: employees/admin.py")

# ─────────────────────────────────────────────
# views.py — No approve/reject in manager view
# ─────────────────────────────────────────────
with open('employees/views.py', 'w', encoding='utf-8') as f:
    f.write("""from django.shortcuts import render, redirect
from .models import Employee, LeaveRequest

def login_view(request):
    if request.method == 'POST':
        try:
            user = Employee.objects.get(email=request.POST['email'], password=request.POST['password'])
            request.session['user_id'] = user.id
            request.session['role'] = user.role
            request.session['name'] = user.name
            if user.role == 'MANAGER':
                return redirect('manager_dashboard')
            return redirect('employee_dashboard')
        except:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def employee_dashboard(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    uid = request.session.get('user_id')
    employee = Employee.objects.get(id=uid)
    leaves = LeaveRequest.objects.filter(employee_id=uid).order_by('-applied_on')
    approved = leaves.filter(status='APPROVED').count()
    pending = leaves.filter(status='PENDING').count()
    rejected = leaves.filter(status='REJECTED').count()
    attendance_gap = round(100 - employee.attendance_percent, 1)
    leave_used = 20 - employee.leave_balance
    leave_used_pct = min(100, round((leave_used / 20) * 100))
    return render(request, 'employee_dashboard.html', {
        'employee': employee, 'leaves': leaves,
        'approved': approved, 'pending': pending,
        'rejected': rejected,
        'attendance_gap': attendance_gap,
        'leave_used_pct': leave_used_pct,
    })

def manager_dashboard(request):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leaves = LeaveRequest.objects.all().select_related('employee').order_by('-applied_on')
    employees = Employee.objects.filter(role='EMPLOYEE')
    pending_count = leaves.filter(status='PENDING').count()
    approved_count = leaves.filter(status='APPROVED').count()
    rejected_count = leaves.filter(status='REJECTED').count()
    return render(request, 'manager_dashboard.html', {
        'leaves': leaves,
        'employees': employees,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_emp': employees.count(),
        'name': request.session.get('name'),
    })

def apply_leave(request):
    role = request.session.get('role')
    if role not in ('EMPLOYEE', 'MANAGER'):
        return redirect('login')
    if request.method == 'POST':
        LeaveRequest.objects.create(
            employee_id=request.session.get('user_id'),
            leave_type=request.POST.get('leave_type', 'CASUAL'),
            start_date=request.POST['start'],
            end_date=request.POST['end'],
            reason=request.POST['reason']
        )
        if role == 'MANAGER':
            return redirect('manager_dashboard')
        return redirect('employee_dashboard')
    return render(request, 'apply_leave.html', {'role': role})

def logout_view(request):
    request.session.flush()
    return redirect('login')
""")
print("Created: employees/views.py")

# ─────────────────────────────────────────────
# urls.py (app) — removed update_status URL
# ─────────────────────────────────────────────
with open('employees/urls.py', 'w', encoding='utf-8') as f:
    f.write("""from django.urls import path
from . import views
urlpatterns = [
    path('', views.login_view, name='login'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('apply/', views.apply_leave, name='apply_leave'),
    path('logout/', views.logout_view, name='logout'),
]
""")
print("Created: employees/urls.py")

# ─────────────────────────────────────────────
# main urls.py
# ─────────────────────────────────────────────
project_dir = None
for item in os.listdir('.'):
    if os.path.isdir(item) and os.path.exists(os.path.join(item, 'settings.py')):
        project_dir = item
        break

if project_dir:
    with open(f'{project_dir}/urls.py', 'w', encoding='utf-8') as f:
        f.write("""from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employees.urls')),
]
""")
    print(f"Created: {project_dir}/urls.py")

    settings_path = f'{project_dir}/settings.py'
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings_content = f.read()
    if "'employees'" not in settings_content and '"employees"' not in settings_content:
        settings_content = settings_content.replace(
            "'django.contrib.staticfiles',",
            "'django.contrib.staticfiles',\n    'employees',"
        )
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(settings_content)
        print(f"Patched: {project_dir}/settings.py")
    else:
        print("OK: 'employees' already in INSTALLED_APPS")

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
with open('employees/templates/login.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LeaveFlow - Sign In</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;font-family:'Inter',sans-serif;display:flex;background:#0b0f1a}
.left{flex:1;background:linear-gradient(135deg,#0b0f1a,#1a1040,#0d1f3c);display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px;position:relative;overflow:hidden}
.blob1{position:absolute;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(102,126,234,0.18),transparent 70%);top:-100px;left:-100px;pointer-events:none}
.blob2{position:absolute;width:350px;height:350px;border-radius:50%;background:radial-gradient(circle,rgba(240,147,251,0.12),transparent 70%);bottom:-50px;right:-50px;pointer-events:none}
.brand-logo{width:84px;height:84px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:26px;display:flex;align-items:center;justify-content:center;margin-bottom:22px;box-shadow:0 20px 50px rgba(102,126,234,0.45);position:relative;z-index:1}
.brand-logo i{font-size:40px;color:white}
.brand-name{font-size:44px;font-weight:800;color:white;letter-spacing:-1.5px;position:relative;z-index:1}
.brand-name span{background:linear-gradient(135deg,#a78bfa,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-tag{color:rgba(255,255,255,0.4);font-size:15px;margin-top:8px;margin-bottom:50px;position:relative;z-index:1}
.features{display:flex;flex-direction:column;gap:18px;position:relative;z-index:1;width:100%;max-width:360px}
.feat{display:flex;align-items:center;gap:14px;color:rgba(255,255,255,0.7);font-size:14px;font-weight:500}
.ficon{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
.fi1{background:rgba(102,126,234,0.2);color:#818cf8}
.fi2{background:rgba(16,185,129,0.2);color:#34d399}
.fi3{background:rgba(245,158,11,0.2);color:#fbbf24}
.fi4{background:rgba(239,68,68,0.2);color:#f87171}
.right{width:500px;background:white;display:flex;align-items:center;justify-content:center;padding:60px 50px}
.box{width:100%}
.title{font-size:28px;font-weight:800;color:#1a1d2e;letter-spacing:-0.5px}
.sub{color:#9ea3b8;font-size:14px;margin-top:6px;margin-bottom:38px}
.lbl{display:block;font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:8px}
.iw{position:relative;margin-bottom:22px}
.iico{position:absolute;left:15px;top:50%;transform:translateY(-50%);color:#c4c8d8;font-size:14px}
input{width:100%;border:1.5px solid #e8eaf0;border-radius:13px;padding:14px 14px 14px 42px;font-size:14px;color:#1a1d2e;font-family:'Inter',sans-serif;background:#f9faff;transition:all 0.2s}
input:focus{border-color:#667eea;box-shadow:0 0 0 4px rgba(102,126,234,0.1);outline:none;background:white}
.btn{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:13px;padding:15px;font-size:15px;font-weight:700;color:white;cursor:pointer;font-family:'Inter',sans-serif;box-shadow:0 8px 24px rgba(102,126,234,0.4);transition:all 0.3s;margin-top:4px}
.btn:hover{transform:translateY(-2px);box-shadow:0 14px 32px rgba(102,126,234,0.55)}
.err{background:#fff0f0;border:1.5px solid #ffd0d0;border-radius:11px;padding:12px 15px;color:#e53e3e;font-size:13px;margin-bottom:22px;display:flex;align-items:center;gap:9px}
.hint{background:#f4f6ff;border-radius:11px;padding:16px 18px;font-size:12px;color:#667eea;margin-top:26px;border:1px solid #e0e7ff}
.hint strong{display:block;color:#3a3d4e;font-size:13px;margin-bottom:5px}
.divider{display:flex;align-items:center;gap:12px;color:#d1d5e0;font-size:11px;margin:22px 0}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:#e8eaf0}
</style>
</head>
<body>
<div class="left">
  <div class="blob1"></div><div class="blob2"></div>
  <div class="brand-logo"><i class="fas fa-calendar-check"></i></div>
  <div class="brand-name">Leave<span>Flow</span></div>
  <div class="brand-tag">Smart Employee Leave Management System</div>
  <div class="features">
    <div class="feat"><div class="ficon fi1"><i class="fas fa-user-clock"></i></div>Real-time leave tracking & status updates</div>
    <div class="feat"><div class="ficon fi2"><i class="fas fa-chart-line"></i></div>Live attendance percentage per employee</div>
    <div class="feat"><div class="ficon fi3"><i class="fas fa-shield-check"></i></div>Admin-controlled approvals & rejections</div>
    <div class="feat"><div class="ficon fi4"><i class="fas fa-layer-group"></i></div>Separate portals for employees & managers</div>
  </div>
</div>
<div class="right">
  <div class="box">
    <div class="title">Welcome back 👋</div>
    <div class="sub">Sign in to your LeaveFlow account</div>
    {% if error %}<div class="err"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
    <form method="POST">{% csrf_token %}
      <label class="lbl">Email Address</label>
      <div class="iw"><i class="fas fa-envelope iico"></i><input type="email" name="email" placeholder="you@company.com" required></div>
      <label class="lbl">Password</label>
      <div class="iw"><i class="fas fa-lock iico"></i><input type="password" name="password" placeholder="Enter your password" required></div>
      <button type="submit" class="btn"><i class="fas fa-sign-in-alt" style="margin-right:8px"></i>Sign In to LeaveFlow</button>
    </form>
    <div class="divider">Admin Access</div>
    <div class="hint">
      <strong><i class="fas fa-crown" style="color:#f59e0b;margin-right:6px"></i>For Admins</strong>
      Go to <code style="background:#e0e7ff;padding:2px 6px;border-radius:4px">/admin/</code> to approve or reject all leave requests, manage employees, and view full records.
    </div>
  </div>
</div>
</body>
</html>
""")
print("Created: employees/templates/login.html")

# ─────────────────────────────────────────────
# EMPLOYEE DASHBOARD
# ─────────────────────────────────────────────
with open('employees/templates/employee_dashboard.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - My Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f3fa;font-family:'Inter',sans-serif}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:252px;background:linear-gradient(180deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;z-index:100;box-shadow:6px 0 28px rgba(0,0,0,0.35)}
.slogo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:13px}
.si{width:44px;height:44px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:13px;display:flex;align-items:center;justify-content:center;color:white;font-size:20px;box-shadow:0 4px 14px rgba(102,126,234,0.45)}
.sn{color:white;font-size:17px;font-weight:800;letter-spacing:-0.3px}
.ss{color:rgba(255,255,255,0.3);font-size:10px}
.snav{padding:16px 12px;flex:1}
.sl-sec{color:rgba(255,255,255,0.22);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:10px 12px 5px}
.sl{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.sl:hover,.sl.active{background:rgba(102,126,234,0.25);color:white}
.sl i{width:16px;text-align:center}
.sfoot{padding:14px 12px;border-top:1px solid rgba(255,255,255,0.07)}
.susr{display:flex;align-items:center;gap:10px;padding:10px 12px;background:rgba(255,255,255,0.06);border-radius:10px}
.sav{width:36px;height:36px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:15px;flex-shrink:0}
.sun{color:white;font-size:12px;font-weight:600}
.srd{color:rgba(255,255,255,0.35);font-size:10px}
.main{margin-left:252px;padding:28px 34px;min-height:100vh}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
.pt{font-size:22px;font-weight:800;color:#1a1d2e;letter-spacing:-0.4px}
.ps{font-size:13px;color:#9ea3b8;margin-top:4px}
.btn-new{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:12px;padding:12px 22px;font-size:13px;font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:8px;box-shadow:0 6px 18px rgba(102,126,234,0.38);transition:all 0.2s}
.btn-new:hover{transform:translateY(-2px);color:white;box-shadow:0 12px 28px rgba(102,126,234,0.5)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px}
.chip{background:white;border-radius:9px;padding:7px 14px;font-size:12px;color:#5a5f7a;display:flex;align-items:center;gap:7px;box-shadow:0 1px 6px rgba(0,0,0,0.06);font-weight:500}
.chip i{color:#667eea;font-size:11px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:22px}
.kpi{background:white;border-radius:16px;padding:20px 22px;box-shadow:0 2px 14px rgba(0,0,0,0.05);position:relative;overflow:hidden}
.kpi::after{content:'';position:absolute;top:0;left:0;right:0;height:3.5px}
.k1::after{background:linear-gradient(90deg,#667eea,#764ba2)}
.k2::after{background:linear-gradient(90deg,#10b981,#34d399)}
.k3::after{background:linear-gradient(90deg,#f59e0b,#fbbf24)}
.k4::after{background:linear-gradient(90deg,#ef4444,#f87171)}
.kn{font-size:32px;font-weight:900;color:#1a1d2e;letter-spacing:-1px}
.kl{font-size:11px;color:#9ea3b8;margin-top:5px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.ki{position:absolute;right:18px;top:50%;transform:translateY(-50%);font-size:38px;opacity:0.055}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
.card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 2px 14px rgba(0,0,0,0.05)}
.ct{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:18px;display:flex;align-items:center;gap:8px}
.ct i{color:#667eea}
.attpct{font-size:58px;font-weight:900;line-height:1;background:linear-gradient(135deg,#10b981,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;display:block;margin-bottom:4px}
.attsub{text-align:center;color:#9ea3b8;font-size:12px;margin-bottom:22px;font-weight:500}
.pr{margin-bottom:13px}
.prl{display:flex;justify-content:space-between;font-size:11px;color:#9ea3b8;margin-bottom:5px;font-weight:500}
.pb{height:7px;border-radius:4px;background:#f0f3fa;overflow:hidden}
.pf{height:100%;border-radius:4px;transition:width 1.2s ease}
.tcard{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 2px 14px rgba(0,0,0,0.05)}
table{width:100%;border-collapse:collapse}
thead th{font-size:10px;font-weight:700;color:#9ea3b8;text-transform:uppercase;letter-spacing:.07em;padding:9px 12px;border-bottom:1px solid #f0f3fa}
tbody td{padding:12px 12px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9ff}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#fafbff}
.bp{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:20px;font-size:11px;font-weight:600}
.bpend{background:#fff8e1;color:#f59e0b}
.bapp{background:#e8faf0;color:#10b981}
.brej{background:#fee8e8;color:#ef4444}
.ltag{font-size:10px;padding:3px 8px;border-radius:6px;font-weight:700;background:#eef0ff;color:#667eea}
.notice{background:linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.05));border:1px solid rgba(102,126,234,0.15);border-radius:11px;padding:12px 16px;font-size:12px;color:#667eea;display:flex;align-items:center;gap:9px;margin-bottom:22px}
</style>
</head>
<body>
<div class="sidebar">
  <div class="slogo">
    <div class="si"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sn">LeaveFlow</div><div class="ss">Employee Portal</div></div>
  </div>
  <div class="snav">
    <div class="sl-sec">Navigation</div>
    <a href="{% url 'employee_dashboard' %}" class="sl active"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="sl"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="sl-sec">Account</div>
    <a href="{% url 'logout' %}" class="sl"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sfoot">
    <div class="susr">
      <div class="sav">{{ employee.name|first }}</div>
      <div><div class="sun">{{ employee.name }}</div><div class="srd">{{ employee.department }}</div></div>
    </div>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div><div class="pt">Welcome, {{ employee.name }} 👋</div><div class="ps">Your leave & attendance overview</div></div>
    <a href="{% url 'apply_leave' %}" class="btn-new"><i class="fas fa-plus"></i>New Leave Request</a>
  </div>

  <div class="notice"><i class="fas fa-info-circle" style="font-size:15px"></i>All leave requests are reviewed and approved by the Admin. You will see status updates here.</div>

  <div class="chips">
    <div class="chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="chip"><i class="fas fa-umbrella-beach"></i>{{ employee.leave_balance }} days balance</div>
    <div class="chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
  </div>

  <div class="g4">
    <div class="kpi k1"><div class="kn">{{ leaves.count }}</div><div class="kl">Total Requests</div><i class="fas fa-file-alt ki"></i></div>
    <div class="kpi k2"><div class="kn">{{ approved }}</div><div class="kl">Approved</div><i class="fas fa-check-circle ki"></i></div>
    <div class="kpi k3"><div class="kn">{{ pending }}</div><div class="kl">Pending</div><i class="fas fa-hourglass-half ki"></i></div>
    <div class="kpi k4"><div class="kn">{{ rejected }}</div><div class="kl">Rejected</div><i class="fas fa-times-circle ki"></i></div>
  </div>

  <div class="g2">
    <div class="card">
      <div class="ct"><i class="fas fa-chart-line"></i>Attendance Overview</div>
      <span class="attpct">{{ employee.attendance_percent }}%</span>
      <div class="attsub">Overall Attendance Rate</div>
      <div class="pr">
        <div class="prl"><span>Present Days</span><span>{{ employee.attendance_percent }}%</span></div>
        <div class="pb"><div class="pf" style="width:{{ employee.attendance_percent }}%;background:linear-gradient(90deg,#10b981,#34d399)"></div></div>
      </div>
      <div class="pr">
        <div class="prl"><span>Absent / On Leave</span><span>{{ attendance_gap }}%</span></div>
        <div class="pb"><div class="pf" style="width:{{ attendance_gap }}%;background:linear-gradient(90deg,#ef4444,#f87171)"></div></div>
      </div>
      <div class="pr">
        <div class="prl"><span>Leave Balance Used</span><span>{{ leave_used_pct }}% of 20 days</span></div>
        <div class="pb"><div class="pf" style="width:{{ leave_used_pct }}%;background:linear-gradient(90deg,#667eea,#764ba2)"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="ct"><i class="fas fa-chart-pie"></i>Request Breakdown</div>
      <canvas id="lc" height="200"></canvas>
    </div>
  </div>

  <div class="tcard">
    <div class="ct"><i class="fas fa-history"></i>Leave Request History</div>
    <table>
      <thead><tr><th>#</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Reason</th><th>Applied On</th><th>Status</th></tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td style="color:#b0b4c8">{{ forloop.counter }}</td>
        <td><span class="ltag">{{ leave.leave_type }}</span></td>
        <td>{{ leave.start_date }}</td>
        <td>{{ leave.end_date }}</td>
        <td><strong>{{ leave.days }}</strong>d</td>
        <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#6b7280">{{ leave.reason }}</td>
        <td style="font-size:12px;color:#b0b4c8">{{ leave.applied_on }}</td>
        <td>
          {% if leave.status == 'APPROVED' %}<span class="bp bapp"><i class="fas fa-check"></i>Approved</span>
          {% elif leave.status == 'REJECTED' %}<span class="bp brej"><i class="fas fa-times"></i>Rejected</span>
          {% else %}<span class="bp bpend"><i class="fas fa-clock"></i>Pending</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="8" style="text-align:center;padding:32px;color:#c4c8d8">No requests yet. Click <strong>New Leave Request</strong> to apply.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<script>
new Chart(document.getElementById('lc'),{type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved }},{{ pending }},{{ rejected }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:8}]},
  options:{responsive:true,cutout:'72%',plugins:{legend:{position:'bottom',labels:{padding:18,font:{size:12,family:'Inter'}}}}}
});
</script>
</body>
</html>
""")
print("Created: employees/templates/employee_dashboard.html")

# ─────────────────────────────────────────────
# MANAGER DASHBOARD — VIEW ONLY, no approve/reject
# ─────────────────────────────────────────────
with open('employees/templates/manager_dashboard.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Manager Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f3fa;font-family:'Inter',sans-serif}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:252px;background:linear-gradient(180deg,#1a0533,#2d1b69,#1e1045);display:flex;flex-direction:column;z-index:100;box-shadow:6px 0 28px rgba(0,0,0,0.35)}
.slogo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:13px}
.si{width:44px;height:44px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:13px;display:flex;align-items:center;justify-content:center;color:white;font-size:20px;box-shadow:0 4px 14px rgba(240,147,251,0.45)}
.sn{color:white;font-size:17px;font-weight:800}
.ss{color:rgba(255,255,255,0.3);font-size:10px}
.snav{padding:16px 12px;flex:1}
.sl-sec{color:rgba(255,255,255,0.22);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:10px 12px 5px}
.sl{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.sl:hover,.sl.active{background:rgba(240,147,251,0.18);color:white}
.sl i{width:16px;text-align:center}
.sfoot{padding:14px 12px;border-top:1px solid rgba(255,255,255,0.07)}
.susr{display:flex;align-items:center;gap:10px;padding:10px 12px;background:rgba(255,255,255,0.06);border-radius:10px}
.sav{width:36px;height:36px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:15px;flex-shrink:0}
.sun{color:white;font-size:12px;font-weight:600}
.srd{color:rgba(255,255,255,0.35);font-size:10px}
.main{margin-left:252px;padding:28px 34px;min-height:100vh}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px}
.pt{font-size:22px;font-weight:800;color:#1a1d2e;letter-spacing:-0.4px}
.ps{font-size:13px;color:#9ea3b8;margin-top:4px}
.btn-apply{background:linear-gradient(135deg,#f093fb,#f5576c);color:white;border:none;border-radius:12px;padding:12px 22px;font-size:13px;font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:8px;box-shadow:0 6px 18px rgba(240,147,251,0.38);transition:all 0.2s}
.btn-apply:hover{transform:translateY(-2px);color:white}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:22px}
.kpi{background:white;border-radius:16px;padding:20px 22px;box-shadow:0 2px 14px rgba(0,0,0,0.05);position:relative;overflow:hidden}
.kpi::after{content:'';position:absolute;top:0;left:0;right:0;height:3.5px}
.k1::after{background:linear-gradient(90deg,#f093fb,#f5576c)}
.k2::after{background:linear-gradient(90deg,#667eea,#764ba2)}
.k3::after{background:linear-gradient(90deg,#10b981,#34d399)}
.kn{font-size:32px;font-weight:900;color:#1a1d2e}
.kl{font-size:11px;color:#9ea3b8;margin-top:5px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.ki{position:absolute;right:18px;top:50%;transform:translateY(-50%);font-size:38px;opacity:0.055}
.g21{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 2px 14px rgba(0,0,0,0.05);margin-bottom:20px}
.ct{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:18px;display:flex;align-items:center;gap:8px}
.ct i{color:#f093fb}
table{width:100%;border-collapse:collapse}
thead th{font-size:10px;font-weight:700;color:#9ea3b8;text-transform:uppercase;letter-spacing:.07em;padding:9px 12px;border-bottom:1px solid #f0f3fa}
tbody td{padding:12px 12px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9ff;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#fafbff}
.bp{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:20px;font-size:11px;font-weight:600}
.bpend{background:#fff8e1;color:#f59e0b}
.bapp{background:#e8faf0;color:#10b981}
.brej{background:#fee8e8;color:#ef4444}
.ltag{font-size:10px;padding:3px 8px;border-radius:6px;font-weight:700;background:#eef0ff;color:#667eea}
.eav{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);display:inline-flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:12px;margin-right:9px;flex-shrink:0;vertical-align:middle}
.abar{height:7px;border-radius:4px;background:#f0f3fa;margin-top:5px;overflow:hidden}
.afill{height:100%;border-radius:4px}
.ag{background:linear-gradient(90deg,#10b981,#34d399)}
.ay{background:linear-gradient(90deg,#f59e0b,#fbbf24)}
.ar{background:linear-gradient(90deg,#ef4444,#f87171)}
.notice{background:linear-gradient(135deg,rgba(240,147,251,0.08),rgba(245,87,108,0.05));border:1px solid rgba(240,147,251,0.2);border-radius:11px;padding:12px 16px;font-size:12px;color:#b05fc0;display:flex;align-items:center;gap:9px;margin-bottom:22px}
</style>
</head>
<body>
<div class="sidebar">
  <div class="slogo">
    <div class="si"><i class="fas fa-shield-alt"></i></div>
    <div><div class="sn">LeaveFlow</div><div class="ss">Manager Panel</div></div>
  </div>
  <div class="snav">
    <div class="sl-sec">Navigation</div>
    <a href="{% url 'manager_dashboard' %}" class="sl active"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="sl"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="sl-sec">Account</div>
    <a href="{% url 'logout' %}" class="sl"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sfoot">
    <div class="susr">
      <div class="sav">M</div>
      <div><div class="sun">{{ name }}</div><div class="srd">Manager</div></div>
    </div>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div><div class="pt">Manager Dashboard 🛡️</div><div class="ps">Monitor team leave requests & attendance</div></div>
    <a href="{% url 'apply_leave' %}" class="btn-apply"><i class="fas fa-plus"></i>Apply for My Leave</a>
  </div>

  <div class="notice"><i class="fas fa-info-circle" style="font-size:15px"></i>Leave approvals and rejections are handled by the <strong style="margin:0 3px">Admin</strong> via the admin portal. This is a read-only view.</div>

  <div class="g3">
    <div class="kpi k1"><div class="kn">{{ total_emp }}</div><div class="kl">Total Employees</div><i class="fas fa-users ki"></i></div>
    <div class="kpi k2"><div class="kn">{{ pending_count }}</div><div class="kl">Pending Approvals</div><i class="fas fa-hourglass-half ki"></i></div>
    <div class="kpi k3"><div class="kn">{{ approved_count }}</div><div class="kl">Approved This Year</div><i class="fas fa-check-double ki"></i></div>
  </div>

  <div class="g21">
    <div class="card" style="margin-bottom:0">
      <div class="ct"><i class="fas fa-list-check"></i>All Leave Requests <span style="margin-left:auto;font-size:11px;font-weight:500;color:#b0b4c8">(read-only — approvals via Admin)</span></div>
      <table>
        <thead><tr><th>Employee</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Reason</th><th>Status</th></tr></thead>
        <tbody>
        {% for leave in leaves %}
        <tr>
          <td>
            <span class="eav">{{ leave.employee.name|first }}</span>
            <span style="font-weight:600">{{ leave.employee.name }}</span>
            <div style="font-size:10px;color:#c4c8d8;margin-left:41px">{{ leave.employee.department }}</div>
          </td>
          <td><span class="ltag">{{ leave.leave_type }}</span></td>
          <td style="font-size:12px">{{ leave.start_date }}</td>
          <td style="font-size:12px">{{ leave.end_date }}</td>
          <td><strong>{{ leave.days }}</strong>d</td>
          <td style="font-size:12px;color:#6b7280;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ leave.reason }}</td>
          <td>
            {% if leave.status == 'APPROVED' %}<span class="bp bapp"><i class="fas fa-check"></i>Approved</span>
            {% elif leave.status == 'REJECTED' %}<span class="bp brej"><i class="fas fa-times"></i>Rejected</span>
            {% else %}<span class="bp bpend"><i class="fas fa-clock"></i>Pending</span>{% endif %}
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="7" style="text-align:center;padding:30px;color:#c4c8d8">No leave requests found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="ct"><i class="fas fa-chart-pie"></i>Leave Overview</div>
      <canvas id="lc" height="230"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="ct"><i class="fas fa-users"></i>Team Attendance Tracker</div>
    <table>
      <thead><tr><th>Employee</th><th>Department</th><th>Leave Balance</th><th>Attendance %</th><th>Status</th></tr></thead>
      <tbody>
      {% for emp in employees %}
      <tr>
        <td><span class="eav">{{ emp.name|first }}</span><strong>{{ emp.name }}</strong></td>
        <td>{{ emp.department }}</td>
        <td><strong>{{ emp.leave_balance }}</strong> days left</td>
        <td>
          <strong>{{ emp.attendance_percent }}%</strong>
          <div class="abar"><div class="afill {% if emp.attendance_percent >= 90 %}ag{% elif emp.attendance_percent >= 75 %}ay{% else %}ar{% endif %}" style="width:{{ emp.attendance_percent }}%"></div></div>
        </td>
        <td>
          {% if emp.attendance_percent >= 90 %}<span style="color:#10b981;font-size:12px;font-weight:700"><i class="fas fa-circle-check me-1"></i>Excellent</span>
          {% elif emp.attendance_percent >= 75 %}<span style="color:#f59e0b;font-size:12px;font-weight:700"><i class="fas fa-exclamation-circle me-1"></i>Average</span>
          {% else %}<span style="color:#ef4444;font-size:12px;font-weight:700"><i class="fas fa-times-circle me-1"></i>Poor</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="5" style="text-align:center;padding:30px;color:#c4c8d8">No employees found.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<script>
new Chart(document.getElementById('lc'),{type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved_count }},{{ pending_count }},{{ rejected_count }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:8}]},
  options:{responsive:true,cutout:'72%',plugins:{legend:{position:'bottom',labels:{padding:18,font:{size:12,family:'Inter'}}}}}
});
</script>
</body>
</html>
""")
print("Created: employees/templates/manager_dashboard.html")

# ─────────────────────────────────────────────
# APPLY LEAVE
# ─────────────────────────────────────────────
with open('employees/templates/apply_leave.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Apply Leave</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f3fa;font-family:'Inter',sans-serif}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:252px;background:linear-gradient(180deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;z-index:100;box-shadow:6px 0 28px rgba(0,0,0,0.35)}
.slogo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:13px}
.si{width:44px;height:44px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:13px;display:flex;align-items:center;justify-content:center;color:white;font-size:20px}
.sn{color:white;font-size:17px;font-weight:800}
.ss{color:rgba(255,255,255,0.3);font-size:10px}
.snav{padding:16px 12px;flex:1}
.sl-sec{color:rgba(255,255,255,0.22);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:10px 12px 5px}
.sl{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.sl:hover,.sl.active{background:rgba(102,126,234,0.25);color:white}
.sl i{width:16px;text-align:center}
.main{margin-left:252px;padding:50px 90px;min-height:100vh}
.pt{font-size:22px;font-weight:800;color:#1a1d2e}
.ps{font-size:13px;color:#9ea3b8;margin-top:5px;margin-bottom:32px}
.fcard{background:white;border-radius:20px;padding:38px 42px;box-shadow:0 4px 26px rgba(0,0,0,0.07);max-width:620px}
.tgrid{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-bottom:26px}
.to{position:relative}
.to input[type=radio]{position:absolute;opacity:0;width:0;height:0}
.tl{display:flex;align-items:center;gap:11px;padding:14px 16px;border:2px solid #e8eaf0;border-radius:13px;cursor:pointer;font-size:13px;font-weight:600;color:#6b7280;background:#f9faff;transition:all 0.2s}
.tl:hover{border-color:#667eea;color:#667eea;background:#f0f2ff}
.to input:checked + .tl{border-color:#667eea;background:linear-gradient(135deg,rgba(102,126,234,0.1),rgba(118,75,162,0.06));color:#667eea}
.tl i{font-size:17px}
.fl{display:block;font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:8px}
.fl i{color:#667eea;margin-right:6px;font-size:12px}
.dr{display:grid;grid-template-columns:1fr 1fr;gap:14px}
input[type=date],textarea{width:100%;border:1.5px solid #e8eaf0;border-radius:13px;padding:13px 14px;font-size:14px;color:#1a1d2e;font-family:'Inter',sans-serif;background:#f9faff;transition:all 0.2s;margin-bottom:20px}
input[type=date]:focus,textarea:focus{border-color:#667eea;box-shadow:0 0 0 4px rgba(102,126,234,0.1);outline:none;background:white}
textarea{resize:vertical}
.btns{display:flex;align-items:center;gap:10px}
.bbk{background:#f0f3fa;border:none;border-radius:12px;padding:13px 22px;font-size:14px;font-weight:600;color:#5a5f7a;text-decoration:none;display:inline-flex;align-items:center;gap:7px;transition:all 0.2s;font-family:'Inter',sans-serif}
.bbk:hover{background:#e4e7f0;color:#3a3d4e}
.bsub{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;padding:13px 30px;font-size:14px;font-weight:700;color:white;cursor:pointer;font-family:'Inter',sans-serif;box-shadow:0 6px 20px rgba(102,126,234,0.38);transition:all 0.3s}
.bsub:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(102,126,234,0.5)}
</style>
</head>
<body>
<div class="sidebar">
  <div class="slogo">
    <div class="si"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sn">LeaveFlow</div><div class="ss">Leave Management</div></div>
  </div>
  <div class="snav">
    <div class="sl-sec">Navigation</div>
    {% if role == 'MANAGER' %}
    <a href="{% url 'manager_dashboard' %}" class="sl"><i class="fas fa-th-large"></i>Dashboard</a>
    {% else %}
    <a href="{% url 'employee_dashboard' %}" class="sl"><i class="fas fa-th-large"></i>Dashboard</a>
    {% endif %}
    <a href="{% url 'apply_leave' %}" class="sl active"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="sl-sec">Account</div>
    <a href="{% url 'logout' %}" class="sl"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
</div>
<div class="main">
  <div class="pt">Apply for Leave</div>
  <div class="ps">Submit your request — the Admin will review and approve it</div>
  <div class="fcard">
    <form method="POST">{% csrf_token %}
      <label class="fl" style="margin-bottom:12px"><i class="fas fa-tag"></i>Select Leave Type</label>
      <div class="tgrid">
        <div class="to"><input type="radio" name="leave_type" id="l1" value="CASUAL" checked><label class="tl" for="l1"><i class="fas fa-coffee" style="color:#667eea"></i>Casual Leave</label></div>
        <div class="to"><input type="radio" name="leave_type" id="l2" value="SICK"><label class="tl" for="l2"><i class="fas fa-thermometer-half" style="color:#ef4444"></i>Sick Leave</label></div>
        <div class="to"><input type="radio" name="leave_type" id="l3" value="ANNUAL"><label class="tl" for="l3"><i class="fas fa-umbrella-beach" style="color:#10b981"></i>Annual Leave</label></div>
        <div class="to"><input type="radio" name="leave_type" id="l4" value="EMERGENCY"><label class="tl" for="l4"><i class="fas fa-exclamation-triangle" style="color:#f59e0b"></i>Emergency</label></div>
      </div>
      <div class="dr">
        <div><label class="fl"><i class="fas fa-calendar-day"></i>Start Date</label><input type="date" name="start" required></div>
        <div><label class="fl"><i class="fas fa-calendar-day"></i>End Date</label><input type="date" name="end" required></div>
      </div>
      <label class="fl"><i class="fas fa-comment-alt"></i>Reason</label>
      <textarea name="reason" rows="4" placeholder="Briefly describe the reason for your leave..." required></textarea>
      <div class="btns">
        {% if role == 'MANAGER' %}<a href="{% url 'manager_dashboard' %}" class="bbk"><i class="fas fa-arrow-left"></i>Back</a>
        {% else %}<a href="{% url 'employee_dashboard' %}" class="bbk"><i class="fas fa-arrow-left"></i>Back</a>{% endif %}
        <button type="submit" class="bsub"><i class="fas fa-paper-plane" style="margin-right:8px"></i>Submit Request</button>
      </div>
    </form>
  </div>
</div>
</body>
</html>
""")
print("Created: employees/templates/apply_leave.html")

print()
print("=" * 55)
print("  ALL FILES CREATED SUCCESSFULLY!")
print("=" * 55)
print()
print("Next — run these commands:")
print("  python manage.py makemigrations")
print("  python manage.py migrate")
print("  python manage.py runserver")
print()
print("Approve/Reject leaves at: http://127.0.0.1:8000/admin/")
print("  -> Go to Leave Requests")
print("  -> Click a request -> change Status to APPROVED/REJECTED -> Save")
print("  -> Or select multiple -> use dropdown action -> Approve/Reject selected")
print()
