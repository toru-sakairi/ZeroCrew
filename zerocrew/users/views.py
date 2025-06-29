# userアプリケーション内のレスポンスを生成する
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View, generic
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login
from django.urls import reverse_lazy, reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect # 追加

from django.db.models import Count

from .models import Profile, Conversation, DirectMessage, Follow
from projects.models import Application
from .forms import UserUpdateForm, ProfileUpdateForm, DirectMessageForm


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
        login(self.request, user)
        messages.success(self.request, 'ユーザー登録が完了しました。')
        # 親クラスのform_validを呼び出し、success_urlにリダイレクトさせる
        return super().form_valid(form)
        
        
# プロフィール表示ビュー
# ユーザーのプロフィールページを表示する。マイページと、他ユーザーのプロフィールページの両方を兼ねる
# プロフィール表示ビュー
class ProfileView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # [修正] userオブジェクトは get_object_or_404 を使うとより安全です
        user = get_object_or_404(User, pk=pk)
        profile = Profile.objects.get(user=user)
        user_projects = user.projects.all().annotate(like_count=Count('like')).order_by('-created_at')
        
        is_following = False
        if request.user.is_authenticated and request.user != user:
            is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
        
        follower_count = user.followers.count()
        following_count = user.following.count()
        
        following_users = User.objects.filter(followers__follower=user)
        
        context = {
            'user': user,
            'profile': profile,
            'user_projects': user_projects,
            'is_following': is_following,
            'follower_count': follower_count,
            'following_count': following_count,
            'following_users': following_users
        }

        # 表示しているプロフィールが、ログイン中のユーザー自身のものかを確認
        if request.user == user:
            # 自分のプロフィールの場合、進行中の会話リストをコンテキストに追加
            context['user_conversations'] = request.user.conversations.all().order_by('-updated_at')
        # ▲▲▲ ここまで ▲▲▲

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
    
class ConversationListView(LoginRequiredMixin, ListView):
    """自分が参加している会話の一覧（受信箱）を表示するビュー。"""
    model = Conversation
    template_name = 'users/conversation_list.html'
    context_object_name = 'conversations'
    
    def get_queryset(self):
        # 自分が参加している会話のみを取得する
        return self.request.user.conversations.all().order_by('-updated_at')


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """特定の会話のメッセージ詳細を表示するビュー。"""
    model = Conversation
    template_name = 'users/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        # 自分が参加している会話のみアクセス可能にする
        return self.request.user.conversations.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DirectMessageForm()
        context['other_user'] = self.object.participants.exclude(pk=self.request.user.pk).first()
        return context
    
    def post(self, request, *args, **kwargs):
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            conversation = self.get_object()
            message = form.save(commit=False)
            message.sender = request.user
            message.conversation = conversation
            message.save()
            conversation.save()
            return redirect('users:conversation_detail', pk = conversation.pk)
        else:
            return self.get(request, *args, **kwargs)

class StartConversationView(LoginRequiredMixin, View):
    """
    指定したユーザーとの会話を開始するか、既存の会話にリダイレクトするビュー。
    """
    def get(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        
        if target_user == request.user:
            return redirect('users:profile', pk=request.user.pk)
        
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=target_user
        ).first()
        
        if conversation:
            return redirect('users:conversation_detail', pk=conversation.pk)
        else:
            new_conversation = Conversation.objects.create()
            new_conversation.participants.add(request.user, target_user)
            return redirect('users:conversation_detail', pk=new_conversation.pk)
        
        
class ToggleFollowView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        followed_user = get_object_or_404(User, pk=pk)
        
        if followed_user == request.user:
            messages.warning(request, "自分自身をフォローすることはできません")
            return redirect("users:profile", pk=pk)
        
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=followed_user)
        
        if not created:
            follow.delete()
            messages.info(request, f"{followed_user.username}さんのフォローを解除しました。")
        else:
            messages.success(request, f"{followed_user.username}さんをフォローしました。")
            
        return HttpResponseRedirect(reverse('users:profile', kwargs={'pk': followed_user.pk}))
    
    
login = LoginView.as_view()
register = RegisterView.as_view()
profile = ProfileView.as_view()
profile_edit = ProfileEditView.as_view()
application_status = ApplicationStatusView.as_view()
conversationList = ConversationListView.as_view()
conversationDetail = ConversationDetailView.as_view()
startConversation = StartConversationView.as_view()
toggle_follow = ToggleFollowView.as_view() # 新しいビューを追記