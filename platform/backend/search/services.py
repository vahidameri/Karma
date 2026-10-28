from django.conf import settings
from django.db.models import Q
from elasticsearch import Elasticsearch
from rest_framework.exceptions import APIException

from .parser import parse


def client():
    return Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=5)


def search_products(text):
    from catalog.models import Product, Standard

    p = parse(text)
    qs = Product.objects.select_related("standard").defer("standard__dimensions")
    if text:
        exact = qs.filter(
            Q(system_code__iexact=p["text"])
            | Q(technical_code__iexact=p["text"])
            | Q(aliases__code__iexact=p["text"])
        ).distinct()
        if exact.exists():
            return (
                list(exact[:60]),
                p,
                "elasticsearch" if settings.ELASTICSEARCH_URL else "database-development",
            )
    standard_query = Q(pk__in=[])
    for code in p["standards"]:
        standard_query |= Q(code__istartswith=code)
        if code.startswith("A"):
            standard_query |= Q(code__icontains=code)
    standards = (
        list(Standard.objects.filter(standard_query).values_list("code", flat=True))
        if p["standards"]
        else []
    )
    if settings.ELASTICSEARCH_URL:
        should = []
        terms = []
        shape = []
        if standards:
            standard_clause = {"terms": {"standard.keyword": standards}}
            terms.append(standard_clause)
            shape.append(standard_clause)
        for key in ["size", "length", "grade", "finish"]:
            if key in p:
                term = {"term": {key: p[key]}}
                terms.append(term)
                if key in ["size", "length"]:
                    shape.append(term)
                should.append(
                    {
                        "constant_score": {
                            "filter": term,
                            "boost": {"size": 30, "length": 10, "grade": 3, "finish": 2}[key],
                        }
                    }
                )
        if terms:
            should.append({"constant_score": {"filter": {"bool": {"must": terms}}, "boost": 1000}})
        if shape:
            should.append({"constant_score": {"filter": {"bool": {"must": shape}}, "boost": 100}})
        if standards:
            should.append(
                {
                    "constant_score": {
                        "filter": {"terms": {"standard.keyword": standards}},
                        "boost": 50,
                    }
                }
            )
        if text:
            should.append(
                {
                    "multi_match": {
                        "query": p["text"],
                        "fields": ["name^2", "technical_code", "aliases"],
                        "fuzziness": "AUTO",
                    }
                }
            )
        query = (
            {"bool": {"should": should, "minimum_should_match": 1}} if text else {"match_all": {}}
        )
        try:
            hits = client().search(index="karma-products", query=query, size=60)["hits"]["hits"]
        except Exception as exc:
            # Keep outages explicit; do not silently change production search semantics.
            error = APIException("سرویس جستجو در دسترس نیست")
            error.status_code = 503
            raise error from exc
        products = qs.in_bulk([h["_id"] for h in hits])
        result = [products[int(h["_id"])] for h in hits if int(h["_id"]) in products]
        if result and terms:
            first = result[0]
            complete = all(
                getattr(first, k) == p[k] for k in ["size", "length", "grade", "finish"] if k in p
            ) and (not standards or first.standard.code in standards)
            if not complete:
                p["notice"] = (
                    "تطبیق کامل موجود نیست؛ نزدیک‌ترین مشخصات نمایش داده می‌شود. پیش از سفارش ابعاد، گرید و پوشش را بررسی کنید."
                )
        return result, p, "elasticsearch"
    if standards:
        qs = qs.filter(standard__code__in=standards)
    for key in ["size", "length", "grade", "finish"]:
        if key in p:
            qs = qs.filter(**{key: p[key]})
    if (
        text
        and not p["standards"]
        and not any(k in p for k in ["size", "length", "grade", "finish"])
    ):
        qs = qs.filter(name__icontains=p["text"])
    return list(qs.order_by("id")[:60]), p, "database-development"


def document(product):
    return {
        "standard": product.standard.code,
        "name": product.name,
        "system_code": product.system_code,
        "technical_code": product.technical_code,
        "aliases": list(product.aliases.values_list("code", flat=True)),
        **{key: getattr(product, key) for key in ["size", "length", "grade", "finish"]},
    }
