from bson.json_util import dumps
from db_operations import db_client
from db_operations.db_client import CategoriesDbAccessor, RawDbAccessor, PreCategorizedDbAccessor
from loguru import logger
import json
import random
import bmemcached
import requests
from app_config.config import Config


# Get Assets From Categories DB 
class GetAssetsFromCategories:  
    # init method or constructor 
    def __init__(self, config:Config, categories_db_accessor: CategoriesDbAccessor, pre_categorized_db_accessor: PreCategorizedDbAccessor):
        self.config = config
        self.categories_db_accessor = categories_db_accessor
        self.pre_categorized_db_accessor = pre_categorized_db_accessor

        # Fetch all categories from DB
        self.categories_list = self.get_category_names()
        # Create MAP of Category to Address List
        self.category_to_address_map_list = {}

        # For Each category get all unique contract addresses
        for category in self.categories_list:
          category_list_name = "".join([item.strip() for item in category.split(" ")])
          # Append List to the name
          category_list_name = category_list_name + "_List"

          # Get all unique addresses for this category
          address_list = self.get_all_addresses_in_category(category)
          self.category_to_address_map_list[category_list_name] = address_list

    # Get Unique Address in Categoru     
    def get_all_addresses_in_category(self, category:str):
      address = self.categories_db_accessor.fetch_distinct_documents(category)
      logger.info("Unique Address {} to be added for Category {}", address, category)
      return address

    # Get Cateogory Name
    def get_category_names_with_weights_payload(self):
      return self.pre_categorized_db_accessor.fetch_category_names()

    # Get Cateogory Name
    def get_category_names(self):
      return self.categories_db_accessor.fetch_category_names()

    def get_token_by_id(self, category, token_id):
      return self.categories_db_accessor.fetch_token_by_id(category_name=category, token_id=token_id)

    # Get Tokens from dB using pagination
    def get_precategorized_token_pair(self, category_name:str, start_index, limit):
      logger.info("*****")
      token_pair_list = self.pre_categorized_db_accessor.fetch_documents(category_name=category_name, start_index=start_index, limit=limit)
      tokens_pair_list = []
      print(token_pair_list)
      for token_pair in token_pair_list:
        if _check_valid_img_urls(token_pair):

          tokens_pair_list.append(token_pair)
      
      json_data = dumps(tokens_pair_list, indent = 2)
      return json_data
    
    
    # Get 2 Tokens for a specific category
    def get_token_for_category(self, category_name:str):
      address_list_name = "".join([item.strip() for item in category_name.split(" ")])

      # Append List to the selected Random Choice from Categories List
      # This is then used to get the contract addres from 
      address_list_name = address_list_name + "_List"
      logger.info("Address list name:{}", address_list_name)


      # Get Token Address List from, Category To Address Map
      # For Example if category_name is Collectibles our token_address_list is Collectibles_List
      tokne1_address_list = self.category_to_address_map_list[address_list_name]
      logger.info("Token1 Address List: {}", tokne1_address_list)
      address1 = random.choice(tokne1_address_list)
      logger.info("Token1 Address: {}", address1)

      # Get Another Token from the list
      # We will remove address1 from the same list since we dont want to present the same token
      tokne2_address_list = tokne1_address_list[:]
      tokne2_address_list.remove(address1)
      logger.info("Token1 Address List: {}", tokne2_address_list)
      address2 = random.choice(tokne2_address_list)
      logger.info("Token2 Address: {}", address2)
      # Build Tokens Dict
      tokens = {}
      # Fetch Token1
      token1 = self.categories_db_accessor.fetch_random_document_contract_address(category_name, address1)

      if token1.keys():
        #Fetch Token2
        token2 = self.categories_db_accessor.fetch_random_document_contract_address(category_name, address2)
        # Build Tokens Dict
        tokens = {}
        tokens["token1"] = token1
        tokens["token2"] = token2
        if _check_valid_img_urls(tokens):
          return tokens
        else:
          return None


    # Get 2 Tokens from Same Category Random BundleName
    def get_tokens_from_db(self):
      # Iterate throught each category
      for category_name in self.categories_list:
        address_list_name = "".join([item.strip() for item in category_name.split(" ")])

        # Append List to the selected Random Choice from Categories List
        # This is then used to get the contract addres from 
        address_list_name = address_list_name + "_List"
        logger.info("Address list name:{}", address_list_name)


        # Get Token Address List from, Category To Address Map
        # For Example if category_name is Collectibles our token_address_list is Collectibles_List
        if address_list_name != "DeFi_List" and address_list_name != "NA_List":
          tokne1_address_list = self.category_to_address_map_list[address_list_name]
          if len(tokne1_address_list) > 1:
            logger.info("Token1 Address List: {}", tokne1_address_list)
            address1 = random.choice(tokne1_address_list)
            logger.info("Token1 Address: {}", address1)

            # Get Another Token from the list
            # We will remove address1 from the same list since we dont want to present the same token
            tokne2_address_list = tokne1_address_list[:]
            tokne2_address_list.remove(address1)
            logger.info("Token1 Address List: {}", tokne2_address_list)
            address2 = random.choice(tokne2_address_list)
            logger.info("Token2 Address: {}", address2)
            # Build Tokens Dict
            tokens = {}
            # Fetch Token1
            token1 = self.categories_db_accessor.fetch_random_document_contract_address(category_name, address1)

            if token1.keys():
              #Fetch Token2
              token2 = self.categories_db_accessor.fetch_random_document_contract_address(category_name, address2)

              if token2.keys():
                logger.debug("Fetched Token1: {}", json.dumps(token1))
                logger.debug("Fetched Token1: {}", json.dumps(token2))
                # Add Tokens To Dictionary
                tokens["token1"] = token1
                tokens["token2"] = token2

                if _check_valid_img_urls(tokens):
                  # Save To Cachec
                  cache = bmemcached.Client(self.config.cache_servers, self.config.cache_user, self.config.cache_pass)
                  token_pair = cache.get("tokens_"+category_name)
                  if token_pair is not None:
                    json1 = json.dumps(token_pair, sort_keys=True)
                    json2 = json.dumps(tokens, sort_keys=True)
                    if json1 != json2:
                      cache.set("tokens_"+category_name, tokens)
                  else:
                    cache.set("tokens_"+category_name, tokens)


# Access for Getting RAW Data
class GetRawDataBundleNames:
    def __init__(self, raw_db_access: RawDbAccessor):
      self.raw_db_accessor = raw_db_access
    # Get Bundle Name
    def get_bundle_names(self):
      #return db_client.fetch_bundle_names()
      return self.raw_db_accessor.fetch_bundle_names()


def _check_valid_img_urls(tokens: dict):

  try:
    url_list = []
    url_list.append(tokens["token1"]["image_url"])
    url_list.append(tokens["token2"]["image_url"])
    # Iterate through URL List
    for url in url_list:
      if not _is_url_image(url):
        return False
      else:
        return True
  except:
    return False


def _is_url_image(image_url):
   image_formats = ("image/png", "image/jpeg", "image/jpg")
   r = requests.head(image_url)
   if r.headers["content-type"] in image_formats:
     logger.info("Valid Image URL")
     return True
   return False


