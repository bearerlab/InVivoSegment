# invivo_util.py
"""
Utility functions for loading/processing InVivo Atlas files
"""

import pandas as pd

# For loading atlas csv
def safe_read_csv(path):
    """Read CSV robustly, converting common NA strings."""
    return pd.read_csv(path, na_values=["", " ", "NA", "-"])

# For ensuring columns are correct
def ensure_required_columns(df, cols):
    """Raise a ValueError if df missing any column in cols."""
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

# For ordering series in a pd.DataFrame
def ordered_levels_from_series(s: pd.Series):
    """
    Return an ordered list of levels for a pandas Series:
      - If Series is categorical and ordered, return categories in order.
      - Else return unique values in first-seen order.
    """
    if pd.api.types.is_categorical_dtype(s):
        cats = list(s.cat.categories)
        if len(cats) > 0:
            return cats
    # fallback: preserve appearance order
    return list(dict.fromkeys(s.dropna().tolist()))