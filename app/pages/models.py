from copy import deepcopy

from django.conf import settings
from django.db import models
from django.utils import timezone, translation
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from modeltranslation.utils import build_localized_fieldname

from .blocks import build_theme_css, normalise_theme, render_blocks


class PageQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Page.Status.PUBLISHED, published_at__isnull=False)

    def visible(self):
        return self.published().filter(is_visible=True)


class Page(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "Needs review"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    summary = models.TextField(blank=True)
    body = CKEditor5Field("Body", blank=True, config_name="default")
    blocks = models.JSONField(
        default=list,
        blank=True,
        help_text="Structured block data used by the visual page builder.",
    )
    theme = models.JSONField(
        default=dict,
        blank=True,
        help_text="Global styling tokens (fonts/colors) applied to this page.",
    )
    custom_css = models.TextField(blank=True, default="")
    custom_js = models.TextField(blank=True, default="")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    is_visible = models.BooleanField(
        default=True,
        help_text="If disabled page stays in drafts and is hidden from navigation.",
    )
    navigation_order = models.PositiveIntegerField(default=0)
    show_navigation_bar = models.BooleanField(
        default=True,
        help_text="Display navigation bar on this page.",
    )
    custom_nav_items = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of page slugs to display when this page renders (leave empty to hide the navigation bar).",
    )
    layout_overrides = models.JSONField(
        default=list,
        blank=True,
        help_text="Languages that have a custom block layout override.",
    )
    hero_image = models.ImageField(upload_to="pages/heroes/", blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="pages_created",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="pages_updated",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    render_body_only = models.BooleanField(
        default=False,
        help_text="If enabled, ignore block builder and render raw HTML body only.",
    )

    objects = PageQuerySet.as_manager()

    class Meta:
        ordering = ("navigation_order", "title")

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        self.theme = normalise_theme(self.theme or {})
        # Normalise blocks to always be a list
        if isinstance(self.blocks, tuple):
            self.blocks = list(self.blocks)
        if self.blocks is None:
            self.blocks = []
        if self.status != Page.Status.PUBLISHED:
            self.published_at = None
        elif not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("public:page-detail", kwargs={"slug": self.slug})

    def publish(self):
        self.status = Page.Status.PUBLISHED
        if not self.published_at:
            self.published_at = timezone.now()

    def _shared_block_source(self) -> list:
        """
        Return the canonical block layout regardless of the currently active language.
        Falls back to any populated translation field if the shared slot is empty
        (useful for legacy data that predates the explicit overrides flag).
        """

        base_field = self._meta.get_field("blocks").attname
        shared = self.__dict__.get(base_field)
        if shared:
            return shared

        default_lang = settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        default_field = build_localized_fieldname("blocks", default_lang)
        shared = getattr(self, default_field, None)
        if shared:
            return shared

        return []

    def get_blocks_for_language(self, lang: str | None = None) -> list:
        lang = lang or translation.get_language() or settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        field = build_localized_fieldname("blocks", lang)
        value = getattr(self, field, None)
        if value:
            return deepcopy(value)
        return deepcopy(self._shared_block_source())

    def set_blocks_for_language(self, lang: str, blocks: list, override: bool) -> None:
        lang = lang or settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        default_lang = settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        overrides = set(self.layout_overrides or [])
        if override:
            field = build_localized_fieldname("blocks", lang)
            setattr(self, field, deepcopy(blocks))
            overrides.add(lang)
        else:
            shared_value = deepcopy(blocks)
            base_field = self._meta.get_field("blocks").attname
            self.__dict__[base_field] = shared_value
            with translation.override(default_lang):
                self.blocks = shared_value
            if lang != default_lang:
                field = build_localized_fieldname("blocks", lang)
                setattr(self, field, None)
            overrides.discard(lang)
        self.layout_overrides = list(overrides)

    def render_content_segments(self, *, request=None, extra_context=None):
        """
        Render the page into main/footer fragments so templates can place them separately.
        """

        lang = translation.get_language() or settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        blocks_source = self.get_blocks_for_language(lang)

        extra = dict(extra_context or {})
        extra.setdefault("nav_override", list(self.custom_nav_items or []))
        extra.setdefault("request", request)
        structured_data: list[dict] = extra.setdefault("structured_data", [])
        page_url = None
        if request:
            try:
                page_url = request.build_absolute_uri(self.get_absolute_url())
            except Exception:
                page_url = None
        extra.setdefault("page_url", page_url)

        if self.render_body_only or not blocks_source:
            html = self.body or ""
            return mark_safe(html), mark_safe(""), mark_safe(""), structured_data

        nav_blocks = [block for block in blocks_source if block.get("type") == "navigation"]
        footer_blocks = [block for block in blocks_source if block.get("type") == "footer"]
        main_blocks = [
            block
            for block in blocks_source
            if block.get("type") not in {"footer", "navigation"}
        ]

        main_html = render_blocks(main_blocks, request=request, extra_context=extra)
        footer_html = render_blocks(footer_blocks, request=request, extra_context=extra)
        nav_html = mark_safe("")
        if nav_blocks:
            nav_html = render_blocks(nav_blocks[:1], request=request, extra_context=extra)
        elif self.show_navigation_bar:
            auto_block = {
                "id": "auto-navigation",
                "type": "navigation",
                "props": {**DEFAULT_NAV_PROPS},
            }
            nav_html = render_blocks([auto_block], request=request, extra_context=extra)
        return main_html, footer_html, nav_html, structured_data

    def render_content(self, *, request=None, extra_context=None) -> str:
        """
        Render the page blocks to HTML. Falls back to legacy body if flagged or empty.
        """

        main_html, footer_html, nav_html, _ = self.render_content_segments(
            request=request, extra_context=extra_context
        )
        return mark_safe(f"{nav_html}{main_html}{footer_html}")

    def get_theme_tokens(self) -> dict:
        """
        Return the normalised theme payload for this page.
        """

        return normalise_theme(self.theme or {})

    def get_theme_css(self) -> str:
        """
        Build inline CSS for the current theme.
        """

        css, _ = build_theme_css(self.theme or {})
        return css
DEFAULT_NAV_PROPS = {
    "show_logo": True,
    "logo_text": "",
    "logo_text_auto": True,
    "logo_image": "",
    "logo_width": None,
    "show_language_switcher": True,
    "layout": "center",
    "links": [],
}
