# utils/project_applications_util.py

def process_project_applications_tool(response):
    """
    Processes the LangChain response for the 'project_applications' tool.
    Robust to optional sections being null and minor shape differences.
    """

    def _tool_calls(msg):
        try:
            return getattr(msg, "tool_calls", None) or []
        except Exception:
            return []

    def _safe_section(parent: dict, key: str):
        """Return a dict section or None if missing/None/not-a-dict."""
        if not isinstance(parent, dict):
            return None
        val = parent.get(key, None)
        return val if isinstance(val, dict) else None

    def _apps_list(section: dict):
        """Return a list from section['applications'] if present and a list, else None."""
        if not isinstance(section, dict):
            return None
        val = section.get("applications", None)
        return val if isinstance(val, list) else None

    # 1) Get tool args safely
    args = {}
    calls = _tool_calls(response)
    if calls:
        tc = calls[0]
        args = (tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}) or {})

    if not isinstance(args, dict):
        args = {}

    # 2) Payload may be under "applications" (expected) or already flattened
    payload = args.get("applications")
    if not isinstance(payload, dict):
        payload = args.get("project_applications")
        if not isinstance(payload, dict):
            payload = args  # last resort: treat args as the payload

    # 3) Extract each category safely (handle nulls without crashing)
    out = {
        "Bulk Energy Services": _apps_list(_safe_section(payload, "bulk_energy_services")),
        "Ancillary Services": _apps_list(_safe_section(payload, "ancillary_services")),
        "Transmission Infrastructure Services": _apps_list(_safe_section(payload, "transmission_infrastructure_services")),
        "Distribution Infrastructure Services": _apps_list(_safe_section(payload, "distribution_infrastructure_services")),
        "Customer Energy Management Services": _apps_list(_safe_section(payload, "customer_energy_management_services")),
        "Other Services": _apps_list(_safe_section(payload, "other_services")),
    }

    return out

