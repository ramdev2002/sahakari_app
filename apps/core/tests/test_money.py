from decimal import Decimal

from django.db import models
from django.test import SimpleTestCase

from apps.core.money import (
    MONEY_DECIMAL_PLACES,
    MONEY_MAX_DIGITS,
    MoneyField,
    MoneyValidationError,
    to_money,
)


class ToMoneyTests(SimpleTestCase):
    def test_integer_converts_and_quantizes(self):
        self.assertEqual(to_money(10), Decimal('10.00'))

    def test_decimal_quantizes_to_two_places(self):
        self.assertEqual(to_money(Decimal('12.5')), Decimal('12.50'))

    def test_rounds_half_up(self):
        self.assertEqual(to_money(Decimal('1.005')), Decimal('1.01'))
        self.assertEqual(to_money(Decimal('1.004')), Decimal('1.00'))

    def test_float_converts_without_binary_artifacts(self):
        self.assertEqual(to_money(0.1), Decimal('0.10'))

    def test_string_amount_accepted(self):
        self.assertEqual(to_money('123.456'), Decimal('123.46'))

    def test_negative_amount_allowed(self):
        self.assertEqual(to_money('-50'), Decimal('-50.00'))

    def test_none_rejected_by_default(self):
        with self.assertRaises(MoneyValidationError):
            to_money(None)

    def test_none_allowed_when_requested(self):
        self.assertIsNone(to_money(None, allow_none=True))

    def test_nan_rejected(self):
        with self.assertRaises(MoneyValidationError):
            to_money(Decimal('NaN'))

    def test_infinity_rejected(self):
        with self.assertRaises(MoneyValidationError):
            to_money(Decimal('Infinity'))
        with self.assertRaises(MoneyValidationError):
            to_money(float('inf'))

    def test_non_numeric_rejected(self):
        for bad in ('abc', [1, 2], object()):
            with self.assertRaises(MoneyValidationError):
                to_money(bad)


class MoneyFieldTests(SimpleTestCase):
    def test_is_decimal_field(self):
        self.assertTrue(issubclass(MoneyField, models.DecimalField))

    def test_default_precision_and_scale(self):
        field = MoneyField()
        self.assertEqual(field.max_digits, MONEY_MAX_DIGITS)
        self.assertEqual(field.decimal_places, MONEY_DECIMAL_PLACES)

    def test_explicit_local_args_still_apply(self):
        field = MoneyField(blank=True, null=True)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)
        self.assertEqual(field.max_digits, MONEY_MAX_DIGITS)
