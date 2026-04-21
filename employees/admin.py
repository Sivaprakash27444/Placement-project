from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Employee, LeaveRequest

admin.site.site_header  = 'S4 Limited — Administration'
admin.site.site_title   = 'S4 Limited Admin'
admin.site.index_title  = 'Leave Management Control Panel'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('name','email','role_badge','department',
                     'attendance_bar','leave_balance')
    list_filter   = ('role','department')
    search_fields = ('name','email')
    ordering      = ('name',)

    @admin.display(description='Attendance')
    def attendance_bar(self, obj):
        pct   = obj.attendance_percent
        color = '#10b981' if pct >= 90 else ('#f59e0b' if pct >= 75 else '#ef4444')
        label = 'Excellent' if pct >= 90 else ('Average' if pct >= 75 else 'Poor')
        return format_html(
            '<div style="min-width:180px">'
            '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">'
            '<span style="font-weight:700;color:{}">{:.1f}%</span>'
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{}</span>'
            '</div>'
            '<div style="background:#2d3148;border-radius:4px;height:8px">'
            '<div style="width:{:.0f}%;background:{};border-radius:4px;height:8px"></div>'
            '</div></div>',
            color, pct, color, label, pct, color
        )

    @admin.display(description='Role')
    def role_badge(self, obj):
        if obj.role == 'MANAGER':
            return format_html(
                '<span style="background:#3b0764;color:#c084fc;padding:4px 12px;'
                'border-radius:20px;font-size:11px;font-weight:700;'
                'border:1px solid #7c3aed">&#128737; Manager</span>'
            )
        return format_html(
            '<span style="background:#1e3a5f;color:#60a5fa;padding:4px 12px;'
            'border-radius:20px;font-size:11px;font-weight:700;'
            'border:1px solid #1d4ed8">&#128100; Employee</span>'
        )


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee_info','leave_type_badge','date_range',
                     'duration','reason_short','status_badge','quick_actions')
    list_filter   = ('status','leave_type','employee__department')
    search_fields = ('employee__name','reason')
    ordering      = ('-id',)
    actions       = ['approve_leaves','reject_leaves']
    list_per_page = 25

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/approve/',
                 self.admin_site.admin_view(self.approve_view),
                 name='leaverequest_approve'),
            path('<int:pk>/reject/',
                 self.admin_site.admin_view(self.reject_view),
                 name='leaverequest_reject'),
        ]
        return custom + urls

    def approve_view(self, request, pk):
        obj = get_object_or_404(LeaveRequest, pk=pk)
        obj.status = 'APPROVED'
        obj.save()
        emp  = obj.employee
        days = obj.days()
        emp.attendance_percent = max(0, round(emp.attendance_percent - days * 0.5, 1))
        emp.leave_balance      = max(0, emp.leave_balance - days)
        emp.save()
        messages.success(request,
            '{} leave for {} APPROVED. Attendance updated.'.format(
                obj.get_leave_type_display(), obj.employee.name))
        return redirect('../../')

    def reject_view(self, request, pk):
        obj = get_object_or_404(LeaveRequest, pk=pk)
        obj.status = 'REJECTED'
        obj.save()
        messages.error(request,
            '{} leave for {} REJECTED.'.format(
                obj.get_leave_type_display(), obj.employee.name))
        return redirect('../../')

    @admin.display(description='Employee')
    def employee_info(self, obj):
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px">'
            '<div style="width:36px;height:36px;border-radius:10px;'
            'background:linear-gradient(135deg,#4f46e5,#7c3aed);'
            'display:flex;align-items:center;justify-content:center;'
            'color:white;font-weight:800;font-size:15px;flex-shrink:0">{}</div>'
            '<div><div style="font-weight:700;font-size:13px;color:#e2e8f0">{}</div>'
            '<div style="font-size:11px;color:#8892b0">{}</div></div></div>',
            obj.employee.name[0].upper(), obj.employee.name, obj.employee.department
        )

    @admin.display(description='Leave Type')
    def leave_type_badge(self, obj):
        colors = {
            'SICK':      ('#1e3a5f','#60a5fa'),
            'CASUAL':    ('#1a2e1a','#4ade80'),
            'ANNUAL':    ('#3b2a00','#fbbf24'),
            'EMERGENCY': ('#3b0a0a','#f87171'),
        }
        bg, fg = colors.get(obj.leave_type, ('#1e293b','#94a3b8'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:6px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.get_leave_type_display()
        )

    @admin.display(description='Dates')
    def date_range(self, obj):
        return format_html(
            '<span style="font-size:12px;color:#a5b4fc;font-weight:600">'
            '{}<br>{}</span>', obj.start_date, obj.end_date)

    @admin.display(description='Days')
    def duration(self, obj):
        d = obj.days()
        return format_html(
            '<span style="background:#1e293b;color:#e2e8f0;padding:4px 10px;'
            'border-radius:6px;font-weight:800;font-size:14px">{}</span>', d)

    @admin.display(description='Reason')
    def reason_short(self, obj):
        r = obj.reason[:35] + '...' if len(obj.reason) > 35 else obj.reason
        return format_html('<span style="color:#8892b0;font-size:12px">{}</span>', r)

    @admin.display(description='Status')
    def status_badge(self, obj):
        cfg = {
            'PENDING':  ('#3b2a00','#fbbf24','&#9203; Pending'),
            'APPROVED': ('#052e16','#4ade80','&#9989; Approved'),
            'REJECTED': ('#3b0a0a','#f87171','&#10060; Rejected'),
        }
        bg, fg, label = cfg.get(obj.status, ('#1e293b','#94a3b8', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:5px 12px;'
            'border-radius:20px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, label)

    @admin.display(description='Action')
    def quick_actions(self, obj):
        if obj.status == 'PENDING':
            return format_html(
                '<a href="{}/approve/" style="display:inline-block;background:'
                'linear-gradient(135deg,#10b981,#059669);color:white;border-radius:7px;'
                'padding:6px 13px;font-size:11px;font-weight:700;text-decoration:none;'
                'margin-right:5px;box-shadow:0 3px 8px rgba(16,185,129,.4)">'
                '&#10003; Approve</a>'
                '<a href="{}/reject/" style="display:inline-block;background:'
                'linear-gradient(135deg,#ef4444,#dc2626);color:white;border-radius:7px;'
                'padding:6px 13px;font-size:11px;font-weight:700;text-decoration:none;'
                'box-shadow:0 3px 8px rgba(239,68,68,.4)">'
                '&#10007; Reject</a>',
                obj.pk, obj.pk)
        elif obj.status == 'APPROVED':
            return format_html(
                '<a href="{}/reject/" style="display:inline-block;background:#1e293b;'
                'color:#f87171;border-radius:7px;padding:6px 13px;font-size:11px;'
                'font-weight:700;text-decoration:none;border:1px solid #3b0a0a">Revoke</a>',
                obj.pk)
        return format_html(
            '<a href="{}/approve/" style="display:inline-block;background:#1e293b;'
            'color:#4ade80;border-radius:7px;padding:6px 13px;font-size:11px;'
            'font-weight:700;text-decoration:none;border:1px solid #052e16">Re-approve</a>',
            obj.pk)

    @admin.action(description='Approve selected leave requests')
    def approve_leaves(self, request, queryset):
        count = queryset.update(status='APPROVED')
        self.message_user(request, '{} request(s) approved.'.format(count))

    @admin.action(description='Reject selected leave requests')
    def reject_leaves(self, request, queryset):
        count = queryset.update(status='REJECTED')
        self.message_user(request, '{} request(s) rejected.'.format(count), messages.ERROR)
