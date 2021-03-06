import ldap3
import json
import time
import sys
import csv
import argparse
# from config.development import config


class Logger:
    def __init__(self):
        self._log = ""

    def info(self, msg):
        self._log += '[INFO] ' + msg + '\n'

    def error(self, msg):
        self._log += '[ERROR] ' + msg + '\n'

class MappedID(tuple):
    def __new__(cls, iterable):
        return super().__new__(cls, iterable)

class LookupFailure(str):
    def __new__(cls, val):
        return super().__new__(cls, val)

class LdapClient:
    def __init__(self, cfg):
        self.sleeper = cfg['LDAP_THROTTLE']
        self.server_addr = cfg['LDAP_SERVER']
        self.user = cfg['LDAP_USER']
        self.passw = cfg['LDAP_PASSWORD']
        self.user_grp = cfg['LDAP_USERGROUP']
        self.server = ldap3.Server(self.server_addr)
        self.conn = ldap3.Connection(
            self.server,
            'cn={0},ou={1},dc=brown,dc=edu'.format(
                self.user, self.user_grp),
            self.passw, auto_bind=True)

    def search_bruids(self, bruids):
        formatted = [ '(brownbruid={0})'.format(b) for b in bruids ]
        chunked = chunk_list(formatted, 100)
        ldap_data = []
        for chunk in chunked:
            time.sleep(self.sleeper)
            print('Querying')
            or_str = '(|{0})'.format(''.join(chunk))
            resp = self.conn.search('ou=people,dc=brown,dc=edu',
                        or_str,
                        attributes=['brownbruid','brownshortid'])
            if resp == True:
                entries = [ json.loads( e.entry_to_json() )
                            for e in self.conn.entries ]
                ldap_data.extend(entries)
            else:
                continue
        return ldap_data

    def close(self):
        self.conn.unbind()

def merge_maps(map1, map2):
    merged = map1.copy()
    merged.update(map2)
    return merged

def chunk_list(lst, size):
    chunked = []
    for i in range(0, len(lst), size):
        chunked.append( lst[i:i + size] )
    return chunked

def get_ldap_attrs(ldapDict):
    try:
        return MappedID(
            [ ldapDict['attributes']['brownbruid'][0],
            ldapDict['attributes']['brownshortid'][0] ])
    except:
        return LookupFailure(ldapDict['attributes']['brownbruid'][0])

def log_map_changes(oldMap, newMap, logger):
    diff = { k: v for k,v in oldMap.items() if k in newMap and v != newMap[k] }
    for k,v in diff.items():
        logger.error(
            "{0}: shortid updated from {1} to {2}".format(k,v,newMap[k]))

def process(dataType, rows, mappedIDs, logger, cfg):
    bruid_list = [ row[ cfg['FIS_BRUID_INDEX'][dataType] ]
                    for row in rows ]
    unknowns = [ b for b in bruid_list if b not in mappedIDs ]
    if unknowns == []:
        logger.info('No new IDs. Returning')
        return
    try:
        client = LdapClient(cfg)
        ldap_data = client.search_bruids(unknowns)
        client.close()
    except:
        logger.error("LDAP failure")
        return
    results = [ get_ldap_attrs(entry) for entry in ldap_data ]
    new_ids = [ m for m in results if isinstance(m, MappedID) ]
    failed = [ f for f in results if isinstance(f, LookupFailure) ]
    for n in new_ids:
        logger.info('Adding new id for: ' + n[0])
    for f in failed:
        logger.error('LDAP failed to return shortid for: ' + f)
    new_shortid_map = { n[0]: n[1] for n in new_ids }
    missing = [ u for u in unknowns if u not in new_shortid_map ]
    for m in missing:
        logger.error('BRUID missing in lookup map: ' + m)
    merged_map = merge_maps(mappedIDs, new_shortid_map)
    return merged_map

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        description='Lookup faculty IDs in LDAP')
    parser.add_argument('id_source', action="store")
    parser.add_argument('id_map', action="store")
    parser.add_argument('-o','--overwrite', action="store_true")
    parser.add_argument('-u','--update', action="store_true")
    parser.add_argument('-c','--changelog', action="store_true")
    args = parser.parse_args()
    logger = Logger()

    with open(args.id_source, 'r') as sourceFile:
        rdr = csv.reader(sourceFile)
        bruid_list = [ row[1] for row in rdr ]
    with open(args.id_map, 'r') as mapFile:
        id_map = json.load(mapFile)

    if args.overwrite == True:
        new_map = process(bruid_list, {}, logger)
    if args.update == True:
        new_map = process(bruid_list, id_map, logger)

    if args.changelog == True: 
        log_map_changes(id_map, new_map, logger)
    if new_map == None:
        new_map = id_map
    with open(args.id_map, 'w') as mapFile:
        json.dump(new_map, mapFile, sort_keys=True, indent=4)

    print(logger.log)