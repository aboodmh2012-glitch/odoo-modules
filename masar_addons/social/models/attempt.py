"""Durable outbound boundary, independent of the queue job transaction.

No foreign keys: a separate cursor must never wait for the job's locked rows.
Only identifiers and sanitized provider results are persisted, never bodies or
credentials. No public ACL/RPC access. Keep entries for delivery audit.
"""
import json

from odoo import fields, models, _
from odoo.exceptions import UserError
from .errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


class SocialAttempt(models.Model):
    _name = "social.attempt"
    _description = "Social Delivery Checkpoint"
    key = fields.Char(required=True)
    status = fields.Char(required=True)
    attempts = fields.Integer(default=0)
    result = fields.Text()
    _key_unique = models.Constraint("UNIQUE(key)", "Delivery checkpoint already exists.")


def deliver(record, callback):
    """At most one unknown-outcome request per job; known 429s may retry.

    Commit only our independent technical cursor, never the queue cursor.
    A crash leaves 'inflight', which is intentionally NOT resent. Successful
    responses survive rollback and can be replayed into Odoo without HTTP.
    """
    job_uuid = record.env.context.get("job_uuid")
    if not job_uuid:
        raise DeliveryPermanent()
    key = checkpoint_key(record)
    with record.env.registry.cursor() as cr:
        cr.execute("INSERT INTO social_attempt (key, status, attempts) VALUES (%s, 'ready', 0) ON CONFLICT (key) DO NOTHING", [key])
        cr.execute("SELECT status, attempts, result FROM social_attempt WHERE key=%s FOR UPDATE", [key])
        status, attempts, result = cr.fetchone()
        if status == "success":
            return json.loads(result)
        if status in ("inflight", "uncertain"):
            raise DeliveryUncertain()
        if status == "permanent" or attempts >= 5:
            raise DeliveryPermanent()
        cr.execute("UPDATE social_attempt SET status='inflight', attempts=attempts+1 WHERE key=%s", [key])
        cr.commit()
    try:
        result = callback()
        # Deliberately persist only these two fields from provider responses.
        result = {"id": str(result["id"]), "url": result.get("url", False)}
        status = "success"
    except DeliveryTemporary:
        status, result = ("permanent" if attempts >= 4 else "temporary"), None
    except DeliveryPermanent:
        status, result = "permanent", None
    except Exception:
        # Unknown exceptions may follow an accepted HTTP request. Do not log
        # their text (provider URLs can contain secrets), and never auto-retry.
        status, result = "uncertain", None
    with record.env.registry.cursor() as cr:
        cr.execute("UPDATE social_attempt SET status=%s, result=%s WHERE key=%s", [status, json.dumps(result), key])
        cr.commit()
    if status == "temporary":
        raise DeliveryTemporary(min(60 * 2 ** attempts, 1800))
    if status == "permanent":
        raise DeliveryPermanent()
    if status == "uncertain":
        raise DeliveryUncertain()
    return result


def checkpoint_key(record):
    # Stable across queue jobs, including explicit retries after a worker crash.
    return f"{record._name}:{record.id}"


def assert_unpublished(records):
    if not records:
        return
    with records.env.registry.cursor() as cr:
        cr.execute("SELECT 1 FROM social_attempt WHERE key IN %s AND status IN ('inflight', 'success', 'uncertain') LIMIT 1", [tuple(checkpoint_key(r) for r in records)])
        if cr.fetchone():
            raise UserError(_("A delivery may already exist on the platform. Inspect it before creating a replacement."))


def reset_rejected_checkpoint(record):
    # Only a known provider rejection may start a fresh explicit attempt.
    with record.env.registry.cursor() as cr:
        cr.execute("DELETE FROM social_attempt WHERE key=%s AND status IN ('permanent', 'temporary')", [checkpoint_key(record)])
        cr.commit()
