"""
Streamlit tables for dashboard
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

months = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]


@st.experimental_memo(suppress_st_warning=True, show_spinner=False)
def tab_mon(fig_mon):

    df = pd.DataFrame()
    df["Monat"] = ["Summe"] + months
    for col in [tr.name for tr in fig_mon.data if tr.visible]:
        col_dat = [tr.y for tr in fig_mon.data if tr.name == col][0]
        df[col] = [sum(col_dat)] + list(col_dat)

    # st.experimental_show(df)

    tab = go.Figure()

    tab.add_trace(
        go.Table(
            header={
                "values": df.columns.tolist(),
                "align": ["left", "right"],
            },
            cells={
                "values": [df[k].tolist() for k in df.columns],
                "align": ["left", "right"],
                "format": ["", ",d"],
            },
        )
    )

    return tab
