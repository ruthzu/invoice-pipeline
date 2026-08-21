from app.schemas.invoice_extraction import ConfidenceScores, InvoiceExtraction


def apply_heuristics(
    extraction: InvoiceExtraction,
) -> ConfidenceScores:
    """Apply deterministic confidence overrides to Gemini's self-report."""
    scores = extraction.confidence_scores.model_copy()

    for field in ConfidenceScores.model_fields:
        if getattr(extraction, field) is None:
            setattr(scores, field, "low")

    if extraction.line_items and extraction.total_amount is not None:
        line_items_total = sum(
            item.quantity * item.unit_price for item in extraction.line_items
        )
        tolerance = max(1.0, abs(extraction.total_amount) * 0.01)
        if abs(line_items_total - extraction.total_amount) > tolerance:
            scores.line_items = "low"
            scores.total_amount = "low"

    return scores
