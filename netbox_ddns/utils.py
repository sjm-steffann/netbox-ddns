import dns.rdatatype
import dns.resolver


def normalize_fqdn(dns_name: str) -> str:
    if not dns_name:
        return ''

    return dns_name.lower().rstrip('.') + '.'


def get_soa(dns_name: str) -> str:
    parts = dns_name.rstrip('.').split('.')
    for i in range(len(parts)):
        zone_name = normalize_fqdn('.'.join(parts[i:]))

        try:
            dns.resolver.query(zone_name, dns.rdatatype.SOA)
            return zone_name
        except dns.resolver.NoAnswer:
            # The name exists, but has no SOA. Continue one level further up
            continue
        except dns.resolver.NXDOMAIN as e:
            # Look for a SOA record in the authority section
            for query, response in e.responses().items():
                for rrset in response.authority:
                    if rrset.rdtype == dns.rdatatype.SOA:
                        return rrset.name.to_text()
