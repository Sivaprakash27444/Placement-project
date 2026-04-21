import os, sys

# Safety check - must be run from inside leave_management folder
if not os.path.exists('manage.py'):
    print("ERROR: Run this script from inside the leave_management folder (where manage.py is).")
    print("Do: cd leave_management  then  python setup_master.py")
    sys.exit(1)

os.makedirs('employees/templates', exist_ok=True)
print("Writing all files...")

# ── models.py ──────────────────────────────────────────────────────────────
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

# ── views.py ────────────────────────────────────────────────────────────────
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

def manager_dashboard(request):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leaves        = LeaveRequest.objects.all().select_related('employee').order_by('-id')
    employees     = Employee.objects.filter(role='EMPLOYEE')
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
        emp = leave.employee
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

# ── urls.py (app) ────────────────────────────────────────────────────────────
with open('employees/urls.py','w',encoding='utf-8') as f:
    f.write("""from django.urls import path
from . import views
urlpatterns = [
    path('',                               views.login_view,         name='login'),
    path('employee/',                      views.employee_dashboard, name='employee_dashboard'),
    path('manager/',                       views.manager_dashboard,  name='manager_dashboard'),
    path('apply/',                         views.apply_leave,        name='apply_leave'),
    path('update/<int:id>/<str:status>/',  views.update_status,      name='update_status'),
    path('logout/',                        views.logout_view,        name='logout'),
]
""")
print("  employees/urls.py")

# ── admin.py ─────────────────────────────────────────────────────────────────
with open('employees/admin.py','w',encoding='utf-8') as f:
    f.write("""from django.contrib import admin
from .models import Employee, LeaveRequest

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('name','email','role','department','attendance_percent','leave_balance')
    list_filter   = ('role','department')
    search_fields = ('name','email')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee','leave_type','start_date','end_date','status','applied_on')
    list_filter   = ('status','leave_type')
    search_fields = ('employee__name',)
    list_editable = ('status',)
""")
print("  employees/admin.py")

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

# ══════════════════════════════════════════════════════════════════════════════
# HTML TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

