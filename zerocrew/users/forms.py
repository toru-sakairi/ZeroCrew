from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, DirectMessage
import json
import re # 正規表現を使うためにインポート(メールの認証に使う)

# ユーザー登録ビューで前まで使っていたDjango標準のUserCrationFormは、今後使わない
class StudentUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='大学のメールアドレス',
        help_text='ac.jp, ed.jp ドメインのメールアドレスで登録してください。'
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if email:
            if not re.search(r'\.ac\.jp$|\.ed\.jp$', email):
                raise forms.ValidationError(
                    "大学提供のメールアドレス(ac.jp, ed.jp)で登録してください"
                )     
        return email
    

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


class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['content']
        widgets = {
            'content':forms.Textarea(attrs={
                'class':'form-control',
                'rows': '3',
                'placeholder': 'メッセージを入力...',
            })
        }
        labels={
            'content':'',
        }
    