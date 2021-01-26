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
__author__ = "Kevin GUILLEMOT"
__credits__ = []
__license__ = "GPLv3"
__version__ = "4.0.0"
__maintainer__ = "Vulture OS"
__email__ = "contact@vultureproject.org"
__doc__ = 'OpenIDRepository dedicated form class'

# Django system imports
from django.conf import settings
from django.core.validators import RegexValidator
from django.forms import CheckboxInput, ModelForm, NumberInput, PasswordInput, Select, TextInput
# Django project imports
from authentication.openid.models import OpenIDRepository, PROVIDERS_TYPE

# Extern modules imports
from re import match as re_match

# Required exceptions imports
from django.forms import ValidationError

# Logger configuration imports
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('gui')


class OpenIDRepositoryForm(ModelForm):

    class Meta:
        model = OpenIDRepository
        fields = ('name', 'provider', 'provider_url', 'client_id', 'client_secret')
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'provider': Select(choices=PROVIDERS_TYPE, attrs={'class': 'form-control select2'}),
            'provider_url': TextInput(attrs={'class': 'form-control'}),
            'client_id': TextInput(attrs={'class': 'form-control'}),
            'client_secret': TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the blank input generated by django
        for field_name in ['provider']:
            self.fields[field_name].empty_label = None
        # Set all fields as non required
        for field in []:
            self.fields[field].required = False
        if not self.initial.get('name'):
            self.fields['name'].initial = "OpenID Repository"

    def clean_name(self):
        """ Replace all spaces by underscores to prevent bugs later """
        return self.cleaned_data['name'].replace(' ', '_')

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean()

        return cleaned_data
