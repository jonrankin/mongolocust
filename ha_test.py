import os
import time
import datetime
import pymongo
from settings import DEFAULTS
import sys 

DB_NAME = 'AUTO_HA'
TTL_INDEX_NAME = 'date_created_ttl_index'


####
# Main start function
####
def main():
    print('')
    peform_inserts(DEFAULTS['CLUSTER_URL'], True)

def peform_inserts(uri, retry):
    mongodb_url = uri
    print(f'Connecting to:\n {mongodb_url}\n')
    connection = pymongo.MongoClient(mongodb_url, retryWrites=retry, retryReads=retry)
    db = connection[DEFAULTS['DB_NAME']]
    db.records.drop()
    db.records.create_index([('val', pymongo.DESCENDING)])
    db.records.create_index('date_created', name=TTL_INDEX_NAME, expireAfterSeconds=7200)
    print('Ensured there is a TTL index to prune records after 2 hours\n')
    print('Inserting records continuously...')
    connect_problem = False
    count = 0

    while True:
        try:            
            count += 1

            db.records.insert_one({
                'val': count,
                'date_created': datetime.datetime.now(datetime.UTC)
            })

            if (count % 30 == 0):
                print(f'{datetime.datetime.now()} - INSERTED TILL {count}')            

            if (connect_problem):
                print(f'{datetime.datetime.now()} - RECONNECTED-TO-DB')
                connect_problem = False
            else:
                time.sleep(0.01)
        except KeyboardInterrupt:
            print
            sys.exit(0)
        except Exception as e:
            print(f'{datetime.datetime.now()} - DB-CONNECTION-PROBLEM: '
                  f'{str(e)}')
            connect_problem = True
####
# Main
####
if __name__ == '__main__':
    main()