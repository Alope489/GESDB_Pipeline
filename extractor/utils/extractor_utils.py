# utils/extractor_utils.py

import inspect

from .project_info_utils import process_project_info_tool
from .location_info_utils import process_location_info_tool
from .date_info_util import process_date_info_tool
from .project_applications_util import process_project_applications_tool
from .grid_utility_util import process_grid_utility_tool
from .project_participants_util import process_project_participants_tool
from .project_ownership_funding_util import process_project_ownership_funding_tool
from .contact_info_util import process_contact_info_tool
from .subsystem_util import process_subsystem_info_tool
from .subsystem_specifications_util import process_subsystem_specifications_tool


def _get_tool_name(tc):
    """Return tool-call name from a dict-like or object-like tool call."""
    if isinstance(tc, dict):
        return tc.get("name")
    return getattr(tc, "name", None)


def _get_tool_args(tc):
    """Return args dict from a dict-like or object-like tool call."""
    if isinstance(tc, dict):
        return tc.get("args", {}) or {}
    return getattr(tc, "args", {}) or {}


def _pick_tool_call(ai_message, tool_name: str):
    """
    Choose the most likely tool call for this tool_name.

    Strategy:
    1) match exact tool_name (e.g., "contact_info" if you later use @tool("contact_info"))
    2) match "extract_<tool_name>" (e.g., current default function names like "extract_contact_info")
    3) fallback to the first tool call if present
    """
    tool_calls = getattr(ai_message, "tool_calls", None) or []
    if not tool_calls:
        return None, {}

    # 1) exact registry key
    for tc in tool_calls:
        if _get_tool_name(tc) == tool_name:
            return tc, _get_tool_args(tc)

    # 2) common pattern: function named extract_<tool_name>
    alt = f"extract_{tool_name}"
    for tc in tool_calls:
        if _get_tool_name(tc) == alt:
            return tc, _get_tool_args(tc)

    # 3) fallback
    tc0 = tool_calls[0]
    return tc0, _get_tool_args(tc0)


class ExtractorUtils:
    @staticmethod
    def process_response(tool_name, response):
        """
        Directs the response to the correct processing function based on tool_name.

        Backward-compatible behavior:
          - If the processor only accepts (response), we call it as before.
          - If it also accepts a second parameter (args), we pass the parsed args dict.
        """
        tool_processing_functions = {
            "project_info": process_project_info_tool,
            "location_info": process_location_info_tool,
            "date_info": process_date_info_tool,
            "project_applications": process_project_applications_tool,
            "grid_utility": process_grid_utility_tool,
            "project_participants": process_project_participants_tool,
            "project_ownership_funding": process_project_ownership_funding_tool,
            "contact_info": process_contact_info_tool,
            "subsystem_info": process_subsystem_info_tool,
            "subsystem_specifications": process_subsystem_specifications_tool,
        }

        func = tool_processing_functions.get(tool_name)
        if not func:
            raise ValueError(f"No processing function found for tool '{tool_name}'.")

        # Parse the tool-call args once, centrally (works with GPT-5 Responses API).
        _, args_dict = _pick_tool_call(response, tool_name)

        # Call the processor. If it supports a second param, pass the parsed args.
        try:
            sig = inspect.signature(func)
            if len(sig.parameters) >= 2:
                return func(response, args_dict)
            else:
                return func(response)
        except (TypeError, ValueError):
            # Fallback to legacy signature
            return func(response)
