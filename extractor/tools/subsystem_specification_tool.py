# utils/subsystem_specification_tool.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.tools import tool

class PowerConversionSystemSpecifications(BaseModel):
    max_charge_power: Optional[float] = Field(
        None,
        description="Maximum Charge Power (kW) is the maximum instantaneous power (kW) at which the system can be charged."
    )
    max_discharge_power: Optional[float] = Field(
        None,
        description="Maximum Discharge Power (kW) is the maximum instantaneous power (kW) at which the system can be discharged."
    )
    overload_capability: Optional[float] = Field(
        None,
        description="Overload Capability (%) is the percent overload capacity of the power conversion system relative to its rated power."
    )
    time_allowed_for_overload: Optional[float] = Field(
        None,
        description="Time Allowed for Overload (s) specifies the time (in seconds) that the power conversion system can operate beyond its rated power."
    )
    ramping_rate: Optional[float] = Field(
        None,
        description="Ramping Rate (kW/min) is the rate of change of power output in kW/min for the energy storage system or power generation source."
    )
    response_time: Optional[float] = Field(
        None,
        description=(
            "Response Time (s) is the time required for the energy storage system to change its power output or state of charge "
            "in response to a command or change in grid conditions. This parameter indicates the system's ability to provide grid support."
        )
    )
    nominal_dc_voltage: Optional[float] = Field(
        None,
        description="Nominal DC voltage (kV) is the rated DC side voltage of the energy storage system, expressed in kV."
    )
    nominal_ac_voltage: Optional[float] = Field(
        None,
        description="Nominal AC voltage (kV) is the rated AC side voltage (kV RMS) for the system. Line-to-line for three-phase, line-to-neutral for single-phase."
    )
    nominal_frequency: Optional[float] = Field(
        None,
        description="Nominal Frequency (Hz) is the rated operating frequency of the system or electric grid, expressed in Hz."
    )
    operating_frequency_range_low: Optional[float] = Field(
        None,
        description="Operating Frequency Range (Hz) Low is the lower bound of the operating frequency range for the power conversion system."
    )
    operating_frequency_range_high: Optional[float] = Field(
        None,
        description="Operating Frequency Range (Hz) High is the upper bound of the operating frequency range for the power conversion system."
    )
    number_of_phases: Optional[int] = Field(
        None,
        description="Number of Phases on the AC terminal of the system (at the inverter output)."
    )
    topology: Optional[str] = Field(
        None,
        description=(
            "Topology describes the physical arrangement of the converter, including configurations such as DC-DC or DC-AC converter/inverter "
            "topologies, grid forming, and grid following controls."
        )
    )
    full_load_efficiency: Optional[float] = Field(
        None,
        description="Full Load Efficiency (%) is the efficiency when the energy storage system operates at maximum output."
    )
    efficiency_degradation: Optional[float] = Field(
        None,
        description=(
            "Efficiency Degradation is a percent value indicating the decrease in efficiency over time, from initial to minimum efficiency "
            "observed over 10 years or 365 cycles/year."
        )
    )
    standby_energy_consumption: Optional[float] = Field(
        None,
        description="Standby Energy Consumption (kWh) is the energy consumed by the device when idle over 24 hours per inverter per day."
    )
    lagging_power_factor_range: Optional[float] = Field(
        None,
        description="Lagging Power Factor Range is the range of power factors at which the inverter can operate while delivering power to a grid or load."
    )
    leading_power_factor_range: Optional[float] = Field(
        None,
        description="Leading Power Factor Range is the range of leading power factors at which the inverter can operate."
    )
    max_total_current_harmonic_distortion: Optional[float] = Field(
        None,
        description="Maximum Total Current Harmonic Distortion (%) is the percentage of harmonic currents in the total waveform injected into the grid."
    )
    frequency_ride_through: Optional[str] = Field(
        None,
        description="Frequency Ride Through (FRT) capability, with valid values: 'YES' or 'NO'. Indicates if the system can maintain operation during grid frequency deviations."
    )
    low_voltage_ride_through: Optional[str] = Field(
        None,
        description="Low Voltage Ride Through (LVRT) capability, with valid values: 'YES' or 'NO'. Indicates if the system can operate during low grid voltages."
    )
    high_voltage_ride_through: Optional[str] = Field(
        None,
        description="High Voltage Ride Through (HVRT) capability, with valid values: 'YES' or 'NO'. Indicates if the system can operate during high grid voltages."
    )
    warranty_lifetime_years_pcs: Optional[int] = Field(
        None,
        description="Warranty Lifetime (years) of the power conversion system, expressed in years."
    )

