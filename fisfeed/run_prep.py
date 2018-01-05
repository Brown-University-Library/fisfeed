#Modules
##PSL
import os
import json
import csv
##Local
from prep import clean_fis_feed, shortid_lookup, add_shortids
#Globals
##PSL
import logging
##Local
from config.development import config as cfg

class Logger:
    def __init__(self):
        self._log = ''

    def info(self, msg):
        self._log += '[INFO] ' + msg + '\n'

    def error(self, msg):
        self._log += '[ERROR] ' + msg + '\n'

    def warn(self, msg):
        self._log += '[WARNING] ' + msg + '\n'

def read_rows(fileName):
    with open(fileName, 'r') as f:
        rdr = csv.reader(f)
        rows = [ row for row in rdr ]
    return rows

def write_rows(fileName, rows):
    with open(fileName, 'w') as f:
        wrtr = csv.writer(f)
        for row in rows:
            wrtr.writerow(row)
    return True

def process_feed(dataType, logger, lookup=False):
    file_name = 'FIS_to_VIVO_{0}.csv'.format(dataType)
    incoming_path = os.path.join(cfg['FIS_DATA_DIR'], file_name)
    outgoing_path = os.path.join(cfg['PREPPED_DATA_DIR'], file_name)
    id_map_path = os.path.join(cfg['DATA_DIR'], 'id_map.json')

    data_rows = read_rows(incoming_path)
    cleaned_rows = clean_fis_feed.process(
        dataType, data_rows, logger, cfg)

    if lookup:
        id_map = shortid_lookup.process(
            dataType, cleaned_rows, {}, logger, cfg)
        with open(id_map_path, 'w') as f:      
            json.dump(id_map, f, sort_keys=True, indent=4)
    else:
        with open(id_map_path, 'r') as f:      
            id_map = json.load(f)

    prepped_rows = add_shortids.process(
        dataType, cleaned_rows, id_map, logger, cfg)
    success = write_rows(outgoing_path, prepped_rows)
    return success

def main():
    logger = Logger()
    walk_generator = os.walk(cfg['FIS_DATA_DIR'])
    data_dir, empty_list, data_files = next(walk_generator)
    try:
        assert sorted(data_files) == sorted(cfg['FIS_DATA_FILES'])
    except:
        logger.error('Error in FIS feed files. Exiting')
        return

    faculty_success = process_feed('faculty', logger, lookup=True)
    assert faculty_success == True
    appointments_success = process_feed('appointments', logger)
    assert appointments_success == True
    degrees_success = process_feed('degrees', logger)
    assert degrees_success == True

    # print(logger._log)

if __name__ == '__main__':
	main()
