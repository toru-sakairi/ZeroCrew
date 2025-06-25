from django.urls import path
from . import views
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView

app_name = "projects"
urlpatterns = [
    # LP（ランディングページ）
    path('', views.home, name="home"),
    #path("home/", views.home, name="home"),
    path("create/", views.project_create, name="project_create"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy('projects:home')), name='logout'),
    path("search/", views.searchView, name="search_results"),
    path("project<int:pk>", views.project_detail, name="project_detail"),
    path("project/<int:pk>/apply/", views.apply_for_project, name="apply_for_project"),
    path("project/<int:pk>/applicants/", views.applicant_list, name="applicant_list"),
    path("application/<int:pk>/update/", views.update_application_status, name="update_application_status"),
    path("project/<int:pk>/chat/", views.project_chat, name="project_chat"),
    path('tags/<str:tag_slug>/', views.tagged_project_list, name='project_list_by_tag'),
]
