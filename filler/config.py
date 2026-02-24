"""Filler config: paths, field groups (View Records categories), and fields where 0 is invalid."""
from pathlib import Path

# Project root (parent of filler package)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths under project root so they work regardless of cwd (e.g. when run from Streamlit)
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "output" / "processed_data.json"
ATTRIBUTIONS_PATH = PROJECT_ROOT / "data" / "output" / "filler_attributions.json"
VALIDATION_STATUS_PATH = PROJECT_ROOT / "validation" / "output" / "validation_status.csv"

# Error codes that trigger a search (Unvalidated + one of these = try to fill)
FILLABLE_ERROR_CODES = frozenset({
    101, 102, 201, 202, 203, 107, 104, 105, 106, 301, 302,
    2501, 2502, 6401, 6402, 6501, 6502, 6503, 6504,
})

# Validation CSV column name -> record key when they differ
VALIDATION_COLUMN_TO_RECORD_KEY = {
    "State/Province/Territory": "State/Province",
    "Capital Expenditure - CAPEX (USD)": "Captial Expenditure - CAPEX (USD)",
}

# Same categories as pipeline.py categorize_data(); keys that may appear in record
# Record may have "State/Province" instead of "State/Province/Territory"
CATEGORY_KEYS = {
    "Project Details": [
        "ID", "Project/Plant Name", "Status", "Rated Power (kW)",
        "Storage Capacity (kWh)", "Applications", "Paired Grid Resources",
        "Description/Notes", "URL", "Latest Update Date",
    ],
    "Location Information": [
        "Country", "City", "State/Province/Territory", "State/Province", "County",
        "Street Address", "Postal Code", "Latitude", "Longitude",
    ],
    "Date Information": [
        "Announced Date", "Constructed Date", "Commissioned Date",
        "Decommissioned Date",
    ],
    "Contact Information": [
        "Contact Information: Name", "Contact Information: Email Address",
        "Contact Information: Phone Number",
    ],
    "Grid & Utility": [
        "Grid Interconnection Level", "Interconnection Type", "ISO/RTO",
        "System Operator", "Utility Type",
    ],
    "Ownership and Financials": [
        "Ownership Model", "Owner(s)",
        "Capital Expenditure - CAPEX (USD)", "Captial Expenditure - CAPEX (USD)",
        "Annual Operational Cost - OPEX (USD)", "Debt Provider",
        "Funding Source 1", "Funding Source Amount 1 (USD)",
        "Funding Source 2", "Funding Source Amount 2 (USD)",
        "Funding Source 3", "Funding Source Amount 3 (USD)",
    ],
    "Subsystems": ["Subsystems"],
}

# Fields where 0 is treated as empty (must be > 0). Top-level and subsystem key names.
# Aligned with validation/data/gesdb_data_rules.csv Lower Range ">0"
FIELDS_REQUIRE_POSITIVE = frozenset({
    "Rated Power (kW)", "Storage Capacity (kWh)", "Discharge Duration at Rated Power (hrs)",
    "Capital Expenditure - CAPEX (USD)", "Captial Expenditure - CAPEX (USD)",
    "Annual Operational Cost - OPEX (USD)", "Annual Maintenance or Warranty Cost (USD)",
    "Projected Payback Period (years)",
    "Funding Source Amount 1 (USD)", "Funding Source Amount 2 (USD)", "Funding Source Amount 3 (USD)",
    "Storage Capacity (kWh)", "Round-trip Efficiency (%)", "Depth of Discharge (%)",
    "Warranty Lifetime (cycles)", "Warranty Lifetime (years)", "Specific Energy (kWh/ton-metric)",
    "Energy Density (kWh/m^3)", "Footprint (m^2/MWh)", "Number of Cells",
    "Maximum Charge Power (kW)", "Maximum Discharge Power (kW)", "Overload Capability (%)",
    "Time Allowed for Overload (s)", "Ramping Rate (kW/min)", "Response Time (s)",
    "Nominal DC Voltage (kV)", "Nominal AC Voltage (kV)", "Nominal Frequency (Hz)",
    "Operating Frequency Range (Hz) Low", "Operating Frequency Range (Hz) High", "Number of Phases",
    "Full Load Efficiency (%)", "Standby Energy Consumption (kWh)",
    "Maximum Total Current Harmonic Distortion (%)", "Warranty Lifetime (years)",
})
