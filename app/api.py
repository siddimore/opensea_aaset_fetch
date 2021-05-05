import os
import time
import datetime
import json
import re
import random
import bmemcached
import logging
from bson.json_util import dumps, CANONICAL_JSON_OPTIONS
from flask import Flask, jsonify, request, make_response, has_request_context
from flask.logging import default_handler
from flask_request_id_header.middleware import RequestID
from flask_expects_json import expects_json
from flask_cors import CORS
from flask_api import status
from threading import Thread
from loguru import logger
from nft_asset_operations.get_assets import GetAssetsFromCategories, GetRawDataBundleNames
from nft_asset_operations.process_asset_data import ProcessAssetData
from nft_asset_operations.process_pre_categorized_token_pair_array import ProcessCadenceTokenPair
from nft_asset_operations.process_nsfw import ProcessNSFW
from user_selection.selection import save_user_selection
from multiprocessing import Process, Value
from app_config.config import Config, ProductionConfig, StagingConfig, DevelopmentConfig
from flask_apscheduler import APScheduler
from db_operations.db_client import RawDbAccessor, CategoriesDbAccessor, UserPrefDbAccessor, PreCategorizedDbAccessor, CadenceTokenPairAccessor


# Start Flask APP
app = Flask(__name__)

print(os.environ['ENV'])
if os.environ['ENV'] == 'production':
    config = ProductionConfig()

if os.environ['ENV'] == 'staging':
    config = StagingConfig()

if os.environ['ENV'] == 'development':
    config = DevelopmentConfig()

# Apply Config
app.config.from_object(config)

# Create DB Accessors
raw_data_db_accessor = RawDbAccessor(config)
categories_data_ab_accesor = CategoriesDbAccessor(config)
user_pref_db_accessor = UserPrefDbAccessor(config)
pre_categorized_db_accessor = PreCategorizedDbAccessor(config)
cadence_categorized_db_accessor = CadenceTokenPairAccessor(config)

# Create Cache Object
cache = bmemcached.Client(config.cache_servers, config.cache_user, config.cache_pass)
tokens_list = ["tokens_Collectibles", "tokens_Music", "tokens_Memes", "tokens_Games", "tokens_Art", "tokens_Trading Cards", "tokens_Utility", "tokens_Video", "tokens_Metaverses"]
token_list_cache = bmemcached.Client(config.token_list_server, config.toke_list_user, config.token_list_pass)
token_list_cache.set("token_lists", tokens_list)

# Create GetAssets Object
get_categorised_assets = GetAssetsFromCategories(config, categories_data_ab_accesor, pre_categorized_db_accessor)
get_raw_data = GetRawDataBundleNames(raw_data_db_accessor)
nsfw_processor = ProcessNSFW(config, categories_data_ab_accesor)

# Enable CORS
CORS(app)

# Enable RequestID
RequestID(app)

class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.request_id = 'NA'

        if has_request_context():
            record.request_id = request.environ.get("HTTP_X_REQUEST_ID")

        return super().format(record)

formatter = RequestFormatter(
    '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(module)s: %(message)s'
)
default_handler.setFormatter(formatter)

# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
scheduler.init_app(app)
scheduler.start()

# TODO: Move schemas later to a seperate file
# Schema for bundle process
schema = {
  "type": "object",
  "properties": {
    "bundleName": { "type": "string" },
    "contractAddress": { "type": "string" },
  },
  "required": ["bundleName", "contractAddress"]
}

nsfw_schema = {
  "type": "object",
  "properties": {
    "token_id": { "type": "string" },
    "category": { "type": "string" },
    "reason": { "type": "string" },
    "permalink": {"type": "string"}
  },
  "required": ["token_id", "category", "reason", "permalink"]
}

# Schema for user preference process
user_preference_schema = {
  "type": "object",
  "properties": {
    "category": { "type": "string" },
    "token1": { "type": "object",
    "properties":{
      "token_id":{
        "type": "string"
      },
      "category":{
        "type": "string"
      },
      "contract_address":{
        "type": "string" 
      },
      "display":{
        "type":"string"
      }
    } },
    "token2": { "type": "object",
    "properties":{
      "token_id":{
        "type": "string"
      },
      "category":{
        "type": "string"
      },
      "contract_address":{
        "type": "string"
      },
      "display":{
        "type":"string"
      }
    } },
    "token_choice": { "type": "object",
    "properties":{
      "token_id":{
        "type": "string"
      },
      "category":{
        "type": "string"
      },
      "contract_address":{
        "type": "string"
      },
      "display":{
        "type":"string"
      }
    } }
  },
  "required": ["category", "token1", "token2", "token_choice"]
}

