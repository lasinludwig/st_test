"""
Darstellung der Plots
"""

import os
from collections import Counter

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from geopy import distance

from modules import def_dics as dics
from modules import meteorolog as meteo


@dics.timer()
def line_plot(
    df: pd.DataFrame,
    dic_meta: dict,
    lines: list = None,
    title: str = "",
    var_name: str = "",
) -> go.Figure:
    """Liniengrafik"""

    if not lines:
        lines = list(df.columns)

    fig = go.Figure()
    fig.layout.meta = {
        "title": title,
        "var_name": var_name,
    }

    lis_units = []
    for line in [lin for lin in lines if "orgidx" not in lin]:
        lis_units.append(dic_meta[line].get("unit_graph"))
        manip = -1 if any(True for x in line.split() if x in dics.LIS_NEG) else 1
        cusd = df[f"{line}_orgidx"] if f"{line}_orgidx" in df.columns else df["orgidx"]

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[line] * manip,
                customdata=cusd,
                name=dic_meta[line].get("tit"),
                hovertemplate=(
                    np.select(
                        [abs(df[line]) < 10, abs(df[line]) < 100],
                        [
                            "%{y:,.2f}"
                            + dic_meta[line].get("unit_graph")
                            + (
                                " (%{customdata|%a %d. %b %Y %H:%M})"
                                if "Monatswerte" not in title
                                else " (%{customdata|%b %Y})"
                            ),
                            "%{y:,.1f}"
                            + dic_meta[line].get("unit_graph")
                            + (
                                " (%{customdata|%a %d. %b %Y %H:%M})"
                                if "Monatswerte" not in title
                                else " (%{customdata|%b %Y})"
                            ),
                        ],
                        "%{y:,.0f}"
                        + dic_meta[line].get("unit_graph")
                        + (
                            " (%{customdata|%a %d. %b %Y %H:%M})"
                            if "Monatswerte" not in title
                            else " (%{customdata|%b %Y})"
                        ),
                    )
                ),
                mode="lines",
                visible=True,
                yaxis=dic_meta[line]["y_axis"],
            )
        )

    fig.layout.meta["units"] = sorted(
        Counter(lis_units), key=Counter(lis_units).get, reverse=True
    )

    return fig


# Lastgang mehrerer Jahre übereinander darstellen
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def line_plot_y_overlay(
    dic_df: dict,
    dic_meta: dict,
    lis_years: list,
    lines: list = None,
    title: str = "",
    var_name: str = "",
) -> go.Figure:
    """Liniengrafik mit mehreren Jahren übereinander (Jahreszahlen werden ausgetauscht)"""
    fig = go.Figure()
    fig.layout.meta = {
        "title": title,
        "var_name": var_name,
        "multi_y": True,
    }

    if lines is None:
        lines = list(dic_df[list(dic_df.keys())[0]].columns)

    lis_units = []
    for line in [lin for lin in lines if "orgidx" not in lin]:

        lis_units.append(dic_meta[line].get("unit_graph"))
        manip = -1 if any(True for x in line.split() if x in dics.LIS_NEG) else 1
        for year in lis_years:
            cusd = (
                dic_df[year][f"{line}_orgidx"]
                if f"{line}_orgidx" in list(dic_df[year].columns)
                else dic_df[year]["orgidx"]
            )

            fig.add_trace(
                go.Scatter(
                    x=dic_df[year].index,
                    y=dic_df[year][line] * manip,
                    customdata=cusd,
                    legendgroup=year,
                    legendgrouptitle_text=year,
                    name=dic_meta[line].get("tit") + " " + str(year),
                    mode="lines",
                    hovertemplate=(
                        np.select(
                            [
                                abs(dic_df[year][line]) < 10,
                                abs(dic_df[year][line]) < 100,
                            ],
                            [
                                "%{y:,.2f}"
                                + dic_meta[line].get("unit_graph")
                                + (
                                    " (%{customdata|%a %d. %b %Y %H:%M})"
                                    if "Monatswerte" not in title
                                    else " (%{customdata|%b %Y})"
                                ),
                                "%{y:,.1f}"
                                + dic_meta[line].get("unit_graph")
                                + (
                                    " (%{customdata|%a %d. %b %Y %H:%M})"
                                    if "Monatswerte" not in title
                                    else " (%{customdata|%b %Y})"
                                ),
                            ],
                            "%{y:,.0f}"
                            + dic_meta[line].get("unit_graph")
                            + (
                                " (%{customdata|%a %d. %b %Y %H:%M})"
                                if "Monatswerte" not in title
                                else " (%{customdata|%b %Y})"
                            ),
                        )
                    ),
                    visible=True,
                    yaxis=dic_meta[line].get("y_axis"),
                )
            )

    fig.layout.meta["units"] = sorted(
        Counter(lis_units), key=Counter(lis_units).get, reverse=True
    )

    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def line_plot_day_overlay(
    dic_days: dict, dic_meta: dict, title: str = "", var_name: str = ""
) -> go.Figure:
    """Liniengrafik für Tagesvergleich"""

    fig = go.Figure()
    fig.layout.meta = {
        "title": title,
        "var_name": var_name,
    }

    lis_units = []
    for date in dic_days:
        for line in [lin for lin in dic_days[date].columns if "orgidx" not in lin]:
            lis_units.append(dic_meta[line].get("unit_graph"))
            manip = -1 if any(True for x in line.split() if x in dics.LIS_NEG) else 1
            cusd = (
                dic_days[f"{line}_orgidx"]
                if f"{line}_orgidx" in dic_days[date].columns
                else dic_days[date]["orgidx"]
            )

            fig.add_trace(
                go.Scatter(
                    x=dic_days[date].index,
                    y=dic_days[date][line] * manip,
                    customdata=cusd,
                    name=date,
                    mode="lines",
                    hovertemplate=(
                        np.select(
                            [
                                abs(dic_days[date][line]) < 10,
                                abs(dic_days[date][line]) < 100,
                            ],
                            [
                                "%{y:,.2f}"
                                + dic_meta[line].get("unit_graph")
                                + " (%{customdata|%a %e. %b %Y %H:%M})<extra>"
                                + line
                                + "</extra>",
                                "%{y:,.1f}"
                                + dic_meta[line].get("unit_graph")
                                + " (%{customdata|%a %e. %b %Y %H:%M})<extra>"
                                + line
                                + "</extra>",
                            ],
                            "%{y:,.0f}"
                            + dic_meta[line].get("unit_graph")
                            + " (%{customdata|%a %e. %b %Y %H:%M})<extra>"
                            + line
                            + "</extra>",
                        )
                    ),
                    legendgroup=line,
                    legendgrouptitle_text=line,
                    visible=True,
                    yaxis=dic_meta[line]["y_axis"],
                )
            )

    fig.layout.meta["units"] = sorted(
        Counter(lis_units), key=Counter(lis_units).get, reverse=True
    )

    return fig


