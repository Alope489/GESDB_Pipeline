from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Define the Pydantic model with location-related fields
class LocationInfoSchema(BaseModel):
    country: str = Field(..., description="The country where the energy storage project/plant is located.")
    city: str = Field(..., description="The city where the energy storage project/plant is located.")
    state_province: str = Field(..., description="The state or province where the energy storage project/plant is located.")
    county: str = Field(None, description="If in the US, the county where the project is located.")
    street_address: str = Field(None, description="The street address where the energy storage project/plant is located.")
    postal_code: str = Field(None, description="The postal code of the location where the project is located.")
    latitude: float = Field(None, description="Latitude in signed degrees format: (+/-) DDD.ddd.")
    longitude: float = Field(None, description="Longitude in signed degrees format: (+/-) DDD.ddd.")

# Define the tool function to extract location information
@tool
def extract_location_info(location_info: LocationInfoSchema):
    """
    Extracts location details for an energy storage project, including:

    - Country, City, State/Province, and County (if in the US)
    - Street Address and Postal Code
    - Latitude and Longitude

    Returns a structured summary of the location for data consistency.
    """


    return (
        f"Country: {location_info.country}, "
        f"City: {location_info.city}, "
        f"State/Province/Territory: {location_info.state_province}, "
        f"County: {location_info.county or None}, "
        f"Street Address: {location_info.street_address or None}, "
        f"Postal Code: {location_info.postal_code or None}, "
        f"Latitude: {location_info.latitude or None}, "
        f"Longitude: {location_info.longitude or None}"
    )
