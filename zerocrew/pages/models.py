from django.db import models
from django.conf import settings

class Feedback(models.Model):
    
    class Category(models.TextChoices):
        BUG = 'BUG','不具合の報告'
        SUGGESTION = 'SUGGESTION','機能改善の提案'
        OTHER = 'OTHER','その他'
        
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='ユーザー'
    )
    category = models.CharField(
        '種別',
        max_length=20,
        choices=Category.choices,
        default=Category.BUG
    )
    content = models.TextField('内容')
    url = models.URLField('URL',max_length=200, blank=True)
    created_at  = models.DateTimeField('送信日時',auto_now_add=True)
    
    def __str__(self):
        # get_category_displayはDjango側が勝手に作る
        return f'{self.get_category_display()}: {self.content[:20]}'
    

