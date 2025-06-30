from django.urls import path
from . import views


app_name = "users"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path('verify/<uidb64>/<token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path("profile/<int:pk>/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("applications/", views.application_status, name="application_status"),
    path("messages/", views.conversation_list, name='conversation_list'),
    path("messages/<int:pk>/", views.conversation_detail, name="conversation_detail"),
    path("messages/start/<int:user_id>/", views.start_conversation,name="start_conversation"),
    path("follow/<int:pk>/", views.toggle_follow, name='toggle_follow'),
]
