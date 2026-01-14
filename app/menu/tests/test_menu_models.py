"""Tests for Menu models (Item, Variant, Category, Unit)."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from app.menu.models import Category, Item, ItemVariant, Unit, UnitGroup


class UnitModelTests(TestCase):
    """Test Unit model."""

    def test_create_unit(self):
        """Test creating a unit."""
        unit = Unit.objects.create(code="oz", display="Ounces", kind=Unit.KIND_VOLUME)
        self.assertEqual(unit.code, "oz")
        self.assertEqual(unit.display, "Ounces")
        self.assertEqual(unit.kind, Unit.KIND_VOLUME)

    def test_unit_str(self):
        """Unit __str__ should return code."""
        unit = Unit.objects.create(code="cup", display="Cups", kind=Unit.KIND_VOLUME)
        self.assertEqual(str(unit), "cup")

    def test_unit_kinds(self):
        """Test all unit kind choices."""
        kinds = [
            (Unit.KIND_VOLUME, "gal"),
            (Unit.KIND_MASS, "oz"),
            (Unit.KIND_COUNT, "dozen"),
        ]
        for kind, code in kinds:
            with self.subTest(kind=kind):
                unit = Unit.objects.create(code=code, display=code, kind=kind)
                self.assertEqual(unit.kind, kind)

    def test_unit_ordering(self):
        """Units should be ordered by kind, then code."""
        # Create the required units for testing
        pc, _ = Unit.objects.get_or_create(
            code="pc", defaults={"display": "Pieces", "kind": Unit.KIND_COUNT}
        )
        g, _ = Unit.objects.get_or_create(
            code="g", defaults={"display": "Grams", "kind": Unit.KIND_MASS}
        )
        kg, _ = Unit.objects.get_or_create(
            code="kg", defaults={"display": "Kilograms", "kind": Unit.KIND_MASS}
        )
        liter, _ = Unit.objects.get_or_create(
            code="l", defaults={"display": "Liters", "kind": Unit.KIND_VOLUME}
        )
        ml, _ = Unit.objects.get_or_create(
            code="ml", defaults={"display": "Milliliters", "kind": Unit.KIND_VOLUME}
        )

        # Test ordering
        units = list(
            Unit.objects.filter(code__in=["pc", "g", "kg", "l", "ml"]).order_by("kind", "code")
        )
        # Should be ordered by kind (count, mass, volume), then code
        self.assertEqual(units[0].code, "pc")  # count
        self.assertEqual(units[1].code, "g")  # mass
        self.assertEqual(units[2].code, "kg")  # mass
        self.assertEqual(units[3].code, "l")  # volume
        self.assertEqual(units[4].code, "ml")  # volume


class UnitGroupModelTests(TestCase):
    """Test UnitGroup model."""

    def setUp(self):
        # Create units if they don't exist
        self.liter, _ = Unit.objects.get_or_create(
            code="l", defaults={"display": "Liters", "kind": Unit.KIND_VOLUME}
        )
        self.ml, _ = Unit.objects.get_or_create(
            code="ml", defaults={"display": "Milliliters", "kind": Unit.KIND_VOLUME}
        )
        self.gram, _ = Unit.objects.get_or_create(
            code="g", defaults={"display": "Grams", "kind": Unit.KIND_MASS}
        )

    def test_create_unit_group(self):
        """Test creating a unit group."""
        group = UnitGroup.objects.create(name="Beverages")
        group.allowed_units.add(self.liter, self.ml)

        self.assertEqual(group.name, "Beverages")
        self.assertEqual(group.allowed_units.count(), 2)
        self.assertIn(self.liter, group.allowed_units.all())
        self.assertIn(self.ml, group.allowed_units.all())

    def test_unit_group_str(self):
        """UnitGroup __str__ should return name."""
        group = UnitGroup.objects.create(name="Drinks")
        self.assertEqual(str(group), "Drinks")


class CategoryModelTests(TestCase):
    """Test Category model."""

    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(name="Beer", slug="beer-test", kind=Category.KIND_DRINK)
        self.assertEqual(category.name, "Beer")
        self.assertEqual(category.slug, "beer-test")
        self.assertEqual(category.kind, Category.KIND_DRINK)

    def test_category_auto_slug(self):
        """Category should auto-generate slug from name."""
        category = Category.objects.create(name="Craft Beer", kind=Category.KIND_DRINK)
        self.assertEqual(category.slug, "craft-beer")

    def test_category_hierarchy(self):
        """Categories should support parent-child relationships."""
        # Create or get the parent category
        parent, _ = Category.objects.get_or_create(
            slug="drinks", defaults={"name": "Drinks", "kind": Category.KIND_DRINK}
        )
        child = Category.objects.create(
            name="Beer", slug="beer-hier", kind=Category.KIND_DRINK, parent=parent
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_category_depth_property(self):
        """Test depth property for nested categories."""
        root = Category.objects.create(name="Root", slug="root-test", kind=Category.KIND_DRINK)
        level1 = Category.objects.create(
            name="Level 1", slug="level1-test", kind=Category.KIND_DRINK, parent=root
        )
        level2 = Category.objects.create(
            name="Level 2", slug="level2-test", kind=Category.KIND_DRINK, parent=level1
        )

        self.assertEqual(root.depth, 0)
        self.assertEqual(level1.depth, 1)
        self.assertEqual(level2.depth, 2)

    def test_category_kinds(self):
        """Test category kind choices."""
        # Create or get the categories
        drink, _ = Category.objects.get_or_create(
            slug="drinks", defaults={"name": "Drinks", "kind": Category.KIND_DRINK}
        )
        food, _ = Category.objects.get_or_create(
            slug="food", defaults={"name": "Food", "kind": Category.KIND_FOOD}
        )

        self.assertEqual(drink.kind, Category.KIND_DRINK)
        self.assertEqual(food.kind, Category.KIND_FOOD)

    def test_category_unit_group_association(self):
        """Categories can be associated with a unit group."""
        unit_group = UnitGroup.objects.create(name="Beverages")
        category = Category.objects.create(
            name="Beer", slug="beer", kind=Category.KIND_DRINK, unit_group=unit_group
        )
        self.assertEqual(category.unit_group, unit_group)


class ItemModelTests(TestCase):
    """Test Item model."""

    def setUp(self):
        # Create test category if it doesn't exist
        self.category, created = Category.objects.get_or_create(
            slug="drinks", defaults={"name": "Drinks", "kind": Category.KIND_DRINK}
        )

    def test_create_item(self):
        """Test creating a menu item."""
        item = Item.objects.create(
            name="Pilsner",
            slug="pilsner",
            category=self.category,
            description="Classic pilsner beer",
        )
        self.assertEqual(item.name, "Pilsner")
        self.assertEqual(item.slug, "pilsner")
        self.assertEqual(item.category, self.category)
        self.assertEqual(item.description, "Classic pilsner beer")

    def test_item_auto_slug(self):
        """Item should auto-generate slug from name."""
        item = Item.objects.create(name="Craft IPA", category=self.category)
        self.assertEqual(item.slug, "craft-ipa")

    def test_item_dietary_flags_default_false(self):
        """All dietary flags should default to False."""
        item = Item.objects.create(name="Test", slug="test", category=self.category)

        self.assertFalse(item.vegan)
        self.assertFalse(item.vegetarian)
        self.assertFalse(item.gluten_free)
        self.assertFalse(item.sugar_free)
        self.assertFalse(item.lactose_free)
        self.assertFalse(item.nut_free)
        self.assertFalse(item.halal)
        self.assertFalse(item.kosher)

    def test_item_dietary_flags_can_be_set(self):
        """Test setting dietary flags."""
        item = Item.objects.create(
            name="Vegan Burger",
            slug="vegan-burger",
            category=self.category,
            vegan=True,
            vegetarian=True,
            gluten_free=False,
            nut_free=True,
        )

        self.assertTrue(item.vegan)
        self.assertTrue(item.vegetarian)
        self.assertFalse(item.gluten_free)
        self.assertTrue(item.nut_free)

    def test_item_allergens_note(self):
        """Test allergens_note field."""
        item = Item.objects.create(
            name="Peanut Butter Sandwich",
            slug="pb-sandwich",
            category=self.category,
            allergens_note="Contains peanuts and gluten",
        )
        self.assertEqual(item.allergens_note, "Contains peanuts and gluten")

    def test_item_visible_public_default_true(self):
        """Items should be visible by default."""
        item = Item.objects.create(name="Test", slug="test", category=self.category)
        self.assertTrue(item.visible_public)

    def test_item_featured_default_false(self):
        """Items should not be featured by default."""
        item = Item.objects.create(name="Test", slug="test", category=self.category)
        self.assertFalse(item.featured)

    def test_item_is_sold_out_method(self):
        """Test is_sold_out method."""
        future = timezone.now() + timedelta(hours=2)
        past = timezone.now() - timedelta(hours=2)

        item_sold_out = Item.objects.create(
            name="Sold Out Item", slug="sold-out", category=self.category, sold_out_until=future
        )
        item_available = Item.objects.create(
            name="Available Item", slug="available", category=self.category, sold_out_until=past
        )
        item_no_date = Item.objects.create(
            name="No Date Item", slug="no-date", category=self.category
        )

        self.assertTrue(item_sold_out.is_sold_out())
        self.assertFalse(item_available.is_sold_out())
        self.assertFalse(item_no_date.is_sold_out())

    def test_item_is_new_method(self):
        """Test is_new method."""
        future = timezone.now() + timedelta(hours=2)
        past = timezone.now() - timedelta(hours=2)

        item_new = Item.objects.create(
            name="New Item", slug="new", category=self.category, new_until=future
        )
        item_old = Item.objects.create(
            name="Old Item", slug="old", category=self.category, new_until=past
        )
        item_no_date = Item.objects.create(
            name="No Date Item", slug="no-date2", category=self.category
        )

        self.assertTrue(item_new.is_new())
        self.assertFalse(item_old.is_new())
        self.assertFalse(item_no_date.is_new())

    def test_item_active_unit_group_from_category(self):
        """Item should use category's unit group if no override."""
        unit_group = UnitGroup.objects.create(name="Beverages")
        category = Category.objects.create(
            name="Test Drinks", slug="test-drinks", kind=Category.KIND_DRINK, unit_group=unit_group
        )
        item = Item.objects.create(name="Test Beer", slug="test-beer", category=category)

        self.assertEqual(item.active_unit_group(), unit_group)

    def test_item_active_unit_group_override(self):
        """Item should use its own unit group if override is set."""
        default_group = UnitGroup.objects.create(name="Default")
        override_group = UnitGroup.objects.create(name="Override")
        category = Category.objects.create(
            name="Mixed", slug="mixed-cat", kind=Category.KIND_DRINK, unit_group=default_group
        )
        item = Item.objects.create(
            name="Special",
            slug="special-item",
            category=category,
            unit_group_override=override_group,
        )

        self.assertEqual(item.active_unit_group(), override_group)


