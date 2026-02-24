# extractor/utils/project_participants_util.py

def process_project_participants_tool(response):
    """
    Processes the LangChain response for the 'project_participants' tool,
    extracting and returning the essential participants' information as a dictionary.

    Args:
        response (LangChain response): The response from LangChain's invoke call.

    Returns:
        dict: The extracted participants' information.
    """
    if response.tool_calls:
        tool_result = response.tool_calls[0]
        extracted_data = tool_result['args']["participants"]

        return {
            "Energy Storage Technology Provider": extracted_data.get("energy_storage_technology_provider"),
            "Power Electronics Provider": extracted_data.get("power_electronics_provider"),
            "Installer": extracted_data.get("installer", None),
            "Developer": extracted_data.get("developer", None),
            "O&M Contractor": extracted_data.get("o_m_contractor", None),
            "EPC 1": extracted_data.get("epc_1", None),
            "EPC 2": extracted_data.get("epc_2", None),
            "EPC 3": extracted_data.get("epc_3", None)
        }
    return {}
