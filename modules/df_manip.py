"""
Bearbeitung der Daten
"""

from fnmatch import fnmatch

import numpy as np
import pandas as pd
import streamlit as st

from modules import def_dics as dics


# Index aus Datum und Zeit
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def idx_date_time(
    df: pd.DataFrame, col_date: str = "Datum", col_time: str = "Uhrzeit"
) -> None:
    """Index in datetime umwandeln"""
    ind = (
        pd.to_datetime(df.loc[:, col_date].values, format="%Y-%m-%d")
        + pd.to_timedelta([x.hour for x in df.loc[:, col_time].values], unit="hours")
        + pd.to_timedelta(
            [x.minute for x in df.loc[:, col_time].values], unit="minutes"
        )
    )

    df.set_index(ind, inplace=True)

    # Datum und Uhrzeit sind jetzt index - Spalten löschen
    df.drop([col_date, col_time], axis=1, inplace=True)


# 12 Stunden Uhr ohne am / pm in 24 Stunden umwandeln
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def am_pm(dic_df: dict, time_column: str = "Zeit") -> dict:
    """Zeitreihen ohne Unterscheidung zwischen vormittags und nachmittags"""
    for key in dic_df:
        if any(
            dic_df[key][time_column].dt.hour.diff().values < 0
        ) and any(  # Stunden haben negative Differenz
            dic_df[key][time_column].dt.day.diff().values == 0
        ):  # Tag bleibt gleich

            conditions = [
                (dic_df[key][time_column].dt.day.diff().values > 0),  # neuer Tag
                (dic_df[key][time_column].dt.month.diff().values != 0),  # neuer Monat
                (dic_df[key][time_column].dt.year.diff().values != 0),  # neues Jahr
                (  # Mittag
                    (dic_df[key][time_column].dt.hour.diff().values < 0)
                    & (  # Stunden haben negative Differenz
                        dic_df[key][time_column].dt.day.diff().values == 0
                    )  # Tag bleibt gleich
                ),
            ]

            choices = [
                pd.Timedelta(0, "h"),
                pd.Timedelta(0, "h"),
                pd.Timedelta(0, "h"),
                pd.Timedelta(12, "h"),
            ]

            offset = pd.Series(
                data=np.select(conditions, choices, default=np.nan),
                index=dic_df[key][time_column].index,
                dtype="timedelta64[ns]",
            )

            offset[0] = pd.Timedelta(0)
            offset.fillna(method="ffill", inplace=True)

            dic_df[key][time_column] += offset

    return dic_df


# Sommer-/Winterzeitumstellung
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def dls(df: pd.DataFrame) -> tuple:
    """Zeitumstellung - doppelte Stunde löschen"""
    # df innerhalb der Funktion
    framedel = df.copy().reset_index()

    conditions = [
        # Sommerzeitumstellung: letzter Sonntag im Maerz - von 2h auf 3h
        (
            (df.index.month.values == 3)  # Monat = 3 ---> März
            & (df.index.day.values > (31 - 7))  # letzte Woche (Tag > 31-7)
            & (df.index.weekday.values == 6)  # Wochentag = 6 ---> Sonntag
            & (df.index.hour.values == 3)  # Stunde 2 wird ausgelassen
        ),
        # Winterzeitumstellung: letzter Sonntag im Oktober - von 3h auf 2h (2h doppelt)
        (
            (df.index.month.values == 10)  # Monat = 10 ---> Oktober
            & (df.index.day.values > (31 - 7))  # letzte Woche (Tag > 31-7)
            & (df.index.weekday.values == 6)  # Wochentag = 6 ---> Sonntag
            & (df.index.hour.values == 2)  # Stunde 2 gibt es doppelt
        ),
    ]
    choices = ["Sommer", "Winter"]
    so_wi = np.select(conditions, choices, "")

    # neue Spalte im neuen df zur Markierung der zu löschenden Zeilen
    df["del"] = False

    # Winterzeitumstellung für jedes vorhandene Jahr bearbeiten
    for year_i in df.index.year.unique():

        # Prüfung, ob eine Zeitumstellung in den Daten ist
        # (negative Zeitdifferenz im Bereich der Winterzeitumstellung)
        if df.loc[
            (so_wi == "Winter") & (df.index.year == year_i)
        ].index.to_series().diff().min() < pd.Timedelta(0):

            print("Winterzeitumstellung", year_i, "wurde gefunden.")

            wi_len = ((so_wi == "Winter") & (df.index.year == year_i)).sum() / 2
            wi_start = (
                np.where((so_wi == "Winter") & (df.index.year == year_i))[0].min()
                + wi_len
            )

            # print("Winterzeitumstellung", wi_start, "bis", wi_start + wi_len)

            todel = (
                (so_wi == "Winter")
                & (framedel.index >= wi_start)
                & (framedel.index < (wi_start + wi_len))
            )

            df["del"] += todel  # Position der doppelten Stunde (zu löschende Zeilen)
        # else:
        # print('Für das Jahr', i, 'wurde keine Winterzeitumstellung gefunden')

    # df in dem nur die entfernten Daten stehen
    entf = df.loc[df["del"] is True].drop(labels="del", axis="columns")

    # df ohne doppelte 2Uhr-Stunde
    df = df.loc[df["del"] is False].drop(labels="del", axis="columns")

    # df mit gelöschten Daten ausgeben
    return (df, entf)


