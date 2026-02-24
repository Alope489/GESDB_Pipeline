# extractor/utils/project_info_utils.py
def process_project_info_tool(response):
    """
    Processes the LangChain response for the 'project_info' tool,
    extracting and returning the essential project information as a dictionary.

    Args:
        response (LangChain response): The response from LangChain's invoke call.

    Returns:
        dict: The extracted project information.
    """
    if response.tool_calls:
        # Extract the relevant data directly from 'tool_calls'
        tool_result = response.tool_calls[0]  # Get the first tool call result
        extracted_data = tool_result['args']["project_info"]  # Access 'project_info' dictionary directly
        
        # Use .get() to avoid KeyErrors and handle optional fields
        return {
            "project_name": extracted_data.get("project_name"),
            "Rated Power (kW)": extracted_data.get("rated_power"),
            "Storage Capacity (kWh)": extracted_data.get("storage_capacity"),
            "Discharge Duration at Rated Power (hrs)": extracted_data.get("discharge_duration"),
            "Paired Grid Resources": extracted_data.get("paired_grid_resources"),
            "Status": extracted_data.get("status"),
            "URL": extracted_data.get("url"),
            "Description/Notes": extracted_data.get("description_notes")
        }
    return {}
