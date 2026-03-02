""" Tests for the validation functions."""
import pytest
import datetime
import pandas as pd
from pathlib import Path
from datetime import date
from validation.validation_functions import validate_data_range
from validation.validation_functions import *
from validation.errorcodes import *

_TEST_DATA_JSON = Path(__file__).resolve().parent / "data" / "test_data.json"


def test_validate_data_range():
    """
    Test for `validate_data_range()` function.
    """

    # Load test data
    # Read the database test JSON file for testing purposes
    df_GESDB = pd.read_json(str(_TEST_DATA_JSON))

    # - assertion 1: both lower and upper range not provided
    des = validate_data_range(data=df_GESDB['Data Source'][1],
                              required='R',
                              lower_range='not applicable',
                              upper_range='not applicable')
    assert des == ('Validated',
                   ' Both upper and lower range are NOT provided and was not checked.',
                   [])

    # - assertion 2: lower range is >0 and upper range not provided
    des = validate_data_range(data=df_GESDB['Storage Capacity (kWh)'][0],
                              required='R',
                              lower_range='>0',
                              upper_range='not applicable')
    assert des == ('Unvalidated',
                   ' Upper range is NOT provided and was not checked.'
                   ' Value for this field should be greater than 0.',
                   [str(DataRangeErrors.CODE_LOWER_RANGE_VIOLATION_1.value)])

    # - assertion 3: lower OR upper range are numeric and data is wrong
    des = validate_data_range(data=0,
                              required='R',
                              lower_range='50',
                              upper_range='60')
    assert des == ('Unvalidated',
                   ' Value for this field should be greater than 50',
                   [str(DataRangeErrors.CODE_LOWER_RANGE_VIOLATION_2.value)])

    # - assertion 4: lower OR upper range are numeric and data is correct
    des = validate_data_range(data=60,
                              required='R',
                              lower_range='50',
                              upper_range='60')
    assert des == ('Validated', '', [])

    # - assertion 5: lower OR upper range are dates and data is out of range
    today = date.today().strftime("%m-%d-%y")
    upper_date_range = datetime.datetime.strptime(today, '%m-%d-%y')
    des = validate_data_range(data=df_GESDB['Constructed Date'][1],
                              required='R',
                              lower_range='1-1-1900',
                              upper_range=today)
    assert des == ('Unvalidated',
                   'Value for this date field is NOT within'
                   ' valid range (1900-01-01 00:00:00, ' + str(upper_date_range) + ')',
                   [str(DataRangeErrors.CODE_DATA_RANGE_VIOLATION.value)])

    # - assertion 6: lower OR upper range are dates and data is within range
    des = validate_data_range(data=df_GESDB['Commissioned Date'][0],
                              required='R',
                              lower_range='1-1-1900',
                              upper_range=today)
    assert des == ('Validated', '', [])

    # - assertion 7: data is 'null' in GESDB (will be read as None or Nan)
    des = validate_data_range(data=df_GESDB['Storage Capacity (kWh)'][1],
                              required='R',
                              lower_range='>0',
                              upper_range='not applicable')
    assert des == ('Unvalidated', 
                   'Missing data - Unable to validate data range.',
                   [str(DataRangeErrors.CODE_MISSING_DATA_REQUIRED.value)])


