from bson.json_util import dumps
from db_operations import db_client

# Gets Documents from dB by Bundle Name
def get_assets_from_db(bundle_name):
  return dumps(db_client.fetch_documents(bundle_name=bundle_name))