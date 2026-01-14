# app/merch/models.py
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

# ---- helpers ---------------------------------------------------------------


def unique_slug(model, base, field_name="slug", instance_id=None):
    """
    Generate a unique slug for `model` using `base`.
    If `instance_id` is provided, exclude that row (for updates).
    """
    base_slug = slugify(base) or "item"
    slug = base_slug
    n = 2
    qs = model.objects.all()
    if instance_id:
        qs = qs.exclude(pk=instance_id)
    while qs.filter(**{field_name: slug}).exists():
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


# ---- core models -----------------------------------------------------------


class Category(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, blank=True, db_index=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, instance_id=self.pk)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True, db_index=True)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    description = models.TextField(blank=True)

    visible_public = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)

    # Optional base price (if you don't want variants yet)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional. If omitted, the min variant price is shown.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-featured", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Product, self.name, instance_id=self.pk)
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        """
        Return the primary image if set; else the first by order.
        """
        img = self.images.filter(is_primary=True).order_by("order", "id").first()
        return img or self.images.order_by("order", "id").first()

    @property
    def min_variant_price(self):
        """
        The lowest variant price (Decimal) or None if no variants.
        """
        v = self.variants.order_by("price").only("price").first()
        return v.price if v else None


def product_image_upload_path(instance, filename):
    ts = timezone.now().strftime("%Y/%m")
    return f"merch/{ts}/{filename}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_image_upload_path)
    alt_text = models.CharField(max_length=160, blank=True)

    # Gallery control
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        # At most one primary image per product
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_primary=True),
                name="unique_primary_image_per_product",
            )
        ]

    def __str__(self):
        return f"{self.product.name} image #{self.pk}"


# Helpful for forms; free text still allowed via size_label
SIZE_CHOICES = [
    ("", "— choose —"),
    ("XS", "XS"),
    ("S", "S"),
    ("M", "M"),
    ("L", "L"),
    ("XL", "XL"),
    ("XXL", "XXL"),
    ("XXXL", "XXXL"),
]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)

    # clothing-style variation
    size_label = models.CharField(
        max_length=32,
        blank=True,
        help_text="Clothing size (e.g., S, M, L) or free text",
    )
    color = models.CharField(max_length=40, blank=True)

    # dimensions for posters, accessories, etc.
    length_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    width_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # inventory / pricing
    sku = models.CharField(max_length=64, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["price", "id"]
        constraints = [
            # Optional: ensure SKU uniqueness per product when provided
            models.UniqueConstraint(
                fields=["product", "sku"],
                condition=~Q(sku=""),
                name="unique_sku_per_product_when_set",
            ),
        ]

    def __str__(self):
        bits = [self.product.name]
        if self.size_label:
            bits.append(self.size_label)
        if self.color:
            bits.append(self.color)
        return " / ".join(bits)
