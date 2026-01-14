# app/menu/models.py
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

# Standard slug (letters, numbers, hyphens, underscores). No dots -> avoids URL reversing issues.
slug_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_-]+$",
    message="Enter a valid “slug” (letters, numbers, underscores, or hyphens).",
)


def unique_slug_for(instance, base: str, field_name: str = "slug"):
    """
    Create a unique slug from `base` for the given model instance,
    stored in the given `field_name`.
    """
    base_slug = slugify(base) or "item"
    slug = base_slug
    n = 2
    Model = instance.__class__
    while Model.objects.filter(**{field_name: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


class Unit(models.Model):
    KIND_VOLUME = "volume"
    KIND_MASS = "mass"
    KIND_COUNT = "count"
    KIND_CHOICES = [
        (KIND_VOLUME, "Volume"),
        (KIND_MASS, "Mass"),
        (KIND_COUNT, "Count"),
    ]

    code = models.CharField(max_length=16, unique=True)  # e.g. L, mL, g, pcs
    display = models.CharField(max_length=32)  # e.g. "Liters", "grams", "pieces"
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)

    class Meta:
        ordering = ["kind", "code"]

    def __str__(self):
        return self.code


class UnitGroup(models.Model):
    """
    Controls which units are allowed for a branch of the menu.
    Drinks will use a group with L/mL; Food a group with g/pcs.
    """

    name = models.CharField(max_length=64, unique=True)
    allowed_units = models.ManyToManyField(Unit, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    KIND_GENERIC = "generic"
    KIND_DRINK = "drink"
    KIND_FOOD = "food"
    KIND_CHOICES = [
        (KIND_GENERIC, "General"),
        (KIND_DRINK, "Drink"),
        (KIND_FOOD, "Food"),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, validators=[slug_validator], blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    kind = models.CharField(
        max_length=16,
        choices=KIND_CHOICES,
        default=KIND_GENERIC,
        blank=True,
    )
    unit_group = models.ForeignKey(UnitGroup, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["parent__id", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_for(self, self.name)
        super().save(*args, **kwargs)

    @property
    def depth(self) -> int:
        d, p = 0, self.parent
        while p:
            d += 1
            p = p.parent
        return d


class Item(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, validators=[slug_validator], blank=True)
    category = models.ForeignKey(Category, related_name="items", on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    allergens_note = models.CharField(max_length=240, blank=True)

    # Dietary flags
    vegan = models.BooleanField(default=False)
    vegetarian = models.BooleanField(default=False)
    gluten_free = models.BooleanField(default=False)
    sugar_free = models.BooleanField(default=False)
    lactose_free = models.BooleanField(default=False)
    nut_free = models.BooleanField(default=False)
    halal = models.BooleanField(default=False)
    kosher = models.BooleanField(default=False)

    # Visibility/featured/new/sold-out
    visible_public = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    sold_out_until = models.DateTimeField(null=True, blank=True)
    new_until = models.DateTimeField(null=True, blank=True)

    # Optionally override category's unit group
    unit_group_override = models.ForeignKey(
        UnitGroup, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_for(self, self.name)
        super().save(*args, **kwargs)

    def active_unit_group(self):
        return self.unit_group_override or self.category.unit_group

    # Note: in Django templates you can call no-arg methods without parentheses,
    # so `{% if i.is_sold_out %}` works with this method signature.
    def is_sold_out(self) -> bool:
        return bool(self.sold_out_until and self.sold_out_until >= timezone.now())

    def is_new(self) -> bool:
        return bool(self.new_until and self.new_until >= timezone.now())


class ItemVariant(models.Model):
    item = models.ForeignKey(Item, related_name="variants", on_delete=models.CASCADE)
    label = models.CharField(max_length=64, blank=True)
    quantity = models.DecimalField(
        max_digits=8, decimal_places=3, validators=[MinValueValidator(0)]
    )
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    abv = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="Alcohol by volume (%)"
    )

    class Meta:
        ordering = ["item__name", "unit__kind", "quantity", "label"]

    def __str__(self):
        base = f"{self.item.name} • {self.quantity:g} {self.unit.code}"
        if self.label:
            base += f" ({self.label})"
        return base
