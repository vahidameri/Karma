from django.db import transaction
from rest_framework.exceptions import ValidationError

from core.models import OutboxEvent

from .models import CodeSequence, Product, ProductAlias


def technical_code(standard, size, length="", grade="", finish=""):
    return "-".join(
        filter(
            None,
            [standard.code, size + ("X" + length if length else ""), grade, finish],
        )
    ).upper()


@transaction.atomic
def create_product(**attrs):
    # One locked sequence also serializes the shared system/technical/alias namespace.
    CodeSequence.objects.get_or_create(name="product")
    sequence = CodeSequence.objects.select_for_update().get(name="product")
    code = technical_code(
        attrs["standard"],
        attrs["size"],
        attrs.get("length", ""),
        attrs.get("grade", ""),
        attrs.get("finish", ""),
    )
    if ProductAlias.objects.filter(code=code).exists():
        raise ValidationError("کد قبلاً استفاده شده است")
    sequence.value += 1
    sequence.save(update_fields=["value"])
    product = Product.objects.create(
        system_code=f"KR-{sequence.value}", technical_code=code, **attrs
    )
    OutboxEvent.objects.create(topic="ProductCreated", payload={"id": product.pk})
    return product


@transaction.atomic
def update_product(product, **attrs):
    CodeSequence.objects.get_or_create(name="product")
    CodeSequence.objects.select_for_update().get(name="product")
    product = Product.objects.select_for_update().get(pk=product.pk)
    old = product.technical_code
    for key, value in attrs.items():
        if key in {"standard", "size", "length", "grade", "finish", "name", "cost"}:
            setattr(product, key, value)
    product.technical_code = technical_code(
        product.standard, product.size, product.length, product.grade, product.finish
    )
    collision = (
        ProductAlias.objects.filter(code=product.technical_code).exclude(product=product).exists()
    )
    if collision:
        raise ValidationError("کد قبلاً استفاده شده است")
    product.save()
    if old != product.technical_code:
        ProductAlias.objects.get_or_create(code=old, defaults={"product": product})
    OutboxEvent.objects.create(topic="ProductUpdated", payload={"id": product.pk})
    return product
