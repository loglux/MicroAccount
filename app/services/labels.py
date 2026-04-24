from __future__ import annotations

CATEGORY_LABELS: dict[str, str] = {
    "software_subscriptions": "Software subscriptions",
    "hosting_and_infrastructure": "Hosting and infrastructure",
    "domains_and_dns": "Domains and DNS",
    "registered_address": "Registered address",
    "formation_and_incorporation": "Formation and incorporation",
    "mixed_use_home_costs": "Mixed-use home costs",
    "equipment_and_hardware": "Equipment and hardware",
    "office_supplies": "Office supplies",
    "professional_fees": "Professional fees",
    "bank_and_payment_fees": "Bank and payment fees",
    "marketing_and_branding": "Marketing and branding",
    "travel": "Travel",
    "training_and_books": "Training and books",
    "communications": "Communications",
    "other": "Other",
}

DOCUMENT_ROLE_LABELS: dict[str, str] = {
    "primary_document": "Primary",
    "supporting_document": "Supporting",
}

PROCESSING_STATUS_LABELS: dict[str, str] = {
    "queued": "Queued",
    "pending": "Pending",
    "completed": "Processed",
    "converted": "Converted",
    "skipped": "Skipped",
    "empty": "No text",
}

COST_TREATMENT_LABELS: dict[str, str] = {
    "revenue": "Revenue",
    "formation_or_capital": "Formation or capital",
}

USE_TYPE_LABELS: dict[str, str] = {
    "business_only": "Business only",
    "mixed_use": "Mixed use",
}

DLA_DIRECTION_LABELS: dict[str, str] = {
    "loan_to_company": "Loan to company",
    "repayment_to_director": "Repayment to director",
}

LABEL_KINDS: dict[str, dict[str, str]] = {
    "category": CATEGORY_LABELS,
    "document_role": DOCUMENT_ROLE_LABELS,
    "processing_status": PROCESSING_STATUS_LABELS,
    "cost_treatment": COST_TREATMENT_LABELS,
    "use_type": USE_TYPE_LABELS,
    "dla_direction": DLA_DIRECTION_LABELS,
}


def humanize(code: str | None, kind: str | None = None) -> str:
    if not code:
        return ""
    if kind and kind in LABEL_KINDS and code in LABEL_KINDS[kind]:
        return LABEL_KINDS[kind][code]
    for mapping in LABEL_KINDS.values():
        if code in mapping:
            return mapping[code]
    words = code.replace("_", " ").strip()
    if not words:
        return ""
    return words[0].upper() + words[1:]
