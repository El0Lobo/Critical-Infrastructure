from django import forms
from django.forms import inlineformset_factory

from .models import Category, Product, ProductImage, ProductVariant


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "parent", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "visible_public", "featured", "base_price"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "visible_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "base_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_primary", "order"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "alt_text": forms.TextInput(attrs={"class": "form-control"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["size_label", "color", "length_cm", "width_cm", "sku", "price", "stock"]
        widgets = {
            "size_label": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "S / M / L or custom"}
            ),
            "color": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Black / Red ..."}
            ),
            "length_cm": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "width_cm": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "sku": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
        }


ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=0, can_delete=True
)

ProductVariantFormSet = inlineformset_factory(
    Product, ProductVariant, form=ProductVariantForm, extra=0, can_delete=True
)