@dics.timer()
def map_dwd_all() -> go.Figure:
    """Karte aller Wetterstationen"""

    hov_temp = "(lat: %{lat:,.2f}° | lon: %{lon:,.2f}°)<br>%{text}<extra></extra>"

    # alle Stationen
    all_sta = meteo.dwd_req().all().df
    all_lat = list(all_sta["latitude"])
    all_lon = list(all_sta["longitude"])
    all_nam = list(all_sta["name"])

    # alle Stationen
    fig = go.Figure(
        data=go.Scattermapbox(
            lat=all_lat,
            lon=all_lon,
            text=all_nam,
            mode="markers",
            marker={
                "size": 4,
                "color": "blue",
                # "colorscale": "Portland",  # Blackbody,Bluered,Blues,Cividis,Earth,Electric,Greens,Greys,Hot,Jet,Picnic,Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                # "colorbar": {
                #     "title": "Entfernung<br>DWD-Station<br>Adresse<br> ----- ",
                #     "bgcolor": "rgba(255,255,255,0.5)",
                #     "ticksuffix": " km",
                #     "x": 0,
                # },
                # "opacity": 0.5,
                # "reversescale": True,
                # "cmax": 400,
                # "cmin": 0,
            },
            hovertemplate=hov_temp,
        )
    )

    fig.update_layout(
        title="Wetterstationen des DWD",
        autosize=True,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": 4.5,
            "center": {
                "lat": 51.5,
                "lon": 9.5,
            },
        },
    )

    return fig


