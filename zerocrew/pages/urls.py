from django.urls import path
from .views import TermsOfServiceView, PrivacyPolicyView, Landing_AboutView

# アプリケーションの名前空間を設定
app_name = 'pages'

urlpatterns = [
    # /terms/ というURLで利用規約ページを表示
    path('terms/', TermsOfServiceView.as_view(), name='terms'),
    # /privacy/ というURLでプライバシーポリシーページを表示
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy'),
    # /landing_about/ というURLでランディングページ＆aboutについてのページを表示
    path('landing_about/', Landing_AboutView.as_view(), name='landing_about'),
]
