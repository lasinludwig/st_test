"""
plots erstellen und in session_state schreiben
"""

import datetime

import pandas as pd
import streamlit as st

from modules import def_dics as dics
from modules import fig_update_anno as fuan
from modules import plotly_plots as ploplo

TIT_H = '<i><span style="font-size: 12px;"> (Stundenwerte)</span></i>'
TIT_15 = '<i><span style="font-size: 12px;"> (15-Minuten-Werte)</span></i>'

# Grund-Grafik
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def cr_fig_base() -> None:
    """Lastgang erstellen"""

    if st.session_state.get("cb_h"):
        tit_res = TIT_H
    elif st.session_state["dic_meta"]["index"]["td_mean"] == pd.Timedelta(minutes=15):
        tit_res = TIT_15

    if st.session_state.get("cb_multi_year"):
        st.session_state["fig_base"] = ploplo.line_plot_y_overlay(
            st.session_state["dic_df_multi"],
            st.session_state["dic_meta"],
            st.session_state["lis_years"],
            title=f"Lastgang{tit_res}",
        )
    else:
        if (
            len(st.session_state["lis_years"]) == 1
            and st.session_state["lis_years"][0] < datetime.datetime.now().year
        ):
            tit = "Lastgang " + str(st.session_state["lis_years"][0]) + tit_res
        else:
            tit = f"Lastgang{tit_res}"
        # tit = (
        #     "Lastgang " + str(st.session_state["lis_years"][0]) + tit_res
        #     if len(st.session_state["lis_years"]) == 1
        #     and st.session_state["lis_years"][0] < datetime.datetime.now().year
        #     else f"Lastgang{tit_res}"
        # )

        st.session_state["fig_base"] = ploplo.line_plot(
            st.session_state["df_h"]
            if st.session_state.get("cb_h")
            else st.session_state["df"],
            st.session_state["dic_meta"],
            title=tit,
        )

    # Pfeile an Maxima
    fuan.arrows_min_max("fig_base")

    # geglättete Linien
    max_val = int(
        max(len(t.x) for t in st.session_state["fig_base"].data if len(t.x) > 20) // 3
    )

    max_val = st.session_state["smooth_max_val"] = int(
        max_val + 1 if max_val % 2 == 0 else max_val
    )
    start_val = max_val // 5
    st.session_state["smooth_start_val"] = int(
        start_val + 1 if start_val % 2 == 0 else start_val
    )
    if "gl_win" not in st.session_state:
        st.session_state["gl_win"] = st.session_state["smooth_start_val"]
    if "gl_deg" not in st.session_state:
        st.session_state["gl_deg"] = 3

    fuan.smooth("fig_base")

    # updates
    st.session_state["fig_base"] = fuan.update(
        st.session_state["fig_base"], st.session_state["dic_meta"]
    )
    st.session_state["fig_base"].update_layout(
        title_text=st.session_state["fig_base"].layout.meta.get("title"),
    )

    # range slider und "zoom"-Knöpfle
    st.session_state["fig_base"] = fuan.range_slider(st.session_state["fig_base"])

    # colours
    for count, line in enumerate(st.session_state["fig_base"].data):
        if len(line.x) > 0 and "hline" not in line.name:
            st.session_state["fig_base"].data[count].line.color = (
                st.session_state["fig_base"]
                .layout.template.layout.colorway[int(str(count)[-1])]
                .lower()
            )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def cr_fig_jdl() -> None:
    """Jahresdauerlinie erstellen"""

    if st.session_state.get("cb_multi_year"):
        st.session_state["fig_jdl"] = ploplo.line_plot_y_overlay(
            st.session_state["dic_jdl"],
            st.session_state["dic_meta"],
            st.session_state["lis_years"],
            title=f"geordnete Jahresdauerlinie{TIT_H}",
        )
    else:
        if (
            len(st.session_state["lis_years"]) == 1
            and st.session_state["lis_years"][0] < datetime.datetime.now().year
        ):
            tit = (
                "geordnete Jahresdauerlinie "
                + str(st.session_state["lis_years"][0])
                + TIT_H
            )
        else:
            tit = f"geordnete Jahresdauerlinie{TIT_H}"

        # tit = (
        #     "geordnete Jahresdauerlinie "
        #     + str(st.session_state["lis_years"][0])
        #     + TIT_H
        #     if len(st.session_state["lis_years"]) == 1
        #     and st.session_state["lis_years"][0] < datetime.datetime.now().year
        #     else f"geordnete Jahresdauerlinie{TIT_H}"
        # )

        st.session_state["fig_jdl"] = ploplo.line_plot(
            st.session_state["df_jdl"], st.session_state["dic_meta"], title=tit
        )

    # Pfeile an Maxima
    fuan.arrows_min_max("fig_jdl")

    # updates
    st.session_state["fig_jdl"] = fuan.update(
        st.session_state["fig_jdl"],
        st.session_state["dic_meta"],
        x_suffix=" h",
        x_tickformat=",d",
    )

    st.session_state["fig_jdl"].update_layout(
        title_text=st.session_state["fig_jdl"].layout.meta.get("title"),
        legend={"yanchor": "top", "y": 0.975, "xanchor": "right", "x": 0.975},
    )
    st.session_state["fig_jdl"].update_traces(
        legendgroup=None,
        legendgrouptitle=None,
    )
    x_min = min(min(d.x) for d in st.session_state["fig_jdl"].data)
    x_max = max(max(d.x) for d in st.session_state["fig_jdl"].data)

    if 7000 < x_max < 9000:
        st.session_state["fig_jdl"].update_xaxes(
            range=[x_min, 9000],
        )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def cr_fig_mon() -> None:
    """Monatswerte erstellen"""

    if st.session_state.get("cb_multi_year"):
        st.session_state["fig_mon"] = ploplo.line_plot_y_overlay(
            st.session_state["dic_mon"],
            st.session_state["dic_meta"],
            st.session_state["lis_years"],
            title="Monatswerte",
        )
    else:
        if (
            len(st.session_state["lis_years"]) == 1
            and st.session_state["lis_years"][0] < datetime.datetime.now().year
        ):
            tit = "Monatswerte " + str(st.session_state["lis_years"][0])
        else:
            tit = "Monatswerte"

        # tit = "Monatswerte " + (
        #     str(st.session_state["lis_years"][0])
        #     if len(st.session_state["lis_years"]) == 1
        #     and st.session_state["lis_years"][0] < datetime.datetime.now().year
        #     else "Monatswerte"
        # )

        st.session_state["fig_mon"] = ploplo.line_plot(
            st.session_state["df_mon"], st.session_state["dic_meta"], title=tit
        )

    # Pfeile an Maxima
    fuan.arrows_min_max("fig_mon")

    if st.session_state.get("cb_multi_year"):
        x_min = datetime.datetime(2020, 1, 1)
        x_max = datetime.datetime(2020, 12, 31)
    else:
        x_min = min(tr.x.min() for tr in st.session_state["fig_mon"].data).replace(
            day=1
        )
        x_max = max(tr.x.max() for tr in st.session_state["fig_mon"].data).replace(
            day=31
        )

    st.session_state["fig_mon"] = fuan.update(st.session_state["fig_mon"], x_max, x_min)

    st.session_state["fig_mon"].update_xaxes(
        tickformat="%b",
        tickformatstops=[
            {"dtickrange": [None, None], "value": "%b"},
        ],
    )
    st.session_state["fig_mon"].update_traces(
        mode="markers+lines",
        line={"dash": "dash", "width": 1},
        marker={"size": 10},
        legendgroup=None,
        legendgrouptitle=None,
    )
    st.session_state["fig_mon"].update_layout(
        title_text=st.session_state["fig_mon"].layout.meta.get("title"),
        legend={"yanchor": "top", "y": 0.975, "xanchor": "right", "x": 0.975},
    )


