# projects/forms.py

import json  # JSONを扱うためにインポート
from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'image', 'outline', 'background', 'goal', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'プロジェクトのタイトルを入力',
                'class': 'form-control',
            }),
            'outline': forms.Textarea(attrs={
                'placeholder': 'プロジェクトの概要を説明してください',
                'class': 'form-control',
                'rows': 8,
            }),
            # backgroundとgoalのウィジェットを追加
            'background': forms.Textarea(attrs={
                'placeholder': 'なぜこのプロジェクトを始めようと思ったのですか？解決したい社会課題や、自身の原体験などを具体的に記述してください。',
                'class': 'form-control',
                'rows': 6
            }),
            'goal': forms.Textarea(attrs={
                'placeholder': 'このプロジェクトを通して、何を達成したいですか？「〇〇な人を100人集める」「〇〇ができるWebアプリをリリースする」など、具体的な目標を記述してください。',
                'class': 'form-control',
                'rows': 6
            }),
            # imageフィールドにもclassを指定してBootstrapのスタイルを適用
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'title': 'プロジェクト名',
            'image': 'プロジェクト画像',
            'outline': 'プロジェクト概要',
            'background': '背景・課題',
            'goal': '目標・ゴール',
            'tags': 'タグ (最大5個まで)',
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
            return []  # タグが空の場合は、空のリストを返します

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
