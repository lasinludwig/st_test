"""
Meteorologische Daten
"""

import datetime
import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

import geopy
import meteostat as met
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from geopy import distance
from wetterdienst import Settings as dwd_settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest as dwd

from modules import def_dics as dics
from modules import global_variables as gv

load_dotenv(".streamlit/secrets.toml")

# Grenze für Daten-Validität
# einen Wetterstation muss für den angegebenen Zeitraum
# mind. diesen Anteil an tatsächlich aufgezeichneten Daten haben
DATA_THRESH = 0.85

# Einstellungen für Daten aus DWD-Stationen
dwd_settings.si_units = False
dwd_settings.skip_empty = True
dwd_settings.skip_threshold = DATA_THRESH
dwd_settings.dropna = True


# nur für Testzwecke im interaktiven Fenster
PAR_TEST = "temperature_air_mean_200"
STATION_ID_TEST = "05822"

# Umkreis für Meteostat-Stationen
WEATHERSTATIONS_MAX_DISTANCE = 700

# minimaler Abstand zwischen DWD-Wetterstationen
MIN_DIST_DWD_STAT = 3.6


@dics.timer()
def start_end_time(
    page: str = None,
) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    """
    Zeitraum für Daten-Download
    """

    if page is None:
        page = st.session_state.get("page")

    if page == "meteo":
        start_year = (
            min(
                st.session_state["meteo_start_year"],
                st.session_state["meteo_end_year"],
            )
            if "meteo_start_year" in st.session_state
            else 2020
        )

        if "meteo_end_year" in st.session_state:
            end_year = max(
                st.session_state["meteo_start_year"],
                st.session_state["meteo_end_year"],
            )
        else:
            end_year = 2020

        start_time = datetime.datetime(
            start_year, 1, 1, 0, 0, tzinfo=ZoneInfo("Europe/Berlin")
        )
        end_time = datetime.datetime(
            end_year, 12, 31, 23, 59, tzinfo=ZoneInfo("Europe/Berlin")
        )
        if end_time.year == datetime.datetime.now().year:
            end_time = datetime.datetime.now()
    elif "df" not in st.session_state:
        start_time = end_time = None
    else:
        ind_0 = min(st.session_state["df"].index[0], st.session_state["df"].index[-1])
        ind_1 = max(st.session_state["df"].index[0], st.session_state["df"].index[-1])
        start_time = datetime.datetime(
            ind_0.year,
            1,
            1,
            0,
            0,
            tzinfo=ZoneInfo("Europe/Berlin"),
        )
        end_time = datetime.datetime(
            ind_1.year,
            12,
            31,
            23,
            59,
            tzinfo=ZoneInfo("Europe/Berlin"),
        )

    return start_time, end_time


if "page" in st.session_state:
    start, end = start_end_time(st.session_state.get("page"))


@dics.timer()
def geo(address: str) -> dict:
    """
    geographische daten (Längengrad, Breitengrad) aus eingegebener Adresse
    """
    geolocator = geopy.geocoders.Nominatim(user_agent=os.getenv("GEO_USER_AGENT"))
    location = geolocator.geocode(address)
    dic_geo = {
        "lat": location.latitude,
        "lon": location.longitude,
        "alt": location.altitude,
    }
    st.session_state["dic_geo"] = dic_geo

    return dic_geo


@dics.timer()
def all_stations() -> pd.DataFrame:
    """df aller Stationen (DWD und Meteostat)"""
    df_dwd = dwd_stations()
    df_met = meteostat_stations()
    df_all = (
        pd.concat([df_dwd, df_met], ignore_index=True)
        .sort_values(["distance"])
        .reset_index(drop=True)
    )
    st.session_state["df_all_stations"] = df_all
    return df_all


