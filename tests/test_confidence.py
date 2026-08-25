from app.schemas.invoice_extraction import (
    ConfidenceScores,
    InvoiceExtraction,
    LineItem,
)
from app.services.confidence import apply_heuristics


def _extraction(**overrides) -> InvoiceExtraction:
    values = {
        "vendor_name": "Acme Corp",
        "invoice_number": "INV-001",
        "invoice_date": "2026-01-15",
        "total_amount": 150.0,
        "line_items": [LineItem(description="Widget", quantity=2.0, unit_price=75.0)],
        "confidence_scores": ConfidenceScores(
            vendor_name="high",
            invoice_number="high",
            invoice_date="medium",
            total_amount="high",
            line_items="medium",
        ),
    }
    values.update(overrides)
    return InvoiceExtraction(**values)


def test_confidence_scores_have_fixed_schema():
    schema = InvoiceExtraction.model_json_schema()

    confidence_schema = schema["$defs"]["ConfidenceScores"]
    assert "additionalProperties" not in confidence_schema
    assert set(confidence_schema["properties"]) == {
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "total_amount",
        "line_items",
    }


def test_missing_values_are_low_confidence():
    extraction = _extraction(invoice_number=None, total_amount=None)

    scores = apply_heuristics(extraction)

    assert scores.invoice_number == "low"
    assert scores.total_amount == "low"
    assert scores.vendor_name == "high"


def test_mismatched_line_items_downgrade_totals():
    extraction = _extraction(total_amount=100.0)

    scores = apply_heuristics(extraction)

    assert scores.total_amount == "low"
    assert scores.line_items == "low"


def test_matching_line_items_preserve_self_reported_confidence():
    extraction = _extraction()

    scores = apply_heuristics(extraction)

    assert scores.total_amount == "high"
    assert scores.line_items == "medium"


def test_small_total_difference_is_within_tolerance():
    extraction = _extraction(total_amount=150.5)

    scores = apply_heuristics(extraction)

    assert scores.total_amount == "high"
    assert scores.line_items == "medium"