class BalanceOfSystemSpecifications(BaseModel):
    transformer_rating: Optional[float] = Field(
        None,
        description="Transformer Rating (kW) is the rated value of the transformer interconnecting the storage device to the grid."
    )
    transformer_configuration: Optional[str] = Field(
        None,
        description=(
            "Transformer Configuration details, including the number of windings, winding types, grounding, turn-ratio, "
            "and other relevant configuration details connecting the power conversion system to the electric grid."
        )
    )
    operating_temperature: Optional[float] = Field(
        None,
        description="Operating Temperature (°C) specifies the temperature range in which the system can operate."
    )
    communications: Optional[str] = Field(
        None,
        description="Communication protocols used within the energy storage subsystem."
    )
    enclosures: Optional[str] = Field(
        None,
        description="Details regarding the type of enclosure used to house the storage device and/or power conversion systems."
    )
    controller_type: Optional[str] = Field(
        None,
        description=(
            "Controller Type specifies the type of controller used to enable the system's functionality. "
            "Examples include Opticaster (Tesla), Egility (Encorp), etc."
        )
    )

# Define BroadCategory Enum with strict hierarchical structure
class BroadCategory(str, Enum):
    electro_chemical_energy_storage = "Electro-chemical energy storage"
    electro_mechanical_energy_storage = "Electro-mechanical energy storage"
    thermal_energy_storage = "Thermal energy storage"

# Define MidType Enum with structured descriptions for each type in all broad categories
class MidType(str, Enum):
    # Electro-Chemical Mid-Types
    lithium_ion_battery = "Lithium-ion battery"
    flow_battery = "Flow battery"
    lead_acid_battery = "Lead-acid battery"
    sodium_based_battery = "Sodium-based battery"
    nickel_based_battery = "Nickel-based battery"
    zinc_based_battery = "Zinc-based battery"
    hydrogen_storage = "Hydrogen storage"
    electro_chemical_capacitor = "Electro-chemical capacitor"
    
    # Electro-Mechanical Mid-Types
    pumped_hydro_storage = "Pumped hydro storage"
    compressed_air_energy_storage = "Compressed air energy storage"
    flywheel = "Flywheel"
    gravity_storage = "Gravity storage"

    # Thermal Energy Storage Mid-Types
    sensible_heat = "Sensible heat"
    latent_heat = "Latent heat (phase change)"
    thermochemical_heat = "Thermochemical heat (TCES)"

