import pandas as pd

def read_config(config_file, system_size):
    df = pd.read_excel(config_file, sheet_name=system_size)
    df = df.dropna(subset=["VM Number", "Service"])
    return df
