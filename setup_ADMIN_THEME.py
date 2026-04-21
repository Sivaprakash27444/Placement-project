import os, sys

if not os.path.exists('manage.py'):
    print("ERROR: Run this from inside leave_management folder (where manage.py is).")
    sys.exit(1)

print("Setting up professional admin theme...")
os.makedirs('employees/static/employees/css', exist_ok=True)
os.makedirs('employees/templates/admin', exist_ok=True)

files = {}

# ── Custom Admin CSS ──────────────────────────────────────────────────────────
files['employees/static/employees/css/admin_theme.css'] = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── BASE ── */
:root {
  --primary: #4f46e5;
  --primary-dark: #3730a3;
  --accent: #6366f1;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --bg: #0f1117;
  --surface: #1a1d2e;
  --surface2: #232640;
  --border: rgba(255,255,255,0.08);
  --text: #e2e8f0;
  --muted: #8892b0;
}

* { font-family: 'Inter', sans-serif !important; }

body {
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* ── HEADER ── */
#header {
  background: linear-gradient(135deg, #0f0c29, #302b63) !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 0 24px !important;
  height: 60px !important;
  display: flex !important;
  align-items: center !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
}

#branding h1, #branding h1 a {
  font-size: 22px !important;
  font-weight: 800 !important;
  color: white !important;
  letter-spacing: -0.5px !important;
}

#branding h1 a::before {
  content: '📅 ';
}

#user-tools {
  color: rgba(255,255,255,0.6) !important;
  font-size: 12px !important;
}

#user-tools a {
  color: #a5b4fc !important;
  font-weight: 600 !important;
}

/* ── NAV / SIDEBAR ── */
#nav-sidebar {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
  padding: 16px 0 !important;
}

#nav-sidebar .module caption,
.app-employees > caption {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important;
  font-weight: 700 !important;
  font-size: 11px !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  padding: 10px 16px !important;
  border-radius: 8px 8px 0 0 !important;
}

/* ── CONTENT AREA ── */
#content, #content-main {
  background: var(--bg) !important;
}

#content h1 {
  font-size: 24px !important;
  font-weight: 800 !important;
  color: white !important;
  margin-bottom: 20px !important;
}

/* ── MODULES / CARDS ── */
.module {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  margin-bottom: 20px !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

.module h2, .module caption {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important;
  font-weight: 700 !important;
  padding: 12px 18px !important;
  font-size: 13px !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
}

/* ── TABLES ── */
#result_list {
  background: var(--surface) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  width: 100% !important;
}

#result_list thead th {
  background: var(--surface2) !important;
  color: var(--muted) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  padding: 13px 16px !important;
  border-bottom: 1px solid var(--border) !important;
}

#result_list thead th a {
  color: var(--muted) !important;
}

#result_list thead th.sorted a {
  color: #a5b4fc !important;
}

#result_list tbody tr {
  border-bottom: 1px solid var(--border) !important;
  transition: background 0.15s !important;
}

#result_list tbody tr:hover {
  background: rgba(99,102,241,0.08) !important;
}

#result_list tbody td {
  padding: 13px 16px !important;
  color: var(--text) !important;
  font-size: 13px !important;
  vertical-align: middle !important;
  border: none !important;
}

#result_list tbody tr.selected {
  background: rgba(99,102,241,0.15) !important;
}

/* ── CHECKBOXES ── */
input[type=checkbox] {
  accent-color: var(--primary) !important;
  width: 16px !important;
  height: 16px !important;
}

/* ── ACTION BAR ── */
.actions {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 12px 16px !important;
  margin-bottom: 16px !important;
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
}

.actions select {
  background: var(--surface) !important;
  color: white !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
}

.actions button[type=submit], .actions input[type=submit] {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 8px 18px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  box-shadow: 0 4px 12px rgba(79,70,229,0.4) !important;
  transition: all 0.2s !important;
}

.actions button[type=submit]:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 16px rgba(79,70,229,0.5) !important;
}

/* ── SEARCH BAR ── */
#searchbar, input[name=q] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: white !important;
  padding: 9px 14px !important;
  font-size: 13px !important;
  width: 280px !important;
}

#searchbar:focus, input[name=q]:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
  outline: none !important;
}

input[type=submit][value=Search] {
  background: var(--primary) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 9px 16px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
}

/* ── FILTERS ── */
#changelist-filter {
  background: var(--surface) !important;
  border-left: 1px solid var(--border) !important;
  padding: 16px !important;
}

#changelist-filter h2 {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  padding: 10px 14px !important;
  border-radius: 8px !important;
  margin-bottom: 12px !important;
}

