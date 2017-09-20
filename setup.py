from setuptools import setup
import amazon_advertising_api.versions as aa_versions


setup(
    name='amazon_advertising',
    packages=['pay_with_amazon'],
    version=aa_versions.versions['application_version'],
    description='Unofficial Amazon Sponsored Products Python client library.',
    url='https://github.com/sguermond/amazon-advertising-api-python')
