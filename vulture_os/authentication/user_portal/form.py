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
__doc__ = 'UserAuthentication and UserSSO dedicated form class'

# Django system imports
from django.conf import settings
from django.forms import (CheckboxInput, ModelForm, ModelChoiceField, ModelMultipleChoiceField, NumberInput, Select,
                          SelectMultiple, TextInput)
from django.utils.translation import ugettext_lazy as _

# Django project imports
from applications.portal_template.models import portalTemplate
from authentication.base_repository import BaseRepository
from authentication.ldap.models import LDAPRepository
from authentication.otp.models import OTPRepository
from authentication.user_portal.models import (AUTH_TYPE_CHOICES, SSO_TYPE_CHOICES, SSO_BASIC_MODE_CHOICES,
                                               SSO_CONTENT_TYPE_CHOICES, UserAuthentication)

# Extern modules imports

# Required exceptions imports

# Logger configuration imports
import logging

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('gui')


class UserAuthenticationForm(ModelForm):
    repository = ModelChoiceField(
        label=_("Authentication repository"),
        queryset=BaseRepository.objects.exclude(subtype="OTP").only(*BaseRepository.str_attrs()),
        widget=Select(attrs={'class': 'form-control select2'}),
    )
    repositories_fallback = ModelMultipleChoiceField(
        label=_("Authentication fallback repositories"),
        queryset=BaseRepository.objects.exclude(subtype="OTP").only(*BaseRepository.str_attrs()),
        widget=SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )

    class Meta:
        model = UserAuthentication
        fields = ('name', 'enable_tracking', 'auth_type', 'portal_template', 'repository', 'repositories_fallback',
                  'auth_timeout', 'enable_timeout_restart', 'enable_captcha', 'otp_repository', 'otp_max_retry',
                  'disconnect_url', 'enable_disconnect_message', 'enable_disconnect_portal', 'enable_registration',
                  'group_registration', 'update_group_registration')
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'enable_tracking': CheckboxInput(attrs={'class': 'form-control js-switch'}),
            'auth_type': Select(choices=AUTH_TYPE_CHOICES, attrs={'class': 'form-control select2'}),
            'portal_template': Select(choices=portalTemplate.objects.all().only(*portalTemplate.str_attrs()),
                                      attrs={'class': 'form-control select2'}),
            'auth_timeout': NumberInput(attrs={'class': 'form-control'}),
            'enable_timeout_restart': CheckboxInput(attrs={'class': 'form-control js-switch'}),
            'enable_captcha': CheckboxInput(attrs={'class': 'form-control js-switch'}),
            'otp_repository': Select(choices=OTPRepository.objects.all().only(*OTPRepository.str_attrs()),
                                     attrs={'class': 'form-control select2'}),
            'otp_max_retry': NumberInput(attrs={'class': 'form-control'}),
            'disconnect_url': TextInput(attrs={'class': 'form-control'}),
            'enable_disconnect_message': CheckboxInput(attrs={'class': 'form-control js-switch'}),
            'enable_disconnect_portal': CheckboxInput(attrs={'class': 'form-control js-switch'}),
            'enable_registration': CheckboxInput(attrs={'class': 'form-control js-switch'}),
            'group_registration': TextInput(attrs={'class': 'form-control'}),
            'update_group_registration': CheckboxInput(attrs={'class': 'form-control js-switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the blank input generated by django
        for field_name in ['portal_template', 'repository', 'auth_type', 'repositories_fallback']:
            self.fields[field_name].empty_label = None
        self.fields['otp_repository'].empty_label = "No double authentication"
        # Set fields as non required in POST data
        for field in ['portal_template', 'otp_repository', 'otp_max_retry', 'group_registration',
                      'update_group_registration']:
            self.fields[field].required = False

    def clean_name(self):
        """ Replace all spaces by underscores to prevent bugs later """
        return self.cleaned_data['name'].replace(' ', '_')

    def clean(self):
        """ Verify required field depending on other fields """
        # Mandatory to prevent bug in Django
        if not self.cleaned_data.get('repositories_fallback'):
            self.cleaned_data['repositories_fallback'] = []

        cleaned_data = super().clean()
        """ Portal template is required if auth_type = HTTP """
        if cleaned_data.get('auth_type') == "http" and not cleaned_data.get('portal_template'):
            self.add_error('portal_template', "This field is required with HTTP auth type.")

        """ Verify if main repository == repository fallback """
        for repo in self.cleaned_data.get('repositories_fallback'):
            if repo == self.cleaned_data.get('repository'):
                self.add_error('repositories_fallback', "This is useless to use the main repository as fallback.")

        """ otp_max_retry required if otp_repository """
        if cleaned_data.get('otp_repository') and not cleaned_data.get('otp_max_retry'):
            self.add_error('otp_max_retry', "This field is required if an OTP repository has been chosen.")
        """ disconnect_url required if enable_disconnect_message or enable_disconnect_portal """
        if cleaned_data.get('enable_disconnect_message') or cleaned_data.get('enable_disconnect_portal'):
            if not cleaned_data.get('disconnect_url'):
                self.add_error('disconnect_url', "This field is required if 'Disconnect message' or 'Destroy portal "
                                                 "session' has been enabled.")

        """ group_registration required if enable_registration """
        repo = LDAPRepository.objects.filter(pk=cleaned_data.get('repository')).first()
        # If enable registration with LDAP Repo : group_registration required
        if cleaned_data.get('enable_registration') and repo and not cleaned_data.get('group_registration'):
            self.add_error('group_registration', "This field is required if registration enabled.")
        if cleaned_data.get('enable_registration') and (cleaned_data.get('group_registration') or
                                                        cleaned_data.get('update_group_registration')) \
                and not repo:
            self.add_error('group_registration', "To use this field, the mail repository must be LDAP.")
            self.add_error('update_group_registration', "To use this field, the mail repository must be LDAP.")

        return cleaned_data