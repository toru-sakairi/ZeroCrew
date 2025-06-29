from django.views.generic import TemplateView

class TermsOfServiceView(TemplateView):
    """
    利用規約ページを表示するためのビュー
    """
    # templates/pages/ ディレクトリ内の `terms_of_service.html` を指定
    template_name = "pages/terms_of_service.html"
    
class Landing_AboutView(TemplateView):
    """
    ランディングページ＆Aboutのページを表示するためのビュー
    """
    template_name = "pages/landing_about.html"
    
class Privacy_PolicyView(TemplateView):
    """
    プライバシーポリシーのページを表示するためのビュー
    """
    template_name = "pages/privacy_policy.html"

