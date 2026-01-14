from __future__ import annotations

from django import forms
from django.forms import ModelForm, modelformset_factory

from app.setup.models import SiteSettings

from .models import POSQuickButton


class POSSettingsForm(ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "pos_show_discounts",
            "pos_apply_discounts",
            "pos_show_tax",
            "pos_apply_tax",
            "pos_tax_rate",
        ]
        labels = {
            "pos_show_discounts": "Show discount panel in POS",
            "pos_apply_discounts": "Allow discounts to change totals",
            "pos_show_tax": "Show tax row in POS",
            "pos_apply_tax": "Apply tax to POS totals",
            "pos_tax_rate": "Default POS tax rate (%)",
        }
        widgets = {
            "pos_tax_rate": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_required_attribute = False
        for field in self.fields.values():
            field.required = False


POSQuickButtonFormSet = modelformset_factory(
    model=POSQuickButton,
    fields=["label", "discount_type", "value", "scope", "reason", "sort_order", "is_active"],
    extra=0,
    can_delete=True,
    widgets={
        "value": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        "sort_order": forms.NumberInput(attrs={"step": "1", "min": "0"}),
    },
)
