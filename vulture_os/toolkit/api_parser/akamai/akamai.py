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
__doc__ = 'Akamai API Parser'


import datetime
import json
import logging
import requests
import base64
import urllib.parse

from akamai.edgegrid import EdgeGridAuth
from django.conf import settings
from django.utils import timezone
from toolkit.api_parser.api_parser import ApiParser

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('crontab')


class AkamaiParseError(Exception):
    pass


class AkamaiAPIError(Exception):
    pass


class AkamaiParser(ApiParser):
    ATTACK_KEYS = ["rules", "ruleMessages", "ruleTags", "ruleActions", "ruleData"]

    def __init__(self, data):
        super().__init__(data)

        self.akamai_host = data.get('akamai_host')
        self.akamai_client_secret = data.get('akamai_client_secret')
        self.akamai_access_token = data.get('akamai_access_token')
        self.akamai_client_token = data.get('akamai_client_token')
        self.akamai_config_id = data.get('akamai_config_id')

        self.version = "v1"

        if not self.akamai_host.startswith('https'):
            self.akamai_host = f"https://{self.akamai_host}"

        self.last_log_time = self.last_api_call

    def _connect(self):
        try:
            self.session = requests.Session()
            self.session.auth = EdgeGridAuth(
                client_token=self.akamai_client_token,
                client_secret=self.akamai_client_secret,
                access_token=self.akamai_access_token
            )

            return True

        except Exception as err:
            raise AkamaiAPIError(err)

    def get_logs(self, test=False):
        self._connect()

        url = f"{self.akamai_host}/siem/{self.version}/configs/{self.akamai_config_id}"

        params = {
            'from': int(self.last_log_time.timestamp())
        }

        if test:
            params['limit'] = 1

        response = self.session.get(
            url,
            params=params,
            proxies=self.proxies
        )

        if response.status_code != 200:
            raise AkamaiAPIError(f"Error on URL: {url} Status: {response.status_code} Content: {response.content}")

        for line in response.content.decode('UTF-8').split('\n'):
            if line == "":
                continue

            try:
                line = json.loads(line)
            except json.decoder.JSONDecodeError:
                continue

            yield line

            if test:
                break

    def _parse_log(self, log):
        timestamp = int(log['httpMessage']['start'])
        timestamp = timezone.make_aware(datetime.datetime.utcfromtimestamp(timestamp))

        if timestamp > self.last_log_time:
            self.last_log_time = timestamp

        tmp = {
            'time': timestamp.isoformat(),
            'httpMessage': log['httpMessage'],
            'geo': log['geo'],
            'attackData': {
                'clientIP': log['attackData'].get('clientIP', '0.0.0.1')
            }
        }

        # Urldecode and parse headers
        request_headers = urllib.parse.unquote(tmp['httpMessage'].get('requestHeaders', "-"))
        all_request_headers = dict()
        for r in request_headers.split("\r\n"):
            if r and r != "{p}":
                try:
                    name, value = r.split(": ", maxsplit=1)
                except:
                    name, value = r.split(":", maxsplit=1)[0], "-"
                all_request_headers[name] = value or "-"

        response_headers = urllib.parse.unquote(tmp['httpMessage'].get('responseHeaders', "-"))
        all_response_headers = {'Set-Cookie': []}
        for r in response_headers.split("\r\n"):
            if r and r != "{p}":
                try:
                    name, value = r.split(": ", maxsplit=1)
                except:
                    name, value = r.split(":", maxsplit=1)[0], "-"
                if name.lower().startswith("set-cookie"):
                    all_response_headers["Set-Cookie"].append(value)
                else:
                    all_response_headers[name] = value or '-'
        all_response_headers['Set-Cookie'] = "; ".join(all_response_headers['Set-Cookie']) or "-"

        tmp['httpMessage']['requestHeaders'] = all_request_headers
        tmp['httpMessage']['responseHeaders'] = all_response_headers

        # Unquote attackData fields and decode them in base64
        for key in self.ATTACK_KEYS:
            tmp_data = urllib.parse.unquote(log['attackData'][key]).split(';')

            values = []
            for data in tmp_data:
                if data:
                    values.append(base64.b64decode(data).decode('utf-8'))

            tmp['attackData'][key] = values

        return tmp

    def test(self):
        try:
            data = []
            self.last_log_time = timezone.now() - datetime.timedelta(minutes=15)
            for log in self.get_logs(test=True):
                data.append(self._parse_log(log))
                break

            return {
                'status': True,
                'data': data
            }

        except AkamaiAPIError as e:
            return {
                'status': False,
                'error': str(e)
            }

    def execute(self):
        try:
            while self.last_log_time < timezone.now():
                data = []
                for log in self.get_logs():
                    if "httpMessage" in log.keys():
                        try:
                            data.append(json.dumps(self._parse_log(log)))
                        except Exception as err:
                            raise AkamaiAPIError(err)

                self.write_to_file(data)
                self.frontend.last_api_call = self.last_log_time
                self.update_lock()

        except Exception as e:
            raise AkamaiParseError(e)