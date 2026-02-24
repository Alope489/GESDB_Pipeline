# utils/subsystem_util.py

def process_subsystem_info_tool(response):
    """
    Processes the LangChain response for the 'subsystem_info' tool,
    extracting the number of subsystems and their names if available.
    Robust to None/missing sections.
    """

    def _tool_calls(msg):
        try:
            return getattr(msg, "tool_calls", None) or []
        except Exception:
            return []

    def _as_dict(x):
        if isinstance(x, dict):
            return x
        to_dict = getattr(x, "dict", None)
        if callable(to_dict):
            try:
                return to_dict()
            except Exception:
                return {}
        return {}

    args = {}
    calls = _tool_calls(response)
    if calls:
        tc = calls[0]
        args = (tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}) or {})
    if not isinstance(args, dict):
        args = {}

    payload = args.get("subsystem_info")
    if not isinstance(payload, dict):
        # sometimes the args are already flat; fall back if keys are present
        if "number_of_subsystems" in args or "subsystem_names" in args:
            payload = args
        else:
            payload = {}

    payload = _as_dict(payload)

    num = payload.get("number_of_subsystems", None)
    names = payload.get("subsystem_names", None)
    if not isinstance(names, list):
        names = None

    return {
        "Number of Subsystems": num,
        "Subsystem Names": names,
    }
