import os
from input_reader import read_requirements
from node_arch_reader import (
    read_node_architecture,
    extract_mandatory_vms,
    extract_optional_vms,
    extract_all_vm_resources
)
from ip_allocator import generate_sb_pool, generate_ip_pool
from record_builder import *
from ciq_writer import write_ciq
from yaml_reader import find_optional_yamls, parse_optional_yaml
from yaml_reader import find_vmware_yaml, load_yaml, parse_vmware_yaml


def find_node_arch_file(folder):
    """Locate Architecture file dynamically"""
    for f in os.listdir(folder):
        if "node architecture" in f.lower():
            return os.path.join(folder, f)
    raise Exception("Node Architecture file not found")


def extract_insteng_service(df):
    """Extract service name for insteng VM"""

    df.columns = df.columns.astype(str).str.strip()
    service_col = [c for c in df.columns if c.lower() == "services"][0]

    for i in range(len(df)):
        first = df.iloc[i, 0]
        if str(first).strip() == "-":
            return str(df.loc[i, service_col])

    return "Instantiation Engine"


def main():

    input_folder = "input"
    output_file = "output/CIQ_OUTPUT.xlsx"

    req_file = os.path.join(input_folder, "Requirement Collection Sheet.xlsx")
    arch_file = find_node_arch_file(input_folder)

    # -----------------------------
    # Read input parameters
    # -----------------------------
    req = read_requirements(req_file)

    prefix = req["prefix"]
    variant = req["variant"]
    optional_input = req["optional_nodes"]

    # -----------------------------
    # Load architecture sheet
    # -----------------------------
    df = read_node_architecture(
        arch_file,
        req["system_size"],
        variant
    )

    # -----------------------------
    # Extract VM details
    # -----------------------------
    mandatory = extract_mandatory_vms(df)
    optional_all = extract_optional_vms(df)
    optional_filtered = filter_optional_vms(optional_all, optional_input)

    # -----------------------------
    # Generate IP pools
    # -----------------------------
    gateway, sb_ips, broadcast = generate_sb_pool(req["sb_subnet"])
    vmotion_ips = generate_ip_pool(req["vmotion_subnet"])

    sb_records = []
    ip_index = 0

    # -----------------------------
    # OpenStack Special VM
    # -----------------------------
    if variant.lower() == "openstack":

        insteng_service = extract_insteng_service(df)

        sb_records.append({
            "IP Address": str(sb_ips[ip_index]),
            "Hostname": f"{prefix}insteng",
            "Description": insteng_service,
            "VLAN Name": "VM_Network_SB",
            "VM_Number": "insteng"
        })

        ip_index += 1

    # -----------------------------
    # Mandatory VMs
    # -----------------------------
    mandatory_records = build_mandatory_vm_records(
        prefix,
        mandatory,
        sb_ips[ip_index:]
    )

    sb_records.extend(mandatory_records)

    # -----------------------------
    # Merge Optional Services (FIXED)
    # -----------------------------
    lookup = {
        str(r["VM_Number"]).strip(): r
        for r in sb_records
        if "VM_Number" in r
    }

    new_optional = []

    for vm in optional_filtered:

        num = extract_vm_number(vm["vm_raw"]).strip()

        if num in lookup:
            existing_desc = lookup[num]["Description"]
            new_service = str(vm["service"])

            if new_service not in existing_desc:
                lookup[num]["Description"] = f"{existing_desc}, {new_service}"
        else:
            new_optional.append(vm)

    print(f"✅ After merge → Mandatory: {len(mandatory_records)}, New Optional: {len(new_optional)}")

    # -----------------------------
    # Add New Optional VMs (FIXED IP LOGIC)
    # -----------------------------
    optional_start_index = len(mandatory_records)

    optional_records = build_optional_vm_records(
        prefix,
        new_optional,
        sb_ips,
        optional_start_index
    )

    sb_records.extend(optional_records)

    # Remove helper key
    for r in sb_records:
        r.pop("VM_Number", None)

    # -----------------------------
    # vMotion Records
    # -----------------------------
    vmotion_records = build_vmotion_records(
        prefix,
        req["host_count"],
        vmotion_ips,
        "vMotion_Network"
    )

    # -----------------------------
    # VM Configuration Sheet
    # -----------------------------
    vm_config_records = None

    if variant.lower() == "vmware":

        resources = extract_all_vm_resources(df)
        yaml_folder = os.path.join(input_folder, "nipe-conf")

        # Base YAML
        base_yaml_file = find_vmware_yaml(
            yaml_folder,
            req["system_size"]
        )

        print(f"\n📄 Base YAML: {os.path.basename(base_yaml_file)}")

        base_yaml = load_yaml(base_yaml_file)
        yaml_data_map = parse_vmware_yaml(base_yaml)

        # Optional YAMLs (FIXED FILTER)
        optional_yaml_files = [
            f for f in find_optional_yamls(
                yaml_folder,
                optional_input,
                req["system_size"],
                variant
            )
            if "openstack" not in os.path.basename(f).lower()
        ]

        print("\n📦 Optional YAMLs:")
        for f in optional_yaml_files:
            print("  →", os.path.basename(f))

        compute_map = {
            "compute1": "vm150",
            "compute2": "vm151",
            "compute3": "vm152"
        }

        # Merge optional YAML
        for file in optional_yaml_files:

            opt_yaml = load_yaml(file)
            opt_data = parse_optional_yaml(opt_yaml)

            for vm_name, data in opt_data.items():

                mapped_vm = compute_map.get(vm_name, vm_name)

                if mapped_vm in yaml_data_map:
                    yaml_data_map[mapped_vm]["disks"].extend(data.get("disks", []))
                    yaml_data_map[mapped_vm]["scsi"] = data.get("scsi", [])
                else:
                    yaml_data_map[mapped_vm] = data

        vm_config_records = build_vm_config_records(
            prefix,
            resources,
            optional_input,
            yaml_data_map
        )

    # -----------------------------
    # Write Output
    # -----------------------------
    write_ciq(
        req_file,
        output_file,
        req["sb_subnet"],
        req["vmotion_subnet"],
        sb_records,
        vmotion_records,
        gateway,
        broadcast,
        vm_config_records
    )


if __name__ == "__main__":
    main()