# /postprocessor/postprocessor.py
from datetime import datetime
from .postprocessor_utils import PostProcessingUtils

import json
import os

class PostProcessor:
    def __init__(self, extracted_data_list, output_file_path = "data/output/processed_data.json"):
        self.extracted_data_list = extracted_data_list
        self.processed_data = []
        
        self.offset = 0
        
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r',encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if isinstance(existing_data,list):
                        self.offset = len(existing_data)
                except json.JSONDecodeError:
                    self.offset = 0
                
    
    def assign_id(self, index):
        id = self.offset + index + 1  # ID starts from 1 and increments for each element
        print(f" starting from ID:{id}")
        return id
    
    def process_element(self, extracted_data, index):
        
        subsys_input = extracted_data.get("subsystem_specifications", {})
        if not isinstance(subsys_input, dict) or not subsys_input.get("Subsystem Details"):
            print("Subsystems: no tool output; emitting default shell")
            
        element = {
            "ID": self.assign_id(index),
            "Data Source": "GESDB_Correct",
            "Project/Plant Name": extracted_data.get("project_info", {}).get("project_name", None),
            "Status": extracted_data.get("project_info", {}).get("Status", None),
            "Rated Power (kW)": extracted_data.get("project_info", {}).get("Rated Power (kW)", None),
            "Discharge Duration at Rated Power (hrs)": extracted_data.get("project_info", {}).get("Discharge Duration at Rated Power (hrs)", None),
            "Storage Capacity (kWh)": extracted_data.get("project_info", {}).get("Storage Capacity (kWh)", None),
            "Applications": self.format_applications(extracted_data.get("project_applications", {})),
            "Paired Grid Resources": extracted_data.get("project_info", {}).get("Paired Grid Resources", None),
            "Description/Notes": extracted_data.get("project_info", {}).get("Description/Notes", None),
            "URL": extracted_data.get("project_info", {}).get("URL", None),
            "Country": extracted_data.get("location_info", {}).get("Country", None),
            "City": extracted_data.get("location_info", {}).get("City", None),
            "County": extracted_data.get("location_info", {}).get("County", None),
            "State/Province/Territory": extracted_data.get("location_info", {}).get("State/Province", None),
            "Street Address": extracted_data.get("location_info", {}).get("Street Address", None),
            "Postal Code": extracted_data.get("location_info", {}).get("Postal Code", None),
            "Latitude": extracted_data.get("location_info", {}).get("Latitude", None),
            "Longitude": extracted_data.get("location_info", {}).get("Longitude", None),
            "Announced Date": extracted_data.get("date_info", {}).get("Announced Date", None),
            "Constructed Date": extracted_data.get("date_info", {}).get("Constructed Date", None),
            "Commissioned Date": extracted_data.get("date_info", {}).get("Commissioned Date", None),
            "Decommissioned Date": extracted_data.get("date_info", {}).get("Decommissioned Date", None),
            "Latest Update Date": datetime.now().strftime("%m-%d-%Y"),
            "Project Data Validated?": "NO",
            "Grid Interconnection Level": extracted_data.get("grid_utility", {}).get("Grid Interconnection Level", None),
            "Interconnection Type": extracted_data.get("grid_utility", {}).get("Interconnection Type", None),
            "ISO/RTO": extracted_data.get("grid_utility", {}).get("ISO/RTO", None),
            "System Operator": extracted_data.get("grid_utility", {}).get("System Operator", None),
            "Utility Type": extracted_data.get("grid_utility", {}).get("Utility Type", None),
            "Utility ID": None,
            "Number of Subsystems": extracted_data.get("grid_utility", {}).get("Number of Subsystems", None),
            "Energy Storage Technology Provider": extracted_data.get("project_participants", {}).get("Energy Storage Technology Provider", None),
            "Power Electronics Provider": extracted_data.get("project_participants", {}).get("Power Electronics Provider", None),
            "Installer": extracted_data.get("project_participants", {}).get("Installer", None),
            "Developer": extracted_data.get("project_participants", {}).get("Developer", None),
            "O&M Contractor": extracted_data.get("project_participants", {}).get("O&M Contractor", None),
            "EPC 1": extracted_data.get("project_participants", {}).get("EPC 1", None),
            "EPC 2": extracted_data.get("project_participants", {}).get("EPC 2", None),
            "EPC 3": extracted_data.get("project_participants", {}).get("EPC 3", None),
            "Ownership Model": extracted_data.get("project_ownership_funding", {}).get("Ownership Model", None),
            "Ownership Model (Other)": extracted_data.get("project_ownership_funding", {}).get("Ownership Model (Other)", None),
            "Owner(s)": extracted_data.get("project_ownership_funding", {}).get("Owners", None),
            "Capital Expenditure - CAPEX (USD)": extracted_data.get("project_ownership_funding", {}).get("Capital Expenditure (CAPEX) - USD", None),
            "Annual Operational Cost - OPEX (USD)": extracted_data.get("project_ownership_funding", {}).get("Operational Cost (OPEX) - USD", None),
            "Annual Maintenance or Warranty Cost (USD)": extracted_data.get("project_ownership_funding", {}).get("Maintenance Cost - USD", None),
            "Projected Payback Period (years)": extracted_data.get("project_ownership_funding", {}).get("Projected Payback Period (years)", None),
            "Debt Provider": extracted_data.get("project_ownership_funding", {}).get("Debt Provider", None),
            "Funding Source 1": extracted_data.get("project_ownership_funding", {}).get("Funding Source 1", None),
            "Funding Source Amount 1 (USD)": extracted_data.get("project_ownership_funding", {}).get("Funding Amount 1 (USD)", None),
            "Funding Source 2": extracted_data.get("project_ownership_funding", {}).get("Funding Source 2", None),
            "Funding Source Amount 2 (USD)": extracted_data.get("project_ownership_funding", {}).get("Funding Amount 2 (USD)", None),
            "Funding Source 3": extracted_data.get("project_ownership_funding", {}).get("Funding Source 3", None),
            "Funding Source Amount 3 (USD)": extracted_data.get("project_ownership_funding", {}).get("Funding Amount 3 (USD)", None),
            "Contact Information: Name": extracted_data.get("contact_info", {}).get("Name", None),
            "Contact Information: Email Address": extracted_data.get("contact_info", {}).get("Email", None),
            "Contact Information: Phone Number": extracted_data.get("contact_info", {}).get("Phone Number", None),
            "Subsystems": self.format_subsystems(extracted_data.get("subsystem_specifications", {}))
        }

        # Ensure at least one empty subsystem is present
        if not element["Subsystems"]:
            element["Subsystems"].append({
                "Subsystem Name": "Subsystem 1",
                "ID": 1.1,
                "Storage Device": {
                    "Technology Broad Category": None,
                    "Technology Mid-Type": None,
                    "Technology Sub-Type": None,                   
                    "Round-trip Efficiency (%)": None,
                    "Depth of Discharge (%)": None,
                    "Warranty Lifetime (cycles)": None,
                    "Warranty Lifetime (years)": None,
                    "Specific Energy (kWh/ton-metric)": None,
                    "Energy Density (kWh/m3)": None,
                    "Footprint (m2/MWh)": None,
                    "Number of Cells": None
                },
                "Power Conversion System": {
                    "Maximum Charge Power (kW)": None,
                    "Maximum Discharge Power (kW)": None,
                    "Overload Capability (%)": None,
                    "Time Allowed for Overload (s)": None,
                    "Ramping Rate (kW/min)": None,
                    "Response Time (s)": None,
                    "Nominal DC Voltage (kV)": None,
                    "Nominal AC Voltage (kV)": None,
                    "Nominal Frequency (Hz)": None,
                    "Operating Frequency Range (Hz) Low": None,
                    "Operating Frequency Range (Hz) High": None,
                    "Number of Phases": None,
                    "Topology": None,
                    "Full Load Efficiency (%)": None,
                    "Efficiency Degradation": None,
                    "Standby Energy Consumption (kWh)": None,
                    "Lagging Power Factor Range": None,
                    "Leading Power Factor Range": None,
                    "Maximum Total Current Harmonic Distortion (%)": None,
                    "Frequency Ride Through (FRT)": None,
                    "Low Voltage Ride Through (LVRT)": None,
                    "High Voltage Ride Through (HVRT)": None,
                    "Warranty Lifetime (years)": None
                },
                "Balance of System": {
                    "Transformer Rating (kW)": None,
                    "Transformer Configuration": None,
                    "Operating Temperature (°C)": None,
                    "Communications": None,
                    "Enclosures": None,
                    "Controller Type": None
                }
            })

        # Post-process element for null values, missing data, etc.
        return PostProcessingUtils.fill_missing_values(element)


    def format_applications(self, applications):
        # Model output keys from the util:
        #   "Bulk Energy Services"
        #   "Ancillary Services"
        #   "Transmission Infrastructure Services"
        #   "Distribution Infrastructure Services"
        #   "Customer Energy Management Services"
        #   "Other Services"

        # Your target display keys:
        display_keys = [
            "Bulk Energy Services (General Energy Applications)",
            "Ancillary Services",
            "Transmission Infrastructure Services",
            "Distribution Infrastructure Services",
            "Customer Energy Management Services (End-User Services)",
            "Others",
        ]

        # Map display -> source key
        key_map = {
            "Bulk Energy Services (General Energy Applications)": "Bulk Energy Services",
            "Ancillary Services": "Ancillary Services",
            "Transmission Infrastructure Services": "Transmission Infrastructure Services",
            "Distribution Infrastructure Services": "Distribution Infrastructure Services",
            "Customer Energy Management Services (End-User Services)": "Customer Energy Management Services",
            "Others": "Other Services",
        }

        # If applications is None or not a dict, return empty lists for all categories
        if not isinstance(applications, dict):
            return {k: [] for k in display_keys}

        out = {}
        for display_key in display_keys:
            source_key = key_map[display_key]
            vals = applications.get(source_key)
            out[display_key] = vals if isinstance(vals, list) else []
        return out


    
    def format_subsystems(self, subsystems_data):
        def _normalize_storage_device(sd: dict) -> dict:
            sd = dict(sd or {})

            # Pull classification fields (support a few possible names)
            broad = sd.pop("Technology Broad Category", sd.pop("Broad Category", sd.pop("broad_category", None)))
            mid   = sd.pop("Technology Mid-Type", sd.pop("Mid Type", sd.pop("mid_type", None)))
            sub   = sd.pop("Technology Sub-Type", sd.pop("Sub Type", sd.pop("sub_type", None)))

            # Ensure standardized labels exist in output
            sd.setdefault("Technology Broad Category", broad)
            sd.setdefault("Technology Mid-Type", mid)
            sd.setdefault("Technology Sub-Type", sub)

            # Normalize a couple of common name variants
            if "Round-trip Efficiency (%)" not in sd and "Round-trip Efficiency" in sd:
                sd["Round-trip Efficiency (%)"] = sd.pop("Round-trip Efficiency")

            return sd

        subsystems = []
        for idx, subsystem in enumerate(subsystems_data.get("Subsystem Details", []), start=1):
            raw_sd  = subsystem.get("Storage Device Specifications", {}) or {}
            raw_pcs = subsystem.get("Power Conversion System Specifications", {}) or {}
            raw_bos = subsystem.get("Balance of System Specifications", {}) or {}

            subsystems.append({
                "Subsystem Name": f"Subsystem {idx}",
                "ID": idx,
                "Storage Device": _normalize_storage_device(raw_sd),
                "Power Conversion System": dict(raw_pcs),  # keep as-is (your labels already match)
                "Balance of System": dict(raw_bos),        # keep as-is
            })

        return subsystems

    def process_all(self):
        for index, data in enumerate(self.extracted_data_list):
            self.processed_data.append(self.process_element(data, index))
        return self.processed_data