@dics.timer()
def cr_fig_days() -> None:
    """Tagesvergleiche"""

    tit = "Vergleich ausgewählter Tage"
    if st.session_state.get("cb_h"):
        tit += TIT_H
    elif st.session_state["dic_meta"]["index"]["td_mean"] == pd.Timedelta(minutes=15):
        tit += TIT_15

    st.session_state["fig_days"] = ploplo.line_plot_day_overlay(
        st.session_state["dic_days"], st.session_state["dic_meta"], tit, "fig_days"
    )

    # Pfeile an Maxima
    # fuan.arrows_min_max("fig_days")

    # updates
    st.session_state["fig_days"] = fuan.update(
        st.session_state["fig_days"], st.session_state["dic_meta"]
    )
    st.session_state["fig_days"].update_layout(
        title_text=st.session_state["fig_days"].layout.meta.get("title"),
    )

    st.session_state["fig_days"].update_xaxes(
        tickformat="%H:%M",
        tickformatstops=[
            {"dtickrange": [None, None], "value": "%H:%M"},
        ],
    )


# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@dics.timer()
def plot_figs() -> None:
    """Grafiken darstellen"""

    with st.container():

        st.plotly_chart(
            st.session_state["fig_base"],
            use_container_width=True,
            config=fuan.plotly_config(450),
        )

        if st.session_state.get("cb_jdl") and st.session_state.get("cb_mon"):
            st.markdown("###")

            fig_col1, fig_col2 = st.columns(2)
            with fig_col1:
                st.plotly_chart(
                    st.session_state["fig_jdl"],
                    use_container_width=True,
                    config=fuan.plotly_config(),
                )
                if st.session_state.get("cb_days"):
                    st.markdown("###")
                    st.plotly_chart(
                        st.session_state["fig_days"],
                        use_container_width=True,
                        config=fuan.plotly_config(),
                    )

            with fig_col2:
                st.plotly_chart(
                    st.session_state["fig_mon"],
                    use_container_width=True,
                    config=fuan.plotly_config(),
                )

        elif st.session_state.get("cb_jdl") and not st.session_state.get("cb_mon"):
            st.markdown("###")

            st.plotly_chart(
                st.session_state["fig_jdl"],
                use_container_width=True,
                config=fuan.plotly_config(),
            )
            if st.session_state.get("cb_days"):
                st.markdown("###")
                st.plotly_chart(
                    st.session_state["fig_days"],
                    use_container_width=True,
                    config=fuan.plotly_config(),
                )

        elif st.session_state.get("cb_mon") and not st.session_state.get("cb_jdl"):
            st.markdown("###")

            st.plotly_chart(
                st.session_state["fig_mon"],
                use_container_width=True,
                config=fuan.plotly_config(),
            )
            if st.session_state.get("cb_days"):
                st.markdown("###")
                st.plotly_chart(
                    st.session_state["fig_days"],
                    use_container_width=True,
                    config=fuan.plotly_config(),
                )