# Define SubType Enum (flat structure for all subtypes, organized to align with mid-types)
class SubType(str, Enum):
    # Electro-Mechanical Subtypes
    open_loop_phs = "Open-loop PHS"
    closed_loop_phs = "Closed-loop PHS"
    above_ground_caes = "Above-ground CAES"
    underground_caes = "Underground CAES"
    none = "N/A"  # Default for Flywheel, Gravity storage, and Electro-chemical capacitor

    # Lithium-ion Battery subtypes
    lithium_iron_phosphate = "Lithium-iron phosphate battery"
    lithium_nickel_manganese_cobalt = "Lithium-nickel-manganese-cobalt battery"
    lithium_nickel_cobalt_aluminum = "Lithium-nickel-cobalt-aluminum battery"
    lithium_ion_titanate = "Lithium-ion titanate battery"
    lithium_manganese_oxide = "Lithium-manganese oxide battery"
    lithium_polymer = "Lithium polymer battery"

    # Flow Battery subtypes
    vanadium_redox = "Vanadium redox flow battery"
    hydrogen_bromine = "Hydrogen-bromine flow battery"
    zinc_bromine = "Zinc-bromine flow battery"
    zinc_iron = "Zinc-iron flow battery"
    zinc_nickel_oxide = "Zinc-nickel oxide flow battery"
    iron_chromium = "Iron-chromium flow battery"

    # Lead-Acid Battery subtypes
    advanced_lead_acid = "Advanced lead-acid battery"
    valve_regulated_lead_acid = "Valve regulated lead-acid battery"
    lead_carbon = "Lead-carbon battery"
    hybrid_lead_acid_capacitor = "Hybrid lead-acid battery/electro-chemical capacitor"

    # Sodium-based Battery subtypes
    sodium_ion = "Sodium-ion battery"
    sodium_nickel_chloride = "Sodium-nickel-chloride battery"
    sodium_sulfur = "Sodium-sulfur battery"

    # Nickel-based Battery subtypes
    nickel_cadmium = "Nickel-cadmium battery"
    nickel_iron = "Nickel-iron battery"
    nickel_metal_hybrid = "Nickel-metal hybrid battery"

    # Zinc-based Battery subtypes
    zinc_air = "Zinc-air battery"
    zinc_manganese_oxide = "Zinc-manganese oxide battery"
    zinc_nickel = "Zinc-nickel battery"

    # Hydrogen Storage subtypes
    high_pressure_gas_tank = "High-pressure gas tank"
    cryogenic_liquid_tank = "Cryogenic liquid tank"
    salt_cavern = "Salt cavern"
    gas_pipelines = "Gas pipelines"
    metal_hydrides = "Metal hydrides"
    liquid_organic_hydrogen_carriers = "Liquid organic hydrogen carriers (LOHCs)"

    # Thermal Energy Storage Subtypes
    # Sensible heat subtypes
    heated_water = "Heated water"
    chilled_water = "Chilled water"
    molten_salt = "Molten salt"
    concrete_blocks = "Concrete blocks, rocks, and sand-like particles"

    # Latent heat subtypes
    ice = "Ice"
    liquid_air = "Liquid air energy storage"
    molten_silicon = "Molten silicon"
    molten_aluminum = "Molten aluminum"

    # Thermochemical heat (TCES) subtypes
    carbonates = "Carbonates"
    hydroxides = "Hydroxides"
    ammonia_synthesis_dissociation = "Ammonia synthesis/dissociation"
    redox_active_oxides = "Redox active oxides"
    sulfur_based_cycles = "Sulfur-based cycles"

