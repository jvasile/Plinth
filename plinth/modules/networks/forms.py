#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _, ugettext_lazy

from plinth import cfg
from plinth import network
from plinth.utils import format_lazy, import_from_gi
nm = import_from_gi('NM', '1.0')


class ConnectionTypeSelectForm(forms.Form):
    """Form to select type for new connection."""
    connection_type = forms.ChoiceField(
        label=_('Connection Type'),
        choices=[(key, value)
                 for key, value in network.CONNECTION_TYPE_NAMES.items()])


class ConnectionForm(forms.Form):
    """Base form to create/edit a connection."""
    name = forms.CharField(label=_('Connection Name'))
    interface = forms.ChoiceField(
        label=_('Physical Interface'),
        choices=(),
        help_text=_('The network device that this connection should be bound '
                    'to.'))
    zone = forms.ChoiceField(
        label=_('Firewall Zone'),
        help_text=_('The firewall zone will control which services are \
available over this interfaces. Select Internal only for trusted networks.'),
        choices=[('external', 'External'), ('internal', 'Internal')])
    ipv4_method = forms.ChoiceField(
        label=_('IPv4 Addressing Method'),
        help_text=format_lazy(
            ugettext_lazy(
                '"Automatic" method will make {box_name} acquire '
                'configuration from this network making it a client. "Shared" '
                'method will make {box_name} act as a router, configure '
                'clients on this network and share its Internet connection.'),
            box_name=ugettext_lazy(cfg.box_name)),
        choices=[('auto', 'Automatic (DHCP)'),
                 ('shared', 'Shared'),
                 ('manual', 'Manual')])
    ipv4_address = forms.CharField(
        label=_('Address'),
        validators=[validators.validate_ipv4_address],
        required=False)
    ipv4_netmask = forms.CharField(
        label=_('Netmask'),
        help_text=_('Optional value. If left blank, a default netmask '
                    'based on the address will be used.'),
        validators=[validators.validate_ipv4_address],
        required=False)
    ipv4_gateway = forms.CharField(
        label=_('Gateway'),
        help_text=_('Optional value.'),
        validators=[validators.validate_ipv4_address],
        required=False)
    ipv4_dns = forms.CharField(
        label=_('DNS Server'),
        help_text=_('Optional value. If this value is given and IPv4 '
                    'addressing method is "Automatic", the DNS Servers '
                    'provided by a DHCP server will be ignored.'),
        validators=[validators.validate_ipv4_address],
        required=False)
    ipv4_second_dns = forms.CharField(
        label=_('Second DNS Server'),
        help_text=_('Optional value. If this value is given and IPv4 '
                    'Addressing Method is "Automatic", the DNS Servers '
                    'provided by a DHCP server will be ignored.'),
        validators=[validators.validate_ipv4_address],
        required=False)

    @staticmethod
    def _get_interface_choices(device_type):
        """Return a list of choices for a given device type."""
        interfaces = network.get_interface_list(device_type)
        choices = [('', _('-- select --'))]
        for interface, mac in interfaces.items():
            display_string = '{interface} ({mac})'.format(interface=interface,
                                                          mac=mac)
            choices.append((interface, display_string))

        return choices

    def get_settings(self):
        """Return settings dict from cleaned data."""
        settings = {}
        settings['common'] = {
            'name': self.cleaned_data['name'],
            'interface': self.cleaned_data['interface'],
            'zone': self.cleaned_data['zone'],
        }
        settings['ipv4'] = self.get_ipv4_settings()
        return settings

    def get_ipv4_settings(self):
        """Return IPv4 dict from cleaned data."""
        ipv4 = {
            'method': self.cleaned_data['ipv4_method'],
            'address': self.cleaned_data['ipv4_address'],
            'netmask': self.cleaned_data['ipv4_netmask'],
            'gateway': self.cleaned_data['ipv4_gateway'],
            'dns': self.cleaned_data['ipv4_dns'],
            'second_dns': self.cleaned_data['ipv4_second_dns'],
        }
        return ipv4


class EthernetForm(ConnectionForm):
    """Form to create/edit a ethernet connection."""
    def __init__(self, *args, **kwargs):
        """Initialize the form, populate interface choices."""
        super(EthernetForm, self).__init__(*args, **kwargs)
        choices = self._get_interface_choices(nm.DeviceType.ETHERNET)
        self.fields['interface'].choices = choices

    def get_settings(self):
        """Return settings dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = '802-3-ethernet'
        return settings


class PPPoEForm(EthernetForm):
    """Form to create a new PPPoE connection."""
    ipv4_method = None
    ipv4_address = None
    ipv4_netmask = None
    ipv4_gateway = None
    ipv4_dns = None
    ipv4_second_dns = None

    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput(render_value=True))
    show_password = forms.BooleanField(label=_('Show password'),
                                       required=False)

    def get_settings(self):
        """Return setting dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = 'pppoe'
        settings['pppoe'] = {
            'username': self.cleaned_data['username'],
            'password': self.cleaned_data['password'],
        }
        return settings

    def get_ipv4_settings(self):
        """Return IPv4 settings from cleaned data."""
        return None


class WifiForm(ConnectionForm):
    """Form to create/edit a Wi-Fi connection."""
    field_order = ['name', 'interface', 'zone', 'ssid', 'mode', 'auth_mode',
                   'passphrase', 'ipv4_method', 'ipv4_address', 'ipv4_netmask',
                   'ipv4_gateway', 'ipv4_dns', 'ipv4_second_dns']

    ssid = forms.CharField(
        label=_('SSID'),
        help_text=_('The visible name of the network.'))
    mode = forms.ChoiceField(
        label=_('Mode'),
        choices=[('infrastructure', 'Infrastructure'),
                 ('ap', 'Access Point'),
                 ('adhoc', 'Ad-hoc')])
    auth_mode = forms.ChoiceField(
        label=_('Authentication Mode'),
        help_text=_('Select WPA if the wireless network is secured and \
requires clients to have the password to connect.'),
        choices=[('wpa', 'WPA'), ('open', 'Open')])
    passphrase = forms.CharField(
        label=_('Passphrase'),
        validators=[validators.MinLengthValidator(8)],
        required=False)

    def __init__(self, *args, **kwargs):
        """Initialize the form, populate interface choices."""
        super(WifiForm, self).__init__(*args, **kwargs)
        choices = self._get_interface_choices(nm.DeviceType.WIFI)
        self.fields['interface'].choices = choices

    def get_settings(self):
        """Return setting dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = '802-11-wireless'
        settings['wireless'] = {
            'ssid': self.cleaned_data['ssid'],
            'mode': self.cleaned_data['mode'],
            'auth_mode': self.cleaned_data['auth_mode'],
            'passphrase': self.cleaned_data['passphrase'],
        }
        return settings
