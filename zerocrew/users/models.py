# ユーザーの情報を入れておく
from django.db import models
from django.conf import settings # settings.AUTH_USER_MODEL を使うため
# ユーザー登録時に自動でProfileも作成する仕組み
from django.db.models.signals import post_save
from django.dispatch import receiver

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