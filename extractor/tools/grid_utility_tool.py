from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class GridInterconnectionLevel(str, Enum):
    transmission = "Transmission"
    primary_distribution = "Primary distribution"
    secondary_distribution = "Secondary distribution"
    off_grid = "Off-grid"

class InterconnectionType(str, Enum):
    ac = "AC"
    dc = "DC"

class UtilityType(str, Enum):
    investor_owned = "Investor-owned"
    public_owned = "Public-owned"
    cooperative = "Cooperative (customer-owned)"
    state_municipal_owned = "State/municipal-owned"
    federally_owned = "Federally-owned"

class GridUtilitySchema(BaseModel):
    grid_interconnection_level: GridInterconnectionLevel = Field(
        ...,
        description=(
            "Grid interconnection level refers to the point at which an energy storage project/plant is connected "
            "to the electrical grid. It determines the scope and scale of the system's interaction with the grid. "
            "Valid values are: Transmission, Primary distribution, Secondary distribution, Off-grid."
        )
    )
    interconnection_type: InterconnectionType = Field(
        None,
        description="Type of interconnection for the project/plant, referring to whether it is connected via AC or DC grid."
    )
    iso_rto: str = Field(
        None,
        description="The ISO/RTO (Independent System Operator/Regional Transmission Organization) associated with the project."
    )
    system_operator: str = Field(
        None,
        description=(
            "The system operator is responsible for the management, control, and maintenance of energy storage assets "
            "in the project/plant. Responsibilities may include system monitoring, dispatch and scheduling, maintenance, "
            "asset management, data analysis, safety compliance, and revenue optimization."
        )
    )
    utility_type: UtilityType = Field(
        None,
        description=(
            "The type of electric utility operating the energy storage project/plant. Valid values are: Investor-owned, "
            "Public-owned, Cooperative (customer-owned), State/municipal-owned, Federally-owned."
        )
    )

@tool
def extract_grid_utility_info(grid_utility_info: GridUtilitySchema):
    """
    Extracts grid and utility details for an energy storage project, including:

    - Grid Interconnection Level (e.g., Transmission, Distribution)
    - Interconnection Type (AC or DC)
    - ISO/RTO and System Operator
    - Utility Type (e.g., Investor-owned, Public-owned)

    Returns structured grid and utility information for integration.
    """

    return {
        "Grid Interconnection Level": grid_utility_info.grid_interconnection_level.value,
        "Interconnection Type": grid_utility_info.interconnection_type.value if grid_utility_info.interconnection_type else "N/A",
        "ISO/RTO": grid_utility_info.iso_rto or None,
        "System Operator": grid_utility_info.system_operator or None,
        "Utility Type": grid_utility_info.utility_type.value if grid_utility_info.utility_type else None,
    }
