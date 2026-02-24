"""Collection of validation functions for GESDB."""
from datetime import date
import datetime
import numpy as np
import pandas as pd
import validators
from .errorcodes import *

def is_date(date_string):
    """
    This function checks if the provided string is a date of format mm-dd-yyyy.

    Parameters
    ----------
    date_string : str
        A string possibly containing a date.

    Returns
    -------
    boolean_result : boolean
        A boolean value indicating whether the input string is a date or not.
    message: str
        A string giving description of the returned boolean result.
    """
    try:
        datetime.datetime.strptime(date_string, '%m-%d-%Y')
        boolean_result = True
        message = 'Data Type Match'
        return boolean_result, message
    except ValueError:
        boolean_result = False
        message = 'Incorrect data type or date NOT in format MM-DD-YYYY'
        return boolean_result, message


def validate_data_type(data, required, required_type):
    """
    This function checks whether the data from a GESDB field matches the
    required data type. Returns a tuple with validation status and a
    description.

    Parameters
    ----------
    data : Any
        GESDB field data to be checked.

    required : str
        Single character indicating whether the field is required or not
        according to the GESDB schema.

    required_type : str
        Required data type for the field being checked.This will be read from
        a CSV file describing the GESDB schema.

    Returns
    -------
    validation_status : str
        String indicating whether the field is Validated/Unvalidated/Empty

    description : str
        String that describes the validation error.
        
    error_codes : List
        A list of error codes.
    """

    # Convert data to string for some checking instances
    data_str = str(data)

    # Empty list to store error codes
    error_codes = []
    
    # ***** Check if 'data' is empty
    # - Empty data is specified as null in the json file. When read by pandas,
    # this is read in either as nan values or none values
    if (data_str.lower() == 'nan') | (data_str.lower() == 'none'):
        if required.upper() == 'R':
            # - If it empty but required
            error_codes.append(
                str(DataTypeErrors.CODE_MISSING_DATA_REQUIRED.value))
            return ('Unvalidated',
                    'Missing data - Entry is required for this field.',
                    error_codes)
        else:
            # - If it empty but optional
            error_codes.append(
                str(DataTypeErrors.CODE_MISSING_DATA_OPTIONAL.value))
            return ('Validated',
                    'Missing data - Data entry is OPTIONAL.',
                    error_codes)

    # ***** Checks to be performed if 'data' is non-empty
    if required_type.lower() == 'text':
        if isinstance(data, str):
            return ('Validated', 'Data Type Match.', error_codes)
        error_codes.append(
            str(DataTypeErrors.CODE_TEXT.value))
        return ('Unvalidated', 'Required data type is text.', error_codes)

    if required_type.lower() == 'integer':
        if isinstance(data, (int, np.int64)):
            return ('Validated', 'Data Type Match.', error_codes)
        error_codes.append(
            str(DataTypeErrors.CODE_INT.value))
        return ('Unvalidated', 'Required data type is integer.', error_codes)

    if required_type.lower() == 'float':
        if isinstance(data, (float, np.float64)):
            return ('Validated', 'Data Type Match.', error_codes)
        error_codes.append(
            str(DataTypeErrors.CODE_FLOAT.value))
        return ('Unvalidated', 'Required data type is float.', error_codes)

    if required_type.lower() == 'integer/float':
        if isinstance(data, (int, np.int64, float,  np.float64)):
            return ('Validated', 'Data Type Match.', error_codes)
        error_codes.append(
            str(DataTypeErrors.CODE_INT_FLOAT.value))
        return ('Unvalidated',
                'Required data type is either integer/float.',
                error_codes)

    if required_type.lower() == "date":
        (date_flag, _) = is_date(data_str)
        if date_flag == True:
            return ('Validated', 'Data Type Match.', error_codes)
        else:
            error_codes.append(
                str(DataTypeErrors.CODE_DATE.value))
            return ('Unvalidated', 
                    'Data is NOT in format MM:DD:YYYY.',
                    error_codes)


