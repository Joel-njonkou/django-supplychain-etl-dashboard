import pandas as pd
from .config import COLUMNS
def extract(path, limit=None) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        encoding="latin-1", # le fichier n'est PAS en UTF-8
        usecols=lambda c: c.strip() in COLUMNS, #pour ne charger que les colonnes utiles
        nrows=limit,
    )
    df.columns = df.columns.str.strip()
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes absentes du fichier source : {sorted(missing)}")
    return df.rename(columns=COLUMNS)