cadence_pair_token_schema = {
    "title": "tokenPairsArray",
    "description": "schema for tokens",
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "bundle_name": {
            "description": "bundle_name of a token",
            "type": "string"
        },
        "category": {
            "description": "categgory of the token",
            "type": "string"
        },
        "contract_address": {
            "description": "contract address of token",
            "type": "string",
        },
        "name": {
            "description": "name of the token",
            "type": "string",
        },
        "image_url": {
            "description": "image url of token",
            "type": "string",
        },
        "token_id": {
            "description": "iidof token",
            "type": "string",
        }
      },
      "required": ["bundle_name", "category", "contract_address", "name", "image_url", "token_id"]
    }
}

@app.route('/', methods=['GET'])
def home():
  return "<h1>NFT Flask API</h1><p>This is a prototype API.</p>"

# Fetch tokens by BundleName
@app.route("/api/fetchPreCategorizedTokens", methods=['GET'])
def fetch_get_precateogirzed_token_pair():
  # # if key doesn't exist, returns a 400, bad request error
  try:
      limit = request.args['limit']
      start_index = request.args['startIndex']
      category=request.args['category']
      all_tokens = get_categorised_assets.get_precategorized_token_pair(category, start_index, limit)
      r = make_response(all_tokens)
      r.mimetype = 'application/json'
      r.status_code = 200
      return r
  except:
      logger.debug("Could not process fetchPreCategorizedTokens")


# Fetch tokens by BundleName
@app.route("/api/fetchTokenById", methods=['GET'])
def fetch_token_by_id():
    # # if key doesn't exist, returns a 400, bad request error
  category_name = request.args['category_name']
  token_id = request.args['token_id']
  logger.debug("category name: {}", category_name)
  logger.debug("token id: {}", token_id)
  token = get_categorised_assets.get_token_by_id(category=category_name, token_id=token_id)
  logger.info(type(token))
  logger.info(token)
  if token is None:
    return make_response(jsonify({"error": "Not Found"}), status.HTTP_404_NOT_FOUND)
  else:
    json_data = dumps(token, indent = 2) 
    return make_response(json_data, 200)

  
# Fetch tokens by BundleName
@app.route("/api/fetchTokens")
def fetch_random_tokens():
  # Pick one randomly from this list
  tokens_list = token_list_cache.get("token_lists")
  if len(tokens_list) != 0:
    sampled_list = random.sample(tokens_list, 1)
    tokens_list.remove(sampled_list[0])
    token_name = sampled_list[0]
    token_list_cache.set("token_lists", tokens_list)
  else:
    tokens_list = ["tokens_Collectibles", "tokens_Music", "tokens_Memes", "tokens_Games", "tokens_Art", "tokens_Trading Cards", "tokens_Utility", "tokens_Metaverses", "tokens_Video"]
    sampled_list = random.sample(tokens_list, 1)
    tokens_list.remove(sampled_list[0])
    token_name = sampled_list[0]
    token_list_cache.set("token_lists", tokens_list)

  logger.debug("Token Name: {}", token_name)

  # Get From Cache
  tokens = cache.get(token_name)
  if tokens is not None:
    return make_response(jsonify(tokens), 200)
  else:
    category_name = token_name.replace("tokens_", '')
    logger.debug("Category_Name:{}", category_name)
    # Get 2 Tokens for given category
    tokens = get_categorised_assets.get_token_for_category(category_name=category_name)
    logger.debug("Queried DB for Tokens:{}" ,tokens)
    if tokens is not None:
      return make_response(jsonify(tokens), 200)
    else:
      for token in tokens_list:
        if token != token_name:
          new_token = cache.get(token)
          logger.warning("Getting another key with value since Cache is empty: {}", new_token)
          return make_response(jsonify(new_token), 200)


