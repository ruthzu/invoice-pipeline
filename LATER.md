# Deferred improvements

- Enqueue failures are currently log-and-continue; invoice stays PENDING with no automatic recovery. If reliable processing becomes mandatory, revisit with an outbox/reconciliation pattern instead of trusting the enqueue call.
- reviewed_by is a hardcoded placeholder; no real auth/user system exists yet. Needed before this is usable by more than one person.
- /metrics and /health are unauthenticated, consistent with the existing no-auth-system gap. If this is ever exposed publicly, both need to be gated.
