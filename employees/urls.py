from django.urls import path
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
