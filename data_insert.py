#!/usr/bin/env python3
import os, json, math, time, argparse
from typing import Any, Dict, List, Tuple, Iterable, Optional
import requests
from tqdm import tqdm

# ========== CONFIG: use ENV VARS for secrets (do NOT hardcode) ==========
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "")
GOOGLE_CSE_ENGINE_ID = os.getenv("GOOGLE_CSE_ENGINE_ID", "")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")

# Optional corporate proxy support
HTTP_PROXY  = os.getenv("HTTP_PROXY", "")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", HTTP_PROXY)
PROXIES = {"http": HTTP_PROXY, "https": HTTPS_PROXY} if (HTTP_PROXY or HTTPS_PROXY) else None

# ========== FIELD RULES ==========
# Add rules to improve search queries + summaries by field.
# key = JSON "field path" (dot notation inside objects; array indices use [i] but you can use wildcards here)
FIELD_RULES: Dict[str, Dict[str, Any]] = {
    "Latitude":  {"type": "float", "desc": "Geographic coordinate latitude in decimal degrees."},
    "Longitude": {"type": "float", "desc": "Geographic coordinate longitude in decimal degrees."},
    "County":    {"type": "string", "desc": "County or shire of project site."},
    "State/Province/Territory": {"type": "string", "desc": "State, province, or territory of the site."},
    "ISO/RTO":   {"type": "string", "desc": "Electricity market ISO/RTO serving the interconnection."},
    "Commissioned Date": {"type": "date", "desc": "First commercial operation date (YYYY-MM-DD or YYYY)."},
    "Announced Date":    {"type": "date", "desc": "Initial public announcement date (YYYY-MM-DD or YYYY)."},
    "Constructed Date":  {"type": "date", "desc": "Construction start or substantial completion date."},
    "Paired Grid Resources": {"type": "string", "desc": "Primary paired resource (e.g., Solar, Wind, Hydro)."},
    # Example nested rule:
    "Subsystems[].Storage Device.Round-trip Efficiency": {
        "type": "percent", "desc": "Battery round-trip efficiency (%)"
    },
    "Subsystems[].Power Conversion System.Nominal AC Voltage": {
        "type": "string", "desc": "PCS nominal AC voltage (kV or V, specify units)."
    },
    # Applications buckets (if empty list -> missing)
    "Applications.Bulk Energy Services (General Energy Applications)": {"type": "list", "desc": "Bulk energy services provided."},
    "Applications.Ancillary Services": {"type": "list", "desc": "Ancillary services provided."},
    "Applications.Transmission Infrastructure Services": {"type": "list", "desc": "Transmission services provided."},
    "Applications.Distribution Infrastructure Services": {"type": "list", "desc": "Distribution services provided."},
    "Applications.Customer Energy Management Services (End-User Services)": {"type": "list", "desc": "End-user energy management services."},
    "Applications.Others": {"type": "list", "desc": "Other services provided."},
}

# Which values count as "missing"? You can tune this per type if needed.
def is_missing(val: Any) -> bool:
    if val is None: return True
    if val == "":   return True
    if isinstance(val, float) and (math.isnan(val) if not math.isfinite(val) else False):
        return True
    # Empty list/dict considered missing
    if isinstance(val, (list, dict)) and len(val) == 0:
        return True
    # Zero can be treated as missing for selected numeric fields — keep it configurable:
    # Returning False by default (safer). Toggle via --treat_zero_as_missing.
    return False

# For optional CLI override
def is_missing_with_zero(val: Any) -> bool:
    if is_missing(val): return True
    if isinstance(val, (int, float)) and val == 0:
        return True
    return False

