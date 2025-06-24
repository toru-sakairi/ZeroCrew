# projects/forms.py

import json # JSONを扱うためにインポート
from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'outline','tags']
        widgets = {
            'title':forms.TextInput(attrs={'placeholder':'プロジェクトのタイトルを入力', 'class':'form-control'}),
            'outline':forms.Textarea(attrs={'placeholder':'プロジェクトの概要や目的、求めるスキルなどを具体的に記述してください。', 'class':'form-control', 'rows': 8}),
        }
        labels = {
            'title':'プロジェクト名',
            'outline':'プロジェクト概要',
        }
    # タグ用のスクリプト
    def clean_tags(self):
        """
        Tagifyから送られてくるJSON形式の文字列を、
        django-taggitが理解できる形式（文字列のリスト）に変換します。
        """
        # フォームから送られてきた生の'tags'データを取得します
        raw_tags = self.data.get('tags')

        if not raw_tags:
            return [] # タグが空の場合は、空のリストを返します

        try:
            # TagifyからのデータはJSON文字列なので、Pythonのリストに変換します
            # 例: '[{"value": "AI"}, {"value": "Python"}]' -> [{'value': 'AI'}, {'value': 'Python'}]
            tags_list = json.loads(raw_tags)
            
            # 各辞書から'value'キーの値（タグ名）だけを取り出して、新しいリストを作成します
            # 例: [{'value': 'AI'}, ...] -> ['AI', 'Python']
            # これがdjango-taggitが最終的に受け取りたい形式です
            return [tag['value'] for tag in tags_list]
            
        except (json.JSONDecodeError, TypeError, AttributeError):
            # もしデータがJSONでない場合（例：ユーザーがJavaScriptを無効にしている場合）
            # カンマ区切りの文字列として扱います
            if isinstance(raw_tags, str):
                # カンマで分割し、各タグの前後の空白を削除します
                return [tag.strip() for tag in raw_tags.split(',') if tag.strip()]
            return []

