import os
document_db_url = ''
api_base_url = 'https://api.opensea.io/api/v1/asset/'

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    SCHEDULER_API_ENABLED = True
    CSRF_ENABLED = True
    REQUEST_ID_UNIQUE_VALUE_PREFIX = "NMC-"
    raw_db_name = "OpenSeaScrappedData"
    categorize_db_name = "OpenSeaCategorizedData"
    user_preferences_db_name = "UserPreferences"
    nsfw_db_name = "NSFWData"
    cadence_token_pair_db_name = "CadenceTokenPairEveryTwoHours"
    cadence_token_pair_weightdb_name = "CadenceTokenPairEveryTwoHourWeights"
    raw_document_db_url = 'mongodb+srv://pg_admin:a3bvNWeER2yVAHgo@cluster0.0kpte.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'
    categorize_db_url = ''
    cache_servers = ''
    cache_user = ''
    cache_pass = ''
    token_list_server = '' 
    toke_list_user = ''
    token_list_pass = ''


class ProductionConfig(Config):
    DEBUG = False
    raw_db_name = "OpenSeaScrappedData"
    categorize_db_name = "OpenSeaCategorizedData"
    user_preferences_db_name = "UserPreferences"
    nsfw_db_name = "NSFWData"
    pre_categorized_db_name = "CatergoirzedTokenPairs"
    cadence_token_pair_db_name = "CadenceTokenPairEveryTwoHours"
    cadence_token_pair_weightdb_name = "CadenceTokenPairEveryTwoHourWeights"
    raw_document_db_url = ''
    categorize_db_url = ''
    nfsw_db_url = ''
    cache_servers = ''
    cache_user = ''
    cache_pass = ''
    token_list_server = '' 
    toke_list_user = ''
    token_list_pass = ''


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    raw_db_name = "OpenSeaScrappedData"
    categorize_db_name = "OpenSeaCategorizedData"
    user_preferences_db_name = "UserPreferences"
    nsfw_db_name = "NSFWData"
    pre_categorized_db_name = "CatergoirzedTokenPairs"
    cadence_token_pair_db_name = "CadenceTokenPairEveryTwoHours"
    cadence_token_pair_weightdb_name = "CadenceTokenPairEveryTwoHourWeights"
    raw_document_db_url = ''
    categorize_db_url = ''
    cache_servers = ''
    cache_user = ''
    cache_pass = ''
    token_list_server = '' 
    toke_list_user = ''
    token_list_pass = ''


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    raw_db_name = "OpenSeaScrappedData"
    categorize_db_name = "OpenSeaCategorizedData"
    user_preferences_db_name = "UserPreferences"
    pre_categorized_db_name = "CatergoirzedTokenPairs"
    cadence_token_pair_db_name = "CadenceTokenPairEveryTwoHours"
    cadence_token_pair_weightdb_name = "CadenceTokenPairEveryTwoHourWeights"
    raw_document_db_url = ''
    categorize_db_url = ''
    cache_servers = ''
    cache_user = ''
    cache_pass = ''
    token_list_server = '' 
    toke_list_user = ''
    token_list_pass = ''


class TestingConfig(Config):
    TESTING = True
    raw_document_db_url = ''
    categorize_db_url = ''