# Duplikate in Zeitstempeln löschen
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def indx_dup(dic_df: dict, time_column: str = "Zeit") -> dict:
    """doppelte Einträge im index löschen"""

    for key in dic_df:

        if dic_df[key].duplicated(subset=[time_column]).sum() > 0:
            dic_df[key].drop_duplicates(
                subset=[time_column], inplace=True, ignore_index=True
            )

        dic_df[key].set_index(time_column, inplace=True)

    return dic_df


# Lücken interpolieren
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def interpol(dic_df: dict) -> dict:
    """Lücken interpolieren"""

    for df in dic_df.values():
        for col in list(df.columns):
            df.loc[df[col].diff() == 0, col] = np.nan
            df = df.interpolate("akima")  # 'akima'

    return dic_df


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def cols_meta(df: pd.DataFrame) -> dict:
    """Metadaten"""

    cols = df.columns
    # test:
    # from fnmatch import fnmatch
    # from modules import def_dics as dics
    # cols= ['Bezug 1-1:1.29.3', 'Lieferung (1-1:2.5.3)', '1-1:1.5.22']
    dic_c_meta = {}
    for col in cols:
        dic_c_meta[col] = {"orig_tit": col}

        if fnmatch(col, dics.OBIS_PATTERN_EL):
            dic_c_meta[col]["code"] = "1-" + col.split("1-")[1].replace(
                "(", ""
            ).replace(")", "")
            dic_c_meta[col]["messgr_c"] = col.split(":")[1].split(".")[0]
            dic_c_meta[col]["messar_c"] = col.split(":")[1].split(".")[1]
            dic_c_meta[col]["messgr_n"] = (
                dics.DIC_OBIS_EL_KEY["Messgröße"]
                .get(dic_c_meta[col]["messgr_c"])
                .get("alt_bez")
            )
            dic_c_meta[col]["messar_n"] = (
                dics.DIC_OBIS_EL_KEY["Messart"]
                .get(dic_c_meta[col]["messar_c"])
                .get("alt_bez")
            )
            dic_c_meta[col]["unit_data"] = " " + dics.DIC_OBIS_EL_KEY["Messgröße"].get(
                dic_c_meta[col]["messgr_c"]
            ).get("unit")
            dic_c_meta[col]["unit_graph"] = (
                " kW"
                if dic_c_meta[col]["unit_data"] == " kWh"
                else dic_c_meta[col]["unit_data"]
            )
        # else:
        #     dic_c_meta[col]['code']     = None
        #     dic_c_meta[col]['messgr_c'] = None
        #     dic_c_meta[col]['messar_c'] = None
        #     dic_c_meta[col]['messgr_n'] = None
        #     dic_c_meta[col]['messar_n'] = None
        #     dic_c_meta[col]['unit_data']     = None

    messgr_vorh = {dic_c_meta[k].get("messgr_c") for k in dic_c_meta}

    lis_c_lang = []
    for messgr in messgr_vorh:
        if messgr:
            lis = [
                dic_c_meta[k].get("messgr_c") + "." + dic_c_meta[k].get("messar_c")
                for k in dic_c_meta
                if dic_c_meta[k].get("messgr_c") == messgr
            ]

            if len(set(lis)) > 1:
                lis_c_lang.append(messgr)

    for col in dic_c_meta:
        if dic_c_meta[col].get("code"):
            dic_c_meta[col]["tit"] = (
                dic_c_meta[col].get("messgr_n")
                if dic_c_meta[col].get("messgr_c") not in lis_c_lang
                else dic_c_meta[col].get("messgr_n")
                + " ("
                + dic_c_meta[col].get("code")
                + ")"
            )
        else:
            dic_c_meta[col]["tit"] = col

    return dic_c_meta


