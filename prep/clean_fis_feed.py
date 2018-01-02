import sys
import os
import csv
import re
import collections
from config.development import config

class Logger:
    def __init__(self):
        self._log = ''

    def error(self, msg):
        self._log += '[ERROR] ' + msg

    def warn(self, msg):
        self._log += '[WARNING] ' + msg

class Row(tuple):
    def __new__(cls, iterable):
        return super().__new__(cls, iterable)

class Invalid:
    def __init__(self, line, func):
        self.error = "{0}: fails {1}".format(line, func.__name__)

def validate(func, lineNumber, row, *args):
    try:
        return Row(func(row, *args))
    except:
        return Invalid(lineNumber, func)

def strip_whitespace(row):
    return [ d.replace('\n', '').replace('\r', '') for d in row ]

def nonify(row):
    return [ None if d == '' else d for d in row ]

def unicodify(row):
    return [ str(d) for d in row ]

def bruid_check(row):
    assert re.match('[0-9]{9}', row[1])
    return [ d for d in row ]

def header_check(head_row, fis_type):
    header_template = config['FIS_HEADERS']
    assert head_row == header_template[fis_type]
    return [ d for d in head_row ]

def validate_data(rows):
    validators = [ unicodify, strip_whitespace, nonify, bruid_check ]
    for func in validators:
        rows = [ validate(func, line_num, row) for line_num, row
                    in enumerate(rows) ]
    return rows

def process(fis_type, rowIter, logger):
    header = next(rowIter)
    checked_head = validate(header_check, 0, Row(header), fis_type)
    if isinstance(checked_head, Invalid):
        logger.error(checked_head.error)
        return []
    validated = validate_data(rowIter)
    invalid = [ row for row in validated if isinstance(row, Invalid) ]
    valid = [ row for row in validated if not isinstance(row, Invalid) ]
    for row in invalid:
        logger.warn(row.error)
    # out = [ checked_head ] + valid
    return valid


if __name__ == "__main__":
    fis_type_map = {
        'FIS_to_VIVO_faculty.csv' : 'faculty',
        'FIS_to_VIVO_appointments.csv' : 'appointments',
        'FIS_to_VIVO_degrees.csv' : 'degrees',
    }

    file_path = sys.argv[1]
    target_dir = sys.argv[2]
    file_name = os.path.split(file_path)[1]
    fis_type = fis_type_map[file_name]
    logger = Logger()
    with open(file_path, 'r') as f:
        row_iter = csv.reader(f)
        out = process(fis_type, row_iter, logger)    

    with open(target_dir + file_name, 'w') as t:
        wrtr = csv.writer(t)
        for row in out:
            wrtr.writerow(row)

    print(logger._log)