# Model for specifying each subsystem with detailed hierarchy description
class SubsystemSpecification(BaseModel):
    broad_category: Optional[BroadCategory] = Field(
        None,
        description="Top-level classification for energy storage. Options:\n"
                    "- Electro-chemical energy storage: Storage types based on chemical reactions.\n"
                    "- Electro-mechanical energy storage: Storage based on mechanical processes.\n"
                    "- Thermal energy storage: Uses heat as an energy carrier for storage and later use."
    )
    mid_type: Optional[MidType] = Field(
        None,
        description=(
            "Technology type within the selected broad category. Choices are constrained by the selected broad category:\n\n"
            "For 'Electro-chemical energy storage':\n"
            "- Lithium-ion battery\n- Flow battery\n- Lead-acid battery\n"
            "- Sodium-based battery\n- Nickel-based battery\n- Zinc-based battery\n"
            "- Hydrogen storage\n- Electro-chemical capacitor\n\n"
            "For 'Electro-mechanical energy storage':\n"
            "- Pumped hydro storage\n- Compressed air energy storage\n"
            "- Flywheel\n- Gravity storage\n\n"
            "For 'Thermal energy storage':\n"
            "- Sensible heat\n- Latent heat (phase change)\n- Thermochemical heat (TCES)"
        )
    )
    sub_type: Optional[SubType] = Field(
        "N/A",
        description=(
            "Specific subtype based on the selected mid_type. This field defaults to 'N/A' when the selected mid_type "
            "does not have further subdivisions. Subtypes are outlined as follows:\n\n"
            
            "For 'Pumped hydro storage':\n"
            "- Open-loop PHS\n"
            "- Closed-loop PHS\n\n"
            
            "For 'Compressed air energy storage':\n"
            "- Above-ground CAES\n"
            "- Underground CAES\n\n"
            
            "For 'Flywheel' and 'Gravity storage':\n"
            "- No specific subtypes available; defaults to 'N/A'\n\n"
            
            "For 'Lithium-ion battery':\n"
            "- Lithium-iron phosphate battery\n"
            "- Lithium-nickel-manganese-cobalt battery\n"
            "- Lithium-nickel-cobalt-aluminum battery\n"
            "- Lithium-ion titanate battery\n"
            "- Lithium-manganese oxide battery\n"
            "- Lithium polymer battery\n\n"
            
            "For 'Flow battery':\n"
            "- Vanadium redox flow battery\n"
            "- Hydrogen-bromine flow battery\n"
            "- Zinc-bromine flow battery\n"
            "- Zinc-iron flow battery\n"
            "- Zinc-nickel oxide flow battery\n"
            "- Iron-chromium flow battery\n\n"
            
            "For 'Lead-acid battery':\n"
            "- Advanced lead-acid battery\n"
            "- Valve regulated lead-acid battery\n"
            "- Lead-carbon battery\n"
            "- Hybrid lead-acid battery/electro-chemical capacitor\n\n"
            
            "For 'Sodium-based battery':\n"
            "- Sodium-ion battery\n"
            "- Sodium-nickel-chloride battery\n"
            "- Sodium-sulfur battery\n\n"
            
            "For 'Nickel-based battery':\n"
            "- Nickel-cadmium battery\n"
            "- Nickel-iron battery\n"
            "- Nickel-metal hybrid battery\n\n"
            
            "For 'Zinc-based battery':\n"
            "- Zinc-air battery\n"
            "- Zinc-manganese oxide battery\n"
            "- Zinc-nickel battery\n\n"
            
            "For 'Hydrogen storage':\n"
            "- High-pressure gas tank\n"
            "- Cryogenic liquid tank\n"
            "- Salt cavern\n"
            "- Gas pipelines\n"
            "- Metal hydrides\n"
            "- Liquid organic hydrogen carriers (LOHCs)\n\n"
            
            "For 'Electro-chemical capacitor':\n"
            "- No specific subtypes available; defaults to 'N/A'\n\n"

            "For 'Sensible heat':\n"
            "- Heated water\n"
            "- Chilled water\n"
            "- Molten salt\n"
            "- Concrete blocks, rocks, and sand-like particles\n\n"
            
            "For 'Latent heat (phase change)':\n"
            "- Ice\n"
            "- Liquid air energy storage\n"
            "- Molten silicon\n"
            "- Molten aluminum\n\n"
            
            "For 'Thermochemical heat (TCES)':\n"
            "- Carbonates\n"
            "- Hydroxides\n"
            "- Metal hydrides\n"
            "- Ammonia synthesis/dissociation\n"
            "- Redox active oxides\n"
            "- Sulfur-based cycles"
        )
    )
    round_trip_efficiency: Optional[float] = Field(
        None,
        description=(
            "Round-trip Efficiency (%) of the storage device at STC (Standard test conditions, 25 deg. C temperature, 1 atm pressure). "
            "A round trip is typically defined as the discharge of the system from 100% to 0% state of energy at rated power, "
            "immediately followed by charging of the system from 0% to 100% energy at rated power. Measured at the AC terminals of the power electronics converter."
        )
    )
    depth_of_discharge: Optional[float] = Field(
        None,
        description=(
            "Depth of Discharge (%) refers to the amount of energy discharged from an energy storage system relative to its total capacity. "
            "Expressed as a percentage representing the state of charge (SoC) of the system after discharging."
        )
    )
    warranty_lifetime_cycles: Optional[float] = Field(
        None,
        description="Warranty Lifetime (cycles) of the storage device, expressed as the number of cycles."
    )
    warranty_lifetime_years: Optional[int] = Field(
        None,
        description="Warranty Lifetime (years) of the storage device, expressed as the number of years of operation."
    )
    specific_energy: Optional[float] = Field(
        None,
        description="Specific Energy (kWh/ton-metric) is the amount of energy stored per unit mass of an energy storage medium, measured in kWh/ton-metric."
    )
    energy_density: Optional[float] = Field(
        None,
        description="Energy Density (kWh/m3) is the amount of energy stored per unit volume of an energy storage medium, measured in kWh/m3."
    )
    footprint: Optional[float] = Field(
        None,
        description="Footprint (m2/MWh) is the physical space or land area required to install and operate the storage system, expressed in m2/MWh."
    )
    number_of_cells: Optional[int] = Field(
        None,
        description="Number of Cells in the storage device (for electrochemical storage types)."
    )
    power_conversion_system: Optional[PowerConversionSystemSpecifications] = Field(
        None,
        description="Specifications for the Power Conversion System."
    )
    balance_of_system: Optional[BalanceOfSystemSpecifications] = Field(
        None,
        description="Specifications for the Balance of System."
    )

