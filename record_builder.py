def extract_vm_number(vm_raw):
    return vm_raw.replace("VM", "").replace("#", "").strip()


def build_mandatory_vm_records(prefix, mandatory_vm_list, sb_ips):

    records = []

    if len(sb_ips) < len(mandatory_vm_list):
        raise Exception("Not enough SB IPs available!")

    for index, vm in enumerate(mandatory_vm_list):

        vm_number = extract_vm_number(vm["vm_raw"])
        hostname = f"{prefix}vm{vm_number}"

        records.append({
            "IP Address": str(sb_ips[index]),
            "Hostname": hostname,
            "Description": str(vm["service"]),
            "VLAN Name": "VM_Network_SB",
            "VM_Number": vm_number  # <-- important for merging
        })

    return records


def build_optional_vm_records(prefix, optional_vm_list, sb_ips, start_index):

    records = []

    for index, vm in enumerate(optional_vm_list):

        vm_number = extract_vm_number(vm["vm_raw"])
        hostname = f"{prefix}vm{vm_number}"

        records.append({
            "IP Address": str(sb_ips[start_index + index]),
            "Hostname": hostname,
            "Description": str(vm["service"]),
            "VLAN Name": "VM_Network_SB",
            "VM_Number": vm_number
        })

    return records


def build_vmotion_records(prefix, host_count, vmotion_ips, vlan_name):

    records = []

    if len(vmotion_ips) < host_count:
        raise Exception("Not enough vMotion IPs available!")

    for i in range(host_count):
        host_name = f"{prefix}esxi{i+1}"

        records.append({
            "IP Address": str(vmotion_ips[i]),
            "Hostname": host_name,
            "Description": "vMotion",
            "VLAN Name": vlan_name
        })

    return records


def filter_optional_vms(optional_vm_list, optional_input):

    if not optional_input:
        return []

    requested_keywords = [
        x.strip().lower()
        for x in optional_input.split(",")
        if x.strip()
    ]

    filtered = []

    for vm in optional_vm_list:

        service_name = str(vm["service"]).lower()

        for keyword in requested_keywords:
            if keyword in service_name:
                filtered.append(vm)
                break

    return filtered