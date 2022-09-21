"""
Import und Download von Excel-Dateien
"""

from io import BytesIO
from typing import Any

import pandas as pd
import pandas.io.formats.excel
import streamlit as st

from modules import def_dics as dics
from modules import df_manip as dfm
from modules import meteorolog as meteo

pandas.io.formats.excel.ExcelFormatter.header_style = None


@dics.timer()
def import_prefab_excel(file: Any) -> None:
    """vordefinierte Datei (benannte Zelle für Indes) importieren"""

    df = pd.read_excel(file, sheet_name="Daten")

    ind = df[df == "↓ Index ↓"].dropna(how="all").dropna(axis=1)
    ind_row = ind.index[0]
    ind_col = df.columns.get_loc(ind.columns[0])
    df.columns = df.iloc[ind_row]
    units = df.iloc[ind_row - 1 : ind_row].copy()
    units = units.reset_index(drop=True)
    df = df.iloc[ind_row + 1 :, ind_col:]
    df = df.set_index("↓ Index ↓")
    pd.to_datetime(df.index, dayfirst=True)
    df.dropna(how="all", inplace=True)
    df.dropna(axis="columns", how="all", inplace=True)
    units.dropna(how="all", inplace=True)
    units.dropna(axis="columns", how="all", inplace=True)
    if not isinstance(df.index, pd.DatetimeIndex) and "01.01. " in df.index[0]:
        df.index = pd.to_datetime(
            [x.split()[0] + "2020 " + x.split()[1] for x in df.index.values],
            dayfirst=True,
        )

    dic_meta = dfm.cols_meta(df)
    for col in df.columns:
        if units[col][0] not in ["", None]:
            dic_meta[col]["unit_data"] = " " + units[col][0]
            dic_meta[col]["unit_graph"] = (
                " kW" if units[col][0] in ["kWh", "kwh", "KWH"] else " " + units[col][0]
            )

    dic_meta["index"] = {"datetime": False}
    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.round("s")
        dic_meta["index"] = {"datetime": True}
        dic_meta["index"]["td_mean"] = df.index.to_series().diff().mean().round("min")
        if dic_meta["index"]["td_mean"] == pd.Timedelta(minutes=15):
            dic_meta["index"]["td_int"] = "15min"
        elif dic_meta["index"]["td_mean"] == pd.Timedelta(hours=1):
            dic_meta["index"]["td_int"] = "h"
        st.session_state["df_dls_deleted"] = df[df.index.duplicated(keep="first")]
        df = df[~df.index.duplicated(keep="first")]
    for col in df.columns:
        tit = dic_meta.get(col).get("tit")
        df.rename(columns={col: tit}, inplace=True)
        dic_meta[tit] = dic_meta.pop(col)
    df["orgidx"] = df.index.copy()
    st.session_state["dic_meta"] = dic_meta
    st.session_state["df"] = df
    if "lis_years" not in st.session_state:
        lis_years = []
        if isinstance(df.index, pd.DatetimeIndex):
            cut_off = 50
            lis_years.extend(
                y
                for y in set(df.index.year)
                if len(df.loc[df.index.year == y, :]) > cut_off
            )

        st.session_state["lis_years"] = lis_years


@dics.timer()
# pylint: disable=too-many-locals
def excel_download(df: pd.DataFrame, page: str = "graph") -> Any:
    """Daten als Excel-Datei herunterladen"""

    if page in ("meteo"):
        ws_name = "Wetterdaten"
        dic_num_formats = {par.tit_de: par.num_format for par in meteo.LIS_PARAMS}

    if page in ("graph"):
        ws_name = "Daten"
        dic_num_formats = {
            key: f'#,##0.0"{st.session_state.get("dic_meta")[key]["unit_data"]}"'
            for key in df.columns
        }

    offset_col = 2
    offset_row = 4

    output = BytesIO()
    # pylint: disable=abstract-class-instantiated
    writer = pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        datetime_format="dd.mm.yyyy hh:mm",
        date_format="dd.mm.yyyy",
    )
    # pylint: enable=abstract-class-instantiated
    df.to_excel(
        writer,
        sheet_name=ws_name,
        startrow=offset_row,
        startcol=offset_col,
    )

    wkb = writer.book  # pylint: disable=no-member
    wks = writer.sheets[ws_name]

    # Formatierung
    wks.hide_gridlines(2)
    dic_format_base = {
        "bold": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "right",
        "border": 0,
    }

    # erste Spalte
    dic_format_col1 = dic_format_base.copy()
    dic_format_col1["align"] = "left"
    cell_format = wkb.add_format(dic_format_col1)
    wks.set_column(offset_col, offset_col, 18, cell_format)

    # erste Zeile
    dic_format_header = dic_format_base.copy()
    dic_format_header["bottom"] = 1
    cell_format = wkb.add_format(dic_format_header)
    wks.write(offset_row, offset_col, "Datum", cell_format)
    for col, header in enumerate(df.columns):
        wks.write(offset_row, col + 1 + offset_col, header, cell_format)

    # Spaltenbreiten
    dic_col_width = {col: len(col) + 1 for col in df.columns}

    for num_format in dic_num_formats.values():
        dic_format_num = dic_format_base.copy()
        dic_format_num["num_format"] = num_format
        col_format = wkb.add_format(dic_format_num)

        for cnt, col in enumerate(df.columns):
            if dic_num_formats[col] == num_format:
                wks.set_column(
                    cnt + offset_col + 1,
                    cnt + offset_col + 1,
                    dic_col_width[col],
                    col_format,
                )

    wkb.close()

    return output.getvalue()