def validate_data_range(data, required, lower_range, upper_range):
    """
    This function checks whether the data from a GESDB field is within the
    specified 'lower_range' and 'upper_range'.

    Parameters
    ----------
    data : Any
        GESDB field data to be checked.

    lower_range : str
        Allowable lower range.

    upper_range : str
        Allowable upper range.

    Returns
    -------
    validation_status : str
        String indicating whether the field is Validated / Unvalidated.

    description : str
        String that describes the validation error.
        
    error_codes : List
        A list of error codes.
    """

    # Convert data to string for some checking instances
    data_str = str(data)
    
    # Empty list to store error codes
    error_codes = []

    # ***** Check if 'data' is empty
    # - Empty data is specified as null in the json file. When read by pandas,
    # this is read in either as nan values or none values
    if (data_str.lower() == 'nan') | (data_str.lower() == 'none'):
        if required.upper() == 'R':
            # - If it empty but required
            error_codes.append(
                str(DataRangeErrors.CODE_MISSING_DATA_REQUIRED.value))
            return ('Unvalidated',
                    'Missing data - Unable to validate data range.',
                    error_codes)
        else:
            # - If it empty but optional
            error_codes.append(
                str(DataRangeErrors.CODE_MISSING_DATA_OPTIONAL.value))
            return ('Validated', 
                    'Missing data - Data entry is OPTIONAL, Unable to validate data range.',
                    error_codes)
  
    is_validated = []
    description_builder = []

    # - check if the range is provided or not
    if (lower_range == "not applicable") & (upper_range == "not applicable"):
        description_builder. \
            append(" Both upper and lower range are"
                   " NOT provided and was not checked.")
        # ****** create the appropriate description
        description = "".join(description_builder)
        validation_status = "Validated"
        return validation_status, description, error_codes

    if upper_range.lower() == "not applicable":
        description_builder \
            .append(" Upper range is NOT provided and was not checked.")

    if lower_range.lower() == "not applicable":
        description_builder \
            .append(" Lower range is NOT provided and was not checked.")

    # ***** perform range checks for provided values
    if lower_range == ">0":
        # Cast data to numeric; if not numeric, skip range check
        # (datatype validator will catch it)
        try:
            data_num = float(data)
        except (TypeError, ValueError):
            data_num = None

        if data_num is not None and data_num <= 0:
            description_builder \
                .append(" Value for this field should be greater than 0.")
            is_validated.append(False)
            error_codes.append(
                str(DataRangeErrors.CODE_LOWER_RANGE_VIOLATION_1.value))

    # ***** checks to be performed if either the lower or upper range
    # is integer
    if lower_range.isnumeric() | upper_range.isnumeric():
        # Strip leading '>' from lower_range and upper_range if present
        if lower_range.startswith('>'):
            lower_range = lower_range[1:]  # Remove the '>'
        if upper_range.startswith('>'):
            upper_range = upper_range[1:]  # Remove the '>'
            
        # - check for lower range
        if int(data) < int(lower_range):
            description_builder \
                .append(" Value for this field should be greater than "
                        + lower_range)
            is_validated.append(False)
            error_codes.append(
                str(DataRangeErrors.CODE_LOWER_RANGE_VIOLATION_2.value))
        # - check for upper range
        if int(data) > int(upper_range):
            description_builder \
                .append(" Value for this field should be lower than "
                        + upper_range)
            is_validated.append(False)
            error_codes.append(
                str(DataRangeErrors.CODE_UPPER_RANGE_VIOLATION.value))

        # ***** checks if there a boolean False in 'is_validated' list
        if False in is_validated:
            validation_status = "Unvalidated"
        else:
            validation_status = "Validated"

        # ****** create the appropriate description
        description = "".join(description_builder)
        return validation_status, description, error_codes

    # ***** checks to be performed if either the lower or upper range is a
    # date
    (lower_range_date_flag, _) = is_date(lower_range)
    (upper_range_date_flag, _) = is_date(upper_range)
    if lower_range_date_flag | upper_range_date_flag:
        # - check for range
        lower_date_range = datetime.datetime.strptime(lower_range, '%m-%d-%Y')
        # - replace 'upper_range' with today's date
        today = date.today().strftime("%m-%d-%y")
        upper_date_range = datetime.datetime.strptime(today, '%m-%d-%y')
        date_entry = datetime.datetime.strptime(data, "%m-%d-%Y")
        if lower_date_range <= date_entry <= upper_date_range:
            is_validated.append(True)
        else:
            description_builder.append(
                "Value for this date field is NOT within valid range ({}, {})"
                .format(lower_date_range, upper_date_range))
            is_validated.append(False)
            error_codes.append(
                str(DataRangeErrors.CODE_DATA_RANGE_VIOLATION.value))

        # ***** checks if there a boolean False in 'is_validated' list
        if False in is_validated:
            validation_status = "Unvalidated"
        else:
            validation_status = "Validated"

        # ****** create the appropriate description
        description = "".join(description_builder)
        return validation_status, description, error_codes

    # ***** checks if there a boolean False in 'is_validated' list
    if False in is_validated:
        validation_status = "Unvalidated"
    else:
        validation_status = "Validated"

    # ****** create the appropriate description
    description = "".join(description_builder)
    return validation_status, description, error_codes


