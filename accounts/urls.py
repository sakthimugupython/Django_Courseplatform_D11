from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("courses/", views.courses, name="courses"),
    path("courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path("courses/new/", views.create_course, name="create_course"),
    path("courses/mine/", views.my_courses, name="my_courses"),
    path("courses/<int:course_id>/manage/", views.manage_course_progress, name="manage_course_progress"),
    path("progress/<int:pk>/edit/", views.update_progress, name="update_progress"),
    path("progress/<int:pk>/delete/", views.delete_progress, name="delete_progress"),
]
