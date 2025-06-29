from django.urls import path
from . import views
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView
from projects.views import health_check

app_name = "projects"
urlpatterns = [
    # LP（ランディングページ）
    path('', views.home, name="home"),
    #path("home/", views.home, name="home"),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('projects:home')), name='logout'),
    path('search/', views.searchView, name="search_results"),
    path('project/create/', views.project_create, name="project_create"),
    path('project<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('project<int:pk>/detail/', views.project_detail, name="project_detail"),
    path('project<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('project/<int:pk>/apply/', views.apply_for_project, name="apply_for_project"),
    path('project/<int:pk>/applicants/', views.applicant_list, name="applicant_list"),
    path('application/<int:pk>/update/', views.update_application_status, name="update_application_status"),
    path('project/<int:pk>/chat/', views.project_chat, name="project_chat"),
    path('tags/<str:tag_slug>/', views.tagged_project_list, name='project_list_by_tag'),
    path('project/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('health/', health_check, name='health_check'),
]
