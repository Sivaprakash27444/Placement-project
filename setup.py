import os

os.makedirs('employees/templates', exist_ok=True)

files = {}

files['employees/models.py'] = """from django.db import models

class Employee(models.Model):
    ROLE_CHOICES = [('EMPLOYEE','Employee'),('MANAGER','Manager')]
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return self.employee.name
"""

files['employees/views.py'] = """from django.shortcuts import render, redirect
from .models import Employee, LeaveRequest

def login_view(request):
    if request.method == 'POST':
        try:
            user = Employee.objects.get(email=request.POST['email'], password=request.POST['password'])
            request.session['user_id'] = user.id
            request.session['role'] = user.role
            if user.role == 'MANAGER':
                return redirect('manager_dashboard')
            return redirect('employee_dashboard')
        except:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def employee_dashboard(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    leaves = LeaveRequest.objects.filter(employee_id=request.session.get('user_id'))
    return render(request, 'employee_dashboard.html', {'leaves': leaves})

def manager_dashboard(request):
    if request.session.get('role') != 'MANAGER':
        return redirect('login')
    return render(request, 'manager_dashboard.html', {'leaves': LeaveRequest.objects.all()})

def apply_leave(request):
    if request.session.get('role') != 'EMPLOYEE':
        return redirect('login')
    if request.method == 'POST':
        LeaveRequest.objects.create(
            employee_id=request.session.get('user_id'),
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
<html>
<head>
<title>Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-5">
<div class="col-md-4 mx-auto bg-white p-4 rounded shadow">
<h3 class="text-center mb-4">Employee Login</h3>
{% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
<form method="POST">{% csrf_token %}
<input type="email" name="email" class="form-control mb-3" placeholder="Email" required>
<input type="password" name="password" class="form-control mb-3" placeholder="Password" required>
<button type="submit" class="btn btn-primary w-100">Login</button>
</form>
</div>
</div>
</body>
</html>
"""

files['employees/templates/employee_dashboard.html'] = """<!DOCTYPE html>
<html>
<head>
<title>Employee Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div class="container mt-4">
<h3>My Leaves</h3>
<a href="/apply/" class="btn btn-success mb-3">Apply Leave</a>
<table class="table table-bordered">
<tr><th>Start</th><th>End</th><th>Reason</th><th>Status</th></tr>
{% for leave in leaves %}
<tr>
<td>{{ leave.start_date }}</td>
<td>{{ leave.end_date }}</td>
<td>{{ leave.reason }}</td>
<td>{{ leave.status }}</td>
</tr>
{% endfor %}
</table>
</div>
</body>
</html>
"""

files['employees/templates/manager_dashboard.html'] = """<!DOCTYPE html>
<html>
<head>
<title>Manager Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div class="container mt-4">
<h3>All Leave Requests</h3>
<table class="table table-bordered">
<tr><th>Employee</th><th>Start</th><th>End</th><th>Reason</th><th>Status</th><th>Action</th></tr>
{% for leave in leaves %}
<tr>
<td>{{ leave.employee.name }}</td>
<td>{{ leave.start_date }}</td>
<td>{{ leave.end_date }}</td>
<td>{{ leave.reason }}</td>
<td>{{ leave.status }}</td>
<td>
<a href="/update/{{ leave.id }}/APPROVED/" class="btn btn-success btn-sm">Approve</a>
<a href="/update/{{ leave.id }}/REJECTED/" class="btn btn-danger btn-sm">Reject</a>
</td>
</tr>
{% endfor %}
</table>
</div>
</body>
</html>
"""

files['employees/templates/apply_leave.html'] = """<!DOCTYPE html>
<html>
<head>
<title>Apply Leave</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div class="container mt-4">
<h3>Apply Leave</h3>
<form method="POST">{% csrf_token %}
<input type="date" name="start" class="form-control mb-2" required>
<input type="date" name="end" class="form-control mb-2" required>
<textarea name="reason" class="form-control mb-2" placeholder="Reason" required></textarea>
<button class="btn btn-primary">Submit</button>
</form>
</div>
</body>
</html>
"""

for filepath, content in files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Created:", filepath)

print("\nALL FILES CREATED SUCCESSFULLY")