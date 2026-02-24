BANNED_PRODUCTS = [
    'pesticide_xyz',
    'banned_chemical_123',
]

def is_product_banned(product_name: str) -> bool:
    return product_name.lower() in [p.lower() for p in BANNED_PRODUCTS]

def filter_banned_from_advisory(advisory_text: str) -> str:
    for banned in BANNED_PRODUCTS:
        if banned.lower() in advisory_text.lower():
            advisory_text = advisory_text.replace(banned, '[REMOVED]')
    return advisory_text