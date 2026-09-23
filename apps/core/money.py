from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import models

MONEY_MAX_DIGITS = 20
MONEY_DECIMAL_PLACES = 2
MONEY_ROUNDING = ROUND_HALF_UP
MONEY_QUANT = Decimal('0.01')


class MoneyValidationError(ValueError):
    """Raised when a value cannot safely become a money amount."""


class MoneyField(models.DecimalField):
    """
    The one money column type for Sahakari.

    Always NUMERIC(20, 2). Never store floats as money; feed this field through
    ``to_money()`` so values are validated and quantized at the boundary.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_digits', MONEY_MAX_DIGITS)
        kwargs.setdefault('decimal_places', MONEY_DECIMAL_PLACES)
        super().__init__(*args, **kwargs)


def to_money(value, *, allow_none=False):
    """
    Convert a value to a validated, quantized Decimal money amount.

    Floats are converted via ``str()`` (never Decimal(float)) to avoid binary
    floating-point artifacts, then rounded half-up to 2 decimal places.

    Raises ``MoneyValidationError`` for NaN/Infinity, non-numeric input, or
    None when ``allow_none`` is False.
    """
    if value is None:
        if allow_none:
            return None
        raise MoneyValidationError('Money amount cannot be None.')

    if isinstance(value, float):
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise MoneyValidationError('Invalid numeric amount.') from exc
    elif isinstance(value, int):
        value = Decimal(value)
    elif isinstance(value, Decimal):
        value = value
    else:
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise MoneyValidationError('Invalid numeric amount.') from exc

    if not value.is_finite():
        raise MoneyValidationError('Money amount must be a finite number.')

    return value.quantize(MONEY_QUANT, rounding=MONEY_ROUNDING)