def test_validate_data_type():
    """
    Test for `validate_data_range()` function.
    """

    # Load test data
    # Read the database test JSON file for testing purposes
    df_GESDB = pd.read_json(str(_TEST_DATA_JSON))

    # - assertion 1: data is empty and required
    des = validate_data_type(data=df_GESDB['Project/Plant Name'][1],
                             required='R', required_type='Text')
    assert des == ('Unvalidated',
                   'Missing data - Entry is required for this field.',
                   [str(DataTypeErrors.CODE_MISSING_DATA_REQUIRED.value)])

    # - assertion 2: data is empty but optional
    des = validate_data_type(
        data=df_GESDB['Discharge Duration at Rated Power (hrs)'][1],
        required='O', required_type='Integer/Float')
    assert des == ('Validated',
                   'Missing data - Data entry is OPTIONAL.',
                   [str(DataTypeErrors.CODE_MISSING_DATA_OPTIONAL.value)])

    # - assertion 3: req data type is text and actual data is also text
    des = validate_data_type(data=df_GESDB['Status'][0],
                             required='R', required_type='Text')
    assert des == ('Validated', 'Data Type Match.', [])

    # - assertion 4: req data type is integer and actual data is also integer
    des = validate_data_type(data=df_GESDB['Number of Subsystems'][0],
                             required='R', required_type='Integer')
    assert des == ('Validated', 'Data Type Match.', [])

    # - assertion 5: req data type is float and actual data is also float
    des = validate_data_type(data=df_GESDB['Latitude'][0],
                             required='O', required_type='Float')
    assert des == ('Validated', 'Data Type Match.', [])

    # - assertion 6: req data type is int/float and actual data is
    # also int/float
    des = validate_data_type(data=df_GESDB['Rated Power (kW)'][0],
                             required='R', required_type='Integer/Float')
    assert des == ('Validated', 'Data Type Match.', [])

    # - assertion 7: req data type is date and actual data is also date
    des = validate_data_type(data=df_GESDB['Commissioned Date'][0],
                             required='R', required_type='Date')
    assert des == ('Validated', 'Data Type Match.', [])

    # - assertion 8: req data type is date and actual data is also date but
    # NOT in format MM:DD:YYYY
    des = validate_data_type(
        data=df_GESDB['Commissioned Date'][1],
        required='R', required_type='Date')
    assert des == ('Unvalidated', 'Data is NOT in format MM:DD:YYYY.',
                   [str(DataTypeErrors.CODE_DATE.value)])

    # - assertion 9: req data type is text and actual data is NOT text
    des = validate_data_type(
        data=df_GESDB['Status'][1],
        required='R', required_type='Text')
    assert des == ('Unvalidated', 'Required data type is text.',
                   [str(DataTypeErrors.CODE_TEXT.value)])

    # - assertion 10: req data type is integer and actual data NOT integer
    des = validate_data_type(
        data=df_GESDB['Utility ID'][1],
        required='O', required_type='Integer')
    assert des == ('Unvalidated', 'Required data type is integer.',
                   [str(DataTypeErrors.CODE_INT.value)])

    # - assertion 11: req data type is float and actual data is NOT float
    des = validate_data_type(
        data=df_GESDB['Latitude'][1],
        required='O', required_type='Float')
    assert des == ('Unvalidated', 'Required data type is float.',
                   [str(DataTypeErrors.CODE_FLOAT.value)])

    # - assertion 12: req data type is int/float and actual data is
    # NOT int/float
    des = validate_data_type(df_GESDB['Rated Power (kW)'][1],
                             required='R', required_type='Integer/Float')
    assert des == (
        'Unvalidated', 'Required data type is either integer/float.',
        [str(DataTypeErrors.CODE_INT_FLOAT.value)])

    # - assertion 13: req data type is date and actual data is NOT date
    des = validate_data_type(df_GESDB['Announced Date'][1],
                             required='O', required_type='Date')
    assert des == ('Unvalidated', 'Data is NOT in format MM:DD:YYYY.',
                   [str(DataTypeErrors.CODE_DATE.value)])


def test_validate_field_status():
    """
    Test for `validate_field_status()` function.
    """

    # Load test data
    # Read the database test JSON file for testing purposes
    df_GESDB = pd.read_json(r'validation/data/test_data.json')

    # - assertion 1: `Status` field is empty but REQUIRED
    des = validate_field_status(df_GESDB['Status'][2])

    assert des == ('Unvalidated',
                   'Status field is empty. This is a REQUIRED field.',
                   [str(StatusFieldError.STATUS_EMPTY.value)])

    # - assertion 2: `Status` field is Invalid
    des = validate_field_status(df_GESDB['Status'][1])

    assert des == ('Unvalidated',
                   'Status for this field is NOT in list of valid values.',
                   [str(StatusFieldError.STATUS_INVALID.value)])

    # - assertion 3: `Status` field is valid
    des = validate_field_status(df_GESDB['Status'][0])

    assert des == ('Validated',
                   'Status value is within the valid values of list.',
                   [])