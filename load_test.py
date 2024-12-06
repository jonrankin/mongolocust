import logging
from locust import between
from mongo_user import MongoUser, mongodb_task
from settings import DEFAULTS
import pymongo
import random
from bson import ObjectId
# Number of cache entries for queries
NAMES_TO_CACHE = 2000000

# Configure root logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure Locust logger
logger = logging.getLogger("locust")
logger.setLevel(logging.INFO)

class MongoSampleUser(MongoUser):
    """
    Generic sample mongodb workload generator
    """
    # No delays between operations
    wait_time = between(0.0, 0.0)

    def __init__(self, environment):
        super().__init__(environment)
        self.name_cache = []

    def generate_new_document(self):
        """
        Generate a new sample document
        """
        document = {
            '_id': ObjectId(),
            'id2': self.faker.pystr(min_chars=50, max_chars=100),
            'id3': self.faker.pystr(min_chars=50, max_chars=100),
            'payload': self.faker.pystr(min_chars=3710, max_chars=3710)
        }
        return document

    def on_start(self):
        """
        Executed every time a new test is started - place init code here
        """
        # Prepare the collection
        # index1 = pymongo.IndexModel([('id1', pymongo.ASCENDING)], name="id1_asc")
        self.collection, self.collection_secondary = self.ensure_collection(DEFAULTS['COLLECTION_NAME'])
        if len(self.name_cache) < NAMES_TO_CACHE:        
            cursor = self.collection.aggregate([ 
                { '$sample': { 'size':  125000 } }
            ])
            self.name_cache.extend(list(cursor))
        

    @mongodb_task(weight=int(DEFAULTS['INSERT_WEIGHT']))
    def insert_single_document(self):
        document = self.generate_new_document()

        # #cache the ids
        # cached_names = {
        #     'id1': document['id1'],
        #     'id2': document['id2'],
        #     'id3': document['id3']
        # }
        # if len(self.name_cache) < NAMES_TO_CACHE:
        #     self.name_cache.append(cached_names)
        # else:
        #     if random.randint(0, 9) == 0:
        #         self.name_cache[random.randint(0, len(self.name_cache) - 1)] = cached_names

        self.collection.insert_one(document)

    @mongodb_task(weight=int(DEFAULTS['FIND_WEIGHT']))
    def find_document(self):
        # At least one insert needs to happen
        if not self.name_cache:
            return

        # Find a random document using an index
        cached_name = random.choice(self.name_cache)
        findOne = self.collection.find_one({'_id': cached_name["_id"]})
        if findOne:
            print(findOne)
    # @mongodb_task(weight=int(DEFAULTS['BULK_INSERT_WEIGHT']), batch_size=int(DEFAULTS['DOCS_PER_BATCH']))
    # def insert_documents_bulk(self):
    #     self.collection.insert_many(
    #         [self.generate_new_document() for _ in range(int(DEFAULTS['DOCS_PER_BATCH']))])
