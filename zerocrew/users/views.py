# userアプリケーション内のレスポンスを生成する
from django.shortcuts import render, redirect
from django.views import View, generic
from django.views.generic import ListView, CreateView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Profile
from projects.models import Application
from .forms import UserUpdateForm, ProfileUpdateForm


# ログインビュー
class LoginView(View):
    # ログインページの表示(GET)と、ログイン処理(POST)を担うビュー。
    def get(self, request, *args, **kwargs):
        # ログインページをGETリクエストで表示する
        # ログインフォームをテンプレートに渡す
        form = AuthenticationForm()
        return render(request, "users/login.html", {"form": form})

    def post(self, request, *args, **kwargs):
        # ポストリクエストで送信された情報で、ログイン処理を行う
        # 送信されたデータでフォームを検証
        form = AuthenticationForm(request, data=request.POST)

        # フォームの検証に成功した場合
        if form.is_valid():
            # ユーザー名とパスワードを取得
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # ユーザー認証
            user = authenticate(username=username, password=password)

            # 認証に成功した場合
            if user is not None:
                # ログイン処理を実行
                auth_login(request, user)
                # ログイン後のホーム画面にリダイレクト
                return redirect("projects:home")

        # フォームの検証に失敗した場合は、エラーメッセージ付きで再度フォームを表示
        return render(request, "users/login.html", {"form": form})
    
# ユーザー登録ビュー：ユーザーの新規登録を行うページ
# CreateViewを継承し、登録成功後、自動でログインさせる
class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("projects:home")

    def form_valid(self, form):
        # フォームを保存し、ユーザーオブジェクトを取得
        user = form.save()
        # 作成したユーザーでそのままログイン処理を行う
        auth_login(self.request, user)
        messages.success(self.request, 'ユーザー登録が完了しました。')
        # 親クラスのform_validを呼び出し、success_urlにリダイレクトさせる
        return super().form_valid(form)
        
        
# プロフィール表示ビュー
# ユーザーのプロフィールページを表示する。マイページと、他ユーザーのプロフィールページの両方を兼ねる
class ProfileView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # ユーザーのpkを使って、表示対象のユーザーを取得
        user = User.objects.get(pk = pk)
        # そのユーザーに紐づくプロフィールを取得
        profile = Profile.objects.get(user = user)
        # （VSCode）projectsがエラーになるが、これはDjangoの方でやってくれると思うので、大丈夫だと
        user_projects = user.projects.all().order_by('-created_at')
        
        context = {
            'user':user,
            'profile':profile,
            'user_projects':user_projects,
        }
        return render(request, 'users/profile.html', context)
        
# プロフィール編集ビュー：自身のプロフィール情報を編集するページの表示（POST）と、更新処理（POST）を担う
class ProfileEditView(LoginRequiredMixin, View):
    
    # プロフィール編集フォームを表示する
    def get(self, request, *args, **kwargs):
        # 現在ログインしているユーザーの情報でフォームを初期化
        user_form = UserUpdateForm(instance = request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        context = {
            'user_form':user_form,
            'profile_form':profile_form
        }
        return render(request, 'users/profile_edit.html', context)
    
    # 送信された情報でプロフィールを更新する
    def post(self, request, *args, **kwargs):
        # request.FILESは、画像などのファイルデータを受け取るために必要
        user_form = UserUpdateForm(request.POST, instance = request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES,instance = request.user.profile)    

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'プロフィールが更新されました。')
            # 自身のプロフィールページにリダイレクト
            return redirect('users:profile', pk = request.user.pk)
        
        # エラーがある場合は、エラーメッセージ付きで再度フォームを表示
        context = {
            'user_form':user_form,
            'profile_form':profile_form
        }
        return render(request, 'users/profile_edit.html', context)

# 応募状況確認ビュー：自身が応募したプロジェクトの状況を一覧で確認するページ
class ApplicationStatusView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'users/application_status.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        # ユーザーが応募者であるものだけに絞り込む
        return Application.objects.filter(applicant=self.request.user).order_by('-applied_at')
    
    
login = LoginView.as_view()
register = RegisterView.as_view()
profile = ProfileView.as_view()
profile_edit = ProfileEditView.as_view()
application_status = ApplicationStatusView.as_view()

