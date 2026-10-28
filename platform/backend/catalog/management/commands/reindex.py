import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
from django.utils import timezone
from elasticsearch.helpers import bulk

from catalog.models import Product
from core.models import OutboxEvent
from search.services import client, document


class Command(BaseCommand):
    help = "Build a fresh index and atomically swap the search alias"

    def handle(self, *args, **kwargs):
        if not settings.ELASTICSEARCH_URL:
            raise CommandError("Set ELASTICSEARCH_URL")
        ceiling = OutboxEvent.objects.aggregate(n=Max("pk"))["n"] or 0
        es = client()
        name = "karma-products-" + str(time.time_ns())
        fields = {key: {"type": "keyword"} for key in ["size", "length", "grade", "finish"]}
        for key in ["standard", "name", "technical_code", "system_code", "aliases"]:
            fields[key] = {
                "type": "text",
                "analyzer": "karma_fa",
                "fields": {"keyword": {"type": "keyword"}},
            }
        es.indices.create(
            index=name,
            settings={
                "analysis": {
                    "analyzer": {
                        "karma_fa": {
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "decimal_digit",
                                "arabic_normalization",
                                "persian_normalization",
                            ],
                        }
                    }
                }
            },
            mappings={"properties": fields},
        )
        bulk(
            es,
            (
                {"_index": name, "_id": p.pk, "_source": document(p)}
                for p in Product.objects.select_related("standard")
                .prefetch_related("aliases")
                .iterator(chunk_size=500)
            ),
        )
        es.indices.refresh(index=name)
        old = (
            es.indices.get_alias(name="karma-products")
            if es.indices.exists_alias(name="karma-products")
            else {}
        )
        actions = [{"remove": {"index": index, "alias": "karma-products"}} for index in old]
        actions.append({"add": {"index": name, "alias": "karma-products"}})
        es.indices.update_aliases(actions=actions)
        OutboxEvent.objects.filter(
            pk__lte=ceiling, topic__in=["ProductCreated", "ProductUpdated"], delivered_at=None
        ).update(delivered_at=timezone.now())
        self.stdout.write(name)
