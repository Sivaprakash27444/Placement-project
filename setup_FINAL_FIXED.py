"""
LeaveFlow - Complete Setup Script
==================================
Run this from the SAME folder as manage.py
Command: python setup_FINAL_FIXED.py
"""

import os
import sys

# Safety check
if not os.path.exists('manage.py'):
    print("ERROR: Run this script from the same folder as manage.py")
    print("Do: cd to your leave_management folder first, then run python setup_FINAL_FIXED.py")
    sys.exit(1)

print("Found manage.py - running setup in correct folder...")
os.makedirs('employees/templates', exist_ok=True)

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
        return self.name

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
        return f"{self.employee.name} - {self.status}"
""")
print("Created: employees/models.py")

# ─────────────────────────────────────────────
# admin.py
# ─────────────────────────────────────────────
with open('employees/admin.py', 'w', encoding='utf-8') as f:
    f.write("""from django.contrib import admin
from .models import Employee, LeaveRequest
admin.site.register(Employee)
admin.site.register(LeaveRequest)
""")
print("Created: employees/admin.py")

# ─────────────────────────────────────────────
# urls.py (app)
# ─────────────────────────────────────────────
with open('employees/urls.py', 'w', encoding='utf-8') as f:
    f.write("""from django.urls import path
from . import views
urlpatterns = [
    path('', views.login_view, name='login'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('apply/', views.apply_leave, name='apply_leave'),
    path('update/<int:id>/<str:status>/', views.update_status, name='update_status'),
    path('logout/', views.logout_view, name='logout'),
]
""")
print("Created: employees/urls.py")

# ─────────────────────────────────────────────
# views.py
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
    return render(request, 'employee_dashboard.html', {
        'employee': employee, 'leaves': leaves,
        'approved': approved, 'pending': pending,
        'rejected': rejected, 'attendance_gap': attendance_gap,
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
        'leaves': leaves, 'employees': employees,
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

def update_status(request, id, status):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leave = LeaveRequest.objects.get(id=id)
    leave.status = status
    leave.save()
    if status == 'APPROVED':
        emp = leave.employee
        days = leave.days()
        emp.attendance_percent = max(0, round(emp.attendance_percent - (days * 0.5), 1))
        emp.leave_balance = max(0, emp.leave_balance - days)
        emp.save()
    return redirect('manager_dashboard')

def logout_view(request):
    request.session.flush()
    return redirect('login')
""")
print("Created: employees/views.py")

# ─────────────────────────────────────────────
# main urls.py — detect project folder name automatically
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

    # Patch settings.py to add 'employees' if not already there
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
        print(f"Patched: {project_dir}/settings.py — added 'employees' to INSTALLED_APPS")
    else:
        print(f"OK: 'employees' already in INSTALLED_APPS")