def validate_field_status(data):
    """
    Rules to validate the `Status` field in GESDB.
    
    Parameters
    ----------
    data : Any
        Data to validate.
        
    Returns
    -------
    result : str
        Validation result (Validated / Unvalidated).
    description : str
        Description providing more information about the result.
    error_codes : List
        A list of error codes.
    """

    # Valid values for the Status field are:
    # Offline/under repair; Under construction; Contracted;
    # Announced; Announced/never built; decomissioned/ de-comissioned; 
    # Under project development
    valid_status_values = ['offline/under repair', 'under construction', 
                           'contracted', 'announced', 'announced/never built',
                           'de-comissioned', 'decommisioned', 
                           'under project developement',
                           'operational']

    # Empty list to store error codes
    error_codes = []
    
    # Convert `data` to a string for easier processing
    data = str(data)
    
    if (data.lower() == 'nan') | (data.lower() == 'none'):
        result = 'Unvalidated'
        description = 'Status field is empty. This is a REQUIRED field.'
        error_codes.append(str(StatusFieldError.STATUS_EMPTY.value))
        return result, description, error_codes

    if data.lower() in valid_status_values:
        result = 'Validated'
        description = 'Status value is within the valid values of list.'
    else:
        result = 'Unvalidated'
        description = 'Status for this field is NOT in list of valid values.'
        error_codes.append(str(StatusFieldError.STATUS_INVALID.value))

    return result, description, error_codes


def validate_field_applications(data):
    """
    Rules to validate the `Applications` field in GESDB.
        
    Parameters
    ----------
    data : Any
        Data to validate.
                
    Returns
    -------
    result : str
        Validation result (Validated / Unvalidated).
    description : str
        Description providing more information about the result.
    error_codes : List
        A list of error codes.
    """
    
    # Modify this list as desired. Ideally should match the options that are
    # provided in the online GESDB project submission page
    valid_application_values = ['electric energy time shift (arbitrage)',
                                'electric supply capacity',
                                'voltage support', 'frequency regulation',
                                'frequency response', 'virtual inertia',
                                'operating reserve (spinning)',
                                'operating reserve (non-spinning)',
                                'operating reserve (supplementary)',
                                'renewable energy time shift', 'black start',
                                'renewable energy time shift (firming)',
                                'renewable energy time shift (smoothing)',
                                'ramp support', 'black start',
                                'transmission congestion relief',
                                'stability damping control',
                                'reliability',
                                'distribution upgrade deferral',
                                'transmission upgrade deferral',
                                'transmission upgrade relief',
                                'microgrid applications',
                                'retail tou energy charges',
                                'demand charge management',
                                'resilience (back-up power)',
                                'peak shaving',
                                'voltage regulation',
                                'demand charge and net metering management',
                                'power quality', 'resilience (back-up power)',
                                'transportation services']
    
    # Empty list to store error codes
    error_codes = []
    
    # Convert `data` to a string for easier processing
    data = str(data)
    if (data.lower() == 'nan') | (data.lower() == 'none'):
        result = 'Unvalidated'
        description = 'Application field is empty. This is a REQUIRED field.'
        error_codes.append(str(ApplicationsFieldError.APPLICATION_EMPTY.value))
        return result, description, error_codes

    if data.lower() in valid_application_values:
        result = 'Validated'
        description = 'Application is within the valid values of list.'
    else:
        result = 'Unvalidated'
        description = 'Application name is NOT in list of valid values.'
        error_codes.append(str(ApplicationsFieldError.APPLICATION_INVALID.value))
    return result, description, error_codes


