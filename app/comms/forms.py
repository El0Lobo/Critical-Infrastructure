from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from app.comms.models import Draft

User = get_user_model()


class InternalComposeForm(forms.Form):
    subject = forms.CharField(required=False, max_length=500)
    body = forms.CharField(widget=forms.Textarea, required=True)
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
    badges = forms.ModelMultipleChoiceField(queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        from django.apps import apps

        super().__init__(*args, **kwargs)
        Badge = apps.get_model("users", "BadgeDefinition")
        if Badge:
            self.fields["badges"].queryset = Badge.objects.all()


class DraftForm(forms.ModelForm):
    class Meta:
        model = Draft
        fields = ["subject", "body_text", "body_html"]
        widgets = {
            "body_text": forms.Textarea(attrs={"rows": 10}),
        }
