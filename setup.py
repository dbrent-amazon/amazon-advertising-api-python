from setuptools import setup
import amazon_advertising_api.versions as aa_versions


setup(
    name='amazon_advertising_api',
    packages=['amazon_advertising_api'],
    version=aa_versions.versions['application_version'],
    description='Unofficial Amazon Sponsored Products Python client library.',
    url='https://github.com/sguermond/amazon-advertising-api-python')