@dics.timer()
def del_smooth() -> None:
    """geglättete Linien löschen"""

    # Spalten in dfs löschen
    for item in st.session_state:
        if isinstance(item, pd.DataFrame):
            for col in item.columns:
                if "(glatt)" in col:
                    item.drop(columns=[col], inplace=True)

    # Linien löschen
    lis_dat = [
        dat for dat in st.session_state["fig_base"].data if "(glatt)" not in dat.name
    ]
    st.session_state["fig_base"].data = tuple(lis_dat)


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def df_multi_y(df: pd.DataFrame) -> None:
    """mehrere Jahre"""

    keys = list(st.session_state["dic_meta"].keys()).copy()
    keys_with_years = [
        k for k in keys if any(str(y) in k for y in st.session_state["lis_years"])
    ]

    keys_without_years = [
        k for k in keys if all(str(y) not in k for y in st.session_state["lis_years"])
    ]

    keys = [k for k in keys_without_years if all(k not in y for y in keys_with_years)]

    dic_df_multi = {}
    for year in st.session_state["lis_years"]:
        dic_df_multi[year] = df.loc[df.index.year == year, :].copy()
        dic_df_multi[year]["orgidx"] = df.loc[df.index.year == year, :].index
        if year != 2020:
            dic_df_multi[year].index = [
                dic_df_multi[year].index[x].replace(year=2020)
                for x in range(len(dic_df_multi[year].index))
            ]

        for key in keys:
            st.session_state["dic_meta"][key + " " + str(year)] = st.session_state[
                "dic_meta"
            ][key]

    st.session_state["dic_df_multi"] = dic_df_multi

    # df geordnete Jahresdauerlinie
    if st.session_state.get("cb_jdl"):
        dic_jdl = {y: jdl(dic_df_multi[y]) for y in st.session_state["lis_years"]}
        st.session_state["dic_jdl"] = dic_jdl

    # df Monatswerte
    if st.session_state.get("cb_mon"):
        dic_mon = {
            y: mon(dic_df_multi[y], st.session_state["dic_meta"], y)
            for y in st.session_state["lis_years"]
        }

        st.session_state["dic_mon"] = dic_mon


# Stundenwerte aus Zählerpunkten
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
# def h_from_zw(dic_df, _counter):
#     dic_df_h= {}
#     for key in dic_df.keys():
#         dic_df_h[key]= dic_df[key].diff()
#         dic_df_h[key]= dic_df_h[key].groupby(pd.Grouper(freq= 'H')).sum()
#         lis_mean= [k for k in _counter.keys() if _counter[k].combo == 'mean']
#         for col in list(dic_df_h[key].columns):
#             if  col in lis_mean:
#                 dic_df_h[key][col]= dic_df[key][col].diff().groupby(pd.Grouper(freq= 'H')).mean()

#     return dic_df_h


