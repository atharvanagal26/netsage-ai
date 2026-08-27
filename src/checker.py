import csv
import os
import re

def run_rule_checker(show_outputs: str) -> list:
    """
    Parses Cisco 'show' command outputs and returns rule check results.
    """
    results = []
    text_lower = show_outputs.lower()

    # 1. Check for Interface Down / Port Security shutdown
    if "is administratively down" in text_lower or "err-disabled" in text_lower:
        results.append({
            "status": "FAIL",
            "check": "Interface / Port Security",
            "message": "Interface is down or tripped by Port Security (err-disabled)."
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Interface Status",
            "message": "Interfaces UP."
        })

    # 2. Check for APIPA / DHCP Failure (169.254.x.x)
    if "169.254." in text_lower or "dhcp failed" in text_lower:
        results.append({
            "status": "FAIL",
            "check": "DHCP Assignment",
            "message": "APIPA address detected (169.254.x.x). Device failed to obtain DHCP lease."
        })

    # 3. Check for Subnet Mask Mismatch
    if "255.255.255.128" in text_lower or "bad mask" in text_lower:
        results.append({
            "status": "WARN",
            "check": "Subnet Mask Validation",
            "message": "Subnet mask mismatch detected (e.g., /25 vs /24 scope)."
        })

    # 4. Check Default Gateway / Route
    if "gateway of last resort is not set" in text_lower:
        results.append({
            "status": "WARN",
            "check": "Default Gateway",
            "message": "Default gateway is missing or not set."
        })

    return results


# Local Testing Block
if __name__ == "__main__":
    csv_path = "cases.csv" if os.path.exists("cases.csv") else "data/cases.csv"
    
    if os.path.exists(csv_path):
        with open(csv_path, mode="r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                test_input = f"{row.get('symptom', '')} {row.get('topology_note', '')}"
                checks = run_rule_checker(test_input)
                print(f"[{row.get('case_id')}] Checked -> {len(checks)} rules evaluated.")
    else:
        print("Run 'git pull origin main' first to get cases.csv!")