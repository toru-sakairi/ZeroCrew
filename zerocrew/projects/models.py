# プロジェクトモデル
from django.db import models
from django.conf import settings
from taggit.managers import TaggableManager

# オリジネーターが投稿するプロジェクトを定義するモデル


class Project(models.Model):
    # user:プロジェクトを投稿したユーザー。外部キー。
    # このプロジェクトを投稿したユーザーと紐づける。Userモデルが削除された場合、関連するプロジェクトも一緒に削除される（on_delete=models.CASCADE）
    # related_name='projects'とすることで、User側から user.projectsのようにして、一覧を取得できるようになる。
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='オーナー',
    )

    # タイトル：プロジェクトのタイトルで、最大100文字としている
    title = models.CharField(max_length=100, verbose_name='タイトル')
    
    # 画像：プロジェクトのイメージを伝える画像（任意）
    image = models.ImageField(
        upload_to='project_images/',
        blank=True,
        null=True,
        verbose_name='プロジェクト画像',
        help_text='プロジェクトのヘッダー画像やアイコンとして表示されます',
    )

    # 概要：プロジェクトの詳しい説明。文字数制限なし。
    outline = models.TextField(
        verbose_name='プロジェクトの概要',
        help_text='プロジェクトの簡単な説明を記述してください。一覧ページなどで表示されます。',
    )

    background = models.TextField(
        blank=True,
        null=True,
        verbose_name='背景・課題',
        help_text='このプロジェクトを立ち上げた背景や、解決したい課題について詳しく記述してください',
    )
    
    goal = models.TextField(
        blank=True,
        null=True,
        verbose_name='目標・ゴール',
        help_text='このプロジェクトで達成したい具体的な目標や、理想の状態を記述してください'
    )

    # 作成日時：このプロジェクトが作成された日時を自動で記録する。
    created_at = models.DateTimeField(auto_now_add=True)

    # 更新日時：このプロジェクトが更新されるたびに、その日時を自動で記録。
    updated_at = models.DateTimeField(auto_now=True)

    # タグ機能の追加 django-taggitを使って、追加するだけでタグをつけられるようにする
    tags = TaggableManager(blank=True, verbose_name='タグ')

    # 管理画面などで表示される際の、このオブジェクトの文字列表現。
    def __str__(self):
        return self.title

# 応募モデル。コントリビューターがプロジェクトに対して行う「応募」を定義するモデル。


class Application(models.Model):
    # --- ステータス管理のための定数 ---
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, '申請中'),
        (STATUS_APPROVED, '承認済み'),
        (STATUS_REJECTED, '拒否済み'),
    ]

    # 応募先のプロジェクト。外部キー。どのプロジェクトへの応募かを示す。
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name='プロジェクト')

    # 応募者。外部キー。誰が応募したかを示す。
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='応募者')

    # ステータス。この応募が、「申請中」「承認済み」「拒否済み」のどの状態かを示す。
    # choices = STATUS_CHOICESにより、上記で定義した選択肢以外は保存できない
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='ステータス')

    # 応募日時。応募が行われた日時を自動で記録。
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name='応募日時')

    # データベースレベルでの制約。projectとapplicantの組み合わせがユニークであることを保証する。
    # これにより、同じユーザーが同じプロジェクトに複数回応募するのを防ぐ
    class Meta:
        unique_together = ('project', 'applicant')

    # 管理画面での表示用
    def __str__(self):
        # self.get_status_display() を使うと、'pending'ではなく'申請中'のように、
        # 人間が読みやすい方のラベルを取得できる。
        return f'{self.applicant.username} -> {self.project.title} ({self.get_status_display()})'

# メッセージモデル。プロジェクトのグループチャットで交わされるメッセージを定義するモデル


class Message(models.Model):
    # メッセージが入力された投稿されたプロジェクト。外部キー。
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, verbose_name='プロジェクト')

    # 送信者。外部キー。
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='送信者')

    # メッセージ本文
    content = models.TextField(verbose_name='内容')

    # 送信日時
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='送信日時')

    # 表示順の指定。'timestamp'の昇順で並べる。つまり、古いメッセージから表示する
    class Meta:
        ordering = ['timestamp']

    # 管理画面での表示用。メッセージの内容を最初の20文字だけ表示する(スライス)
    def __str__(self):
        return f'{self.sender.username}:{self.content[:20]}'
