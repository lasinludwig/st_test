"""
Einstellungen und Anmerkungen für plots
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import signal

from modules import def_dics as dics
from modules import global_variables as gv

gv.exclude = ("hline", "(glatt)")

HALFDAY_MS = 12 * 60 * 60 * 1000  # 43.200.000
WEEK_MS = 7 * 24 * 60 * 60 * 1000  # 604.800.000
MON_MS = 30 * 24 * 60 * 60 * 1000  # 2.592.000.000


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def range_slider(fig: go.Figure) -> go.Figure:
    """Einstellungen für den range slider"""

    # max_y = max([max(t.y) for t in fig.data])
    # min_y = min([min(t.y) for t in fig.data])

    fig.update_xaxes(
        {
            "rangeslider": {
                "visible": True,
                # 'autorange': True,
                # 'yaxis': {
                #     'rangemode': 'fixed',
                #     'range': [min_y, max_y]
                # },
            },
            "rangeselector": {
                "buttons": [
                    {"count": 1, "label": "Tag", "step": "day", "stepmode": "backward"},
                    {
                        "count": 7,
                        "label": "Woche",
                        "step": "day",
                        "stepmode": "backward",
                    },
                    {
                        "count": 1,
                        "label": "Monat",
                        "step": "month",
                        "stepmode": "backward",
                    },
                    {"step": "all", "label": "alle"},
                ],
                "xanchor": "left",
            },
        }
    )

    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def update(
    fig: go.Figure,
    x_min: datetime = None,
    x_max: datetime = None,
    x_suffix: str = None,
    x_tickformat: str = "%b",
) -> go.Figure:
    """Aussehen der Grafik anpassen"""

    if x_max is None:
        x_max = max(max(p["x"]) for p in fig.data)

    if x_min is None:
        x_min = min(min(p["x"]) for p in fig.data)

    amo_y = len(fig.layout.meta.get("units"))

    fig.update_xaxes(
        nticks=13,
        tickformat=x_tickformat,
        ticklabelmode="period",
        ticksuffix=x_suffix,
        range=[x_min, x_max],
        separatethousands=True,
        tickformatstops=[
            {
                "dtickrange": [None, HALFDAY_MS],
                "value": "%H:%M\n%e. %b"
                if fig.layout.meta.get("multi_y")
                else "%H:%M\n%a %e. %b",
            },
            {
                "dtickrange": [HALFDAY_MS + 1, WEEK_MS],
                "value": "%e. %b" if fig.layout.meta.get("multi_y") else "%a\n%e. %b",
            },
            {"dtickrange": [WEEK_MS + 1, MON_MS], "value": "%e.\n%b"},
            {"dtickrange": [MON_MS + 1, None], "value": "%b"},
        ]
        if x_tickformat == "%b"
        else None,
        showspikes=True,
        spikemode="across",
        spikecolor="black",
        spikesnap="cursor",
        spikethickness=1,
        domain=[0, 1 - (amo_y - 1) * 0.025] if amo_y > 1 else [0, 1],
        fixedrange="Monatswerte" in fig.layout.meta.get("title"),
    )

    if (
        "Monatswerte" in fig.layout.meta.get("title")
        and fig.layout.meta.get("units")[0] == " kW"
    ):
        y_suffix = " kWh"
    else:
        y_suffix = fig.layout.meta.get("units")[0]

    fig.update_layout(
        {
            "yaxis": {
                "ticksuffix": y_suffix,
                "side": "left",
                "anchor": "x",
                "position": 0,
                "separatethousands": True,
                "fixedrange": False,
            }
        }
    )

    if amo_y > 1:
        for axis_i in range(1, amo_y):
            y_suffix = fig.layout.meta.get("units")[axis_i]

            fig.update_layout(
                {
                    "yaxis"
                    + str(axis_i + 1): {
                        "ticksuffix": y_suffix,
                        "side": "right",
                        "anchor": "free" if axis_i > 1 else "x",
                        "overlaying": "y",
                        "position": 1 - (amo_y - 2) * 0.15,
                        "separatethousands": True,
                        "fixedrange": False,
                        # 'scaleanchor': 'y',
                        "visible": True,
                        "gridcolor": "rgba("
                        + dics.FARBEN["hellgrau"]
                        + dics.ALPHA["bg"],
                    }
                }
            )

    fig.update_layout(
        separators=",.",
        font_family="Arial",
        title={
            # 'text': fig.layout.meta['title'],
            "xref": "container",
            "x": 0.02,
            "yref": "container",
            "y": 0.98,
        },
        legend={
            "groupclick": "toggleitem",
            # 'orientation': 'v',
            # 'yanchor': 'top',
            # 'y': 0.98,
            # 'xanchor': 'right',
            # 'x': 0.99
        },
        showlegend=len(
            [
                tr
                for tr in fig.data
                if tr.visible is True
                and all(n not in gv.exclude for n in tr.name.split())
            ]
        )
        != 1,
        # showlegend=(
        #     False
        #     if len(
        #         [
        #             tr
        #             for tr in fig.data
        #             if tr.visible is True
        #             and all([n not in exclude for n in tr.name.split()])
        #         ]
        #     )
        #     == 1
        #     else True
        # ),
        margin={"l": 5, "r": 5, "t": 70, "b": 10},
        hovermode="x",
    )

    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def add_arrow(
    fig: go.Figure,
    dic_meta: dict,
    lines: str = None,
    a_type: str = "peak",
    wert_x: datetime = None,
    wert_y: float = None,
    txt: str = None,
    hovtxt: str = None,
    anker: str = None,
    x_vers: int = 20,
    y_vers: int = 10,
) -> go.Figure:
    """Anmerkung mit Pfeil einfügen"""

    lines_input = lines
    anker_input = anker

    # Mitte der x-Achse
    x_max = max(max(dat["x"]) for dat in fig.data if len(dat["x"]) > 0)
    x_min = min(min(dat["x"]) for dat in fig.data if len(dat["x"]) > 0)
    middle_x = x_min + (x_max - x_min) / 2

    # alle Linien in Grafik
    lis_lines = [
        line.name for line in fig.data if all(e not in line.name for e in gv.exclude)
    ]

    # Ausrichtung
    if wert_x and anker_input is None:
        anker = "right" if wert_x > middle_x else "left"

    if a_type == "peak" and lines_input is None:
        lines = lis_lines

    lis_add_anno = [
        {
            "x": wert_x,
            "y": wert_y,
            "text": txt,
            "hovertext": hovtxt,
            "xanchor": anker,
            "ax": -20 if anker == "right" else 20,
            "ay": y_vers,
        }
    ]

    if lines:
        txt_input = txt
        hovtxt_input = hovtxt

        for line in lines:
            if dic_meta:
                manip = -1 if any(x in line for x in dics.LIS_NEG) else 1

            if a_type == "peak":
                dat = [x for x in fig.data if x.name == line][0]
                wert_y = max(dat["y"]) if manip > 0 else min(dat["y"])
                wert_x = dat["x"][np.where(dat["y"] == wert_y)[0][0]]

            if txt_input is None:
                txt = (
                    ("max. " if a_type == "peak" else "")
                    + str(line)
                    + ": "
                    + dics.nachkomma(wert_y)
                    + " "
                    + (dic_meta[line].get("unit_graph") if dic_meta else "")
                )

            if anker_input is None:
                anker = "right" if wert_x > middle_x else "left"

            x_vers = x_vers if anker == "left" else -x_vers
            y_vers = y_vers * manip

            if hovtxt_input is None and isinstance(wert_x, datetime):
                hovtxt = f"{wert_x:%d.%m.%Y %H:%M}"

            if hovtxt_input is None and "Jahresdauerlinie" in fig.layout.meta["title"]:
                hovtxt = dat["customdata"][np.where(dat["y"] == wert_y)[0][0]]
                hovtxt = f"{hovtxt:%d.%m.%Y %H:%M}"

            lis_add_anno.append(
                {
                    "x": wert_x,
                    "y": wert_y,
                    "text": txt,
                    "hovertext": hovtxt_input or hovtxt,
                    "xanchor": anker,
                    "ax": x_vers,
                    "ay": y_vers,
                }
            )

    # st.experimental_show(lis_add_anno)

    for item in lis_add_anno:

        fi_lis_anno = [
            fig.layout.annotations[pos]["text"]
            for pos in range(len(fig.layout.annotations))
        ]

        if item["text"] not in fi_lis_anno and item["x"]:
            fig.add_annotation(
                x=item["x"],
                y=item["y"],
                name=item["text"],
                text=item["text"],
                hovertext=item["hovertext"],
                xanchor=item["xanchor"],
                ax=item["ax"],
                ay=item["ay"],
                showarrow=True,
                arrowhead=3,
                bgcolor="rgba(" + dics.FARBEN["weiß"] + dics.ALPHA["bg"],
                visible=False,
            )

    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def arrows_min_max(figure: str) -> None:
    """Pfeile an Maximum und Minimum"""

    a_x = 20
    a_y = 10

    fig = st.session_state[figure]

    # Mitte der x-Achse
    x_max = max(max(dat["x"]) for dat in fig.data if len(dat["x"]) > 0)
    x_min = min(min(dat["x"]) for dat in fig.data if len(dat["x"]) > 0)
    mid_x = x_min + (x_max - x_min) / 2

    # alle Linien in Grafik
    lis_lines = [
        line for line in fig.data if all(e not in line.name for e in gv.exclude)
    ]

    for line in lis_lines:
        manip = -1 if any(x in line.name for x in dics.LIS_NEG) else 1

        val_y = np.nanmax(line.y) if manip > 0 else np.nanmin(line.y)
        val_x = line.x[np.where(line.y == val_y)[0][0]]
        yaxis = line.yaxis
        anc = "right" if val_x > mid_x else "left"

        text = (
            f"max. {str(line.name)}: "
            f"{dics.nachkomma(val_y*manip)} "
            f'{st.session_state["dic_meta"][line.name].get("unit_graph")}'
        )

        if isinstance(val_x, datetime):
            hovertext = f"{val_x:%d.%m. %H:%M}"

        if "Jahresdauerlinie" in fig.layout.meta["title"]:
            val = line.customdata[np.where(line.y == val_y)[0][0]]
            hovertext = f"{val:%d.%m. %H:%M}"

        if text in [an.name for an in fig.layout.annotations]:
            fig.layout.annotations[text] = {
                "x": val_x,
                "y": val_y,
                "yref": yaxis,
                "name": text,
                "text": text,
                "hovertext": hovertext,
                "xanchor": anc,
                "ax": -a_x if anc == "right" else a_x,
                "ay": a_y * manip,
            }
        else:
            fig.add_annotation(
                x=val_x,
                y=val_y,
                yref=yaxis,
                name=text,
                text=text,
                hovertext=hovertext,
                xanchor=anc,
                ax=-a_x if anc == "right" else a_x,
                ay=a_y * manip,
                showarrow=True,
                arrowhead=3,
                bgcolor="rgba(" + dics.FARBEN["weiß"] + dics.ALPHA["bg"],
                visible=False,
            )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def vline(fig: go.Figure, x_val: float or datetime, txt: str, pos: str) -> None:
    """eine vertikale Linie einfügen"""

    fig.add_vline(
        x=x_val,
        line_dash="dot",
        line_width=1,
        annotation_text=txt,
        annotation_position=pos,
        annotation_textangle=-90,
        annotation_bgcolor="rgba(" + dics.FARBEN["weiß"] + dics.ALPHA["bg"],
    )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def hide_hlines(fig: go.Figure) -> None:
    """horizontale Linien ausblenden (ohne sie zu löschen)"""

    for dat in fig.data:
        if "hline" in dat.name:
            dat.visible = False

    lis_data = [fig.layout.shapes, fig.layout.annotations]
    for dat in lis_data:
        for item in dat:
            if "hline" in item.name:
                item.visible = False

    # fig.for_each_trace(
    #     lambda trace: trace.update(visible=False) if "hline" in trace.name else None
    # )

    # for sh in fig.layout.shapes:
    #     if "hline" in sh.name:
    #         sh.visible = False

    # for an in fig.layout.annotations:
    #     if "hline" in an.name:
    #         an.visible = False


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def hline_line(
    fig: go.Figure, value: float, ti_hor: str = None, cb_hor_dash: bool = True
) -> None:
    """horizontale Linie einfügen"""

    ti_hor = None if ti_hor in {"", "new text"} else ti_hor

    if any("hline" in x for x in [s.name for s in fig.layout.shapes]):
        for shape in fig.layout.shapes:
            if "hline" in shape.name:
                shape.y0 = shape.y1 = value
                shape.visible = True
                shape.line.dash = "dot" if cb_hor_dash else "solid"

        for annot in fig.layout.annotations:
            if "hline" in annot.name:
                annot.y = value
                annot.visible = bool(ti_hor)
                annot.text = ti_hor

    else:
        fig.add_hline(
            y=value,
            name="hline",
            line_dash="dot" if cb_hor_dash else "solid",
            line_width=1,
            annotation_text=ti_hor,
            annotation_name="hline",
            annotation_visible=bool(ti_hor),
            annotation_position="top left",
            annotation_bgcolor="rgba(" + dics.FARBEN["weiß"] + dics.ALPHA["bg"],
            visible=True,
        )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def hline_fill(fig: go.Figure, value: float, ms_hor: list) -> go.Figure:
    """Ausfüllen zwischen horizontaler Linie und Linien"""
    dic_fill = {}
    traces = [tr for tr in fig.data if tr.name in ms_hor]

    for trace in traces:
        if value > 0:
            dic_fill[trace.name] = np.where(trace.y < value, trace.y, value)
        else:
            dic_fill[trace.name] = np.where(trace.y > value, trace.y, value)

    # hline-Füllungen, die es schon gibt
    for key in dic_fill:
        if "hline " + key in [tr.name for tr in fig.data]:
            trace = [tr for tr in fig.data if tr.name == "hline " + key][0]
            trace.y = dic_fill[trace.name.replace("hline ", "")]
            trace.showlegend = False
            trace.visible = True

        else:
            trace = [tr for tr in fig.data if tr.name == key][0]
            fig.add_trace(
                go.Scatter(
                    x=trace.x,
                    y=dic_fill[trace.name],
                    legendgroup=trace.legendgroup,
                    name="hline " + trace.name,
                    fill="tozeroy",
                    fillcolor="rgba(" + dics.FARBEN["schwarz"] + dics.ALPHA["fill"],
                    mode="none",
                    showlegend=False,
                    visible=True,
                    hoverinfo="skip",
                )
            )

    return fig


# horizontale / vertikale Linien
@dics.timer()
def h_v_lines() -> None:
    """horizontale und vertikale Linien"""

    # horizontale Linie
    lis_figs_hor = ["fig_base"]
    if st.session_state.get("cb_jdl"):
        lis_figs_hor.append("fig_jdl")

    for fig in lis_figs_hor:
        hide_hlines(st.session_state[fig])
        if st.session_state["ni_hor"] != 0:
            hline_line(
                st.session_state[fig],
                st.session_state["ni_hor"],
                st.session_state["ti_hor"],
                st.session_state.get("cb_hor_dash"),
            )
            # st.session_state[fig]= fuan.hline_fill(
            #   st.session_state[fig],
            #   st.session_state['ni_hor'],
            #   st.session_state['ms_hor']
            # )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def smooth(fig: go.Figure) -> None:
    """geglättete Linien"""

    lis_trace = [
        trace
        for trace in st.session_state[fig].data
        if all(n not in gv.exclude for n in trace.name.split())
    ]

    for trace in lis_trace:

        y_glatt = signal.savgol_filter(
            x=pd.Series(trace["y"]).interpolate("akima"),
            mode="mirror",
            window_length=int(st.session_state["gl_win"]),
            polyorder=int(st.session_state["gl_deg"]),
        )

        if trace.name + " (glatt)" not in [
            tr.name for tr in st.session_state[fig].data
        ]:
            st.session_state[fig].add_trace(
                go.Scatter(
                    x=trace["x"],
                    y=y_glatt,
                    mode="lines",
                    line_dash="0.75%",
                    name=trace.name + " (glatt)",
                    legendgroup=trace.legendgroup or "geglättet",
                    legendgrouptitle_text=trace.legendgroup or "geglättet",
                    hoverinfo="skip",
                    visible=True,
                    yaxis=st.session_state["dic_meta"][trace.name].get("y_axis"),
                )
            )

        else:
            for dat in st.session_state[fig].data:
                if dat.name == trace.name + " (glatt)":
                    dat["y"] = y_glatt
                    break


# Ausreißer entfernen
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def remove_outl(fig: go.Figure, cut_off: float) -> go.Figure:
    """Ausreißerbereinigung"""
    for trace in fig.data:
        trace["y"] = pd.Series(
            np.where(trace["y"] > cut_off, np.nan, trace["y"])
        ).interpolate("akima")

    for annot in fig.layout.annotations:
        if annot["y"] > cut_off:
            y_old = annot["y"]
            annot["y"] = cut_off
            # an['name'] = an['name'].replace(str(y_old), str(cut_off))
            annot["text"] = annot["text"].replace(str(y_old), str(cut_off))

    return fig


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def add_points(fig: go.Figure, df: pd.DataFrame, lines: list) -> None:
    """Punkte hinzufügen"""

    for line in lines:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[line],
                name=line,
                hovertemplate=("%{y:,.1f}"),
                mode="markers",
                showlegend=False,
            )
        )


# Ausreißerbereinigung
@dics.timer()
def clean_outliers() -> None:
    """Ausreißerbereinigung"""

    if st.session_state["ni_outl"] < st.session_state["abs_max"]:
        for fig in st.session_state["lis_figs"]:
            if fig != "fig_mon":
                st.session_state[fig] = remove_outl(
                    st.session_state[fig], st.session_state["ni_outl"]
                )


# geglättete Linien
# @dics.timer()
# def smooth():
#     # geglättete Linien
#     st.session_state["fig_base"] = smoothing(
#         fig=st.session_state["fig_base"],
#         dic_meta=st.session_state["dic_meta"],
#         window=int(st.session_state["gl_win"]),
#         order=int(st.session_state["gl_deg"]),
#     )


@dics.timer()
def update_vis_main() -> None:
    """Darstellungseinstellungen"""

    for fig in st.session_state["lis_figs"]:

        switch = fig == "fig_days"

        # anzuzeigende Achsen
        axes_vis = [
            dat.yaxis
            for dat in st.session_state[fig].data
            if st.session_state.get(f"cb_vis_{dat.legendgroup if switch else dat.name}")
        ]
        axes_layout = [x for x in st.session_state[fig].layout if "yaxis" in x]

        for a_x in axes_layout:
            st.session_state[fig].update_layout(
                {a_x: {"visible": a_x.replace("axis", "") in axes_vis}}
            )

        # anzuzeigende Traces
        for trace in st.session_state[fig].data:
            if not switch:
                trace.line.color = st.session_state.get("cp_" + trace.name)
            trace.visible = st.session_state[
                f"cb_vis_{trace.legendgroup if switch else trace.name}"
            ]
            trace.fill = (
                "tozeroy"
                if st.session_state[
                    f"cb_fill_{trace.legendgroup if switch else trace.name}"
                ]
                else None
            )

        for annot in st.session_state[fig].layout.annotations:
            if "hline" not in annot.name:
                annot.visible = bool(st.session_state.get("cb_anno_" + annot.name))

        # Legende ausblenden, wenn nur eine Linie angezeigt wird
        st.session_state[fig].update_layout(
            showlegend=len(
                [
                    tr
                    for tr in st.session_state[fig].data
                    if tr.visible is True
                    and all(n not in gv.exclude for n in tr.name.split())
                ]
            )
            != 1
        )

    # Gruppierung der Legende ausschalten, wenn nur eine Linie in Gruppe
    if st.session_state.get("cb_multi_year"):
        if "lgr" not in st.session_state:
            st.session_state["lgr"] = {
                tr.name: tr.legendgroup
                for tr in st.session_state["fig_base"].data
                if tr.legendgroup is not None
            }

        if "lgr_t" not in st.session_state:
            st.session_state["lgr_t"] = {
                tr.name: tr.legendgrouptitle
                for tr in st.session_state["fig_base"].data
                if tr.legendgrouptitle is not None
            }

        b_gr = False
        if (
            len(
                {
                    tr.legendgroup
                    for tr in st.session_state["fig_base"].data
                    if tr.visible
                }
            )
            > 1
        ):
            for leg_gr in set(st.session_state["lgr"].values()):
                if (
                    len(
                        [
                            trace
                            for trace in st.session_state["fig_base"].data
                            if (
                                st.session_state["lgr"].get(trace.name) == leg_gr
                                and trace.visible
                            )
                        ]
                    )
                    > 1
                ):
                    b_gr = True

        if b_gr:
            for trace in st.session_state["fig_base"].data:
                if trace.legendgroup is None:
                    trace.legendgroup = st.session_state["lgr"].get(trace.name)
                    trace.legendgrouptitle = st.session_state["lgr_t"].get(trace.name)
        else:
            st.session_state["fig_base"].update_traces(
                legendgroup=None,
                legendgrouptitle=None,
            )


@dics.timer()
def plotly_config(height: int = 420, title_edit: bool = True) -> dict:
    """Anzeigeeinstellungen für Plotly-Grafiken"""

    config = {
        "scrollZoom": True,
        "locale": "de_DE",
        "displaylogo": False,
        "modeBarButtonsToAdd": [
            "lasso2d",
            "select2d",
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
        ],
        "modeBarButtonsToRemove": [
            "zoomIn",
            "zoomOut",
        ],
        "toImageButtonOptions": {
            "format": "svg",  # one of png, svg, jpeg, webp
            "filename": "grafische Datenauswertung",
            "height": height,
            "width": 640,  # 640 passt auf eine A4-Seite (ist in Word knapp 17 cm breit)
            # 'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
        },
        "edits": {
            "annotationTail": True,  # Enables changing the length and direction of the arrow.
            "annotationPosition": True,
            "annotationText": True,
            "axisTitleText": False,
            "colorbarPosition": True,
            "colorbarTitleText": True,
            "legendPosition": True,
            "legendText": True,
            "shapePosition": True,
            "titleText": title_edit,
        },
    }

    return config


@dics.timer()
def html_exp(f_pn: str = "export/interaktive_grafische_Auswertung.html") -> None:
    """html-Export"""

    if os.path.exists(f_pn):
        os.remove(f_pn)

    with open(f_pn, "w") as fil:
        fil.write("<!DOCTYPE html>")
        fil.write("<title>Interaktive Grafische Datenauswertung</title>")
        fil.write("<head><style>")
        fil.write("h1{text-align: left; font-family: sans-serif;}")
        fil.write("body{width: 85%; margin-left:auto; margin-right:auto}")
        fil.write("</style></head>")
        fil.write('<body><h1><a href="https://www.utec-bremen.de/">')
        fil.write(dics.render_svg())
        fil.write("</a><br /><br />")
        fil.write("Interaktive Grafische Datenauswertung")
        fil.write("</h1><br /><hr><br /><br />")

        fil.write("<style>")
        fil.write("#las{width: 100%; margin-left:auto; margin-right:auto; }")

        if any(
            "Jahresdauerlinie" in st.session_state[fig].layout.meta.get("title")
            for fig in st.session_state["lis_figs"]
        ):
            fil.write("#jdl{width: 45%; float: left; margin-right: 5%; }")
            fil.write("#mon{width: 45%; float: right; margin-left: 5%; }")
        else:
            fil.write("#mon{width: 45%; float: left; margin-right: 5%; }")

        fil.write("</style>")

        for fig in st.session_state["lis_figs"]:
            if "Lastgang" in st.session_state[fig].layout.meta.get("title"):
                fil.write('<div id="las">')
            elif "Jahresdauerlinie" in st.session_state[fig].layout.meta.get("title"):
                fil.write('<div id="jdl">')
            elif "Monatswerte" in st.session_state[fig].layout.meta.get("title"):
                fil.write('<div id="mon">')

            fil.write(
                st.session_state[fig].to_html(full_html=False, config=plotly_config())
            )

            fil.write("<br /><br /><hr><br /><br /><br /></div>")

        fil.write("</body></html>")
