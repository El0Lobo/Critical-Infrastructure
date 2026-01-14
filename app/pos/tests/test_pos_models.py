"""Tests for POS (Point of Sale) models."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.menu.models import Category, Item, ItemVariant, Unit
from app.pos.models import DiscountReason, Payment, POSQuickButton, Sale, SaleItem

User = get_user_model()


class DiscountReasonModelTests(TestCase):
    """Test DiscountReason model."""

    def test_create_discount_reason(self):
        """Test creating a discount reason."""
        reason = DiscountReason.objects.create(name="Staff Discount")
        self.assertEqual(reason.name, "Staff Discount")
        self.assertTrue(reason.is_active)

    def test_discount_reason_str(self):
        """DiscountReason __str__ should return name."""
        reason = DiscountReason.objects.create(name="Happy Hour")
        self.assertEqual(str(reason), "Happy Hour")

    def test_discount_reason_can_be_inactive(self):
        """Discount reasons can be marked inactive."""
        reason = DiscountReason.objects.create(name="Expired", is_active=False)
        self.assertFalse(reason.is_active)


class POSQuickButtonModelTests(TestCase):
    """Test POSQuickButton model."""

    def setUp(self):
        self.reason = DiscountReason.objects.create(name="Staff Discount")

    def test_create_percent_discount_button(self):
        """Test creating a percentage discount button."""
        button = POSQuickButton.objects.create(
            label="10% Off",
            discount_type=POSQuickButton.TYPE_PERCENT,
            value=Decimal("10.00"),
            scope=POSQuickButton.SCOPE_ORDER,
            reason=self.reason,
        )

        self.assertEqual(button.label, "10% Off")
        self.assertEqual(button.discount_type, POSQuickButton.TYPE_PERCENT)
        self.assertEqual(button.value, Decimal("10.00"))
        self.assertEqual(button.scope, POSQuickButton.SCOPE_ORDER)
        self.assertEqual(button.reason, self.reason)

    def test_create_amount_discount_button(self):
        """Test creating a fixed amount discount button."""
        button = POSQuickButton.objects.create(
            label="$5 Off",
            discount_type=POSQuickButton.TYPE_AMOUNT,
            value=Decimal("5.00"),
            scope=POSQuickButton.SCOPE_ITEM,
        )

        self.assertEqual(button.discount_type, POSQuickButton.TYPE_AMOUNT)
        self.assertEqual(button.value, Decimal("5.00"))
        self.assertEqual(button.scope, POSQuickButton.SCOPE_ITEM)

    def test_create_free_button(self):
        """Test creating a free (100%) discount button."""
        button = POSQuickButton.objects.create(
            label="Free", discount_type=POSQuickButton.TYPE_FREE, scope=POSQuickButton.SCOPE_ITEM
        )

        self.assertEqual(button.discount_type, POSQuickButton.TYPE_FREE)

    def test_button_str_percent(self):
        """Test __str__ for percentage button."""
        button = POSQuickButton.objects.create(
            label="Staff",
            discount_type=POSQuickButton.TYPE_PERCENT,
            value=Decimal("15.00"),
            scope=POSQuickButton.SCOPE_ORDER,
        )
        button_str = str(button)
        self.assertIn("Staff", button_str)
        self.assertIn("15", button_str)
        self.assertIn("%", button_str)
        self.assertIn("ORDER", button_str)

    def test_button_str_amount(self):
        """Test __str__ for amount button."""
        button = POSQuickButton.objects.create(
            label="Discount",
            discount_type=POSQuickButton.TYPE_AMOUNT,
            value=Decimal("10.00"),
            scope=POSQuickButton.SCOPE_ITEM,
        )
        button_str = str(button)
        self.assertIn("Discount", button_str)
        self.assertIn("10", button_str)
        self.assertIn("ITEM", button_str)

    def test_button_str_free(self):
        """Test __str__ for free button."""
        button = POSQuickButton.objects.create(
            label="Comp", discount_type=POSQuickButton.TYPE_FREE, scope=POSQuickButton.SCOPE_ITEM
        )
        button_str = str(button)
        self.assertIn("Comp", button_str)
        self.assertIn("FREE", button_str)

    def test_button_ordering(self):
        """Buttons should be ordered by sort_order, then id."""
        POSQuickButton.objects.create(
            label="Third",
            discount_type=POSQuickButton.TYPE_PERCENT,
            value=Decimal("10"),
            sort_order=30,
        )
        POSQuickButton.objects.create(
            label="First",
            discount_type=POSQuickButton.TYPE_PERCENT,
            value=Decimal("10"),
            sort_order=10,
        )
        POSQuickButton.objects.create(
            label="Second",
            discount_type=POSQuickButton.TYPE_PERCENT,
            value=Decimal("10"),
            sort_order=20,
        )

        buttons = list(POSQuickButton.objects.all())
        self.assertEqual(buttons[0].label, "First")
        self.assertEqual(buttons[1].label, "Second")
        self.assertEqual(buttons[2].label, "Third")


class SaleModelTests(TestCase):
    """Test Sale model."""

    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="password")
        self.reason = DiscountReason.objects.create(name="Happy Hour")

    def test_create_sale(self):
        """Test creating a sale."""
        sale = Sale.objects.create(opened_by=self.user, status=Sale.STATUS_OPEN)

        self.assertEqual(sale.opened_by, self.user)
        self.assertEqual(sale.status, Sale.STATUS_OPEN)
        self.assertIsNone(sale.closed_by)
        self.assertIsNone(sale.closed_at)
        self.assertIsNotNone(sale.created_at)

    def test_sale_defaults(self):
        """Test sale default values."""
        sale = Sale.objects.create(opened_by=self.user)

        self.assertEqual(sale.status, Sale.STATUS_OPEN)
        self.assertEqual(sale.subtotal, Decimal("0"))
        self.assertEqual(sale.discount_total, Decimal("0"))
        self.assertEqual(sale.tax_total, Decimal("0"))
        self.assertEqual(sale.grand_total, Decimal("0"))
        self.assertEqual(sale.note, "")

    def test_sale_str(self):
        """Sale __str__ should show ID and status."""
        sale = Sale.objects.create(opened_by=self.user, status=Sale.STATUS_PAID)
        sale_str = str(sale)
        self.assertIn(str(sale.pk), sale_str)
        self.assertIn("PAID", sale_str)

    def test_sale_status_choices(self):
        """Test all sale status choices."""
        statuses = [Sale.STATUS_OPEN, Sale.STATUS_PAID, Sale.STATUS_VOID]
        for status in statuses:
            with self.subTest(status=status):
                sale = Sale.objects.create(opened_by=self.user, status=status)
                self.assertEqual(sale.status, status)

    def test_sale_with_order_discount(self):
        """Test sale with order-level discount."""
        sale = Sale.objects.create(
            opened_by=self.user,
            order_discount_type=POSQuickButton.TYPE_PERCENT,
            order_discount_value=Decimal("10.00"),
            order_discount_reason=self.reason,
        )

        self.assertEqual(sale.order_discount_type, POSQuickButton.TYPE_PERCENT)
        self.assertEqual(sale.order_discount_value, Decimal("10.00"))
        self.assertEqual(sale.order_discount_reason, self.reason)

    def test_sale_close(self):
        """Test closing a sale."""
        sale = Sale.objects.create(opened_by=self.user)

        closer = User.objects.create_user(username="closer", password="password")
        sale.status = Sale.STATUS_PAID
        sale.closed_by = closer
        sale.closed_at = timezone.now()
        sale.save()

        self.assertEqual(sale.status, Sale.STATUS_PAID)
        self.assertEqual(sale.closed_by, closer)
        self.assertIsNotNone(sale.closed_at)

    def test_sale_totals(self):
        """Test sale with calculated totals."""
        sale = Sale.objects.create(
            opened_by=self.user,
            subtotal=Decimal("100.00"),
            discount_total=Decimal("10.00"),
            tax_total=Decimal("9.00"),
            grand_total=Decimal("99.00"),
        )

        self.assertEqual(sale.subtotal, Decimal("100.00"))
        self.assertEqual(sale.discount_total, Decimal("10.00"))
        self.assertEqual(sale.tax_total, Decimal("9.00"))
        self.assertEqual(sale.grand_total, Decimal("99.00"))


class SaleItemModelTests(TestCase):
    """Test SaleItem model."""

    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="password")
        self.sale = Sale.objects.create(opened_by=self.user)

        # Create menu items for testing using seeded data
        self.category, _ = Category.objects.get_or_create(
            slug="drinks", defaults={"name": "Drinks", "kind": Category.KIND_DRINK}
        )
        self.item = Item.objects.create(name="Beer", slug="beer-pos", category=self.category)
        self.unit, _ = Unit.objects.get_or_create(
            code="l", defaults={"display": "Liters", "kind": Unit.KIND_VOLUME}
        )  # Use seeded liter unit
        self.variant = ItemVariant.objects.create(
            item=self.item, quantity=Decimal("0.5"), unit=self.unit, price=Decimal("5.00")
        )

    def test_create_sale_item(self):
        """Test creating a sale item."""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            menu_variant=self.variant,
            title_snapshot="Beer • 0.5 L",
            quantity=2,
            unit_price=Decimal("5.00"),
            line_subtotal=Decimal("10.00"),
            line_total=Decimal("10.00"),
        )

        self.assertEqual(sale_item.sale, self.sale)
        self.assertEqual(sale_item.menu_variant, self.variant)
        self.assertEqual(sale_item.quantity, 2)
        self.assertEqual(sale_item.unit_price, Decimal("5.00"))
        self.assertEqual(sale_item.line_subtotal, Decimal("10.00"))
        self.assertEqual(sale_item.line_total, Decimal("10.00"))

    def test_sale_item_str(self):
        """SaleItem __str__ should show title and quantity."""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            menu_variant=self.variant,
            title_snapshot="Beer • 0.5 L",
            quantity=3,
            unit_price=Decimal("5.00"),
        )
        sale_item_str = str(sale_item)
        self.assertIn("Beer", sale_item_str)
        self.assertIn("x3", sale_item_str)

    def test_sale_item_with_discount(self):
        """Test sale item with item-level discount."""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            menu_variant=self.variant,
            title_snapshot="Beer • 0.5 L",
            quantity=1,
            unit_price=Decimal("5.00"),
            discount_type=POSQuickButton.TYPE_PERCENT,
            discount_value=Decimal("20.00"),
            line_subtotal=Decimal("5.00"),
            line_discount=Decimal("1.00"),
            line_total=Decimal("4.00"),
        )

        self.assertEqual(sale_item.discount_type, POSQuickButton.TYPE_PERCENT)
        self.assertEqual(sale_item.discount_value, Decimal("20.00"))
        self.assertEqual(sale_item.line_discount, Decimal("1.00"))

    def test_sale_item_with_tax(self):
        """Test sale item with tax calculation."""
        sale_item = SaleItem.objects.create(
            sale=self.sale,
            menu_variant=self.variant,
            title_snapshot="Beer • 0.5 L",
            quantity=1,
            unit_price=Decimal("5.00"),
            tax_rate=Decimal("10.00"),
            tax_amount=Decimal("0.50"),
            line_subtotal=Decimal("5.00"),
            line_total=Decimal("5.50"),
        )

        self.assertEqual(sale_item.tax_rate, Decimal("10.00"))
        self.assertEqual(sale_item.tax_amount, Decimal("0.50"))

    def test_sale_multiple_items(self):
        """Sale can have multiple items."""
        item2 = Item.objects.create(name="Wine", slug="wine", category=self.category)
        variant2 = ItemVariant.objects.create(
            item=item2, quantity=Decimal("0.2"), unit=self.unit, price=Decimal("8.00")
        )

        sale_item1 = SaleItem.objects.create(
            sale=self.sale,
            menu_variant=self.variant,
            title_snapshot="Beer",
            quantity=2,
            unit_price=Decimal("5.00"),
        )
        sale_item2 = SaleItem.objects.create(
            sale=self.sale,
            menu_variant=variant2,
            title_snapshot="Wine",
            quantity=1,
            unit_price=Decimal("8.00"),
        )

        self.assertEqual(self.sale.items.count(), 2)
        self.assertIn(sale_item1, self.sale.items.all())
        self.assertIn(sale_item2, self.sale.items.all())


class PaymentModelTests(TestCase):
    """Test Payment model."""

    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="password")
        self.sale = Sale.objects.create(opened_by=self.user, grand_total=Decimal("50.00"))

    def test_create_cash_payment(self):
        """Test creating a cash payment."""
        payment = Payment.objects.create(
            sale=self.sale, kind=Payment.KIND_CASH, amount=Decimal("50.00"), received_by=self.user
        )

        self.assertEqual(payment.sale, self.sale)
        self.assertEqual(payment.kind, Payment.KIND_CASH)
        self.assertEqual(payment.amount, Decimal("50.00"))
        self.assertEqual(payment.received_by, self.user)
        self.assertIsNotNone(payment.received_at)

    def test_create_card_payment(self):
        """Test creating a card payment."""
        payment = Payment.objects.create(
            sale=self.sale, kind=Payment.KIND_CARD, amount=Decimal("50.00"), received_by=self.user
        )

        self.assertEqual(payment.kind, Payment.KIND_CARD)

    def test_create_other_payment(self):
        """Test creating an other payment."""
        payment = Payment.objects.create(
            sale=self.sale, kind=Payment.KIND_OTHER, amount=Decimal("50.00"), received_by=self.user
        )

        self.assertEqual(payment.kind, Payment.KIND_OTHER)

    def test_payment_str(self):
        """Payment __str__ should show kind, amount, and sale."""
        payment = Payment.objects.create(
            sale=self.sale, kind=Payment.KIND_CASH, amount=Decimal("50.00"), received_by=self.user
        )
        payment_str = str(payment)
        self.assertIn("CASH", payment_str)
        self.assertIn("50", payment_str)
        self.assertIn(str(self.sale.id), payment_str)

    def test_payment_default_kind_cash(self):
        """Payment should default to cash."""
        payment = Payment.objects.create(
            sale=self.sale, amount=Decimal("50.00"), received_by=self.user
        )
        self.assertEqual(payment.kind, Payment.KIND_CASH)

    def test_split_payment(self):
        """Sale can have multiple payments (split payment)."""
        payment1 = Payment.objects.create(
            sale=self.sale, kind=Payment.KIND_CASH, amount=Decimal("30.00"), received_by=self.user
        )
        payment2 = Payment.objects.create(
            sale=self.sale, kind=Payment.KIND_CARD, amount=Decimal("20.00"), received_by=self.user
        )

        self.assertEqual(self.sale.payments.count(), 2)
        self.assertIn(payment1, self.sale.payments.all())
        self.assertIn(payment2, self.sale.payments.all())

        total_paid = sum(p.amount for p in self.sale.payments.all())
        self.assertEqual(total_paid, Decimal("50.00"))