# ── login.html ────────────────────────────────────────────────────────────────
with open('employees/templates/login.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LeaveFlow &mdash; Sign In</title>
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
.brand-icon{width:88px;height:88px;background:linear-gradient(135deg,#667eea,#764ba2);
  border-radius:26px;display:inline-flex;align-items:center;justify-content:center;
  box-shadow:0 24px 60px rgba(102,126,234,.45);margin-bottom:24px}
.brand-icon i{font-size:42px;color:#fff}
.brand-name{font-size:48px;font-weight:900;color:#fff;letter-spacing:-2px;line-height:1}
.brand-name span{background:linear-gradient(135deg,#a78bfa,#60a5fa);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-tag{font-size:15px;color:rgba(255,255,255,.4);margin-top:10px;font-weight:400}
.features{margin-top:50px;width:100%;max-width:380px;position:relative;z-index:1}
.feat{display:flex;align-items:center;gap:14px;padding:15px 18px;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  border-radius:14px;margin-bottom:10px;backdrop-filter:blur(8px)}
.feat-ic{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;
  justify-content:center;font-size:16px;flex-shrink:0}
.f1{background:rgba(102,126,234,.25);color:#a5b4fc}
.f2{background:rgba(16,185,129,.25);color:#6ee7b7}
.f3{background:rgba(245,158,11,.25);color:#fcd34d}
.feat-txt{color:rgba(255,255,255,.7);font-size:13px;font-weight:500}
.right{width:500px;background:#fff;display:flex;align-items:center;
  justify-content:center;padding:60px 50px;box-shadow:-30px 0 80px rgba(0,0,0,.3)}
.login-box{width:100%}
.login-title{font-size:30px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.login-sub{font-size:14px;color:#94a3b8;margin-top:6px;margin-bottom:36px;font-weight:400}
.field-group{margin-bottom:20px}
.field-label{font-size:11px;font-weight:700;color:#374151;margin-bottom:8px;display:block;
  text-transform:uppercase;letter-spacing:.07em}
.input-wrap{position:relative}
.input-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);
  color:#94a3b8;font-size:14px}
.form-field{width:100%;padding:14px 14px 14px 42px;border:1.5px solid #e2e8f0;
  border-radius:12px;font-size:14px;color:#0f172a;background:#f8fafc;
  transition:all .2s;outline:none;font-family:'Inter',sans-serif}
.form-field:focus{border-color:#667eea;background:#fff;
  box-shadow:0 0 0 4px rgba(102,126,234,.1)}
.form-field::placeholder{color:#cbd5e1}
.btn-login{width:100%;padding:15px;background:linear-gradient(135deg,#667eea,#764ba2);
  border:none;border-radius:12px;color:#fff;font-size:15px;font-weight:700;
  cursor:pointer;font-family:'Inter',sans-serif;letter-spacing:.2px;
  box-shadow:0 8px 24px rgba(102,126,234,.4);transition:all .25s;margin-top:6px}
.btn-login:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(102,126,234,.55)}
.error-box{background:#fff1f2;border:1.5px solid #fecdd3;border-radius:12px;
  padding:12px 16px;margin-bottom:22px;display:flex;align-items:center;gap:10px;
  font-size:13px;color:#e11d48;font-weight:500}
.divider{display:flex;align-items:center;gap:12px;margin:22px 0;color:#e2e8f0;font-size:11px}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:#e2e8f0}
.demo-row{display:flex;gap:10px}
.demo-chip{flex:1;padding:11px 10px;border:1.5px solid #e2e8f0;border-radius:11px;
  text-align:center;font-size:11px;color:#64748b;font-weight:600;background:#f8fafc;
  line-height:1.7}
.demo-chip i{display:block;font-size:20px;margin-bottom:4px;color:#94a3b8}
.footer-note{text-align:center;font-size:11px;color:#cbd5e1;margin-top:24px}
</style>
</head>
<body>
<div class="left">
  <div class="brand-wrap">
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
      <div class="feat-txt">One-click Leave Approvals &amp; Rejections</div></div>
  </div>
</div>
<div class="right">
  <div class="login-box">
    <div class="login-title">Welcome back</div>
    <div class="login-sub">Sign in to your LeaveFlow account to continue</div>
    {% if error %}<div class="error-box"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
    <form method="POST">
      {% csrf_token %}
      <div class="field-group">
        <label class="field-label">Email Address</label>
        <div class="input-wrap">
          <i class="fas fa-envelope input-icon"></i>
          <input type="email" name="email" class="form-field" placeholder="you@company.com" required>
        </div>
      </div>
      <div class="field-group">
        <label class="field-label">Password</label>
        <div class="input-wrap">
          <i class="fas fa-lock input-icon"></i>
          <input type="password" name="password" class="form-field" placeholder="Enter your password" required>
        </div>
      </div>
      <button type="submit" class="btn-login"><i class="fas fa-sign-in-alt me-2"></i>Sign In to LeaveFlow</button>
    </form>
    <div class="divider">Demo Credentials</div>
    <div class="demo-row">
      <div class="demo-chip"><i class="fas fa-user"></i>Employee<br>john@test.com<br><span style="color:#94a3b8;font-weight:400">test123</span></div>
      <div class="demo-chip"><i class="fas fa-user-shield"></i>Manager<br>sarah@test.com<br><span style="color:#94a3b8;font-weight:400">test123</span></div>
    </div>
    <div class="footer-note">LeaveFlow &copy; 2025 &middot; All rights reserved</div>
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
<title>LeaveFlow &mdash; My Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f0f4f8;min-height:100vh;display:flex}
/* ── sidebar ── */
.sb{width:256px;background:linear-gradient(180deg,#0f172a,#1e1b4b);position:fixed;
  top:0;left:0;bottom:0;display:flex;flex-direction:column;
  box-shadow:4px 0 24px rgba(0,0,0,.3);z-index:50}
.sb-hd{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:12px}
.sb-logo{width:42px;height:42px;background:linear-gradient(135deg,#667eea,#764ba2);
  border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sb-logo i{color:#fff;font-size:19px}
.sb-name{font-size:18px;font-weight:800;color:#fff;letter-spacing:-.5px}
.sb-tag{font-size:10px;color:rgba(255,255,255,.35)}
.sb-user{padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:10px}
.sb-av{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;
  font-size:15px;flex-shrink:0}
.sb-un{font-size:13px;font-weight:600;color:#fff}
.sb-ud{font-size:11px;color:rgba(255,255,255,.4)}
.sb-badge{display:inline-block;background:rgba(102,126,234,.25);color:#a5b4fc;
  font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;margin-top:2px}
.sb-nav{padding:14px 10px;flex:1}
.sb-lbl{font-size:10px;color:rgba(255,255,255,.25);font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;padding:8px 12px 5px}
.sb-a{display:flex;align-items:center;gap:11px;padding:11px 12px;border-radius:10px;
  color:rgba(255,255,255,.5);text-decoration:none;font-size:13px;font-weight:500;
  margin-bottom:2px;transition:all .2s}
.sb-a:hover{background:rgba(255,255,255,.06);color:rgba(255,255,255,.85)}
.sb-a.on{background:rgba(102,126,234,.22);color:#fff;box-shadow:inset 2px 0 0 #667eea}
.sb-a i{width:15px;text-align:center;font-size:14px}
.sb-ft{padding:14px 18px;border-top:1px solid rgba(255,255,255,.07)}
.sb-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
  color:rgba(255,255,255,.38);text-decoration:none;font-size:13px;font-weight:500;
  transition:all .2s}
.sb-out:hover{background:rgba(239,68,68,.12);color:#f87171}
/* ── main ── */
.main{margin-left:256px;flex:1;padding:26px 30px}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:26px}
.pg-title{font-size:23px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.pg-sub{font-size:13px;color:#64748b;margin-top:3px}
.new-btn{display:inline-flex;align-items:center;gap:8px;padding:11px 20px;
  background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;
  border-radius:12px;font-size:13px;font-weight:700;
  box-shadow:0 6px 18px rgba(102,126,234,.38);transition:all .2s;white-space:nowrap}
.new-btn:hover{transform:translateY(-2px);color:#fff;box-shadow:0 10px 28px rgba(102,126,234,.55)}
/* chips */
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.chip{display:inline-flex;align-items:center;gap:6px;background:#fff;
  border:1px solid #e8edf2;border-radius:8px;padding:6px 12px;
  font-size:12px;color:#475569;font-weight:500;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.chip i{color:#667eea;font-size:11px}
/* kpi row */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:22px}
.kpi{background:#fff;border-radius:15px;padding:19px 20px;
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
/* two-col */
.two-col{display:grid;grid-template-columns:1.35fr .65fr;gap:18px;margin-bottom:20px}
.card{background:#fff;border-radius:15px;padding:20px 22px;
  box-shadow:0 1px 6px rgba(0,0,0,.05);border:1px solid #f0f4f8}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.card-title{font-size:13px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:7px}
.card-title i{color:#667eea}
.cnt-badge{background:#f1f5f9;color:#64748b;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
/* attendance card */
.att-score{font-size:60px;font-weight:900;letter-spacing:-3px;text-align:center;line-height:1;margin:6px 0 2px}
.att-g{background:linear-gradient(135deg,#10b981,#059669);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-o{background:linear-gradient(135deg,#f59e0b,#d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-r{background:linear-gradient(135deg,#ef4444,#dc2626);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.att-lbl{font-size:12px;color:#94a3b8;text-align:center;margin-bottom:18px}
.att-status{display:flex;align-items:center;justify-content:center;gap:6px;
  padding:7px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:16px}
.s-good{background:#f0fdf4;color:#16a34a}.s-avg{background:#fffbeb;color:#d97706}.s-poor{background:#fef2f2;color:#dc2626}
/* progress */
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
/* table */
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
.th{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.06em;padding:10px 12px;border-bottom:1px solid #f1f5f9;white-space:nowrap}
.td{padding:13px 12px;font-size:13px;color:#334155;border-bottom:1px solid #f8fafc;vertical-align:middle}
tr:last-child .td{border:none}
tr:hover .td{background:#fafbff}
.st{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.st-a{background:#f0fdf4;color:#16a34a}.st-p{background:#fffbeb;color:#d97706}.st-r{background:#fef2f2;color:#dc2626}
.lt{background:#ede9fe;color:#7c3aed;font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600}
.empty{text-align:center;padding:40px;color:#94a3b8;font-size:13px}
.empty i{font-size:38px;display:block;margin-bottom:10px;opacity:.35}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sb-name">LeaveFlow</div><div class="sb-tag">Employee Portal</div></div>
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
    <div class="sb-lbl">My Info</div>
    <a href="#attendance" class="sb-a"><i class="fas fa-chart-bar"></i>Attendance</a>
    <a href="#history"    class="sb-a"><i class="fas fa-history"></i>Leave History</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Good day, {{ employee.name }} &#128075;</div>
      <div class="pg-sub">Your complete leave &amp; attendance overview</div>
    </div>
    <a href="{% url 'apply_leave' %}" class="new-btn"><i class="fas fa-plus"></i>New Leave Request</a>
  </div>

  <div class="chips">
    <div class="chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
    <div class="chip"><i class="fas fa-umbrella-beach"></i>{{ employee.leave_balance }} leave days remaining</div>
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

  <div class="two-col" id="attendance">
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-line"></i>Attendance Breakdown</div></div>
      <div class="prog">
        <div class="prog-top">
          <span class="prog-lbl"><span class="prog-dot" style="background:#10b981"></span>Attendance Rate</span>
          <span class="prog-val">{{ employee.attendance_percent }}%</span>
        </div>
        <div class="prog-bar"><div class="prog-fill pg" style="width:{{ employee.attendance_percent }}%"></div></div>
      </div>
      <div class="prog">
        <div class="prog-top">
          <span class="prog-lbl"><span class="prog-dot" style="background:#ef4444"></span>Absent / On Leave</span>
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
      <div class="prog">
        <div class="prog-top">
          <span class="prog-lbl"><span class="prog-dot" style="background:#f59e0b"></span>Balance Remaining</span>
          <span class="prog-val">{{ employee.leave_balance }} days</span>
        </div>
        <div class="prog-bar"><div class="prog-fill py" style="width:{% widthratio employee.leave_balance 20 100 %}%"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-tachometer-alt"></i>Score</div></div>
      <div class="att-score {% if employee.attendance_percent >= 90 %}att-g{% elif employee.attendance_percent >= 75 %}att-o{% else %}att-r{% endif %}">{{ employee.attendance_percent }}%</div>
      <div class="att-lbl">Overall Attendance Rate</div>
      <div class="att-status {% if employee.attendance_percent >= 90 %}s-good{% elif employee.attendance_percent >= 75 %}s-avg{% else %}s-poor{% endif %}">
        {% if employee.attendance_percent >= 90 %}<i class="fas fa-check-circle"></i>Excellent Standing
        {% elif employee.attendance_percent >= 75 %}<i class="fas fa-exclamation-circle"></i>Needs Improvement
        {% else %}<i class="fas fa-times-circle"></i>Critical{% endif %}
      </div>
      <canvas id="attChart" height="160"></canvas>
    </div>
  </div>

  <div class="card" id="history">
    <div class="card-hd">
      <div class="card-title"><i class="fas fa-history"></i>Leave Request History</div>
      <span class="cnt-badge">{{ leaves.count }} records</span>
    </div>
    <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th class="th">#</th><th class="th">Type</th><th class="th">From</th>
        <th class="th">To</th><th class="th">Days</th><th class="th">Reason</th>
        <th class="th">Status</th>
      </tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td class="td" style="color:#94a3b8;font-size:12px">{{ forloop.counter }}</td>
        <td class="td"><span class="lt">{{ leave.leave_type }}</span></td>
        <td class="td">{{ leave.start_date }}</td>
        <td class="td">{{ leave.end_date }}</td>
        <td class="td"><strong>{{ leave.days }}d</strong></td>
        <td class="td" style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ leave.reason }}</td>
        <td class="td">
          {% if leave.status == 'APPROVED' %}<span class="st st-a"><i class="fas fa-check"></i>Approved</span>
          {% elif leave.status == 'REJECTED' %}<span class="st st-r"><i class="fas fa-times"></i>Rejected</span>
          {% else %}<span class="st st-p"><i class="fas fa-clock"></i>Pending</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="7"><div class="empty"><i class="fas fa-folder-open"></i>No leave requests yet. Click New Leave Request to get started.</div></td></tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </div>
</div>

<script>
new Chart(document.getElementById('attChart'),{
  type:'doughnut',
  data:{labels:['Present','Absent'],
    datasets:[{data:[{{ employee.attendance_percent }},{{ att_gap }}],
      backgroundColor:['#10b981','#fee2e2'],
      borderColor:['#059669','#fca5a5'],borderWidth:2,hoverOffset:5}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',
    labels:{padding:14,font:{size:11},boxWidth:10}}},cutout:'72%'}
});
</script>
</body>
</html>
""")
print("  employees/templates/employee_dashboard.html")

# ── manager_dashboard.html ────────────────────────────────────────────────────
with open('employees/templates/manager_dashboard.html','w',encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow &mdash; Manager Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f0f4f8;min-height:100vh;display:flex}
.sb{width:256px;background:linear-gradient(180deg,#0f0c29,#1a0533,#2d1b69);position:fixed;
  top:0;left:0;bottom:0;display:flex;flex-direction:column;
  box-shadow:4px 0 24px rgba(0,0,0,.3);z-index:50}
.sb-hd{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:12px}
.sb-logo{width:42px;height:42px;background:linear-gradient(135deg,#f093fb,#f5576c);
  border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sb-logo i{color:#fff;font-size:19px}
.sb-name{font-size:18px;font-weight:800;color:#fff;letter-spacing:-.5px}
.sb-tag{font-size:10px;color:rgba(255,255,255,.35)}
.sb-user{padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:10px}
.sb-av{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#f093fb,#f5576c);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:16px;flex-shrink:0}
.sb-un{font-size:13px;font-weight:600;color:#fff}
.sb-badge{display:inline-block;background:rgba(240,147,251,.2);color:#f9a8d4;
  font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;margin-top:2px}
.sb-nav{padding:14px 10px;flex:1}
.sb-lbl{font-size:10px;color:rgba(255,255,255,.25);font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;padding:8px 12px 5px}
.sb-a{display:flex;align-items:center;gap:11px;padding:11px 12px;border-radius:10px;
  color:rgba(255,255,255,.5);text-decoration:none;font-size:13px;font-weight:500;
  margin-bottom:2px;transition:all .2s}
.sb-a:hover{background:rgba(255,255,255,.06);color:rgba(255,255,255,.85)}
.sb-a.on{background:rgba(240,147,251,.15);color:#fff;box-shadow:inset 2px 0 0 #f093fb}
.sb-a i{width:15px;text-align:center;font-size:14px}
.pend-pill{background:#f59e0b;color:#fff;font-size:10px;padding:2px 7px;
  border-radius:10px;margin-left:auto;font-weight:600}
.sb-ft{padding:14px 18px;border-top:1px solid rgba(255,255,255,.07)}
.sb-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
  color:rgba(255,255,255,.38);text-decoration:none;font-size:13px;font-weight:500;transition:all .2s}
.sb-out:hover{background:rgba(239,68,68,.12);color:#f87171}
.main{margin-left:256px;flex:1;padding:26px 30px}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:26px}
.pg-title{font-size:23px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.pg-sub{font-size:13px;color:#64748b;margin-top:3px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:22px}
.kpi{background:#fff;border-radius:15px;padding:19px 20px;
  box-shadow:0 1px 6px rgba(0,0,0,.05);border:1px solid #f0f4f8}
.kpi-ic{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;
  justify-content:center;font-size:18px;margin-bottom:13px}
.ki1{background:#fdf4ff;color:#a855f7}.ki2{background:#eff6ff;color:#3b82f6}
.ki3{background:#f0fdf4;color:#16a34a}.ki4{background:#fff7ed;color:#ea580c}
.kpi-v{font-size:30px;font-weight:800;color:#0f172a;letter-spacing:-1px}
.kpi-l{font-size:12px;color:#64748b;font-weight:500;margin-top:2px}
.kpi-note{font-size:11px;margin-top:8px;font-weight:600;color:#64748b}
.row2{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.card{background:#fff;border-radius:15px;padding:20px 22px;
  box-shadow:0 1px 6px rgba(0,0,0,.05);border:1px solid #f0f4f8;margin-bottom:20px}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.card-title{font-size:13px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:7px}
.card-title i{color:#a855f7}
.cnt-badge{background:#f1f5f9;color:#64748b;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
.pend-badge{background:#fffbeb;color:#d97706;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
table{width:100%;border-collapse:collapse}
.th{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.06em;padding:10px 12px;border-bottom:1px solid #f1f5f9;white-space:nowrap}
.td{padding:12px 12px;font-size:13px;color:#334155;border-bottom:1px solid #f8fafc;vertical-align:middle}
tr:last-child .td{border:none}
tr:hover .td{background:#fafbff}
.emp-cell{display:flex;align-items:center;gap:9px}
.emp-av{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;flex-shrink:0}
.emp-nm{font-size:13px;font-weight:600;color:#0f172a}
.emp-dep{font-size:11px;color:#94a3b8}
.st{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.st-a{background:#f0fdf4;color:#16a34a}.st-p{background:#fffbeb;color:#d97706}.st-r{background:#fef2f2;color:#dc2626}
.lt{background:#ede9fe;color:#7c3aed;font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600}
.btn-app{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;
  background:linear-gradient(135deg,#10b981,#059669);border:none;border-radius:7px;
  color:#fff;font-size:11px;font-weight:600;text-decoration:none;transition:all .15s}
.btn-app:hover{transform:translateY(-1px);color:#fff;box-shadow:0 4px 10px rgba(16,185,129,.3)}
.btn-rej{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;
  background:linear-gradient(135deg,#ef4444,#dc2626);border:none;border-radius:7px;
  color:#fff;font-size:11px;font-weight:600;text-decoration:none;margin-left:5px;transition:all .15s}
.btn-rej:hover{transform:translateY(-1px);color:#fff;box-shadow:0 4px 10px rgba(239,68,68,.3)}
/* attendance tracker */
.att-row{display:flex;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid #f8fafc}
.att-row:last-child{border:none}
.att-av{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;flex-shrink:0}
.att-info{min-width:130px}
.att-nm{font-size:13px;font-weight:600;color:#0f172a}
.att-dp{font-size:11px;color:#94a3b8}
.att-bar-wrap{flex:1}
.att-bar-top{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px}
.att-bar-lbl{color:#64748b}
.att-bar-pct{font-weight:700;color:#0f172a}
.att-bar{height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.att-fill{height:100%;border-radius:4px}
.ag{background:linear-gradient(90deg,#10b981,#059669)}
.ay{background:linear-gradient(90deg,#f59e0b,#d97706)}
.ar{background:linear-gradient(90deg,#ef4444,#dc2626)}
.att-tag{font-size:10px;padding:3px 9px;border-radius:10px;font-weight:600;white-space:nowrap;min-width:68px;text-align:center}
.tg{background:#f0fdf4;color:#16a34a}.ty{background:#fffbeb;color:#d97706}.tr{background:#fef2f2;color:#dc2626}
.empty{text-align:center;padding:40px;color:#94a3b8;font-size:13px}
.empty i{font-size:38px;display:block;margin-bottom:10px;opacity:.35}
.tbl-scroll{overflow-x:auto}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-shield-alt"></i></div>
    <div><div class="sb-name">LeaveFlow</div><div class="sb-tag">Manager Portal</div></div>
  </div>
  <div class="sb-user">
    <div class="sb-av">M</div>
    <div><div class="sb-un">{{ name }}</div><div class="sb-badge">Manager</div></div>
  </div>
  <div class="sb-nav">
    <div class="sb-lbl">Management</div>
    <a href="{% url 'manager_dashboard' %}" class="sb-a on"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="#requests" class="sb-a">
      <i class="fas fa-inbox"></i>Leave Requests
      {% if pending_count > 0 %}<span class="pend-pill">{{ pending_count }}</span>{% endif %}
    </a>
    <a href="#attendance" class="sb-a"><i class="fas fa-chart-bar"></i>Attendance</a>
    <a href="#team" class="sb-a"><i class="fas fa-users"></i>Team</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Manager Dashboard &#128737;</div>
      <div class="pg-sub">Manage leave requests and monitor team attendance</div>
    </div>
  </div>

  <div class="kpis">
    <div class="kpi"><div class="kpi-ic ki1"><i class="fas fa-users"></i></div>
      <div class="kpi-v">{{ total_emp }}</div><div class="kpi-l">Total Employees</div>
      <div class="kpi-note">Active team members</div></div>
    <div class="kpi"><div class="kpi-ic ki2"><i class="fas fa-hourglass-half"></i></div>
      <div class="kpi-v">{{ pending_count }}</div><div class="kpi-l">Pending Approvals</div>
      <div class="kpi-note" style="{% if pending_count > 0 %}color:#d97706{% endif %}">
        {% if pending_count > 0 %}Needs attention{% else %}All clear{% endif %}</div></div>
    <div class="kpi"><div class="kpi-ic ki3"><i class="fas fa-check-double"></i></div>
      <div class="kpi-v">{{ approved_count }}</div><div class="kpi-l">Approved</div>
      <div class="kpi-note">This period</div></div>
    <div class="kpi"><div class="kpi-ic ki4"><i class="fas fa-file-alt"></i></div>
      <div class="kpi-v">{{ total_leaves }}</div><div class="kpi-l">Total Requests</div>
      <div class="kpi-note">All time</div></div>
  </div>

  <div class="row2" id="requests">
    <div class="card" style="margin-bottom:0">
      <div class="card-hd">
        <div class="card-title"><i class="fas fa-inbox"></i>Leave Requests</div>
        {% if pending_count > 0 %}<span class="pend-badge"><i class="fas fa-clock me-1"></i>{{ pending_count }} pending</span>
        {% else %}<span class="cnt-badge">{{ total_leaves }} total</span>{% endif %}
      </div>
      <div class="tbl-scroll">
      <table>
        <thead><tr>
          <th class="th">Employee</th><th class="th">Type</th><th class="th">From</th>
          <th class="th">To</th><th class="th">Days</th><th class="th">Reason</th>
          <th class="th">Status</th><th class="th">Action</th>
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
          <td class="td" style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;color:#64748b">{{ leave.reason }}</td>
          <td class="td">
            {% if leave.status == 'APPROVED' %}<span class="st st-a"><i class="fas fa-check"></i>Approved</span>
            {% elif leave.status == 'REJECTED' %}<span class="st st-r"><i class="fas fa-times"></i>Rejected</span>
            {% else %}<span class="st st-p"><i class="fas fa-clock"></i>Pending</span>{% endif %}
          </td>
          <td class="td">
            {% if leave.status == 'PENDING' %}
            <a href="{% url 'update_status' leave.id 'APPROVED' %}" class="btn-app"><i class="fas fa-check"></i>Approve</a>
            <a href="{% url 'update_status' leave.id 'REJECTED' %}" class="btn-rej"><i class="fas fa-times"></i>Reject</a>
            {% else %}<span style="color:#e2e8f0;font-size:12px">&mdash;</span>{% endif %}
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="8"><div class="empty"><i class="fas fa-inbox"></i>No leave requests found.</div></td></tr>
        {% endfor %}
        </tbody>
      </table>
      </div>
    </div>
    <div class="card" style="margin-bottom:0">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-pie"></i>Overview</div></div>
      <canvas id="donut" height="220"></canvas>
      <div style="margin-top:16px">
        <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f8fafc;font-size:12px"><span style="color:#64748b">Approved</span><strong style="color:#16a34a">{{ approved_count }}</strong></div>
        <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f8fafc;font-size:12px"><span style="color:#64748b">Pending</span><strong style="color:#d97706">{{ pending_count }}</strong></div>
        <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:12px"><span style="color:#64748b">Rejected</span><strong style="color:#dc2626">{{ rejected_count }}</strong></div>
      </div>
    </div>
  </div>

  <div class="card" id="attendance">
    <div class="card-hd">
      <div class="card-title"><i class="fas fa-chart-bar"></i>Employee Attendance Tracker</div>
      <span class="cnt-badge">{{ total_emp }} employees</span>
    </div>
    {% for emp in employees %}
    <div class="att-row">
      <div class="att-av">{{ emp.name|first }}</div>
      <div class="att-info">
        <div class="att-nm">{{ emp.name }}</div>
        <div class="att-dp">{{ emp.department }} &middot; {{ emp.leave_balance }}d left</div>
      </div>
      <div class="att-bar-wrap">
        <div class="att-bar-top">
          <span class="att-bar-lbl">Attendance Rate</span>
          <span class="att-bar-pct">{{ emp.attendance_percent }}%</span>
        </div>
        <div class="att-bar">
          <div class="att-fill {% if emp.attendance_percent >= 90 %}ag{% elif emp.attendance_percent >= 75 %}ay{% else %}ar{% endif %}" style="width:{{ emp.attendance_percent }}%"></div>
        </div>
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
      borderColor:['#d1fae5','#fef3c7','#fee2e2'],
      borderWidth:2,hoverOffset:6}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',
    labels:{padding:14,font:{size:11},boxWidth:10}}},cutout:'68%'}
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
<title>LeaveFlow &mdash; Apply Leave</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f0f4f8;min-height:100vh;display:flex}
.sb{width:256px;background:linear-gradient(180deg,#0f172a,#1e1b4b);position:fixed;
  top:0;left:0;bottom:0;display:flex;flex-direction:column;
  box-shadow:4px 0 24px rgba(0,0,0,.3);z-index:50}
.sb-hd{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:12px}
.sb-logo{width:42px;height:42px;background:linear-gradient(135deg,#667eea,#764ba2);
  border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sb-logo i{color:#fff;font-size:19px}
.sb-name{font-size:18px;font-weight:800;color:#fff;letter-spacing:-.5px}
.sb-tag{font-size:10px;color:rgba(255,255,255,.35)}
.sb-user{padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.07);
  display:flex;align-items:center;gap:10px}
.sb-av{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#667eea,#764ba2);
  display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:15px;flex-shrink:0}
.sb-un{font-size:13px;font-weight:600;color:#fff}
.sb-ud{font-size:11px;color:rgba(255,255,255,.4)}
.sb-nav{padding:14px 10px;flex:1}
.sb-lbl{font-size:10px;color:rgba(255,255,255,.25);font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;padding:8px 12px 5px}
.sb-a{display:flex;align-items:center;gap:11px;padding:11px 12px;border-radius:10px;
  color:rgba(255,255,255,.5);text-decoration:none;font-size:13px;font-weight:500;
  margin-bottom:2px;transition:all .2s}
.sb-a:hover{background:rgba(255,255,255,.06);color:rgba(255,255,255,.85)}
.sb-a.on{background:rgba(102,126,234,.22);color:#fff;box-shadow:inset 2px 0 0 #667eea}
.sb-a i{width:15px;text-align:center;font-size:14px}
.sb-ft{padding:14px 18px;border-top:1px solid rgba(255,255,255,.07)}
.sb-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
  color:rgba(255,255,255,.38);text-decoration:none;font-size:13px;font-weight:500;transition:all .2s}
.sb-out:hover{background:rgba(239,68,68,.12);color:#f87171}
.main{margin-left:256px;flex:1;display:flex;justify-content:center;padding:40px 60px;align-items:flex-start}
.form-wrap{width:100%;max-width:600px}
.pg-title{font-size:23px;font-weight:800;color:#0f172a;letter-spacing:-.5px;margin-bottom:4px}
.pg-sub{font-size:13px;color:#64748b;margin-bottom:24px}
.bal-info{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:11px;
  padding:12px 16px;margin-bottom:22px;display:flex;align-items:center;gap:10px;
  font-size:13px;color:#166534;font-weight:500}
.bal-info i{color:#16a34a}
.form-card{background:#fff;border-radius:18px;padding:34px 36px;
  box-shadow:0 4px 24px rgba(0,0,0,.07);border:1px solid #f0f4f8}
.section-hd{font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.08em;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #f1f5f9}
.lt-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px}
.lt-opt{position:relative}
.lt-opt input{position:absolute;opacity:0;width:0}
.lt-card{display:flex;align-items:center;gap:10px;padding:12px 14px;
  border:1.5px solid #e2e8f0;border-radius:11px;cursor:pointer;
  transition:all .2s;background:#fafafa}
.lt-card:hover{border-color:#a5b4fc;background:#f5f3ff}
.lt-opt input:checked + .lt-card{border-color:#667eea;background:#ede9fe;
  box-shadow:0 0 0 3px rgba(102,126,234,.12)}
.lt-ic{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;
  justify-content:center;font-size:14px;flex-shrink:0}
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
  border:none;border-radius:11px;color:#fff;font-size:14px;font-weight:700;
  cursor:pointer;font-family:'Inter',sans-serif;
  box-shadow:0 6px 18px rgba(102,126,234,.35);transition:all .2s}
.btn-submit:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(102,126,234,.5)}
.btn-back{padding:13px 20px;background:#f8fafc;border:1.5px solid #e2e8f0;
  border-radius:11px;color:#64748b;font-size:14px;font-weight:600;text-decoration:none;
  display:inline-flex;align-items:center;gap:7px;transition:all .2s}
.btn-back:hover{background:#f1f5f9;color:#334155}
</style>
</head>
<body>
<div class="sb">
  <div class="sb-hd">
    <div class="sb-logo"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sb-name">LeaveFlow</div><div class="sb-tag">Employee Portal</div></div>
  </div>
  <div class="sb-user">
    <div class="sb-av">{{ employee.name|first }}</div>
    <div><div class="sb-un">{{ employee.name }}</div><div class="sb-ud">{{ employee.department }}</div></div>
  </div>
  <div class="sb-nav">
    <div class="sb-lbl">Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="sb-a"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}"        class="sb-a on"><i class="fas fa-plus-circle"></i>Apply Leave</a>
  </div>
  <div class="sb-ft"><a href="{% url 'logout' %}" class="sb-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a></div>
</div>

<div class="main">
  <div class="form-wrap">
    <div class="pg-title">Apply for Leave</div>
    <div class="pg-sub">Submit your leave request for manager approval</div>
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

print("\n" + "="*50)
print("ALL FILES CREATED SUCCESSFULLY!")
print("="*50)
print("\nNow run:")
print("  python manage.py makemigrations")
print("  python manage.py migrate")
print("  python manage.py runserver")
