from django.db import models

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
