from django.shortcuts import render, redirect
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
