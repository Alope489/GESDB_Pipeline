# utils/contact_info_util.py

def process_contact_info_tool(response):
    """
    Processes the LangChain response for the 'contact_info' tool.

    Args:
        response: The response from LangChain's invoke call.

    Returns:
        dict: The structured contact information.
    """
    if response.tool_calls:
        tool_result = response.tool_calls[0]  # Get the first tool call result
        extracted_data = tool_result['args']["contact_info"]  # Access 'contact_info' dictionary directly
        
        # Structure the output
        return {
            "Name": extracted_data.get("name"),
            "Email": extracted_data.get("email"),
            "Phone Number": extracted_data.get("phone_number", None)
        }
    return {}
