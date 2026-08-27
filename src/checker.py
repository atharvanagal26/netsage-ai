import csv
import os
import re

def run_rule_checker(show_outputs: str) -> list:
    """
    Parses Cisco 'show' command outputs and network symptoms,
    returning deterministic rule check results for Member 4's UI.
    """
    results = []
    text_lower = show_outputs.lower()

    # 1. Check for Interface Shutdown or Port Security Tripping
    if "is administratively down" in text_lower or "err-disabled" in text_lower or "port security" in text_lower:
        results.append({
            "status": "FAIL",
            "check": "Interface / Port Security",
            "message": "Interface is down or tripped by Port Security (err-disabled)."
        })
    else:
        results.append({
            "status": "PASS",
            "check": "Interface Status",
            "message": "Interfaces are up and operational."
        })

    # 2. Check for APIPA / DHCP Lease Failure (169.254.x.x)
    if "169.254." in text_lower or "dhcp failed" in text_lower or "obtain an ip" in text_lower:
        results.append({
            "status": "FAIL",
            "check": "DHCP & APIPA Validation",
            "message": "APIPA address (169.254.x.x) or DHCP lease failure detected."
        })
    else:
        results.append({
            "status": "PASS",
            "check": "DHCP & APIPA Validation",
            "message": "No APIPA address issues detected."
        })

    # 3. Check for Subnet Mask Mismatch
    if "255.255.255.128" in text_lower or "bad mask" in text_lower or "wrong subnet mask" in text_lower:
        results.append({
            "status": "WARN",
            "check": "Subnet Mask Validation",
            "message": "Subnet mask mismatch detected (e.g., /25 scope vs /24 host configuration)."
        })

    # 4. Check for Default Gateway / Route Issues
    if "gateway of last resort is not set" in text_lower or "cannot reach default gateway" in text_lower:
        results.append({
            "status": "WARN",
            "check": "Default Gateway",
            "message": "Default gateway is missing, unconfigured, or unreachable."
        })

    # 5. Check for DNS Name Resolution Failures
    if "cannot resolve domain names" in text_lower or "dns server" in text_lower:
        results.append({
            "status": "WARN",
            "check": "DNS Resolution",
            "message": "Domain name resolution failing; check host DNS configuration."
        })

    # 6. Check for VLAN Trunking & Leaking Misconfigurations
    if "vlan" in text_lower or "trunk" in text_lower:
        if "leaking" in text_lower or "failing to pass" in text_lower or "untagged" in text_lower:
            results.append({
                "status": "FAIL",
                "check": "VLAN Trunking",
                "message": "VLAN trunking misconfiguration or native VLAN mismatch detected."
            })

    return results


def get_rule_stats(results: list) -> dict:
    """
    Returns summary counts of rule check results for Member 4's Streamlit charts.
    """
    return {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "warn": sum(1 for r in results if r["status"] == "WARN")
    }


# Local Test Execution
if __name__ == "__main__":
    csv_path = "cases.csv" if os.path.exists("cases.csv") else "data/cases.csv"

    if os.path.exists(csv_path):
        print("=== Running Rule Checker against cases.csv ===\n")
        with open(csv_path, mode="r") as f:
            reader = csv.DictReader(f)
            flagged_count = 0
            total_cases = 0

            for row in reader:
                total_cases += 1
                case_id = row.get("case_id", f"CASE_{total_cases}")
                test_input = f"{row.get('symptom', '')} {row.get('topology_note', '')}"
                
                checks = run_rule_checker(test_input)
                flags = [c for c in checks if c["status"] in ["FAIL", "WARN"]]

                if flags:
                    flagged_count += 1
                    print(f"[{case_id}] Flagged {len(flags)} issue(s):")
                    for flag in flags:
                        print(f"  - [{flag['status']}] {flag['check']}: {flag['message']}")
                else:
                    print(f"[{case_id}] All checks PASSED.")

        print(f"\nSummary: Flagged deterministic issues in {flagged_count}/{total_cases} cases.")
    else:
        print("Error: cases.csv not found! Run 'git pull origin main' first.")