# Utilities to walk JSON and yield (path, value, parent, key_in_parent)
def walk(obj: Any, base_path: str = "") -> Iterable[Tuple[str, Any, Any, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{base_path}.{k}" if base_path else k
            yield (p, v, obj, k)
            yield from walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{base_path}[{i}]"
            yield (p, v, obj, i)
            yield from walk(v, p)

# Match a concrete path like "Subsystems[0].Power Conversion System.Nominal AC Voltage"
# to a wildcard rule path like "Subsystems[].Power Conversion System.Nominal AC Voltage"
def rule_for_path(path: str) -> Optional[Dict[str, Any]]:
    candidates = []
    for rule_path, rule in FIELD_RULES.items():
        rp_parts = rule_path.replace("[]", "[*]").split(".")
        p_parts  = path.split(".")
        ok = True
        for rp, pp in zip(rp_parts, p_parts):
            if "[*]" in rp:
                # allow any [index]
                rp_clean = rp.replace("[*]", "")
                pp_clean = pp.split("[")[0]
                if rp_clean != pp_clean:
                    ok = False; break
            else:
                if rp != pp:
                    ok = False; break
        if ok and len(rp_parts) == len(p_parts):
            candidates.append((rule_path, rule))
    if not candidates:
        return None
    # Most specific wins -> longer rule path
    candidates.sort(key=lambda x: len(x[0]), reverse=True)
    return candidates[0][1]

# Extract helpful context fields to build better queries
def extract_context(record: Dict[str, Any]) -> Dict[str, str]:
    ctx = {}
    ctx["site_name"] = record.get("Project/Plant Name") or record.get("Site Name") or record.get("Project Name") or ""
    ctx["country"]   = record.get("Country", "") or ""
    ctx["state"]     = record.get("State/Province/Territory", "") or ""
    ctx["city"]      = record.get("City", "") or ""
    return ctx

# Build a Google CSE query string
def make_query(ctx: Dict[str, str], field_name: str, rule: Optional[Dict[str, Any]] = None) -> str:
    bits = []
    if ctx.get("site_name"): bits.append(ctx["site_name"])
    # Add type qualifiers:
    bits.append("battery energy storage" if "Storage" in field_name or "battery" in (rule or {}).get("desc","").lower() else "energy storage project")
    # Location for precision
    loc = ", ".join([x for x in [ctx.get("city"), ctx.get("state"), ctx.get("country")] if x])
    if loc: bits.append(loc)
    # Field name & descriptor
    bits.append(field_name)
    if rule and rule.get("desc"):
        bits.append(rule["desc"])
    return " ".join(bits)

# Google CSE
def google_cse_search(query: str, max_results: int = 5, sleep_s: float = 0.0) -> Tuple[List[str], List[str]]:
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ENGINE_ID:
        return [], []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_CSE_API_KEY, "cx": GOOGLE_CSE_ENGINE_ID, "q": query, "num": max_results}
    resp = requests.get(url, params=params, proxies=PROXIES, timeout=30)
    if resp.status_code != 200:
        return [], []
    js = resp.json()
    items = js.get("items", []) or []
    snippets = [it.get("snippet", "") for it in items]
    urls     = [it.get("link", "")    for it in items]
    if sleep_s > 0: time.sleep(sleep_s)
    return snippets, urls

# OpenAI: keep the model constrained to evidence only
def summarize_value(field_path: str, field_rule: Optional[Dict[str,Any]], ctx: Dict[str,str], snippets: List[str]) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return {"value": "Unknown", "confidence": 0.0, "rationale": "Missing OPENAI_API_KEY"}

    # Build prompt
    field_name = field_path.split(".")[-1]
    type_hint  = field_rule.get("type") if field_rule else None
    desc       = field_rule.get("desc") if field_rule else ""
    sys = (
        "You are a careful fact-extraction assistant. "
        "Use ONLY the provided web snippets. If there is insufficient evidence, return Unknown."
    )
    user = f"""Task: Extract the value for the field "{field_name}" (path: "{field_path}").
Project: {ctx.get("site_name","Unknown")}
Location: {ctx.get("city","")}, {ctx.get("state","")}, {ctx.get("country","")}

Field type: {type_hint or "string"}
Description: {desc or "(none)"}

Web snippets (may contain duplicates/irrelevant info):
"""
    for s in snippets:
        user += f"- {s}\n"
    user += """
Rules:
- Rely only on the snippets above; do not guess.
- If not clearly stated, return "Unknown".
- If numeric, provide units if available.
- If list-like, return a comma-separated list.
- Prefer the most recent/reliable sounding snippet if multiple conflict.

Respond strictly as JSON with keys: value, confidence (0-1), rationale (short).
"""

    # Minimal client without importing the new SDKs; use HTTP directly to avoid version drift
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",  # light, cheap, good for extraction; change if you prefer
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
    }
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, proxies=PROXIES, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        # Best-effort parse
        import json as _json
        return _json.loads(text)
    except Exception as e:
        return {"value": "Unknown", "confidence": 0.0, "rationale": f"Error: {e}"}

def process_record(record: Dict[str, Any], treat_zero_as_missing: bool = False, max_results: int = 5, sleep_s: float = 0.0) -> Dict[str, Any]:
    missing_check = is_missing_with_zero if treat_zero_as_missing else is_missing
    ctx = extract_context(record)
    suggestions: Dict[str, Dict[str, Any]] = {}

    for path, val, _parent, _key in walk(record):
        # Only leaf values (not dict/list containers) OR empty lists/dicts
        is_container = isinstance(val, (dict, list))
        consider = (not is_container) or (is_container and missing_check(val))
        if not consider:
            continue

        if not missing_check(val):
            continue

        rule = rule_for_path(path)
        # If no rule: still try (generic)
        field_name = path.split(".")[-1].split("[")[0]
        query = make_query(ctx, field_name, rule)
        snippets, urls = google_cse_search(query, max_results=max_results, sleep_s=sleep_s)

        if not snippets:
            suggestions[path] = {
                "value": "Unknown",
                "confidence": 0.0,
                "rationale": "No search results",
                "references": []
            }
            continue

        summary = summarize_value(path, rule or {}, ctx, snippets)
        suggestions[path] = {
            "value": summary.get("value", "Unknown"),
            "confidence": summary.get("confidence", 0.0),
            "rationale": summary.get("rationale", ""),
            "references": urls
        }

    return suggestions

def main():
    ap = argparse.ArgumentParser(description="Auto-fill suggestions for missing fields in JSON records via web search + extraction.")
    ap.add_argument("input_json", help="Path to JSON file (array of objects).")
    ap.add_argument("--output", help="Output JSON for suggestions", default=None)
    ap.add_argument("--treat-zero-as-missing", action="store_true", help="Also treat numeric 0 as missing.")
    ap.add_argument("--max-results", type=int, default=5, help="Max Google CSE results per query.")
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between Google queries.")
    args = ap.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of objects (records).")

    all_suggestions: List[Dict[str, Any]] = []

    for rec in tqdm(data, desc="Records"):
        sugg = process_record(
            rec,
            treat_zero_as_missing=args.treat_zero_as_missing,
            max_results=args.max_results,
            sleep_s=args.sleep
        )
        all_suggestions.append({"Project/Plant Name": rec.get("Project/Plant Name"), "suggestions": sugg})

    out_path = args.output or (os.path.splitext(args.input_json)[0] + "_autofill.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_suggestions, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote suggestions to: {out_path}")
    print("Note: This file does not modify your source data. You can review/merge suggestions as needed.")

if __name__ == "__main__":
    main()
