from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
import shutil


def write_ciq(input_file, output_file,
              sb_subnet, vmotion_subnet,
              sb_records, vmotion_records,
              gateway_ip, broadcast_ip,
              vm_config_records=None):
    """
    Create output Excel file:
    - Keep original sheet as first tab
    - Add CIQ tab
    - Add VM Configuration tab (if VMware)
    """

    shutil.copy(input_file, output_file)

    wb = load_workbook(output_file)

    # ---------------- CIQ TAB ----------------
    ws = wb.create_sheet("CIQ")  # Added AFTER original sheet

    headers = ["IP Address", "Hostname", "Description", "VLAN Name"]

    ws["A1"] = f"VM_Network_SB VLAN: {sb_subnet}"

    for i, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=i)
        cell.value = h
        cell.fill = PatternFill(start_color="92D050", fill_type="solid")
        cell.font = Font(bold=True)

    # Gateway
    ws.append([gateway_ip, "Gateway", "Default Gateway", "VM_Network_SB"])

    # VM records
    for r in sb_records:
        ws.append([
            r["IP Address"],
            r["Hostname"],
            r["Description"],
            r["VLAN Name"]
        ])

    # Broadcast
    ws.append([broadcast_ip, "Broadcast", "Broadcast Address", "VM_Network_SB"])

    # ---------------- VM CONFIG TAB ----------------
    if vm_config_records:

        ws2 = wb.create_sheet("VM Configuration Sheet")

        headers = ["VM Name", "CPU", "RAM", "Memory Reservation", "SWAP"]

        for i, h in enumerate(headers, 1):
            cell = ws2.cell(row=1, column=i)
            cell.value = h
            cell.fill = PatternFill(start_color="FFFF00", fill_type="solid")
            cell.font = Font(bold=True)

        for r in vm_config_records:
            ws2.append([
                r["VM Name"],
                r["CPU"],
                r["RAM"],
                r["Memory Reservation"],
                r["SWAP"]
            ])

    wb.save(output_file)

    print(f"✅ Output Generated: {output_file}")