#!/home/vlt-os/env/bin/python
"""This file is part of Vulture OS.

Vulture OS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture OS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture OS.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "4.0.0"
__maintainer__ = "Vulture OS"
__email__ = "contact@vultureproject.org"
__doc__ = 'Office365 API Parser'


import datetime
import logging
import requests

from django.conf import settings
from toolkit.api_parser.api_parser import ApiParser

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('crontab')


class Office365ParseError(Exception):
    pass


class Office365APIError(Exception):
    pass


class Office365Parser(ApiParser):
    def __init__(self, data):
        super().__init__(data)

        self.office365_client_id = data.get('office365_client_id')
        self.office365_tenant_id = data.get('office365_tenant_id')
        self.office365_client_secret = data.get('office365_client_secret')

        self.grant_type = "client_credentials"

        self.office365_login_uri = "https://login.windows.net"

        version = "v1.0"

        self.office365_manage_uri = f"https://manage.office.com/api/{version}"

        self.access_token = False
        self.expires_on = False

    def _get_access_token(self):
        if not self.expires_on or datetime.datetime.now() > self.expires_on:
            self.__connect()
        else:
            return self.access_token

        return self._get_access_token()

    def __connect(self):
        uri = f"{self.office365_login_uri}/{self.office365_tenant_id}/oauth2/token"

        response = requests.post(
            uri,
            data={
                'grant_type': self.grant_type,
                'resource': 'https://manage.office.com',
                'client_id': self.office365_client_id,
                'client_assertion_type': 'urn%3Aietf%3Aparams%3Aoauth',
                'client_secret': self.office365_client_secret
            }
        )

        if response.status_code != 200:
            raise Office365APIError(response.content)

        data = response.json()

        self.access_token = data['access_token']
        self.expires_on = datetime.datetime.fromtimestamp(int(data['expires_on']))

    def _get_feed(self, test=False):
        access_token = self._get_access_token()

        url = f"{self.office365_manage_uri}/{self.office365_tenant_id}/activity/feed/subscriptions/content"

        response = requests.get(
            url,
            params={
                'contentType': "Audit.SharePoint",
                'PublisherIdentifier': self.office365_tenant_id
            },
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        for feed in response.json():
            yield feed['contentUri']

            if test:
                break

    def _get_logs(self, url):
        access_token = self._get_access_token()

        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {access_token}'
            }
        )

        for tmp_log in response.json():
            yield tmp_log

    def test(self):
        try:
            data = []
            for feed_url in self._get_feed(test=True):
                for log in self._get_logs(feed_url):
                    data.append(log)

                    break
                break

            return {
                'status': True,
                'data': data
            }
        except Office365APIError as e:
            return {
                'status': False,
                'error': str(e)
            }

    def execute(self):
        try:
            pass
        except Exception as e:
            raise Office365ParseError(e)
