# tools/project_applications_tool.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class BulkEnergyApplications(str, Enum):
    electric_energy_time_shift = "Electric Energy Time Shift (Arbitrage)"
    peak_shaving = "Peak Shaving"
    renewable_energy_time_shift = "Renewable Energy Time Shift"
    renewable_energy_time_shift_firming = "Renewable Energy Time Shift (Firming)"

class AncillaryApplications(str, Enum):
    frequency_regulation = "Frequency Regulation"
    operating_reserve_non_spinning = "Operating Reserve (Non-spinning)"
    operating_reserve_spinning = "Operating Reserve (Spinning)"
    operating_reserve_supplementary = "Operating Reserve (Supplementary)"
    voltage_support = "Voltage Support"
    black_start = "Black Start"
    frequency_response_virtual_inertia = "Frequency Response and Virtual Inertia"
    ramp_support = "Ramp Support"

class TransmissionInfrastructureApplications(str, Enum):
    transmission_upgrade_deferral = "Transmission Upgrade Deferral"
    transmission_congestion_relief = "Transmission Congestion Relief"
    stability_damping_control = "Stability Damping Control"

class DistributionInfrastructureApplications(str, Enum):
    distribution_upgrade_deferral = "Distribution Upgrade Deferral"
    voltage_regulation = "Voltage Regulation"
    reliability = "Reliability"

class CustomerEnergyManagementApplications(str, Enum):
    power_quality = "Power Quality"
    resilience_backup_power = "Resilience (Back-up Power)"
    retail_tou_energy_charges = "Retail TOU Energy Charges"
    demand_charge_management = "Demand Charge Management"
    microgrid_applications = "Microgrid Applications"

class OtherApplications(str, Enum):
    transportation_services = "Transportation Services"
    electric_supply_capacity = "Electric Supply Capacity"

class BulkEnergyServices(BaseModel):
    applications: List[BulkEnergyApplications] = Field(..., description="List of bulk energy applications provided by the project.")

class AncillaryServices(BaseModel):
    applications: List[AncillaryApplications] = Field(..., description="List of ancillary services provided by the project, supporting grid stability.")

class TransmissionInfrastructureServices(BaseModel):
    applications: List[TransmissionInfrastructureApplications] = Field(..., description="List of transmission infrastructure applications aimed at enhancing grid transmission.")

class DistributionInfrastructureServices(BaseModel):
    applications: List[DistributionInfrastructureApplications] = Field(..., description="List of distribution infrastructure services that support distribution grid operations.")

class CustomerEnergyManagementServices(BaseModel):
    applications: List[CustomerEnergyManagementApplications] = Field(..., description="Customer-oriented applications focusing on energy management.")

class OtherServices(BaseModel):
    applications: List[OtherApplications] = Field(..., description="Additional services that do not fit into the other categories.")

# Full model definition for ProjectApplications with descriptions
class ProjectApplications(BaseModel):
    bulk_energy_services: Optional[BulkEnergyServices] = Field(None, description="Details about bulk energy services offered by the project.")
    ancillary_services: Optional[AncillaryServices] = Field(None, description="Ancillary services details provided by the project for grid stability.")
    transmission_infrastructure_services: Optional[TransmissionInfrastructureServices] = Field(None, description="Transmission infrastructure-related services offered by the project.")
    distribution_infrastructure_services: Optional[DistributionInfrastructureServices] = Field(None, description="Distribution infrastructure services provided by the project to support grid distribution.")
    customer_energy_management_services: Optional[CustomerEnergyManagementServices] = Field(None, description="Energy management services aimed at end customers.")
    other_services: Optional[OtherServices] = Field(None, description="Other additional services provided by the project.")

def extract_project_applications(applications: ProjectApplications):
    """
    Extracts application details for different energy services provided by a power project or plant, including:

    - Bulk Energy Services: Large-scale energy services like energy time shift and peak shaving.
    - Ancillary Services: Grid stability services such as frequency regulation and voltage support.
    - Transmission Infrastructure Services: Services focused on grid transmission, like upgrade deferral.
    - Distribution Infrastructure Services: Supports distribution needs such as voltage regulation and reliability.
    - Customer Energy Management Services: Customer-oriented services, including demand charge management.
    - Other Services: Additional applications, such as transportation services.

    Returns a dictionary of applications by service category.
    """


    # Process each service category
    output = {
        "Bulk Energy Services": [app.value for app in applications.bulk_energy_services.applications] if applications.bulk_energy_services else None,
        "Ancillary Services": [app.value for app in applications.ancillary_services.applications] if applications.ancillary_services else None,
        "Transmission Infrastructure Services": [app.value for app in applications.transmission_infrastructure_services.applications] if applications.transmission_infrastructure_services else None,
        "Distribution Infrastructure Services": [app.value for app in applications.distribution_infrastructure_services.applications] if applications.distribution_infrastructure_services else None,
        "Customer Energy Management Services": [app.value for app in applications.customer_energy_management_services.applications] if applications.customer_energy_management_services else None,
        "Other Services": [app.value for app in applications.other_services.applications] if applications.other_services else None
    }
    return output