@dics.timer()
def all_stations_without_dups() -> pd.DataFrame:
    """alle Stationen (DWD und Meteostat) ohne Duplikate"""
    df = (
        st.session_state["df_all_stations"]
        if "df_all_stations" in st.session_state
        else all_stations()
    ).copy()

    lis_drop = []
    for ind in df.index:
        if "DWD" in df.loc[ind, "provider"]:
            df_met_sta = meteostat_stations(
                lat=df.loc[ind, "latitude"],
                lon=df.loc[ind, "longitude"],
                distance_sta=250,
            )
            df_met_sta = df_met_sta[df_met_sta["distance"] <= MIN_DIST_DWD_STAT * 1000]

            for sta_id in df_met_sta.index:
                df_drp = df[
                    (df["station_id"] == sta_id) & (df["provider"] == "Meteostat")
                ]
                lis_drop += list(df_drp.index)

    df = df.drop(lis_drop, axis="index")
    st.session_state["all_stations_without_dups"] = df
    return df


@dics.timer()
def same_station_in_meteostat(latitude: float, longitude: float) -> None:
    """DWD-Station in Meteostat finden"""
    df_met_sta = meteostat_stations(
        lat=latitude,
        lon=longitude,
        distance_sta=250,
    )
    if df_met_sta.loc[df_met_sta.index[0], "distance"] <= MIN_DIST_DWD_STAT * 1000:
        return df_met_sta.index[0]

    return None


@dics.timer()
def dwd_req(par: list = None) -> dwd:
    """Zugriff auf DWD-Stationen"""
    if "start" not in locals():
        start_time, end_time = start_end_time(st.session_state.get("page"))

    if par is None:
        par = ["temperature_air_mean_200"]
    return dwd(
        parameter=par,
        resolution="hourly",
        start_date=start_time,
        end_date=end_time,
    )


@dics.timer()
def dwd_stations() -> pd.DataFrame:
    """
    Alle dwd-Stationen, die Temperaturdaten in stündlicher Auflösung
    für den gewählten Zeitraum haben
    (Temperaturdaten weil das hoffentlich alle haben)
    """
    adr = st.session_state.get("ti_adr")  # or "Bremen"
    lat = geo(adr)["lat"]
    lon = geo(adr)["lon"]

    # mit Abstandsspalte
    df_dwd_stations = (
        dwd_req()
        .filter_by_distance(
            latitude=lat,
            longitude=lon,
            distance=1_000_000,
        )
        .df
    )

    # für den gewählten Zeitraum
    df_dwd_stations = dwd_stations_df_edit(df_dwd_stations)
    st.session_state["df_dwd_stations"] = df_dwd_stations

    return df_dwd_stations


