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


def find_node_arch_file(folder):
    """Locate Architecture file dynamically"""
    for f in os.listdir(folder):
        if "node architecture" in f.lower():
            return os.path.join(folder, f)
    raise Exception("Node Architecture file not found")


def extract_insteng_service(df):
    """
    Extract service name for insteng VM
    (Row where VM column contains '-')
    """

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
    # OpenStack Special VM (insteng)
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
    # Merge Optional Services
    # -----------------------------
    lookup = {
        r["VM_Number"]: r
        for r in sb_records
        if "VM_Number" in r
    }

    new_optional = []

    for vm in optional_filtered:

        num = extract_vm_number(vm["vm_raw"])

        if num in lookup:
            # Merge service into existing VM
            if vm["service"] not in lookup[num]["Description"]:
                lookup[num]["Description"] += ", " + vm["service"]
        else:
            new_optional.append(vm)

    # -----------------------------
    # Add New Optional VMs
    # -----------------------------
    optional_start_index = len(sb_records)

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
    # VM Configuration Sheet (VMware only)
    # -----------------------------
    vm_config_records = None

    if variant.lower() == "vmware":
        resources = extract_all_vm_resources(df)

        vm_config_records = build_vm_config_records(
            prefix,
            resources,
            optional_input
        )

    # -----------------------------
    # Write Output File
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