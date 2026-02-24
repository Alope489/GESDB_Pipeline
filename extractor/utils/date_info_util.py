# extractor/utils/date_info_util.py

def process_date_info_tool(response):
    """
    Processes the LangChain response for the 'date_info' tool,
    extracting and returning the essential date information as a dictionary.

    Args:
        response (LangChain response): The response from LangChain's invoke call.

    Returns:
        dict: The extracted date information.
    """
    if response.tool_calls:
        tool_result = response.tool_calls[0]  # Get the first tool call result
        extracted_data = tool_result['args']["date_info"]  # Access 'date_info' dictionary directly
        
        # Use .get() to avoid KeyErrors and handle optional fields
        return {
            "Announced Date": extracted_data.get("announced_date"),
            "Constructed Date": extracted_data.get("constructed_date"),
            "Commissioned Date": extracted_data.get("commissioned_date"),
            "Decommissioned Date": extracted_data.get("decommissioned_date"),
        }
    return {}