@dics.timer()
def dwd_stations_df_edit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Anpassung auf Format der Meteostat-Stationen und
    Filter DWD-Stationen, die Daten für den gewählten Zeitraum haben
    """
    if "start" not in locals():
        start_time, end_time = start_end_time(st.session_state.get("page"))
    df["provider"] = "DWD"
    df["timezone"] = "Europe/Berlin"
    df["country"] = "DE"
    ren_cols = {
        "height": "elevation",
        "state": "region",
        "from_date": "hourly_start",
        "to_date": "hourly_end",
    }
    df = df.rename(columns=ren_cols)

    df = df[df["hourly_start"] < start_time]
    df = df[df["hourly_end"] > end_time]
    df = df.reset_index(drop=True)
    return df


@dics.timer()
def meteostat_stations(
    lat: float = None,
    lon: float = None,
    distance_sta: float = WEATHERSTATIONS_MAX_DISTANCE,
) -> pd.DataFrame:
    """
    verfügbare Wetterstationen von meteostat
    in x Meter entfernung zur gegebenen Addresse
    mit stündlichen Daten in der erforderlichen Zeitperiode
    """
    if "start" not in locals():
        start_time, end_time = start_end_time(st.session_state.get("page"))

    if lat is None or lon is None:
        adr = st.session_state.get("ti_adr")  # or "Bremen"
        lat = geo(adr)["lat"]
        lon = geo(adr)["lon"]

    # alle Wetterstationen im gewählten Umkreis um den Standort
    df_meteostat_stations = (
        met.Stations()
        .nearby(lat, lon, distance_sta * 1_000)
        .inventory(
            "hourly", (start_time.replace(tzinfo=None), end_time.replace(tzinfo=None))
        )
    ).fetch()

    if distance_sta == WEATHERSTATIONS_MAX_DISTANCE:
        df_meteostat_stations = meteostat_stations_df_edit(df_meteostat_stations)
        st.session_state["df_meteostat_stations"] = df_meteostat_stations

    return df_meteostat_stations


@dics.timer()
def meteostat_stations_df_edit(df: pd.DataFrame) -> pd.DataFrame:
    """Anpassung auf Format der Meteostat-Stationen"""
    df["station_id"] = df.index
    df = df.reset_index(drop=True)
    df["provider"] = "Meteostat"

    drop_cols = [
        "wmo",
        "icao",
        "daily_start",
        "daily_end",
        "monthly_start",
        "monthly_end",
    ]
    df = df.drop(columns=drop_cols)

    # Distanz zum gewählten Standort in km umrechnen (wird in m ausgegeben)
    df["distance"] = df["distance"] / 1000

    return df


@dics.timer()
def meteostat_data_by_stationid(station_id: str) -> pd.DataFrame:
    """Meteostat-Daten eine einzelnen Station"""
    if "start" not in locals():
        start_time, end_time = start_end_time(st.session_state.get("page"))

    meteostat_data_hourly = met.Hourly(
        station_id,
        start_time.replace(tzinfo=None),
        end_time.replace(tzinfo=None),
    )
    meteostat_codes = [par.code for par in LIS_PARAMS if "Meteostat" in par.provider]
    meteostat_data_norm = meteostat_data_hourly.normalize()
    meteostat_data_inter = meteostat_data_norm.interpolate()
    df_meteostat_data = meteostat_data_inter.fetch()

    # only columns where at least x% of entries are valid data
    df_meteostat_data = df_meteostat_data.dropna(
        axis="columns", thresh=df_meteostat_data.shape[0] * DATA_THRESH
    )

    df_meteostat_data = df_meteostat_data.drop(
        columns=[
            col
            for col in df_meteostat_data.columns
            if col.upper() not in meteostat_codes
        ]
    )

    return df_meteostat_data


@dics.timer()
def closest_station_with_data(param: str) -> tuple[str | float]:
    """nächstgelegene Station, die Daten zum gewählten Parameter hat"""
    if "DWD" in param.provider:
        df_dwd_st = (
            st.session_state.get("df_dwd_stations")
            if "df_dwd_stations" in st.session_state
            else dwd_stations()
        )
        idx_0 = df_dwd_st.index[0]
        station_id = f'DWD_{df_dwd_st.loc[idx_0, "station_id"]}'
        distance_sta = df_dwd_st.loc[idx_0, "distance"]
        df = (
            dwd_req([param.code])
            .filter_by_station_id(station_id.split("_")[-1])
            .values.all()
            .df
        )
        if df.empty:
            for rank in range(1, df_dwd_st.shape[0]):
                idx = df_dwd_st.index[rank]
                station_id = f'DWD_{df_dwd_st.loc[idx, "station_id"]}'
                distance_sta = df_dwd_st.loc[idx, "distance"]
                df = (
                    dwd_req([param.code])
                    .filter_by_station_id(station_id.split("_")[-1])
                    .values.all()
                    .df
                )
                if not df.empty:
                    break

    if "Meteostat" in param.provider:
        df_met_st = (
            st.session_state.get("df_meteostat_stations")
            if "df_meteostat_stations" in st.session_state
            else meteostat_stations()
        )
        idx_0 = df_met_st.index[0]
        station_id = f'Meteostat_{df_met_st.loc[idx_0, "station_id"]}'
        distance_sta = df_met_st.loc[idx_0, "distance"]
        df_station_data = meteostat_data_by_stationid(station_id.split("_")[-1])
        if param.code.lower() not in df_station_data.columns:
            for rank in range(1, df_met_st.shape[0]):
                idx = df_met_st.index[rank]
                station_id = f'Meteostat_{df_met_st.loc[idx, "station_id"]}'
                distance_sta = df_met_st.loc[idx, "distance"]
                df_station_data = meteostat_data_by_stationid(station_id.split("_")[-1])
                if param.code.lower() in df_station_data.columns:
                    break

    return station_id, distance_sta


@dics.timer()
def selected_params(page: str = "meteo") -> list:
    """ausgewählte Parameter"""

    if "graph" in page:
        lis_sel_params = st.session_state.get("lis_sel_params")
    else:
        lis_sel_params = [
            par for par in LIS_PARAMS if st.session_state.get(f"cb_{par.tit_de}")
        ] or [par for par in LIS_PARAMS if par.tit_de in LIS_DEFAULT_PARAMS]

    df_dwd_st = (
        st.session_state.get("df_dwd_stations")
        if "df_dwd_stations" in st.session_state
        else dwd_stations()
    )
    df_met_st = (
        st.session_state.get("df_meteostat_stations")
        if "df_meteostat_stations" in st.session_state
        else meteostat_stations()
    )

    for par in lis_sel_params:
        par.closest_station_id, par.distance = closest_station_with_data(par)

    for par in lis_sel_params:
        lis_dup = [param for param in lis_sel_params if param.tit_de in par.tit_de]
        if len(lis_dup) > 1:
            station_ids = [lis_dup[pos].closest_station_id for pos in range(2)]
            stations = [
                df_dwd_st[df_dwd_st["station_id"] == s_id.split("_")[-1]]
                if "DWD" in s_id
                else df_met_st[df_met_st["station_id"] == s_id.split("_")[-1]]
                for s_id in station_ids
            ]
            positions = [
                (
                    station.loc[station.index[0], "latitude"],
                    station.loc[station.index[0], "longitude"],
                )
                for station in stations
            ]

            if distance.distance(positions[0], positions[1]).km < MIN_DIST_DWD_STAT:
                lis_sel_params.remove(
                    lis_dup[0] if "DWD" in lis_dup[0].provider else lis_dup[1]
                )
            else:
                lis_sel_params.remove(
                    lis_dup[0]
                    if lis_dup[0].distance > lis_dup[1].distance
                    else lis_dup[1]
                )

    st.session_state["lis_sel_params"] = lis_sel_params
    return lis_sel_params


@dics.timer()
def used_stations() -> pd.DataFrame:
    """nur verwendete Stationen"""
    lis_sel_params = (
        st.session_state["lis_sel_params"]
        if "lis_sel_params" in st.session_state
        else selected_params()
    )

    df_all = (
        st.session_state["df_all_stations"]
        if "df_all_stations" in st.session_state
        else all_stations()
    )

    set_used_stations = {par.closest_station_id for par in lis_sel_params}
    df_used_stations = pd.concat(
        [
            df_all[
                (df_all["station_id"] == st.split("_")[1])
                & (df_all["provider"] == st.split("_")[0])
            ]
            for st in set_used_stations
        ]
    )
    df_used_stations["params"] = [
        [
            par.tit_de
            for par in lis_sel_params
            if par.closest_station_id.split("_")[1]
            in df_used_stations.loc[idx, "station_id"]
        ]
        for idx in df_used_stations.index
    ]

    st.session_state["df_used_stations"] = df_used_stations
    return df_used_stations


@dics.timer()
def used_stations_show() -> pd.DataFrame:
    """df mit verwendeten Stationen für die Darstellung in der app"""
    df = (
        st.session_state["df_used_stations"]
        if "df_used_stations" in st.session_state
        else used_stations()
    )

    # delete station if closer than max_dist_wetter
    for cnt_1 in range(df.shape[0] - 2) or [0]:
        idx_1 = df.index[cnt_1]
        pos_1 = (df.loc[idx_1, "latitude"], df.loc[idx_1, "longitude"])
        for cnt_2 in range(cnt_1 + 1, df.shape[0] - 1) or [1]:
            idx_2 = df.index[cnt_2]
            pos_2 = (df.loc[idx_2, "latitude"], df.loc[idx_2, "longitude"])
            if distance.distance(pos_1, pos_2).km < MIN_DIST_DWD_STAT:
                params = df.loc[idx_1, "params"] + df.loc[idx_2, "params"]
                prov_1 = df.loc[idx_1, "provider"]
                ind = (idx_2, idx_1) if "DWD" in prov_1 else (idx_1, idx_2)
                df = df.drop(ind[0], axis="index")
                df.at[ind[1], "params"] = params

    st.session_state["df_used_stations_show"] = df
    return df


@dics.timer()
def df_used_show_edit() -> pd.DataFrame:
    """Anpassen und formatieren des df der benutzten Wetterstationen"""
    df = (
        st.session_state["df_used_stations_show"]
        if "df_used_stations_show" in st.session_state
        else used_stations_show()
    )

    li_drp = [
        "hourly_start",
        "hourly_end",
        "timezone",
        "provider",
        "station_id",
    ]
    df = df.drop(li_drp, axis="columns")
    df.index = df["name"]

    # rename everything
    ren = {
        "distance": "Entfernung",
        "region": "Region",
        "country": "Land",
        "elevation": "Höhe über NN",
        "latitude": "Breitengrad",
        "longitude": "Längengrad",
        "params": "Parameter",
    }
    df = df.rename(ren, axis="columns")
    df = df[ren.values()]
    df = df.sort_values(["Entfernung"])

    df = df.style.format(
        {
            "Höhe über NN": "{:,.1f} m",
            "Breitengrad": "{:,.2f}°",
            "Längengrad": "{:,.2f}°",
            "Entfernung": "{:,.1f} km",
        },
        decimal=",",
        thousands=".",
    )

    return df


@dics.timer()
def meteo_data() -> pd.DataFrame:
    """
    Meteorologische Daten für die ausgewählten Parameter
    """
    page = st.session_state.get("page")
    if "start" not in locals():
        start_time, end_time = start_end_time(st.session_state.get("page"))

    # alte Grafiken löschen
    for key, value in st.session_state.items():
        if isinstance(value, go.Figure):
            dics.del_session_state_entry(key)

    lis_sel_params = (
        st.session_state.get("lis_sel_params")
        if "lis_sel_params" in st.session_state
        else selected_params()
    )

    if "graph" in page:
        lis_sel_params = selected_params("graph")

    set_used_stations = {par.closest_station_id for par in lis_sel_params}

    met_data = {}
    for station in set_used_stations:
        station_provider = station.split("_")[0]
        station_id = station.split("_")[1]
        ren = {}
        if "Meteostat" in station_provider:
            met_data[station_id] = meteostat_data_by_stationid(station_id)

            for col in met_data[station_id]:
                ren[col] = DIC_METEOSTAT_CODES[col.upper()]["tit"]
            met_data[station_id].rename(columns=ren, inplace=True)

        else:
            pars = [
                par.code
                for par in lis_sel_params
                if station_id in par.closest_station_id.split("_")
            ]
            df = dwd_req(pars).filter_by_station_id(station_id).values.all().df

            met_data[station_id] = df.dropna().pivot(
                index="date", columns="parameter", values="value"
            )

            for col in met_data[station_id]:
                ren[col] = DIC_TRANSLATE_DWD_NAMES[col]
            met_data[station_id].rename(columns=ren, inplace=True)
            met_data[station_id].index = met_data[station_id].index.tz_localize(None)

    df = pd.DataFrame()
    for par in lis_sel_params:
        station_id = par.closest_station_id.split("_")[1]
        for col in met_data[station_id]:
            if col in [param.tit_de for param in lis_sel_params]:
                df[col] = met_data[station_id][col]

    df = df[df.index >= start_time.replace(tzinfo=None)]
    df = df[df.index <= end_time.replace(tzinfo=None)]

    # df = dls(df)[0]
    st.session_state["meteo_data"] = df

    return df


# ---------------------------------------------------------------------------


@dics.timer()
def outside_temp_graph() -> None:
    """
    Außentemperatur in df für Grafiken eintragen
    """
    page = st.session_state.get("page")
    if "graph" not in page:
        return

    st.session_state["lis_sel_params"] = [ClassParam("temperature_air_mean_200")]
    if "meteo_data" not in st.session_state:
        meteo_data()
    st.session_state["meteo_data"].rename(
        columns={"Lufttemperatur in 2 m Höhe": "temp"}, inplace=True
    )

    st.session_state["df_temp"] = st.session_state["meteo_data"]["temp"]

    st.session_state["dic_meta"]["Temperatur"] = {
        "tit": "Temperatur",
        "orig_tit": "temp",
        "unit_data": " °C",
        "unit_graph": " °C",
    }
    if "Temperatur" in st.session_state["df"].columns:
        st.session_state["df"].drop(columns=["Temperatur"], inplace=True)

    df = pd.concat(
        [
            st.session_state["df"],
            st.session_state["df_temp"].reindex(st.session_state["df"].index),
        ],
        axis=1,
    )
    df.rename(columns={"temp": "Temperatur"}, inplace=True)
    dics.units()

    if st.session_state.get("cb_h") is False:
        df["Temperatur"] = df["Temperatur"].interpolate(method="akima", axis="index")

    st.session_state["df"] = df


@dics.timer()
def del_meteo() -> None:
    """vorhandene meteorologische Daten löschen"""
    # Spalten in dfs löschen
    for key in st.session_state:
        if isinstance(st.session_state[key], pd.DataFrame):
            for col in st.session_state[key].columns:
                for meteo in [
                    str(DIC_METEOSTAT_CODES[code]["tit"])
                    for code in DIC_METEOSTAT_CODES
                ]:
                    if meteo in col:
                        st.session_state[key].drop(columns=[str(col)], inplace=True)

    # Metadaten löschen
    if st.session_state.get("dic_meta"):
        if "Temperatur" in st.session_state["dic_meta"].keys():
            del st.session_state["dic_meta"]["Temperatur"]
        if (
            " °C"
            not in [
                st.session_state["dic_meta"][key].get("unit_graph")
                for key in st.session_state["dic_meta"].keys()
            ]
            and " °C" in st.session_state["dic_meta"]["units"]["set"]
        ):
            st.session_state["dic_meta"]["units"]["set"].remove(" °C")

    # Linien löschen
    for key in st.session_state:
        if isinstance(st.session_state[key], go.Figure):
            dics.del_session_state_entry(key)


# --------------------------------------------------------------------------

# Parameter
@dataclass
class ClassParam:
    """Parameter der Wetterstationen"""

    code: str
    tit_en: str = field(default=None)
    tit_de: str = field(default=None)
    cat_utec: str = field(default=None)
    cat_en: str = field(default=None)
    cat_de: str = field(default=None)
    default: bool = field(default=False)
    unit: str = field(default=None)
    pandas_styler: str = field(default=None)
    num_format: str = field(default=None)
    provider: str = field(default="DWD")
    closest_station_id: str = None
    distance: float = None

    def __post_init__(self) -> None:
        """Eigenschaften nach Erzeugung der Felder ausfüllen"""
        if self.code in DIC_METEOSTAT_CODES:
            self.provider = "Meteostat"

        # meteostat Parameter
        if "Meteostat" in self.provider:
            self.tit_en = DIC_METEOSTAT_CODES[self.code].get("orig_name")
            self.tit_de = DIC_METEOSTAT_CODES[self.code].get("tit")
            self.unit = DIC_METEOSTAT_CODES[self.code].get("unit")
            self.cat_utec = DIC_METEOSTAT_CODES[self.code].get("cat_utec")

        # dwd Parameter
        if "DWD" in self.provider:
            self.tit_en = self.code
            self.tit_de = DIC_TRANSLATE_DWD_NAMES[self.code]
            self.cat_en = [
                cat
                for cat in gv.dic_dwd_hourly_parameters
                if self.code in gv.dic_dwd_hourly_parameters[cat]
            ][0]
            self.cat_de = DIC_TRANSLATE_DWD_CATEGORIES[self.cat_en]

            # eigene Kategorien
            if self.code.startswith("temperature"):
                self.cat_utec = LIS_CAT_UTEC[0]
            elif self.code[:3] in ["rad", "sun", "win"]:
                self.cat_utec = LIS_CAT_UTEC[1]
            elif self.code[:8] in ["humidity", "pressure", "precipit"]:
                self.cat_utec = LIS_CAT_UTEC[2]
            elif self.code[:5] in ["cloud", "visib"]:
                self.cat_utec = LIS_CAT_UTEC[3]

            self.unit = gv.dic_dwd_hourly_parameters[self.cat_en][self.code].get(
                "origin"
            )

        self.num_format = f'#,##0.0" {self.unit}"'
        self.pandas_styler = "{:,.1f} " + self.unit
        self.default = self.tit_de in LIS_DEFAULT_PARAMS


# alle DWD-Parameter, die stündliche Auflösung haben
gv.dic_dwd_hourly_parameters = dwd.discover(flatten=False)["hourly"]

# Parameter, die standardmäßig für den Download ausgewählt sind
LIS_DEFAULT_PARAMS: list = [
    "Lufttemperatur in 2 m Höhe",
    "Globalstrahlung",
    "Windgeschwindigkeit",
    "Windrichtung",
]

# Übersetzungen
DIC_TRANSLATE_DWD_CATEGORIES: dict = {
    "temperature_air": "Lufttemperatur",
    "cloud_type": "Bewölkungstyp",
    "cloudiness": "Bewölkungsgrad",
    "dew_point": "Taupunkt",
    "wind_extreme": "Extremer Wind",
    "moisture": "Feuchtigkeit",
    "precipitation": "Niederschlag",
    "pressure": "Druck",
    "temperature_soil": "Temperatur Erdreich",
    "solar": "Solarstrahlung",
    "sun": "Sonne",
    "visibility": "Sicht",
    "weather_phenomena": "Wetterphänomene",
    "wind": "Wind",
    "wind_synoptic": "Wind synoptisch",
}

DIC_TRANSLATE_DWD_NAMES: dict = {
    "temperature_air_mean_200": "Lufttemperatur in 2 m Höhe",
    "temperature_soil_mean_002": "Erdbodentemperatur in 2 cm Tiefe",
    "temperature_soil_mean_005": "Erdbodentemperatur in 5 cm Tiefe",
    "temperature_soil_mean_010": "Erdbodentemperatur in 10 cm Tiefe",
    "temperature_soil_mean_020": "Erdbodentemperatur in 20 cm Tiefe",
    "temperature_soil_mean_050": "Erdbodentemperatur in 50 cm Tiefe",
    "temperature_soil_mean_100": "Erdbodentemperatur in 100 cm Tiefe",
    "temperature_dew_point_mean_200": "Taupunkttemperatur in 2 m Höhe",
    "temperature_wet_mean_200": "Feuchtetemperatur",
    "radiation_global": "Globalstrahlung",
    "radiation_sky_short_wave_diffuse": "diffuse Strahlung",
    "radiation_sky_long_wave": "atmosphärische Gengenstrahlung",
    "sunshine_duration": "Sonnenscheindauer",
    "sun_zenith_angle": "Zenitwinkel der Sonne",
    "wind_speed": "Windgeschwindigkeit",
    "wind_direction": "Windrichtung",
    "wind_gust_max": "stärktste Windböe",
    "humidity": "relative Feuchte",
    "humidity_absolute": "absolute Feuchte",
    "pressure_air_sea_level": "Luftdruck auf Meereshöhe",
    "pressure_vapor": "Dampfdruck",
    "pressure_air_site": "Luftdruck auf Stationshöhe",
    "precipitation_height": "Niederschlagshöhe",
    "precipitation_form": "Niederschlagsart",
    "precipitation_indicator": "Niederschlagsindikator",
    "cloud_cover_total": "Gesamtbedeckungsgrad",
    "cloud_cover_total_indicator": "Gesamtbedeckungsgrad Index",
    "cloud_cover_layer1": "Bedeckungsgrad der 1. Schicht",
    "cloud_cover_layer2": "Bedeckungsgrad der 2. Schicht",
    "cloud_cover_layer3": "Bedeckungsgrad der 3. Schicht",
    "cloud_cover_layer4": "Bedeckungsgrad der 4. Schicht",
    "cloud_height_layer1": "Wolkenhöhe der 1. Schicht",
    "cloud_height_layer2": "Wolkenhöhe der 2. Schicht",
    "cloud_height_layer3": "Wolkenhöhe der 3. Schicht",
    "cloud_height_layer4": "Wolkenhöhe der 4. Schicht",
    "cloud_type_layer1": "Wolkenart der 1. Schicht",
    "cloud_type_layer2": "Wolkenart der 2. Schicht",
    "cloud_type_layer3": "Wolkenart der 3. Schicht",
    "cloud_type_layer4": "Wolkenart der 4. Schicht",
    "visibility_range": "Sichtweite",
    "visibility_range_indicator": "Sichtweite Index",
    "true_local_time": "Ortszeit",
    "end_of_interval": "Intervallende",
    "weather": "Wetter",
    "weather_text": "Wetterbeschreibung",
    "quality": "Qualität",
}

# Parameter von Meteostat
DIC_METEOSTAT_CODES: dict = {
    "TEMP": {
        "orig_name": "Air Temperature",
        "tit": "Lufttemperatur in 2 m Höhe",
        "unit": "°C",
        "cat_utec": "Temperaturen",
    },
    "DWPT": {
        "orig_name": "Dew Point",
        "tit": "Taupunkt",
        "unit": "°C",
        "cat_utec": "Temperaturen",
    },
    "PRCP": {
        "orig_name": "Total Precipitation",
        "tit": "Niederschlag",
        "unit": "mm",
        "cat_utec": "Feuchte, Luftdruck, Niederschlag",
    },
    "WDIR": {
        "orig_name": "Wind (From) Direction",
        "tit": "Windrichtung",
        "unit": "°",
        "cat_utec": "Sonne und Wind",
    },
    "WSPD": {
        "orig_name": "Average Wind Speed",
        "tit": "Windgeschwindigkeit",
        "unit": "km/h",
        "cat_utec": "Sonne und Wind",
    },
    "WPGT": {
        "orig_name": "Wind Peak Gust",
        "tit": "max. Windböe",
        "unit": "km/h",
        "cat_utec": "Sonne und Wind",
    },
    "RHUM": {
        "orig_name": "Relative Humidity",
        "tit": "rel. Luftfeuchtigkeit",
        "unit": "%",
        "cat_utec": "Feuchte, Luftdruck, Niederschlag",
    },
    "PRES": {
        "orig_name": "Sea-Level Air Pressure",
        "tit": "Luftdruck (Meereshöhe)",
        "unit": "hPa",
        "cat_utec": "Feuchte, Luftdruck, Niederschlag",
    },
    "SNOW": {
        "orig_name": "Snow Depth",
        "tit": "Schneehöhe",
        "unit": "m",
        "cat_utec": "Feuchte, Luftdruck, Niederschlag",
    },
    "TSUN": {
        "orig_name": "Total Sunshine Duration",
        "tit": "Sonnenstunden",
        "unit": "min",
        "cat_utec": "Sonne und Wind",
    },
}

# Eigene Kategorien
LIS_CAT_UTEC: list = [
    "Temperaturen",
    "Sonne und Wind",
    "Feuchte, Luftdruck, Niederschlag",
    "Bewölkung und Sichtweite",
]

# alle Parameter
LIS_PARAMS: list = [
    ClassParam(key)
    for key in list(DIC_TRANSLATE_DWD_NAMES.keys()) + list(DIC_METEOSTAT_CODES.keys())
    if ClassParam(key).cat_utec
]

DIC_PARAMS: dict = {
    key: ClassParam(key)
    for key in list(DIC_TRANSLATE_DWD_NAMES.keys()) + list(DIC_METEOSTAT_CODES.keys())
    if ClassParam(key).cat_utec
}
