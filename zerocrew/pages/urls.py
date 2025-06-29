from django.urls import path
from .views import TermsOfServiceView, Privacy_PolicyView, Landing_AboutView

# アプリケーションの名前空間を設定
app_name = 'pages'

urlpatterns = [
    # /terms/ というURLで利用規約ページを表示
    path('terms/', TermsOfServiceView.as_view(), name='terms'),
    # /privacy/ というURLでプライバシーポリシーページを表示
    path('privacy_policy/', Privacy_PolicyView.as_view(), name='privacy_policy'),
    # /landing_about/ というURLでランディングページ＆aboutについてのページを表示
    path('landing_about/', Landing_AboutView.as_view(), name='landing_about'),
]
