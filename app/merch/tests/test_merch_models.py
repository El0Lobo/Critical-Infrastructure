"""Tests for Merch models (Category, Product, ProductImage, ProductVariant)."""

from decimal import Decimal

from django.test import TestCase

from app.merch.models import Category, Product, ProductImage, ProductVariant


class MerchCategoryModelTests(TestCase):
    """Test merch Category model."""

    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        self.assertEqual(category.name, "T-Shirts")
        self.assertEqual(category.slug, "t-shirts")

    def test_category_auto_slug(self):
        """Category should auto-generate slug from name."""
        category = Category.objects.create(name="Limited Edition")
        self.assertEqual(category.slug, "limited-edition")

    def test_category_str(self):
        """__str__ should return category name."""
        category = Category.objects.create(name="Posters")
        self.assertEqual(str(category), "Posters")

    def test_category_hierarchy(self):
        """Categories should support parent-child relationships."""
        parent = Category.objects.create(name="Clothing", slug="clothing")
        child = Category.objects.create(name="Shirts", slug="shirts", parent=parent)

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_category_ordering(self):
        """Categories should be ordered by order field, then name."""
        Category.objects.create(name="Zebra", slug="zebra", order=10)
        Category.objects.create(name="Alpha", slug="alpha", order=5)
        Category.objects.create(name="Beta", slug="beta", order=5)

        categories = list(Category.objects.all())
        self.assertEqual(categories[0].name, "Alpha")
        self.assertEqual(categories[1].name, "Beta")
        self.assertEqual(categories[2].name, "Zebra")


class ProductModelTests(TestCase):
    """Test Product model."""

    def setUp(self):
        self.category = Category.objects.create(name="T-Shirts", slug="t-shirts")

    def test_create_product(self):
        """Test creating a product."""
        product = Product.objects.create(
            name="Band Logo Tee",
            slug="band-logo-tee",
            category=self.category,
            description="Classic band logo t-shirt",
        )
        self.assertEqual(product.name, "Band Logo Tee")
        self.assertEqual(product.slug, "band-logo-tee")
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.description, "Classic band logo t-shirt")

    def test_product_auto_slug(self):
        """Product should auto-generate slug from name."""
        product = Product.objects.create(name="Tour Poster 2024", category=self.category)
        self.assertEqual(product.slug, "tour-poster-2024")

    def test_product_str(self):
        """__str__ should return product name."""
        product = Product.objects.create(name="Hoodie", category=self.category)
        self.assertEqual(str(product), "Hoodie")

    def test_product_visibility_defaults(self):
        """Test product visibility defaults."""
        product = Product.objects.create(name="Test", category=self.category)
        self.assertTrue(product.visible_public)
        self.assertFalse(product.featured)

    def test_product_featured(self):
        """Test featured product flag."""
        product = Product.objects.create(
            name="Featured Item", category=self.category, featured=True
        )
        self.assertTrue(product.featured)

    def test_product_base_price(self):
        """Test product base_price field."""
        product = Product.objects.create(
            name="Simple Product", category=self.category, base_price=Decimal("25.00")
        )
        self.assertEqual(product.base_price, Decimal("25.00"))

    def test_product_min_variant_price_no_variants(self):
        """min_variant_price should return None when no variants."""
        product = Product.objects.create(name="No Variants", category=self.category)
        self.assertIsNone(product.min_variant_price)

    def test_product_min_variant_price_with_variants(self):
        """min_variant_price should return lowest variant price."""
        product = Product.objects.create(name="Varied Product", category=self.category)

        ProductVariant.objects.create(product=product, price=Decimal("30.00"), stock=10)
        ProductVariant.objects.create(product=product, price=Decimal("20.00"), stock=10)
        ProductVariant.objects.create(product=product, price=Decimal("25.00"), stock=10)

        self.assertEqual(product.min_variant_price, Decimal("20.00"))

    def test_product_primary_image_none(self):
        """primary_image should return None when no images."""
        product = Product.objects.create(name="No Images", category=self.category)
        self.assertIsNone(product.primary_image)

    def test_product_ordering(self):
        """Products should be ordered by featured (desc), then name."""
        Product.objects.create(name="Zebra", category=self.category, featured=False)
        Product.objects.create(name="Alpha", category=self.category, featured=True)
        Product.objects.create(name="Mike", category=self.category, featured=False)

        products = list(Product.objects.all())
        # Featured first
        self.assertEqual(products[0].name, "Alpha")
        # Then alphabetically
        self.assertIn(products[1].name, ["Mike", "Zebra"])
        self.assertIn(products[2].name, ["Mike", "Zebra"])