def validate_field_url(data):
    """
    Rules to validate the `URL` field in GESDB. Currently only checks if the 
    URL is malformed. Does not actually check if the link works.
        
    Parameters
    ----------
    data : Any
        Data/URL to validate.
                
    Returns
    -------
    result : str
        Validation result (Validated / Unvalidated).
    description : str
        Description providing more information about the result.
    error_codes : List
        A list of error codes.
    """
    
    # Empty list to store error codes
    error_codes = []
    
    # Convert `data` to a string for easier processing
    data = str(data)
    
    # This is an optional field
    if (data.lower() == 'nan') | (data.lower() == 'none'):
        result = 'Validated'
        description = 'Application field is empty. This is an OPTIONAL field.'
        return result, description, error_codes
    
    if not validators.url(data):
        result = 'Unvalidated'
        description = 'The URL provided is possibly malformed.'
        error_codes.append(str(URLFieldError.URL_MALFORMED.value))
        return result, description, error_codes
    else:
        result = 'Validated'
        description = 'The URL provided is in the correct format.'
        return result, description, error_codes    


def validate_field_interconnection_level(data):
    """
    Rules to validate the `Grid Interconnection Level` field in GESDB.
    
    Parameters
    ----------
    data : Any
        Data to validate.
        
    Returns
    -------
    result : str
        Validation result (Validated / Unvalidated).
    description : str
        Description providing more information about the result.
    error_codes : List
        A list of error codes.
    """

    # Valid values for the Grid Interconnection Level field are:
    # Transmission; Distribution; Primary Distribution; Secondary Distribution
    valid_field_values = ['transmission', 
                           'distribution',
                           'primary distribution', 
                           'secondary distribution']

    # Empty list to store error codes
    error_codes = []
    
    # Convert `data` to a string for easier processing
    data = str(data)
    
    if (data.lower() == 'nan') | (data.lower() == 'none'):
        result = 'Unvalidated'
        description = 'Grid Interconnection Level field is empty, this is a REQUIRED field.'
        error_codes.append(str(GridInterConnectionLevelFieldError.GRID_INTERCONNECTION_LEVEL_EMPTY.value))
        return result, description, error_codes

    if data.lower() in valid_field_values:
        result = 'Validated'
        description = 'Grid interconnection level is within the valid values of list.'
    else:
        result = 'Unvalidated'
        description = 'Grid interconnection level is NOT in list of valid values.'
        error_codes.append(str(GridInterConnectionLevelFieldError.GRID_INTERCONNECTION_LEVEL_INVALID.value))

    return result, description, error_codes


def validate_field_tech_broad_category(data):
    """
    Rules to validate the `Technology Broad Category` field in GESDB.
    
    Parameters
    ----------
    data : Any
        Data to validate.
        
    Returns
    -------
    result : str
        Validation result (Validated / Unvalidated).
    description : str
        Description providing more information about the result.
    error_codes : List
        A list of error codes.
    """
    
    # Valid values for Technology Broad Category field are:
    # Electro-mechanical energy storage, 
    # Electro-chemical battery and chemical storage,
    # Thermal energy storage
    valid_field_values = ['electro-mechanical energy storage', 
                          'electro-chemical battery and chemical storage',
                          'thermal energy storage']

    # Empty list to store error codes
    error_codes = []
    
    # Convert `data` to a string for easier processing
    data = str(data)
    
    if (data.lower() == 'nan') | (data.lower() == 'none'):
        result = 'Unvalidated'
        description = 'Technology Broad Category field is empty, this is a REQUIRED field.'
        error_codes.append(str(TechBoardCategoryFieldError.TECH_BROAD_CATEGORY_EMPTY.value))
        return result, description, error_codes

    if data.lower() in valid_field_values:
        result = 'Validated'
        description = 'Technology broad category is within the valid values of list.'
    else:
        result = 'Unvalidated'
        description = 'Technology broad category is NOT in list of valid values.'
        error_codes.append(str(TechBoardCategoryFieldError.TECH_BROAD_CATEGORY_INVALID.value))

    return result, description, error_codes 


