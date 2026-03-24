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


# =========================================================
# 🆕 NEW FUNCTION (DO NOT REMOVE OLD LOGIC)
# =========================================================
def merge_ciq_records(mandatory_records, optional_records):
    """
    Merge mandatory + optional CIQ records

    ✔ Avoid duplicate VMs
    ✔ Merge descriptions
    ✔ Preserve original IP of mandatory VM
    """

    merged = {}

    # First add mandatory VMs
    for r in mandatory_records:
        merged[r["Hostname"]] = r

    # Merge optional VMs
    for r in optional_records:
        hostname = r["Hostname"]

        if hostname in merged:
            # Merge description
            existing = merged[hostname]["Description"]
            new = r["Description"]

            if new not in existing:
                merged[hostname]["Description"] = f"{existing}, {new}"
        else:
            # New VM → add
            merged[hostname] = r

    return list(merged.values())


# =========================================================
# EXISTING LOGIC (UNCHANGED)
# =========================================================
def build_vm_config_records(prefix, resources, optional_input, yaml_data):
    """
    FIXED VERSION

    ✔ No duplicate VMs
    ✔ Merge optional + mandatory into same VM
    ✔ Aggregate disks
    ✔ Keep existing logic intact
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

        # ---------------- OPTIONAL FILTER ----------------
        if vm["is_optional"]:
            if optional_keys:
                if not any(k in service_text for k in optional_keys):
                    continue

        # ---------------- BASE RESOURCES ----------------
        cpu = vm["cpu"]
        ram = vm["ram"]
        mem = vm["mem"]
        swap = vm["swap"]

        # ---------------- YAML DATA ----------------
        yaml_key = f"vm{vm_number}"
        yaml_vm = yaml_data.get(yaml_key, {})

        disks = yaml_vm.get("disks", [])
        scsi = yaml_vm.get("scsi", [])
        scsi_type = yaml_vm.get("scsi_type", "")
        adapter = yaml_vm.get("adapter", "")

        # ---------------- MERGE LOGIC ----------------
        if hostname in records:

            # 🔥 Merge disks
            records[hostname]["Disks"].extend(disks)

            # 🔥 Update SCSI if larger
            if len(scsi) > len(records[hostname]["SCSI Controllers"]):
                records[hostname]["SCSI Controllers"] = scsi

        else:
            records[hostname] = {
                "VM Name": hostname,
                "CPU": cpu,
                "RAM": ram,
                "Memory Reservation": mem,
                "SWAP": swap,
                "Disks": list(disks),
                "SCSI Controllers": scsi,
                "SCSI Type": scsi_type,
                "Adapter": adapter
            }

    final_records = list(records.values())

    print(f"✅ VM Config Records Generated (DEDUPED): {len(final_records)}")

    return final_records