@dics.timer()
def map_weatherstations() -> go.Figure:
    """Karte der Wetterstationen (verwendete hervorgehoben)"""

    # alle Stationen ohne Duplikate
    all_sta = meteo.meteostat_stations()

    # nächstgelegene Station
    clo_sta = all_sta[all_sta.index == all_sta.index[0]].copy()

    # verwendete Stationen
    used_sta = (
        st.session_state["df_used_stations_show"]
        if "df_used_stations_show" in st.session_state
        else meteo.used_stations_show()
    )

    # verwendete und nächstgelegene Stationen löschen
    for ind in used_sta.index:
        lat = used_sta.loc[ind, "latitude"]
        lon = used_sta.loc[ind, "longitude"]
        met_sta = meteo.same_station_in_meteostat(lat, lon)

        if met_sta is not None:
            ind = all_sta[all_sta["station_id"] == met_sta].index[0]
            all_sta = all_sta.drop(ind, axis="index")
    if clo_sta.index[0] in used_sta.index:
        used_sta = used_sta.drop(clo_sta.index[0], axis="index")

    # delete station if closer than max_dist_wetter
    clo_pos = (
        clo_sta.loc[clo_sta.index[0], "latitude"],
        clo_sta.loc[clo_sta.index[0], "longitude"],
    )
    for ind in used_sta.index:
        sta_pos = (used_sta.loc[ind, "latitude"], used_sta.loc[ind, "longitude"])
        if distance.distance(clo_pos, sta_pos).km < meteo.MIN_DIST_DWD_STAT:
            used_sta = used_sta.drop(ind, axis="index")

    if clo_sta.index[0] in all_sta.index:
        all_sta = all_sta.drop(clo_sta.index[0], axis="index")

    # alle Stationen
    fig = go.Figure(
        data=go.Scattermapbox(
            lat=list(all_sta["latitude"]),
            lon=list(all_sta["longitude"]),
            text=list(all_sta["name"]),
            customdata=list(all_sta["distance"]),
            mode="markers",
            marker={
                "size": list(all_sta["distance"])[::-1],
                "sizeref": float(meteo.WEATHERSTATIONS_MAX_DISTANCE / 7),
                "sizemin": 2,
                "allowoverlap": True,
                "color": list(all_sta["distance"]),
                "colorscale": "Blues",  # Blackbody,Bluered,Blues,Cividis,Earth,Electric,Greens,Greys,Hot,Jet,Picnic,Portland,Rainbow,RdBu,Reds,Viridis,YlGnBu,YlOrRd
                "colorbar": {
                    "title": "Entfernung<br> ----- ",
                    "bgcolor": "rgba(255,255,255,0.5)",
                    "ticksuffix": " km",
                    "x": 0,
                },
                "opacity": 0.5,
                "reversescale": True,
                "cmax": meteo.WEATHERSTATIONS_MAX_DISTANCE,
                "cmin": 0,
            },
            hovertemplate="<b>%{text}</b> <i>(Entfernung: %{customdata:,.1f} km)</i><extra></extra>",
        )
    )

    # eingegebene Adresse
    fig.add_trace(
        go.Scattermapbox(
            lat=[st.session_state["dic_geo"]["lat"]],
            lon=[st.session_state["dic_geo"]["lon"]],
            text=[st.session_state["ti_adr"].title()],
            hovertemplate="<b>%{text}</b><br>→ eingegebener Standort<extra></extra>",
            mode="markers",
            marker={
                "size": 12,
                "color": "limegreen",
            },
        )
    )

    # closest station
    fig.add_trace(
        go.Scattermapbox(
            lat=[clo_sta.loc[clo_sta.index[0], "latitude"]],
            lon=[clo_sta.loc[clo_sta.index[0], "longitude"]],
            customdata=[clo_sta.loc[clo_sta.index[0], "distance"]],
            text=[f"{clo_sta.loc[clo_sta.index[0], 'name']}"],
            hovertemplate="<b>%{text}</b> <i>(Entfernung: %{customdata:,.1f} km)</i><br>→ nächstgelgene Wetterstation<extra></extra>",
            mode="markers",
            marker={
                "size": 12,
                "color": "crimson",
            },
        )
    )

    # Wetterstationen für Zusatzparameter
    if used_sta.shape[0] > 0:
        for ind in used_sta.index:
            fig.add_trace(
                go.Scattermapbox(
                    lat=[used_sta.loc[ind, "latitude"]],
                    lon=[used_sta.loc[ind, "longitude"]],
                    customdata=[
                        f'<i>(Entfernung: {used_sta.loc[ind, "distance"]:,.1f} km)</i><br>→ nächstgelgene Wetterstation für Parameter<br>{", ".join(used_sta.loc[ind, "params"])}'
                    ],
                    text=[used_sta.loc[ind, "name"]],
                    hovertemplate="<b>%{text}</b> %{customdata}<extra></extra>",
                    mode="markers",
                    marker={
                        "size": 12,
                        "color": "gold",
                    },
                )
            )

    fig.update_layout(
        # title=f"Wetterstationen im Radius von {meteo.weatherstations_max_distance} km um den Standort",
        autosize=False,
        height=800,
        showlegend=False,
        font_family="Arial",
        separators=",.",
        margin={"l": 5, "r": 5, "t": 30, "b": 5},
        mapbox={
            "accesstoken": os.getenv("MAPBOX_TOKEN"),
            "zoom": 6,
            "center": {
                "lat": st.session_state["dic_geo"]["lat"],
                "lon": st.session_state["dic_geo"]["lon"],
            },
        },
    )
    st.session_state["meteo_fig"] = fig
    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
def timings(dic: dict) -> go.Figure:
    """Grafik mit Ausführungszeiten für debug"""
    fig_tim = go.Figure(
        [
            go.Bar(
                x=list(dic.keys()),
                y=list(dic.values()),
            )
        ]
    )

    fig_tim.update_layout(
        {
            "title": {
                "text": "execution times of the latest run",
            },
            "yaxis": {
                "ticksuffix": " s",
            },
        }
    )

    return fig_tim
