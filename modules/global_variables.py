"""
global variables
"""
from typing import Any

import pandas as pd
import plotly.graph_objects as go

# allgemein
fig: go.Figure
df_data: pd.DataFrame

# Benutzerkonten
deta_key: str
deta: Any
deta_db: Any
users: list
access_lvl_user: list or str

# buttons
but_upd_main: bool

# meteorologische Daten
dic_dwd_hourly_parameters: dict
df_used_stations: pd.DataFrame

# figrues
exclude: tuple[str]
