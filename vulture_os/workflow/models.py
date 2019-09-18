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
__doc__ = 'Frontends & Listeners model classes'

# Django system imports
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from djongo import models

# Django project imports
from applications.backend.models import Backend
from darwin.access_control.models import AccessControl
from authentication.user_portal.models import UserAuthentication
from darwin.defender_policy.models import DefenderPolicy
from services.frontend.models import Frontend
from services.haproxy.haproxy import HAPROXY_OWNER, HAPROXY_PERMS, HAPROXY_PATH
from system.cluster.models import Cluster, Node
from toolkit.network.network import get_hostname

# Extern modules imports
from jinja2 import Environment, FileSystemLoader

# Required exceptions imports
from jinja2.exceptions import (TemplateAssertionError, TemplateNotFound, TemplatesNotFound, TemplateRuntimeError,
                               TemplateSyntaxError, UndefinedError)
from services.exceptions import ServiceJinjaError
from system.exceptions import VultureSystemConfigError
import json

# Logger configuration imports
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('gui')

# Jinja template for backends rendering
JINJA_PATH = "/home/vlt-os/vulture_os/workflow/config/"
JINJA_TEMPLATE = "haproxy_portal.conf"

WORKFLOW_OWNER = HAPROXY_OWNER
WORKFLOW_PERMS = HAPROXY_PERMS


