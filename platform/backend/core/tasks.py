import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import connection, transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from .models import OutboxEvent

log = logging.getLogger(__name__)


def deliver(event):
    if event.topic in ["ProductCreated", "ProductUpdated"]:
        if not settings.ELASTICSEARCH_URL:
            return False
        from catalog.models import Product
        from search.services import client, document

        product = Product.objects.select_related("standard").get(pk=event.payload["id"])
        client().index(index="karma-products", id=product.pk, document=document(product))
    elif event.topic == "InvoiceIssued":
        from accounting.services import post_invoice_event

        post_invoice_event(event.payload["id"])
    else:
        return False
    return True


@shared_task
def dispatch_outbox():
    pending = OutboxEvent.objects.filter(delivered_at=None).filter(
        Q(retry_at=None) | Q(retry_at__lte=timezone.now())
    )
    pending = pending.annotate(
        priority=Case(
            When(topic="InvoiceIssued", then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by("priority", "pk")
    ids = list(pending.values_list("pk", flat=True)[:100])
    delivered = 0
    for event_id in ids:
        try:
            with transaction.atomic():
                event = (
                    OutboxEvent.objects.select_for_update(
                        skip_locked=connection.features.has_select_for_update_skip_locked
                    )
                    .filter(pk=event_id, delivered_at=None)
                    .first()
                )
                if not event:
                    continue
                if not deliver(event):
                    continue
                event.delivered_at = timezone.now()
                event.last_error = ""
                event.save(update_fields=["delivered_at", "last_error"])
                delivered += 1
        except Exception as exc:
            # Rollback first, then retain diagnostic metadata without customer data or credentials.
            event = OutboxEvent.objects.get(pk=event_id)
            event.attempts += 1
            event.last_error = type(exc).__name__
            event.retry_at = timezone.now() + timedelta(
                seconds=min(3600, 5 * 2 ** min(event.attempts, 9))
            )
            event.save(update_fields=["attempts", "last_error", "retry_at"])
            log.error(
                "outbox_delivery_failed event_id=%s error_type=%s", event_id, type(exc).__name__
            )
    return delivered
