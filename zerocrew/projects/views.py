# projects/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q , Count
from taggit.models import Tag 

# settings.pyで設定した上限値を利用するためにインポート
from django.conf import settings

# 複数キーワード検索のために追加
import shlex

# モデルとフォームをインポート
from .models import Project, Application, Message, Like
from .forms import ProjectForm


class HomeView(ListView):
    """ホーム画面。各カテゴリーのプロジェクトを一覧表示する。"""
    model = Project
    template_name = 'projects/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = Project.objects.annotate(like_count=Count('like'))
        
        context['new_projects'] = base_queryset.order_by('-created_at')[:4]
        context['recruiting_projects'] = base_queryset.filter(status=Project.STATUS_RECRUITING).order_by('-updated_at')[:4]
        context['in_progress_projects'] = base_queryset.filter(status=Project.STATUS_IN_PROGRESS).order_by('-updated_at')[:4]
        context['completed_projects'] = base_queryset.filter(status=Project.STATUS_COMPLETED).order_by('-updated_at')[:4]
        
        # 各タグが使われている回数を集計し、多い順に並べる
        # annotate: 集計した値に'num_times'という名前を付ける
        # order_by('-num_times'): 'num_times'の降順（多い順）で並べ替え
        # [:10]: 上位10件だけを取得
        popular_tags = Tag.objects.annotate(
            num_times=Count('taggit_taggeditem_items')
        ).order_by('-num_times')[:10]

        context['popular_tags'] = popular_tags
        
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """新規プロジェクト作成ビュー。作成数の上限チェックも行う。"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:home')

    def dispatch(self, request, *args, **kwargs):
        # ユーザーが作成したプロジェクト数をカウント
        project_count = Project.objects.filter(user=request.user).count()
        # settings.pyで定義した上限値（なければ3）と比較
        limit = getattr(settings, 'MAX_PROJECTS_PER_USER', 3)
        if project_count >= limit:
            messages.error(request, f"作成できるプロジェクトの上限（{limit}件）に達しました。")
            return redirect('projects:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, '新しいプロジェクトを作成しました！')
        return super().form_valid(form)


class ProjectEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """プロジェクト編集ビュー。"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_edit.html'

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.user

    def get_success_url(self):
        messages.success(self.request, 'プロジェクトを更新しました。')
        return reverse('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """プロジェクト詳細ビュー。"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        owner = project.user
        
        # いいね情報
        context['like_count'] = project.like_set.count()
        if self.request.user.is_authenticated:
            context['is_liked'] = project.like_set.filter(user=self.request.user).exists()
        
        # 応募・メンバー状態
        context['is_applied'] = Application.objects.filter(project=project, applicant=self.request.user).exists()
        context['is_member'] = Application.objects.filter(project=project, applicant=self.request.user, status=Application.STATUS_APPROVED).exists() or self.request.user == owner
        
        # メンバー情報
        approved_applications = Application.objects.filter(project=project, status=Application.STATUS_APPROVED)
        context['contributors'] = [app.applicant for app in approved_applications]
        context['owner'] = owner
        
        # 募集状況
        approved_count = len(context['contributors'])
        remaining_slots = project.max_members - approved_count
        context['approved_count'] = approved_count
        context['remaining_slots'] = remaining_slots if remaining_slots > 0 else 0
        
        # プログレスバー用パーセンテージ
        progress_percentage = 0
        if project.max_members > 0:
            progress_percentage = (approved_count * 100) / project.max_members
        context['progress_percentage'] = progress_percentage
        
        return context


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """プロジェクト削除ビュー。"""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.user
    
    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'pk': self.request.user.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"プロジェクト「{self.object.title}」を削除しました。")
        return super().form_valid(form)


