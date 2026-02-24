from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from datetime import date

# Define the Pydantic model with date-related fields
class DateInfoSchema(BaseModel):
    announced_date: str = Field(None, description="Date when the energy storage project/plant was announced. The expected date format is MM-DD-YYYY.")
    constructed_date: str = Field(None, description="Date when the energy storage project/plant construction was completed. The expected date format is MM-DD-YYYY.")
    commissioned_date: str = Field(..., description="Date when the energy storage project/plant was commissioned. The expected date format is MM-DD-YYYY or N/A if not commissioned.")
    decommissioned_date: str = Field(..., description="Date when the energy storage project/plant was decommissioned. The expected date format is MM-DD-YYYY or N/A if not decommissioned.")

# Define the tool function to extract date information
@tool
def extract_date_info(date_info: DateInfoSchema):
    """
    Extract date-related information for the energy storage project/plant, such as announced, constructed, commissioned, and decommissioned dates.
    """
    return (
        f"Announced Date: {date_info.announced_date or None}, "
        f"Constructed Date: {date_info.constructed_date or None}, "
        f"Commissioned Date: {date_info.commissioned_date}, "
        f"Decommissioned Date: {date_info.decommissioned_date}, "
    )
