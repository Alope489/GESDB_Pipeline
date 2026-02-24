# extractor/utils/grid_utility_util.py

def process_grid_utility_tool(response):
    """
    Processes the LangChain response for the 'grid_utility' tool,
    extracting and returning the relevant grid and utility information as a dictionary.

    Args:
        response (LangChain response): The response from LangChain's invoke call.

    Returns:
        dict: The extracted grid and utility information.
    """
    if response.tool_calls:
        tool_result = response.tool_calls[0]
        extracted_data = tool_result['args']['grid_utility_info']
        
        return {
            "Grid Interconnection Level": extracted_data.get("grid_interconnection_level"),
            "Interconnection Type": extracted_data.get("interconnection_type"),
            "ISO/RTO": extracted_data.get("iso_rto"),
            "System Operator": extracted_data.get("system_operator"),
            "Utility Type": extracted_data.get("utility_type"),
            "Number of Subsystems": extracted_data.get("number_of_subsystems")
        }
    return {}