def validate_field_tech_mid_type(data, tech_broad_category):
    """
    Rules to validate the `Technology Mid Type` field in GESDB.
    
    Parameters
    ----------
    data : Any
        Data to validate.
    tech_broad_category: str
        Technology broad category for a specific data point in GESDB.
        
    Returns
    -------
    result : str
        Validation result (Validated / Unvalidated).
    description : str
        Description providing more information about the result.
    error_codes : List
        A list of error codes.
    """
    
    # Valid values for Technology Mid-Type separated by
    # Technology Broad Category field are:
    valid_field_values_elec_chem = ['lithium-ion battery',
                                    'flow battery',
                                    'lead-acid battery',
                                    'sodium-based battery',
                                    'nickel-based battery',
                                    'zinc-base battery',
                                    'hydrogen storage',
                                    'electro-chemical capacitor']
    valid_field_values_elec_mech = ['pumped hydro storage',
                                    'compressed air energy storage',
                                    'flywheel',
                                    'gravity storage']
    valid_field_values_thermal = ['sensible heat',
                                  'latent heat',
                                  'thermochemical heat']

    # Empty list to store error codes
    error_codes = []
    
    # Convert `data` to a string for easier processing
    data = str(data)
    
    if (data.lower() == 'nan') | (data.lower() == 'none'):
        result = 'Unvalidated'
        description = 'Technology Mid-Type field is empty, this is a REQUIRED field.'
        error_codes.append(str(TechMidTypeFieldError.TECH_MID_TYPE_EMPTY.value))
        return result, description, error_codes

    # -  Check for 'electro-chemical battery and chemical storage'
    if tech_broad_category.lower() == 'electro-chemical battery and chemical storage':
        if data.lower() in valid_field_values_elec_chem:
            result = 'Validated'
            description = 'Technology mid-type is within the valid values of list.'
        else:
            result = 'Unvalidated'
            description = 'Technology mid-type is NOT in list of valid values for broad category electro-chemical battery and chemical storage.'
            error_codes.append(str(TechMidTypeFieldError.TECH_MID_TYPE_INVALID_1.value))
    
    # - Check for 'electro-mechanical energy storage'
    if tech_broad_category.lower() == 'electro-mechanical energy storage':
        if data.lower() in valid_field_values_elec_mech:
            result = 'Validated'
            description = 'Technology mid-type is within the valid values of list.'
        else:
            result = 'Unvalidated'
            description = 'Technology mid-type is NOT in list of valid values for broad category electro-mechanical energy storage.'
            error_codes.append(str(TechMidTypeFieldError.TECH_MID_TYPE_INVALID_2.value))

    # Check for 'thermal energy storage'
    if tech_broad_category.lower() == 'thermal energy storage':
        if data.lower() in valid_field_values_thermal:
            result = 'Validated'
            description = 'Technology mid-type is within the valid values of list.'
        else:
            result = 'Unvalidated'
            description = 'Technology mid-type is NOT in list of valid values for broad category thermal energy storage.'
            error_codes.append(str(TechMidTypeFieldError.TECH_MID_TYPE_INVALID_3.value))

    return result, description, error_codes
 

