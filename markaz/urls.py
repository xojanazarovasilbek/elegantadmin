from django.urls import path
from . import views
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ... boshqa url-lar
    path('', views.custom_login, name='login'),
    path('logout/',views.logout_view, name='logout'),

    # Asosiy sahifa (Dashboard)
    path('bosh-sahifa/', views.dashboard, name='dashboard'),
    
    # O'quvchilar va Ustozlar ro'yxati
    path('students/', views.student_list, name='student_list'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    
    # Guruhlar va Davomat
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/attendance/', views.group_attendance_view, name='take_attendance'),
    
    # To'lovlar
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('student/<int:student_id>/payment/', views.student_payment, name='add_payment'),
    
    # Davomat natijalari (Kelgan/Kelmaganlar filtri)
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    path('attendance/edit/<int:pk>/', views.attendance_edit, name='attendance_edit'),

 
    # O'quvchilar
    path('student/add/', views.student_create, name='student_create'),
    path('student/<int:pk>/edit/', views.student_update, name='student_update'),
    path('student/<int:pk>/delete/', views.student_delete, name='student_delete'),
    
    # Guruhlar
    path('group/add/', views.group_create, name='group_create'),
    # path('group/<int:pk>/edit/', views.group_update, name='group_update'), # Funksiyasini yuqoridagidek yozasiz
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teacher/add-new/', views.teacher_create_simple, name='teacher_create'),
    path('teacher/<int:pk>/edit/', views.teacher_update, name='teacher_update'),
    path('teacher/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),

    path('student/<int:student_id>/move/', views.move_student, name='move_student'),
    path('group/<int:group_id>/change-teacher/', views.change_group_teacher, name='change_teacher'),

    path('reports/finance/', views.financial_report, name='financial_report'),
    path('reports/finance/add/', views.add_expense, name='add_expense'),


    path('schedule/', views.schedule_view, name='schedule_view'),
    path('schedule/edit/<int:group_id>/', views.schedule_edit, name='schedule_edit'),


    path("groups/<int:pk>/delete/", views.delete_group, name="delete_groups"),


]