class ItemVariantModelTests(TestCase):
    """Test ItemVariant model."""

    def setUp(self):
        self.category, created = Category.objects.get_or_create(
            slug="drinks", defaults={"name": "Drinks", "kind": Category.KIND_DRINK}
        )
        self.item = Item.objects.create(name="Pilsner", slug="pilsner", category=self.category)
        self.unit, _ = Unit.objects.get_or_create(
            code="l", defaults={"display": "Liters", "kind": Unit.KIND_VOLUME}
        )  # Use seeded liter unit

    def test_create_variant(self):
        """Test creating an item variant."""
        variant = ItemVariant.objects.create(
            item=self.item,
            label="Pint",
            quantity=Decimal("0.568"),
            unit=self.unit,
            price=Decimal("5.50"),
        )

        self.assertEqual(variant.item, self.item)
        self.assertEqual(variant.label, "Pint")
        self.assertEqual(variant.quantity, Decimal("0.568"))
        self.assertEqual(variant.unit, self.unit)
        self.assertEqual(variant.price, Decimal("5.50"))

    def test_variant_str_with_label(self):
        """Variant __str__ should include label if set."""
        variant = ItemVariant.objects.create(
            item=self.item,
            label="Pint",
            quantity=Decimal("0.5"),
            unit=self.unit,
            price=Decimal("5.00"),
        )
        self.assertIn("Pilsner", str(variant))
        self.assertIn("0.5", str(variant))
        self.assertIn("l", str(variant))  # lowercase l from seeded unit
        self.assertIn("(Pint)", str(variant))

    def test_variant_str_without_label(self):
        """Variant __str__ should work without label."""
        variant = ItemVariant.objects.create(
            item=self.item, quantity=Decimal("0.5"), unit=self.unit, price=Decimal("5.00")
        )
        variant_str = str(variant)
        self.assertIn("Pilsner", variant_str)
        self.assertIn("0.5", variant_str)
        self.assertIn("l", variant_str)  # lowercase l from seeded unit
        self.assertNotIn("()", variant_str)

    def test_variant_abv_field(self):
        """Test ABV (alcohol by volume) field."""
        variant = ItemVariant.objects.create(
            item=self.item,
            quantity=Decimal("0.5"),
            unit=self.unit,
            price=Decimal("5.00"),
            abv=Decimal("5.2"),
        )
        self.assertEqual(variant.abv, Decimal("5.2"))

    def test_variant_abv_nullable(self):
        """ABV should be nullable for non-alcoholic items."""
        variant = ItemVariant.objects.create(
            item=self.item, quantity=Decimal("0.5"), unit=self.unit, price=Decimal("3.00")
        )
        self.assertIsNone(variant.abv)

    def test_variant_multiple_per_item(self):
        """Items can have multiple variants."""
        unit_ml, _ = Unit.objects.get_or_create(
            code="ml", defaults={"display": "Milliliters", "kind": Unit.KIND_VOLUME}
        )  # Use seeded unit

        variant1 = ItemVariant.objects.create(
            item=self.item,
            label="Small",
            quantity=Decimal("0.33"),
            unit=self.unit,
            price=Decimal("4.00"),
        )
        variant2 = ItemVariant.objects.create(
            item=self.item,
            label="Large",
            quantity=Decimal("0.5"),
            unit=self.unit,
            price=Decimal("5.50"),
        )
        variant3 = ItemVariant.objects.create(
            item=self.item,
            label="Pitcher",
            quantity=Decimal("1000"),
            unit=unit_ml,
            price=Decimal("15.00"),
        )

        self.assertEqual(self.item.variants.count(), 3)
        self.assertIn(variant1, self.item.variants.all())
        self.assertIn(variant2, self.item.variants.all())
        self.assertIn(variant3, self.item.variants.all())

    def test_variant_ordering(self):
        """Variants should be ordered by item name, unit kind, quantity, label."""
        unit_g, _ = Unit.objects.get_or_create(
            code="g", defaults={"display": "Grams", "kind": Unit.KIND_MASS}
        )  # Use seeded unit

        ItemVariant.objects.create(
            item=self.item,
            quantity=Decimal("1.0"),
            unit=self.unit,
            price=Decimal("10.00"),
            label="Large",
        )
        ItemVariant.objects.create(
            item=self.item,
            quantity=Decimal("0.5"),
            unit=self.unit,
            price=Decimal("6.00"),
            label="Small",
        )
        ItemVariant.objects.create(
            item=self.item, quantity=Decimal("100"), unit=unit_g, price=Decimal("3.00")
        )

        variants = list(ItemVariant.objects.all())
        # Should be ordered by: item name, unit kind (count, mass, volume), quantity, label
        self.assertEqual(variants[0].unit.kind, Unit.KIND_MASS)
        self.assertEqual(variants[1].quantity, Decimal("0.5"))
        self.assertEqual(variants[2].quantity, Decimal("1.0"))
