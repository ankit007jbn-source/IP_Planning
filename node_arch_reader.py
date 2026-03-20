import pandas as pd


def read_node_architecture(file_path, system_size, variant):
    """
    Select correct sheet based on:
    - NetAct Configuration (system_size)
    - Variant (VMware/OpenStack)

    Also dynamically finds header row.
    """

    excel_file = pd.ExcelFile(file_path)
    sheets = excel_file.sheet_names

    system_size = system_size.lower()
    variant = variant.lower()

    selected_sheet = None

    # Identify correct tab
    for sheet in sheets:
        s = sheet.lower()
        if system_size in s and variant in s:
            selected_sheet = sheet
            break

    if not selected_sheet:
        raise Exception("Matching Architecture sheet not found!")

    print(f"✅ Selected Architecture Sheet: {selected_sheet}")

    # Read without header first
    temp_df = pd.read_excel(file_path, sheet_name=selected_sheet, header=None)

    header_row = None

    # Detect header row dynamically
    for i in range(len(temp_df)):
        row = [str(x).strip().lower() for x in temp_df.iloc[i]]
        if "services" in row and "operating system" in row:
            header_row = i
            break

    if header_row is None:
        raise Exception("Header row not found!")

    # Reload with correct header
    df = pd.read_excel(file_path, sheet_name=selected_sheet, header=header_row)

    return df


def extract_mandatory_vms(df):
    """
    Extract mandatory VMs (before OPTIONAL section)
    """

    df.columns = df.columns.astype(str).str.strip()

    service_col = [c for c in df.columns if c.lower() == "services"][0]

    result = []

    for i in range(len(df)):

        first = df.iloc[i, 0]

        # Stop at OPTIONAL section
        if isinstance(first, str) and "optional" in first.lower():
            break

        if isinstance(first, str) and first.startswith("VM#"):
            result.append({
                "vm_raw": first,
                "service": df.loc[i, service_col]
            })

    return result


def extract_optional_vms(df):
    """
    Extract optional VMs (after OPTIONAL section)
    """

    df.columns = df.columns.astype(str).str.strip()
    service_col = [c for c in df.columns if c.lower() == "services"][0]

    result = []
    optional = False

    for i in range(len(df)):

        first = df.iloc[i, 0]

        # Detect OPTIONAL section start
        if isinstance(first, str) and "optional" in first.lower():
            optional = True
            continue

        if optional and isinstance(first, str) and first.startswith("VM#"):
            result.append({
                "vm_raw": first,
                "service": df.loc[i, service_col]
            })

    return result


def extract_all_vm_resources(df):
    """
    Extract:
    - CPU (vCPU)
    - RAM (vRAM)
    - Memory Reservation
    - SWAP
    - Service name

    Includes both Mandatory and Optional VMs
    """

    df.columns = df.columns.astype(str).str.strip()

    col_map = {}

    # Map required columns dynamically
    for c in df.columns:
        cl = c.lower()
        if cl == "vcpu": col_map["cpu"] = c
        elif cl == "vram": col_map["ram"] = c
        elif "memory reservation" in cl: col_map["mem"] = c
        elif cl == "swap": col_map["swap"] = c
        elif cl == "services": col_map["service"] = c

    result = []
    optional = False

    for i in range(len(df)):

        first = df.iloc[i, 0]

        # Detect OPTIONAL section
        if isinstance(first, str) and "optional" in first.lower():
            optional = True
            continue

        if isinstance(first, str) and first.startswith("VM#"):
            result.append({
                "vm_raw": first,
                "service": str(df.loc[i, col_map["service"]]),
                "cpu": df.loc[i, col_map["cpu"]],
                "ram": df.loc[i, col_map["ram"]],
                "mem": df.loc[i, col_map["mem"]],
                "swap": df.loc[i, col_map["swap"]],
                "is_optional": optional
            })

    return result