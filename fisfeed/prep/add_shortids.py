import sys
import os
import csv
import re
import collections
# from config.development import config

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

class BruidFailure(str):
    def __new__(cls, val):
        return super().__new__(cls, val)

class LookupFailure(str):
    def __new__(cls, val):
        return super().__new__(cls, val)

def bruid_check(row, bruidIdx):
    try:
        assert re.match('[0-9]{9}', row[bruidIdx])
        return [ d for d in row ]
    except:
        return BruidFailure(row[bruidIdx])

def overwrite_bruid(row, bruidIdx, idMap):
    bruid = row[bruidIdx]
    try:
        ovrwrtn = [ r for r in row ]
        ovrwrtn[bruidIdx] =  idMap[bruid]
        return ovrwrtn
    except:
        return LookupFailure(bruid)

def process(dataType, rows, idMap, logger,cfg):
    bruid_idx = cfg['FIS_BRUID_INDEX'][dataType]
    checked = [ bruid_check(row, bruid_idx) for row in rows ]
    print(checked[:10])
    garbled = [ row for row in checked if isinstance(row, BruidFailure) ]
    for row in garbled:
        logger.warn("Bad bruid: {}".format(row))
    subbed = [ overwrite_bruid(row, bruid_idx, idMap)
                for row in checked if not isinstance(row, BruidFailure) ]
    print(subbed[:10])
    failed = [ row for row in subbed if isinstance(row, LookupFailure) ]
    mapped = [ row for row in subbed if not isinstance(row, LookupFailure) ]
    for row in failed:
        logger.warn("No matching shortid for {}".format(row))
    return mapped


if __name__ == "__main__":
    fis_type_map = {
        'FIS_to_VIVO_faculty.csv' : 'faculty',
        'FIS_to_VIVO_appointments.csv' : 'appointments',
        'FIS_to_VIVO_degrees.csv' : 'degrees',
    }

    file_path = sys.argv[1]
    target_dir = sys.argv[2]
    id_map = sys.argv[3]
    
    file_name = os.path.split(file_path)[1]
    fis_type = fis_type_map[file_name]
    logger = Logger()
    with open(file_path, 'r') as f:
        row_iter = csv.reader(f)
        out = process(fis_type, row_iter, id_map, logger)    

    with open(target_dir + file_name, 'w') as t:
        wrtr = csv.writer(t)
        for row in out:
            wrtr.writerow(row)

    print(logger._log)