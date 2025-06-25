# ユーザーの情報を入れておく
from django.db import models
from django.conf import settings # settings.AUTH_USER_MODEL を使うため
# ユーザー登録時に自動でProfileも作成する仕組み
from django.db.models.signals import post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager

# ユーザーのプロフィールモデル
class Profile(models.Model):
    # Django標準のUserモデルを拡張して、追加のユーザー情報を格納するためのモデル。
    # 自己紹介文やアイコン画像など、Userモデルにデフォルトで存在しないフィールドを定義する
    
    # ユーザー(OneToOneField)：Djangoの承認システムで使われるUserモデルと、このProfileモデルを1対1の関係で紐づける
    # これにより、一人のユーザーは、必ず一つのプロフィールを持つという関係が保証される
    # userモデルが削除されたとき、関連するプロフィールも一緒に削除される(on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # 自己紹介文：ユーザの自己紹介文を保存する。blank=Trueで空でも許容する
    bio = models.TextField(blank=True, verbose_name='自己紹介')
    
    # アイコン画像：ユーザーのアイコン画像
    # upload_to = 'icons/'：アップロードされた画像ファイルが'meta/icons/'ディレクトリに保存される
    # blank=True, null = True：必須ではないことを指す
    icon = models.ImageField(upload_to='icons/', blank=True, null=True, verbose_name='アイコン')
    
    # タグ機能を追加
    tags = TaggableManager(verbose_name="スキル・役割", blank = True)
    
    # 管理画面での表示
    def __str__(self):
        return f'{self.user.username}のプロフィール'

# シグナルレシーバー（自動プロフィール作成機能）
# @receiverデコレ―タ：
# 特定のイベント（今回はpost_save）が発生したときに、指定した関数（今回はcreate_profile）を実行する
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
# 新しいユーザーが作成された場合のみ、対応するProfileオブジェクトを作成する
# sender:シグナルを送信したモデル
# instance:保存されたUserモデルの実際のインスタンス
# created:新規作成の場合True
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        
# ユーザー間の会話を表す
class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name='参加者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now = True, verbose_name='最終更新日時')
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        user_list = [user.username for user in self.participants.all()]
        return f"Conversation between{','.join(user_list)}"
    
# ここのダイレクトメッセージを表すモデル
class DirectMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete = models.CASCADE,
        related_name='messages',
        verbose_name='会話'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_direct_messages',
        verbose_name='送信者'
    )
    content = models.TextField(verbose_name='内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='送信日時')
    # 拡張機能として一応残しておく
    is_read=models.BooleanField(default=False, verbose_name='既読フラグ')
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"Form{self.sender.username} at {self.timestamp:%Y-%m-%d %H%M}"