def validate_capacity_to_power_ratio(data_rated_power,
                                     data_storage_capacity,
                                     discharge_hours,
                                     threshold_hours):
    """
    Checks to see if the ratio of `Storage Capacity` to `Rated Power` exceeds
    a the `threshold` hours. This will also check if the ratio of
    `Storage Capacity` to `Rated Power` is equal to the
    `Discharge duration at rated power`

    Parameters
    ----------
    data : Any
        Data to validate.
     discharge_hours : float
        Specified discharge duration in the GESDB.
    threshold_hours : float
        Maximum threshold for the ratio above which the data entry will be 
        deemed unvalidated.
        
    Returns
    -------
    warning_msg : str
        Warning message.
    error_codes : List
        A list of error codes.
    """

    def ratio_compute(capacity, power):
        try:
            return capacity/power
        except ZeroDivisionError:
            return 0

    error_codes = []
    description_builder = []

    # Check to see if the ratio of capacity to rated power is equal to
    # discharge_hours. This function does not produce any warning message for
    # case when both capacity and rated power is zero. This will be caught
    # by other validation rules.

    if ratio_compute(data_storage_capacity,data_rated_power) != discharge_hours:
        description_builder.append('Discharge duration should be equal to ratio of Storage Capacity to Rated Power.')
        error_codes.append(str(CapacityPowerRatioError.RATIO_NOT_EQUAL.value))
    
    if ratio_compute(data_storage_capacity,data_rated_power) > threshold_hours:
        description_builder.append(' The ratio of storage capacity to rated power is very high, validate the entries.')
        error_codes.append(str(CapacityPowerRatioError.RATIO_HIGH.value))

    # ****** create the appropriate description
    warning_msg = "".join(description_builder)
    return warning_msg, error_codes


def validate_dates(announced_date,
                   constructed_date,
                   commissioned_date,
                   decommissioned_date):
    """
    Rules to check the order of the dates.
    
    Parameters
    ----------
    announced_date : str
        Announced date of project.
    constructed_date : str
        Constructed date of project.
    commissioned_date : str
        Commissioned date of project.
    decommissioned_date : str
        Decommissioned date of project.
    
        
    Returns
    -------
    warning_msg : str
        Warning message.
    error_codes : List
        A list of error codes.
    """
    
    error_codes = []
    description_builder = []
    
    # ***** Convert non-empty strings to dates
    if announced_date is not None:
        a_date = datetime.datetime.strptime(announced_date, '%m-%d-%Y')
    if constructed_date is not None:
        c1_date = datetime.datetime.strptime(constructed_date, '%m-%d-%Y')
    if commissioned_date is not None:
        c2_date = datetime.datetime.strptime(commissioned_date, '%m-%d-%Y')
    if decommissioned_date is not None:
        d_date = datetime.datetime.strptime(decommissioned_date, '%m-%d-%Y')

    # ****** Check order of dates
    if (announced_date is not None) and (constructed_date is not None):
        if a_date > c1_date:
            description_builder.append('Constructed date cannot be earlier than announced date.')
            error_codes.append(str(DateError.C1_EARLIER_THAN_A.value))

    if (constructed_date is not None) and (commissioned_date is not None):
        if c1_date > c2_date:
            description_builder.append(' Commissioned date cannot be earlier than constructed date.')
            error_codes.append(str(DateError.C2_EARLIER_THAN_C1.value))

    if (commissioned_date is not None) and (decommissioned_date is not None):
        if c2_date > d_date:
            description_builder.append(' Decommissioned date cannot be earlier than commissioned date.')
            error_codes.append(str(DateError.D_EARLIER_THAN_C2.value))

    if (announced_date is not None) and (commissioned_date is not None):
        if a_date > c2_date:
            description_builder.append(' Commissioned date cannot be earlier than announced date.')
            error_codes.append(str(DateError.C2_EARLIER_THAN_A.value))
     
    if (announced_date is not None) and (decommissioned_date is not None):
        if a_date > d_date:
            description_builder.append(' Decommissioned date cannot be earlier than announced date.')
            error_codes.append(str(DateError.D_EARLIER_THAN_A.value))
   
    if (constructed_date is not None) and (decommissioned_date is not None):
        if c1_date > d_date:
            description_builder.append(' Decommissioned date cannot be earlier than constructed date.')
            error_codes.append(str(DateError.D_EARLIER_THAN_C1.value))

    # ****** create the appropriate description
    warning_msg = "".join(description_builder)
    return warning_msg, error_codes
   