# Stundenwerte aus anderer zeitlicher Auflösung
@dics.timer()
def h_from_other(df: pd.DataFrame, dic_meta: dict) -> pd.DataFrame:
    """Stundenwerte"""

    df_h = pd.DataFrame()
    for col in [col for col in df.columns if "orgidx" not in col]:
        if col.endswith(" *h"):
            df_h.loc[:, col] = df.loc[:, col].copy()
        else:
            dic_meta[col + " *h"] = dic_meta[col].copy()

        if st.session_state["dic_meta"]["index"]["td_mean"] < pd.Timedelta(hours=1):
            if dic_meta[col].get("unit_data") in dics.GRP_MEAN:
                df_h.loc[:, col + " *h"] = df.loc[:, col].resample("H").mean()
            else:
                df_h.loc[:, col + " *h"] = df.loc[:, col].resample("H").sum()

        if st.session_state["dic_meta"]["index"]["td_mean"] == pd.Timedelta(hours=1):
            df_h.loc[:, col + " *h"] = df.loc[:, col].copy()

        for key in [col, col + " *h"]:
            dic_meta[key]["unit_graph"] = (
                " kW"
                if dic_meta[key].get("unit_data") == " kWh"
                else dic_meta[key].get("unit_data")
            )

            # dic_meta[k+' *h']['unit'] = (
            #     dic_meta[k].get('unit') + 'h'
            #     if dic_meta[k].get('unit')[-1] != 'h'
            #     else dic_meta[k].get('unit')
            # )
    df_h["orgidx"] = df_h.index.copy()
    st.session_state["dic_meta"] = dic_meta

    return df_h


# Jahresdauerlinie
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def jdl(df: pd.DataFrame) -> pd.DataFrame:
    """Jahresdauerlinie"""

    if df.index.to_series().diff().mean().round("min") < pd.Timedelta(hours=1):
        df = h_from_other(df, st.session_state["dic_meta"])

    df_jdl = pd.DataFrame(
        index=range(1, len(df.index) + 1),
        columns=[c for c in df.columns if c != "orgidx"],
    )

    for col in df_jdl.columns:
        df_col = df.sort_values(col, ascending=False)

        df_jdl[col] = df_col[col].values

        df_jdl[col + "_orgidx"] = (
            df_col["orgidx"].values if "orgidx" in df_col.columns else df_col.index
        )

    st.session_state["df_jdl"] = df_jdl

    return df_jdl


# Monatswerte
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def mon(df: pd.DataFrame, dic_meta: dict, year: int = None) -> pd.DataFrame:
    """Monatswerte"""

    if df.index.to_series().diff().mean().round("min") < pd.Timedelta(hours=1):
        df = h_from_other(df, dic_meta)

    df_mon = df.groupby(pd.Grouper(freq="M")).sum()
    for col in df_mon.columns:
        if dic_meta[col].get("unit_data") in [
            unit for unit in dics.GRP_MEAN if unit not in [" kWh", " kW"]
        ]:
            df_mon[col] = df[col].resample("M").mean()

    df_mon.index = [df_mon.index[x].replace(day=15) for x in range(len(df_mon.index))]

    if year:
        df_mon["orgidx"] = [
            df_mon.index[x].replace(year=year) for x in range(len(df_mon.index))
        ]
    else:
        df_mon["orgidx"] = df_mon.index.copy()

    st.session_state["df_mon"] = df_mon

    return df_mon


@dics.timer()
def dic_days(df: pd.DataFrame) -> None:
    """dictionary für Tage"""

    st.session_state["dic_days"] = {}
    for num in range(int(st.session_state["ni_days"])):
        date = st.session_state[f"day_{str(num)}"]

        item = st.session_state["dic_days"][f"{date:%d. %b %Y}"] = df.loc[
            f"{date:%Y-%m-%d}"
        ].copy()

        item["orgidx"] = item.index.copy()
        item.index = [
            item.index[x].replace(day=1, month=1, year=2020)
            for x in range(len(item.index))
        ]


# Spalte nach Einheiten durchsuchen
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def find_unit(df: pd.DataFrame, col: str) -> str | None:
    """Einheit für Spalte finden"""
    unit = None
    lis_units_low = [u.lower() for u in dics.LIS_UNITS]

    if any(str(x_i).lower() in lis_units_low for x_i in df.loc[:, col]):
        for u_i in df.loc[:, col]:
            if str(u_i).lower() in lis_units_low:
                unit = str(u_i)
                break

    return unit
