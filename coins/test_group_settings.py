from .test_settings import *
INSTALLED_APPS = [*INSTALLED_APPS, 'torob_integration.apps.TorobIntegrationConfig']
ROOT_URLCONF = 'coins.test_group_urls'
MEDIA_URL = '/media/'
ALLOWED_HOSTS = ['testserver']
