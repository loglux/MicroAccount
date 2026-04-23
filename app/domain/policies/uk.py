from decimal import Decimal

DIRECTOR_PAID_METHOD = "director_personal_card"
DIRECTOR_LOAN_EXPENSE_TYPE = "director_loan_funded_expense"
DLA_LOAN_TO_COMPANY = "loan_to_company"
DLA_REPAYMENT_TO_DIRECTOR = "repayment_to_director"
GBP = "GBP"
DEFAULT_CATEGORIES = [
    "software_subscriptions",
    "hosting_and_infrastructure",
    "domains_and_dns",
    "registered_address",
    "formation_and_incorporation",
    "mixed_use_home_costs",
    "equipment_and_hardware",
    "office_supplies",
    "professional_fees",
    "bank_and_payment_fees",
    "marketing_and_branding",
    "travel",
    "training_and_books",
    "communications",
    "other",
]


def build_expense_loan_reference(expense_id: int, description: str) -> str:
    short_description = description.strip()[:180]
    return f"Expense #{expense_id}: {short_description}"


def director_loan_balance(total_loaned: Decimal, total_repaid: Decimal) -> Decimal:
    return total_loaned - total_repaid


DEFAULT_ACCOUNT_MAPPINGS = {
    "software_subscriptions": ("5010", "Software subscriptions"),
    "hosting_and_infrastructure": ("5020", "Hosting and infrastructure"),
    "domains_and_dns": ("5030", "Domains and DNS"),
    "registered_address": ("5040", "Registered address and company admin"),
    "formation_and_incorporation": ("5200", "Formation and incorporation costs"),
    "mixed_use_home_costs": ("5300", "Mixed-use home costs pending review"),
    "equipment_and_hardware": ("5070", "Equipment and hardware"),
    "office_supplies": ("5000", "Administrative expenses"),
    "professional_fees": ("5050", "Professional fees"),
    "bank_and_payment_fees": ("5000", "Administrative expenses"),
    "marketing_and_branding": ("5080", "Marketing and branding"),
    "travel": ("5090", "Travel"),
    "training_and_books": ("5000", "Administrative expenses"),
    "communications": ("5060", "Telephone and internet"),
    "other": ("5999", "Other expenses"),
}
