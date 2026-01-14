from django.forms.widgets import ClearableFileInput


class SetupClearableFileInput(ClearableFileInput):
    """Custom clearable file input that swaps the checkbox for a button."""

    template_name = "setup/widgets/clearable_file_input.html"
