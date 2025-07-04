from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views import View
from .forms import FeedbackForm

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

# エラー報告＆改善フォーム
class SubmitFeedbackView(View):
    def post(self, request, *args, **kwargs):
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
               feedback.user = request.user
            feedback.save()
            return JsonResponse({'success': True, 'message': 'フィードバックを送信しました。ご協力ありがとうございます！'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': '入力内容に誤りがあります。', 'errors': errors})
        