from bson.json_util import dumps
from db_operations import db_client
from db_operations.db_client import CategoriesDbAccessor
from loguru import logger
import json
from app_config.config import Config


# Get Assets From Categories DB 
class ProcessNSFW:  
    # init method or constructor 
    def __init__(self, config:Config, categories_db_accessor: CategoriesDbAccessor):
        self.config = config
        self.categories_db_accessor = categories_db_accessor

    def add_nsfw_flag(self, category:str, token_id:str, permalink:str, reason:str=""):
        result = self.categories_db_accessor.update_with_nsfw_flag(category_name=category, token_id=token_id, permalink=permalink, reason=reason)
        logger.info("Update Document Result:{}" , result)
        if result > 0:
            return True
        return False

