from django.urls import path
from . import views


app_name = "projects"
urlpatterns = [
    path("home/", views.home, name="home"),
    path("create/", views.project_create, name="project_create"),
    path("project<int:pk>", views.project_detail, name="project_detail"),
    path("project/<int:pk>/apply/", views.apply_for_project, name="apply_for_project"),
    path("project/<int:pk>/applicants/", views.applicant_list, name="applicant_list"),
    path("application/<int:pk>/update/", views.update_application_status, name="update_application_status"),
    path("project/<int:pk>/chat/", views.project_chat, name="project_chat"),
]
