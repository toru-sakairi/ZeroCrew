from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 2025/06/22 projects.urlのやつのパスをサーバー側のやつに合わせた。エラー出たら治して
urlpatterns = [
    path('', include('projects.urls')),
    path('admin/', admin.site.urls),
    path('users/', include("users.urls")),
    # path('projects/', include("projects.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    
