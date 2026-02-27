import pynetbox
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko.tasks import netmiko_send_config
from ipaddress import ip_interface
from dotenv import load_dotenv
import os
from nornir.core.filter import F


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
NETBOX_URL = os.getenv("URL")
API_TOKEN = os.getenv("TOKEN")

def get_netbox_interfaces(nb,devices):
    """ Get the IP address, interface and IP subnet info of the device"""
    
    device_dict = {}
    for device in devices:       
        interface_dict = {}   
        ips = nb.ipam.ip_addresses.filter(device_id=device.id)

        for ip in ips:            
            if ip.assigned_object:
                interface = ip.assigned_object
                interface_dict[interface.name] = str(ip.address)
                device_dict[str(device)] = interface_dict

    return device_dict


def config_devices(task,device_data):
    """ Get data from netbox now use nornir to configure IP on those interface of the devices"""

    config_commands = []
    for intf, ip_addr in device_data[task.host.name].items():
        ip = ip_interface(ip_addr)
        config_commands.append(f"interface {intf} ")
        config_commands.append(f"ip address {ip.ip} {ip.network.netmask}")

    print(f"{task.host.name}{config_commands}")

    try:
        results = task.run(task=netmiko_send_config, config_commands=config_commands)

    except:
       results = print(f"Unable to run on {task.host.name}")

    return results
    



def main():
    """ Connect to netbox through API, filter device according to tag"""

    nb = pynetbox.api(NETBOX_URL,token= API_TOKEN)
    nr = InitNornir(config_file="config_netbox.yaml")
    devices = nb.dcim.devices.filter(tag='provisioning')
    data = get_netbox_interfaces(nb,devices) 
    # data -> {'site_name' : {'int_A' : 'ip_address', 'int_B' : 'ip_address'}, 'site_B' : {'int_A' : 'ip_address', 'int_B' : 'ip_address'}}   
    
    filtered_hosts = nr.filter(F(name__in=list(data.keys())))
    filtered_hosts.run(task=config_devices,device_data=data)
    


if __name__ == "__main__":
    main()



            