else:
    print("WARNING: Could not find settings.py — manually add 'employees' to INSTALLED_APPS")

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
with open('employees/templates/login.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeaveFlow - Sign In</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;font-family:'Inter',sans-serif;display:flex;background:#0b0f1a}
.left-panel{flex:1;background:linear-gradient(135deg,#0b0f1a 0%,#1a1040 50%,#0d1f3c 100%);display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px;position:relative;overflow:hidden}
.left-panel::before{content:'';position:absolute;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(102,126,234,0.15) 0%,transparent 70%);top:-100px;left:-100px}
.left-panel::after{content:'';position:absolute;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(240,147,251,0.1) 0%,transparent 70%);bottom:-50px;right:-50px}
.brand-logo{width:80px;height:80px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:24px;display:flex;align-items:center;justify-content:center;margin-bottom:28px;box-shadow:0 20px 40px rgba(102,126,234,0.4);position:relative;z-index:1}
.brand-logo i{font-size:38px;color:white}
.brand-name{font-size:42px;font-weight:800;color:white;letter-spacing:-1px;position:relative;z-index:1}
.brand-name span{background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-tagline{color:rgba(255,255,255,0.45);font-size:15px;margin-top:10px;margin-bottom:48px;position:relative;z-index:1}
.features{display:flex;flex-direction:column;gap:16px;position:relative;z-index:1}
.feat-item{display:flex;align-items:center;gap:14px;color:rgba(255,255,255,0.7);font-size:14px}
.feat-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
.fi1{background:rgba(102,126,234,0.2);color:#667eea}
.fi2{background:rgba(16,185,129,0.2);color:#10b981}
.fi3{background:rgba(245,158,11,0.2);color:#f59e0b}
.fi4{background:rgba(239,68,68,0.2);color:#ef4444}
.right-panel{width:480px;background:#ffffff;display:flex;align-items:center;justify-content:center;padding:60px 50px}
.login-box{width:100%}
.login-title{font-size:26px;font-weight:800;color:#1a1d2e;margin-bottom:6px}
.login-sub{color:#8a8ea8;font-size:14px;margin-bottom:36px}
.field-label{display:block;font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:7px}
.input-wrap{position:relative;margin-bottom:20px}
.input-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#b0b4c8;font-size:14px}
.form-control{width:100%;border:1.5px solid #e8eaf0;border-radius:12px;padding:13px 14px 13px 40px;font-size:14px;color:#1a1d2e;font-family:'Inter',sans-serif;transition:all 0.2s;background:#f9faff}
.form-control:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.12);outline:none;background:white}
.btn-login{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;padding:14px;font-size:15px;font-weight:700;color:white;cursor:pointer;transition:all 0.3s;font-family:'Inter',sans-serif;box-shadow:0 8px 20px rgba(102,126,234,0.35);margin-top:4px}
.btn-login:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(102,126,234,0.5)}
.err-box{background:#fff0f0;border:1px solid #ffd0d0;border-radius:10px;padding:11px 14px;color:#e53e3e;font-size:13px;margin-bottom:20px;display:flex;align-items:center;gap:8px}
.divider{display:flex;align-items:center;gap:12px;margin:24px 0;color:#c4c8d8;font-size:12px}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:#e8eaf0}
.hint-box{background:#f0f4ff;border-radius:10px;padding:14px 16px;font-size:12px;color:#667eea}
.hint-box strong{display:block;margin-bottom:4px;color:#4a5568}
</style>
</head>
<body>
<div class="left-panel">
  <div class="brand-logo"><i class="fas fa-calendar-check"></i></div>
  <div class="brand-name">Leave<span>Flow</span></div>
  <div class="brand-tagline">Smart Employee Leave Management</div>
  <div class="features">
    <div class="feat-item"><div class="feat-icon fi1"><i class="fas fa-user-clock"></i></div>Real-time leave tracking & approvals</div>
    <div class="feat-item"><div class="feat-icon fi2"><i class="fas fa-chart-line"></i></div>Live attendance percentage per employee</div>
    <div class="feat-item"><div class="feat-icon fi3"><i class="fas fa-bell"></i></div>Instant manager notifications</div>
    <div class="feat-item"><div class="feat-icon fi4"><i class="fas fa-shield-alt"></i></div>Role-based access for employees & managers</div>
  </div>
</div>
<div class="right-panel">
  <div class="login-box">
    <div class="login-title">Welcome back 👋</div>
    <div class="login-sub">Sign in to your LeaveFlow account</div>
    {% if error %}<div class="err-box"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
    <form method="POST">
      {% csrf_token %}
      <label class="field-label">Email Address</label>
      <div class="input-wrap">
        <i class="fas fa-envelope input-icon"></i>
        <input type="email" name="email" class="form-control" placeholder="you@company.com" required>
      </div>
      <label class="field-label">Password</label>
      <div class="input-wrap">
        <i class="fas fa-lock input-icon"></i>
        <input type="password" name="password" class="form-control" placeholder="Enter your password" required>
      </div>
      <button type="submit" class="btn-login"><i class="fas fa-sign-in-alt me-2"></i>Sign In to LeaveFlow</button>
    </form>
    <div class="divider">How to get started</div>
    <div class="hint-box">
      <strong>First time?</strong>
      Go to <code>/admin/</code> and add employees with email, password and role (EMPLOYEE or MANAGER). Then log in here.
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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeaveFlow - My Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f3fa;font-family:'Inter',sans-serif}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:250px;background:linear-gradient(180deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;z-index:100;box-shadow:6px 0 24px rgba(0,0,0,0.3)}
.slogo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:12px}
.slogo-icon{width:42px;height:42px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;display:flex;align-items:center;justify-content:center;color:white;font-size:18px;box-shadow:0 4px 12px rgba(102,126,234,0.4)}
.slogo-name{color:white;font-size:17px;font-weight:800;letter-spacing:-0.3px}
.slogo-sub{color:rgba(255,255,255,0.3);font-size:10px}
.snav{padding:16px 12px;flex:1}
.snav-section{color:rgba(255,255,255,0.22);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:10px 12px 6px}
.slink{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.slink:hover,.slink.active{background:rgba(102,126,234,0.25);color:white}
.slink i{width:16px;text-align:center;font-size:14px}
.sfooter{padding:14px 12px;border-top:1px solid rgba(255,255,255,0.07)}
.suser{display:flex;align-items:center;gap:10px;padding:10px 12px;background:rgba(255,255,255,0.06);border-radius:10px}
.suser-av{width:36px;height:36px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:14px;flex-shrink:0}
.suser-name{color:white;font-size:12px;font-weight:600}
.suser-dept{color:rgba(255,255,255,0.35);font-size:10px}
.main{margin-left:250px;padding:28px 32px;min-height:100vh}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:26px}
.ptitle{font-size:22px;font-weight:800;color:#1a1d2e;letter-spacing:-0.3px}
.psub{font-size:13px;color:#8a8ea8;margin-top:3px}
.btn-apply{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:12px;padding:11px 20px;font-size:13px;font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:8px;box-shadow:0 6px 16px rgba(102,126,234,0.35);transition:all 0.2s}
.btn-apply:hover{transform:translateY(-2px);color:white;box-shadow:0 10px 24px rgba(102,126,234,0.5)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.chip{background:white;border-radius:8px;padding:7px 13px;font-size:12px;color:#5a5f7a;display:flex;align-items:center;gap:6px;box-shadow:0 1px 6px rgba(0,0,0,0.06)}
.chip i{color:#667eea;font-size:11px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:22px}
.kpi{background:white;border-radius:16px;padding:20px 22px;box-shadow:0 2px 12px rgba(0,0,0,0.05);position:relative;overflow:hidden}
.kpi::after{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.kpi.k1::after{background:linear-gradient(90deg,#667eea,#764ba2)}
.kpi.k2::after{background:linear-gradient(90deg,#10b981,#34d399)}
.kpi.k3::after{background:linear-gradient(90deg,#f59e0b,#fbbf24)}
.kpi.k4::after{background:linear-gradient(90deg,#ef4444,#f87171)}
.kpi-num{font-size:30px;font-weight:800;color:#1a1d2e}
.kpi-lbl{font-size:11px;color:#9ea3b8;margin-top:4px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.kpi-ico{position:absolute;right:18px;top:50%;transform:translateY(-50%);font-size:36px;opacity:0.06}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
.card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 2px 12px rgba(0,0,0,0.05)}
.ctitle{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:18px;display:flex;align-items:center;gap:8px}
.ctitle i{color:#667eea}
.att-pct{font-size:54px;font-weight:900;line-height:1;background:linear-gradient(135deg,#10b981,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;display:block}
.att-sub{text-align:center;color:#9ea3b8;font-size:12px;margin-bottom:20px;font-weight:500}
.prog-row{margin-bottom:10px}
.prog-labels{display:flex;justify-content:space-between;font-size:11px;color:#9ea3b8;margin-bottom:5px}
.prog-bar{height:7px;border-radius:4px;background:#f0f3fa;overflow:hidden}
.prog-fill{height:100%;border-radius:4px;transition:width 1s ease}
.table-card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 2px 12px rgba(0,0,0,0.05)}
table{width:100%;border-collapse:collapse}
thead th{font-size:10px;font-weight:700;color:#9ea3b8;text-transform:uppercase;letter-spacing:.07em;padding:10px 12px;border-bottom:1px solid #f0f3fa}
tbody td{padding:12px 12px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9ff}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#fafbff}
.badge-p{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.bp{background:#fff8e1;color:#f59e0b}
.ba{background:#e8faf0;color:#10b981}
.br{background:#fee8e8;color:#ef4444}
.lt-tag{font-size:10px;padding:3px 8px;border-radius:6px;font-weight:700;background:#eef0ff;color:#667eea}
</style>
</head>
<body>
<div class="sidebar">
  <div class="slogo">
    <div class="slogo-icon"><i class="fas fa-calendar-check"></i></div>
    <div><div class="slogo-name">LeaveFlow</div><div class="slogo-sub">Employee Portal</div></div>
  </div>
  <div class="snav">
    <div class="snav-section">Navigation</div>
    <a href="{% url 'employee_dashboard' %}" class="slink active"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="slink"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="snav-section">Account</div>
    <a href="{% url 'logout' %}" class="slink"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sfooter">
    <div class="suser">
      <div class="suser-av">{{ employee.name|first }}</div>
      <div><div class="suser-name">{{ employee.name }}</div><div class="suser-dept">{{ employee.department }}</div></div>
    </div>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="ptitle">Welcome back, {{ employee.name }} 👋</div>
      <div class="psub">Here's your leave & attendance overview</div>
    </div>
    <a href="{% url 'apply_leave' %}" class="btn-apply"><i class="fas fa-plus"></i>New Leave Request</a>
  </div>

  <div class="chips">
    <div class="chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="chip"><i class="fas fa-umbrella-beach"></i>{{ employee.leave_balance }} days leave balance</div>
    <div class="chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
  </div>

  <div class="grid4">
    <div class="kpi k1"><div class="kpi-num">{{ leaves.count }}</div><div class="kpi-lbl">Total Requests</div><i class="fas fa-file-alt kpi-ico"></i></div>
    <div class="kpi k2"><div class="kpi-num">{{ approved }}</div><div class="kpi-lbl">Approved</div><i class="fas fa-check-circle kpi-ico"></i></div>
    <div class="kpi k3"><div class="kpi-num">{{ pending }}</div><div class="kpi-lbl">Pending</div><i class="fas fa-hourglass-half kpi-ico"></i></div>
    <div class="kpi k4"><div class="kpi-num">{{ rejected }}</div><div class="kpi-lbl">Rejected</div><i class="fas fa-times-circle kpi-ico"></i></div>
  </div>

  <div class="grid2">
    <div class="card">
      <div class="ctitle"><i class="fas fa-chart-line"></i>Attendance Overview</div>
      <span class="att-pct">{{ employee.attendance_percent }}%</span>
      <div class="att-sub">Overall Attendance Rate</div>
      <div class="prog-row">
        <div class="prog-labels"><span>Present Days</span><span>{{ employee.attendance_percent }}%</span></div>
        <div class="prog-bar"><div class="prog-fill" style="width:{{ employee.attendance_percent }}%;background:linear-gradient(90deg,#10b981,#34d399)"></div></div>
      </div>
      <div class="prog-row">
        <div class="prog-labels"><span>Absent / On Leave</span><span>{{ attendance_gap }}%</span></div>
        <div class="prog-bar"><div class="prog-fill" style="width:{{ attendance_gap }}%;background:linear-gradient(90deg,#ef4444,#f87171)"></div></div>
      </div>
      <div class="prog-row">
        <div class="prog-labels"><span>Leave Balance Remaining</span><span>{{ employee.leave_balance }}/20 days</span></div>
        <div class="prog-bar"><div class="prog-fill" style="width:{% widthratio employee.leave_balance 20 100 %}%;background:linear-gradient(90deg,#667eea,#764ba2)"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="ctitle"><i class="fas fa-chart-donut"></i>Request Breakdown</div>
      <canvas id="leaveChart" height="200"></canvas>
    </div>
  </div>

  <div class="table-card">
    <div class="ctitle"><i class="fas fa-history"></i>Leave Request History</div>
    <table>
      <thead><tr><th>#</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Reason</th><th>Applied On</th><th>Status</th></tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td style="color:#9ea3b8">{{ forloop.counter }}</td>
        <td><span class="lt-tag">{{ leave.leave_type }}</span></td>
        <td>{{ leave.start_date }}</td>
        <td>{{ leave.end_date }}</td>
        <td><strong>{{ leave.days }}</strong>d</td>
        <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ leave.reason }}</td>
        <td style="color:#9ea3b8;font-size:12px">{{ leave.applied_on }}</td>
        <td>
          {% if leave.status == 'APPROVED' %}<span class="badge-p ba"><i class="fas fa-check"></i>Approved</span>
          {% elif leave.status == 'REJECTED' %}<span class="badge-p br"><i class="fas fa-times"></i>Rejected</span>
          {% else %}<span class="badge-p bp"><i class="fas fa-clock"></i>Pending</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="8" style="text-align:center;padding:30px;color:#b0b4c8">No requests yet. Click <strong>New Leave Request</strong> above to apply.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
new Chart(document.getElementById('leaveChart').getContext('2d'),{
  type:'doughnut',
  data:{
    labels:['Approved','Pending','Rejected'],
    datasets:[{data:[{{ approved }},{{ pending }},{{ rejected }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:8}]
  },
  options:{responsive:true,cutout:'70%',plugins:{legend:{position:'bottom',labels:{padding:18,font:{size:12,family:'Inter'}}}}}
});
</script>
</body>
</html>
""")
print("Created: employees/templates/employee_dashboard.html")

# ─────────────────────────────────────────────
# MANAGER DASHBOARD
# ─────────────────────────────────────────────
with open('employees/templates/manager_dashboard.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeaveFlow - Manager Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f3fa;font-family:'Inter',sans-serif}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:250px;background:linear-gradient(180deg,#1a0533,#2d1b69,#1e1045);display:flex;flex-direction:column;z-index:100;box-shadow:6px 0 24px rgba(0,0,0,0.3)}
.slogo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:12px}
.slogo-icon{width:42px;height:42px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:12px;display:flex;align-items:center;justify-content:center;color:white;font-size:18px;box-shadow:0 4px 12px rgba(240,147,251,0.4)}
.slogo-name{color:white;font-size:17px;font-weight:800;letter-spacing:-0.3px}
.slogo-sub{color:rgba(255,255,255,0.3);font-size:10px}
.snav{padding:16px 12px;flex:1}
.snav-section{color:rgba(255,255,255,0.22);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:10px 12px 6px}
.slink{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.slink:hover,.slink.active{background:rgba(240,147,251,0.18);color:white}
.slink i{width:16px;text-align:center;font-size:14px}
.sfooter{padding:14px 12px;border-top:1px solid rgba(255,255,255,0.07)}
.suser{display:flex;align-items:center;gap:10px;padding:10px 12px;background:rgba(255,255,255,0.06);border-radius:10px}
.suser-av{width:36px;height:36px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:14px;flex-shrink:0}
.suser-name{color:white;font-size:12px;font-weight:600}
.suser-role{color:rgba(255,255,255,0.35);font-size:10px}
.main{margin-left:250px;padding:28px 32px;min-height:100vh}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:26px}
.ptitle{font-size:22px;font-weight:800;color:#1a1d2e;letter-spacing:-0.3px}
.psub{font-size:13px;color:#8a8ea8;margin-top:3px}
.btn-apply-mgr{background:linear-gradient(135deg,#f093fb,#f5576c);color:white;border:none;border-radius:12px;padding:11px 20px;font-size:13px;font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:8px;box-shadow:0 6px 16px rgba(240,147,251,0.35);transition:all 0.2s}
.btn-apply-mgr:hover{transform:translateY(-2px);color:white;box-shadow:0 10px 24px rgba(240,147,251,0.5)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:22px}
.kpi{background:white;border-radius:16px;padding:20px 22px;box-shadow:0 2px 12px rgba(0,0,0,0.05);position:relative;overflow:hidden}
.kpi::after{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.k1::after{background:linear-gradient(90deg,#f093fb,#f5576c)}
.k2::after{background:linear-gradient(90deg,#667eea,#764ba2)}
.k3::after{background:linear-gradient(90deg,#10b981,#34d399)}
.kpi-num{font-size:30px;font-weight:800;color:#1a1d2e}
.kpi-lbl{font-size:11px;color:#9ea3b8;margin-top:4px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.kpi-ico{position:absolute;right:18px;top:50%;transform:translateY(-50%);font-size:36px;opacity:0.06}
.grid21{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 2px 12px rgba(0,0,0,0.05);margin-bottom:20px}
.ctitle{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:18px;display:flex;align-items:center;gap:8px}
.ctitle i{color:#f093fb}
table{width:100%;border-collapse:collapse}
thead th{font-size:10px;font-weight:700;color:#9ea3b8;text-transform:uppercase;letter-spacing:.07em;padding:10px 12px;border-bottom:1px solid #f0f3fa}
tbody td{padding:12px 12px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9ff;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#fafbff}
.badge-p{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.bp{background:#fff8e1;color:#f59e0b}
.ba{background:#e8faf0;color:#10b981}
.br{background:#fee8e8;color:#ef4444}
.lt-tag{font-size:10px;padding:3px 8px;border-radius:6px;font-weight:700;background:#eef0ff;color:#667eea}
.btn-a{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:linear-gradient(135deg,#10b981,#34d399);color:white;border:none;border-radius:8px;font-size:11px;font-weight:700;text-decoration:none;transition:all 0.2s;cursor:pointer}
.btn-a:hover{transform:translateY(-1px);color:white;box-shadow:0 4px 10px rgba(16,185,129,0.3)}
.btn-r{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:linear-gradient(135deg,#ef4444,#f87171);color:white;border:none;border-radius:8px;font-size:11px;font-weight:700;text-decoration:none;margin-left:5px;transition:all 0.2s;cursor:pointer}
.btn-r:hover{transform:translateY(-1px);color:white;box-shadow:0 4px 10px rgba(239,68,68,0.3)}
.emp-av{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);display:inline-flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:12px;margin-right:9px;flex-shrink:0;vertical-align:middle}
.att-bar{height:6px;border-radius:3px;background:#f0f3fa;margin-top:5px;overflow:hidden}
.att-fill{height:100%;border-radius:3px}
.att-green{background:linear-gradient(90deg,#10b981,#34d399)}
.att-yellow{background:linear-gradient(90deg,#f59e0b,#fbbf24)}
.att-red{background:linear-gradient(90deg,#ef4444,#f87171)}
</style>
</head>
<body>
<div class="sidebar">
  <div class="slogo">
    <div class="slogo-icon"><i class="fas fa-shield-alt"></i></div>
    <div><div class="slogo-name">LeaveFlow</div><div class="slogo-sub">Manager Panel</div></div>
  </div>
  <div class="snav">
    <div class="snav-section">Navigation</div>
    <a href="{% url 'manager_dashboard' %}" class="slink active"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="slink"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="snav-section">Account</div>
    <a href="{% url 'logout' %}" class="slink"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sfooter">
    <div class="suser">
      <div class="suser-av">M</div>
      <div><div class="suser-name">{{ name }}</div><div class="suser-role">Manager</div></div>
    </div>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="ptitle">Manager Dashboard 🛡️</div>
      <div class="psub">Approve requests & monitor team attendance in real time</div>
    </div>
    <a href="{% url 'apply_leave' %}" class="btn-apply-mgr"><i class="fas fa-plus"></i>Apply for My Leave</a>
  </div>

  <div class="grid3">
    <div class="kpi k1"><div class="kpi-num">{{ total_emp }}</div><div class="kpi-lbl">Total Employees</div><i class="fas fa-users kpi-ico"></i></div>
    <div class="kpi k2"><div class="kpi-num">{{ pending_count }}</div><div class="kpi-lbl">Pending Approvals</div><i class="fas fa-hourglass-half kpi-ico"></i></div>
    <div class="kpi k3"><div class="kpi-num">{{ approved_count }}</div><div class="kpi-lbl">Approved This Year</div><i class="fas fa-check-double kpi-ico"></i></div>
  </div>

  <div class="grid21">
    <div class="card" style="margin-bottom:0">
      <div class="ctitle"><i class="fas fa-list-check"></i>All Leave Requests</div>
      <table>
        <thead><tr><th>Employee</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
        {% for leave in leaves %}
        <tr>
          <td>
            <span class="emp-av">{{ leave.employee.name|first }}</span>
            <span style="font-weight:600">{{ leave.employee.name }}</span>
            <div style="font-size:10px;color:#b0b4c8;margin-left:41px;margin-top:1px">{{ leave.employee.department }}</div>
          </td>
          <td><span class="lt-tag">{{ leave.leave_type }}</span></td>
          <td style="font-size:12px">{{ leave.start_date }}</td>
          <td style="font-size:12px">{{ leave.end_date }}</td>
          <td><strong>{{ leave.days }}</strong>d</td>
          <td>{% if leave.status == 'APPROVED' %}<span class="badge-p ba">Approved</span>{% elif leave.status == 'REJECTED' %}<span class="badge-p br">Rejected</span>{% else %}<span class="badge-p bp">Pending</span>{% endif %}</td>
          <td>
            {% if leave.status == 'PENDING' %}
            <a href="{% url 'update_status' leave.id 'APPROVED' %}" class="btn-a"><i class="fas fa-check"></i>Approve</a>
            <a href="{% url 'update_status' leave.id 'REJECTED' %}" class="btn-r"><i class="fas fa-times"></i>Reject</a>
            {% else %}<span style="color:#c4c8d8;font-size:12px">Done</span>{% endif %}
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="7" style="text-align:center;padding:30px;color:#b0b4c8">No leave requests found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="ctitle"><i class="fas fa-chart-pie"></i>Leave Overview</div>
      <canvas id="leaveChart" height="220"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="ctitle"><i class="fas fa-users"></i>Team Attendance Tracker</div>
    <table>
      <thead><tr><th>Employee</th><th>Department</th><th>Leave Balance</th><th>Attendance %</th><th>Status</th></tr></thead>
      <tbody>
      {% for emp in employees %}
      <tr>
        <td><span class="emp-av">{{ emp.name|first }}</span><strong>{{ emp.name }}</strong></td>
        <td>{{ emp.department }}</td>
        <td><strong>{{ emp.leave_balance }}</strong> days left</td>
        <td>
          <strong>{{ emp.attendance_percent }}%</strong>
          <div class="att-bar">
            <div class="att-fill {% if emp.attendance_percent >= 90 %}att-green{% elif emp.attendance_percent >= 75 %}att-yellow{% else %}att-red{% endif %}" style="width:{{ emp.attendance_percent }}%"></div>
          </div>
        </td>
        <td>
          {% if emp.attendance_percent >= 90 %}
            <span style="color:#10b981;font-size:12px;font-weight:700"><i class="fas fa-circle-check me-1"></i>Excellent</span>
          {% elif emp.attendance_percent >= 75 %}
            <span style="color:#f59e0b;font-size:12px;font-weight:700"><i class="fas fa-exclamation-circle me-1"></i>Average</span>
          {% else %}
            <span style="color:#ef4444;font-size:12px;font-weight:700"><i class="fas fa-times-circle me-1"></i>Poor</span>
          {% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="5" style="text-align:center;padding:30px;color:#b0b4c8">No employees found. Add them via /admin/</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
new Chart(document.getElementById('leaveChart').getContext('2d'),{
  type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved_count }},{{ pending_count }},{{ rejected_count }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:8}]},
  options:{responsive:true,cutout:'70%',plugins:{legend:{position:'bottom',labels:{padding:18,font:{size:12,family:'Inter'}}}}}
});
</script>
</body>
</html>
""")
print("Created: employees/templates/manager_dashboard.html")

# ─────────────────────────────────────────────
# APPLY LEAVE (works for both employee & manager)
# ─────────────────────────────────────────────
with open('employees/templates/apply_leave.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeaveFlow - Apply Leave</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f3fa;font-family:'Inter',sans-serif}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:250px;background:linear-gradient(180deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;z-index:100;box-shadow:6px 0 24px rgba(0,0,0,0.3)}
.slogo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:12px}
.slogo-icon{width:42px;height:42px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;display:flex;align-items:center;justify-content:center;color:white;font-size:18px}
.slogo-name{color:white;font-size:17px;font-weight:800}
.slogo-sub{color:rgba(255,255,255,0.3);font-size:10px}
.snav{padding:16px 12px;flex:1}
.snav-section{color:rgba(255,255,255,0.22);font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:10px 12px 6px}
.slink{display:flex;align-items:center;gap:12px;padding:11px 14px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.slink:hover,.slink.active{background:rgba(102,126,234,0.25);color:white}
.slink i{width:16px;text-align:center;font-size:14px}
.main{margin-left:250px;padding:50px 80px;min-height:100vh}
.ptitle{font-size:22px;font-weight:800;color:#1a1d2e}
.psub{font-size:13px;color:#8a8ea8;margin-top:4px;margin-bottom:30px}
.form-card{background:white;border-radius:20px;padding:36px 40px;box-shadow:0 4px 24px rgba(0,0,0,0.07);max-width:600px}
.type-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:22px}
.type-option{position:relative}
.type-option input[type=radio]{position:absolute;opacity:0;width:0;height:0}
.type-label{display:flex;align-items:center;gap:10px;padding:13px 16px;border:2px solid #e8eaf0;border-radius:12px;cursor:pointer;transition:all 0.2s;font-size:13px;font-weight:600;color:#5a5f7a;background:#f9faff}
.type-label:hover{border-color:#667eea;background:#f0f2ff;color:#667eea}
.type-option input:checked + .type-label{border-color:#667eea;background:linear-gradient(135deg,rgba(102,126,234,0.1),rgba(118,75,162,0.08));color:#667eea}
.type-label i{font-size:16px}
.field-label{display:block;font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:7px}
.field-label i{color:#667eea;margin-right:6px;font-size:12px}
.form-control,.form-select{width:100%;border:1.5px solid #e8eaf0;border-radius:12px;padding:12px 14px;font-size:14px;color:#1a1d2e;font-family:'Inter',sans-serif;transition:all 0.2s;background:#f9faff;margin-bottom:18px}
.form-control:focus,.form-select:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);outline:none;background:white}
.date-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.btns{display:flex;align-items:center;gap:10px;margin-top:4px}
.btn-back{background:#f0f3fa;border:none;border-radius:12px;padding:12px 20px;font-size:14px;font-weight:600;color:#5a5f7a;text-decoration:none;display:inline-flex;align-items:center;gap:7px;transition:all 0.2s;font-family:'Inter',sans-serif}
.btn-back:hover{background:#e4e7f0;color:#3a3d4e}
.btn-submit{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;padding:12px 28px;font-size:14px;font-weight:700;color:white;cursor:pointer;transition:all 0.3s;font-family:'Inter',sans-serif;box-shadow:0 6px 18px rgba(102,126,234,0.35)}
.btn-submit:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(102,126,234,0.5)}
</style>
</head>
<body>
<div class="sidebar">
  <div class="slogo">
    <div class="slogo-icon"><i class="fas fa-calendar-check"></i></div>
    <div><div class="slogo-name">LeaveFlow</div><div class="slogo-sub">Leave Management</div></div>
  </div>
  <div class="snav">
    <div class="snav-section">Navigation</div>
    {% if role == 'MANAGER' %}
    <a href="{% url 'manager_dashboard' %}" class="slink"><i class="fas fa-th-large"></i>Dashboard</a>
    {% else %}
    <a href="{% url 'employee_dashboard' %}" class="slink"><i class="fas fa-th-large"></i>Dashboard</a>
    {% endif %}
    <a href="{% url 'apply_leave' %}" class="slink active"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="snav-section">Account</div>
    <a href="{% url 'logout' %}" class="slink"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
</div>

<div class="main">
  <div class="ptitle">Apply for Leave</div>
  <div class="psub">Fill in the details below to submit your leave request</div>
  <div class="form-card">
    <form method="POST">
      {% csrf_token %}
      <label class="field-label" style="margin-bottom:12px"><i class="fas fa-tag"></i>Select Leave Type</label>
      <div class="type-grid">
        <div class="type-option"><input type="radio" name="leave_type" id="lt1" value="CASUAL" checked><label class="type-label" for="lt1"><i class="fas fa-coffee" style="color:#667eea"></i>Casual Leave</label></div>
        <div class="type-option"><input type="radio" name="leave_type" id="lt2" value="SICK"><label class="type-label" for="lt2"><i class="fas fa-thermometer-half" style="color:#ef4444"></i>Sick Leave</label></div>
        <div class="type-option"><input type="radio" name="leave_type" id="lt3" value="ANNUAL"><label class="type-label" for="lt3"><i class="fas fa-umbrella-beach" style="color:#10b981"></i>Annual Leave</label></div>
        <div class="type-option"><input type="radio" name="leave_type" id="lt4" value="EMERGENCY"><label class="type-label" for="lt4"><i class="fas fa-exclamation-triangle" style="color:#f59e0b"></i>Emergency</label></div>
      </div>
      <div class="date-row">
        <div><label class="field-label"><i class="fas fa-calendar-day"></i>Start Date</label><input type="date" name="start" class="form-control" required></div>
        <div><label class="field-label"><i class="fas fa-calendar-day"></i>End Date</label><input type="date" name="end" class="form-control" required></div>
      </div>
      <label class="field-label"><i class="fas fa-comment-alt"></i>Reason</label>
      <textarea name="reason" class="form-control" rows="4" placeholder="Briefly describe the reason for your leave request..." required></textarea>
      <div class="btns">
        {% if role == 'MANAGER' %}
        <a href="{% url 'manager_dashboard' %}" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
        {% else %}
        <a href="{% url 'employee_dashboard' %}" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
        {% endif %}
        <button type="submit" class="btn-submit"><i class="fas fa-paper-plane me-2"></i>Submit Request</button>
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
print("Next steps — run these commands:")
print("  python manage.py makemigrations")
print("  python manage.py migrate")
print("  python manage.py createsuperuser")
print("  python manage.py runserver")
print()
print("Then open: http://127.0.0.1:8000/admin/")
print("  -> Add Employees with role=EMPLOYEE")
print("  -> Add a Manager with role=MANAGER")
print("Then open: http://127.0.0.1:8000/")
print()