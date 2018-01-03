#Modules
##PSL
import os
import json
import csv
##Local
import prep
#Globals
##PSL
import logging
##Local
from config.development import config as cfg

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

def process_feed(dataType, lookup=False):
    file_name = "FIS_to_VIVO_{0}.csv".format(dataType)
    incoming_path = os.path.join(cfg['DATA_DIR'], file_name)
    outgoing_path = os.path.join(cfg['PREPPED_DIR'], file_name)
    id_map_path = os.path.join(cfg['DATA_DIR'], 'id_map.json')

    data_rows = read_rows(incoming_path)
    cleaned_rows = prep.clean_fis_feed.process(
        dataType, data_rows, logger)

    if lookup:
        id_map = prep.shortid_lookup.process(cleaned_rows, {}, logger)
        with open(id_map_path, 'w') as f:      
            json.dump(id_map, f, sort_keys=True, indent=4)
    else:
        with open(id_map_path, 'r') as f:      
            id_map = json.load(f)

    prepped_rows = prep.add_shortids.process(
        dataType, cleaned_rows, id_map, logger)
    success = write_rows(outgoing_path, prepped_rows)
    return success

def main():
	walk_generator = os.walk(cfg['FIS_DATA_DIR'])
	data_dir, empty_list, data_files = next(walk_generator)
	try:
		assert sorted(data_files) == sorted(cfg['DATA_FILES'])
	except:
		logger.error('Error in FIS feed files. Exiting')
		return

    faculty_success = process_feed('faculty', lookup=True)
    assert faculty_success == True
    appointments_success = process_feed('appointments')
    assert appointments_success == True
    degrees_success = process_feed('degrees')
    assert degrees_success == True

if __name__ == '__main__':
	main()
