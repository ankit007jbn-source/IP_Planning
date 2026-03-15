from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def write_section(ws, title, subnet, records, start_row,
                  gateway_ip=None, broadcast_ip=None):

    ws[f"A{start_row}"] = f"{title} VLAN: {subnet}"
    ws[f"A{start_row}"].font = Font(bold=True)

    headers = ["IP Address", "Hostname", "Description", "VLAN Name"]
    header_row = start_row + 1

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="92D050",
                                end_color="92D050",
                                fill_type="solid")

    row = header_row + 1

    # Gateway
    if gateway_ip:
        ws.cell(row=row, column=1).value = gateway_ip
        ws.cell(row=row, column=2).value = "Gateway"
        ws.cell(row=row, column=3).value = "Default Gateway"
        ws.cell(row=row, column=4).value = title
        row += 1

    # VM records
    for record in records:
        ws.cell(row=row, column=1).value = record["IP Address"]
        ws.cell(row=row, column=2).value = record["Hostname"]
        ws.cell(row=row, column=3).value = record["Description"]
        ws.cell(row=row, column=4).value = record["VLAN Name"]
        row += 1

    # Broadcast (only for SB section)
    if broadcast_ip:
        ws.cell(row=row, column=1).value = broadcast_ip
        ws.cell(row=row, column=2).value = "Broadcast"
        ws.cell(row=row, column=3).value = "Broadcast Address"
        ws.cell(row=row, column=4).value = title
        row += 1

    return row + 2


def write_ciq(output_path, sb_subnet, vmotion_subnet,
              sb_records, vmotion_records,
              gateway_ip, broadcast_ip):

    wb = Workbook()
    ws = wb.active
    ws.title = "CIQ"

    current_row = 1

    current_row = write_section(
        ws,
        "VM_Network_SB",
        sb_subnet,
        sb_records,
        current_row,
        gateway_ip=gateway_ip,
        broadcast_ip=broadcast_ip
    )

    current_row = write_section(
        ws,
        "vMotion_Network",
        vmotion_subnet,
        vmotion_records,
        current_row
    )

    wb.save(output_path)
    print("✅ CIQ file generated successfully!")