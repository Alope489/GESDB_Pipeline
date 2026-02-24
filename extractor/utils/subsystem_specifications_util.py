# utils/subsystem_specifications_util.py

def process_subsystem_specifications_tool(response):
    """
    Processes the LangChain response for the 'subsystem_specifications' tool,
    robust to optional sections being null and minor shape differences.
    """

    # --- helpers ---
    def _tool_calls(msg):
        try:
            return getattr(msg, "tool_calls", None) or []
        except Exception:
            return []

    def _as_dict(x):
        """Return a dict or {} if x is None/not a dict. If it's a pydantic model, call .dict()."""
        if x is None:
            return {}
        if isinstance(x, dict):
            return x
        # pydantic BaseModel-like
        to_dict = getattr(x, "dict", None)
        if callable(to_dict):
            try:
                return to_dict()
            except Exception:
                return {}
        return {}

    def _as_list(x):
        """Return a list or [] if x isn't a list."""
        return x if isinstance(x, list) else []

    # --- get args safely ---
    args = {}
    calls = _tool_calls(response)
    if calls:
        tc = calls[0]
        args = (tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}) or {})
    if not isinstance(args, dict):
        args = {}

    # payload can be under "subsystem_data" (expected), sometimes "subsystem_specifications",
    # or (rarely) args already is the payload.
    payload = args.get("subsystem_data")
    if not isinstance(payload, dict):
        payload = args.get("subsystem_specifications")
        if not isinstance(payload, dict):
            payload = args  # last resort

    payload = _as_dict(payload)

    # number of subsystems
    num_subsystems = payload.get("number_of_subsystems", None)

    # iterate subsystems
    details = []
    for raw_spec in _as_list(payload.get("subsystems")):
        spec = _as_dict(raw_spec)

        storage_device_specs = {
            "Broad Category": spec.get("broad_category"),
            "Mid Type": spec.get("mid_type"),
            "Sub Type": spec.get("sub_type"),
            "Round-trip Efficiency": spec.get("round_trip_efficiency"),
            "Depth of Discharge": spec.get("depth_of_discharge"),
            "Warranty Lifetime (cycles)": spec.get("warranty_lifetime_cycles"),
            "Warranty Lifetime (years)": spec.get("warranty_lifetime_years"),
            "Specific Energy": spec.get("specific_energy"),
            "Energy Density": spec.get("energy_density"),
            "Footprint": spec.get("footprint"),
            "Number of Cells": spec.get("number_of_cells"),
        }

        pcs_src = spec.get("power_conversion_system")
        pcs_dict = _as_dict(pcs_src)
        power_conversion_system = {
            "Maximum Charge Power": pcs_dict.get("max_charge_power"),
            "Maximum Discharge Power": pcs_dict.get("max_discharge_power"),
            "Overload Capability": pcs_dict.get("overload_capability"),
            "Time Allowed for Overload": pcs_dict.get("time_allowed_for_overload"),
            "Ramping Rate": pcs_dict.get("ramping_rate"),
            "Response Time": pcs_dict.get("response_time"),
            "Nominal DC Voltage": pcs_dict.get("nominal_dc_voltage"),
            "Nominal AC Voltage": pcs_dict.get("nominal_ac_voltage"),
            "Nominal Frequency": pcs_dict.get("nominal_frequency"),
            "Operating Frequency Range (Low)": pcs_dict.get("operating_frequency_range_low"),
            "Operating Frequency Range (High)": pcs_dict.get("operating_frequency_range_high"),
            "Number of Phases": pcs_dict.get("number_of_phases"),
            "Topology": pcs_dict.get("topology"),
            "Full Load Efficiency": pcs_dict.get("full_load_efficiency"),
            "Efficiency Degradation": pcs_dict.get("efficiency_degradation"),
            "Standby Energy Consumption": pcs_dict.get("standby_energy_consumption"),
            "Lagging Power Factor Range": pcs_dict.get("lagging_power_factor_range"),
            "Leading Power Factor Range": pcs_dict.get("leading_power_factor_range"),
            "Maximum Total Current Harmonic Distortion": pcs_dict.get("max_total_current_harmonic_distortion"),
            "Frequency Ride Through (FRT)": pcs_dict.get("frequency_ride_through"),
            "Low Voltage Ride Through (LVRT)": pcs_dict.get("low_voltage_ride_through"),
            "High Voltage Ride Through (HVRT)": pcs_dict.get("high_voltage_ride_through"),
            "Warranty Lifetime (years)": pcs_dict.get("warranty_lifetime_years_pcs"),
        }

        bos_src = spec.get("balance_of_system")
        bos_dict = _as_dict(bos_src)
        balance_of_system = {
            "Transformer Rating": bos_dict.get("transformer_rating"),
            "Transformer Configuration": bos_dict.get("transformer_configuration"),
            "Operating Temperature": bos_dict.get("operating_temperature"),
            "Communications": bos_dict.get("communications"),
            "Enclosures": bos_dict.get("enclosures"),
            "Controller Type": bos_dict.get("controller_type"),
        }

        details.append({
            "Storage Device Specifications": storage_device_specs,
            "Power Conversion System Specifications": power_conversion_system,
            "Balance of System Specifications": balance_of_system,
        })

    return {
        "Number of Subsystems": num_subsystems,
        "Subsystem Details": details,
    }
