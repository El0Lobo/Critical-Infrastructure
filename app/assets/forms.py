# app/assets/forms.py
from django import forms
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.utils.text import slugify

from .models import (
    ASSET_KIND_CHOICES,
    ASSET_VISIBILITY_CHOICES,
    VISIBILITY_MODE_CHOICES,
    Asset,
    Collection,
    Tag,
)


# -------------------------------------------------------------------
# Custom widget FIRST so other classes can reference it
# -------------------------------------------------------------------
class TagCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Renders tag checkboxes as 'pill' chips using templates under app/templates.
    We bypass the default forms renderer to ensure project-level templates are used.
    """

    template_name = "assets/widgets/checkbox_pills.html"
    option_template_name = "assets/widgets/checkbox_pill_option.html"

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        context["widget"]["option_template_name"] = self.option_template_name
        return render_to_string(self.template_name, context)


# -------------------------------------------------------------------
# Filters (for the list page)
# -------------------------------------------------------------------
VISIBILITY_FILTER_CHOICES = [
    ("", "Any"),
    ("public", "Public"),
    ("internal", "Internal"),
    ("groups", "Groups"),
]


class AssetFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    kind = forms.ChoiceField(required=False, choices=[("", "All types")] + ASSET_KIND_CHOICES)
    visibility = forms.ChoiceField(required=False, choices=VISIBILITY_FILTER_CHOICES)
    collection = forms.ModelChoiceField(required=False, queryset=Collection.objects.none())

    # use pills here too
    tags = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Tag.objects.none(),
        widget=TagCheckboxSelectMultiple(attrs={"class": "tag-checks small"}),
    )

    source = forms.ChoiceField(
        required=False, choices=[("", "Any"), ("local", "Local"), ("external", "External")]
    )
    referenced = forms.ChoiceField(
        required=False, choices=[("", "Any"), ("yes", "Used"), ("no", "Unused")]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collection"].queryset = Collection.objects.all().order_by("title")
        self.fields["tags"].queryset = Tag.objects.all().order_by("name")


# -------------------------------------------------------------------
# Create / quick-add form
# -------------------------------------------------------------------
class AssetCreateForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "collection",
            "title",
            "slug",
            "visibility",
            "description",
            "tags",
            "file",
            "url",
            "text_content",
            "appears_on",
        ]
        widgets = {
            "tags": TagCheckboxSelectMultiple(attrs={"class": "tag-checks"}),
            "appears_on": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collection"].queryset = Collection.objects.all().order_by("title")
        self.fields["tags"].queryset = Tag.objects.all().order_by("name")
        self.fields["url"].label = "External URL"
        self.fields["text_content"].label = "Text content"
        self.fields["visibility"].choices = ASSET_VISIBILITY_CHOICES

    def clean(self):
        cleaned = super().clean()
        file = cleaned.get("file")
        url = (cleaned.get("url") or "").strip()
        text = (cleaned.get("text_content") or "").strip()
        provided = sum([bool(file), bool(url), bool(text)])
        if provided != 1:
            raise forms.ValidationError("Provide exactly one: a file OR a URL OR text.")
        return cleaned

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        title = (self.cleaned_data.get("title") or "").strip()
        if not slug and title:
            slug = slugify(title)
        return slug


# -------------------------------------------------------------------
# Collections
# -------------------------------------------------------------------
class CollectionForm(forms.ModelForm):
    visibility_mode = forms.ChoiceField(choices=VISIBILITY_MODE_CHOICES, label="Visibility")
    allowed_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 6}),
        label="Allowed groups (for Groups visibility)",
    )

    class Meta:
        model = Collection
        fields = [
            "title",
            "slug",
            "parent",
            "visibility_mode",
            "allowed_groups",
            "description",
            "tags",
        ]
        widgets = {
            "tags": TagCheckboxSelectMultiple(attrs={"class": "tag-checks"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = Collection.objects.all().order_by("title")
        self.fields["allowed_groups"].queryset = Group.objects.all().order_by("name")
        self.fields["tags"].queryset = Tag.objects.all().order_by("name")

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("visibility_mode")
        groups = cleaned.get("allowed_groups")
        if mode == "groups" and (not groups or groups.count() == 0):
            self.add_error(
                "allowed_groups", "Select at least one group when visibility is set to Groups."
            )
        return cleaned

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        title = (self.cleaned_data.get("title") or "").strip()
        if not slug and title:
            slug = slugify(title)
        return slug


# -------------------------------------------------------------------
# Tags
# -------------------------------------------------------------------
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "e.g. promo, press, flyer"})}
