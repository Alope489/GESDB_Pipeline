"""Defines errors codes through enumerations"""
import enum


@enum.unique
class DataTypeErrors(enum.Enum):
    """Data Type error code enumerations."""
    #: Msg: Missing data - Entry is required for this field.
    CODE_MISSING_DATA_REQUIRED = 101
    #: Msg: Missing data - Data entry is OPTIONAL
    CODE_MISSING_DATA_OPTIONAL = 102
    #: Msg: Required data type is text
    CODE_TEXT = 103
    #: Msg: Required data type is integer
    CODE_INT = 104
    #: Msg: Required data type is float
    CODE_FLOAT = 105
    #: Msg: Required data type is either integer/float
    CODE_INT_FLOAT = 106
    #: Msg: Data is NOT in format MM:DD:YYYY
    CODE_DATE = 107
    #: Msg: Data type mismatch
    CODE_DATA_TYPE_MISMATCH_GENERIC = 108
    
    # def __str__(self):
    #     return str(self.value)


@enum.unique
class DataRangeErrors(enum.Enum):
    """Data Range error code enumerations."""
    #: Msg: Missing data - Unable to validate data range.
    CODE_MISSING_DATA_REQUIRED = 201
    #: Msg: Missing data - Data entry is OPTIONAL,
    # Unable to validate data range
    CODE_MISSING_DATA_OPTIONAL = 202
    #: Msg: Value for this field should be greater than 0
    CODE_LOWER_RANGE_VIOLATION_1 = 203
    #: Msg: Value for this field should be greater than `lower_range`
    CODE_LOWER_RANGE_VIOLATION_2 = 204
    #: Msg: Value for this field should be lower than `upper_range`
    CODE_UPPER_RANGE_VIOLATION = 205
    #: Msg: Value for this date field is NOT within
    # valid range (lower_data, upper_data)
    CODE_DATA_RANGE_VIOLATION = 206
    
    # def __str__(self):
    #     return str(self.value)


@enum.unique
class StatusFieldError(enum.Enum):
    """Status field error code enumerations."""
    #: Msg: Status field is empty. This is a required field.
    STATUS_EMPTY = 301
    #: Msg: Status for this field is NOT in the valid value of list.
    STATUS_INVALID = 302


@enum.unique
class ApplicationsFieldError(enum.Enum):
    """Applications field error code enumerations.."""
    #: Msg: All applications field are empty.
    # At least one application is required per projects.
    APPLICATION_EMPTY = 701
    #: Msg: At least one of the values in the applications field
    # is NOT in the valid value of list.
    APPLICATION_INVALID = 702


@enum.unique
class URLFieldError(enum.Enum):
    """URL field error code enumerations.."""
    #: Msg: The URL provided is possibly malformed.
    URL_MALFORMED = 1001


@enum.unique
class GridInterConnectionLevelFieldError(enum.Enum):
    """Grid Interconnection Level field error code enumerations."""
    #: Msg: Grid Interconnection Level field is empty,
    # this is a REQUIRED field.
    GRID_INTERCONNECTION_LEVEL_EMPTY = 2501
    #: Msg: Grid interconnection level for this field is NOT
    # in the list of valid values.
    GRID_INTERCONNECTION_LEVEL_INVALID = 2502
  

@enum.unique
class TechBoardCategoryFieldError(enum.Enum):
    """Technology Board Category field error code enumerations."""
    #: Msg: Technology Board Category field is empty,
    # this is a REQUIRED field.
    TECH_BROAD_CATEGORY_EMPTY = 6401
    #: Msg: Technology Board Category for this field is NOT
    # in the list of valid values.
    TECH_BROAD_CATEGORY_INVALID = 6402


@enum.unique
class TechMidTypeFieldError(enum.Enum):
    """Technology Mid Type field error code enumerations."""
    #: Msg: Technology Mid Type field is empty,
    # this is a REQUIRED field.
    TECH_MID_TYPE_EMPTY = 6501
    #: Msg: Technology mid-type is NOT in list of valid values for broad 
    # category electro-chemical battery and chemical storage
    TECH_MID_TYPE_INVALID_1 = 6502
    #: Msg: Technology mid-type is NOT in list of valid values for broad 
    # category electro-mechanical energy storage.
    TECH_MID_TYPE_INVALID_2 = 6503
    #: Msg: Technology mid-type is NOT in list of valid values for broad 
    # category thermal energy storage.
    TECH_MID_TYPE_INVALID_3 = 6504
    

@enum.unique
class CapacityPowerRatioError(enum.Enum):
    """Capacity to power ratio error code enumerations."""
    #: Msg: Discharge duration should be equal to ratio of 
    # Storage Capacity to Rated Power
    RATIO_NOT_EQUAL = 20001
    #: Msg: The ratio of storage capacity to rated power is very high, 
    # validate the entries
    RATIO_HIGH = 20002


@enum.unique
class DateError(enum.Enum):
    """Date error code enumerations."""
    #: Msg: Constructed date cannot be earlier than announced date.
    C1_EARLIER_THAN_A = 30001
    #: Msg: Commissioned date cannot be earlier than constructed date.
    C2_EARLIER_THAN_C1 = 30002
    #: Msg: Decommissioned date cannot be earlier than commissioned date.
    D_EARLIER_THAN_C2 = 30003
    #: Msg: Commissioned date cannot be earlier than announced date.
    C2_EARLIER_THAN_A = 30004
    #: Msg: Decommissioned date cannot be earlier than announced date.
    D_EARLIER_THAN_A = 30005
    #: Msg: Decommissioned date cannot be earlier than constructed date.
    D_EARLIER_THAN_C1 = 30006