from amazon_advertising_api.regions import regions
from amazon_advertising_api.versions import versions
from io import BytesIO
from six.moves import urllib
import gzip
import json
import os
import base64


class AdvertisingApi:

    """Lightweight client library for Amazon Sponsored Products API."""

    def __init__(self,
                 client_id,
                 client_secret,
                 region,
                 profile_id=None,
                 access_token=None,
                 refresh_token=None,
                 sandbox=False):
        """
        Client initialization.

        :param client_id: Login with Amazon client Id that has been whitelisted
            for cpc_advertising:campaign_management
        :type client_id: string
        :param client_secret: Login with Amazon client secret key.
        :type client_id: string
        :param region: Region code for endpoint. See regions.py.
        :type region: string
        :param access_token: The access token for the advertiser account.
        :type access_token: string
        :param refresh_token: The refresh token for the advertiser account.
        :type refresh_token: string
        :param sandbox: Indicate whether you are operating in sandbox or prod.
        :type sandbox: boolean
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self.refresh_token = refresh_token

        self.api_version = versions['api_version']
        self.user_agent = 'AdvertisingAPI Python Client Library v{}'.format(
            versions['application_version'])
        self.profile_id = profile_id
        self.token_url = None

        if region in regions:
            if sandbox:
                self.endpoint = regions[region]['sandbox']
            else:
                self.endpoint = regions[region]['prod']
            self.token_url = regions[region]['token_url']
        else:
            raise KeyError('Region {} not found in regions.'.format(regions))

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        """Set access_token"""
        self._access_token = value

    def do_refresh_token(self):
        if self.refresh_token is None:
            return {'success': False,
                    'code': 0,
                    'response': 'refresh_token is empty.'}

        if self._access_token:
            self._access_token = urllib.parse.unquote(self._access_token)
        self.refresh_token = urllib.parse.unquote(self.refresh_token)

        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret}

        data = urllib.parse.urlencode(params)

        req = urllib.request.Request(
            url='https://{}'.format(self.token_url),
            data=data.encode('utf-8'))

        try:
            f = urllib.request.urlopen(req)
            response = f.read().decode('utf-8')
            if 'access_token' in response:
                json_data = json.loads(response)
                self._access_token = json_data['access_token']
                return {'success': True,
                        'code': f.code,
                        'response': self._access_token}
            else:
                return {'success': False,
                        'code': f.code,
                        'response': 'access_token not in response.'}
        except urllib.error.HTTPError as e:
            return {'success': False,
                    'code': e.code,
                    'response': '{msg}: {details}'.format(msg=e.msg, details=e.read())}

    def get_profiles(self):
        """
        Retrieves profiles associated with an auth token.

        :GET: /profiles
        :returns:
            :200: Success
            :401: Unauthorized
        """
        interface = 'profiles'
        return self._operation(interface)

    def get_profile(self, profile_id):
        """
        Retrieves a single profile by Id.

        :GET: /profiles/{profileId}
        :param profile_id: The Id of the requested profile.
        :type profile_id: string
        :returns:
            :200: List of **Profile**
            :401: Unauthorized
            :404: Profile not found
        """
        interface = 'profiles/{}'.format(profile_id)
        return self._operation(interface)

    def update_profiles(self, data):
        """
        Updates one or more profiles. Advertisers are identified using their
        profileIds.

        :PUT: /profiles
        :param data: A list of updates containing **profileId** and the
            mutable fields to be modified. Only daily budgets are mutable at
            this time.
        :type data: List of **Profile**
        :returns:
            :207: List of **ProfileResponse** reflecting the same order as the
                input
            :401: Unauthorized
        """
        interface = 'profiles'
        return self._operation(interface, data, method='PUT')

    def get_campaign(self, campaign_id):
        """
        Retrieves a campaign by Id. Note that this call returns the minimal
        set of campaign fields, but is more efficient than **getCampaignEx**.

        :GET: /campaigns/{campaignId}
        :param campaign_id: The Id of the requested campaign.
        :type campaign_id: string
        :returns:
            :200: Campaign
            :401: Unauthorized
            :404: Campaign not found
        """
        interface = 'campaigns/{}'. format(campaign_id)
        return self._operation(interface)

    def get_campaign_ex(self, campaign_id):
        """
        Retrieves a campaign and its extended fields by ID. Note that this
        call returns the complete set of campaign fields (including serving
        status and other read-only fields), but is less efficient than
        **getCampaign**.

        :GET: /campaigns/extended/{campaignId}
        :param campaign_id: The Id of the requested campaign.
        :type campaign_id: string
        :returns:
            :200: Campaign
            :401: Unauthorized
            :404: Campaign not found

        """
        interface = 'campaigns/extended/{}'. format(campaign_id)
        return self._operation(interface)

    def create_campaigns(self, data):
        """
        Creates one or more campaigns. Successfully created campaigns will be
        assigned unique **campaignIds**.

        :POST: /campaigns
        :param data: A list of up to 100 campaigns to be created.  Required
            fields for campaign creation are **name**, **campaignType**,
            **targetingType**, **state**, **dailyBudget** and **startDate**.
        :type data: List of **Campaign**
        :returns:
            :207: List of **CampaignResponse** reflecting the same order as the
                input.
            :401: Unauthorized
        """
        interface = 'campaigns'
        return self._operation(interface, data, method='POST')

    def update_campaigns(self, data):
        """
        Updates one or more campaigns.  Campaigns are identified using their
        **campaignIds**.

        :PUT: /campaigns
        :param data: A list of up to 100 updates containing **campaignIds** and
            the mutable fields to be modified. Mutable fields are **name**,
            **state**, **dailyBudget**, **startDate**, and **endDate**.
        :type data: List of **Campaign**
        :returns:
            :207: List of **CampaignResponse** reflecting the same order as the
                input
            :401: Unauthorized
        """
        interface = 'campaigns'
        return self._operation(interface, data, method='PUT')

    def archive_campaign(self, campaign_id):
        """
        Sets the campaign status to archived. This same operation can be
        performed via an update, but is included for completeness.

        :DELETE: /campaigns/{campaignId}
        :param campaign_id: The Id of the campaign to be archived.
        :type campaign_id: string
        :returns:
            :200: Success, campaign response
            :401: Unauthorized
            :404: Campaign not found
        """
        interface = 'campaigns/{}'.format(campaign_id)
        return self._operation(interface, method='DELETE')

    def list_campaigns(self, data=None):
        """
        Retrieves a list of campaigns satisfying optional criteria.

        :GET: /campaigns
        :param data: Optional, search criteria containing the following
            parameters.

        data may contain the following optional parameters:

        :param startIndex: 0-indexed record offset for the result set. 
            Defaults to 0.
        :type startIndex: Integer
        :param count: Number of records to include in the paged response. 
            Defaults to max page size.
        :type count: Integer
        :param campaignType: Restricts results to campaigns of a single 
            campaign type. Must be **sponsoredProducts**.
        :type campaignType: String
        :param stateFilter: Restricts results to campaigns with state within 
            the specified comma-separatedlist. Must be one of **enabled**, 
            **paused**, **archived**. Default behavior is to include all.
        :param name: Restricts results to campaigns with the specified name.
        :type name: String
        :param campaignFilterId: Restricts results to campaigns specified in 
            comma-separated list.
        :type campaignFilterId: String
        :returns:
            :200: Success. list of campaign
            :401: Unauthorized
        """
        interface = 'campaigns'
        return self._operation(interface, data)

    def list_campaigns_ex(self, data=None):
        """
        Retrieves a list of campaigns with extended fields satisfying
        optional filtering criteria.

        :GET: /campaigns/extended
        :param data: Optional, search criteria containing the following
            parameters.
        :type data: JSON string
        """
        interface = 'campaigns/extended'
        return self._operation(interface, data)

    def get_ad_group(self, ad_group_id):
        """
        Retrieves an ad group by Id. Note that this call returns the minimal
        set of ad group fields, but is more efficient than getAdGroupEx.

        :GET: /adGroups/{adGroupId}
        :param ad_group_id: The Id of the requested ad group.
        :type ad_group_id: string

        :returns:
            :200: Success, AdGroup response
            :401: Unauthorized
            :404: Ad group not found
        """
        interface = 'adGroups/{}'.format(ad_group_id)
        return self._operation(interface)

    def get_ad_group_ex(self, ad_group_id):
        """
        Retrieves an ad group and its extended fields by ID. Note that this
        call returns the complete set of ad group fields (including serving
        status and other read-only fields), but is less efficient than
        getAdGroup.

        :GET: /adGroups/extended/{adGroupId}
        :param ad_group_id: The Id of the requested ad group.
        :type ad_group_id: string

        :returns:
            :200: Success, AdGroup response
            :401: Unauthorized
            :404: Ad group not found
        """
        interface = 'adGroups/extended/{}'.format(ad_group_id)
        return self._operation(interface)

    def create_ad_groups(self, data):
        """
        Creates one or more ad groups. Successfully created ad groups will
        be assigned unique adGroupIds.

        :POST: /adGroups
        :param data: A list of up to 100 ad groups to be created. Required
            fields for ad group creation are campaignId, name, state and
            defaultBid.
        :type data: List of **AdGroup**

        :returns:
            :207: Multi-status. List of AdGroupResponse reflecting the same
                order as the input
            :401: Unauthorized
        """
        interface = 'adGroups'
        return self._operation(interface, data, method='POST')

    def update_ad_groups(self, data):
        """
        Updates one or more ad groups. Ad groups are identified using their
        adGroupIds.

        :PUT: /adGroups
        :param data: A list of up to 100 updates containing adGroupIds and the
            mutable fields to be modified.
        :type data: List of **AdGroup**

        :returns:
            :207: Multi-status. List of AdGroupResponse reflecting the same
                order as the input
            :401: Unauthorized
        """
        interface = 'adGroups'
        return self._operation(interface, data, method='PUT')

    def archive_ad_group(self, ad_group_id):
        """
        Sets the ad group status to archived. This same operation can be
        performed via an update, but is included for completeness.

        :DELETE: /adGroup/{adGroupId}
        :param ad_group_id: The Id of the ad group to be archived.
        :type ad_group_id: string

        :returns:
            :200: Success. AdGroupResponse
            :401: Unauthorized
            :404: Ad group not found
        """
        interface = 'adGroups/{}'.format(ad_group_id)
        return self._operation(interface, method='DELETE')

    def list_ad_groups(self, data=None):
        """
        Retrieves a list of ad groups satisfying optional criteria.

        :GET: /adGroups
        :param data: Parameter list of criteria.

        data may contain the following optional parameters:

        :param startIndex: 0-indexed record offset for the result
            set. Defaults to 0.
        :type startIndex: integer
        :param count: Number of records to include in the paged response.
            Defaults to max page size.
        :type count: integer
        :param campaignType: Restricts results to ad groups belonging to
            campaigns of the specified type. Must be sponsoredProducts
        :type campaignType: string
        :param campaignIdFilter: Restricts results to ad groups within
            campaigns specified in comma-separated list.
        :type campaignIdFilter: string
        :param adGroupIdFilter: Restricts results to ad groups specified in
            comma-separated list.
        :type adGroupIdFilter: string
        :param stateFilter: Restricts results to keywords with state within the
            specified comma-separatedlist. Must be one of enabled, paused,
            archived.  Default behavior is to include all.
        :type stateFilter: string
        :param name: Restricts results to ad groups with the specified name.
        :type name: string

        :returns:
            :200: Success. List of adGroup.
            :401: Unauthorized.

        """
        interface = 'adGroups'
        return self._operation(interface, data)

    def list_ad_groups_ex(self, data=None):
        """
        Retrieves a list of ad groups satisfying optional criteria.

        :GET: /adGroups/extended
        :param data: Parameter list of criteria.

        data may contain the following optional parameters:

        :param startIndex: 0-indexed record offset for the result
            set. Defaults to 0.
        :type startIndex: integer
        :param count: Number of records to include in the paged response.
            Defaults to max page size.
        :type count: integer
        :param campaignType: Restricts results to ad groups belonging to
            campaigns of the specified type. Must be sponsoredProducts
        :type campaignType: string
        :param campaignIdFilter: Restricts results to ad groups within
            campaigns specified in comma-separated list.
        :type campaignIdFilter: string
        :param adGroupIdFilter: Restricts results to ad groups specified in
            comma-separated list.
        :type adGroupIdFilter: string
        :param stateFilter: Restricts results to keywords with state within the
            specified comma-separatedlist. Must be one of enabled, paused,
            archived.  Default behavior is to include all.
        :type stateFilter: string
        :param name: Restricts results to ad groups with the specified name.
        :type name: string

        :returns:
            :200: Success. List of adGroup.
            :401: Unauthorized.
        """
        interface = 'adGroups/extended'
        return self._operation(interface, data)

    def get_biddable_keyword(self, keyword_id):
        """
        Retrieves a keyword by ID. Note that this call returns the minimal set 
        of keyword fields, but is more efficient than getBiddableKeywordEx.

        :GET: /keywords/{keywordId}
        :param keyword_id: The Id of the requested keyword.
        :type keyword_id: string

        :returns:
            :200: Success. Keyword.
            :401: Unauthorized.
            :404: Keyword not found.
        """
        interface = 'keywords/{}'.format(keyword_id)
        return self._operation(interface)

    def get_biddable_keyword_ex(self, keyword_id):
        """
        Retrieves a keyword and its extended fields by ID. Note that this call 
        returns the complete set of keyword fields (including serving status 
        and other read-only fields), but is less efficient than 
        getBiddableKeyword.

        :GET: /keywords/extended/{keywordId}
        :param keyword_id: The Id of the requested keyword.
        :type keyword_id: string

        :returns:
            :200: Success. Keyword.
            :401: Unauthorized.
            :404: Keyword not found.
        """
        interface = 'keywords/extended/{}'.format(keyword_id)
        return self._operation(interface)

    def create_biddable_keywords(self, data):
        """
        Creates one or more keywords. Successfully created keywords will be 
        assigned unique keywordIds.

        :POST: /keywords
        :param data: A list of up to 1000 keywords to be created. Required 
            fields for keyword creation are campaignId, adGroupId, keywordText, 
            matchType and state.
        :type data: List of **Keyword**
        """
        interface = 'keywords'
        return self._operation(interface, data, method='POST')

    def update_biddable_keywords(self, data):
        interface = 'keywords'
        return self._operation(interface, data, method='PUT')

    def archive_biddable_keyword(self, keyword_id):
        interface = 'keywords/{}'.format(keyword_id)
        return self._operation(interface, method='DELETE')

    def list_biddable_keywords(self, data=None):
        interface = 'keywords'
        return self._operation(interface, data)

    def list_biddable_keywords_ex(self, data=None):
        interface = 'keywords/extended'
        return self._operation(interface, data)

    def get_negative_keyword(self, negative_keyword_id):
        interface = 'negativeKeywords/{}'.format(negative_keyword_id)
        return self._operation(interface)

    def get_negative_keyword_ex(self, negative_keyword_id):
        interface = 'negativeKeywords/extended/{}'.format(negative_keyword_id)
        return self._operation(interface)

    def create_negative_keywords(self, data):
        interface = 'negativeKeywords'
        return self._operation(interface, data, method='POST')

    def update_negative_keywords(self, data):
        interface = 'negativeKeywords'
        return self._operation(interface, data, method='PUT')

    def archive_negative_keyword(self, negative_keyword_id):
        interface = 'negativeKeywords/{}'.format(negative_keyword_id)
        return self._operation(interface, method='DELETE')

    def list_negative_keywords(self, data=None):
        interface = 'negativeKeywords'
        return self._operation(interface, data)

    def list_negative_keywords_ex(self, data=None):
        interface = 'negativeKeywords/extended'
        return self._operation(interface, data)

    def get_campaign_negative_keyword(self, campaign_negative_keyword_id):
        interface = 'campaignNegativeKeywords/{}'.format(
            campaign_negative_keyword_id)
        return self._operation(interface)

    def get_campaign_negative_keyword_ex(self, campaign_negative_keyword_id):
        interface = 'campaignNegativeKeywords/extended/{}'.format(
            campaign_negative_keyword_id)
        return self._operation(interface)

    def create_campaign_negative_keywords(self, data):
        interface = 'campaignNegativeKeywords'
        return self._operation(interface, data, method='POST')

    def update_campaign_negative_keywords(self, data):
        interface = 'campaignNegativeKeywords'
        return self._operation(interface, data, method='PUT')

    def remove_campaign_negative_keyword(self, campaign_negative_keyword_id):
        interface = 'campaignNegativeKeywords/{}'.format(
            campaign_negative_keyword_id)
        return self._operation(interface, method='DELETE')

    def list_campaign_negative_keywords(self, data=None):
        interface = 'campaignNegativeKeywords'
        return self._operation(interface, data)

    def list_campaign_negative_keywords_ex(self, data=None):
        interface = 'campaignNegativeKeywords/extended'
        return self._operation(interface, data)

    def get_product_ad(self, product_ad_id):
        interface = 'productAds/{}'.format(product_ad_id)
        return self._operation(interface)

    def get_product_ad_ex(self, product_ad_id):
        interface = 'productAds/extended/{}'.format(product_ad_id)
        return self._operation(interface)

    def create_product_ads(self, data):
        interface = 'productAds'
        return self._operation(interface, data, method='POST')

    def update_product_ads(self, data):
        interface = 'productAds'
        return self._operation(interface, data, method='PUT')

    def archive_product_ads(self):
        pass

    def list_product_ads(self, data=None):
        interface = 'productAds'
        return self._operation(interface, data)

    def list_product_ads_ex(self, data=None):
        interface = 'productAds/extended'
        return self._operation(interface, data)

    def request_snapshot(self, record_type=None, snapshot_id=None, data=None):
        if record_type is not None:
            interface = '{}/snapshot'.format(record_type)
            return self._operation(interface, data, method='POST')
        elif snapshot_id is not None:
            interface = 'snapshots/{}'.format(snapshot_id)
            return self._operation(interface, data)

    def request_report(self, record_type=None, report_id=None, data=None):
        if record_type is not None:
            interface = '{}/report'.format(record_type)
            return self._operation(interface, data, method='POST')
        elif report_id is not None:
            interface = 'reports/{}'.format(report_id)
            return self._operation(interface)

    def get_report(self, report_id):
        interface = 'reports/{}'.format(report_id)
        res = self._operation(interface)
        if json.loads(res['response'])['status'] == 'SUCCESS':
            res = self._download(
                location=json.loads(res['response'])['location'])
            return res
        else:
            return res

    def get_snapshot(self, snapshot_id):
        interface = 'snapshots/{}'.format(snapshot_id)
        res = self._operation(interface)
        if json.loads(res['response'])['status'] == 'SUCCESS':
            res = self._download(
                location=json.loads(res['response'])['location'])
            return res
        else:
            return res

    def _download(self, location):
        headers = {'Authorization': 'Bearer {}'.format(self._access_token),
                   'Content-Type': 'application/json',
                   'User-Agent': self.user_agent}

        if self.profile_id is not None:
            headers['Amazon-Advertising-API-Scope'] = self.profile_id
        else:
            raise ValueError('Invalid profile Id.')

        opener = urllib.request.build_opener(NoRedirectHandler())
        urllib.request.install_opener(opener)
        req = urllib.request.Request(url=location, headers=headers, data=None)
        try:
            response = urllib.request.urlopen(req)
            if 'location' in response:
                if response['location'] is not None:
                    req = urllib.request.Request(url=response['location'])
                    res = urllib.request.urlopen(req)
                    res_data = res.read()
                    buf = BytesIO(res_data)
                    f = gzip.GzipFile(fileobj=buf)
                    data = f.read()
                    return {'success': True,
                            'code': res.code,
                            'response': json.loads(data.decode('utf-8'))}
                else:
                    return {'success': False,
                            'code': response.code,
                            'response': 'Location is empty.'}
            else:
                return {'success': False,
                        'code': response.code,
                        'response': 'Location not found.'}
        except urllib.error.HTTPError as e:
            return {'success': False,
                    'code': e.code,
                    'response': '{msg}: {details}'.format(msg=e.msg, details=e.read())}

    def _operation(self, interface, params=None, method='GET'):
        """
        Makes that actual API call.

        :param interface: Interface used for this call.
        :type interface: string
        :param params: Parameters associated with this call.
        :type params: GET: string POST: dictionary
        :param method: Call method. Should be either 'GET', 'PUT', or 'POST'
        :type method: string
        """
        if self._access_token is None:
            return {'success': False,
                    'code': 0,
                    'response': 'access_token is empty.'}

        headers = {'Authorization': 'Bearer {}'.format(self._access_token),
                   'Content-Type': 'application/json',
                   'User-Agent': self.user_agent}

        if self.profile_id is not None and self.profile_id != '':
            headers['Amazon-Advertising-API-Scope'] = self.profile_id
        elif 'profiles' not in interface:
            # Profile ID is required for all calls beyond authentication and getting profile info
            return {'success': False,
                    'code': 0,
                    'response': 'profile_id is empty.'}

        data = None

        if method == 'GET':
            if params is not None:
                p = '?{}'.format(urllib.parse.urlencode(params))
            else:
                p = ''

            url = 'https://{host}/{api_version}/{interface}{params}'.format(
                host=self.endpoint,
                api_version=self.api_version,
                interface=interface,
                params=p)
        else:
            if params is not None:
                data = json.dumps(params).encode('utf-8')

            url = 'https://{host}/{api_version}/{interface}'.format(
                host=self.endpoint,
                api_version=self.api_version,
                interface=interface)

        req = urllib.request.Request(url=url, headers=headers, data=data)
        req.method = method

        try:
            f = urllib.request.urlopen(req)
            return {'success': True,
                    'code': f.code,
                    'response': f.read().decode('utf-8')}
        except urllib.error.HTTPError as e:
            return {'success': False,
                    'code': e.code,
                    'response': '{msg}: {details}'.format(msg=e.msg, details=e.read())}


class NoRedirectHandler(urllib.request.HTTPErrorProcessor):

    """Handles report and snapshot redirects."""

    def http_response(self, request, response):
        if response.code == 307:
            if 'Location' in response.headers:
                return {'code': 307,
                        'location': response.headers['Location']}
            else:
                return {'code': response.code, 'location': None}
        else:
            return urllib.request.HTTPErrorProcessor.http_response(
                self, request, response)

    https_response = http_response
