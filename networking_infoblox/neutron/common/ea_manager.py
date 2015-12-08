# Copyright 2015 Infoblox Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from infoblox_client import objects as ib_objects
from neutron.api.v2 import attributes
from neutron.extensions import external_net
from neutron.extensions import providernet

from networking_infoblox.neutron.common import constants as const


def get_ea_for_network_view(tenant_id):
    """Generates EAs for Network View.

    :param tenant_id: tenant_id
    :return: dict with extensible attributes ready to be sent as part of
    NIOS WAPI
    """
    # OpenStack should not own entire network view,
    # since shared or external networks may be created in it
    attributes = {const.EA_TENANT_ID: tenant_id,
                  const.EA_CLOUD_API_OWNED: 'False'}
    return ib_objects.EA(attributes)


def get_ea_for_network(user_id, tenant_id, network, subnet):
    """Generates EAs for Network.

    :param user_id: user_id
    :param tenant_id: tenant_id
    :param subnet: neutron subnet object
    :param network: neutron network object
    :return: dict with extensible attributes ready to be sent as part of
    NIOS WAPI
    """
    subnet = {} if subnet is None else subnet
    network = {} if network is None else network

    network_type = network.get(providernet.NETWORK_TYPE)
    physical_network = network.get(providernet.PHYSICAL_NETWORK)
    segmentation_id = network.get(providernet.SEGMENTATION_ID)

    attributes = {const.EA_SUBNET_ID: subnet.get('id'),
                  const.EA_SUBNET_NAME: subnet.get('name'),
                  const.EA_NETWORK_ID: network.get('id'),
                  const.EA_NETWORK_NAME: network.get('name'),
                  const.EA_NETWORK_ENCAP: network_type,
                  const.EA_SEGMENTATION_ID: segmentation_id,
                  const.EA_PHYSICAL_NETWORK_NAME: physical_network}

    common_ea = get_common_ea(network, user_id, tenant_id, for_network=True)
    attributes.update(common_ea)

    return ib_objects.EA(attributes)


def get_ea_for_range(user_id, tenant_id, network):
    return ib_objects.EA(get_common_ea(network, user_id, tenant_id))


def get_dict_for_ip(port_id, device_owner, device_id,
                    vm_id, ip_type):
    return {const.EA_PORT_ID: port_id,
            const.EA_PORT_DEVICE_OWNER: device_owner,
            const.EA_PORT_DEVICE_ID: device_id,
            const.EA_VM_ID: vm_id,
            const.EA_IP_TYPE: ip_type}


def get_default_ea_for_ip(user_id, tenant_id):
    common_ea = get_common_ea(None, user_id, tenant_id)
    ip_dict = get_dict_for_ip(None, None, None, None, const.IP_TYPE_FIXED)
    common_ea.update(ip_dict)
    return ib_objects.EA(common_ea)


def get_ea_for_ip(user_id, tenant_id, network, port_id, device_id,
                  device_owner):
    # for gateway ip, no instance id exists
    instance_id = device_id
    common_ea = get_common_ea(network, user_id, tenant_id)
    ip_dict = get_dict_for_ip(port_id, device_owner, device_id,
                              instance_id, const.IP_TYPE_FIXED)
    common_ea.update(ip_dict)
    return ib_objects.EA(common_ea)


def get_ea_for_floatingip(user_id, tenant_id, network, port_id, device_id,
                          device_owner, instance_id):
    common_ea = get_common_ea(network, user_id, tenant_id)
    ip_dict = get_dict_for_ip(port_id, device_owner, device_id,
                              instance_id, const.IP_TYPE_FLOATING)
    common_ea.update(ip_dict)
    return ib_objects.EA(common_ea)


def get_ea_for_zone(user_id, tenant_id, network=None):
    return ib_objects.EA(get_common_ea(network, user_id, tenant_id))


def get_common_ea(network, user_id, tenant_id, for_network=False):
    if network:
        is_external = network.get(external_net.EXTERNAL, False)
        is_shared = network.get(attributes.SHARED)
    else:
        is_external = False
        is_shared = False

    is_cloud_owned = not (is_external or is_shared)
    ea_dict = {const.EA_CMP_TYPE: const.CLOUD_PLATFORM_NAME,
               const.EA_TENANT_ID: tenant_id,
               const.EA_ACCOUNT: user_id,
               const.EA_CLOUD_API_OWNED: str(is_cloud_owned)}
    if for_network:
        ea_dict[const.EA_IS_EXTERNAL] = str(is_external)
        ea_dict[const.EA_IS_SHARED] = str(is_shared)
    return ea_dict