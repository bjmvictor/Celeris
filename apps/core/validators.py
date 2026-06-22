import re

from django.core.exceptions import ValidationError


def only_digits(value):
    return re.sub(r"\D", "", str(value or ""))


def validate_cpf(value):
    digits = only_digits(value)
    if len(digits) != 11 or digits == digits[0] * 11:
        raise ValidationError("Informe um CPF válido.")
    for size in (9, 10):
        total = sum(int(digit) * weight for digit, weight in zip(digits[:size], range(size + 1, 1, -1)))
        verifier = (total * 10 % 11) % 10
        if verifier != int(digits[size]):
            raise ValidationError("Informe um CPF válido.")


def validate_cnes(value):
    digits = only_digits(value)
    if len(digits) != 7:
        raise ValidationError("O CNES deve conter exatamente 7 dígitos.")
