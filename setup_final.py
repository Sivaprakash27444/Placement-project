import os
os.makedirs('employees/templates', exist_ok=True)

files = {}

files['employees/views.py'] = """from django.shortcuts import render, redirect
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
    return render(request, 'employee_dashboard.html', {
        'employee': employee, 'leaves': leaves,
        'approved': approved, 'pending': pending,
        'rejected': rejected,
        'attendance_gap': attendance_gap,
        'leave_used': leave_used,
    })

def manager_dashboard(request):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    leaves = LeaveRequest.objects.all().select_related('employee').order_by('-applied_on')
    # Show ALL non-manager employees
    employees = Employee.objects.filter(role='EMPLOYEE')
    pending_count = leaves.filter(status='PENDING').count()
    approved_count = leaves.filter(status='APPROVED').count()
    rejected_count = leaves.filter(status='REJECTED').count()
    total_leaves = leaves.count()
    # Attendance stats
    total_emp = employees.count()
    excellent = employees.filter(attendance_percent__gte=90).count()
    average = employees.filter(attendance_percent__gte=75, attendance_percent__lt=90).count()
    poor = employees.filter(attendance_percent__lt=75).count()
    return render(request, 'manager_dashboard.html', {
        'leaves': leaves, 'employees': employees,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_leaves': total_leaves,
        'total_emp': total_emp,
        'excellent': excellent,
        'average': average,
        'poor': poor,
        'name': request.session.get('name'),
    })

def apply_leave(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    if request.method == 'POST':
        LeaveRequest.objects.create(
            employee_id=request.session.get('user_id'),
            leave_type=request.POST.get('leave_type', 'CASUAL'),
            start_date=request.POST['start'],
            end_date=request.POST['end'],
            reason=request.POST['reason']
        )
        return redirect('employee_dashboard')
    uid = request.session.get('user_id')
    employee = Employee.objects.get(id=uid)
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
        emp.attendance_percent = max(0, round(emp.attendance_percent - (days * 0.5), 1))
        emp.leave_balance = max(0, emp.leave_balance - days)
        emp.save()
    return redirect('manager_dashboard')

def update_attendance(request, emp_id):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    if request.method == 'POST':
        emp = Employee.objects.get(id=emp_id)
        emp.attendance_percent = float(request.POST.get('attendance_percent', emp.attendance_percent))
        emp.leave_balance = int(request.POST.get('leave_balance', emp.leave_balance))
        emp.save()
    return redirect('manager_dashboard')

def logout_view(request):
    request.session.flush()
    return redirect('login')
"""

files['employees/urls.py'] = """from django.urls import path
from . import views
urlpatterns = [
    path('', views.login_view, name='login'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('apply/', views.apply_leave, name='apply_leave'),
    path('update/<int:id>/<str:status>/', views.update_status, name='update_status'),
    path('update-attendance/<int:emp_id>/', views.update_attendance, name='update_attendance'),
    path('logout/', views.logout_view, name='logout'),
]
"""

