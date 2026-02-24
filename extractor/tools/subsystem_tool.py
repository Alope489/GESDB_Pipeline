# tools/subsystem_tool.py

from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.tools import tool

class SubsystemInfoSchema(BaseModel):
    number_of_subsystems: int = Field(
        ...,
        description=(
            "The total number of individual power storage subsystems in the project. Examples of power storage subsystems include: "
            "Electrochemical systems (e.g., lithium-ion batteries, lead acid batteries, vanadium redox flow batteries), "
            "Thermal systems (e.g., molten salt storage, ice storage), "
            "Mechanical systems (e.g., flywheels, pumped hydroelectric power), "
            "Compressed Air Energy Storage (CAES), Superconducting Magnetic Energy Storage (SMES), "
            "and Phase Change Material (PCM) systems."
        )
    )
    subsystem_names: Optional[List[str]] = Field(
        None,
        description=(
            "List of power storage subsystem names, if provided. Examples might include specific technologies such as "
            "'Battery Energy Storage System (BESS)', 'Thermal Storage System', 'Flywheel Storage', 'CAES', 'SMES', "
            "or 'PCM Thermal Storage'."
        )
    )

@tool
def extract_subsystem_info(subsystem_info: SubsystemInfoSchema):
    """
    Extracts information on the number of power storage subsystems and optional power storage subsystem names. 
    Examples include Electrochemical systems (e.g., lithium-ion batteries), Thermal systems (e.g., ice storage), 
    Mechanical systems (e.g., flywheels), CAES, SMES, and PCM systems.

    Returns a dictionary with the number of subsystems and an optional list of names.
    """
    return {
        "Number of Subsystems": subsystem_info.number_of_subsystems,
        "Subsystem Names": subsystem_info.subsystem_names or None
    }
