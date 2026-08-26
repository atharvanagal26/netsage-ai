import re

def run_rule_checker(show_outputs: str) -> list:
    """
    Parses Cisco 'show' command outputs and returns rule check results.
    """
    results = []
    
    # 1. Check for Down Interfaces
    down_interfaces = re.findall(r'(\n?\S+\d+/\d+|\S+\d+)\s+is\s+(administratively down|down)', show_outputs)
    if down_interfaces:
        interfaces_str = ", ".join([iface[0].strip() for iface in down_interfaces])
        results.append({
            "status": "FAIL",
            "check": "Interface Status Check",
            "message": f"Interface(s) down: {interfaces_str}"
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Interface Status Check",
            "message": "All listed interfaces are UP."
        })

    # 2. Check Default Route / Gateway
    if "show ip route" in show_outputs.lower():
        if "gateway of last resort is not set" in show_outputs.lower():
            results.append({
                "status": "WARN",
                "check": "Default Route Check",
                "message": "Gateway of last resort is NOT set."
            })
        else:
            results.append({
                "status": "PASS",
                "check": "Default Route Check",
                "message": "Default route / Gateway is present."
            })

    return results