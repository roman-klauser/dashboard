#!/usr/bin/env python3
"""
csv_to_json.py — Wandelt den Broker-CSV-Export in ein JSON für das Dashboard.

Verwendung:
    python csv_to_json.py transactions.csv
    python csv_to_json.py transactions.csv data/latest.json
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_number(s):
    """'1,159.03' -> 1159.03 ; leer -> None"""
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_timestamp(s):
    """'2026-10-02 15:21:54.303843 +00:00' -> ISO 8601 in UTC"""
    if not s:
        return None
    s = str(s).strip()
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def convert(input_path, output_path):
    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    transactions = []
    skipped = 0

    for r in rows:
        ts = parse_timestamp(r.get("Modified (UTC)", ""))
        balance = parse_number(r.get("Balance", ""))
        if ts is None or balance is None:
            skipped += 1
            continue

        transactions.append({
            "id":        (r.get("Id", "") or "").strip(),
            "timestamp": ts,
            "balance":   balance,
            "amount":    parse_number(r.get("Amount", "")) or 0.0,
            "currency":  (r.get("Currency", "") or "USD").strip() or "USD",
            "type":      (r.get("Type", "") or "").strip(),
            "symbol":    (r.get("Instrument Symbol", "") or "").strip(),
            "name":      (r.get("Instrument Name", "") or "").strip(),
            "status":    (r.get("Status", "") or "").strip(),
            "tradeId":   (r.get("Trade Id", "") or "").strip(),
        })

    # chronologisch aufsteigend
    transactions.sort(key=lambda t: t["timestamp"])

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "currency": transactions[0]["currency"] if transactions else "USD",
        "count": len(transactions),
        "transactions": transactions,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    msg = f"{len(transactions)} Transaktionen → {output_path}"
    if skipped:
        msg += f" ({skipped} Zeilen übersprungen)"
    print(msg)


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Verwendung: python csv_to_json.py <input.csv> [output.json]")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) == 3 else "data/latest.json"
    convert(input_path, output_path)