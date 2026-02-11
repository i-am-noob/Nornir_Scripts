from nornir import InitNornir
from nornir_utils.plugins.tasks.data import load_yaml
from nornir_jinja2.plugins.tasks import template_file
from nornir_netmiko.tasks import netmiko_send_command

def generate_my_config(task):
    file_data = task.run(task=load_yaml, file="acl_data.yaml")
    task.host["my_vars"] = file_data.result

    config_output = task.run(
        task=template_file,
        template="template.j2",
        path=".",
        **task.host["my_vars"]
    )

    
    golden_config = config_output.result.strip().splitlines()
    golden_set = set(golden_config)

    print(f"\n\nGENERATED config for {task.host.name}")
    print(golden_set)

    switch_task = task.run(
    task=netmiko_send_command,
    command_string="show run | section access-list 50",
    )
    
    actual_config = switch_task.result.strip().splitlines()
    actual_set = set(actual_config)
    
    print(f"\nActual config for {task.host.name}")
    print(actual_set)
    
    if golden_set != actual_set:
        print(f"Config different in {task.host.name}")
    else:
        print(f"\nConfig matches in {task.host.name}")


nr = InitNornir(config_file="config_netbox.yaml")
switch = nr.filter(name="SW_ACCESS_01")
switch.run(task=generate_my_config)