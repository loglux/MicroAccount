from __future__ import annotations

import re

from app.documents.schemas import DocumentExtractionResult


def build_document_description(
    *,
    document_type: str | None,
    supplier_name: str | None,
    reference_number: str | None,
    extracted_text: str | None,
    fallback_filename: str | None = None,
) -> str:
    supplier = (supplier_name or "").strip()
    reference = (reference_number or "").strip()
    text = (extracted_text or "").replace("\x00", "-")

    ionos_contract = re.search(r"Contract:\s*\d+\s*-\s*(.+)", text, re.I)
    if supplier == "IONOS" and ionos_contract:
        service_name = ionos_contract.group(1).splitlines()[0].strip()
        return f"{service_name} invoice {reference}".strip()

    if supplier and document_type and reference:
        return f"{supplier} {document_type} {reference}"
    if supplier and reference:
        return f"{supplier} document {reference}"
    if supplier and document_type:
        return f"{supplier} {document_type}"
    if document_type and reference:
        return f"{document_type} {reference}"
    if fallback_filename:
        return fallback_filename
    return "document"


def build_extracted_text_preview(extracted_text: str | None, limit: int = 400) -> str:
    if not extracted_text:
        return ""
    normalized = " ".join(extracted_text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def parse_extracted_text(result: DocumentExtractionResult) -> DocumentExtractionResult:
    text = (result.extracted_text or "").replace("\x00", "-")
    lowered = text.lower()

    document_type = result.document_type
    if "receipt" in lowered:
        document_type = "receipt"
    elif "invoice" in lowered:
        document_type = "invoice"

    supplier_guess = result.supplier_guess
    for candidate in ("IONOS", "IONOS Cloud Ltd.", "Anthropic", "Claude", "Stripe"):
        if candidate.lower() in lowered:
            supplier_guess = "IONOS" if "ionos" in candidate.lower() else candidate
            break

    amount_patterns = [
        r"total amount due[^\d£$€]{0,40}([£$€]\s?\d[\d,]*\.\d{2})",
        r"charges[^\d£$€]{0,20}([£$€]\s?\d[\d,]*\.\d{2})",
        r"amount\s+(?:due|paid)[^\d£$€]{0,20}([£$€]\s?\d[\d,]*\.\d{2})",
        r"([£$€]\s?\d[\d,]*\.\d{2})\s+(?:paid on|due)\b",
        r"(?<!excluding\s)total[^\d£$€]{0,20}([£$€]\s?\d[\d,]*\.\d{2})",
    ]
    amount_value = None
    for pattern in amount_patterns:
        amount_matches = re.findall(pattern, text, re.I)
        if amount_matches:
            amount_value = amount_matches[-1]
            break
    if not amount_value:
        all_amounts = re.findall(r"([£$€]\s?\d[\d,]*\.\d{2})", text)
        amount_value = all_amounts[-1] if all_amounts else None
    total_amount_guess = (
        amount_value.replace(" ", "") if amount_value else result.total_amount_guess
    )

    currency_guess = result.currency_guess
    if "£" in text or "gbp" in lowered:
        currency_guess = "GBP"
    elif "$" in text or "usd" in lowered:
        currency_guess = "USD"
    elif "€" in text or "eur" in lowered:
        currency_guess = "EUR"

    invoice_number_guess = result.invoice_number_guess
    if document_type == "receipt":
        number_match = re.search(r"receipt number\s+([A-Z0-9-]{4,})", text, re.I)
    else:
        number_match = re.search(r"invoice number\s+([A-Z0-9-]{4,})", text, re.I)
    if not number_match:
        number_match = re.search(
            r"(?:invoice|receipt)(?:\s+number|\s+#|#| no\.?| id)?[^\w]{0,5}([A-Z0-9-]{4,})",
            text,
            re.I,
        )
    if number_match:
        candidate = number_match.group(1).strip("-")
        if candidate.lower() not in {"invoice", "receipt", "number"}:
            invoice_number_guess = candidate

    invoice_date_guess = result.invoice_date_guess
    date_match = re.search(
        r"(?:date of issue|date due|date paid|paid on)?\s*"
        r"(\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2,9}\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
        text,
        re.I,
    )
    if date_match:
        invoice_date_guess = date_match.group(1)

    if not supplier_guess:
        ionos_match = re.search(r"\b(IONOS(?:\s+Cloud\s+Ltd\.)?)\b", text, re.I)
        if ionos_match:
            supplier_guess = "IONOS"

    confidence_score = "0.35"
    filled = sum(
        bool(value)
        for value in (
            document_type,
            supplier_guess,
            invoice_number_guess,
            invoice_date_guess,
            total_amount_guess,
            currency_guess,
        )
    )
    if filled >= 5:
        confidence_score = "0.85"
    elif filled >= 3:
        confidence_score = "0.65"
    elif filled >= 1:
        confidence_score = "0.45"

    result.document_type = document_type
    result.supplier_guess = supplier_guess
    result.invoice_number_guess = invoice_number_guess
    result.invoice_date_guess = invoice_date_guess
    result.total_amount_guess = total_amount_guess
    result.currency_guess = currency_guess
    result.confidence_score = confidence_score
    return result
