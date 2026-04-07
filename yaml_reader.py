import os
import yaml


def find_vmware_yaml(folder, system_size):
    """
    Find base VMware YAML:
    Example: vmware_vconf_3xl.yml
    """

    system_size = system_size.lower()

    for file in os.listdir(folder):
        f = file.lower()

        if f.startswith("vmware_vconf") and system_size in f and f.endswith(".yml"):
            return os.path.join(folder, file)

    raise Exception("Base VMware YAML not found!")


def find_optional_yamls(folder, optional_input, system_size, variant):
    """
    Find optional YAMLs based on:
    - optional services
    - config (3XL, Large, etc.)
    - must contain addnode
    - filter based on variant (VMware/OpenStack)
    """

    def normalize(x):
        return x.lower().replace("&", "").replace(" ", "")

    files = []

    keys = [normalize(x) for x in optional_input.split(",") if x.strip()]
    system_size = system_size.lower()
    variant = variant.lower()

    for file in os.listdir(folder):
        f = file.lower()

        if "addnode" not in f:
            continue

        if system_size not in f:
            continue

        # ✅ Filter variant
        if variant == "vmware" and "openstack" in f:
            continue

        if variant == "openstack" and "vmware" in f:
            continue

        f_norm = normalize(f)

        for key in keys:
            if key in f_norm:
                files.append(os.path.join(folder, file))
                break

    return files


def load_yaml(file_path):
    """Load YAML file"""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def parse_vmware_yaml(yaml_data):
    """
    Parse base VMware YAML and extract:
    - disks (with disk_name)
    - scsi controllers (with IDs)
    - scsi type
    - network adapter
    """

    vm_data = {}

    for vm in yaml_data.get("vm", []):

        # Normalize VM name
        vm_name = str(vm.get("vm_name", "")).strip().lower()

        if not vm_name or vm_name == "vm1":
            continue

        # ---------------- SCSI ----------------
        scsi_raw = vm.get("scsi_controller", [])

        if isinstance(scsi_raw, dict):
            scsi_raw = [scsi_raw]

        scsi_list = []

        for idx, s in enumerate(scsi_raw):
            scsi_list.append({
                "id": s.get("scsi_controller_id", idx),
                "type": s.get("scsi_controller_type", "")
            })

        scsi_type = scsi_list[0]["type"] if scsi_list else ""

        # ---------------- DISKS ----------------
        disks = []
        disk_data = vm.get("disk", [])

        if isinstance(disk_data, dict):
            disk_data = [disk_data]

        for d in disk_data:
            size_mb = d.get("sizeMB", 0)

            disks.append({
                "disk_name": d.get("disk_name", ""),
                "size": int(size_mb / 1024) if size_mb else 0,
                "controller": d.get("scsi_controller_id", 0),
                "scsi_id": d.get("scsi_id", 0),
                "mode": d.get("diskMode", "")
            })

        # ---------------- NETWORK ----------------
        adapter = ""
        network_interfaces = vm.get("network_interface", [])

        if isinstance(network_interfaces, dict):
            network_interfaces = [network_interfaces]

        if network_interfaces:
            adapter = network_interfaces[0].get("network_adapter_type", "")

        # ---------------- STORE ----------------
        vm_data[vm_name] = {
            "disks": disks,
            "scsi": scsi_list,
            "scsi_type": scsi_type,
            "adapter": adapter
        }

    print(f"📊 Base YAML Parsed VMs: {len(vm_data)}")

    return vm_data


def parse_optional_yaml(yaml_data):
    """
    Parse optional YAMLs (same structure as base)
    """

    vm_data = {}

    for vm in yaml_data.get("vm", []):

        vm_name = str(vm.get("vm_name", "")).strip().lower()

        if not vm_name:
            continue

        # ---------------- SCSI ----------------
        scsi_raw = vm.get("scsi_controller", [])

        if isinstance(scsi_raw, dict):
            scsi_raw = [scsi_raw]

        scsi_list = []

        for idx, s in enumerate(scsi_raw):
            scsi_list.append({
                "id": s.get("scsi_controller_id", idx),
                "type": s.get("scsi_controller_type", "")
            })

        scsi_type = scsi_list[0]["type"] if scsi_list else ""

        # ---------------- DISKS ----------------
        disks = []
        disk_data = vm.get("disk", [])

        if isinstance(disk_data, dict):
            disk_data = [disk_data]

        for d in disk_data:
            size_mb = d.get("sizeMB", 0)

            disks.append({
                "disk_name": d.get("disk_name", ""),   # ⭐ REQUIRED
                "size": int(size_mb / 1024) if size_mb else 0,
                "controller": d.get("scsi_controller_id", 0),
                "scsi_id": d.get("scsi_id", 0)
            })

        # ---------------- NETWORK ----------------
        adapter = ""
        network_interfaces = vm.get("network_interface", [])

        if isinstance(network_interfaces, dict):
            network_interfaces = [network_interfaces]

        if network_interfaces:
            adapter = network_interfaces[0].get("network_adapter_type", "")

        # ---------------- STORE ----------------
        vm_data[vm_name] = {
            "disks": disks,
            "scsi": scsi_list,
            "scsi_type": scsi_type,
            "adapter": adapter
        }

    print(f"📦 Optional YAML Parsed VMs: {len(vm_data)}")

    return vm_data


def parse_drs_rules(yaml_data):

    """
    Read DRS rules from yml file
    """

    rules = []

    for r in yaml_data.get("drs_rule", []):
        rules.append({
            "Rule Name": r.get("drs_rule_name", ""),
            "Type": r.get("type", ""),
            "VM1": r.get("vm1", ""),
            "VM2": r.get("vm2", "")
        })

    return rules