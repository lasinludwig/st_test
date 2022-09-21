"""
Seite Grafische Datenauswertung
"""

import locale

import streamlit as st

from modules import def_dics as dics
from modules import df_manip as dfm
from modules import excel as ex
from modules import fig_update_anno as fuan
from modules import figs
from modules import global_variables as gv
from modules import meteorolog as meteo
from modules import streamlit_menus as sm
from modules import user_authentication as uauth

locale.setlocale(locale.LC_ALL, "")

# setup
MANUAL_DEBUG = True
PAGE = st.session_state["page"] = "graph"
sm.page_setup(PAGE)


def debug_show(var: str) -> None:  # sourcery skip: flag_streamlit_show
    """Anzeige mit st.experimental_show() für Debugging"""
    return st.experimental_show(var)


if uauth.authentication(PAGE):

    # debug
    if (
        MANUAL_DEBUG
        and not isinstance(st.session_state.get("access_lvl"), list)
        and st.session_state.get("access_lvl") in ("god")
    ):
        with st.expander("Debug before", False):

            st.plotly_chart(
                figs.ploplo.timings(st.session_state["dic_exe_time"]),
                use_container_width=True,
                config=fuan.plotly_config(),
            )

            if "dic_meta" in st.session_state:
                debug_show(st.session_state["dic_meta"])

            debug_show(st.session_state)

        st.markdown("###")
        st.markdown("---")

    st.session_state["dic_exe_time"] = {}

    # sidebar - Datei Down-/Upload
    sm.sidebar_file_upload()

    if st.session_state.get("f_up") is not None:

        if any(x not in st.session_state for x in ("df", "dic_meta")):
            with st.spinner("Momentle bitte - Datei wird gelesen..."):

                # Excel-Datei importieren
                ex.import_prefab_excel(st.session_state["f_up"])

                # Einheiten
                if "all_units" not in st.session_state:
                    dics.units()

        # Grundeinstellungen in der sidebar
        sm.base_settings()
        if st.session_state.get("but_base_settings"):
            for entry in ("fig_base", "df_h"):
                dics.del_session_state_entry(entry)

        # anzuzeigende Grafiken
        sm.select_graphs()

        # Außentemperatur
        with st.sidebar:
            with st.expander("Außentemperatur", False):
                sm.meteo_sidebar("graph")

        if st.session_state.get("but_meteo_sidebar"):
            if st.session_state.get("cb_temp"):
                meteo.outside_temp_graph()
            else:
                meteo.del_meteo()

        # df mit Stundenwerten erzeugen
        if st.session_state.get("cb_h") and "df_h" not in st.session_state:
            with st.spinner("Momentle bitte - Stundenwerte werden erzeugt..."):
                st.session_state["df_h"] = dfm.h_from_other(
                    st.session_state["df"], st.session_state["dic_meta"]
                )

        # df für Tagesvergleich
        if st.session_state.get("but_select_graphs") and st.session_state.get(
            "cb_days"
        ):
            if st.session_state.get("cb_h"):
                dfm.dic_days(st.session_state["df_h"])
            else:
                dfm.dic_days(st.session_state["df"])

        # einzelnes Jahr
        if (
            len(st.session_state["lis_years"]) == 1
            or st.session_state.get("cb_multi_year") is False
        ):
            # df geordnete Jahresdauerlinie
            if st.session_state.get("cb_jdl") and "df_jdl" not in st.session_state:
                with st.spinner("Momentle bitte - Jahresdauerlinie wird erzeugt..."):
                    if "df_h" not in st.session_state:
                        st.session_state["df_h"] = dfm.h_from_other(
                            st.session_state["df"], st.session_state["dic_meta"]
                        )

                    dfm.jdl(st.session_state["df_h"])

            # df Monatswerte
            if st.session_state.get("cb_mon") and "df_mon" not in st.session_state:
                with st.spinner("Momentle bitte - Monatswerte werden erzeugt..."):
                    dfm.mon(st.session_state["df"], st.session_state["dic_meta"])

        # mehrere Jahre übereinander
        else:
            with st.spinner("Momentle bitte - Werte werden auf Jahre aufgeteilt..."):
                if "dic_df_multi" not in st.session_state:
                    dfm.df_multi_y(
                        st.session_state["df_h"]
                        if st.session_state.get("cb_h")
                        else st.session_state["df"]
                    )

        # --- Grafiken erzeugen ---
        # Grund-Grafik
        st.session_state["lis_figs"] = ["fig_base"]
        if "fig_base" not in st.session_state:
            with st.spinner('Momentle bitte - Grafik "Lastgang" wird erzeugt...'):
                figs.cr_fig_base()

        # Jahresdauerlinie
        if st.session_state.get("cb_jdl"):
            st.session_state["lis_figs"].append("fig_jdl")
            if "fig_jdl" not in st.session_state:
                with st.spinner(
                    'Momentle bitte - Grafik "Jahresdauerlinie" wird erzeugt...'
                ):
                    figs.cr_fig_jdl()

        # Monatswerte
        if st.session_state.get("cb_mon"):
            st.session_state["lis_figs"].append("fig_mon")
            if "fig_mon" not in st.session_state:
                with st.spinner(
                    'Momentle bitte - Grafik "Monatswerte" wird erzeugt...'
                ):
                    figs.cr_fig_mon()

        # Tagesvergleich
        if st.session_state.get("cb_days"):
            st.session_state["lis_figs"].append("fig_days")
            if st.session_state.get("but_select_graphs"):
                with st.spinner(
                    'Momentle bitte - Grafik "Tagesvergleich" wird erzeugt...'
                ):
                    figs.cr_fig_days()

        # horizontale / vertikale Linien
        sm.h_v_lines()
        if st.session_state.get("but_h_v_lines"):
            fuan.h_v_lines()

        # Ausreißerbereinigung
        sm.clean_outliers()
        if st.session_state.get("but_clean_outliers"):
            fuan.clean_outliers()

        # glatte Linien
        sm.smooth()
        if st.session_state.get("but_smooth") and st.session_state.get("cb_smooth"):
            fuan.smooth()
        if (
            st.session_state.get("but_smooth")
            and st.session_state.get("cb_smooth") is not True
        ):
            dfm.del_smooth()

        tab_grafik, tab_download = st.tabs(["Datenauswertung", "Downloads"])
        with tab_grafik:
            # --- Darstellungsoptionen ---
            with st.spinner("Momentle bitte - Optionen werden erzeugt..."):
                gv.but_upd_main = sm.display_options_main()

            if gv.but_upd_main:
                with st.spinner("Momentle bitte - Grafiken werden aktualisiert..."):
                    fuan.update_vis_main()

            # --- Grafiken zeichnen ---
            # if not any([st.session_state.get("but_html"), st.session_state.get("but_h")]):
            with st.spinner("Momentle bitte - Grafiken werden angezeigt..."):
                figs.plot_figs()

        # --- Downloads ---
        # with st.sidebar:
        with tab_download:
            sm.downloads()

            #     # --- Monatswerte als Tabelle und Data Frame Report ---
            #     st.markdown('---')
            #     st.subheader('Monatswerte als Tabelle')
            #     but_tab_mon= st.button('Monatswerte als Tabelle erzeugen')

            #     # st.subheader('Pandas Profiling Report')
            #     # but_ppr= st.button('Report erzeugen')

            # if but_tab_mon:
            #     cont_tab= st.container()
            #     with cont_tab:
            #         # Monatswerte
            #         st.plotly_chart(
            #             tabs.tab_mon(st.session_state['fig_mon']),
            #             use_container_width= True,
            #         )

            # # if but_ppr:
            #     with st.expander('Pandas Profiling Report'):
            #         st_profile_report(df_rep)

    # debug
    if MANUAL_DEBUG and st.session_state.get("name") in ("Florian"):
        with st.expander("Debug after", False):

            st.plotly_chart(
                figs.ploplo.timings(st.session_state["dic_exe_time"]),
                use_container_width=True,
                config=fuan.plotly_config(),
            )

            if "dic_days" in st.session_state:
                debug_show(st.session_state["dic_days"])

            if "dic_meta" in st.session_state:
                debug_show(st.session_state["dic_meta"])

            debug_show(st.session_state)

        st.markdown("###")
        st.markdown("---")
