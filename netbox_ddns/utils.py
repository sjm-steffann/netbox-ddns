def normalize_fqdn(dns_name: str) -> str:
    if not dns_name:
        return ''

    return dns_name.lower().rstrip('.') + '.'
