import requests
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
import json
from db_operations.db_client import RawDbAccessor
import os
from dataclasses import dataclass
import threading
import queue
from typing import Dict, List
import requests


# Move to Config later
api_base_url = 'https://api.opensea.io/api/v1/asset/'

# Move to models
# Data Class to save bundle name and asset id
@dataclass
class AssetInfo:
  bundle_name: str
  asset_id: str

# Processes Scrapper Post and Gets Document from OpenSea by Querying OPENSEA API
# Stores each OPENSEA document in DB
@dataclass
class ProcessAssetData(object):
# class ProcessAssetData(object):
    assets_list: queue.Queue = queue.Queue()

    def __init__(
        self,
        input_json: json,
        db_accessor: RawDbAccessor,
        nb_threads: int = 2,
    ) -> None:
        """Put all urls to the queue url """
        self.nb_threads = nb_threads
        self.workers = self.worker_get_asset_info
        self.db_accessor = db_accessor
        print(input_json)
        bundle_name = input_json["bundleName"].lower().replace(" ", "")
        contract_address = input_json["contractAddress"]
        assets = input_json["assets"]
        for asset in assets:
          nft_asset = AssetInfo(bundle_name=bundle_name,asset_id=contract_address+"/"+asset)
          self.assets_list.put(nft_asset)

    def fix_dict(self, data, ignore_duplicate_key=True):
        """
        Removes dots "." from keys, as mongo doesn't like that.
        If the key is already there without the dot, the dot-value get's lost.
        This modifies the existing dict!

        :param ignore_duplicate_key: True: if the replacement key is already in the dict, now the dot-key value will be ignored.
                                    False: raise ValueError in that case.
        """
        if isinstance(data, (list, tuple)):
            list2 = list()
            for e in data:
                list2.append(self.fix_dict(e))
            # end if
            return list2
        if isinstance(data, dict):
            # end if
            for key, value in data.items():
                value = self.fix_dict(value)
                old_key = key
                if "." in key:
                    key = old_key.replace(".", "")
                    if key not in data:
                        data[key] = value
                    else:
                        error_msg = "Dict key {key} containing a \".\" was ignored, as {replacement} already exists".format(
                            key=key_old, replacement=key)
                        if force:
                            import warnings
                            warnings.warn(error_msg, category=RuntimeWarning)
                        else:
                            raise ValueError(error_msg)
                        # end if
                    # end if
                    del data[old_key]
                # end if
                data[key] = value
            # end for
            return data
        # end if
        return data
    # end def
  

    # Process Items from Queue
    def worker_get_asset_info(self) -> None:
        """Pull a url from the queue and make a get request to endpoint"""
        while not self.assets_list.empty():
            asset = self.assets_list.get()
            api_url = api_base_url  + asset.asset_id
            response_code = self.get_asset(api_url, asset.bundle_name, asset.asset_id)
            if response_code == 429:
              time.sleep(3)
              self.get_asset(api_url, bundle_name)
            self.assets_list.task_done()

    # Get Individual Asset Information
    def get_asset(self, input_url, bundle_name, asset_id):
      try:
          api_url = input_url
          print(api_url)
          response = requests.get(api_url)

          if response.status_code == 200:
            data = self.fix_dict(response.json())
            self.db_accessor.insert_raw_document(bundle_name=bundle_name, document=data)
            return response.status_code

      except requests.exceptions.RequestException as e:
          return e