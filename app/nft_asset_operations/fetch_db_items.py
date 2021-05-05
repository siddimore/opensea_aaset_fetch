# Move to seperate class
# Processes Scrapper Post and Gets Document from OpenSea by Querying OPENSEA API
# Stores each OPENSEA document in DB
@dataclass
class FetchDB(object):
    assets_list: queue.Queue = queue.Queue()

    def __init__(
        self,
        input_json: json,
        nb_threads: int = 2,
    ) -> None:
        """Put all urls to the queue url """
        self.nb_threads = nb_threads
        self.workers = self.worker_get_asset_info
        print(input_json)
        bundle_name = input_json["bundleName"].lower().replace(" ", "")
        contract_address = input_json["contractAddress"]
        assets = input_json["assets"]
        for asset in assets:
          nft_asset = AssetInfo(bundle_name=bundle_name,asset_id=contract_address+"/"+asset)
          self.assets_list.put(nft_asset)

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
            db_client.insert_document(bundle_name=bundle_name, document=data)
            return response.status_code

      except requests.exceptions.RequestException as e:
          return e