# Schema for handling multiple subsystems with an explicit hierarchical description
class SubsystemSpecificationsSchema(BaseModel):
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
    subsystems: List[SubsystemSpecification] = Field(
        ...,
        description=(
            "List of subsystem specifications for an energy storage subsystem, with details for:\n\n"
            
            "1. **Storage Device Specifications**:\n"
            "- Round-trip Efficiency (%)\n"
            "- Depth of Discharge (%)\n"
            "- Warranty Lifetime (cycles)\n"
            "- Warranty Lifetime (years)\n"
            "- Specific Energy (kWh/ton-metric)\n"
            "- Energy Density (kWh/m3)\n"
            "- Footprint (m2/MWh)\n"
            "- Number of Cells\n\n"
            
            "2. **Power Conversion System Specifications**:\n"
            "- Maximum Charge Power (kW)\n"
            "- Maximum Discharge Power (kW)\n"
            "- Overload Capability (%)\n"
            "- Time Allowed for Overload (s)\n"
            "- Ramping Rate (kW/min)\n"
            "- Response Time (s)\n"
            "- Nominal DC Voltage (kV)\n"
            "- Nominal AC Voltage (kV)\n"
            "- Nominal Frequency (Hz)\n"
            "- Operating Frequency Range (Hz) Low\n"
            "- Operating Frequency Range (Hz) High\n"
            "- Number of Phases\n"
            "- Topology\n"
            "- Full Load Efficiency (%)\n"
            "- Efficiency Degradation\n"
            "- Standby Energy Consumption (kWh)\n"
            "- Lagging Power Factor Range\n"
            "- Leading Power Factor Range\n"
            "- Maximum Total Current Harmonic Distortion (%)\n"
            "- Frequency Ride Through (FRT)\n"
            "- Low Voltage Ride Through (LVRT)\n"
            "- High Voltage Ride Through (HVRT)\n"
            "- Warranty Lifetime (years)\n\n"
            
            "3. **Balance of System Specifications**:\n"
            "- Transformer Rating (kW)\n"
            "- Transformer Configuration\n"
            "- Operating Temperature (°C)\n"
            "- Communications\n"
            "- Enclosures\n"
            "- Controller Type\n\n"
            
            "Each entry in `subsystems` includes a classification hierarchy:\n"
            "- **Broad Category**: Groups storage types by primary classification (e.g., Electro-chemical, Electro-mechanical, Thermal).\n"
            "- **Mid Type**: Technology group within each category.\n"
            "- **Sub Type**: Specific distinctions within each mid-type (if applicable)."
        )
    )

@tool
def extract_subsystem_specifications(subsystem_data: SubsystemSpecificationsSchema):
    """
    Extracts information on the number of power storage systems, with optional detailed specifications for each system.
    Supports multiple subsystems in a single data entry, extracting and returning the following fields for each system:

    - Number of Systems
    - System Details: Each entry includes:
        - 'Broad Category', 'Mid Type', 'Sub Type': describes the power storage subsystems used by the power plant/projectsuch as a BESS or Pumped Hydro which are common power storage systems.
        - 'Storage Device Specifications'
        - 'Power Conversion System Specifications'
        - 'Balance of System Specifications'
    """


    return {
        "Number of Subsystems": subsystem_data.number_of_subsystems,
        "Subsystem Details": [
            {
                "Storage Device Specifications": {
                    "Broad Category": spec.broad_category or None,
                    "Mid Type": spec.mid_type or None,
                    "Sub Type": spec.sub_type or None,
                    "Round-trip Efficiency": spec.round_trip_efficiency,
                    "Depth of Discharge": spec.depth_of_discharge,
                    "Warranty Lifetime (cycles)": spec.warranty_lifetime_cycles,
                    "Warranty Lifetime (years)": spec.warranty_lifetime_years,
                    "Specific Energy": spec.specific_energy,
                    "Energy Density": spec.energy_density,
                    "Footprint": spec.footprint,
                    "Number of Cells": spec.number_of_cells,
                },
                "Power Conversion System Specifications": spec.power_conversion_system.dict() if spec.power_conversion_system else None,
                "Balance of System Specifications": spec.balance_of_system.dict() if spec.balance_of_system else None,
            }
            for spec in subsystem_data.subsystems
        ]
    }