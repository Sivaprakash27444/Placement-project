import os
os.makedirs('employees/templates', exist_ok=True)

files = {}

# ─── MODELS ───────────────────────────────────────────────────────────────────
files['employees/models.py'] = """from django.db import models

class Employee(models.Model):
    ROLE_CHOICES  = [('EMPLOYEE','Employee'),('MANAGER','Manager')]
    DEPT_CHOICES  = [('IT','IT'),('HR','HR'),('Finance','Finance'),('Operations','Operations'),('Marketing','Marketing')]
    name          = models.CharField(max_length=100)
    email         = models.EmailField(unique=True)
    password      = models.CharField(max_length=100)
    role          = models.CharField(max_length=10,  choices=ROLE_CHOICES)
    department    = models.CharField(max_length=20,  choices=DEPT_CHOICES, default='IT')
    attendance_percent = models.FloatField(default=95.0)
    leave_balance = models.IntegerField(default=20)
    joined_date   = models.DateField(auto_now_add=True)
    def __str__(self): return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected')]
    LEAVE_TYPES    = [('SICK','Sick'),('CASUAL','Casual'),('ANNUAL','Annual'),('EMERGENCY','Emergency')]
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPES, default='CASUAL')
    start_date = models.DateField()
    end_date   = models.DateField()
    reason     = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_on = models.DateField(auto_now_add=True)
    def days(self):
        return (self.end_date - self.start_date).days + 1
    def __str__(self): return f"{self.employee.name} - {self.status}"
"""

# ─── VIEWS ────────────────────────────────────────────────────────────────────
files['employees/views.py'] = """from django.shortcuts import render, redirect
from .models import Employee, LeaveRequest

def login_view(request):
    if request.method == 'POST':
        try:
            user = Employee.objects.get(email=request.POST['email'], password=request.POST['password'])
            request.session['user_id'] = user.id
            request.session['role']    = user.role
            request.session['name']    = user.name
            return redirect('dashboard')
        except:
            return render(request, 'login.html', {'error': 'Invalid email or password'})
    return render(request, 'login.html')

def dashboard(request):
    if not request.session.get('user_id'):
        return redirect('login')
    uid      = request.session['user_id']
    role     = request.session['role']
    employee = Employee.objects.get(id=uid)
    my_leaves = LeaveRequest.objects.filter(employee_id=uid)

    if role == 'MANAGER':
        all_leaves   = LeaveRequest.objects.all().select_related('employee')
        all_employees = Employee.objects.filter(role='EMPLOYEE')
        pending   = all_leaves.filter(status='PENDING').count()
        approved  = all_leaves.filter(status='APPROVED').count()
        rejected  = all_leaves.filter(status='REJECTED').count()
        return render(request, 'dashboard.html', {
            'employee': employee, 'role': role,
            'all_leaves': all_leaves, 'all_employees': all_employees,
            'pending': pending, 'approved': approved, 'rejected': rejected,
            'total_emp': all_employees.count(),
        })
    else:
        approved  = my_leaves.filter(status='APPROVED').count()
        pending   = my_leaves.filter(status='PENDING').count()
        rejected  = my_leaves.filter(status='REJECTED').count()
        att_gap   = round(100 - employee.attendance_percent, 1)
        return render(request, 'dashboard.html', {
            'employee': employee, 'role': role,
            'my_leaves': my_leaves,
            'approved': approved, 'pending': pending,
            'rejected': rejected, 'att_gap': att_gap,
        })

def apply_leave(request):
    if not request.session.get('user_id'):
        return redirect('login')
    employee = Employee.objects.get(id=request.session['user_id'])
    if request.method == 'POST':
        LeaveRequest.objects.create(
            employee_id=request.session['user_id'],
            leave_type=request.POST.get('leave_type','CASUAL'),
            start_date=request.POST['start'],
            end_date=request.POST['end'],
            reason=request.POST['reason']
        )
        return redirect('dashboard')
    return render(request, 'apply_leave.html', {'employee': employee})

def update_status(request, id, status):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leave = LeaveRequest.objects.get(id=id)
    leave.status = status
    leave.save()
    if status == 'APPROVED':
        emp = leave.employee
        emp.attendance_percent = max(0, round(emp.attendance_percent - (leave.days() * 0.5), 1))
        emp.leave_balance      = max(0, emp.leave_balance - leave.days())
        emp.save()
    return redirect('dashboard')

def logout_view(request):
    request.session.flush()
    return redirect('login')
"""

# ─── URLS ─────────────────────────────────────────────────────────────────────
files['employees/urls.py'] = """from django.urls import path
from . import views
urlpatterns = [
    path('',                              views.login_view,    name='login'),
    path('dashboard/',                    views.dashboard,     name='dashboard'),
    path('apply/',                        views.apply_leave,   name='apply_leave'),
    path('update/<int:id>/<str:status>/', views.update_status, name='update_status'),
    path('logout/',                       views.logout_view,   name='logout'),
]
"""

files['employees/admin.py'] = """from django.contrib import admin
from .models import Employee, LeaveRequest
admin.site.register(Employee)
admin.site.register(LeaveRequest)
"""

files['leave_management/urls.py'] = """from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employees.urls')),
]
"""

# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
files['employees/templates/login.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LeaveFlow — Sign In</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;min-height:100vh;background:#0a0a1a;display:flex;overflow:hidden}
.left-panel{flex:1;position:relative;display:flex;flex-direction:column;justify-content:center;padding:60px;background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%);overflow:hidden}
.left-panel::before{content:'';position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")}
.blob{position:absolute;border-radius:50%;filter:blur(80px);opacity:0.15}
.blob1{width:500px;height:500px;background:#667eea;top:-100px;right:-100px}
.blob2{width:400px;height:400px;background:#764ba2;bottom:-80px;left:-80px}
.blob3{width:300px;height:300px;background:#f093fb;top:50%;left:50%;transform:translate(-50%,-50%)}
.brand-logo{display:flex;align-items:center;gap:14px;margin-bottom:60px;position:relative;z-index:1}
.logo-icon{width:52px;height:52px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:15px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(102,126,234,0.4)}
.logo-icon i{font-size:24px;color:white}
.logo-title{font-size:26px;font-weight:800;color:white;letter-spacing:-0.5px}
.logo-sub{font-size:12px;color:rgba(255,255,255,0.4);font-weight:400}
.hero-text{position:relative;z-index:1;margin-bottom:50px}
.hero-text h1{font-size:44px;font-weight:800;color:white;line-height:1.2;letter-spacing:-1px;margin-bottom:16px}
.hero-text h1 span{background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-text p{font-size:16px;color:rgba(255,255,255,0.5);line-height:1.7;max-width:380px}
.features{display:flex;flex-direction:column;gap:16px;position:relative;z-index:1}
.feature-item{display:flex;align-items:center;gap:14px}
.feat-icon{width:40px;height:40px;border-radius:11px;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.feat-icon i{font-size:16px;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.feat-text{font-size:14px;color:rgba(255,255,255,0.6)}
.feat-text strong{color:rgba(255,255,255,0.9);display:block;font-size:13px}
.right-panel{width:480px;background:#0d0d1f;display:flex;align-items:center;justify-content:center;padding:40px;border-left:1px solid rgba(255,255,255,0.05)}
.form-box{width:100%;max-width:380px}
.form-box h2{font-size:26px;font-weight:800;color:white;margin-bottom:6px;letter-spacing:-0.5px}
.form-box p{font-size:14px;color:rgba(255,255,255,0.4);margin-bottom:36px}
.field-wrap{margin-bottom:20px}
.field-label{font-size:12px;font-weight:600;color:rgba(255,255,255,0.5);margin-bottom:8px;display:block;text-transform:uppercase;letter-spacing:.06em}
.input-row{display:flex;align-items:center;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;transition:all 0.2s}
.input-row:focus-within{border-color:#667eea;background:rgba(102,126,234,0.07);box-shadow:0 0 0 3px rgba(102,126,234,0.15)}
.input-row .icon{width:48px;height:48px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.input-row .icon i{font-size:15px;color:rgba(255,255,255,0.25)}
.input-row input{flex:1;background:transparent;border:none;outline:none;color:white;font-size:14px;padding:14px 14px 14px 0;font-family:'Inter',sans-serif}
.input-row input::placeholder{color:rgba(255,255,255,0.2)}
.btn-signin{width:100%;padding:15px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;color:white;font-size:15px;font-weight:700;cursor:pointer;transition:all 0.3s;letter-spacing:0.3px;box-shadow:0 8px 24px rgba(102,126,234,0.35);font-family:'Inter',sans-serif;margin-top:8px}
.btn-signin:hover{transform:translateY(-2px);box-shadow:0 14px 32px rgba(102,126,234,0.5)}
.error-box{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);border-radius:11px;padding:12px 16px;font-size:13px;color:#fc8181;margin-bottom:22px;display:flex;align-items:center;gap:10px}
.divider{display:flex;align-items:center;gap:12px;margin:24px 0}
.divider span{font-size:11px;color:rgba(255,255,255,0.2);white-space:nowrap}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:rgba(255,255,255,0.06)}
.role-pills{display:flex;gap:10px}
.role-pill{flex:1;padding:11px;border-radius:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);text-align:center;cursor:pointer;transition:all 0.2s}
.role-pill:hover{background:rgba(102,126,234,0.1);border-color:rgba(102,126,234,0.3)}
.role-pill i{display:block;font-size:18px;margin-bottom:5px;color:rgba(255,255,255,0.4)}
.role-pill span{font-size:11px;color:rgba(255,255,255,0.4);font-weight:500}
.footer-note{text-align:center;font-size:11px;color:rgba(255,255,255,0.15);margin-top:28px}
</style>
</head>
<body>
<div class="left-panel">
  <div class="blob blob1"></div>
  <div class="blob blob2"></div>
  <div class="blob blob3"></div>
  <div class="brand-logo">
    <div class="logo-icon"><i class="fas fa-calendar-check"></i></div>
    <div><div class="logo-title">LeaveFlow</div><div class="logo-sub">Leave Management System</div></div>
  </div>
  <div class="hero-text">
    <h1>Manage Leave<br>The <span>Smart Way</span></h1>
    <p>A unified portal for employees and managers. Track attendance, apply for leave, and manage approvals — all in one place.</p>
  </div>
  <div class="features">
    <div class="feature-item"><div class="feat-icon"><i class="fas fa-chart-pie"></i></div><div class="feat-text"><strong>Live Attendance Tracking</strong>Real-time percentage per employee</div></div>
    <div class="feature-item"><div class="feat-icon"><i class="fas fa-layer-group"></i></div><div class="feat-text"><strong>Unified Dashboard</strong>One login for employee & manager</div></div>
    <div class="feature-item"><div class="feat-icon"><i class="fas fa-bolt"></i></div><div class="feat-text"><strong>Instant Approvals</strong>One-click approve or reject</div></div>
  </div>
</div>

<div class="right-panel">
  <div class="form-box">
    <h2>Welcome back</h2>
    <p>Sign in to your LeaveFlow account</p>
    {% if error %}<div class="error-box"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
    <form method="POST">
      {% csrf_token %}
      <div class="field-wrap">
        <label class="field-label">Email Address</label>
        <div class="input-row"><div class="icon"><i class="fas fa-envelope"></i></div><input type="email" name="email" placeholder="you@company.com" required></div>
      </div>
      <div class="field-wrap">
        <label class="field-label">Password</label>
        <div class="input-row"><div class="icon"><i class="fas fa-lock"></i></div><input type="password" name="password" placeholder="Enter your password" required></div>
      </div>
      <button type="submit" class="btn-signin"><i class="fas fa-arrow-right-to-bracket me-2"></i>Sign In to LeaveFlow</button>
    </form>
    <div class="divider"><span>Role auto-detected on login</span></div>
    <div class="role-pills">
      <div class="role-pill"><i class="fas fa-user-tie"></i><span>Employee</span></div>
      <div class="role-pill"><i class="fas fa-shield-halved"></i><span>Manager</span></div>
    </div>
    <div class="footer-note">© 2025 LeaveFlow · All rights reserved</div>
  </div>
</div>
</body>
</html>
"""

# ─── UNIFIED DASHBOARD ────────────────────────────────────────────────────────
files['employees/templates/dashboard.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LeaveFlow — Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f4f6fb;color:#1a1d2e}
/* SIDEBAR */
.sidebar{position:fixed;top:0;left:0;height:100vh;width:250px;background:linear-gradient(180deg,#0f0c29,#302b63);z-index:200;display:flex;flex-direction:column;box-shadow:4px 0 30px rgba(0,0,0,0.25)}
.sb-logo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:13px}
.sb-logo-icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sb-logo-icon.emp{background:linear-gradient(135deg,#667eea,#764ba2)}
.sb-logo-icon.mgr{background:linear-gradient(135deg,#f093fb,#f5576c)}
.sb-logo-icon i{color:white;font-size:18px}
.sb-title{color:white;font-size:16px;font-weight:700}
.sb-sub{color:rgba(255,255,255,0.35);font-size:10px;font-weight:400}
.sb-nav{flex:1;padding:16px 12px;overflow-y:auto}
.sb-section{font-size:10px;font-weight:600;color:rgba(255,255,255,0.22);text-transform:uppercase;letter-spacing:.08em;padding:12px 12px 6px}
.sb-link{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:2px;transition:all 0.2s;cursor:pointer}
.sb-link:hover{background:rgba(255,255,255,0.07);color:rgba(255,255,255,0.85)}
.sb-link.active{background:rgba(102,126,234,0.25);color:white}
.sb-link.active-mgr{background:rgba(240,147,251,0.2);color:white}
.sb-link i{width:18px;text-align:center;font-size:14px;flex-shrink:0}
.sb-badge{margin-left:auto;background:rgba(239,68,68,0.8);color:white;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px}
.sb-footer{padding:14px 12px;border-top:1px solid rgba(255,255,255,0.07)}
.sb-user{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:rgba(255,255,255,0.05)}
.sb-avatar{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700;color:white;flex-shrink:0}
.sb-avatar.emp{background:linear-gradient(135deg,#667eea,#764ba2)}
.sb-avatar.mgr{background:linear-gradient(135deg,#f093fb,#f5576c)}
.sb-uname{color:white;font-size:12px;font-weight:600}
.sb-urole{color:rgba(255,255,255,0.35);font-size:10px;text-transform:capitalize}
/* MAIN */
.main{margin-left:250px;min-height:100vh}
/* TOPBAR */
.topbar{background:white;padding:0 30px;height:64px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #eaedf5;position:sticky;top:0;z-index:100;box-shadow:0 1px 8px rgba(0,0,0,0.04)}
.tb-left{display:flex;flex-direction:column}
.tb-title{font-size:16px;font-weight:700;color:#1a1d2e}
.tb-sub{font-size:12px;color:#8a8ea8}
.tb-right{display:flex;align-items:center;gap:12px}
.tb-btn{display:inline-flex;align-items:center;gap:7px;padding:9px 18px;border-radius:10px;font-size:13px;font-weight:600;text-decoration:none;border:none;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif}
.tb-btn.primary{background:linear-gradient(135deg,#667eea,#764ba2);color:white;box-shadow:0 4px 14px rgba(102,126,234,0.3)}
.tb-btn.primary:hover{transform:translateY(-1px);box-shadow:0 8px 20px rgba(102,126,234,0.4);color:white}
.tb-btn.outline{background:white;color:#5a5f7a;border:1.5px solid #e4e7f0}
.tb-btn.outline:hover{background:#f4f6fb;color:#1a1d2e}
.role-tag{padding:5px 12px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.role-tag.emp{background:#eef0ff;color:#667eea}
.role-tag.mgr{background:#fde8ff;color:#9333ea}
/* CONTENT */
.content{padding:28px 30px}
/* WELCOME BANNER */
.welcome-banner{background:linear-gradient(135deg,#0f0c29,#302b63);border-radius:18px;padding:28px 32px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;overflow:hidden;position:relative}
.welcome-banner::before{content:'';position:absolute;right:-40px;top:-40px;width:200px;height:200px;border-radius:50%;background:rgba(102,126,234,0.15)}
.welcome-banner::after{content:'';position:absolute;right:60px;bottom:-60px;width:160px;height:160px;border-radius:50%;background:rgba(240,147,251,0.1)}
.wb-text h2{font-size:22px;font-weight:800;color:white;margin-bottom:6px}
.wb-text p{font-size:13px;color:rgba(255,255,255,0.5);max-width:400px}
.wb-chips{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}
.wb-chip{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:6px 12px;font-size:12px;color:rgba(255,255,255,0.7);display:flex;align-items:center;gap:6px}
.wb-chip i{font-size:11px;color:rgba(255,255,255,0.4)}
.wb-visual{position:relative;z-index:1;text-align:right}
.att-circle{width:100px;height:100px;position:relative}
.att-circle svg{transform:rotate(-90deg)}
.att-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.att-pct{font-size:22px;font-weight:800;color:white;line-height:1}
.att-lbl{font-size:9px;color:rgba(255,255,255,0.4);margin-top:2px}
/* STATS */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:white;border-radius:15px;padding:20px 22px;box-shadow:0 1px 8px rgba(0,0,0,0.05);position:relative;overflow:hidden;transition:transform 0.2s,box-shadow 0.2s}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,0.1)}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:3px 3px 0 0}
.sc1::before{background:linear-gradient(90deg,#667eea,#764ba2)}
.sc2::before{background:linear-gradient(90deg,#11998e,#38ef7d)}
.sc3::before{background:linear-gradient(90deg,#f7971e,#ffd200)}
.sc4::before{background:linear-gradient(90deg,#eb3349,#f45c43)}
.stat-val{font-size:32px;font-weight:800;color:#1a1d2e;line-height:1}
.stat-lbl{font-size:12px;color:#8a8ea8;font-weight:500;margin-top:5px}
.stat-icon-bg{position:absolute;right:16px;top:50%;transform:translateY(-50%);width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;opacity:0.08}
.sc1 .stat-icon-bg{background:#667eea}.sc2 .stat-icon-bg{background:#11998e}
.sc3 .stat-icon-bg{background:#f7971e}.sc4 .stat-icon-bg{background:#eb3349}
.stat-icon-bg i{font-size:26px;color:#1a1d2e}
.stat-trend{font-size:11px;margin-top:6px;display:flex;align-items:center;gap:4px}
/* GRID */
.grid-3-1{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
/* CARD */
.card-box{background:white;border-radius:15px;padding:22px 24px;box-shadow:0 1px 8px rgba(0,0,0,0.05)}
.card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.card-title-row{display:flex;align-items:center;gap:8px}
.card-icon{width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center}
.ci-blue{background:#eef0ff}.ci-blue i{color:#667eea}
.ci-green{background:#e8faf0}.ci-green i{color:#10b981}
.ci-purple{background:#fde8ff}.ci-purple i{color:#9333ea}
.ci-orange{background:#fff7e6}.ci-orange i{color:#f59e0b}
.card-icon i{font-size:14px}
.card-title{font-size:14px;font-weight:700;color:#1a1d2e}
.card-sub{font-size:11px;color:#8a8ea8;margin-top:1px}
/* TABLE */
.data-table{width:100%;border-collapse:collapse}
.data-table thead th{font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;padding:10px 12px;border-bottom:1px solid #f0f2f8;white-space:nowrap}
.data-table tbody td{padding:12px 12px;font-size:13px;color:#374151;border-bottom:1px solid #f9fafb;vertical-align:middle}
.data-table tbody tr:last-child td{border-bottom:none}
.data-table tbody tr:hover td{background:#f9fafb}
/* BADGES */
.badge-pill{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.bp{background:#fffbeb;color:#d97706}.ba{background:#ecfdf5;color:#059669}.br{background:#fef2f2;color:#dc2626}
.dept-badge{font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600;background:#eef0ff;color:#667eea}
.type-badge{font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600;background:#f3f4f6;color:#6b7280}
/* EMPLOYEE AVATAR */
.emp-row{display:flex;align-items:center;gap:10px}
.emp-av{width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:13px;flex-shrink:0;background:linear-gradient(135deg,#667eea,#764ba2)}
.emp-av.mgr-av{background:linear-gradient(135deg,#f093fb,#f5576c)}
.emp-name{font-weight:600;font-size:13px;color:#1a1d2e}
.emp-email{font-size:11px;color:#9ca3af}
/* ACTION BTNS */
.act-btn{display:inline-flex;align-items:center;gap:5px;padding:6px 12px;border-radius:8px;font-size:11px;font-weight:600;text-decoration:none;border:none;cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.15s}
.act-approve{background:#ecfdf5;color:#059669}.act-approve:hover{background:#059669;color:white}
.act-reject{background:#fef2f2;color:#dc2626;margin-left:6px}.act-reject:hover{background:#dc2626;color:white}
/* ATTENDANCE */
.att-bar-wrap{margin-top:5px}
.att-num{font-size:13px;font-weight:700;color:#1a1d2e}
.att-bar{height:6px;border-radius:3px;background:#f3f4f6;margin-top:4px;overflow:hidden}
.att-fill{height:100%;border-radius:3px;transition:width 1s ease}
.att-fill.excellent{background:linear-gradient(90deg,#11998e,#38ef7d)}
.att-fill.average{background:linear-gradient(90deg,#f7971e,#ffd200)}
.att-fill.poor{background:linear-gradient(90deg,#eb3349,#f45c43)}
.att-status{font-size:10px;font-weight:600;margin-top:3px}
.att-status.excellent{color:#059669}.att-status.average{color:#d97706}.att-status.poor{color:#dc2626}
/* MINI CHART INSIDE CARD */
.chart-wrap{position:relative;height:200px;display:flex;align-items:center;justify-content:center}
/* LEAVE TYPE LEGEND */
.legend-list{display:flex;flex-direction:column;gap:9px;margin-top:14px}
.legend-item{display:flex;align-items:center;justify-content:space-between;font-size:12px}
.legend-dot{width:10px;height:10px;border-radius:3px;flex-shrink:0;margin-right:8px}
.legend-label{display:flex;align-items:center;color:#6b7280}
.legend-val{font-weight:700;color:#1a1d2e}
/* PROGRESS CIRCLES */
.prog-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px}
.prog-item{text-align:center;background:#f9fafb;border-radius:12px;padding:16px 10px}
.prog-num{font-size:24px;font-weight:800;color:#1a1d2e}
.prog-lbl{font-size:11px;color:#9ca3af;margin-top:3px}
.prog-bar{height:5px;border-radius:3px;background:#f0f2f8;margin-top:8px}
.prog-bar-fill{height:100%;border-radius:3px}
/* EMPTY STATE */
.empty-state{text-align:center;padding:40px 20px;color:#9ca3af}
.empty-state i{font-size:40px;opacity:0.3;margin-bottom:12px}
.empty-state p{font-size:13px}
/* TAG */
.section-title{font-size:17px;font-weight:700;color:#1a1d2e;margin-bottom:4px}
.section-sub{font-size:13px;color:#9ca3af;margin-bottom:20px}
/* NOTIFICATION DOT */
.notif{width:8px;height:8px;background:#ef4444;border-radius:50%;flex-shrink:0}
/* SCROLLABLE TABLE */
.table-scroll{overflow-x:auto}
/* DIVIDER */
.divider-h{height:1px;background:#f0f2f8;margin:18px 0}
</style>
</head>
<body>

<!-- SIDEBAR -->
<div class="sidebar">
  <div class="sb-logo">
    <div class="sb-logo-icon {% if role == 'MANAGER' %}mgr{% else %}emp{% endif %}">
      <i class="fas {% if role == 'MANAGER' %}fa-shield-halved{% else %}fa-calendar-check{% endif %}"></i>
    </div>
    <div>
      <div class="sb-title">LeaveFlow</div>
      <div class="sb-sub">{% if role == 'MANAGER' %}Manager Panel{% else %}Employee Portal{% endif %}</div>
    </div>
  </div>

  <nav class="sb-nav">
    <div class="sb-section">Main</div>
    <a href="{% url 'dashboard' %}" class="sb-link {% if role == 'MANAGER' %}active-mgr{% else %}active{% endif %}">
      <i class="fas fa-th-large"></i>Dashboard
    </a>
    {% if role == 'EMPLOYEE' %}
    <a href="{% url 'apply_leave' %}" class="sb-link"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    {% endif %}

    {% if role == 'MANAGER' %}
    <div class="sb-section">Management</div>
    <a href="#requests-section" class="sb-link"><i class="fas fa-inbox"></i>Leave Requests{% if pending %}<span class="sb-badge">{{ pending }}</span>{% endif %}</a>
    <a href="#team-section" class="sb-link"><i class="fas fa-users"></i>Team Attendance</a>
    {% endif %}

    <div class="sb-section">Account</div>
    <a href="{% url 'logout' %}" class="sb-link"><i class="fas fa-right-from-bracket"></i>Sign Out</a>
  </nav>

  <div class="sb-footer">
    <div class="sb-user">
      <div class="sb-avatar {% if role == 'MANAGER' %}mgr{% else %}emp{% endif %}">{{ employee.name|first }}</div>
      <div>
        <div class="sb-uname">{{ employee.name }}</div>
        <div class="sb-urole">{{ role|lower }} · {{ employee.department }}</div>
      </div>
    </div>
  </div>
</div>

<!-- MAIN -->
<div class="main">
  <!-- TOPBAR -->
  <div class="topbar">
    <div class="tb-left">
      <div class="tb-title">
        {% if role == 'MANAGER' %}Manager Dashboard{% else %}My Dashboard{% endif %}
      </div>
      <div class="tb-sub">{% now "l, N j, Y" %}</div>
    </div>
    <div class="tb-right">
      <span class="role-tag {% if role == 'MANAGER' %}mgr{% else %}emp{% endif %}">
        <i class="fas {% if role == 'MANAGER' %}fa-shield-halved{% else %}fa-user{% endif %} me-1"></i>{{ role|title }}
      </span>
      {% if role == 'EMPLOYEE' %}
      <a href="{% url 'apply_leave' %}" class="tb-btn primary"><i class="fas fa-plus"></i>Apply Leave</a>
      {% endif %}
      <a href="{% url 'logout' %}" class="tb-btn outline"><i class="fas fa-right-from-bracket"></i>Logout</a>
    </div>
  </div>

  <!-- CONTENT -->
  <div class="content">

    <!-- WELCOME BANNER -->
    <div class="welcome-banner">
      <div class="wb-text">
        <h2>Hello, {{ employee.name }} 👋</h2>
        <p>{% if role == 'MANAGER' %}You have {{ pending }} pending leave request{{ pending|pluralize }} awaiting your approval.{% else %}You have {{ employee.leave_balance }} leave days remaining. Your attendance stands at {{ employee.attendance_percent }}%.{% endif %}</p>
        <div class="wb-chips">
          <div class="wb-chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
          <div class="wb-chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
          {% if role == 'EMPLOYEE' %}<div class="wb-chip"><i class="fas fa-suitcase"></i>{{ employee.leave_balance }} days left</div>{% endif %}
          {% if role == 'MANAGER' %}<div class="wb-chip"><i class="fas fa-users"></i>{{ total_emp }} team member{{ total_emp|pluralize }}</div>{% endif %}
        </div>
      </div>
      <div class="wb-visual">
        <div class="att-circle">
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="8"/>
            <circle cx="50" cy="50" r="42" fill="none" stroke="url(#grad)" stroke-width="8" stroke-linecap="round"
              stroke-dasharray="{{ employee.attendance_percent|floatformat:0 }} 264" style="stroke-dasharray:calc({{ employee.attendance_percent }} * 2.64px) 264px"/>
            <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#667eea"/><stop offset="100%" stop-color="#f093fb"/></linearGradient></defs>
          </svg>
          <div class="att-center"><div class="att-pct">{{ employee.attendance_percent }}%</div><div class="att-lbl">Attendance</div></div>
        </div>
      </div>
    </div>

    <!-- STATS ROW -->
    <div class="stats-row">
      {% if role == 'EMPLOYEE' %}
      <div class="stat-card sc1"><div class="stat-val">{{ my_leaves.count }}</div><div class="stat-lbl">Total Requests</div><div class="stat-icon-bg"><i class="fas fa-file-lines"></i></div></div>
      <div class="stat-card sc2"><div class="stat-val">{{ approved }}</div><div class="stat-lbl">Approved</div><div class="stat-icon-bg"><i class="fas fa-check-circle"></i></div></div>
      <div class="stat-card sc3"><div class="stat-val">{{ pending }}</div><div class="stat-lbl">Pending</div><div class="stat-icon-bg"><i class="fas fa-hourglass-half"></i></div></div>
      <div class="stat-card sc4"><div class="stat-val">{{ rejected }}</div><div class="stat-lbl">Rejected</div><div class="stat-icon-bg"><i class="fas fa-times-circle"></i></div></div>
      {% else %}
      <div class="stat-card sc1"><div class="stat-val">{{ total_emp }}</div><div class="stat-lbl">Total Employees</div><div class="stat-icon-bg"><i class="fas fa-users"></i></div></div>
      <div class="stat-card sc2"><div class="stat-val">{{ approved }}</div><div class="stat-lbl">Approved</div><div class="stat-icon-bg"><i class="fas fa-check-circle"></i></div></div>
      <div class="stat-card sc3"><div class="stat-val">{{ pending }}</div><div class="stat-lbl">Pending Approval</div><div class="stat-icon-bg"><i class="fas fa-hourglass-half"></i></div></div>
      <div class="stat-card sc4"><div class="stat-val">{{ rejected }}</div><div class="stat-lbl">Rejected</div><div class="stat-icon-bg"><i class="fas fa-times-circle"></i></div></div>
      {% endif %}
    </div>

    <!-- CHARTS + TABLE ROW -->
    <div class="grid-3-1">
      {% if role == 'EMPLOYEE' %}
      <!-- MY LEAVE TABLE -->
      <div class="card-box">
        <div class="card-head">
          <div class="card-title-row"><div class="card-icon ci-blue"><i class="fas fa-history"></i></div><div><div class="card-title">My Leave History</div><div class="card-sub">All your submitted requests</div></div></div>
        </div>
        <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Applied</th><th>Status</th></tr></thead>
          <tbody>
          {% for leave in my_leaves %}
          <tr>
            <td><span class="type-badge">{{ leave.leave_type }}</span></td>
            <td>{{ leave.start_date }}</td><td>{{ leave.end_date }}</td>
            <td><strong>{{ leave.days }}</strong></td>
            <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ leave.reason }}</td>
            <td>{{ leave.applied_on }}</td>
            <td>{% if leave.status == 'APPROVED' %}<span class="badge-pill ba"><i class="fas fa-check"></i>Approved</span>
                {% elif leave.status == 'REJECTED' %}<span class="badge-pill br"><i class="fas fa-times"></i>Rejected</span>
                {% else %}<span class="badge-pill bp"><i class="fas fa-clock"></i>Pending</span>{% endif %}</td>
          </tr>
          {% empty %}
          <tr><td colspan="7"><div class="empty-state"><i class="fas fa-calendar-xmark"></i><p>No leave requests yet.<br>Click Apply for Leave to get started.</p></div></td></tr>
          {% endfor %}
          </tbody>
        </table>
        </div>
      </div>

      {% else %}
      <!-- MANAGER: ALL REQUESTS TABLE -->
      <div class="card-box" id="requests-section">
        <div class="card-head">
          <div class="card-title-row"><div class="card-icon ci-purple"><i class="fas fa-inbox"></i></div><div><div class="card-title">All Leave Requests</div><div class="card-sub">Review and take action</div></div></div>
        </div>
        <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Employee</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
          {% for leave in all_leaves %}
          <tr>
            <td><div class="emp-row"><div class="emp-av">{{ leave.employee.name|first }}</div><div><div class="emp-name">{{ leave.employee.name }}</div><div class="emp-email">{{ leave.employee.department }}</div></div></div></td>
            <td><span class="type-badge">{{ leave.leave_type }}</span></td>
            <td>{{ leave.start_date }}</td><td>{{ leave.end_date }}</td>
            <td><strong>{{ leave.days }}</strong></td>
            <td>{% if leave.status == 'APPROVED' %}<span class="badge-pill ba"><i class="fas fa-check"></i>Approved</span>
                {% elif leave.status == 'REJECTED' %}<span class="badge-pill br"><i class="fas fa-times"></i>Rejected</span>
                {% else %}<span class="badge-pill bp"><i class="fas fa-clock"></i>Pending</span>{% endif %}</td>
            <td>{% if leave.status == 'PENDING' %}
              <a href="{% url 'update_status' leave.id 'APPROVED' %}" class="act-btn act-approve"><i class="fas fa-check"></i>Approve</a>
              <a href="{% url 'update_status' leave.id 'REJECTED' %}" class="act-btn act-reject"><i class="fas fa-times"></i>Reject</a>
            {% else %}<span style="font-size:11px;color:#d1d5db">Done</span>{% endif %}</td>
          </tr>
          {% empty %}
          <tr><td colspan="7"><div class="empty-state"><i class="fas fa-inbox"></i><p>No leave requests yet.</p></div></td></tr>
          {% endfor %}
          </tbody>
        </table>
        </div>
      </div>
      {% endif %}

      <!-- CHART CARD -->
      <div class="card-box">
        <div class="card-head">
          <div class="card-title-row"><div class="card-icon ci-green"><i class="fas fa-chart-pie"></i></div><div><div class="card-title">Leave Breakdown</div></div></div>
        </div>
        <div class="chart-wrap"><canvas id="donut"></canvas></div>
        <div class="legend-list">
          <div class="legend-item"><div class="legend-label"><div class="legend-dot" style="background:#059669"></div>Approved</div><div class="legend-val">{{ approved }}</div></div>
          <div class="legend-item"><div class="legend-label"><div class="legend-dot" style="background:#d97706"></div>Pending</div><div class="legend-val">{{ pending }}</div></div>
          <div class="legend-item"><div class="legend-label"><div class="legend-dot" style="background:#dc2626"></div>Rejected</div><div class="legend-val">{{ rejected }}</div></div>
        </div>
        {% if role == 'EMPLOYEE' %}
        <div class="divider-h"></div>
        <div class="prog-grid">
          <div class="prog-item"><div class="prog-num">{{ employee.attendance_percent }}%</div><div class="prog-lbl">Attendance</div><div class="prog-bar"><div class="prog-bar-fill" style="width:{{ employee.attendance_percent }}%;background:linear-gradient(90deg,#667eea,#764ba2)"></div></div></div>
          <div class="prog-item"><div class="prog-num">{{ employee.leave_balance }}</div><div class="prog-lbl">Days Left</div><div class="prog-bar"><div class="prog-bar-fill" style="width:{{ employee.leave_balance }}%;background:linear-gradient(90deg,#11998e,#38ef7d)"></div></div></div>
        </div>
        {% endif %}
      </div>
    </div>

    <!-- MANAGER: EMPLOYEE ATTENDANCE TABLE -->
    {% if role == 'MANAGER' %}
    <div class="card-box" id="team-section">
      <div class="card-head">
        <div class="card-title-row"><div class="card-icon ci-orange"><i class="fas fa-chart-bar"></i></div><div><div class="card-title">Team Attendance Tracker</div><div class="card-sub">Live attendance percentage per employee</div></div></div>
      </div>
      <div class="table-scroll">
      <table class="data-table">
        <thead><tr><th>Employee</th><th>Department</th><th>Email</th><th>Leave Balance</th><th style="min-width:180px">Attendance</th><th>Rating</th></tr></thead>
        <tbody>
        {% for emp in all_employees %}
        <tr>
          <td><div class="emp-row"><div class="emp-av">{{ emp.name|first }}</div><div><div class="emp-name">{{ emp.name }}</div><div class="emp-email">Joined {{ emp.joined_date }}</div></div></div></td>
          <td><span class="dept-badge">{{ emp.department }}</span></td>
          <td style="font-size:12px;color:#9ca3af">{{ emp.email }}</td>
          <td><strong>{{ emp.leave_balance }}</strong> <span style="font-size:11px;color:#9ca3af">days</span></td>
          <td>
            <div class="att-bar-wrap">
              <div class="att-num">{{ emp.attendance_percent }}%</div>
              <div class="att-bar"><div class="att-fill {% if emp.attendance_percent >= 90 %}excellent{% elif emp.attendance_percent >= 75 %}average{% else %}poor{% endif %}" style="width:{{ emp.attendance_percent }}%"></div></div>
            </div>
          </td>
          <td>
            {% if emp.attendance_percent >= 90 %}<span class="att-status excellent"><i class="fas fa-circle-check me-1"></i>Excellent</span>
            {% elif emp.attendance_percent >= 75 %}<span class="att-status average"><i class="fas fa-circle-exclamation me-1"></i>Average</span>
            {% else %}<span class="att-status poor"><i class="fas fa-circle-xmark me-1"></i>Poor</span>{% endif %}
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="6"><div class="empty-state"><i class="fas fa-users"></i><p>No employees yet.</p></div></td></tr>
        {% endfor %}
        </tbody>
      </table>
      </div>
    </div>
    {% endif %}

  </div><!-- /content -->
</div><!-- /main -->

<script>
new Chart(document.getElementById('donut').getContext('2d'),{
  type:'doughnut',
  data:{
    labels:['Approved','Pending','Rejected'],
    datasets:[{
      data:[{{ approved }},{{ pending }},{{ rejected }}],
      backgroundColor:['#059669','#d97706','#dc2626'],
      borderWidth:0, hoverOffset:8
    }]
  },
  options:{
    responsive:true,
    plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return ' '+c.label+': '+c.raw}}}},
    cutout:'70%'
  }
});
</script>
</body>
</html>
"""

# ─── APPLY LEAVE PAGE ─────────────────────────────────────────────────────────
files['employees/templates/apply_leave.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow — Apply for Leave</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f4f6fb;color:#1a1d2e}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:250px;background:linear-gradient(180deg,#0f0c29,#302b63);z-index:200;display:flex;flex-direction:column;box-shadow:4px 0 30px rgba(0,0,0,0.25)}
.sb-logo{padding:24px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:13px}
.sb-logo-icon{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center}
.sb-logo-icon i{color:white;font-size:18px}
.sb-title{color:white;font-size:16px;font-weight:700}.sb-sub{color:rgba(255,255,255,0.35);font-size:10px}
.sb-nav{flex:1;padding:16px 12px}
.sb-section{font-size:10px;font-weight:600;color:rgba(255,255,255,0.22);text-transform:uppercase;letter-spacing:.08em;padding:12px 12px 6px}
.sb-link{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:10px;color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:2px;transition:all 0.2s}
.sb-link:hover{background:rgba(255,255,255,0.07);color:rgba(255,255,255,0.85)}
.sb-link.active{background:rgba(102,126,234,0.25);color:white}
.sb-link i{width:18px;text-align:center;font-size:14px}
.main{margin-left:250px;padding:40px}
.page-header{margin-bottom:28px}
.page-header h1{font-size:22px;font-weight:800;color:#1a1d2e;margin-bottom:4px}
.page-header p{font-size:13px;color:#9ca3af}
.form-card{background:white;border-radius:18px;box-shadow:0 4px 20px rgba(0,0,0,0.06);overflow:hidden;max-width:700px}
.form-card-header{padding:24px 30px;background:linear-gradient(135deg,#0f0c29,#302b63);display:flex;align-items:center;gap:14px}
.form-card-header i{font-size:22px;color:white;opacity:0.8}
.form-card-header h2{font-size:16px;font-weight:700;color:white;margin:0}
.form-card-header p{font-size:12px;color:rgba(255,255,255,0.4);margin:2px 0 0}
.form-body{padding:30px}
.field-group{margin-bottom:22px}
.field-label{font-size:12px;font-weight:600;color:#374151;margin-bottom:8px;display:flex;align-items:center;gap:7px;text-transform:uppercase;letter-spacing:.05em}
.field-label i{color:#667eea;font-size:11px}
.form-control,.form-select{border:1.5px solid #e5e7eb;border-radius:11px;padding:12px 14px;font-size:14px;color:#1a1d2e;font-family:'Inter',sans-serif;transition:all 0.2s;background:#fafafa;width:100%}
.form-control:focus,.form-select:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);background:white}
textarea.form-control{resize:vertical;min-height:110px}
.date-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.type-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.type-opt{display:none}
.type-lbl{display:flex;align-items:center;gap:10px;padding:13px 16px;border-radius:11px;border:1.5px solid #e5e7eb;cursor:pointer;transition:all 0.2s;font-size:13px;font-weight:500;color:#6b7280;background:#fafafa}
.type-lbl:hover{border-color:#667eea;color:#667eea;background:#f0f0ff}
.type-opt:checked + .type-lbl{border-color:#667eea;background:#eef0ff;color:#667eea;font-weight:600}
.type-lbl i{font-size:16px;opacity:0.7}
.form-actions{display:flex;align-items:center;gap:12px;margin-top:8px;padding-top:20px;border-top:1px solid #f3f4f6}
.btn-submit{display:inline-flex;align-items:center;gap:8px;padding:13px 28px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:11px;font-size:14px;font-weight:700;cursor:pointer;transition:all 0.2s;box-shadow:0 6px 18px rgba(102,126,234,0.3);font-family:'Inter',sans-serif}
.btn-submit:hover{transform:translateY(-2px);box-shadow:0 10px 26px rgba(102,126,234,0.45)}
.btn-back{display:inline-flex;align-items:center;gap:7px;padding:13px 20px;background:#f3f4f6;color:#6b7280;border:none;border-radius:11px;font-size:14px;font-weight:600;text-decoration:none;transition:all 0.2s;font-family:'Inter',sans-serif}
.btn-back:hover{background:#e5e7eb;color:#374151}
.info-strip{background:#f0f4ff;border:1px solid #dde3ff;border-radius:11px;padding:13px 16px;margin-bottom:22px;font-size:13px;color:#4f5fa3;display:flex;align-items:center;gap:10px}
.info-strip i{font-size:15px;color:#667eea;flex-shrink:0}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sb-logo">
    <div class="sb-logo-icon"><i class="fas fa-calendar-check"></i></div>
    <div><div class="sb-title">LeaveFlow</div><div class="sb-sub">Employee Portal</div></div>
  </div>
  <nav class="sb-nav">
    <div class="sb-section">Menu</div>
    <a href="{% url 'dashboard' %}" class="sb-link"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="sb-link active"><i class="fas fa-plus-circle"></i>Apply for Leave</a>
    <div class="sb-section">Account</div>
    <a href="{% url 'logout' %}" class="sb-link"><i class="fas fa-right-from-bracket"></i>Sign Out</a>
  </nav>
</div>

<div class="main">
  <div class="page-header">
    <h1>Apply for Leave</h1>
    <p>Submit a leave request — your manager will be notified for approval.</p>
  </div>

  <div class="form-card">
    <div class="form-card-header">
      <i class="fas fa-paper-plane"></i>
      <div><h2>New Leave Request</h2><p>Fill in all the details below and submit</p></div>
    </div>
    <div class="form-body">
      <div class="info-strip"><i class="fas fa-circle-info"></i>You currently have <strong style="margin:0 4px">{{ employee.leave_balance }} days</strong> of leave balance remaining.</div>

      <form method="POST">
        {% csrf_token %}
        <div class="field-group">
          <label class="field-label"><i class="fas fa-tag"></i>Leave Type</label>
          <div class="type-grid">
            <div><input type="radio" name="leave_type" value="CASUAL" id="t1" class="type-opt" checked><label for="t1" class="type-lbl"><i class="fas fa-mug-hot"></i>Casual Leave</label></div>
            <div><input type="radio" name="leave_type" value="SICK" id="t2" class="type-opt"><label for="t2" class="type-lbl"><i class="fas fa-heart-pulse"></i>Sick Leave</label></div>
            <div><input type="radio" name="leave_type" value="ANNUAL" id="t3" class="type-opt"><label for="t3" class="type-lbl"><i class="fas fa-umbrella-beach"></i>Annual Leave</label></div>
            <div><input type="radio" name="leave_type" value="EMERGENCY" id="t4" class="type-opt"><label for="t4" class="type-lbl"><i class="fas fa-triangle-exclamation"></i>Emergency</label></div>
          </div>
        </div>

        <div class="field-group date-row">
          <div>
            <label class="field-label"><i class="fas fa-calendar-day"></i>Start Date</label>
            <input type="date" name="start" class="form-control" required>
          </div>
          <div>
            <label class="field-label"><i class="fas fa-calendar-day"></i>End Date</label>
            <input type="date" name="end" class="form-control" required>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label"><i class="fas fa-comment-lines"></i>Reason for Leave</label>
          <textarea name="reason" class="form-control" placeholder="Briefly describe why you need this leave..." required></textarea>
        </div>

        <div class="form-actions">
          <a href="{% url 'dashboard' %}" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
          <button type="submit" class="btn-submit"><i class="fas fa-paper-plane"></i>Submit Request</button>
        </div>
      </form>
    </div>
  </div>
</div>
</body>
</html>
"""

for filepath, content in files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Created:', filepath)

print('\n ALL FILES CREATED SUCCESSFULLY — now run:')
print('  python manage.py makemigrations')
print('  python manage.py migrate')
print('  python manage.py runserver')