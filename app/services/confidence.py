from app.schemas.invoice_extraction import ConfidenceLevel, InvoiceExtraction

TOP_LEVEL_FIELDS = (
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "total_amount",
    "line_items",
)


def apply_heuristics(
    extraction: InvoiceExtraction,
) -> dict[str, ConfidenceLevel]:
    """Apply deterministic confidence overrides to Gemini's self-report."""
    scores = {
        field: extraction.confidence_scores.get(field, "low")
        for field in TOP_LEVEL_FIELDS
    }

    for field in TOP_LEVEL_FIELDS:
        if getattr(extraction, field) is None:
            scores[field] = "low"

    if extraction.line_items and extraction.total_amount is not None:
        line_items_total = sum(
            item.quantity * item.unit_price for item in extraction.line_items
        )
        tolerance = max(1.0, abs(extraction.total_amount) * 0.01)
        if abs(line_items_total - extraction.total_amount) > tolerance:
            scores["line_items"] = "low"
            scores["total_amount"] = "low"

    return scores
