def extract_vm_number(vm_raw):
    """Extract VM number from 'VM#123'"""
    return vm_raw.replace("VM", "").replace("#", "").strip()


def build_mandatory_vm_records(prefix, vm_list, ips):
    """Build CIQ records for mandatory VMs"""

    records = []

    for i, vm in enumerate(vm_list):
        num = extract_vm_number(vm["vm_raw"])

        records.append({
            "IP Address": str(ips[i]),
            "Hostname": f"{prefix}vm{num}",
            "Description": str(vm["service"]),
            "VLAN Name": "VM_Network_SB",
            "VM_Number": num
        })

    return records


def build_optional_vm_records(prefix, vm_list, ips, start):
    """Build CIQ records for new optional VMs"""

    records = []

    for i, vm in enumerate(vm_list):
        num = extract_vm_number(vm["vm_raw"])

        records.append({
            "IP Address": str(ips[start + i]),
            "Hostname": f"{prefix}vm{num}",
            "Description": str(vm["service"]),
            "VLAN Name": "VM_Network_SB",
            "VM_Number": num
        })

    return records


def build_vmotion_records(prefix, count, ips, vlan):
    """Build ESXi vMotion records"""

    return [{
        "IP Address": str(ips[i]),
        "Hostname": f"{prefix}esxi{i+1}",
        "Description": "vMotion",
        "VLAN Name": vlan
    } for i in range(count)]


def filter_optional_vms(vm_list, optional_input):
    """
    Filter optional VMs based on user-selected services
    """

    keys = [x.strip().lower() for x in optional_input.split(",") if x.strip()]

    return [
        vm for vm in vm_list
        if any(k in str(vm["service"]).lower() for k in keys)
    ]


def build_vm_config_records(prefix, resources, optional_input):
    """
    Build VM Configuration Sheet

    Handles:
    ✔ Mandatory VMs
    ✔ Optional VMs
    ✔ Optional services merged into existing VM
    ✔ Resource aggregation (CPU, RAM, etc.)
    """

    records = {}

    optional_keys = [
        x.strip().lower()
        for x in optional_input.split(",")
        if x.strip()
    ]

    for vm in resources:

        vm_number = extract_vm_number(vm["vm_raw"])
        hostname = f"{prefix}vm{vm_number}"

        service_text = vm["service"].lower()

        # Skip optional services not selected
        if vm["is_optional"]:
            if not any(k in service_text for k in optional_keys):
                continue

        cpu = vm["cpu"]
        ram = vm["ram"]
        mem = vm["mem"]
        swap = vm["swap"]

        if hostname in records:
            # 🔥 Aggregate resources
            records[hostname]["CPU"] += cpu
            records[hostname]["RAM"] += ram
            records[hostname]["Memory Reservation"] += mem
            records[hostname]["SWAP"] += swap
        else:
            records[hostname] = {
                "VM Name": hostname,
                "CPU": cpu,
                "RAM": ram,
                "Memory Reservation": mem,
                "SWAP": swap
            }

    return list(records.values())