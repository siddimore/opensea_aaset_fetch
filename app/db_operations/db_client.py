from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps, CANONICAL_JSON_OPTIONS
from loguru import logger
import os
import pymongo
import json
import re
import random
from app_config.config import Config


# Class to Fetch Categorized Data
class CategoriesDbAccessor:
   
    # init method or constructor 
    def __init__(self, config:Config):
        self.config = config
        self.client = pymongo.MongoClient(self.config.categorize_db_url)

    def __del__(self):
        logger.info('Destructor called, TokenOperationsDbAccessor deleted.')
        self.client.close()

    def fetch_distinct_documents(self, category_name:str):
      logger.info("URL for categorized db: {}", self.config.categorize_db_url)
      db = self.client[self.config.categorize_db_name]
      collection = db[category_name]
      content = collection.distinct("asset_contract.address")
      return content

    # Fetch CategoryNames
    def fetch_category_names(self):
      database = self.client[self.config.categorize_db_name]
      collection = database.collection_names(include_system_collections=False)
      # Remove an uncategorized tokens from View
      collection.remove("UnCategorized")
      return collection

    def fetch_documents(category_name:str, start_index:str, limit:str):
      # Query DB
      database = self.client[self.config.categorize_db_name]
      collection = database[category_name]
      content = collection.find().sort("_id",pymongo.ASCENDING).skip(int(start_index)).limit(int(limit))
      return content

    # Fetch Token By Id
    def fetch_token_by_id(self, category_name: str, token_id:str):
      # Query DB
      database = self.client[self.config.categorize_db_name]
      collection = database[category_name]
      if token_id is not None:
        # Get Token By TokenId
        content = collection.find({"token_id":token_id})
        token = {}
        for doc in content:
          token["category"] = category_name
          token["token_id"] = doc["token_id"]
          token["permalink"] = doc["permalink"]
          token["image_url"] = doc["image_url"]
          token["contract_address"] = doc["asset_contract"]["address"]
          token["bundle_name"] = doc["asset_contract"]["name"]
        return token
      else:
        return None

    # Query the DB and Get 2 random tokens
    def fetch_random_document_contract_address(self, category_name: str, contract_address:str):
      logger.info("URL for categorized db: {} and contract address to fetch: {}", self.config.categorize_db_url, contract_address)
      db = self.client[self.config.categorize_db_name]
      collection = db[category_name]

      # Query DB and get one document of the same type
      total_docs = collection.find({"asset_contract.address":contract_address}).count()
      content = collection.find({"asset_contract.address":contract_address}).limit(1).skip(random.randint(1,total_docs))

      if content.count() == 0:
        logger.debug("Empty cursor")

      # Build our token 
      token = {}
      for doc in content:
        token["category"] = category_name
        token["token_id"] = doc["token_id"]
        token["permalink"] = doc["permalink"]
        token["image_url"] = doc["image_url"]
        token["contract_address"] = doc["asset_contract"]["address"]
        token["bundle_name"] = doc["asset_contract"]["name"]
        token["name"] = doc["name"]

      return token

    # Insert Document One by One in BundleName Collection
    def update_with_nsfw_flag(self, category_name:str, token_id: str, permalink:str, reason: str):
      logger.info("category_name {}", category_name)
      logger.info("token_id {}", token_id)
      logger.info("url {}", self.config.nfsw_db_url)

      db = self.client[self.config.nsfw_db_name]
      collection = db[category_name]
      regex_query = { "token_id" : {"$regex" : token_id} }
      if collection.find(regex_query).count() > 0:
        result = collection.update_one({'token_id': token_id}, {"$push": {"nsfw.user_reason": reason}})
        return result.modified_count
      else:
        # Set NSFW Flag
        nsfw_doc = {"token_id": token_id, "nsfw": {"isNSFW": True, "permalink": permalink, "user_reason": [reason], "pg_reason":""}}
        #newvalues = { "$set": { "nsfw": {"isNSFW": True, "permalink": permalink, "user_reason": [reason], "pg_reason":""} } }
        result = collection.insert_one(nsfw_doc)
        logger.debug("Update NSFW Flag: {}" ,result)
        return 1


