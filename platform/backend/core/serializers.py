import jdatetime
from rest_framework import serializers


class JalaliDateField(serializers.DateField):
    def to_internal_value(self, value):
        if isinstance(value, str):
            from search.parser import normalize

            value = normalize(value).replace("/", "-")
            try:
                y, m, d = map(int, value.split("-"))
                if y < 1700:
                    return jdatetime.date(y, m, d).togregorian()
            except (ValueError, TypeError):
                self.fail("invalid", format="YYYY-MM-DD")
        return super().to_internal_value(value)

    def to_representation(self, value):
        return jdatetime.date.fromgregorian(date=value).strftime("%Y-%m-%d") if value else None


def validate_money_precision(value):
    from django.db import connection

    if connection.vendor == "sqlite" and abs(value) >= 10**15:
        raise serializers.ValidationError(
            "برای مبالغ بزرگ‌تر از ۱۵ رقم از PostgreSQL استفاده کنید؛ محدودیت SQLite توسعه اجازهٔ ثبت بدون دقت را نمی‌دهد"
        )
    return value


class ExactModelSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        from decimal import Decimal

        for name, value in attrs.items():
            field = self.fields.get(name)
            if (
                isinstance(field, serializers.DecimalField)
                and field.decimal_places == 0
                and isinstance(value, Decimal)
            ):
                validate_money_precision(value)
        return super().validate(attrs)
