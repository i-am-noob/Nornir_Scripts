import csv
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_command

target_macs = set()
with open('phones.csv', mode='r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Normalize to lowercase and remove separators to make matching easier
        clean_mac = row['mac'].lower().replace(':', '').replace('.', '').replace('-', '')
        target_macs.add(clean_mac)

nr = InitNornir(config_file="config_netbox.yaml")

results = nr.run(
    task=netmiko_send_command,
    command_string="show arp",
    use_textfsm=True,
)

print(f"HOST,IP ADDRESS,MAC ADDRESS")

for host, task in results.items():
    arp_data = task[0].result

    if isinstance(arp_data, list):
        for entry in arp_data:
            # Normalize the MAC address returned by the switch
            switch_mac = entry["hardware_address"].lower().replace(':', '').replace('.', '').replace('-', '')
            
            # Check if this switch MAC exists in our target set
            if switch_mac in target_macs:
                print(f'{host},{entry["address"]},{entry["hardware_address"]}')
    else:
        print(f"Host {host} returned unstructured data or no ARP entries found.")

if results.failed:
    print(f"\nFailed hosts: {list(results.failed_hosts.keys())}")