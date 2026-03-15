import pandas as pd

def read_requirements(file_path):
    df = pd.read_excel(file_path)

    df = df.dropna(subset=["Name of parameter:"])
    data = dict(zip(df["Name of parameter:"], df["Parameter:"]))

    return {
        "prefix": data["Prefix for VMs"],
        "system_size": data["NetAct configuration"],
        "variant": data["Variant"],
        "sb_subnet": data["VM_Network_SB subnet"],
        "vmotion_subnet": data["vMotion subnet"],
        "host_count": int(data["Host_count"]),
        "optional_nodes": data.get("OPTIONAL NODE", "")
    }