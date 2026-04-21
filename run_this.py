import os
os.makedirs('employees/templates', exist_ok=True)

files = {}

files['employees/models.py'] = """from django.db import models

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
    joined_date = models.DateField(auto_now_add=True)
    def __str__(self): return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected')]
    LEAVE_TYPES = [('SICK','Sick Leave'),('CASUAL','Casual Leave'),('ANNUAL','Annual Leave'),('EMERGENCY','Emergency')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPES, default='CASUAL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_on = models.DateField(auto_now_add=True)
    def days(self):
        return (self.end_date - self.start_date).days + 1
    def __str__(self): return f"{self.employee.name} - {self.status}"
"""

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
    leaves = LeaveRequest.objects.filter(employee_id=uid)
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
    leaves = LeaveRequest.objects.all().select_related('employee')
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
    return render(request, 'apply_leave.html')

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
"""

files['employees/urls.py'] = """from django.urls import path
from . import views
urlpatterns = [
    path('', views.login_view, name='login'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('apply/', views.apply_leave, name='apply_leave'),
    path('update/<int:id>/<str:status>/', views.update_status, name='update_status'),
    path('logout/', views.logout_view, name='logout'),
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

files['employees/templates/login.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LeaveFlow - Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);display:flex;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif}
.card{background:rgba(255,255,255,0.06);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.1);border-radius:24px;padding:48px 40px;width:100%;max-width:420px;box-shadow:0 32px 64px rgba(0,0,0,0.4)}
.logo-box{width:72px;height:72px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:20px;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(102,126,234,0.4);margin-bottom:14px}
.logo-box i{font-size:34px;color:white}
.brand{font-size:28px;font-weight:800;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand-sub{color:rgba(255,255,255,0.4);font-size:13px;margin-top:4px;margin-bottom:32px}
.field-label{color:rgba(255,255,255,0.6);font-size:13px;margin-bottom:6px;display:block;font-weight:500}
.input-group-text{background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);border-right:none;color:rgba(255,255,255,0.5);border-radius:12px 0 0 12px}
.form-control{background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);border-left:none;border-radius:0 12px 12px 0;color:white;padding:12px 14px;font-size:14px}
.form-control:focus{background:rgba(255,255,255,0.1);border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.2);color:white}
.form-control::placeholder{color:rgba(255,255,255,0.3)}
.btn-login{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;padding:14px;font-size:15px;font-weight:600;color:white;width:100%;margin-top:8px;transition:all 0.3s;box-shadow:0 8px 20px rgba(102,126,234,0.3)}
.btn-login:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(102,126,234,0.5);color:white}
.alert-custom{background:rgba(220,53,69,0.15);border:1px solid rgba(220,53,69,0.3);border-radius:12px;color:#ff6b7a;font-size:13px;padding:10px 14px;margin-bottom:20px}
.footer-text{text-align:center;color:rgba(255,255,255,0.25);font-size:11px;margin-top:24px}
.mb-field{margin-bottom:16px}
</style>
</head>
<body>
<div class="card">
  <div class="text-center">
    <div class="logo-box"><i class="fas fa-calendar-check"></i></div>
    <div class="brand">LeaveFlow</div>
    <div class="brand-sub">Employee Leave Management System</div>
  </div>
  {% if error %}<div class="alert-custom"><i class="fas fa-exclamation-circle me-2"></i>{{ error }}</div>{% endif %}
  <form method="POST">
    {% csrf_token %}
    <div class="mb-field">
      <label class="field-label"><i class="fas fa-envelope me-1"></i>Email Address</label>
      <div class="input-group">
        <span class="input-group-text"><i class="fas fa-envelope"></i></span>
        <input type="email" name="email" class="form-control" placeholder="you@company.com" required>
      </div>
    </div>
    <div class="mb-field">
      <label class="field-label"><i class="fas fa-lock me-1"></i>Password</label>
      <div class="input-group">
        <span class="input-group-text"><i class="fas fa-lock"></i></span>
        <input type="password" name="password" class="form-control" placeholder="Enter your password" required>
      </div>
    </div>
    <button type="submit" class="btn-login"><i class="fas fa-sign-in-alt me-2"></i>Sign In to LeaveFlow</button>
  </form>
  <div class="footer-text">© 2025 LeaveFlow &middot; All rights reserved</div>
</div>
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
*{box-sizing:border-box}body{background:#f0f2f8;font-family:'Segoe UI',sans-serif;margin:0}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:240px;background:linear-gradient(180deg,#0f0c29,#302b63);z-index:100;box-shadow:4px 0 20px rgba(0,0,0,0.3);display:flex;flex-direction:column}
.sidebar-logo{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:11px}
.logo-box{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:11px;display:flex;align-items:center;justify-content:center}
.logo-box i{color:white;font-size:17px}
.logo-text{color:white;font-size:17px;font-weight:700}
.logo-sub2{color:rgba(255,255,255,0.35);font-size:10px}
.sidebar-nav{padding:14px 10px;flex:1}
.nav-section-label{color:rgba(255,255,255,0.25);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 14px 5px}
.nav-item{display:flex;align-items:center;gap:11px;padding:10px 14px;border-radius:9px;color:rgba(255,255,255,0.55);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.nav-item:hover,.nav-item.active{background:rgba(102,126,234,0.2);color:white}
.nav-item i{width:17px;text-align:center;font-size:13px}
.sidebar-footer{padding:14px 10px;border-top:1px solid rgba(255,255,255,0.08)}
.user-card{display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:9px;background:rgba(255,255,255,0.06)}
.user-avatar{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;color:white;font-size:14px;font-weight:700;flex-shrink:0}
.user-name{color:white;font-size:12px;font-weight:600}
.user-role{color:rgba(255,255,255,0.4);font-size:10px}
.main{margin-left:240px;padding:26px 30px;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.page-title{font-size:21px;font-weight:700;color:#1a1d2e}
.page-sub{font-size:13px;color:#8a8ea8;margin-top:2px}
.btn-apply{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:11px;padding:10px 18px;font-size:13px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:7px;box-shadow:0 4px 14px rgba(102,126,234,0.35);transition:all 0.2s}
.btn-apply:hover{transform:translateY(-2px);color:white;box-shadow:0 8px 20px rgba(102,126,234,0.5)}
.info-row{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}
.info-chip{background:white;border-radius:8px;padding:6px 12px;font-size:12px;color:#5a5f7a;display:flex;align-items:center;gap:6px;box-shadow:0 1px 6px rgba(0,0,0,0.06)}
.info-chip i{color:#667eea}
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
.stat-card{background:white;border-radius:15px;padding:18px 20px;box-shadow:0 2px 10px rgba(0,0,0,0.05);position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat-card.c1::before{background:linear-gradient(90deg,#667eea,#764ba2)}
.stat-card.c2::before{background:linear-gradient(90deg,#11998e,#38ef7d)}
.stat-card.c3::before{background:linear-gradient(90deg,#f7971e,#ffd200)}
.stat-card.c4::before{background:linear-gradient(90deg,#eb3349,#f45c43)}
.stat-num{font-size:28px;font-weight:800;color:#1a1d2e}
.stat-label{font-size:11px;color:#8a8ea8;margin-top:3px;font-weight:500}
.stat-icon{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:34px;opacity:0.07}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}
.card-box{background:white;border-radius:15px;padding:20px 22px;box-shadow:0 2px 10px rgba(0,0,0,0.05)}
.card-title{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:16px;display:flex;align-items:center;gap:7px}
.card-title i{color:#667eea}
.att-num{font-size:50px;font-weight:800;background:linear-gradient(135deg,#11998e,#38ef7d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center}
.att-label{font-size:12px;color:#8a8ea8;text-align:center;margin-bottom:16px}
.prog-label{display:flex;justify-content:space-between;font-size:11px;color:#8a8ea8;margin-bottom:4px}
.progress{height:6px;border-radius:3px;background:#f0f2f8;margin-bottom:12px}
.progress-bar{border-radius:3px}
table{width:100%;border-collapse:collapse}
thead th{font-size:11px;font-weight:600;color:#8a8ea8;text-transform:uppercase;letter-spacing:.05em;padding:9px 11px;border-bottom:1px solid #f0f2f8}
tbody td{padding:11px 11px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9fe}
tbody tr:hover td{background:#fafbff}
.badge-s{display:inline-block;padding:3px 9px;border-radius:18px;font-size:11px;font-weight:600}
.bp{background:#fff8e1;color:#f59e0b}
.ba{background:#e8faf0;color:#10b981}
.br{background:#fee8e8;color:#ef4444}
.lt-badge{font-size:10px;padding:3px 7px;border-radius:5px;font-weight:600;background:#eef0ff;color:#667eea}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-box"><i class="fas fa-calendar-check"></i></div>
    <div><div class="logo-text">LeaveFlow</div><div class="logo-sub2">Leave Management</div></div>
  </div>
  <div class="sidebar-nav">
    <div class="nav-section-label">Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="nav-item active"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="nav-item"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="nav-section-label">Account</div>
    <a href="{% url 'logout' %}" class="nav-item"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sidebar-footer">
    <div class="user-card">
      <div class="user-avatar">{{ employee.name|first }}</div>
      <div><div class="user-name">{{ employee.name }}</div><div class="user-role">{{ employee.department }}</div></div>
    </div>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="page-title">Welcome back, {{ employee.name }} 👋</div>
      <div class="page-sub">Here's your leave overview for this year</div>
    </div>
    <a href="{% url 'apply_leave' %}" class="btn-apply"><i class="fas fa-plus"></i>Apply for Leave</a>
  </div>

  <div class="info-row">
    <div class="info-chip"><i class="fas fa-building"></i>{{ employee.department }}</div>
    <div class="info-chip"><i class="fas fa-envelope"></i>{{ employee.email }}</div>
    <div class="info-chip"><i class="fas fa-suitcase"></i>{{ employee.leave_balance }} days balance left</div>
    <div class="info-chip"><i class="fas fa-calendar-alt"></i>Joined: {{ employee.joined_date }}</div>
  </div>

  <div class="stats-grid">
    <div class="stat-card c1"><div class="stat-num">{{ leaves.count }}</div><div class="stat-label">Total Requests</div><i class="fas fa-file-alt stat-icon"></i></div>
    <div class="stat-card c2"><div class="stat-num">{{ approved }}</div><div class="stat-label">Approved</div><i class="fas fa-check-circle stat-icon"></i></div>
    <div class="stat-card c3"><div class="stat-num">{{ pending }}</div><div class="stat-label">Pending</div><i class="fas fa-clock stat-icon"></i></div>
    <div class="stat-card c4"><div class="stat-num">{{ rejected }}</div><div class="stat-label">Rejected</div><i class="fas fa-times-circle stat-icon"></i></div>
  </div>

  <div class="grid-2">
    <div class="card-box">
      <div class="card-title"><i class="fas fa-chart-line"></i>Attendance Overview</div>
      <div class="att-num">{{ employee.attendance_percent }}%</div>
      <div class="att-label">Overall Attendance Rate</div>
      <div class="prog-label"><span>Present</span><span>{{ employee.attendance_percent }}%</span></div>
      <div class="progress"><div class="progress-bar bg-success" style="width:{{ employee.attendance_percent }}%"></div></div>
      <div class="prog-label"><span>Absent / Leave</span><span>{{ attendance_gap }}%</span></div>
      <div class="progress"><div class="progress-bar bg-danger" style="width:{{ attendance_gap }}%"></div></div>
      <div class="prog-label"><span>Leave Balance Used</span><span>{{ employee.leave_balance }} days left</span></div>
      <div class="progress"><div class="progress-bar" style="width:{{ employee.leave_balance }}%;background:linear-gradient(90deg,#667eea,#764ba2)"></div></div>
    </div>
    <div class="card-box">
      <div class="card-title"><i class="fas fa-chart-pie"></i>Leave Status Breakdown</div>
      <canvas id="leaveChart" height="210"></canvas>
    </div>
  </div>

  <div class="card-box">
    <div class="card-title"><i class="fas fa-history"></i>Leave Request History</div>
    <table>
      <thead><tr><th>#</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Reason</th><th>Applied On</th><th>Status</th></tr></thead>
      <tbody>
      {% for leave in leaves %}
      <tr>
        <td>{{ forloop.counter }}</td>
        <td><span class="lt-badge">{{ leave.leave_type }}</span></td>
        <td>{{ leave.start_date }}</td>
        <td>{{ leave.end_date }}</td>
        <td><strong>{{ leave.days }}</strong></td>
        <td>{{ leave.reason }}</td>
        <td>{{ leave.applied_on }}</td>
        <td>
          {% if leave.status == 'APPROVED' %}<span class="badge-s ba"><i class="fas fa-check me-1"></i>Approved</span>
          {% elif leave.status == 'REJECTED' %}<span class="badge-s br"><i class="fas fa-times me-1"></i>Rejected</span>
          {% else %}<span class="badge-s bp"><i class="fas fa-clock me-1"></i>Pending</span>{% endif %}
        </td>
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
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved }},{{ pending }},{{ rejected }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:6}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:16,font:{size:12}}}},cutout:'65%'}
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
*{box-sizing:border-box}body{background:#f0f2f8;font-family:'Segoe UI',sans-serif;margin:0}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:240px;background:linear-gradient(180deg,#1a0533,#2d1b69);z-index:100;box-shadow:4px 0 20px rgba(0,0,0,0.3);display:flex;flex-direction:column}
.sidebar-logo{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:11px}
.logo-box{width:40px;height:40px;background:linear-gradient(135deg,#f093fb,#f5576c);border-radius:11px;display:flex;align-items:center;justify-content:center}
.logo-box i{color:white;font-size:17px}
.logo-text{color:white;font-size:17px;font-weight:700}
.logo-sub2{color:rgba(255,255,255,0.35);font-size:10px}
.sidebar-nav{padding:14px 10px;flex:1}
.nav-section-label{color:rgba(255,255,255,0.25);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 14px 5px}
.nav-item{display:flex;align-items:center;gap:11px;padding:10px 14px;border-radius:9px;color:rgba(255,255,255,0.55);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.nav-item:hover,.nav-item.active{background:rgba(240,147,251,0.15);color:white}
.nav-item i{width:17px;text-align:center;font-size:13px}
.sidebar-footer{padding:14px 10px;border-top:1px solid rgba(255,255,255,0.08)}
.user-card{display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:9px;background:rgba(255,255,255,0.06)}
.user-avatar{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#f093fb,#f5576c);display:flex;align-items:center;justify-content:center;color:white;font-size:14px;font-weight:700;flex-shrink:0}
.user-name{color:white;font-size:12px;font-weight:600}
.user-role{color:rgba(255,255,255,0.4);font-size:10px}
.main{margin-left:240px;padding:26px 30px;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.page-title{font-size:21px;font-weight:700;color:#1a1d2e}
.page-sub{font-size:13px;color:#8a8ea8;margin-top:2px}
.stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.stat-card{background:white;border-radius:15px;padding:20px 22px;box-shadow:0 2px 10px rgba(0,0,0,0.05);position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.c1::before{background:linear-gradient(90deg,#f093fb,#f5576c)}
.c2::before{background:linear-gradient(90deg,#667eea,#764ba2)}
.c3::before{background:linear-gradient(90deg,#11998e,#38ef7d)}
.stat-num{font-size:32px;font-weight:800;color:#1a1d2e}
.stat-label{font-size:11px;color:#8a8ea8;margin-top:3px;font-weight:500}
.stat-icon{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:38px;opacity:0.07}
.grid-2{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-bottom:20px}
.card-box{background:white;border-radius:15px;padding:20px 22px;box-shadow:0 2px 10px rgba(0,0,0,0.05);margin-bottom:20px}
.card-title{font-size:13px;font-weight:700;color:#1a1d2e;margin-bottom:16px;display:flex;align-items:center;gap:7px}
.card-title i{color:#f093fb}
table{width:100%;border-collapse:collapse}
thead th{font-size:11px;font-weight:600;color:#8a8ea8;text-transform:uppercase;letter-spacing:.05em;padding:9px 11px;border-bottom:1px solid #f0f2f8}
tbody td{padding:11px 11px;font-size:13px;color:#3a3d4e;border-bottom:1px solid #f8f9fe}
tbody tr:hover td{background:#fafbff}
.badge-s{display:inline-block;padding:3px 9px;border-radius:18px;font-size:11px;font-weight:600}
.bp{background:#fff8e1;color:#f59e0b}.ba{background:#e8faf0;color:#10b981}.br{background:#fee8e8;color:#ef4444}
.btn-app{background:linear-gradient(135deg,#11998e,#38ef7d);border:none;border-radius:7px;color:white;padding:5px 11px;font-size:11px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:4px;transition:all 0.2s}
.btn-app:hover{transform:translateY(-1px);color:white;box-shadow:0 4px 10px rgba(17,153,142,0.3)}
.btn-rej{background:linear-gradient(135deg,#eb3349,#f45c43);border:none;border-radius:7px;color:white;padding:5px 11px;font-size:11px;font-weight:600;text-decoration:none;display:inline-flex;align-items:center;gap:4px;margin-left:5px;transition:all 0.2s}
.btn-rej:hover{transform:translateY(-1px);color:white;box-shadow:0 4px 10px rgba(235,51,73,0.3)}
.att-bar{height:5px;border-radius:3px;background:#f0f2f8;margin-top:4px}
.att-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,#11998e,#38ef7d)}
.emp-avt{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#667eea,#764ba2);display:inline-flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:12px;margin-right:8px;flex-shrink:0}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-box"><i class="fas fa-shield-alt"></i></div>
    <div><div class="logo-text">LeaveFlow</div><div class="logo-sub2">Manager Panel</div></div>
  </div>
  <div class="sidebar-nav">
    <div class="nav-section-label">Menu</div>
    <a href="{% url 'manager_dashboard' %}" class="nav-item active"><i class="fas fa-th-large"></i>Dashboard</a>
    <div class="nav-section-label">Account</div>
    <a href="{% url 'logout' %}" class="nav-item"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
  <div class="sidebar-footer">
    <div class="user-card">
      <div class="user-avatar">M</div>
      <div><div class="user-name">{{ name }}</div><div class="user-role">Manager</div></div>
    </div>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <div>
      <div class="page-title">Manager Dashboard 🛡️</div>
      <div class="page-sub">Manage leave requests and monitor team attendance</div>
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card c1"><div class="stat-num">{{ total_emp }}</div><div class="stat-label">Total Employees</div><i class="fas fa-users stat-icon"></i></div>
    <div class="stat-card c2"><div class="stat-num">{{ pending_count }}</div><div class="stat-label">Pending Approvals</div><i class="fas fa-hourglass-half stat-icon"></i></div>
    <div class="stat-card c3"><div class="stat-num">{{ approved_count }}</div><div class="stat-label">Approved This Year</div><i class="fas fa-check-double stat-icon"></i></div>
  </div>

  <div class="grid-2">
    <div class="card-box" style="margin-bottom:0">
      <div class="card-title"><i class="fas fa-list-check"></i>All Leave Requests</div>
      <table>
        <thead><tr><th>Employee</th><th>Type</th><th>Start</th><th>End</th><th>Days</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
        {% for leave in leaves %}
        <tr>
          <td><div style="display:flex;align-items:center"><span class="emp-avt">{{ leave.employee.name|first }}</span><div><div style="font-weight:600;font-size:13px">{{ leave.employee.name }}</div><div style="font-size:10px;color:#aaa">{{ leave.employee.department }}</div></div></div></td>
          <td><span style="font-size:10px;background:#eef0ff;color:#667eea;padding:3px 7px;border-radius:5px;font-weight:600">{{ leave.leave_type }}</span></td>
          <td>{{ leave.start_date }}</td>
          <td>{{ leave.end_date }}</td>
          <td><strong>{{ leave.days }}</strong></td>
          <td>{% if leave.status == 'APPROVED' %}<span class="badge-s ba">Approved</span>{% elif leave.status == 'REJECTED' %}<span class="badge-s br">Rejected</span>{% else %}<span class="badge-s bp">Pending</span>{% endif %}</td>
          <td>{% if leave.status == 'PENDING' %}<a href="{% url 'update_status' leave.id 'APPROVED' %}" class="btn-app"><i class="fas fa-check"></i>Approve</a><a href="{% url 'update_status' leave.id 'REJECTED' %}" class="btn-rej"><i class="fas fa-times"></i>Reject</a>{% else %}<span style="color:#ccc;font-size:12px">Done</span>{% endif %}</td>
        </tr>
        {% empty %}
        <tr><td colspan="7" class="text-center py-4" style="color:#aaa">No leave requests found.</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="card-box" style="margin-bottom:0">
      <div class="card-title"><i class="fas fa-chart-pie"></i>Leave Overview</div>
      <canvas id="leaveChart" height="230"></canvas>
    </div>
  </div>

  <div class="card-box">
    <div class="card-title"><i class="fas fa-users"></i>Employee Attendance Tracker</div>
    <table>
      <thead><tr><th>Employee</th><th>Department</th><th>Email</th><th>Leave Balance</th><th>Attendance %</th><th>Status</th></tr></thead>
      <tbody>
      {% for emp in employees %}
      <tr>
        <td><div style="display:flex;align-items:center"><span class="emp-avt">{{ emp.name|first }}</span><strong>{{ emp.name }}</strong></div></td>
        <td>{{ emp.department }}</td>
        <td style="font-size:12px;color:#888">{{ emp.email }}</td>
        <td><strong>{{ emp.leave_balance }}</strong> days</td>
        <td>
          <strong>{{ emp.attendance_percent }}%</strong>
          <div class="att-bar"><div class="att-fill" style="width:{{ emp.attendance_percent }}%"></div></div>
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
  data:{labels:['Approved','Pending','Rejected'],datasets:[{data:[{{ approved_count }},{{ pending_count }},{{ rejected_count }}],backgroundColor:['#10b981','#f59e0b','#ef4444'],borderWidth:0,hoverOffset:6}]},
  options:{responsive:true,plugins:{legend:{position:'bottom',labels:{padding:16,font:{size:12}}}},cutout:'65%'}
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
*{box-sizing:border-box}body{background:#f0f2f8;font-family:'Segoe UI',sans-serif;margin:0}
.sidebar{position:fixed;top:0;left:0;height:100vh;width:240px;background:linear-gradient(180deg,#0f0c29,#302b63);z-index:100;box-shadow:4px 0 20px rgba(0,0,0,0.3);display:flex;flex-direction:column}
.sidebar-logo{padding:22px 18px;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:11px}
.logo-box{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:11px;display:flex;align-items:center;justify-content:center}
.logo-box i{color:white;font-size:17px}
.logo-text{color:white;font-size:17px;font-weight:700}
.logo-sub2{color:rgba(255,255,255,0.35);font-size:10px}
.sidebar-nav{padding:14px 10px;flex:1}
.nav-section-label{color:rgba(255,255,255,0.25);font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;padding:10px 14px 5px}
.nav-item{display:flex;align-items:center;gap:11px;padding:10px 14px;border-radius:9px;color:rgba(255,255,255,0.55);text-decoration:none;font-size:13px;font-weight:500;margin-bottom:3px;transition:all 0.2s}
.nav-item:hover,.nav-item.active{background:rgba(102,126,234,0.2);color:white}
.nav-item i{width:17px;text-align:center;font-size:13px}
.main{margin-left:240px;padding:40px 70px;min-height:100vh}
.page-title{font-size:21px;font-weight:700;color:#1a1d2e;margin-bottom:4px}
.page-sub{font-size:13px;color:#8a8ea8;margin-bottom:26px}
.form-card{background:white;border-radius:18px;padding:34px 38px;box-shadow:0 4px 22px rgba(0,0,0,0.07);max-width:580px}
.field-group{margin-bottom:20px}
.field-label{font-size:13px;font-weight:600;color:#3a3d4e;margin-bottom:7px;display:block}
.field-label i{color:#667eea;margin-right:6px}
.form-control,.form-select{border:1.5px solid #e8eaf0;border-radius:11px;padding:11px 13px;font-size:14px;color:#3a3d4e;transition:all 0.2s;background:#fafbff}
.form-control:focus,.form-select:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);background:white}
.date-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.btn-submit{background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:11px;padding:12px 26px;font-size:14px;font-weight:600;color:white;cursor:pointer;transition:all 0.2s;box-shadow:0 6px 16px rgba(102,126,234,0.35)}
.btn-submit:hover{transform:translateY(-2px);box-shadow:0 10px 22px rgba(102,126,234,0.5)}
.btn-back{background:#f0f2f8;border:none;border-radius:11px;padding:12px 20px;font-size:14px;font-weight:600;color:#5a5f7a;text-decoration:none;display:inline-flex;align-items:center;gap:6px;margin-right:10px;transition:all 0.2s}
.btn-back:hover{background:#e4e7f0;color:#3a3d4e}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-box"><i class="fas fa-calendar-check"></i></div>
    <div><div class="logo-text">LeaveFlow</div><div class="logo-sub2">Leave Management</div></div>
  </div>
  <div class="sidebar-nav">
    <div class="nav-section-label">Menu</div>
    <a href="{% url 'employee_dashboard' %}" class="nav-item"><i class="fas fa-th-large"></i>Dashboard</a>
    <a href="{% url 'apply_leave' %}" class="nav-item active"><i class="fas fa-plus-circle"></i>Apply Leave</a>
    <div class="nav-section-label">Account</div>
    <a href="{% url 'logout' %}" class="nav-item"><i class="fas fa-sign-out-alt"></i>Logout</a>
  </div>
</div>

<div class="main">
  <div class="page-title">Apply for Leave</div>
  <div class="page-sub">Fill in the details below to submit your leave request</div>
  <div class="form-card">
    <form method="POST">
      {% csrf_token %}
      <div class="field-group">
        <label class="field-label"><i class="fas fa-tag"></i>Leave Type</label>
        <select name="leave_type" class="form-select" required>
          <option value="CASUAL">Casual Leave</option>
          <option value="SICK">Sick Leave</option>
          <option value="ANNUAL">Annual Leave</option>
          <option value="EMERGENCY">Emergency Leave</option>
        </select>
      </div>
      <div class="date-row">
        <div class="field-group">
          <label class="field-label"><i class="fas fa-calendar-day"></i>Start Date</label>
          <input type="date" name="start" class="form-control" required>
        </div>
        <div class="field-group">
          <label class="field-label"><i class="fas fa-calendar-day"></i>End Date</label>
          <input type="date" name="end" class="form-control" required>
        </div>
      </div>
      <div class="field-group">
        <label class="field-label"><i class="fas fa-comment-alt"></i>Reason</label>
        <textarea name="reason" class="form-control" rows="4" placeholder="Briefly describe the reason for your leave..." required></textarea>
      </div>
      <div style="margin-top:6px">
        <a href="{% url 'employee_dashboard' %}" class="btn-back"><i class="fas fa-arrow-left"></i>Back</a>
        <button type="submit" class="btn-submit"><i class="fas fa-paper-plane me-2"></i>Submit Request</button>
      </div>
    </form>
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