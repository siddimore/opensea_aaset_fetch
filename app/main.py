import os
import time
import json
from flask import Flask, jsonify, request
from threading import Thread
from opensea_operations.process_asset_data import ProcessAssetData
from opensea_operations.get_assets import get_assets_from_db

app = Flask(__name__)



# Fetch API by Collection Name
@app.route("/api/fetch")
def fetch_data():
  return jsonify(get_assets_from_db("hashmasks"))


# Helper Method for Async processing of Input Data from Process
def process_data(data):
  # do processing...
  opensea_client = ProcessAssetData(data)
  opensea_client.worker_get()
  print('Finished processing')


# Call API Process to save Assets in dB
@app.route('/api/process', methods=['POST'])  
def process_handle():
  data = request.get_json()
  print('Received data at process')

  if not data:
    return jsonify(status=400, body="Missing data")

  #Spawn thread to process the data
  t = Thread(target=process_data, args=(data, ))
  t.start()

  #Immediately return a 200 response to the caller
  return jsonify(status=200, body="Complete process")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)