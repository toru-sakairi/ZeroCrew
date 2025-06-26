from django.urls import path
from . import views


app_name = "users"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("profile/<int:pk>/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("applications/", views.application_status, name="application_status"),
    path("messages/", views.conversationList, name='conversation_list'),
    path("messages/<int:pk>/", views.conversationDetail, name="conversation_detail"),
    path("messages/start/<int:user_id>/", views.startConversation,name="start_conversation"),
    path("follow/<int:pk>/", views.toggle_follow, name='toggle_follow'),
]
