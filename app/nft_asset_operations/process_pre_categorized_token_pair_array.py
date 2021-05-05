
import requests
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
import json
from db_operations.db_client import CadenceTokenPairAccessor
import os
from dataclasses import dataclass
import threading
import queue
from typing import Dict, List
import requests


# Processes Scrapper Post and Gets Document from OpenSea by Querying OPENSEA API
# Stores each OPENSEA document in DB
@dataclass
class ProcessCadenceTokenPair(object):
# class ProcessAssetData(object):
    token_pair_queue: queue.Queue = queue.Queue()

    def __init__(
        self,
        input_json,
        db_accessor: CadenceTokenPairAccessor,
        nb_threads: int = 2,
    ) -> None:
        """Put all urls to the queue url """
        self.nb_threads = nb_threads
        self.workers = self.insert_token_pair
        self.db_accessor = db_accessor
        for token_pair in input_json:
          self.token_pair_queue.put(token_pair)

    # Process Items from Queue
    def add_tokenpair_to_dB(self) -> None:
        """Pull a url from the queue and make a get request to endpoint"""
        count = 0
        while not self.token_pair_queue.empty():
            token_pair = self.token_pair_queue.get()
            self.insert_token_pair(token_pair["token1"]["category"], token_pair)
            self.token_pair_queue.task_done()

    # Get Individual Asset Information
    def insert_token_pair(self, category: str, token_pair:json):
      try:
          print(token_pair)
          #if token_pair:
          self.db_accessor.insert_cadence_pair(category_name=category, token_pair=token_pair)
      except:
          print("Could not process token_pair")