from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional

class ProjectParticipantsSchema(BaseModel):
    energy_storage_technology_provider: str = Field(..., description="Provider or equipment manufacturer of the energy storage technology for the energy storage project/plant.")
    power_electronics_provider: str = Field(..., description="Provider or equipment manufacturer of the power electronics equipment for the energy storage project/plant.")
    installer: Optional[str] = Field(None, description="The installer of an energy storage project/plant, responsible for the physical installation and integration of the various components and subsystems that make up the plant. They play a crucial role in ensuring that the energy storage system is properly installed, connected, and commissioned.")
    developer: Optional[str] = Field(None, description="The developer of an energy storage project/plant, responsible for the overall planning, design, and financing of the project. They play a key role in identifying opportunities, securing funding, and overseeing the development process.")
    o_m_contractor: Optional[str] = Field(None, description="The contractor of an energy storage project/plant, responsible for the physical construction and installation of the project. They are typically engaged by the developer or owner of the plant to execute the construction activities.")
    epc_1: Optional[str] = Field(None, description="EPC (Engineering, Procurement, and Construction) contractor 1 for the project.")
    epc_2: Optional[str] = Field(None, description="EPC (Engineering, Procurement, and Construction) contractor 2 for the project.")
    epc_3: Optional[str] = Field(None, description="EPC (Engineering, Procurement, and Construction) contractor 3 for the project.")

@tool
def extract_project_participants(participants: ProjectParticipantsSchema):
    """
    Extract project participants' information for an energy storage project/plant.

    Returns a dictionary of project participants by role.
    """
    return {
        "Energy Storage Technology Provider": participants.energy_storage_technology_provider,
        "Power Electronics Provider": participants.power_electronics_provider,
        "Installer": participants.installer or None,
        "Developer": participants.developer or None,
        "O&M Contractor": participants.o_m_contractor or None,
        "EPC 1": participants.epc_1 or None,
        "EPC 2": participants.epc_2 or None,
        "EPC 3": participants.epc_3 or None
    }
