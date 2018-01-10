import re
import logging

class Invalid:
    def __init__(self, val):
        self.log_info = val

def id_picker(row, idIndexes):
    '''
    expects a list of values, 2 of which are ids
    returns a pair of ids
    '''
    id_set = [ None ] * len(idIndexes)
    try:
        for rem, loc in idIndexes.items():
            id_set[loc] = row[rem]
        return tuple(id_set)
    except:
    	return Invalid(row)

def validate_shortid(pair, shortIdx):
    try:
        assert re.match('^[a-z0-9]{2,10}$', pair[shortIdx])
        return pair
    except:
        new_pair = [ i for i in pair ]
        new_pair[shortIdx] = None
        return tuple(new_pair)

def validate_bruid(row, bruIdx):
    try:
        assert re.match('^[0-9]{9}$', row[bruIdx])
        return row
    except:
        return Invalid(row[bruIdx])


def update_id_map(rows, fisIndexes, existingMap):
    id_idx = { 'BRUID': 0, 'SHORTID': 1 }

    mapped_idx = { fisIndexes[k]: v for k,v in id_idx.items() }
    pairs = [ id_picker(row, mapped_idx) for row in rows ]
    for invld in pairs:
        if isinstance(invld, Invalid):
            logging.info(
                'No IDs at specified indexes: {}'.format(invld.log_info) )
    
    good_ids= [ pair for pair in pairs if not isinstance(pair, Invalid) ]
    checked_bruids = [ validate_bruid(pair, id_idx['BRUID'])
                        for pair in good_ids ]
    for invld in checked_bruids:
        if isinstance(invld, Invalid):
            logging.info( 'Bad bruid: {}'.format(invld.log_info) )
    
    valid_bruids= [ pair for pair in checked_bruids
                        if not isinstance(pair, Invalid) ]
    checked_shortids = [ validate_shortid(pair, id_idx['SHORTID'])
                            for pair in valid_bruids ]
    future_id_map = { bru: short for bru, short in checked_shortids
                        if short is not None }
    bru_without_short = [ pair[id_idx['BRUID']] for pair in checked_shortids
                            if pair[id_idx['SHORTID']] is None ]
    looked_up = { bru: existingMap.get( bru, None )
                    for bru in bru_without_short }
    future_id_map.update(looked_up)

    changed_shortids = [ bru for bru, short in future_id_map.items()
        if bru in existingMap and existingMap[bru] != short ]
    for bru in changed_shortids:
        logging.warning(
            'ShortID changed from {0} to {1} for bruid {2}'.format(
                existingMap[bru], future_id_map[bru], bru)
            )
        del future_id_map[bru]

    return future_id_map