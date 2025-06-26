# views.pyの役割:Webリクエストを処理し、レスポンスを返す役割を担う。リクエストを受け取り、必要な処理を実行して、
# 適切なレスポンス（通常HTMLページ）を生成してクライアントに返す
# ここでは、projectsアプリケーション内でのレスポンスを生成する。
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import CreateView, ListView, DetailView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Project, Application, Message
from .forms import ProjectForm
from django.http import HttpResponseForbidden
from django.db.models import Q 
# --- 複数キーワード検索のために追加 ---
import shlex
from functools import reduce
from operator import and_

# ホームビュー(今のところ(2025_06_20)プロジェクト一覧にしている)
# ログイン後のホーム画面で、投稿されたプロジェクトを一覧で表示する。
# ListViewを継承することで、オブジェクトの一覧表示を簡単に実装している
class HomeView(ListView):
    model = Project
    
    # 表示するテンプレート（HTML）の指定
    template_name = 'projects/home.html'
    
    # テンプレート内で使う変数名の指定。project_listという名前でプロジェクトのリストをテンプレートに渡す。
    template_object_name = 'project_list'
    
    # 表示順の指定。作成日時の新しい順に並べる
    ordering = ['-created_at']

# プロジェクト作成ビュー。新規プロジェクトを投稿するページ。CreateViewを継承することで、オブジェクトの作成フォームを簡単に実装できる。
class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    # フォームの保存が成功した後のリダイレクト先。
    success_url = reverse_lazy('projects:home')

    # フォームのデータが有効だった場合に呼ばれるメソッド。
    def form_valid(self, form):
        # 保存する前に、プロジェクトのオーナー（user）を現在ログインしているユーザーに設定する。
        form.instance.user = self.request.user
        # 親クラスのform_validを呼び出して、オブジェクトを正式に保存する。
        return super().form_valid(form)


# プロジェクト詳細ビュー。個別のプロジェクトの詳細ページ。DetailViewを継承することで、単一オブジェクトの詳細表示を簡単に実装する。
class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    # テンプレートに渡す追加のコンテキストデータを定義するメソッド
    def get_context_data(self, **kwargs):
        # まず親クラスのメソッドを呼び出して、基本的なコンテキストを取得
        context = super().get_context_data(**kwargs)
        
        # ログインユーザーがこのプロジェクトに応募済みかどうかのフラグを追加
        # (VSCode内)objectがエラーになっていると思うが、これはDjangoの方でちゃんと理解されるから大丈夫だと思われる
        is_applied = Application.objects.filter(
            project=self.object, applicant=self.request.user).exists()
        
        is_member = Application.objects.filter(
            project=self.object, applicant=self.request.user, status=Application.STATUS_APPROVED
        ).exists() or self.request.user == self.object.user
        
        # テンプレートに渡すコンテキストに追加
        context['is_member'] = is_member
        context['is_applied'] = is_applied
        return context

# プロジェクト応募ビュー
class ApplyForProjectView(LoginRequiredMixin, CreateView):
    # プロジェクトへの応募処理を行う。
    # 応募オブジェクトを「作成する」ため、CreateViewが適している。
    model = Application
    fields = []  # フォームに表示するフィールドはないので空にする

    # 処理成功時のリダイレクト先を動的に決定する。
    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.kwargs['pk']})

    # フォームが送信され、データが有効な場合の処理。
    def form_valid(self, form):
        # 応募データの保存前に、バリデーションや追加情報のセットを行う
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        applicant = self.request.user

        # ガード節：不正な操作をチェックして。問題があれば処理を中断する。
        # プロジェクトのオーナーは応募できない
        if project.user == applicant:
            messages.error(self.request, 'ご自身のプロジェクトには応募できません。')
            return redirect(self.get_success_url())
        # 既に応募済みか確認
        if Application.objects.filter(project=project, applicant=applicant).exists():
            messages.warning(self.request, 'このプロジェクトには既に応募済みです。')
            return redirect(self.get_success_url())

        # Applicationオブジェクトに情報をセットして保存
        form.instance.project = project
        form.instance.applicant = applicant
        messages.success(self.request, 'プロジェクトに応募しました。')

        return super().form_valid(form)

    # フォームデータが無効だった場合の処理
    def form_invalid(self, form):
        messages.error(self.request, '応募処理中にエラーが発生しました。')
        return redirect(self.get_success_url())
    