# Class to Fetch PreCategorized Token Data
# Used to FetchData from CadenceDB Refreshed every `n` hours
class PreCategorizedDbAccessor:
  
    # init method or constructor 
    def __init__(self, config:Config):
        self.config = config
        self.client = pymongo.MongoClient(self.config.categorize_db_url)

    def __del__(self):
        logger.info('Destructor called, TokenOperationsDbAccessor deleted.')
        self.client.close()

    # Fetch CategoryNames
    def fetch_category_names(self):
      db = self.client[self.config.cadence_token_pair_weightdb_name]
      collection = db["Weights"]
      content = collection.find({},{"_id" : False}).sort("_id",pymongo.ASCENDING).limit(1)
      for doc in content:
        print(type(doc))
        if 'id' in doc:
          logger.info("****")
          del doc['id']
        return doc

    # Fetch Categorized Documents By CategoryName
    # This method is used to retrieve tokens with pagination
    def fetch_documents(self, category_name:str, start_index:str, limit:str):
      db = self.client["CadenceTokenPairEveryTwoHours"]
      collection = db[category_name]
      logger.info(category_name)
      logger.info(collection)
      content = collection.find().sort("_id",pymongo.ASCENDING).skip(int(start_index)).limit(int(limit))
      list_cur = list(content)
      return list_cur

# Class to insert RAWData
class RawDbAccessor:
   
    # init method or constructor 
    def __init__(self, config:Config):
        self.config = config
        self.client = pymongo.MongoClient(self.config.raw_document_db_url)

    # Insert Document One by One in BundleName Collection
    def insert_raw_document(self, bundle_name:str, document: json):
      db = self.client[self.config.raw_db_name]
      bundle_name = bundle_name.replace(".", "_")
      logger.debug("Insert Documet to: {}", bundle_name)
      collection = db[bundle_name]
      # insert document into collection
      exists = self.document_exists(self.config.raw_db_name, bundle_name, document['token_id'])
      # If Doc exists replace
      if exists:
        logger.info("Document with token_id {} exists", document['token_id'])    
        collection.replace_one(
          { "token_id" : document['token_id']},
          document
        )
      else:
        logger.info("Inserting Document with token_id {}", document['token_id'])
        collection.insert_one(document)

    # Fetch Document By BundleName
    def fetch_bundle_names(self):
      logger.warning(self.config.raw_document_db_url)
      logger.warning(self.config.raw_db_name)
      database = self.client[self.config.raw_db_name]
      collection = database.collection_names(include_system_collections=False)
      return collection

    def document_exists(self, db_name: str, bundle_name:str, token_id:str):
      #client = pymongo.MongoClient(self.config.raw_document_db_url)
      db_name = self.client[db_name]
      collection = db_name[bundle_name.replace(".", "_")]
      regex_query = { "token_id" : {"$regex" : token_id} }
      if collection.find(regex_query).count() > 0:
        return True
      else:
        return False


#### TODO: Merge this method later with PreCategorizedDbAccessor
class CadenceTokenPairAccessor:
   
    # init method or constructor 
    def __init__(self, config:Config):
        self.config = config
        self.client = pymongo.MongoClient(self.config.raw_document_db_url)

    def insert_weights(self, weights: json):
      db = self.client[self.config.cadence_token_pair_weightdb_name]
      collection = db["Weights"]
      total_docs = collection.count()
      if total_docs == 0:
        weights["id"] = 1
        collection.insert_one(weights)
      else:
        count = collection.find({"id":1}).count()
        logger.info("found weight document to replace {}", count)
        weights["id"] = 1
        collection.replace_one({"id":1}, weights)

    # Insert Document One by One in BundleName Collection
    def insert_cadence_pair(self, category_name:str, token_pair: json):
      db = self.client[self.config.cadence_token_pair_db_name]
      category_name = category_name.replace(".", "_")
      collection = db[category_name]
      # insert document into collection
      count = collection.find({"token1.token_id": token_pair["token1"]["token_id"], "token2.token_id": token_pair["token2"]["token_id"]}).count()
      logger.info("Find Document Count: {},  with tokenPair token1: {}, token2: {}", count, token_pair["token1"]["token_id"], token_pair["token2"]["token_id"])
      if count == 0:
        logger.debug("Inserting Document with token1: {}, token2: {}", token_pair["token1"]["token_id"], token_pair["token2"]["token_id"])
        collection.insert_one(token_pair)

# Class to process User Preference
class UserPrefDbAccessor:
    # init method or constructor 
    def __init__(self, config:Config):
        self.config = config
        self.client = pymongo.MongoClient(self.config.categorize_db_url)

    # Insert Document One by One in BundleName Collection
    def save_user_choice(self, category_name:str, document: json):
      db = self.client[self.config.user_preferences_db_name]
      logger.debug(category_name)
      collection = db[category_name.replace(".", "_")]
      return collection.insert_one(document)