# project_ownership_funding_util.py

def process_project_ownership_funding_tool(response):
    """
    Processes the LangChain response for the 'project_ownership_funding' tool,
    extracting and returning the ownership and funding information.

    Args:
        response (LangChain response): The response from LangChain's invoke call.

    Returns:
        dict: The extracted project ownership and funding data.
    """
    if response.tool_calls:
        tool_result = response.tool_calls[0]
        extracted_data = tool_result['args']['data']  # Access 'data' dictionary directly
        
        # Use .get() to avoid KeyErrors and handle optional fields
        return {
            "Ownership Model": extracted_data.get("ownership_model"),
            "Ownership Model (Other)": extracted_data.get("ownership_model_other"),
            "Owners": extracted_data.get("owners"),
            "Capital Expenditure (CAPEX) - USD": extracted_data.get("capex"),
            "Operational Cost (OPEX) - USD": extracted_data.get("opex"),
            "Maintenance Cost - USD": extracted_data.get("maintenance_cost"),
            "Projected Payback Period (years)": extracted_data.get("projected_payback_period"),
            "Debt Provider": extracted_data.get("debt_provider"),
            "Funding Source 1": extracted_data.get("funding_source_1"),
            "Funding Amount 1 (USD)": extracted_data.get("funding_amount_1"),
            "Funding Source 2": extracted_data.get("funding_source_2"),
            "Funding Amount 2 (USD)": extracted_data.get("funding_amount_2"),
            "Funding Source 3": extracted_data.get("funding_source_3"),
            "Funding Amount 3 (USD)": extracted_data.get("funding_amount_3")
        }
    return {}
