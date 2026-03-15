import pandas as pd


def read_node_architecture(file_path, system_size, variant):

    excel_file = pd.ExcelFile(file_path)
    available_sheets = excel_file.sheet_names

    system_size_lower = system_size.lower()
    variant_lower = variant.lower()

    selected_sheet = None

    # Select correct sheet
    for sheet in available_sheets:
        sheet_lower = sheet.lower()

        if (
            system_size_lower in sheet_lower
            and variant_lower in sheet_lower
        ):
            selected_sheet = sheet
            break

    if not selected_sheet:
        raise Exception(
            f"No matching sheet found.\n"
            f"Configuration: {system_size}\n"
            f"Variant: {variant}\n"
            f"Available sheets: {available_sheets}"
        )

    print(f"✅ Selected Architecture Sheet: {selected_sheet}")

    # --------------------------------------------
    # Step 1: Read entire sheet without header
    # --------------------------------------------
    temp_df = pd.read_excel(
        file_path,
        sheet_name=selected_sheet,
        header=None
    )

    header_row_index = None

    # --------------------------------------------
    # Step 2: Detect header row by looking for BOTH:
    #   - "Services"
    #   - "Operating System"
    # --------------------------------------------
    for i in range(len(temp_df)):

        row_values = temp_df.iloc[i].tolist()
        row_str = [str(cell).strip().lower() for cell in row_values]

        if "services" in row_str and "operating system" in row_str:
            header_row_index = i
            break

    if header_row_index is None:
        raise Exception("Header row with 'Services' and 'Operating System' not found!")

    # --------------------------------------------
    # Step 3: Reload sheet using detected header
    # --------------------------------------------
    df = pd.read_excel(
        file_path,
        sheet_name=selected_sheet,
        header=header_row_index
    )

    return df


def extract_mandatory_vms(df):

    df.columns = df.columns.astype(str).str.strip()

    # Find exact Services column
    service_column = None

    for col in df.columns:
        if col.strip().lower() == "services":
            service_column = col
            break

    if service_column is None:
        raise Exception("Services column not found!")

    mandatory_vms = []

    for i in range(len(df)):

        first_col = df.iloc[i, 0]

        # Stop at OPTIONAL section
        if isinstance(first_col, str) and "optional" in first_col.lower():
            break

        if isinstance(first_col, str) and first_col.strip().startswith("VM#"):

            vm_raw = first_col.strip()
            service = df.loc[i, service_column]

            mandatory_vms.append({
                "vm_raw": vm_raw,
                "service": service
            })

    if not mandatory_vms:
        raise Exception("No Mandatory VMs found in sheet!")

    return mandatory_vms


def extract_optional_vms(df):

    df.columns = df.columns.astype(str).str.strip()

    service_column = None

    for col in df.columns:
        if col.strip().lower() == "services":
            service_column = col
            break

    if service_column is None:
        raise Exception("Services column not found!")

    optional_vms = []
    optional_section_started = False

    for i in range(len(df)):

        first_col = df.iloc[i, 0]

        # Detect OPTIONAL section start
        if isinstance(first_col, str) and "optional" in first_col.lower():
            optional_section_started = True
            continue

        if not optional_section_started:
            continue

        # Collect VM rows after OPTIONAL section
        if isinstance(first_col, str) and first_col.strip().startswith("VM#"):

            vm_raw = first_col.strip()
            service = df.loc[i, service_column]

            optional_vms.append({
                "vm_raw": vm_raw,
                "service": service
            })

    return optional_vms