class ProductImageModelTests(TestCase):
    """Test ProductImage model."""

    def setUp(self):
        category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(name="Test Product", category=category)

    def test_product_image_str(self):
        """__str__ should show product name and image pk."""
        img = ProductImage.objects.create(product=self.product, image="test.jpg")
        self.assertIn("Test Product", str(img))
        self.assertIn(str(img.pk), str(img))

    def test_product_image_ordering(self):
        """Images should be ordered by order field, then id."""
        ProductImage.objects.create(product=self.product, image="1.jpg", order=10)
        ProductImage.objects.create(product=self.product, image="2.jpg", order=5)
        ProductImage.objects.create(product=self.product, image="3.jpg", order=5)

        images = list(ProductImage.objects.all())
        self.assertEqual(images[0].order, 5)
        self.assertEqual(images[1].order, 5)
        self.assertEqual(images[2].order, 10)

    def test_product_image_alt_text(self):
        """Test alt_text field."""
        img = ProductImage.objects.create(
            product=self.product, image="test.jpg", alt_text="Band logo on black tee"
        )
        self.assertEqual(img.alt_text, "Band logo on black tee")

    def test_product_image_is_primary(self):
        """Test is_primary flag."""
        img = ProductImage.objects.create(product=self.product, image="test.jpg", is_primary=True)
        self.assertTrue(img.is_primary)


class ProductVariantModelTests(TestCase):
    """Test ProductVariant model."""

    def setUp(self):
        category = Category.objects.create(name="Clothing", slug="clothing")
        self.product = Product.objects.create(name="Band Tee", category=category)

    def test_create_variant(self):
        """Test creating a product variant."""
        variant = ProductVariant.objects.create(
            product=self.product, size_label="M", color="Black", price=Decimal("25.00"), stock=50
        )
        self.assertEqual(variant.size_label, "M")
        self.assertEqual(variant.color, "Black")
        self.assertEqual(variant.price, Decimal("25.00"))
        self.assertEqual(variant.stock, 50)

    def test_variant_str_with_size_and_color(self):
        """__str__ should include size and color if set."""
        variant = ProductVariant.objects.create(
            product=self.product, size_label="L", color="Red", price=Decimal("30.00")
        )
        variant_str = str(variant)
        self.assertIn("Band Tee", variant_str)
        self.assertIn("L", variant_str)
        self.assertIn("Red", variant_str)

    def test_variant_str_with_only_size(self):
        """__str__ should work with only size."""
        variant = ProductVariant.objects.create(
            product=self.product, size_label="XL", price=Decimal("30.00")
        )
        variant_str = str(variant)
        self.assertIn("Band Tee", variant_str)
        self.assertIn("XL", variant_str)

    def test_variant_str_with_only_color(self):
        """__str__ should work with only color."""
        variant = ProductVariant.objects.create(
            product=self.product, color="Blue", price=Decimal("25.00")
        )
        variant_str = str(variant)
        self.assertIn("Band Tee", variant_str)
        self.assertIn("Blue", variant_str)

    def test_variant_str_without_size_or_color(self):
        """__str__ should work without size or color."""
        variant = ProductVariant.objects.create(product=self.product, price=Decimal("25.00"))
        self.assertEqual(str(variant), "Band Tee")

    def test_variant_dimensions(self):
        """Test length_cm and width_cm fields."""
        variant = ProductVariant.objects.create(
            product=self.product,
            length_cm=Decimal("50.00"),
            width_cm=Decimal("30.00"),
            price=Decimal("15.00"),
        )
        self.assertEqual(variant.length_cm, Decimal("50.00"))
        self.assertEqual(variant.width_cm, Decimal("30.00"))

    def test_variant_sku(self):
        """Test SKU field."""
        variant = ProductVariant.objects.create(
            product=self.product, sku="TEE-BLK-M", price=Decimal("25.00")
        )
        self.assertEqual(variant.sku, "TEE-BLK-M")

    def test_variant_stock_default(self):
        """Stock should default to 0."""
        variant = ProductVariant.objects.create(product=self.product, price=Decimal("25.00"))
        self.assertEqual(variant.stock, 0)

    def test_variant_ordering(self):
        """Variants should be ordered by price, then id."""
        ProductVariant.objects.create(product=self.product, price=Decimal("30.00"))
        ProductVariant.objects.create(product=self.product, price=Decimal("20.00"))
        ProductVariant.objects.create(product=self.product, price=Decimal("25.00"))

        variants = list(ProductVariant.objects.all())
        self.assertEqual(variants[0].price, Decimal("20.00"))
        self.assertEqual(variants[1].price, Decimal("25.00"))
        self.assertEqual(variants[2].price, Decimal("30.00"))

    def test_multiple_variants_per_product(self):
        """Products can have multiple variants."""
        v1 = ProductVariant.objects.create(
            product=self.product, size_label="S", price=Decimal("20.00")
        )
        v2 = ProductVariant.objects.create(
            product=self.product, size_label="M", price=Decimal("25.00")
        )
        v3 = ProductVariant.objects.create(
            product=self.product, size_label="L", price=Decimal("30.00")
        )

        self.assertEqual(self.product.variants.count(), 3)
        self.assertIn(v1, self.product.variants.all())
        self.assertIn(v2, self.product.variants.all())
        self.assertIn(v3, self.product.variants.all())
