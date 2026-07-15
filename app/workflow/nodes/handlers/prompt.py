BILLING_CONSTRAINTS = (
    "Must not promise automatic refunds. Must not confirm plan changes without verification."
)
TECHNICAL_CONSTRAINTS = (
    "Must not claim an issue is fixed without confirmation. "
    "Must ask for reproduction steps if the customer has not provided any."
)
ACCOUNT_CONSTRAINTS = "Must never request passwords, OTPs, or authentication codes."
SUBSCRIPTION_CONSTRAINTS = (
    "Must not confirm cancellations or changes without quoting the relevant policy."
)
GENERAL_CONSTRAINTS = "Should be helpful and redirect to the appropriate FAQ where relevant."
