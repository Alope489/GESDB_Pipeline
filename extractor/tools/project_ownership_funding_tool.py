from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# Enum for Ownership Model with exact options
class OwnershipModel(str, Enum):
    utility_owned = "Utility-owned"
    customer_owned = "Customer-owned"
    other = "Other"

# Pydantic model for Project Ownership and Funding
class ProjectOwnershipFundingSchema(BaseModel):
    ownership_model: OwnershipModel = Field(..., description="The ownership model of an energy storage project/plant refers to the structure and ownership arrangement of the plant. Examples: Utility-owned, customer-owned, independent power producer (IPP), Third-party owned, community-owned.")
    ownership_model_other: str = Field(..., description="What kind of ownership model is this (if user selected 'Other' for Ownership Model). Can be 'N/A' if not applicable. The ownership model of an energy storage project/plant refers to the structure and ownership arrangement of the plant. Examples: Utility-owned, customer-owned, independent power producer (IPP), Third-party owned, community-owned.")
    owners: Optional[str] = Field(None, description="List of owners of the energy storage project/plant.")
    capex: Optional[int] = Field(None, description="Capital Expenditure - CAPEX of the energy storage project/plant in USD.")
    opex: Optional[int] = Field(None, description="Annual Operational Cost of the energy storage project/plant in USD.")
    maintenance_cost: Optional[int] = Field(None, description="Annual Maintenance or Warranty Cost of the energy storage project/plant in USD.")
    projected_payback_period: Optional[int] = Field(None, description="Projected payback period of the energy storage project/plant in years.")
    debt_provider: Optional[str] = Field(None, description="Debt provider for the energy storage project/plant.")
    funding_source_1: Optional[str] = Field(None, description="Primary funding source for the energy storage project/plant.")
    funding_amount_1: Optional[float] = Field(None, description="Amount provided by the primary funding source in USD.")
    funding_source_2: Optional[str] = Field(None, description="Secondary funding source for the energy storage project/plant.")
    funding_amount_2: Optional[float] = Field(None, description="Amount provided by the secondary funding source in USD.")
    funding_source_3: Optional[str] = Field(None, description="Tertiary funding source for the energy storage project/plant.")
    funding_amount_3: Optional[float] = Field(None, description="Amount provided by the tertiary funding source in USD.")

@tool
def extract_project_ownership_funding(data: ProjectOwnershipFundingSchema):
    """
    Extracts information about the ownership and funding structure of an energy storage project/plant.
    
    Returns a dictionary with details about ownership model, expenditure, funding, and financial providers.
    """
    return {
        "Ownership Model": data.ownership_model.value,
        "Ownership Model (Other)": data.ownership_model_other or None,
        "Owners": data.owners or None,
        "Capital Expenditure (CAPEX) - USD": data.capex or None,
        "Operational Cost (OPEX) - USD": data.opex or None,
        "Maintenance Cost - USD": data.maintenance_cost or None,
        "Projected Payback Period (years)": data.projected_payback_period or None,
        "Debt Provider": data.debt_provider or None,
        "Funding Source 1": data.funding_source_1 or None,
        "Funding Amount 1 (USD)": data.funding_amount_1 or None,
        "Funding Source 2": data.funding_source_2 or None,
        "Funding Amount 2 (USD)": data.funding_amount_2 or None,
        "Funding Source 3": data.funding_source_3 or None,
        "Funding Amount 3 (USD)": data.funding_amount_3 or None
    }
