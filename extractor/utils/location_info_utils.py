# extractor/utils/location_info_utils.py
def process_location_info_tool(response):
    """
    Processes the LangChain response for the 'location_info' tool,
    extracting and returning the essential location information as a dictionary.

    Args:
        response (LangChain response): The response from LangChain's invoke call.

    Returns:
        dict: The extracted location information.
    """
    if response.tool_calls:
        # Extract the relevant data directly from 'tool_calls'
        tool_result = response.tool_calls[0]  # Get the first tool call result
        extracted_data = tool_result['args']["location_info"]  # Access 'location_info' dictionary directly
        
        # Use .get() to avoid KeyErrors and handle optional fields
        return {
            "Country": extracted_data.get("country"),
            "City": extracted_data.get("city"),
            "State/Province/Territory": extracted_data.get("state_province"),
            "County": extracted_data.get("county"),
            "Street Address": extracted_data.get("street_address"),
            "Postal Code": extracted_data.get("postal_code"),
            "Latitude": extracted_data.get("latitude"),
            "Longitude": extracted_data.get("longitude")
        }
    return {}