class ApplyForProjectView(LoginRequiredMixin, CreateView):
    """プロジェクト応募ビュー。応募数の上限チェックも行う。"""
    model = Application
    fields = []

    def dispatch(self, request, *args, **kwargs):
        # ユーザーの応募数をカウント（申請中 or 承認済み）
        application_count = Application.objects.filter(
            applicant=request.user,
            status__in=[Application.STATUS_PENDING, Application.STATUS_APPROVED]
        ).count()
        limit = getattr(settings, 'MAX_APPLICATIONS_PER_USER', 5)
        if application_count >= limit:
            messages.error(request, f"同時に応募できるプロジェクトの上限（{limit}件）に達しました。")
            return redirect('projects:project_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        
        # オーナー自身のプロジェクトへの応募防止
        if project.user == self.request.user:
            messages.error(self.request, 'ご自身のプロジェクトには応募できません。')
            return redirect('projects:project_detail', pk=project.pk)
        
        # 重複応募の防止
        if Application.objects.filter(project=project, applicant=self.request.user).exists():
            messages.warning(self.request, 'このプロジェクトには既に応募済みです。')
            return redirect('projects:project_detail', pk=project.pk)

        form.instance.project = project
        form.instance.applicant = self.request.user
        messages.success(self.request, 'プロジェクトに応募しました。')
        return super().form_valid(form)


class ApplicantListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """応募者一覧ビュー。"""
    model = Application
    template_name = 'projects/applicant_list.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return Application.objects.filter(project=project).order_by('-applied_at')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context
    
    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return self.request.user == project.user
    

class UpdateApplicationStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """応募ステータス更新ビュー。プロジェクトステータスの自動更新も担う。"""
    def post(self, request, pk, *args, **kwargs):
        application = get_object_or_404(Application, pk=pk)
        project = application.project
        new_status = request.POST.get('status')

        # 承認前の人数チェック
        if new_status == Application.STATUS_APPROVED:
            approved_count = Application.objects.filter(project=project, status=Application.STATUS_APPROVED).count()
            if approved_count >= project.max_members:
                messages.error(request, '募集人数が上限に達しているため、これ以上承認できません。')
                return redirect('projects:applicant_list', pk=project.pk)

        # 応募ステータス更新
        if new_status in [Application.STATUS_APPROVED, Application.STATUS_REJECTED]:
            application.status = new_status
            application.save()
            messages.success(request, f'応募ステータスを「{application.get_status_display()}」に変更しました。')
        else:
            messages.error(request, '無効な操作です。')
            return redirect('projects:applicant_list', pk=project.pk)

        # 承認後のプロジェクトステータス自動更新チェック
        if application.status == Application.STATUS_APPROVED:
            current_approved_count = Application.objects.filter(project=project, status=Application.STATUS_APPROVED).count()
            if current_approved_count >= project.max_members:
                project.status = Project.STATUS_IN_PROGRESS
                project.save()
                messages.info(request, f'メンバーが満員になったため、プロジェクト「{project.title}」のステータスが「実行中」に更新されました。')
        
        return redirect('projects:applicant_list', pk=project.pk)

    def test_func(self):
        application = get_object_or_404(Application, pk=self.kwargs['pk'])
        return self.request.user == application.project.user


class UpdateProjectStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """プロジェクト自体のステータスを手動更新するビュー（実行中→実現済）。"""
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        new_status = request.POST.get('status')
        if new_status == Project.STATUS_COMPLETED and project.status == Project.STATUS_IN_PROGRESS:
            project.status = new_status
            project.save()
            messages.success(request, "プロジェクトのステータスを「実現済」に変更しました。お疲れ様でした！")
        else:
            messages.error(request, "無効な操作です。")
        return redirect('projects:project_detail', pk=project.pk)

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return self.request.user == project.user


class ProjectChatView(LoginRequiredMixin, UserPassesTestMixin, View):
    """プロジェクトチャットビュー。"""
    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        is_owner = self.request.user == project.user
        is_approved_member = Application.objects.filter(
            project=project,
            applicant=self.request.user,
            status=Application.STATUS_APPROVED
        ).exists()
        return is_owner or is_approved_member
    
    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        messages_qs = Message.objects.filter(project=project)
        context = {
            'project': project,
            'messages': messages_qs,
        }
        return render(request, 'projects/project_chat.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        content = request.POST.get('content')
        if content:
            Message.objects.create(project=project, sender=request.user, content=content)
        return redirect('projects:project_chat', pk=pk)


class TaggedProjectListView(ListView):
    """タグによるプロジェクト一覧ビュー。"""
    model = Project
    template_name = 'projects/project_list_by_tag.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        tag_slug = self.kwargs.get('tag_slug')
        return Project.objects.filter(tags__slug=tag_slug).annotate(like_count=Count('like')).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag_name'] = self.kwargs.get('tag_slug')
        return context


class SearchView(ListView):
    """検索ビュー。"""
    model = Project
    template_name = 'projects/search_results.html'
    context_object_name = 'projects'
    paginate_by = 10
    
    def get_queryset(self):
        query = self.request.GET.get('q', None)
        if not query:
            return Project.objects.none()
        
        keywords = shlex.split(query)
        if not keywords:
            return Project.objects.none()

        search_conditions = Q()
        for keyword in keywords:
            keyword_condition = (
                Q(title__icontains=keyword) |
                Q(outline__icontains=keyword) |
                Q(background__icontains=keyword) |
                Q(goal__icontains=keyword) |
                Q(tags__name__icontains=keyword)
            )
            search_conditions &= keyword_condition
        
        return Project.objects.filter(search_conditions).distinct().annotate(like_count=Count('like')).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        # 人気のタグをサイドバーなどに表示するために追加
        context['popular_tags'] = Tag.objects.annotate(num_times=Count('taggit_taggeditem_items')).order_by('-num_times')[:15]
        return context
        

class ToggleLikeView(LoginRequiredMixin, View):
    """いいね切り替えビュー。"""
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, project=project)
        if not created:
            like.delete()
        return HttpResponseRedirect(reverse('projects:project_detail', kwargs={'pk': project.pk}))

def health_check(request):
    """ヘルスチェック用ビュー。"""
    return HttpResponse("OK", status=200)

# .as_view()を使って、各クラスベースビューをURLconfで使えるようにする
home = HomeView.as_view()
project_create = ProjectCreateView.as_view()
project_detail = ProjectDetailView.as_view()
project_edit = ProjectEditView.as_view()
project_delete = ProjectDeleteView.as_view()
apply_for_project = ApplyForProjectView.as_view()
applicant_list = ApplicantListView.as_view()
update_application_status = UpdateApplicationStatusView.as_view()
update_project_status = UpdateProjectStatusView.as_view()
project_chat = ProjectChatView.as_view()
tagged_project_list = TaggedProjectListView.as_view()
search_results = SearchView.as_view() # searchViewからリネーム
toggle_like = ToggleLikeView.as_view()
