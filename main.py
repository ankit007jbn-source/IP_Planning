## This is the main file which take care of all other things

import os
from input_reader import read_requirements
from node_arch_reader import (
    read_node_architecture,
    extract_mandatory_vms,
    extract_optional_vms
)
from ip_allocator import generate_sb_pool, generate_ip_pool
from record_builder import (
    build_mandatory_vm_records,
    build_optional_vm_records,
    build_vmotion_records,
    filter_optional_vms,
    extract_vm_number
)
from ciq_writer import write_ciq


def find_node_arch_file(input_folder):
    for file in os.listdir(input_folder):
        if (
            "node architecture and resource plan" in file.lower()
            and file.lower().endswith(".xlsx")
        ):
            return os.path.join(input_folder, file)

    raise Exception("Node Architecture and Resource Plan file not found in input folder!")


def main():

    input_folder = "input"
    output_file = "output/CIQ_GENERATED.xlsx"

    # -----------------------------
    # Auto-detect files
    # -----------------------------
    requirement_file = os.path.join(input_folder, "Requirement Collection Sheet.xlsx")
    node_arch_file = find_node_arch_file(input_folder)

    print(f"📄 Using Architecture File: {os.path.basename(node_arch_file)}")

    # -----------------------------
    # Read Requirements
    # -----------------------------
    req = read_requirements(requirement_file)

    prefix = req["prefix"]
    system_size = req["system_size"]
    variant = req["variant"]
    sb_subnet = req["sb_subnet"]
    vmotion_subnet = req["vmotion_subnet"]
    host_count = req["host_count"]
    optional_input = req["optional_nodes"]

    # -----------------------------
    # Read Architecture Sheet
    # -----------------------------
    node_df = read_node_architecture(
        node_arch_file,
        system_size,
        variant
    )

    mandatory_vms = extract_mandatory_vms(node_df)
    optional_vms_all = extract_optional_vms(node_df)

    # -----------------------------
    # Filter Optional Based on Input
    # -----------------------------
    filtered_optional_vms = filter_optional_vms(
        optional_vms_all,
        optional_input
    )

    # -----------------------------
    # Generate IP Pools
    # -----------------------------
    gateway_ip, sb_ips, broadcast_ip = generate_sb_pool(sb_subnet)
    vmotion_ips = generate_ip_pool(vmotion_subnet)

    # -----------------------------
    # Build Mandatory Records
    # -----------------------------
    sb_records = build_mandatory_vm_records(
        prefix,
        mandatory_vms,
        sb_ips
    )

    mandatory_lookup = {
        record["VM_Number"]: record
        for record in sb_records
    }

    # -----------------------------
    # Process Optional VMs
    # -----------------------------
    new_optional_vms = []

    for vm in filtered_optional_vms:

        vm_number = extract_vm_number(vm["vm_raw"])

        if vm_number in mandatory_lookup:
            existing_record = mandatory_lookup[vm_number]
            existing_services = existing_record["Description"]
            new_service = str(vm["service"])

            if new_service not in existing_services:
                existing_record["Description"] = (
                    existing_services + ", " + new_service
                )

            print(f"🔄 Merged optional service into existing VM{vm_number}")

        else:
            new_optional_vms.append(vm)

    # -----------------------------
    # Build New Optional VMs
    # -----------------------------
    optional_start_index = len(sb_records)

    sb_records_optional = build_optional_vm_records(
        prefix,
        new_optional_vms,
        sb_ips,
        optional_start_index
    )

    sb_records.extend(sb_records_optional)

    # Remove helper key before writing
    for record in sb_records:
        record.pop("VM_Number", None)

    # -----------------------------
    # Build vMotion Records
    # -----------------------------
    vmotion_records = build_vmotion_records(
        prefix,
        host_count,
        vmotion_ips,
        "vMotion_Network"
    )

    # -----------------------------
    # Generate CIQ
    # -----------------------------
    write_ciq(
        output_file,
        sb_subnet,
        vmotion_subnet,
        sb_records,
        vmotion_records,
        gateway_ip,
        broadcast_ip
    )


if __name__ == "__main__":
    main()