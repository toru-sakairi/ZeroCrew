from django.urls import path
from .views import TermsOfServiceView, PrivacyPolicyView

# アプリケーションの名前空間を設定
app_name = 'pages'

urlpatterns = [
    # /terms/ というURLで利用規約ページを表示
    path('terms/', TermsOfServiceView.as_view(), name='terms'),
    
    # /privacy/ というURLでプライバシーポリシーページを表示
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy'),
]
