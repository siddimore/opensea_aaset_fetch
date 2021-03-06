from pymongo import MongoClient
import os
import pymongo
import json

#TODO: Move to config and read it at run-time
document_db_url = 'mongodb+srv://test:1234@cluster0.9wtcv.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'
db_name = "opensea_data"

# Insert Document One by One in BundleName Collection
def insert_document(bundle_name:str, document: json):
  client = pymongo.MongoClient(document_db_url)
  db = client.opensea_data
  collection = db[bundle_name.replace(".", "_")]
  # insert document into collection
  id = collection.insert_one(document).inserted_id

# Fetch Document By BundleName
def fetch_documents(bundle_name:str):
  client = pymongo.MongoClient(document_db_url)
  db = client.opensea_data
  collection = db[bundle_name]
  content = collection.find()
  return list(content)

