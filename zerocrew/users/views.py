# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.db.models import Count

from .models import Profile, Conversation, DirectMessage, Follow
from projects.models import Application
from .forms import StudentUserCreationForm, UserUpdateForm, ProfileUpdateForm, DirectMessageForm


class LoginView(View):
    """ログインビュー"""
    def get(self, request, *args, **kwargs):
        form = AuthenticationForm()
        return render(request, "users/login.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    return redirect("projects:home")
                else:
                    messages.error(request, "このアカウントはまだ有効化されていません。メールを確認してください。")
            else:
                messages.error(request, "ユーザー名またはパスワードが正しくありません。")
        
        return render(request, 'users/login.html', {'form': form})
    
    
class RegisterView(View):
    """ユーザーの仮登録と確認メールの送信を行うビュー"""
    def get(self, request, *args, **kwargs):
        form = StudentUserCreationForm()
        return render(request, 'users/register.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = StudentUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            subject = '[ZeroCrew] アカウント本登録のご案内'
            message = render_to_string('users/verification_email.txt', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            
            send_mail(subject, message, 'no-reply@zerocrew.com', [user.email])
            
            messages.success(request, '確認メールを送信しました。メールボックスを確認し、本登録を完了してください。')
            return redirect('users:login')

        return render(request, 'users/register.html', {'form': form})


class EmailVerificationView(View):
    """メール内のリンクをクリックした後の処理を行うビュー"""
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, 'メール認証が完了しました。ようこそZeroCrewへ！')
            return redirect('projects:home')
        else:
            messages.error(request, 'この認証リンクは無効です。')
            return redirect('users:login')


class ProfileView(LoginRequiredMixin, View):
    """プロフィール表示ビュー"""
    def get(self, request, pk, *args, **kwargs):
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

        if request.user == user:
            context['user_conversations'] = request.user.conversations.all().order_by('-updated_at')

        return render(request, 'users/profile.html', context)
        

class ProfileEditView(LoginRequiredMixin, View):
    """プロフィール編集ビュー"""
    def get(self, request, *args, **kwargs):
        user_form = UserUpdateForm(instance = request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        context = {
            'user_form':user_form,
            'profile_form':profile_form
        }
        return render(request, 'users/profile_edit.html', context)
    
    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance = request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES,instance = request.user.profile)     

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'プロフィールが更新されました。')
            return redirect('users:profile', pk = request.user.pk)
        
        context = {
            'user_form':user_form,
            'profile_form':profile_form
        }
        return render(request, 'users/profile_edit.html', context)


class ApplicationStatusView(LoginRequiredMixin, ListView):
    """応募状況確認ビュー"""
    model = Application
    template_name = 'users/application_status.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).order_by('-applied_at')
    

class ConversationListView(LoginRequiredMixin, ListView):
    """会話一覧ビュー"""
    model = Conversation
    template_name = 'users/conversation_list.html'
    context_object_name = 'conversations'
    
    def get_queryset(self):
        return self.request.user.conversations.all().order_by('-updated_at')


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """会話詳細ビュー"""
    model = Conversation
    template_name = 'users/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
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
    """会話開始ビュー"""
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
    """フォロー切り替えビュー"""
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
conversation_list = ConversationListView.as_view()
conversation_detail = ConversationDetailView.as_view()
start_conversation = StartConversationView.as_view()
toggle_follow = ToggleFollowView.as_view()
email_verification = EmailVerificationView.as_view()
