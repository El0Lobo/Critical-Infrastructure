# app/menu/forms.py
from django import forms
from django.forms import inlineformset_factory

from .models import Category, Item, ItemVariant, Unit


class CategoryForm(forms.ModelForm):
    """
    Form for creating/editing menu categories with an unrestricted tree structure.
    """

    class Meta:
        model = Category
        fields = ["name", "parent", "unit_group"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Category name"}
            ),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "unit_group": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Category.objects.all().order_by("name")
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = qs
        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "— Top level —"
        self.fields["unit_group"].required = False

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        instance_pk = self.instance.pk
        if parent and instance_pk:
            current = parent
            while current:
                if current.pk == instance_pk:
                    raise forms.ValidationError("A category cannot be its own parent.")
                current = current.parent
        return parent


class ItemForm(forms.ModelForm):
    visible_public = forms.BooleanField(required=False, label="Show on public menu")
    featured = forms.BooleanField(required=False, label="Feature this item")
    sold_out_until = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
    )
    new_until = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
    )

    class Meta:
        model = Item
        fields = [
            "name",
            "description",
            "visible_public",
            "featured",
            "sold_out_until",
            "new_until",
            "vegan",
            "vegetarian",
            "gluten_free",
            "sugar_free",
            "lactose_free",
            "nut_free",
            "halal",
            "kosher",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Item name"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Optional description"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove ":" after all labels rendered via label_tag
        self.label_suffix = ""


class ItemVariantForm(forms.ModelForm):
    """
    Form for item variants (e.g., Small/0.5 L vs. Large/1.0 L).
    """

    class Meta:
        model = ItemVariant
        fields = ["label", "quantity", "unit", "price", "abv"]
        widgets = {
            "label": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Glass, Bottle, Large"}
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "abv": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1", "min": "0", "max": "100"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit"].queryset = Unit.objects.all().order_by("display")
        self.fields["abv"].required = False
        self.fields["abv"].help_text = "Optional. Alcohol by volume (%)"

    def clean(self):
        """
        Hook for variant-specific validations.
        (Currently no hard caps on quantity — only basic filtering per kind.)
        """
        cleaned = super().clean()
        return cleaned


# Inline formset for managing multiple variants inside the item form
ItemVariantFormSet = inlineformset_factory(
    Item, ItemVariant, form=ItemVariantForm, extra=2, can_delete=True
)
