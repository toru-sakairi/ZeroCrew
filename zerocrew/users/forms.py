from django import forms
from django.contrib.auth.models import User
from .models import Profile
import json


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'icon', 'tags')
        help_texts = {
            'tags': 'あなたのスキルや役割、興味のある分野などをタグとして入力してください。(例：エンジニア、デザイン)',
        }

        # jsonからもらうデータを合わせる
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
            # 例: '[{"value": "AI"}]' -> [{'value': 'AI'}]
            tags_list = json.loads(raw_tags)

            # 各辞書から'value'キーの値（タグ名）だけを取り出して、新しいリストを作成します
            # 例: [{'value': 'AI'}, ...] -> ['AI', 'Python']
            return [tag['value'] for tag in tags_list]

        except (json.JSONDecodeError, TypeError, AttributeError):
            # もしデータがJSONでない場合（JavaScriptが無効など）の予備処理
            if isinstance(raw_tags, str):
                return [tag.strip() for tag in raw_tags.split(',') if tag.strip()]
            return []