files['employees/templates/login.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeaveFlow - Sign In</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;min-height:100vh;background:#0a0a1a;display:flex;overflow:hidden}
.left{flex:1;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px;position:relative;overflow:hidden}
.left::before{content:'';position:absolute;top:-20%;left:-10%;width:500px;height:500px;background:radial-gradient(circle,rgba(102,126,234,0.18),transparent 70%);border-radius:50%}
.left::after{content:'';position:absolute;bottom:-10%;right:-5%;width:400px;height:400px;background:radial-gradient(circle,rgba(118,75,162,0.14),transparent 70%);border-radius:50%}
.brand-logo{width:80px;height:80px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:24px;display:flex;align-items:center;justify-content:center;box-shadow:0 20px 60px rgba(102,126,234,0.45);margin-bottom:24px;position:relative;z-index:1;animation:float 3s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.brand-logo i{font-size:38px;color:white}
.brand-name{font-size:44px;font-weight:900;color:white;letter-spacing:-1.5px;position:relative;z-index:1}
.brand-name span{background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-tagline{font-size:15px;color:rgba(255,255,255,0.45);margin-top:10px;text-align:center;max-width:340px;line-height:1.7;position:relative;z-index:1}
.features{margin-top:44px;width:100%;max-width:360px;position:relative;z-index:1}
.feat{display:flex;align-items:center;gap:14px;padding:14px 18px;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);margin-bottom:10px}
.feat-ic{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
.f1{background:rgba(102,126,234,0.2);color:#a78bfa}
.f2{background:rgba(16,185,129,0.2);color:#6ee7b7}
.f3{background:rgba(245,158,11,0.2);color:#fcd34d}
.f4{background:rgba(239,68,68,0.2);color:#fca5a5}
.feat-txt{color:rgba(255,255,255,0.7);font-size:13px;font-weight:500}
.right{width:500px;background:#fff;display:flex;align-items:center;justify-content:center;padding:60px 50px;box-shadow:-20px 0 60px rgba(0,0,0,0.25)}
.login-box{width:100%}
.login-title{font-size:30px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.login-sub{font-size:14px;color:#94a3b8;margin-top:6px;margin-bottom:34px}
.flabel{font-size:11px;font-weight:700;color:#374151;margin-bottom:8px;display:block;text-transform:uppercase;letter-spacing:.06em}
.input-wrap{position:relative;margin-bottom:18px}
.input-ic{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:#94a3b8;font-size:13px}
.finput{width:100%;padding:13px 13px 13px 40px;border:1.5px solid #e2e8f0;border-radius:12px;font-size:14px;color:#0f172a;background:#fafafa;outline:none;font-family:'Inter',sans-serif;transition:all .2s}
.finput:focus{border-color:#667eea;background:white;box-shadow:0 0 0 4px rgba(102,126,234,0.1)}
.btn-sign{width:100%;padding:14px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;color:white;font-size:15px;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;box-shadow:0 8px 24px rgba(102,126,234,0.35);transition:all .25s;letter-spacing:.2px}
.btn-sign:hover{transform:translateY(-2px);box-shadow:0 14px 32px rgba(102,126,234,0.5)}
.err{background:#fff1f2;border:1.5px solid #fecdd3;border-radius:12px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#e11d48;font-weight:500;display:flex;align-items:center;gap:9px}
.divider{display:flex;align-items:center;gap:12px;margin:22px 0;color:#e2e8f0;font-size:11px;color:#cbd5e1}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:#e2e8f0}
.demo-cards{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.demo-card{padding:12px;border:1.5px solid #e2e8f0;border-radius:11px;text-align:center;background:#fafafa;cursor:pointer;transition:all .2s}
.demo-card:hover{border-color:#667eea;background:#f5f3ff}
.demo-card i{font-size:22px;margin-bottom:6px;display:block;color:#94a3b8}
.demo-card .role{font-size:12px;font-weight:700;color:#374151}
.demo-card .creds{font-size:11px;color:#94a3b8;margin-top:3px}
.footer{text-align:center;font-size:11px;color:#cbd5e1;margin-top:24px}
</style>
</head>
<body>
<div class="left">
  <div class="brand-logo"><i class="fas fa-calendar-check"></i></div>
  <div class="brand-name">Leave<span>Flow</span></div>
  <div class="brand-tagline">The complete leave management platform — track attendance, manage approvals, and empower your team.</div>
  <div class="features">
    <div class="feat"><div class="feat-ic f1"><i class="fas fa-shield-alt"></i></div><div class="feat-txt">Role-based Manager & Employee Portals</div></div>
    <div class="feat"><div class="feat-ic f2"><i class="fas fa-chart-pie"></i></div><div class="feat-txt">Live Attendance Tracking & Analytics</div></div>
    <div class="feat"><div class="feat-ic f3"><i class="fas fa-bolt"></i></div><div class="feat-txt">One-click Leave Approvals</div></div>
    <div class="feat"><div class="feat-ic f4"><i class="fas fa-sliders-h"></i></div><div class="feat-txt">Inline Attendance Editing for Managers</div></div>
  </div>
</div>
<div class="right">
  <div class="login-box">
    <div class="login-title">Welcome back 👋</div>
    <div class="login-sub">Sign in to your LeaveFlow account</div>
    {% if error %}<div class="err"><i class="fas fa-exclamation-circle"></i>{{ error }}</div>{% endif %}
    <form method="POST" id="loginForm">
      {% csrf_token %}
      <div><label class="flabel">Email Address</label></div>
      <div class="input-wrap">
        <i class="fas fa-envelope input-ic"></i>
        <input type="email" name="email" id="emailField" class="finput" placeholder="you@company.com" required>
      </div>
      <div><label class="flabel">Password</label></div>
      <div class="input-wrap">
        <i class="fas fa-lock input-ic"></i>
        <input type="password" name="password" id="passField" class="finput" placeholder="Enter your password" required>
      </div>
      <button type="submit" class="btn-sign"><i class="fas fa-sign-in-alt me-2"></i>Sign In to LeaveFlow</button>
    </form>
    <div class="divider">Quick Demo Login</div>
    <div class="demo-cards">
      <div class="demo-card" onclick="fillDemo('john@test.com','test123')">
        <i class="fas fa-user"></i>
        <div class="role">Employee</div>
        <div class="creds">john@test.com</div>
      </div>
      <div class="demo-card" onclick="fillDemo('sarah@test.com','test123')">
        <i class="fas fa-user-shield"></i>
        <div class="role">Manager</div>
        <div class="creds">sarah@test.com</div>
      </div>
    </div>
    <div class="footer">LeaveFlow &copy; 2025 &middot; Password: test123</div>
  </div>
</div>
<script>
function fillDemo(email, pass){
  document.getElementById('emailField').value = email;
  document.getElementById('passField').value = pass;
  document.getElementById('loginForm').submit();
}
</script>
</body>
</html>
"""

files['employees/templates/employee_dashboard.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - My Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f1f5f9;display:flex;min-height:100vh}
.sidebar{width:260px;background:linear-gradient(180deg,#0f172a,#1e1b4b);min-height:100vh;position:fixed;top:0;left:0;bottom:0;display:flex;flex-direction:column;z-index:50;box-shadow:4px 0 24px rgba(0,0,0,0.2)}
.s-header{padding:22px 20px;border-bottom:1px solid rgba(255,255,255,0.07)}
.s-logo{display:flex;align-items:center;gap:12px}
.s-logo-ic{width:42px;height:42px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 14px rgba(102,126,234,0.35)}
.s-logo-ic i{color:white;font-size:19px}
.s-logo-name{font-size:19px;font-weight:800;color:white;letter-spacing:-.5px}
.s-logo-tag{font-size:10px;color:rgba(255,255,255,0.3)}
.s-user{padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:10px}
.s-av{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:17px;flex-shrink:0}
.s-name{font-size:13px;font-weight:600;color:white}
.s-role{font-size:10px;color:rgba(255,255,255,0.4)}
.s-badge{display:inline-block;background:rgba(102,126,234,0.25);color:#a5b4fc;font-size:10px;padding:2px 8px;border-radius:8px;font-weight:600;margin-top:2px}
.s-nav{padding:14px 12px;flex:1}
.s-sec{font-size:10px;color:rgba(255,255,255,0.22);font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 10px 5px}
.s-link{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:10px;color:rgba(255,255,255,0.48);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:2px;transition:all .18s;cursor:pointer}
.s-link:hover{background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.85)}
.s-link.active{background:rgba(102,126,234,0.22);color:white;box-shadow:inset 2px 0 0 #667eea}
.s-link i{width:15px;text-align:center;font-size:13px}
.s-foot{padding:14px 20px;border-top:1px solid rgba(255,255,255,0.07)}
.s-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:rgba(255,255,255,0.38);text-decoration:none;font-size:13px;font-weight:500;transition:all .18s}
.s-out:hover{background:rgba(239,68,68,0.12);color:#f87171}
.main{margin-left:260px;flex:1;padding:28px 30px}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:26px}
.pg-title{font-size:23px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.pg-sub{font-size:13px;color:#64748b;margin-top:3px}
.apply-btn{display:inline-flex;align-items:center;gap:8px;padding:11px 20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;text-decoration:none;border-radius:12px;font-size:13px;font-weight:700;box-shadow:0 5px 16px rgba(102,126,234,0.35);transition:all .2s}
.apply-btn:hover{transform:translateY(-2px);color:white;box-shadow:0 10px 24px rgba(102,126,234,0.5)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.chip{display:inline-flex;align-items:center;gap:6px;background:white;border:1px solid #e2e8f0;border-radius:8px;padding:6px 12px;font-size:12px;color:#475569;font-weight:500;box-shadow:0 1px 4px rgba(0,0,0,0.04)}
.chip i{color:#667eea;font-size:11px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}
.kpi{background:white;border-radius:16px;padding:20px 20px 16px;box-shadow:0 1px 6px rgba(0,0,0,0.05);border:1px solid #f1f5f9;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s}
.kpi:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,0.08)}
.kpi-ic{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:14px}
.i1{background:#ede9fe;color:#7c3aed}
.i2{background:#dcfce7;color:#16a34a}
.i3{background:#fef3c7;color:#d97706}
.i4{background:#fee2e2;color:#dc2626}
.kpi-val{font-size:34px;font-weight:900;color:#0f172a;letter-spacing:-1.5px;line-height:1}
.kpi-lbl{font-size:12px;color:#64748b;font-weight:500;margin-top:5px}
.kpi-bar{height:3px;border-radius:2px;background:#f1f5f9;margin-top:16px}
.kpi-fill{height:100%;border-radius:2px}
.fp{background:linear-gradient(90deg,#667eea,#764ba2)}
.fg{background:linear-gradient(90deg,#10b981,#059669)}
.fy{background:linear-gradient(90deg,#f59e0b,#d97706)}
.fr{background:linear-gradient(90deg,#ef4444,#dc2626)}
.row2{display:grid;grid-template-columns:1.4fr 0.6fr;gap:18px;margin-bottom:22px}
.card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 1px 6px rgba(0,0,0,0.05);border:1px solid #f1f5f9}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.card-title{font-size:14px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:7px}
.card-title i{color:#667eea}
.cnt-badge{background:#f1f5f9;color:#64748b;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
.att-score{font-size:64px;font-weight:900;letter-spacing:-4px;text-align:center;line-height:1;margin:8px 0 4px}
.att-sub{text-align:center;font-size:12px;color:#94a3b8;margin-bottom:18px}
.att-status{display:flex;align-items:center;justify-content:center;gap:6px;padding:7px 14px;border-radius:20px;font-size:12px;font-weight:700;margin-bottom:16px}
.sg{background:#f0fdf4;color:#16a34a}
.so{background:#fffbeb;color:#d97706}
.sr{background:#fef2f2;color:#dc2626}
.ag{background:linear-gradient(135deg,#10b981,#059669);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.ao{background:linear-gradient(135deg,#f59e0b,#d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.ar{background:linear-gradient(135deg,#ef4444,#dc2626);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.prog{margin-bottom:13px}
.prog-top{display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px}
.prog-lbl{color:#64748b;font-weight:500}
.prog-val{color:#0f172a;font-weight:700}
.prog-bar{height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.prog-fill{height:100%;border-radius:4px;transition:width 1s ease}
table{width:100%;border-collapse:collapse}
th{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;padding:9px 12px;border-bottom:1px solid #f1f5f9;white-space:nowrap}
td{padding:13px 12px;font-size:13px;color:#334155;border-bottom:1px solid #f8fafc;vertical-align:middle}
tr:last-child td{border:none}
tr:hover td{background:#fafbff}
.pill{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.pa{background:#f0fdf4;color:#16a34a}
.pp{background:#fffbeb;color:#d97706}
.pr{background:#fef2f2;color:#dc2626}
.lt{background:#ede9fe;color:#7c3aed;font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600}
.empty{text-align:center;padding:40px;color:#94a3b8}
.empty i{font-size:38px;display:block;margin-bottom:10px;opacity:.35}
</style>
</head>
<body>
<div class="sidebar">
  <div class="s-header">
    <div class="s-logo">
      <div class="s-logo-ic"><i class="fas fa-calendar-check"></i></div>
      <div><div class="s-logo-name">LeaveFlow</div><div class="s-logo-tag">Employee Portal</div></div>
    </div>
  </div>
  <div class="s-user">
    <div class="s-av">{{ employee.name|first }}</div>
    <div>
      <div class="s-name">{{ employee.name }}</div>
      <div class="s-role">{{ employee.department }}</div>
      <div class="s-badge">Employee</div>
    </div>
  </div>
  <div class="s-nav">
    <div class="s-sec">Main</div>
    <a href="{% url 'employee_dashboard' %}" class="s-link active"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="s-link"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="s-sec">My Info</div>
    <a href="#attendance" class="s-link"><i class="fas fa-chart-bar"></i>Attendance</a>
    <a href="#history" class="s-link"><i class="fas fa-history"></i>Leave History</a>
  </div>
  <div class="s-foot">
    <a href="{% url 'logout' %}" class="s-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Good day, {{ employee.name }} 👋</div>
      <div class="pg-sub">Your leave and attendance overview</div>
    </div>
    <a href="{% url 'apply_leave' %}" class="apply-btn"><i class="fas fa-plus"></i>New Leave Request</a>
  </div>

  <div class="chips">
    <div class="chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="chip"><i class="fas fa-id-badge"></i>Employee</div>
    <div class="chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
    <div class="chip"><i class="fas fa-umbrella-beach"></i>{{ employee.leave_balance }} days balance left</div>
  </div>

  <div class="kpis">
    <div class="kpi"><div class="kpi-ic i1"><i class="fas fa-file-alt"></i></div><div class="kpi-val">{{ leaves.count }}</div><div class="kpi-lbl">Total Requests</div><div class="kpi-bar"><div class="kpi-fill fp" style="width:100%"></div></div></div>
    <div class="kpi"><div class="kpi-ic i2"><i class="fas fa-check-circle"></i></div><div class="kpi-val">{{ approved }}</div><div class="kpi-lbl">Approved</div><div class="kpi-bar"><div class="kpi-fill fg" style="width:80%"></div></div></div>
    <div class="kpi"><div class="kpi-ic i3"><i class="fas fa-clock"></i></div><div class="kpi-val">{{ pending }}</div><div class="kpi-lbl">Pending</div><div class="kpi-bar"><div class="kpi-fill fy" style="width:60%"></div></div></div>
    <div class="kpi"><div class="kpi-ic i4"><i class="fas fa-times-circle"></i></div><div class="kpi-val">{{ rejected }}</div><div class="kpi-lbl">Rejected</div><div class="kpi-bar"><div class="kpi-fill fr" style="width:40%"></div></div></div>
  </div>

  <div class="row2" id="attendance">
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-line"></i>Attendance Breakdown</div></div>
      <div class="prog">
        <div class="prog-top"><span class="prog-lbl"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#10b981;margin-right:5px"></span>Attendance Rate</span><span class="prog-val">{{ employee.attendance_percent }}%</span></div>
        <div class="prog-bar"><div class="prog-fill fg" style="width:{{ employee.attendance_percent }}%"></div></div>
      </div>
      <div class="prog">
        <div class="prog-top"><span class="prog-lbl"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ef4444;margin-right:5px"></span>Absent / On Leave</span><span class="prog-val">{{ attendance_gap }}%</span></div>
        <div class="prog-bar"><div class="prog-fill fr" style="width:{{ attendance_gap }}%"></div></div>
      </div>
      <div class="prog">
        <div class="prog-top"><span class="prog-lbl"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#667eea;margin-right:5px"></span>Leave Days Used</span><span class="prog-val">{{ leave_used }} of 20 days</span></div>
        <div class="prog-bar"><div class="prog-fill fp" style="width:{{ leave_used }}0%"></div></div>
      </div>
      <div class="prog">
        <div class="prog-top"><span class="prog-lbl"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f59e0b;margin-right:5px"></span>Leave Balance Left</span><span class="prog-val">{{ employee.leave_balance }} days</span></div>
        <div class="prog-bar"><div class="prog-fill fy" style="width:{{ employee.leave_balance }}0%"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-tachometer-alt"></i>Attendance Score</div></div>
      <div class="att-score {% if employee.attendance_percent >= 90 %}ag{% elif employee.attendance_percent >= 75 %}ao{% else %}ar{% endif %}">{{ employee.attendance_percent }}%</div>
      <div class="att-sub">Overall Attendance Rate</div>
      <div class="att-status {% if employee.attendance_percent >= 90 %}sg{% elif employee.attendance_percent >= 75 %}so{% else %}sr{% endif %}">
        {% if employee.attendance_percent >= 90 %}<i class="fas fa-check-circle"></i>Excellent Standing
        {% elif employee.attendance_percent >= 75 %}<i class="fas fa-exclamation-circle"></i>Needs Improvement
        {% else %}<i class="fas fa-times-circle"></i>Critical — Act Now{% endif %}
      </div>
      <canvas id="attChart" height="145"></canvas>
    </div>
  </div>

  <div class="card" id="history">
    <div class="card-hd">
      <div class="card-title"><i class="fas fa-history"></i>Leave Request History</div>
      <span class="cnt-badge">{{ leaves.count }} records</span>
    </div>
    <table>
      <thead><tr><th>#</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Applied On</th><th>Status</th></tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td style="color:#94a3b8;font-size:12px">{{ forloop.counter }}</td>
        <td><span class="lt">{{ leave.leave_type }}</span></td>
        <td>{{ leave.start_date }}</td>
        <td>{{ leave.end_date }}</td>
        <td><strong>{{ leave.days }}d</strong></td>
        <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ leave.reason }}</td>
        <td style="color:#94a3b8;font-size:12px">{{ leave.applied_on }}</td>
        <td>
          {% if leave.status == 'APPROVED' %}<span class="pill pa"><i class="fas fa-check"></i>Approved</span>
          {% elif leave.status == 'REJECTED' %}<span class="pill pr"><i class="fas fa-times"></i>Rejected</span>
          {% else %}<span class="pill pp"><i class="fas fa-clock"></i>Pending</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="8"><div class="empty"><i class="fas fa-folder-open"></i>No leave requests yet. Click New Leave Request to start.</div></td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
new Chart(document.getElementById('attChart'),{
  type:'doughnut',
  data:{
    labels:['Present','Absent'],
    datasets:[{data:[{{ employee.attendance_percent }},{{ attendance_gap }}],backgroundColor:['#10b981','#fee2e2'],borderColor:['#059669','#fca5a5'],borderWidth:2,hoverOffset:5}]
  },
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:12,font:{size:11},boxWidth:10}}},cutout:'72%'}
});
</script>
</body>
</html>
"""

files['employees/templates/manager_dashboard.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Manager Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f1f5f9;display:flex;min-height:100vh}
.sidebar{width:260px;background:linear-gradient(180deg,#0f0c29,#1a0533,#2d1b69);min-height:100vh;position:fixed;top:0;left:0;bottom:0;display:flex;flex-direction:column;z-index:50;box-shadow:4px 0 24px rgba(0,0,0,0.25)}
.s-header{padding:22px 20px;border-bottom:1px solid rgba(255,255,255,0.07)}
.s-logo{display:flex;align-items:center;gap:12px}
.s-logo-ic{width:42px;height:42px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 14px rgba(240,147,251,0.35)}
.s-logo-ic i{color:white;font-size:19px}
.s-logo-name{font-size:19px;font-weight:800;color:white;letter-spacing:-.5px}
.s-logo-tag{font-size:10px;color:rgba(255,255,255,0.3)}
.s-user{padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:10px}
.s-av{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#f093fb,#f5576c);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:17px;flex-shrink:0}
.s-name{font-size:13px;font-weight:600;color:white}
.s-badge{display:inline-block;background:rgba(240,147,251,0.2);color:#f9a8d4;font-size:10px;padding:2px 8px;border-radius:8px;font-weight:600;margin-top:3px}
.s-nav{padding:14px 12px;flex:1}
.s-sec{font-size:10px;color:rgba(255,255,255,0.22);font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 10px 5px}
.s-link{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:10px;color:rgba(255,255,255,0.48);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:2px;transition:all .18s}
.s-link:hover{background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.85)}
.s-link.active{background:rgba(240,147,251,0.15);color:white;box-shadow:inset 2px 0 0 #f093fb}
.s-link i{width:15px;text-align:center;font-size:13px}
.s-nbadge{background:#f59e0b;color:white;font-size:10px;padding:2px 7px;border-radius:10px;margin-left:auto;font-weight:600}
.s-foot{padding:14px 20px;border-top:1px solid rgba(255,255,255,0.07)}
.s-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:rgba(255,255,255,0.38);text-decoration:none;font-size:13px;font-weight:500;transition:all .18s}
.s-out:hover{background:rgba(239,68,68,0.12);color:#f87171}
.main{margin-left:260px;flex:1;padding:28px 30px}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:26px}
.pg-title{font-size:23px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.pg-sub{font-size:13px;color:#64748b;margin-top:3px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}
.kpi{background:white;border-radius:16px;padding:20px 20px 16px;box-shadow:0 1px 6px rgba(0,0,0,0.05);border:1px solid #f1f5f9;transition:transform .2s,box-shadow .2s}
.kpi:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,0.08)}
.kpi-ic{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:14px}
.i1{background:#fdf4ff;color:#a855f7}
.i2{background:#eff6ff;color:#3b82f6}
.i3{background:#f0fdf4;color:#16a34a}
.i4{background:#fff7ed;color:#ea580c}
.kpi-val{font-size:34px;font-weight:900;color:#0f172a;letter-spacing:-1.5px;line-height:1}
.kpi-lbl{font-size:12px;color:#64748b;font-weight:500;margin-top:5px}
.kpi-note{font-size:11px;font-weight:600;margin-top:8px;color:#94a3b8}
.tabs{display:flex;gap:4px;background:white;padding:5px;border-radius:13px;border:1px solid #f1f5f9;box-shadow:0 1px 6px rgba(0,0,0,0.04);margin-bottom:20px;width:fit-content}
.tab{padding:8px 18px;border-radius:9px;font-size:13px;font-weight:600;color:#64748b;cursor:pointer;transition:all .18s;user-select:none}
.tab.active{background:linear-gradient(135deg,#667eea,#764ba2);color:white;box-shadow:0 4px 12px rgba(102,126,234,0.3)}
.tab-content{display:none}
.tab-content.active{display:block}
.row2{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:22px}
.card{background:white;border-radius:16px;padding:22px 24px;box-shadow:0 1px 6px rgba(0,0,0,0.05);border:1px solid #f1f5f9;margin-bottom:20px}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.card-title{font-size:14px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:7px}
.card-title i{color:#a855f7}
.cnt-badge{background:#f1f5f9;color:#64748b;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
.pend-badge{background:#fffbeb;color:#d97706;font-size:11px;padding:3px 9px;border-radius:20px;font-weight:600}
table{width:100%;border-collapse:collapse}
th{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;padding:9px 12px;border-bottom:1px solid #f1f5f9;white-space:nowrap}
td{padding:12px 12px;font-size:13px;color:#334155;border-bottom:1px solid #f8fafc;vertical-align:middle}
tr:last-child td{border:none}
tr:hover td{background:#fafbff}
.emp-cell{display:flex;align-items:center;gap:9px}
.emp-av{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:13px;flex-shrink:0}
.emp-nm{font-size:13px;font-weight:600;color:#0f172a}
.emp-dep{font-size:11px;color:#94a3b8}
.pill{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}
.pa{background:#f0fdf4;color:#16a34a}
.pp{background:#fffbeb;color:#d97706}
.pr{background:#fef2f2;color:#dc2626}
.lt{background:#ede9fe;color:#7c3aed;font-size:10px;padding:3px 8px;border-radius:6px;font-weight:600}
.btn-app{display:inline-flex;align-items:center;gap:4px;padding:5px 11px;background:linear-gradient(135deg,#10b981,#059669);border:none;border-radius:7px;color:white;font-size:11px;font-weight:600;text-decoration:none;transition:all .15s}
.btn-app:hover{transform:translateY(-1px);color:white;box-shadow:0 4px 10px rgba(16,185,129,0.3)}
.btn-rej{display:inline-flex;align-items:center;gap:4px;padding:5px 11px;background:linear-gradient(135deg,#ef4444,#dc2626);border:none;border-radius:7px;color:white;font-size:11px;font-weight:600;text-decoration:none;margin-left:5px;transition:all .15s}
.btn-rej:hover{transform:translateY(-1px);color:white;box-shadow:0 4px 10px rgba(239,68,68,0.3)}
.att-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #f8fafc}
.att-row:last-child{border:none}
.att-av{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:15px;flex-shrink:0}
.att-info{min-width:120px}
.att-name{font-size:13px;font-weight:600;color:#0f172a}
.att-dep{font-size:11px;color:#94a3b8}
.att-bar-wrap{flex:1}
.att-bar-top{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px}
.att-bar{height:7px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.att-fill{height:100%;border-radius:4px;transition:width 1s ease}
.bg{background:linear-gradient(90deg,#10b981,#059669)}
.by{background:linear-gradient(90deg,#f59e0b,#d97706)}
.br2{background:linear-gradient(90deg,#ef4444,#dc2626)}
.att-sl{font-size:10px;padding:3px 9px;border-radius:10px;font-weight:600;white-space:nowrap;min-width:68px;text-align:center}
.slg{background:#f0fdf4;color:#16a34a}
.sly{background:#fffbeb;color:#d97706}
.slr{background:#fef2f2;color:#dc2626}
.edit-btn{background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:8px;padding:4px 10px;font-size:11px;font-weight:600;color:#475569;cursor:pointer;transition:all .2s;font-family:'Inter',sans-serif}
.edit-btn:hover{background:#ede9fe;border-color:#a5b4fc;color:#7c3aed}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal-box{background:white;border-radius:20px;padding:32px 36px;width:400px;box-shadow:0 24px 60px rgba(0,0,0,0.2)}
.modal-title{font-size:18px;font-weight:800;color:#0f172a;margin-bottom:6px}
.modal-sub{font-size:13px;color:#64748b;margin-bottom:24px}
.modal-field{margin-bottom:16px}
.modal-label{font-size:12px;font-weight:600;color:#374151;text-transform:uppercase;letter-spacing:.04em;margin-bottom:7px;display:block}
.modal-input{width:100%;padding:11px 13px;border:1.5px solid #e2e8f0;border-radius:10px;font-size:14px;color:#0f172a;font-family:'Inter',sans-serif;outline:none;transition:all .2s}
.modal-input:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
.modal-btns{display:flex;gap:10px;margin-top:8px}
.modal-save{flex:1;padding:11px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:10px;color:white;font-size:13px;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif}
.modal-cancel{padding:11px 18px;background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:10px;color:#64748b;font-size:13px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif}
.stat-chips{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}
.stat-chip{flex:1;min-width:80px;padding:14px 10px;border-radius:13px;text-align:center;border:1.5px solid transparent}
.sc-g{background:#f0fdf4;border-color:#bbf7d0}
.sc-y{background:#fffbeb;border-color:#fde68a}
.sc-r{background:#fef2f2;border-color:#fecaca}
.sc-val{font-size:22px;font-weight:800;margin-bottom:3px}
.scg{color:#16a34a} .scy{color:#d97706} .scr{color:#dc2626}
.sc-lbl{font-size:11px;color:#64748b;font-weight:500}
.empty{text-align:center;padding:36px;color:#94a3b8}
.empty i{font-size:36px;display:block;margin-bottom:10px;opacity:.35}
</style>
</head>
<body>

<div class="sidebar">
  <div class="s-header">
    <div class="s-logo">
      <div class="s-logo-ic"><i class="fas fa-shield-alt"></i></div>
      <div><div class="s-logo-name">LeaveFlow</div><div class="s-logo-tag">Manager Portal</div></div>
    </div>
  </div>
  <div class="s-user">
    <div class="s-av">M</div>
    <div>
      <div class="s-name">{{ name }}</div>
      <div class="s-badge">Manager</div>
    </div>
  </div>
  <div class="s-nav">
    <div class="s-sec">Management</div>
    <a href="#overview" onclick="showTab('overview')" class="s-link active" id="nav-overview"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="#requests" onclick="showTab('requests')" class="s-link" id="nav-requests"><i class="fas fa-inbox"></i>Leave Requests{% if pending_count > 0 %}<span class="s-nbadge">{{ pending_count }}</span>{% endif %}</a>
    <a href="#attendance" onclick="showTab('attendance')" class="s-link" id="nav-attendance"><i class="fas fa-chart-bar"></i>Attendance</a>
    <a href="#team" onclick="showTab('team')" class="s-link" id="nav-team"><i class="fas fa-users"></i>Team</a>
  </div>
  <div class="s-foot">
    <a href="{% url 'logout' %}" class="s-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="pg-title">Manager Dashboard 🛡️</div>
      <div class="pg-sub">Team leave management and attendance monitoring</div>
    </div>
  </div>

  <!-- TAB: OVERVIEW -->
  <div class="tab-content active" id="tab-overview">
    <div class="kpis">
      <div class="kpi"><div class="kpi-ic i1"><i class="fas fa-users"></i></div><div class="kpi-val">{{ total_emp }}</div><div class="kpi-lbl">Total Employees</div><div class="kpi-note">Active team members</div></div>
      <div class="kpi"><div class="kpi-ic i2"><i class="fas fa-hourglass-half"></i></div><div class="kpi-val">{{ pending_count }}</div><div class="kpi-lbl">Pending Approvals</div><div class="kpi-note">{% if pending_count > 0 %}Needs attention{% else %}All clear{% endif %}</div></div>
      <div class="kpi"><div class="kpi-ic i3"><i class="fas fa-check-double"></i></div><div class="kpi-val">{{ approved_count }}</div><div class="kpi-lbl">Approved</div><div class="kpi-note">This period</div></div>
      <div class="kpi"><div class="kpi-ic i4"><i class="fas fa-file-alt"></i></div><div class="kpi-val">{{ total_leaves }}</div><div class="kpi-lbl">Total Requests</div><div class="kpi-note">All time</div></div>
    </div>
    <div class="row2">
      <div class="card" style="margin:0">
        <div class="card-hd"><div class="card-title"><i class="fas fa-inbox"></i>Recent Leave Requests</div>{% if pending_count > 0 %}<span class="pend-badge"><i class="fas fa-clock me-1"></i>{{ pending_count }} pending</span>{% else %}<span class="cnt-badge">{{ total_leaves }} total</span>{% endif %}</div>
        <table>
          <thead><tr><th>Employee</th><th>Type</th><th>Dates</th><th>Days</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
          {% for leave in leaves %}
          <tr>
            <td><div class="emp-cell"><div class="emp-av">{{ leave.employee.name|first }}</div><div><div class="emp-nm">{{ leave.employee.name }}</div><div class="emp-dep">{{ leave.employee.department }}</div></div></div></td>
            <td><span class="lt">{{ leave.leave_type }}</span></td>
            <td style="font-size:12px;color:#64748b">{{ leave.start_date }}<br>{{ leave.end_date }}</td>
            <td><strong>{{ leave.days }}d</strong></td>
            <td>{% if leave.status == 'APPROVED' %}<span class="pill pa"><i class="fas fa-check"></i>Approved</span>{% elif leave.status == 'REJECTED' %}<span class="pill pr"><i class="fas fa-times"></i>Rejected</span>{% else %}<span class="pill pp"><i class="fas fa-clock"></i>Pending</span>{% endif %}</td>
            <td>{% if leave.status == 'PENDING' %}<a href="{% url 'update_status' leave.id 'APPROVED' %}" class="btn-app"><i class="fas fa-check"></i>Approve</a><a href="{% url 'update_status' leave.id 'REJECTED' %}" class="btn-rej"><i class="fas fa-times"></i>Reject</a>{% else %}<span style="color:#cbd5e1;font-size:12px">—</span>{% endif %}</td>
          </tr>
          {% empty %}
          <tr><td colspan="6"><div class="empty"><i class="fas fa-inbox"></i>No requests found.</div></td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
      <div class="card" style="margin:0">
        <div class="card-hd"><div class="card-title"><i class="fas fa-chart-pie"></i>Leave Overview</div></div>
        <canvas id="leaveDonut" height="220"></canvas>
        <div style="margin-top:14px">
          <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f8fafc;font-size:12px"><span style="color:#64748b">Approved</span><strong style="color:#16a34a">{{ approved_count }}</strong></div>
          <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f8fafc;font-size:12px"><span style="color:#64748b">Pending</span><strong style="color:#d97706">{{ pending_count }}</strong></div>
          <div style="display:flex;justify-content:space-between;padding:7px 0;font-size:12px"><span style="color:#64748b">Rejected</span><strong style="color:#dc2626">{{ rejected_count }}</strong></div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB: REQUESTS -->
  <div class="tab-content" id="tab-requests">
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-inbox"></i>All Leave Requests</div><span class="cnt-badge">{{ total_leaves }} total</span></div>
      <table>
        <thead><tr><th>#</th><th>Employee</th><th>Dept</th><th>Type</th><th>From</th><th>To</th><th>Days</th><th>Reason</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
        {% for leave in leaves %}
        <tr>
          <td style="color:#94a3b8;font-size:12px">{{ forloop.counter }}</td>
          <td><div class="emp-cell"><div class="emp-av">{{ leave.employee.name|first }}</div><div class="emp-nm">{{ leave.employee.name }}</div></div></td>
          <td style="font-size:12px;color:#64748b">{{ leave.employee.department }}</td>
          <td><span class="lt">{{ leave.leave_type }}</span></td>
          <td style="font-size:12px">{{ leave.start_date }}</td>
          <td style="font-size:12px">{{ leave.end_date }}</td>
          <td><strong>{{ leave.days }}d</strong></td>
          <td style="max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;color:#64748b">{{ leave.reason }}</td>
          <td>{% if leave.status == 'APPROVED' %}<span class="pill pa"><i class="fas fa-check"></i>Approved</span>{% elif leave.status == 'REJECTED' %}<span class="pill pr"><i class="fas fa-times"></i>Rejected</span>{% else %}<span class="pill pp"><i class="fas fa-clock"></i>Pending</span>{% endif %}</td>
          <td>{% if leave.status == 'PENDING' %}<a href="{% url 'update_status' leave.id 'APPROVED' %}" class="btn-app"><i class="fas fa-check"></i>Approve</a><a href="{% url 'update_status' leave.id 'REJECTED' %}" class="btn-rej"><i class="fas fa-times"></i>Reject</a>{% else %}<span style="color:#cbd5e1;font-size:12px">—</span>{% endif %}</td>
        </tr>
        {% empty %}
        <tr><td colspan="10"><div class="empty"><i class="fas fa-inbox"></i>No requests.</div></td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAB: ATTENDANCE -->
  <div class="tab-content" id="tab-attendance">
    <div class="stat-chips">
      <div class="stat-chip sc-g"><div class="sc-val scg">{{ excellent }}</div><div class="sc-lbl">Excellent ≥90%</div></div>
      <div class="stat-chip sc-y"><div class="sc-val scy">{{ average }}</div><div class="sc-lbl">Average 75–89%</div></div>
      <div class="stat-chip sc-r"><div class="sc-val scr">{{ poor }}</div><div class="sc-lbl">Poor &lt;75%</div></div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-chart-bar"></i>Employee Attendance Tracker</div><span class="cnt-badge">{{ total_emp }} employees</span></div>
      {% for emp in employees %}
      <div class="att-row">
        <div class="att-av">{{ emp.name|first }}</div>
        <div class="att-info">
          <div class="att-name">{{ emp.name }}</div>
          <div class="att-dep">{{ emp.department }} &bull; {{ emp.leave_balance }}d left</div>
        </div>
        <div class="att-bar-wrap">
          <div class="att-bar-top">
            <span style="color:#64748b;font-size:11px">Attendance</span>
            <span style="font-weight:700;color:#0f172a;font-size:12px">{{ emp.attendance_percent }}%</span>
          </div>
          <div class="att-bar">
            <div class="att-fill {% if emp.attendance_percent >= 90 %}bg{% elif emp.attendance_percent >= 75 %}by{% else %}br2{% endif %}" style="width:{{ emp.attendance_percent }}%"></div>
          </div>
        </div>
        <div class="att-sl {% if emp.attendance_percent >= 90 %}slg{% elif emp.attendance_percent >= 75 %}sly{% else %}slr{% endif %}">
          {% if emp.attendance_percent >= 90 %}Excellent{% elif emp.attendance_percent >= 75 %}Average{% else %}Poor{% endif %}
        </div>
        <button class="edit-btn" onclick="openEdit({{ emp.id }},'{{ emp.name }}',{{ emp.attendance_percent }},{{ emp.leave_balance }})"><i class="fas fa-pen me-1"></i>Edit</button>
      </div>
      {% empty %}
      <div class="empty"><i class="fas fa-users"></i>No employees found. Add employees with role=EMPLOYEE in the admin panel.</div>
      {% endfor %}
    </div>
  </div>

  <!-- TAB: TEAM -->
  <div class="tab-content" id="tab-team">
    <div class="card">
      <div class="card-hd"><div class="card-title"><i class="fas fa-users"></i>Full Team Overview</div><span class="cnt-badge">{{ total_emp }} members</span></div>
      <table>
        <thead><tr><th>Employee</th><th>Department</th><th>Email</th><th>Leave Balance</th><th>Attendance</th><th>Status</th><th>Edit</th></tr></thead>
        <tbody>
        {% for emp in employees %}
        <tr>
          <td><div class="emp-cell"><div class="emp-av">{{ emp.name|first }}</div><div><div class="emp-nm">{{ emp.name }}</div><div class="emp-dep">{{ emp.email }}</div></div></div></td>
          <td><span class="lt">{{ emp.department }}</span></td>
          <td style="font-size:12px;color:#64748b">{{ emp.email }}</td>
          <td><strong>{{ emp.leave_balance }}</strong> <span style="color:#94a3b8;font-size:11px">days</span></td>
          <td>
            <strong style="{% if emp.attendance_percent >= 90 %}color:#16a34a{% elif emp.attendance_percent >= 75 %}color:#d97706{% else %}color:#dc2626{% endif %}">{{ emp.attendance_percent }}%</strong>
            <div style="height:4px;background:#f1f5f9;border-radius:2px;margin-top:4px;width:80px;overflow:hidden"><div style="height:100%;border-radius:2px;width:{{ emp.attendance_percent }}%;background:{% if emp.attendance_percent >= 90 %}#10b981{% elif emp.attendance_percent >= 75 %}#f59e0b{% else %}#ef4444{% endif %}"></div></div>
          </td>
          <td><span class="att-sl {% if emp.attendance_percent >= 90 %}slg{% elif emp.attendance_percent >= 75 %}sly{% else %}slr{% endif %}">{% if emp.attendance_percent >= 90 %}Excellent{% elif emp.attendance_percent >= 75 %}Average{% else %}Poor{% endif %}</span></td>
          <td><button class="edit-btn" onclick="openEdit({{ emp.id }},'{{ emp.name }}',{{ emp.attendance_percent }},{{ emp.leave_balance }})"><i class="fas fa-pen me-1"></i>Edit</button></td>
        </tr>
        {% empty %}
        <tr><td colspan="7"><div class="empty"><i class="fas fa-users"></i>No employees found.</div></td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- EDIT ATTENDANCE MODAL -->
<div class="modal-overlay" id="editModal">
  <div class="modal-box">
    <div class="modal-title">Edit Attendance</div>
    <div class="modal-sub" id="modalSub">Update attendance for employee</div>
    <form method="POST" id="editForm">
      {% csrf_token %}
      <div class="modal-field">
        <label class="modal-label">Attendance Percentage (%)</label>
        <input type="number" name="attendance_percent" id="attInput" class="modal-input" min="0" max="100" step="0.1" required>
      </div>
      <div class="modal-field">
        <label class="modal-label">Leave Balance (days)</label>
        <input type="number" name="leave_balance" id="balInput" class="modal-input" min="0" max="30" required>
      </div>
      <div class="modal-btns">
        <button type="button" class="modal-cancel" onclick="closeEdit()">Cancel</button>
        <button type="submit" class="modal-save"><i class="fas fa-save me-1"></i>Save Changes</button>
      </div>
    </form>
  </div>
</div>

<script>
// Tabs
function showTab(name){
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.s-link').forEach(l=>l.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.getElementById('nav-'+name).classList.add('active');
}

// Charts
new Chart(document.getElementById('leaveDonut'),{
  type:'doughnut',
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved_count }},{{ pending_count }},{{ rejected_count }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderColor:['#d1fae5','#fef3c7','#fee2e2'],borderWidth:2,hoverOffset:6}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:14,font:{size:11},boxWidth:10}}},cutout:'68%'}
});

// Edit Modal
function openEdit(id, name, att, bal){
  document.getElementById('modalSub').textContent = 'Update attendance for ' + name;
  document.getElementById('attInput').value = att;
  document.getElementById('balInput').value = bal;
  document.getElementById('editForm').action = '/update-attendance/' + id + '/';
  document.getElementById('editModal').classList.add('show');
}
function closeEdit(){
  document.getElementById('editModal').classList.remove('show');
}
document.getElementById('editModal').addEventListener('click', function(e){
  if(e.target === this) closeEdit();
});
</script>
</body>
</html>
"""

files['employees/templates/apply_leave.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Apply Leave</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f1f5f9;display:flex;min-height:100vh}
.sidebar{width:260px;background:linear-gradient(180deg,#0f172a,#1e1b4b);min-height:100vh;position:fixed;top:0;left:0;bottom:0;display:flex;flex-direction:column;z-index:50}
.s-header{padding:22px 20px;border-bottom:1px solid rgba(255,255,255,0.07)}
.s-logo{display:flex;align-items:center;gap:12px}
.s-logo-ic{width:42px;height:42px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.s-logo-ic i{color:white;font-size:19px}
.s-logo-name{font-size:19px;font-weight:800;color:white}
.s-logo-tag{font-size:10px;color:rgba(255,255,255,0.3)}
.s-user{padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:10px}
.s-av{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:17px;flex-shrink:0}
.s-name{font-size:13px;font-weight:600;color:white}
.s-dep{font-size:11px;color:rgba(255,255,255,0.4)}
.s-nav{padding:14px 12px;flex:1}
.s-sec{font-size:10px;color:rgba(255,255,255,0.22);font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 10px 5px}
.s-link{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:10px;color:rgba(255,255,255,0.48);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:2px;transition:all .18s}
.s-link:hover{background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.85)}
.s-link.active{background:rgba(102,126,234,0.22);color:white;box-shadow:inset 2px 0 0 #667eea}
.s-link i{width:15px;text-align:center}
.s-foot{padding:14px 20px;border-top:1px solid rgba(255,255,255,0.07)}
.s-out{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:rgba(255,255,255,0.38);text-decoration:none;font-size:13px;transition:all .18s}
.s-out:hover{background:rgba(239,68,68,0.12);color:#f87171}
.main{margin-left:260px;flex:1;display:flex;justify-content:center;padding:40px 40px}
.form-wrap{width:100%;max-width:600px}
.pg-title{font-size:23px;font-weight:800;color:#0f172a;letter-spacing:-.5px}
.pg-sub{font-size:13px;color:#64748b;margin-top:3px;margin-bottom:22px}
.info-bar{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:11px;padding:12px 16px;margin-bottom:22px;display:flex;align-items:center;gap:10px;font-size:13px;color:#166534;font-weight:500}
.form-card{background:white;border-radius:18px;padding:34px 36px;box-shadow:0 4px 20px rgba(0,0,0,0.06);border:1px solid #f1f5f9}
.sec-title{font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #f1f5f9}
.lt-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px}
.lt-opt input{position:absolute;opacity:0;width:0}
.lt-opt{position:relative}
.lt-card{display:flex;align-items:center;gap:10px;padding:12px 14px;border:1.5px solid #e2e8f0;border-radius:11px;cursor:pointer;transition:all .2s;background:#fafafa}
.lt-card:hover{border-color:#a5b4fc;background:#f5f3ff}
.lt-opt input:checked+.lt-card{border-color:#667eea;background:#ede9fe;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
.lt-ic{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
.l1{background:#dbeafe;color:#2563eb}
.l2{background:#fce7f3;color:#db2777}
.l3{background:#dcfce7;color:#16a34a}
.l4{background:#fee2e2;color:#dc2626}
.lt-name{font-size:13px;font-weight:600;color:#0f172a}
.lt-sub{font-size:11px;color:#94a3b8}
.date-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}
.fg{margin-bottom:20px}
.flabel{font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;margin-bottom:7px;display:block}
.flabel i{color:#667eea;margin-right:5px}
.finput{width:100%;padding:12px 14px;border:1.5px solid #e2e8f0;border-radius:11px;font-size:14px;color:#0f172a;background:#fafafa;outline:none;font-family:'Inter',sans-serif;transition:all .2s}
.finput:focus{border-color:#667eea;background:white;box-shadow:0 0 0 3px rgba(102,126,234,0.08)}
.btn-row{display:flex;gap:10px;margin-top:6px}
.btn-sub{flex:1;padding:13px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:11px;color:white;font-size:14px;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;box-shadow:0 5px 16px rgba(102,126,234,0.35);transition:all .2s}
.btn-sub:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(102,126,234,0.5)}
.btn-back{padding:13px 18px;background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:11px;color:#64748b;font-size:14px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:7px;transition:all .2s}
.btn-back:hover{background:#f1f5f9;color:#334155}
</style>
</head>
<body>
<div class="sidebar">
  <div class="s-header">
    <div class="s-logo">
      <div class="s-logo-ic"><i class="fas fa-calendar-check"></i></div>
      <div><div class="s-logo-name">LeaveFlow</div><div class="s-logo-tag">Employee Portal</div></div>
    </div>
  </div>
  <div class="s-user">
    <div class="s-av">{{ employee.name|first }}</div>
    <div><div class="s-name">{{ employee.name }}</div><div class="s-dep">{{ employee.department }}</div></div>
  </div>
  <div class="s-nav">
    <div class="s-sec">Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="s-link"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="s-link active"><i class="fas fa-plus-circle"></i>Apply Leave</a>
  </div>
  <div class="s-foot">
    <a href="{% url 'logout' %}" class="s-out"><i class="fas fa-sign-out-alt"></i>Sign Out</a>
  </div>
</div>

<div class="main">
  <div class="form-wrap">
    <div class="pg-title">Apply for Leave</div>
    <div class="pg-sub">Submit your leave request for manager approval</div>
    <div class="info-bar"><i class="fas fa-info-circle"></i>You have <strong style="margin:0 4px">{{ employee.leave_balance }} days</strong> of leave balance remaining.</div>
    <div class="form-card">
      <form method="POST">
        {% csrf_token %}
        <div class="sec-title">Select Leave Type</div>
        <div class="lt-grid">
          <label class="lt-opt"><input type="radio" name="leave_type" value="CASUAL" checked><div class="lt-card"><div class="lt-ic l1"><i class="fas fa-coffee"></i></div><div><div class="lt-name">Casual</div><div class="lt-sub">Personal errands</div></div></div></label>
          <label class="lt-opt"><input type="radio" name="leave_type" value="SICK"><div class="lt-card"><div class="lt-ic l2"><i class="fas fa-heartbeat"></i></div><div><div class="lt-name">Sick Leave</div><div class="lt-sub">Health & medical</div></div></div></label>
          <label class="lt-opt"><input type="radio" name="leave_type" value="ANNUAL"><div class="lt-card"><div class="lt-ic l3"><i class="fas fa-umbrella-beach"></i></div><div><div class="lt-name">Annual Leave</div><div class="lt-sub">Vacation</div></div></div></label>
          <label class="lt-opt"><input type="radio" name="leave_type" value="EMERGENCY"><div class="lt-card"><div class="lt-ic l4"><i class="fas fa-exclamation-triangle"></i></div><div><div class="lt-name">Emergency</div><div class="lt-sub">Urgent situation</div></div></div></label>
        </div>
        <div class="sec-title">Leave Duration</div>
        <div class="date-row">
          <div class="fg" style="margin:0"><label class="flabel"><i class="fas fa-calendar-day"></i>Start Date</label><input type="date" name="start" class="finput" required></div>
          <div class="fg" style="margin:0"><label class="flabel"><i class="fas fa-calendar-day"></i>End Date</label><input type="date" name="end" class="finput" required></div>
        </div>
        <div class="sec-title" style="margin-top:4px">Reason</div>
        <div class="fg">
          <label class="flabel"><i class="fas fa-comment-alt"></i>Describe your reason</label>
          <textarea name="reason" class="finput" rows="4" placeholder="Please describe the reason for your leave..." required style="resize:vertical"></textarea>
        </div>
        <div class="btn-row">
          <a href="{% url 'employee_dashboard' %}" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
          <button type="submit" class="btn-sub"><i class="fas fa-paper-plane me-2"></i>Submit Request</button>
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

print('\nALL FILES CREATED SUCCESSFULLY')