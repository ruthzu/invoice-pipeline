from typing import Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["high", "medium", "low"]


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float


class InvoiceExtraction(BaseModel):
    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    total_amount: float | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    confidence_scores: dict[str, ConfidenceLevel] = Field(
        default_factory=dict,
        description=(
            "Self-reported confidence for each top-level field "
            "(vendor_name, invoice_number, invoice_date, total_amount, "
            "line_items). For each field, report high, medium, or low based "
            "on how certain you are that the extracted value is correct and "
            "present in the document."
        ),
    )