#changelist-filter h3 {
  color: var(--muted) !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  margin: 14px 0 6px !important;
}

#changelist-filter ul {
  padding: 0 !important;
  list-style: none !important;
}

#changelist-filter ul li a {
  color: rgba(255,255,255,0.6) !important;
  font-size: 13px !important;
  padding: 6px 10px !important;
  border-radius: 6px !important;
  display: block !important;
  transition: all 0.15s !important;
}

#changelist-filter ul li a:hover,
#changelist-filter ul li.selected a {
  background: rgba(99,102,241,0.15) !important;
  color: #a5b4fc !important;
}

/* ── SUBMIT ROW (Save buttons) ── */
.submit-row {
  background: var(--surface2) !important;
  border-top: 1px solid var(--border) !important;
  border-radius: 0 0 12px 12px !important;
  padding: 14px 18px !important;
  gap: 10px !important;
  display: flex !important;
}

.submit-row input[type=submit] {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 20px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  box-shadow: 0 4px 12px rgba(79,70,229,0.35) !important;
}

.submit-row a.deletelink {
  background: var(--danger) !important;
  color: white !important;
  border-radius: 8px !important;
  padding: 10px 20px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
}

/* ── FORM FIELDS ── */
.form-row {
  border-bottom: 1px solid var(--border) !important;
  padding: 14px 18px !important;
}

.form-row label {
  color: var(--muted) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

input[type=text], input[type=email], input[type=password],
input[type=number], select, textarea {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: white !important;
  padding: 9px 12px !important;
  font-size: 13px !important;
}

input[type=text]:focus, select:focus, textarea:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
  outline: none !important;
}

/* ── MESSAGES / ALERTS ── */
.messagelist li {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  padding: 12px 18px !important;
  margin-bottom: 10px !important;
}

.messagelist li.success {
  background: rgba(16,185,129,0.15) !important;
  border: 1px solid rgba(16,185,129,0.3) !important;
  color: #6ee7b7 !important;
}

.messagelist li.error {
  background: rgba(239,68,68,0.15) !important;
  border: 1px solid rgba(239,68,68,0.3) !important;
  color: #fca5a5 !important;
}

.messagelist li.warning {
  background: rgba(245,158,11,0.15) !important;
  border: 1px solid rgba(245,158,11,0.3) !important;
  color: #fcd34d !important;
}

/* ── BREADCRUMBS ── */
.breadcrumbs {
  background: var(--surface) !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 10px 24px !important;
  font-size: 12px !important;
}

.breadcrumbs a {
  color: #a5b4fc !important;
}

/* ── PAGINATOR ── */
.paginator {
  color: var(--muted) !important;
  font-size: 13px !important;
}

.paginator a {
  background: var(--surface2) !important;
  color: white !important;
  border-radius: 6px !important;
  padding: 4px 10px !important;
  border: 1px solid var(--border) !important;
}

/* ── INDEX PAGE APP LIST ── */
#content-main .app-employees th a {
  color: #a5b4fc !important;
  font-weight: 700 !important;
}

#content-main td.addlink a, #content-main td.changelink a {
  color: var(--primary) !important;
  font-weight: 600 !important;
}

/* ── OBJECT TOOLS (top-right Add button) ── */
.object-tools a {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important;
  border-radius: 8px !important;
  padding: 8px 16px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  box-shadow: 0 4px 12px rgba(79,70,229,0.35) !important;
}

