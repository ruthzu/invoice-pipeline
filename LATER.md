# Deferred improvements

- Enqueue failures are currently log-and-continue; invoice stays PENDING with no automatic recovery. If reliable processing becomes mandatory, revisit with an outbox/reconciliation pattern instead of trusting the enqueue call.