# 応募者一覧ビュー
class ApplicantListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    # 特定のプロジェクトへの応募者一覧を表示する
    model = Application
    template_name = 'projects/applicant_list.html'
    context_object_name = 'applications'
    
    # 表示するオブジェクトリストをカスタマイズする
    def get_queryset(self):
        project = get_object_or_404(Project, pk = self.kwargs['pk'])
        return Application.objects.filter(project=project).order_by('-applied_at')
       
    # テンプレートにプロジェクト情報も渡す 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context
    
    # このページにアクセスできる権限があるかテストする
    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return self.request.user == project.user
    
# 応募ステータス更新ビュー
class UpdateApplicationStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    # 応募のステータスを更新する
    def post(self, request, pk, *args, **kwargs):
        application = get_object_or_404(Application, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in [Application.STATUS_APPROVED, Application.STATUS_REJECTED]:
            application.status = new_status
            application.save()
            messages.success(request, f'応募ステータスを「{application.get_status_display()}」に変更しました。')
        else:
            messages.error(request, '無効な操作です。')
                            
        return redirect('projects:applicant_list', pk=application.project.pk)
        
    # この処理を実行できる権限があるかテストする。
    def test_func(self):
        application = get_object_or_404(Application, pk = self.kwargs['pk'])
        project = application.project
        return self.request.user == project.user
    
# プロジェクトチャットビュー
class ProjectChatView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    # プロジェクトメンバー専用のチャットルーム
    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        is_owner = self.request.user == project.user
        is_approved_member = Application.objects.filter(
            project = project,
            applicant = self.request.user,
            status=Application.STATUS_APPROVED
        ).exists()
        # オーナー、または承認済みのメンバーのみアクセスを許可
        return is_owner or is_approved_member
    
    # チャットルームの表示
    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        # プロジェクトのメッセージをすべて取得
        messages = Message.objects.filter(project=project)
        context={
            'project' : project,
            'messages' : messages,
        }
        return render(request, 'projects/project_chat.html',context)
    
    # メッセージの投稿処理
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        content = request.POST.get('content')
        
        # メッセージ内容が空でなければ保存
        if content:
            Message.objects.create(
                project = project,
                sender = request.user,
                content = content,
            )
        return redirect('projects:project_chat', pk=pk)
    
# タグ機能のクラス
class TaggedProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list_by_tag.html'
    context_object_name = 'projects'
    paginate_by = 10 # ページネーション（任意）

    def get_queryset(self):
        # URLからタクスラッグを取得
        tag_slug = self.kwargs.get('tag_slug')
        # そのタグを持つプロジェクトをフィルタリング
        return Project.objects.filter(tags__slug=tag_slug).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートにタグの名前も渡す
        context['tag_name'] = self.kwargs.get('tag_slug')
        return context
    
# 検索機能
class SearchView(ListView):
    model = Project
    template_name = 'projects/search_results.html'
    context_object_name = 'projects'
    paginate_by = 10 # 一ページに表示するプロジェクト数
    
    def get_queryset(self):
        # 'q'という名前で送られてきた検索キーワードを取得
        query = self.request.GET.get('q', None)
            
        if query:
            # shlex.split() を使い、空白でキーワードを分割する。
            # ""で囲まれたフレーズは一つのキーワードとして扱われる。
            # 例: "Python AI" -> ['Python', 'AI']
            keywords = shlex.split(query)
            
            if not keywords:
                return Project.objects.none()

            search_query = Q()
            
            for keyword in keywords:
                keyword_query = (
                    Q(title__icontains=keyword) |
                    Q(outline__icontains=keyword) |
                    Q(background__icontains=keyword) |
                    Q(goal__icontains=keyword) |
                    Q(tags__name__icontains=keyword) # タグの名前で検索
                )
                search_query &= keyword_query
            
            # functools.reduceとoperator.and_を使い、各キーワードのQオブジェクトをANDで結合
            # (Q(...) | Q(...)) & (Q(...) | Q(...)) のようなクエリが生成される
            queryset = Project.objects.filter(search_query).distinct().order_by('-created_at')
            
        else:
            queryset = Project.objects.none()
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
        
    
# .as_view()を使って、各クラスベースビューを関数ベースビューのようにURLconfで使えるようにする
home = HomeView.as_view()
project_create = ProjectCreateView.as_view()
project_detail = ProjectDetailView.as_view()
apply_for_project = ApplyForProjectView.as_view()
applicant_list = ApplicantListView.as_view()
update_application_status = UpdateApplicationStatusView.as_view()
project_chat = ProjectChatView.as_view()
tagged_project_list = TaggedProjectListView.as_view()
searchView = SearchView.as_view()