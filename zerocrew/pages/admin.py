from django.contrib import admin
from django.http import HttpRequest
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    # 管理サイトのリストページに表示するフィールド
    list_display = ('created_at', 'category', 'content', 'user', 'url') 
    # 絞り込みに使うフィールド
    list_filter = ('category', 'created_at')
    # 検索に使うフィールド
    search_fields = ('content','user__username','url')
    # 日付で絞り込むためのドリルダウンナビゲーション
    date_hierarchy = 'created_at'
    # 読み取り専用にするフィールド
    readonly_fields = ('user', 'category', 'content', 'url', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj = None):
        return False