/* ── QUICK APPROVE/REJECT BUTTONS on change form ── */
.approve-btn {
  display: inline-block;
  background: linear-gradient(135deg, #10b981, #059669) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 22px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  box-shadow: 0 4px 12px rgba(16,185,129,0.35) !important;
  margin-right: 8px !important;
  text-decoration: none !important;
}

.reject-btn {
  display: inline-block;
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 22px !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  box-shadow: 0 4px 12px rgba(239,68,68,0.35) !important;
  text-decoration: none !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
"""

# ── Admin base override with quick approve/reject on change form ──────────────
files['employees/templates/admin/base_site.html'] = """{% extends "admin/base.html" %}
{% load i18n %}

{% block title %}{% if subtitle %}{{ subtitle }} | {% endif %}{{ title }} | LeaveFlow Admin{% endblock %}

{% block extrastyle %}
{{ block.super }}
<link rel="stylesheet" href="/static/employees/css/admin_theme.css">
<style>
/* Extra quick-action styles inline */
.quick-actions {
  display: flex;
  gap: 10px;
  margin: 16px 0;
  padding: 16px 20px;
  background: #1a1d2e;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  align-items: center;
}
.quick-actions span {
  color: #8892b0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 6px;
}
</style>
{% endblock %}

{% block branding %}
<h1 id="site-name">
  <a href="{% url 'admin:index' %}">
    &#x1F4C5; LeaveFlow Administration
  </a>
</h1>
{% endblock %}

{% block nav-global %}{% endblock %}
"""

# ── Updated admin.py with quick approve/reject on the change form ─────────────
files['employees/admin.py'] = """from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Employee, LeaveRequest

admin.site.site_header  = 'LeaveFlow Administration'
admin.site.site_title   = 'LeaveFlow Admin'
admin.site.index_title  = 'Leave Management Control Panel'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'role_badge', 'department',
                     'attendance_bar', 'leave_balance', 'joined_date')
    list_filter   = ('role', 'department')
    search_fields = ('name', 'email')
    ordering      = ('name',)

    @admin.display(description='Attendance %')
    def attendance_bar(self, obj):
        pct   = obj.attendance_percent
        color = '#10b981' if pct >= 90 else ('#f59e0b' if pct >= 75 else '#ef4444')
        label = 'Excellent' if pct >= 90 else ('Average' if pct >= 75 else 'Poor')
        return format_html(
            '<div style="min-width:170px">'
            '<div style="display:flex;justify-content:space-between;'
            'font-size:12px;margin-bottom:4px">'
            '<span style="font-weight:700;color:{}">{:.1f}%</span>'
            '<span style="color:#888;font-size:11px">{}</span></div>'
            '<div style="background:#2d3148;border-radius:4px;height:8px">'
            '<div style="width:{:.0f}%;background:{};border-radius:4px;height:8px"></div>'
            '</div></div>',
            color, pct, label, pct, color
        )

    @admin.display(description='Role')
    def role_badge(self, obj):
        if obj.role == 'MANAGER':
            return format_html(
                '<span style="background:#3b0764;color:#c084fc;padding:4px 12px;'
                'border-radius:20px;font-size:11px;font-weight:700;'
                'border:1px solid #7c3aed">&#x1F6E1; Manager</span>'
            )
        return format_html(
            '<span style="background:#1e3a5f;color:#60a5fa;padding:4px 12px;'
            'border-radius:20px;font-size:11px;font-weight:700;'
            'border:1px solid #1d4ed8">&#x1F464; Employee</span>'
        )


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee_info', 'leave_type_badge', 'date_range',
                     'duration', 'reason_short', 'status_badge',
                     'applied_on', 'quick_actions')
    list_filter   = ('status', 'leave_type', 'employee__department')
    search_fields = ('employee__name', 'reason')
    ordering      = ('-applied_on',)
    actions       = ['approve_leaves', 'reject_leaves']
    list_per_page = 20

    # ── Custom URLs for quick approve/reject ─────────────────────────────────
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
        messages.success(request,
            '{} leave request for {} has been APPROVED.'.format(
                obj.leave_type, obj.employee.name))
        return redirect('../..')

    def reject_view(self, request, pk):
        obj = get_object_or_404(LeaveRequest, pk=pk)
        obj.status = 'REJECTED'
        obj.save()
        messages.error(request,
            '{} leave request for {} has been REJECTED.'.format(
                obj.leave_type, obj.employee.name))
        return redirect('../..')

    # ── Display columns ───────────────────────────────────────────────────────
    @admin.display(description='Employee')
    def employee_info(self, obj):
        initials = obj.employee.name[0].upper()
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px">'
            '<div style="width:34px;height:34px;border-radius:9px;'
            'background:linear-gradient(135deg,#4f46e5,#7c3aed);'
            'display:flex;align-items:center;justify-content:center;'
            'color:white;font-weight:700;font-size:14px;flex-shrink:0">{}</div>'
            '<div><div style="font-weight:700;font-size:13px;color:#e2e8f0">{}</div>'
            '<div style="font-size:11px;color:#8892b0">{}</div></div></div>',
            initials, obj.employee.name, obj.employee.department
        )

    @admin.display(description='Leave Type')
    def leave_type_badge(self, obj):
        colors = {
            'SICK':      ('#1e3a5f', '#60a5fa'),
            'CASUAL':    ('#1a2e1a', '#4ade80'),
            'ANNUAL':    ('#3b2a00', '#fbbf24'),
            'EMERGENCY': ('#3b0a0a', '#f87171'),
        }
        bg, fg = colors.get(obj.leave_type, ('#1e293b', '#94a3b8'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:6px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.get_leave_type_display()
        )

    @admin.display(description='Date Range')
    def date_range(self, obj):
        return format_html(
            '<span style="font-size:12px;color:#a5b4fc;font-weight:600">'
            '{} &rarr; {}</span>',
            obj.start_date, obj.end_date
        )

    @admin.display(description='Days')
    def duration(self, obj):
        d = obj.days()
        return format_html(
            '<span style="background:#1e293b;color:#e2e8f0;padding:4px 10px;'
            'border-radius:6px;font-weight:700;font-size:13px">{}</span>',
            d
        )

    @admin.display(description='Reason')
    def reason_short(self, obj):
        r = obj.reason[:40] + '...' if len(obj.reason) > 40 else obj.reason
        return format_html(
            '<span style="color:#8892b0;font-size:12px">{}</span>', r)

    @admin.display(description='Status')
    def status_badge(self, obj):
        cfg = {
            'PENDING':  ('#3b2a00', '#fbbf24', '&#x23F3; Pending'),
            'APPROVED': ('#052e16', '#4ade80', '&#x2705; Approved'),
            'REJECTED': ('#3b0a0a', '#f87171', '&#x274C; Rejected'),
        }
        bg, fg, label = cfg.get(obj.status, ('#1e293b', '#94a3b8', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:5px 12px;'
            'border-radius:20px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, label
        )

    @admin.display(description='Quick Action')
    def quick_actions(self, obj):
        if obj.status == 'PENDING':
            return format_html(
                '<a href="{}/approve/" style="display:inline-block;'
                'background:linear-gradient(135deg,#10b981,#059669);'
                'color:white;border-radius:7px;padding:5px 12px;'
                'font-size:11px;font-weight:700;text-decoration:none;'
                'margin-right:5px;box-shadow:0 3px 8px rgba(16,185,129,0.35)">'
                '&#x2713; Approve</a>'
                '<a href="{}/reject/" style="display:inline-block;'
                'background:linear-gradient(135deg,#ef4444,#dc2626);'
                'color:white;border-radius:7px;padding:5px 12px;'
                'font-size:11px;font-weight:700;text-decoration:none;'
                'box-shadow:0 3px 8px rgba(239,68,68,0.35)">'
                '&#x2717; Reject</a>',
                obj.pk, obj.pk
            )
        elif obj.status == 'APPROVED':
            return format_html(
                '<a href="{}/reject/" style="display:inline-block;'
                'background:#1e293b;color:#f87171;border-radius:7px;'
                'padding:5px 12px;font-size:11px;font-weight:700;'
                'text-decoration:none;border:1px solid #3b0a0a">'
                'Revoke</a>', obj.pk
            )
        else:
            return format_html(
                '<a href="{}/approve/" style="display:inline-block;'
                'background:#1e293b;color:#4ade80;border-radius:7px;'
                'padding:5px 12px;font-size:11px;font-weight:700;'
                'text-decoration:none;border:1px solid #052e16">'
                'Re-approve</a>', obj.pk
            )

    @admin.action(description='✅  Approve selected leave requests')
    def approve_leaves(self, request, queryset):
        count = queryset.update(status='APPROVED')
        self.message_user(request,
            '{} leave request(s) approved successfully.'.format(count))

    @admin.action(description='❌  Reject selected leave requests')
    def reject_leaves(self, request, queryset):
        count = queryset.update(status='REJECTED')
        self.message_user(request,
            '{} leave request(s) rejected.'.format(count), messages.ERROR)
"""

# Write all files
for filepath, content in files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Created:', filepath)

# Patch settings.py for STATICFILES_DIRS and APP_DIRS
settings_path = 'leave_management/settings.py'
with open(settings_path, 'r', encoding='utf-8') as f:
    settings = f.read()

# Ensure employees in INSTALLED_APPS
if "'employees'" not in settings and '"employees"' not in settings:
    settings = settings.replace(
        "'django.contrib.staticfiles',",
        "'django.contrib.staticfiles',\n    'employees',"
    )
    print("Patched: added 'employees' to INSTALLED_APPS")

# Patch TEMPLATES to ensure APP_DIRS is True (for admin template override)
if 'APP_DIRS' in settings and "'APP_DIRS': False" in settings:
    settings = settings.replace("'APP_DIRS': False", "'APP_DIRS': True")
    print("Patched: APP_DIRS set to True")

with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(settings)

print()
print("=" * 55)
print("  ALL FILES CREATED SUCCESSFULLY!")
print("=" * 55)
print()
print("Next steps:")
print("  python manage.py collectstatic --noinput")
print("  python manage.py runserver")
print()
print("Then open: http://127.0.0.1:8000/admin/")
print("  Hard refresh: Ctrl + Shift + R")
