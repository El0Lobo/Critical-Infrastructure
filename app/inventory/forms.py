from django import forms
from django.forms import inlineformset_factory

from app.menu.models import Item as MenuItem
from app.merch.models import Product as MerchProduct
from app.setup.models import SiteSettings

from .models import InventoryCategory, InventoryItem, InventoryPackage


class InventoryCategoryForm(forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = ["name", "parent", "sort_order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class InventoryItemForm(forms.ModelForm):
    menu_items = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
    )
    merch_products = forms.ModelMultipleChoiceField(
        queryset=MerchProduct.objects.order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
    )

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "kind",
            "description",
            "location",
            "unit",
            "unit_label",
            "pack_quantity",
            "pack_unit",
            "current_stock",
            "desired_stock",
            "reorder_point",
            "auto_track_sales",
            "public_visible",
            "public_description",
            "public_url",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "unit_label": forms.TextInput(attrs={"class": "form-control"}),
            "pack_quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "pack_unit": forms.Select(attrs={"class": "form-select"}),
            "current_stock": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "desired_stock": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "reorder_point": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "public_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "public_url": forms.URLInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["menu_items"].initial = self.instance.menu_items.all()
            self.fields["merch_products"].initial = self.instance.merch_products.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


InventoryPackageFormSet = inlineformset_factory(
    InventoryItem,
    InventoryPackage,
    fields=["label", "quantity", "unit", "is_default", "notes"],
    extra=1,
    can_delete=True,
    widgets={
        "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bottle / Case"}),
        "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        "unit": forms.Select(attrs={"class": "form-select"}),
        "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Notes"}),
    },
)


class InventoryAlertSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["inventory_notification_groups", "inventory_dashboard_groups"]
        widgets = {
            "inventory_notification_groups": forms.CheckboxSelectMultiple,
            "inventory_dashboard_groups": forms.CheckboxSelectMultiple,
        }
        labels = {
            "inventory_notification_groups": "Notify these groups when items need reordering",
            "inventory_dashboard_groups": "Allow these groups to see dashboard alerts",
        }
