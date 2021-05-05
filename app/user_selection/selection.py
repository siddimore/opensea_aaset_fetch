import requests
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
import json
from db_operations import db_client
import os
from dataclasses import dataclass
import threading
import queue
from typing import Dict, List
import requests
from db_operations.db_client import UserPrefDbAccessor

db_name = "user_preferences"
@dataclass
class UserChoice:
  bundle_name: str
  token_id: str 

# Get Individual Asset Information
def save_user_selection(user_db_accessor: UserPrefDbAccessor, user_choice:json):
  try:
      # Add To User Choice
      category = user_choice["category"]
      user_db_accessor.save_user_choice(user_choice["category"], user_choice)
  except requests.exceptions.RequestException as e:
      return e

# TODO: Remove this method
def save_displayed_token(displayed_token:json):
  try:
      # Add To User Choice
      db_client.save_shown_user_token(bundle_name=user_choice["bundle_name"], document=user_choice)
      return db_client.document_exists("opensea_displayed_token", user_choice["bundle_name"], user_choice["token_id"])
  except requests.exceptions.RequestException as e:
      return e