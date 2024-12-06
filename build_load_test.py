#!/usr/bin/env python

import gevent
_ = gevent.monkey.patch_all()

import pymongo
from bson import json_util, ObjectId, Decimal128
from locust import User, events, task, constant, tag, between, runners
import time
import uuid
from pickle import TRUE
import datetime
from datetime import timedelta
import random
from decimal import Decimal
from itertools import product
from queue import Queue
from mimesis import Field, Fieldset, Schema
from mimesis.enums import Gender, TimestampFormat
from mimesis.locales import Locale

# Global vars
_WORKER_ID = None
_CLIENT = None
_SRV = None
_HOST = None
_SHOULD_INIT_QUEUE = True
_QUEUE = Queue()  # Global queue

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    global _WORKER_ID, _SHOULD_INIT_QUEUE, _QUEUE
    if not isinstance(environment.runner, runners.MasterRunner):
        _WORKER_ID = environment.runner.worker_index

# Mimesis global vars
_ = Field(locale=Locale.EN)
_FS = Fieldset(locale=Locale.EN)
_SCHEMA = None
_INSSCHEMA = None

class MetricsLocust(User):
    client, coll, bulk_size = None, None, None

    def __init__(self, parent):
        global _, _FS, _SCHEMA, _WORKER_ID, _HOST, _CLIENT, _SRV, _INSSCHEMA

        super().__init__(parent)

        try:
            vars = self.host.split("|")
            srv = vars[0]
            print("SRV:", srv)

            isInit = (_HOST != self.host)
            if isInit:
                print("Initializing...")
                self.client = pymongo.MongoClient(srv)
                _CLIENT = self.client
                _SRV = srv
                _HOST = self.host
            else:
                self.client = _CLIENT

            db = self.client[vars[1]]
            self.coll = db[vars[2]]

            self.bulk_size = int(vars[3])
            self.chunk_size = int(vars[4])
            print("Batch size from Host:", self.bulk_size)

            if isInit:
                
                _SCHEMA = Schema(
                    schema=lambda: {
                        '_id': "{}".format(uuid.uuid5(uuid.NAMESPACE_DNS, "{}".format({_("increment")+self.chunk_size*(_WORKER_ID):"012"}))),
                        'id2': _("uuid"),
                        'id3': _("uuid"),
                        'payload': _("random.randbytes", n=3710)
                    }
                        
                        ,
                    iterations=self.bulk_size
                )

                _INSSCHEMA = Schema(
                    schema=lambda: {
                        '_id': "{}".format(uuid.uuid5(uuid.NAMESPACE_DNS, "{}".format({random.randint(100000000,10000000000000)+self.chunk_size*(_WORKER_ID):"012"}))),
                        'id2': _("uuid"),
                        'id3': _("uuid"),
                        'payload': _("random.randbytes", n=3710)
                    }
                        
                        ,
                    iterations=1
                )

        except Exception as e:
            events.request.fire(request_type="Host Init Failure", name=str(e), response_time=0, response_length=0, exception=e)
            raise e

    def get_time(self):
        return time.time()

    @task(1)
    def _bulk_insert(self):
        global _SCHEMA, _QUEUE

        _ = Field(locale=Locale.EN)

        name = "Bulk Insert"

        tic = self.get_time()
        try:
            self.coll.insert_many(_SCHEMA.create(),ordered=False)
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)
            time.sleep(5)