class WorkflowACL(models.Model):
    workflow = models.ForeignKey('Workflow', on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    access_control = models.ForeignKey(AccessControl, on_delete=models.PROTECT, null=True)
    action_satisfy = models.TextField()
    action_not_satisfy = models.TextField()
    redirect_url_satisfy = models.TextField()
    redirect_url_not_satisfy = models.TextField()
    before_policy = models.BooleanField(default=True)

    def generate_condition(self, acls_names):
        conditions = []

        for tmp_acls in acls_names:
            acls = []
            for a in tmp_acls:
                if self.action_satisfy == "200":
                    acls.append("!{}".format(a))
                elif self.action_not_satisfy == "200":
                    acls.append(a)

            conditions.append(" ".join(acls))

        return conditions

    def to_dict(self):
        return {
            'access_control': self.access_control.to_template(),
            'action_satisfy': self.action_satisfy,
            'action_not_satisfy': self.action_not_satisfy,
            'redirect_url_satisfy': self.redirect_url_satisfy,
            'redirect_url_not_satisfy': self.redirect_url_not_satisfy,
            'before_policy': self.before_policy
        }


class Workflow(models.Model):
    """ Join class of Frontend-Backend """
    enabled = models.BooleanField(default=True)
    name = models.TextField(help_text=_("Friendly name"), default="")

    """ Frontend """
    frontend = models.ForeignKey(
        Frontend,
        on_delete=models.PROTECT,
        help_text=_("Frontend"),
    )

    defender_policy = models.ForeignKey(
        DefenderPolicy,
        on_delete=models.CASCADE,
        null=True
    )

    """ FQDN """
    fqdn = models.TextField(
        help_text=_("Public name")
    )
    public_dir = models.TextField(
        help_text=_("Directory on which apply the conf")
    )
    """ Backend """
    backend = models.ForeignKey(
        Backend,
        on_delete=models.PROTECT,
        help_text=_("Backend"),
    )

    workflow_json = models.ListField(default=[])

    class Meta:
        unique_together = (('frontend', 'fqdn', 'public_dir', 'backend'),)

    @staticmethod
    def str_attrs():
        """ List of attributes required by __str__ method """
        return ['frontend', 'backend']

    def __str__(self):
        return "'{}' ==> '{}'".format(str(self.frontend), str(self.backend))

    def to_html_template(self):
        """ Dictionary used to render object as html
        :return     Dictionnary of configuration parameters
        """
        """ Retrieve list/custom objects """

        """ And returns the attributes of the class """
        return {
            'id': str(self.id),
            'name': self.name,
            'fqdn': self.fqdn,
            'enabled': self.enabled,
            'frontend': str(self.frontend),
            'public_dir': self.public_dir,
            'backend': str(self.backend),
            'defender_policy': str(self.defender_policy),
            'frontend_status': dict(self.frontend.status),
            'backend_status': dict(self.backend.status),
            'acls': self.workflowacl_set.count()
        }

    def to_dict(self):
        result = {
            'id': str(self.id),
            'name': self.name,
            'enabled': self.enabled,
            'frontend': self.frontend.to_dict(),
            'backend': self.backend.to_dict(),
            'workflow_json': json.dumps(self.workflow_json),
            'frontend_status': dict(self.frontend.status),
            'backend_status': dict(self.backend.status),
            'public_dir': self.public_dir,
            'backend': str(self.backend),
            'defender_policy': str(self.defender_policy),
            'acls': [acl.to_dict() for acl in self.workflowacl_set.all()]
        }

        if self.fqdn:
            result['fqdn'] = self.fqdn
        if self.public_dir:
            result['public_dir'] = self.public_dir

        return result

    def to_template(self):
        """ Dictionary used to create configuration file

        :return     Dictionnary of configuration parameters
        """
        """ Retrieve list/custom objects """

        """ And returns the attributes of the class """
        return {
            'id': str(self.id),
            'name': self.name,
            'enabled': self.enabled,
            'frontend': self.frontend,
            'backend': self.backend
        }

    def generate_conf(self):
        """ Render the conf with Jinja template and self.to_template() method
        :return     The generated configuration as string, or raise
        """
        # The following var is only used by error, do not forget to adapt if needed
        template_name = JINJA_PATH + JINJA_TEMPLATE
        try:
            jinja2_env = Environment(loader=FileSystemLoader(JINJA_PATH))
            template = jinja2_env.get_template(JINJA_TEMPLATE)
            return template.render({'conf': self.to_template(),
                                    'nodes': Node.objects.exclude(name=get_hostname())})
        # In ALL exceptions, associate an error message
        # The exception instantiation MUST be IN except statement, to retrieve traceback in __init__
        except TemplateNotFound:
            exception = ServiceJinjaError("The following file cannot be found : '{}'".format(template_name), "haproxy")
        except TemplatesNotFound:
            exception = ServiceJinjaError("The following files cannot be found : '{}'".format(template_name), "haproxy")
        except (TemplateAssertionError, TemplateRuntimeError):
            exception = ServiceJinjaError("Unknown error in template generation: {}".format(template_name), "haproxy")
        except UndefinedError:
            exception = ServiceJinjaError("A variable is undefined while trying to render the following template: "
                                          "{}".format(template_name), "haproxy")
        except TemplateSyntaxError:
            exception = ServiceJinjaError("Syntax error in the template: '{}'".format(template_name), "haproxy")
        # If there was an exception, raise a more general exception with the message and the traceback
        raise exception

    def get_base_filename(self):
        """ Return the workflow filename, without directory """
        return "workflow_{}.cfg".format(self.id)

    def get_filename(self):
        """  """
        return "{}/{}".format(HAPROXY_PATH, self.get_base_filename())

    def save_conf(self):
        """
        :return   A message of what has been done
        """
        if not self.authentication:
            return "No authentication activated, no need to write portal conf."

        params = [self.get_filename(), self.generate_conf(), WORKFLOW_OWNER, WORKFLOW_PERMS]
        try:
            api_res = Cluster.api_request("system.config.models.write_conf", config=params)
            if not api_res.get('status'):
                raise VultureSystemConfigError(". API request failure ", traceback=api_res.get('message'))
        except Exception:
            raise VultureSystemConfigError("API request failure.")

        return "Workflow configuration written."

    def get_redirect_uri(self):
        listener = None
        for l in self.frontend.listener_set.all().only('tls_profiles', 'port'):
            """ TLS priority """
            if l.tls_profiles.count() > 0:
                listener = l

        """ No TLS listener, get the first one """
        if not listener:
            listener = self.frontend.listener_set.first()

        port = listener.port

        if listener.tls_profiles.count() > 0:
            if port == "443":
                url = "https://" + str(self.fqdn) + str(self.public_dir)
            else:
                url = "https://" + str(self.fqdn) + ":" + str(port) + str(self.public_dir)
        else:
            if port == "80":
                url = "http://" + str(self.fqdn) + str(self.public_dir)
            else:
                url = "http://" + str(self.fqdn) + ":" + str(port) + str(self.public_dir)
        return url