# Fetch API by Collection Name
@app.route("/api/fetchBundleNames")
def fetch_bundle_name():
  # # if key doesn't exist, returns a 400, bad request error
  bundles = get_raw_data.get_bundle_names()
  bundles_json = {"bundles": bundles}
  logger.info("Fetched BundleNames From Db: {}", json.dumps(bundles_json))
  return make_response(jsonify(bundles_json), 200)

# Fetch API by Collection Name
@app.route("/api/fetchCategoryNames")
def fetch_category_names():
  # # if key doesn't exist, returns a 400, bad request error
  categories = get_categorised_assets.get_category_names_with_weights_payload()
  categories_json = categories
  logger.info("Fetched Categories From Db: {}", json.dumps(categories_json))
  return make_response(jsonify(categories_json), 200)

#Job To Refresh Cache
# Commenting this out as it wont be required
# @scheduler.task('interval', id='refresh_cache', seconds=2)
# def refresh_cache():
#   get_categorised_assets.get_tokens_from_db()

# Helper Method for Async processing of Input Data from Process
def process_data(data):
  # do processing...
  opensea_client = ProcessAssetData(data, raw_data_db_accessor)
  opensea_client.worker_get_asset_info()
  logger.debug('Finished processing Process Data Helper Method')

# Call API Process to save Assets in dB
@app.route('/api/processNSFW', methods=['POST'])
@expects_json(nsfw_schema)
def process_nsfw():
  data = request.get_json()
  if not data:
    return jsonify(status=400, body="Missing data")
  result = nsfw_processor.add_nsfw_flag(data["category"], data["token_id"], data["permalink"], data["reason"])
  if result:
    return jsonify(status=200, body="Processed NSFW")
  else:
    return jsonify(status=400, body="Failed To Process")


# Helper Method for Async processing of Input Data from Process
def process_cadence_token_pair_backgroun_task(data):
  # do processing...
  opensea_client = ProcessCadenceTokenPair(data, cadence_categorized_db_accessor)
  opensea_client.add_tokenpair_to_dB()
  logger.debug('Finished processing Process Data Helper Method')


# Call API Process to save Assets in dB
@app.route('/api/processWeights', methods=['POST'])
def process_category_weights():
  data = request.get_json()
  if not data:
    return jsonify(status=400, body="Missing data")
  logger.info("Process Weights: {}", json.dumps(data))
  cadence_categorized_db_accessor.insert_weights(data)
  return jsonify(status=200, body="Processed Weights Insert")

# Call API Process to save Assets in dB
@app.route('/api/addPreCuratedTokenPair', methods=['POST'])
# @expects_json(cadence_pair_token_schema)
def process_cadence_pair():
  # We will only support this on development 
  # possibly later on staging
  if os.environ['ENV'] == 'staging':
    data = request.get_json()
    if not data:
      return jsonify(status=400, body="Missing data")

    logger.info("Process Scrapper Input: {}", json.dumps(data))
    #Spawn thread to process the data
    t = Thread(target=process_cadence_token_pair_backgroun_task, args=(data, ))
    t.start()

    #Immediately return a 200 response to the caller
    return jsonify(status=200, body="Processed Cadence Pair")
  else:
    return make_response(jsonify({"error": "Not Supported"}), status.HTTP_405_METHOD_NOT_ALLOWED)
  
# Call API Process to save Assets in dB
@app.route('/api/process', methods=['POST'])
@expects_json(schema)
def process_handle():
  # We will only support this on development 
  # possibly later on staging
  data = request.get_json()
  if not data:
    return jsonify(status=400, body="Missing data")

  logger.info("Process Scrapper Input: {}", json.dumps(data))
  #Spawn thread to process the data
  t = Thread(target=process_data, args=(data, ))
  t.start()

  #Immediately return a 200 response to the caller
  return jsonify(status=200, body="Complete process")


# Call API Process to save Assets in dB
@app.route('/api/processUserSelection', methods=['POST'])
@expects_json(user_preference_schema)
def process_user_selection():
  data = request.get_json()
  if not data:
    return jsonify(status=400, body="Missing data")
  
  logger.info("Process User Selection: {}", json.dumps(data))
  
  processed = save_user_selection(user_pref_db_accessor, data)
  return jsonify(status=200, body="Processed User Selection")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)