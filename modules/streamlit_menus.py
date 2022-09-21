"""
UI - Menus
"""

import datetime
import secrets
import sys
from glob import glob
from typing import Any

import pandas as pd
import streamlit as st

from modules import def_dics as dics
from modules import excel as ex
from modules import fig_update_anno as fuan
from modules import meteorolog as meteo
from modules import user_authentication as uauth

# Aussehen der labels (Überschriften)    {font-size:105%; font-weight:bold; font-style:italic; color:blue;}
CSS_LABEL_1 = "{font-size:1rem; font-weight:600}"
CSS_LABEL_2 = "{font-size:0.95rem; font-weight:600;}"

# browser tab
@dics.timer()
def page_setup(page: str) -> None:
    """Seitenkopf"""

    st.set_page_config(
        page_title="UTEC Online Tools", page_icon="logo/UTEC_logo.png", layout="wide"
    )

    st.markdown(
        f"""
            <style>
                div.row-widget.stSelectbox > label {CSS_LABEL_1}
                div.row-widget.stMultiSelect > label {CSS_LABEL_1}
                [data-testid='stFileUploader'] > label {CSS_LABEL_1}
                div.streamlit-expanderHeader {CSS_LABEL_2}
            </style>
        """,
        unsafe_allow_html=True,
    )

    st.session_state["title_container"] = st.container()

    with st.session_state["title_container"]:

        # Logo und Titel
        col1, col2 = st.columns(2)
        with col1:
            st.write(dics.render_svg(), unsafe_allow_html=True)

        # Version info
        with col2:
            if "com_date" not in st.session_state:
                dics.get_com_date()
            st.write(
                f"""
                    <i><span style="line-height: 110%; font-size: 12px; float:right; text-align:right">
                        letzte Änderungen:<br>
                        {st.session_state["com_date"]:%d.%m.%Y}   {st.session_state["com_date"]:%H:%M}<br><br>
                        "{st.session_state["com_msg"]}"
                    </span></i>
                """,
                unsafe_allow_html=True,
            )

            users = uauth.list_all_users()
            god_users = [user["key"] for user in users if user["access_lvl"] == "god"]
            if st.session_state.get("username") in god_users:
                st.write(
                    f"""
                        <i><span style="line-height: 110%; font-size: 12px; float:right; text-align:right">
                            (Python version {sys.version.split()[0]})
                        </span></i>
                    """,
                    unsafe_allow_html=True,
                )

        st.title(dics.PAGES[page]["page_tit"])
        st.markdown("---")


@dics.timer()
def user_accounts() -> None:
    """Benutzerkontensteuerung"""

    st.markdown("###")
    st.markdown("---")

    lis_butt = [
        "butt_add_new_user",
        "butt_del_user",
    ]

    # Knöpfle für neuen Benutzer, Benutzer löschen...
    if not any(st.session_state.get(butt) for butt in lis_butt):
        st.button("Liste aller Konten", "butt_list_all")
        st.button("neuen Benutzer hinzufügen", "butt_add_new_user")
        st.button("Benutzer löschen", "butt_del_user")
        st.button("Benutzerdaten ändern", "butt_change_user", disabled=True)

        st.markdown("---")

    # Menu für neuen Benutzer
    if st.session_state.get("butt_add_new_user"):
        new_user_form()
        st.button("abbrechen")
    st.session_state["butt_sub_new_user"] = st.session_state.get(
        "FormSubmitter:Neuer Benutzer-Knöpfle"
    )

    # Menu zum Löschen von Benutzern
    if st.session_state.get("butt_del_user"):
        delete_user_form()
        st.button("abbrechen")
    st.session_state["butt_sub_del_user"] = st.session_state.get(
        "FormSubmitter:Benutzer löschen-Knöpfle"
    )

    if st.session_state.get("butt_list_all"):
        list_all_accounts()


@dics.timer()
def delete_user_form() -> None:
    """Benutzer löschen"""

    with st.form("Benutzer löschen"):
        st.multiselect(
            label="Benutzer wählen, die gelöscht werden sollen",
            options=[
                f"{user['key']} ({user['name']})"
                for user in uauth.list_all_users()
                if user["key"] not in ("utec", "fl")
            ],
            key="ms_del_user",
        )

        st.markdown("###")
        st.form_submit_button("Knöpfle")


@dics.timer()
def new_user_form() -> None:
    """neuen Benutzer hinzufügen"""
    with st.form("Neuer Benutzer"):

        st.text_input(
            label="Benutzername",
            key="new_user_user",
            help=("Benutzername, wei er für den login benutzt wird - z.B. fl"),
        )
        st.text_input(
            label="Passwort",
            key="new_user_pw",
            help=("...kann ruhig auch etwas 'merkbares' sein."),
            value=secrets.token_urlsafe(8),
        )
        st.date_input(
            label="Benutzung erlaubt bis:",
            key="new_user_until",
            min_value=datetime.date.today(),
            value=datetime.date.today() + datetime.timedelta(weeks=3),
        )

        st.text_input(
            label="Name oder Firma",
            key="new_user_name",
            help=("z.B. Florian"),
        )
        st.multiselect(
            label="Zugriffsrechte",
            key="new_user_access",
            help=("Auswahl der Module, auf die dieser Benutzer zugreifen darf."),
            options=[key for key in dics.PAGES.keys() if key not in ("login")],
            default=[key for key in dics.PAGES.keys() if key not in ("login")],
        )

        st.markdown("###")
        st.form_submit_button("Knöpfle")


@dics.timer()
def list_all_accounts() -> None:
    """Liste aller Benutzerkonten"""
    users = uauth.list_all_users()
    df_users = pd.DataFrame()
    df_users["Benutzername"] = [user["key"] for user in users]
    df_users["Name"] = [user["name"] for user in users]
    df_users["Verfallsdatum"] = [user["access_until"] for user in users]
    df_users["Zugriffsrechte"] = [str(user["access_lvl"]) for user in users]

    st.dataframe(df_users)
    st.button("ok")


# Spaltenüberschriften
@dics.timer()
def text_with_hover(text: str, hovtxt: str) -> None:  # &#xF505; oder   &#9432
    """
    css-hack für Überschrift mit mouse-over-tooltip
    """
    st.markdown("###")
    st.markdown(
        f"""
        <html>
            <body>
                <span style="{CSS_LABEL_1[1:-1]}; float:left; text-align:left;">
                    <div title="{hovtxt}">
                        {text}
                    </div>
            </body>
        </html>
        """,
        unsafe_allow_html=True,
    )


# Datei Down-/Upload
@dics.timer()
def sidebar_file_upload() -> Any:
    """hochgeladene Excel-Datei"""

    with st.sidebar:

        # Download and Upload
        with st.expander(
            "Auszuwertende Daten", expanded=not bool(st.session_state.get("f_up"))
        ):

            # Download
            sb_example = st.selectbox(
                "Beispieldateien",
                options=[
                    x.replace("/", "\\").split("\\")[-1].replace(".xlsx", "")
                    for x in glob("example_files/*.xlsx")
                ],
                help=(
                    """
                    Bitte eine der Beispieldateien (egal welche) herunterladen
                     und mit den zu untersuchenden Daten füllen.
                    """
                ),
            )

            with open("example_files/" + sb_example + ".xlsx", "rb") as exfile:
                st.download_button(
                    label="Beispieldatei herunterladen",
                    data=exfile,
                    file_name=sb_example + ".xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # Upload
            st.markdown("---")
            f_up = st.file_uploader(
                label="Datei hochladen",
                type=["xlsx", "xlsm"],
                accept_multiple_files=False,
                help=(
                    """
                    Das Arbeitsblatt "Daten" in der Datei muss
                     wie eine der Beispieldateien aufgebaut sein.
                    """
                ),
                key="f_up",
            )

    return f_up


@dics.timer()
def base_settings() -> None:
    """Grundeinstellungen (Stundenwerte, JDL, Monatswerte)"""

    if st.session_state["dic_meta"]["index"]["td_mean"] == pd.Timedelta(hours=1):
        st.session_state["cb_h"] = True

    if (
        st.session_state["dic_meta"]["index"]["td_mean"] < pd.Timedelta(hours=1)
        or len(st.session_state["lis_years"]) > 1
    ):
        with st.sidebar:
            with st.form("Grundeinstellungen"):

                if st.session_state["dic_meta"]["index"]["td_mean"] < pd.Timedelta(
                    hours=1
                ):
                    st.checkbox(
                        label="Umrechnung in Stundenwerte",
                        help=(
                            """
                            Die Werte aus der Excel-Tabelle werden in Stundenwerte umgewandelt.  \n
                            _(abhängig von der angebenen Einheit entweder per Summe oder Mittelwert)_
                            """
                        ),
                        value=False,
                        disabled=False,
                        key="cb_h",
                    )

                if len(st.session_state["lis_years"]) > 1:
                    st.checkbox(
                        label="mehrere Jahre übereinander",
                        help=(
                            """
                            Die Werte in der Excel-Tabelle werden in Jahre 
                            gruppiert und übereinander gezeichnet.
                            """
                        ),
                        value=True,
                        key="cb_multi_year",
                        disabled=True,
                    )

                st.session_state["but_base_settings"] = st.form_submit_button("Knöpfle")


@dics.timer()
def select_graphs() -> None:
    """Auswahl der anzuzeigenden Grafiken"""
    with st.sidebar:
        with st.expander("anzuzeigende Grafiken", False):
            with st.form("anzuzeigende Grafiken"):

                st.checkbox(
                    label="geordnete Jahresdauerlinie",
                    help=(
                        """
                        Die Werte aus der Excel-Tabelle werden nach Größe sortiert ausgegeben.  \n
                        _(Werden mehrere Jahre übereinander dargestellt, werden auch hier 
                        die Werte in Jahre gruppiert und übereinander dargestellt.)_
                        """
                    ),
                    value=True,
                    key="cb_jdl",
                )

                st.checkbox(
                    label="Monatswerte",
                    help=(
                        """
                        Aus den gegebenen Werten werden Monatswerte (je nach gegebener Einheit) 
                        entweder durch Aufsummieren oder durch Bilden von Mittelwerten erzeugt 
                        und als Liniengrafik dargestellt.
                        """
                    ),
                    value=True,
                    key="cb_mon",
                )

                st.markdown("###")
                st.markdown("---")

                # Tagesvergleiche
                st.checkbox(
                    label="Tagesvergleich",
                    help=(
                        """
                        Hier können Tage gewählt werden, die übereinander als Liniengrafik dargestellt werden sollen.  \n
                        _(z.B. zum Vergleich eines Wintertags mit einem Sommertag oder Woche - Wochenende, etc.)_
                        """
                    ),
                    value=False,
                    key="cb_days",
                    # disabled=True,
                )

                st.number_input(
                    label="Anzahl der Tage",
                    min_value=2,
                    value=2,
                    format="%i",
                    help=(
                        """
                        Wieveile Tage sollen verglichen werden?  \n
                        _(Wird die Anzahl geändert muss auf "aktualisieren" 
                        geklickt werden um weitere Felder anzuzeigen)_
                        """
                    ),
                    key="ni_days",
                )

                for num in range(int(st.session_state["ni_days"])):
                    st.date_input(
                        label=f"Tag {str(num + 1)}",
                        min_value=st.session_state["df"].index.min(),
                        max_value=st.session_state["df"].index.max(),
                        value=st.session_state["df"].index.min() + pd.DateOffset(num),
                        key=f"day_{str(num)}",
                    )

                st.markdown("---")
                st.markdown("###")

                st.session_state["but_select_graphs"] = st.form_submit_button("Knöpfle")


@dics.timer()
def meteo_sidebar(page: str) -> None:
    """sidebar-Menu zur Außentemperatur"""

    with st.form("Außentemperatur"):

        if page in ("graph"):
            st.checkbox(
                label="anzeigen",
                value=False,
                key="cb_temp",
                help=(
                    """
                    Außentemperaturen  werden 
                    für den unten eingegebenen Ort heruntergeladen 
                    und in den Grafiken angezeigt.
                    """
                ),
            )

        if page in ("meteo"):
            st.number_input(
                label="von (Jahr)",
                format="%i",
                value=2020,
                help=(
                    """
                    Falls nur ein Jahr ausgegeben werden soll, in beide Felder das gleiche Jahr eingeben.
                    """
                ),
                key="meteo_start_year",
            )

            st.number_input(
                label="bis (Jahr)",
                format="%i",
                value=2020,
                key="meteo_end_year",
            )

            st.markdown("###")

        st.text_area(
            label="Adresse",
            value=("Cuxhavener Str. 10  \n20217 Bremen"),
            help=(
                """
                Je genauer, desto besser, 
                aber es reicht auch nur eine Stadt.  \n
                _(Wird oben "anzeigen" ausgewählt und as Knöpfle gedrückt, 
                wird eine Karte eingeblendet, mit der kontrolliert werden kann, 
                ob die richtige Adresse gefunden wurde.)_
                """
            ),
            # placeholder= 'Cuxhavener Str. 10, 20217 Bremen',
            # autocomplete= '',
            key="ti_adr",
        )

        st.markdown("###")
        st.session_state["but_meteo_sidebar"] = st.form_submit_button("Knöpfle")
        st.markdown("###")


@dics.timer()
def meteo_params_main() -> None:
    """Wetterdaten-Menu auf der Hauptseite"""

    cats = meteo.LIS_CAT_UTEC
    all_params = meteo.LIS_PARAMS
    set_params = []
    for par in all_params:
        if par.tit_de not in [param.tit_de for param in set_params]:
            set_params.append(par)

    with st.expander("Datenauswahl", False):
        with st.form("Meteo Datenauswahl"):
            col_cat_1, col_cat_2, col_cat_3, col_cat_4 = st.columns(4)
            li_col = [col_cat_1, col_cat_2, col_cat_3, col_cat_4]
            for cnt, col in enumerate(li_col):
                with col:
                    st.markdown("###")
                    st.markdown(
                        f"""
                        <html>
                            <body>
                                <span style="{CSS_LABEL_1[1:-1]}; float:left; text-align:left;">
                                    <div>{cats[cnt]}</div>
                            </body>
                        </html>
                        """,
                        unsafe_allow_html=True,
                    )

                    for par in set_params:
                        if par.cat_utec == cats[cnt]:
                            st.checkbox(
                                label=par.tit_de,
                                key=f"cb_{par.tit_de}",
                                value=par.default,
                                disabled=True,
                            )

            st.session_state["but_meteo_main"] = st.form_submit_button("Knöpfle")


# Ausreißerbereinigung
@dics.timer()
def clean_outliers() -> None:
    """Menu zur Ausreißerbereinigung"""

    with st.sidebar:
        with st.expander("Ausreißerbereinigung", False):
            with st.form("Ausreißerbereinigung"):

                if "abs_max" not in st.session_state:
                    st.session_state["abs_max"] = float(
                        max(
                            line["y"].max()
                            for line in st.session_state["fig_base"].data
                            if "orgidx" not in line.name
                        )
                    )

                st.number_input(
                    label="Bereinigung von Werten über:",
                    value=st.session_state["abs_max"],
                    format="%.0f",
                    help=(
                        """
                        Ist ein Wert in den Daten höher als der hier eingegebene, 
                        wird dieser Datenpunkt aus der Reihe gelöscht und die Lücke interpoliert.
                        """
                    ),
                    key="ni_outl",
                    disabled=True,
                )

                st.markdown("###")

                st.session_state["but_clean_outliers"] = st.form_submit_button(
                    "Knöpfle"
                )


# geglättete Linien
@dics.timer()
def smooth() -> None:
    """Einstellungen für die geglätteten Linien"""

    with st.sidebar:
        with st.expander("geglättete Linien", False):
            with st.form("geglättete Linien"):
                st.checkbox(
                    label="anzeigen",
                    value=True,
                    key="cb_smooth",
                    help=("Anzeige geglätteter Linien (gleitender Durchschnitt)"),
                )
                st.slider(
                    label="Glättung",
                    min_value=1,
                    max_value=st.session_state["smooth_max_val"],
                    value=st.session_state["smooth_start_val"],
                    format="%i",
                    step=2,
                    help=(
                        """
                        Je niedriger die Zahl, 
                        desto weniger wird die Ursprungskurve geglättet.
                        """
                    ),
                    key="gl_win",
                )

                st.number_input(
                    label="Polynom",
                    value=3,
                    format="%i",
                    help=(
                        """
                        Grad der polinomischen Linie  \n
                        _(normalerweise passen 2 oder 3 ganz gut)_
                        """
                    ),
                    key="gl_deg",
                )

                st.markdown("###")

                st.session_state["but_smooth"] = st.form_submit_button("Knöpfle")


# horizontale und vertikale Linien
@dics.timer()
def h_v_lines() -> None:
    """Menu für horizontale und vertikale Linien"""

    with st.sidebar:
        with st.expander("horizontale / vertikale Linien", False):
            with st.form("horizontale / vertikale Linien"):
                st.markdown("__horizontale Linie einfügen__")

                st.text_input(label="Bezeichnung", value="", key="ti_hor")

                st.number_input(
                    value=0.0,
                    label="y-Wert",
                    format="%f",
                    help=(
                        """
                        Bei diesem Wert wird eine horizontale Linie eingezeichnet.  \n
                        _(Zum Löschen einfach "0" eingeben und Knöpfle drücken.)_
                        """
                    ),
                    key="ni_hor",
                    step=1.0,
                )

                # st.multiselect(
                #     label= 'ausfüllen',
                #     options= [
                #         line.name for line in fig_base.data
                #         if len(line.x) > 0 and
                #         not any([ex in line.name for ex in fuan.exclude])
                #     ],
                #     help=(
                #         'Diese Linie(n) wird (werden) zwischen X-Achse und hozizontaler Linie ausgefüllt.'
                #     ),
                #     key= 'ms_fil'
                # )

                st.checkbox(
                    label="gestrichelt",
                    help=("Soll die horizontale Linie gestrichelt sein?"),
                    value=True,
                    key="cb_hor_dash",
                )

                st.markdown("###")

                st.session_state["but_h_v_lines"] = st.form_submit_button("Knöpfle")


# Darstellungsoptionen für Linien auf Hauptseite
@dics.timer()
def display_options_main() -> bool:
    """Hauptmenu für die Darstellungsoptionen (Linienfarben, Füllung, etc.)"""

    with st.expander("Anzeigeoptionen", False):

        with st.form("Anzeigeoptionen"):

            # columns
            col_vis_1, col_vis_2, col_fill, col_anno = st.columns(4)

            # change color picker
            st.markdown(
                """
                <style>
                    div.css-1me30nu {           
                        gap: 0.5rem;
                    }
                    div.css-96rroi {
                        display: flex; 
                        flex-direction: row-reverse; 
                        align-items: center; 
                        justify-content: flex-end; 
                        line-height: 1.6; 
                    }
                    div.css-96rroi > label {
                        margin-bottom: 0px;
                        padding-left: 8px;
                        font-size: 1rem; 
                    } 
                    div.css-96rroi > div {
                        height: 20px;
                        width: 20px;
                        vertical-align: middle;
                    } 
                    div.css-96rroi > div > div {
                        height: 20px;
                        width: 20px;
                        padding: 0px;
                        vertical-align: middle;
                    } 
                </style>   
                """,
                unsafe_allow_html=True,
            )

            # Überschriften
            with col_vis_1:
                text_with_hover("Anzeigen", "Linien, die angezeigt werden sollen")
            with col_vis_2:
                text_with_hover("Farbe", "Linienfarbe wählen")
            with col_fill:
                text_with_hover(
                    "Füllen", "Linien, die zur x-Achse ausgefüllt werden sollen"
                )
            with col_anno:
                text_with_hover("Maximum", "Maxima als Anmerkung mit Pfeil")

            # Check Boxes for line visibility, fill and color
            for line in st.session_state["fig_base"].data:
                l_n = line.name
                l_c = line.line.color
                if (
                    len(line.x) > 0
                    and "hline" not in l_n
                    and l_n is not None
                    and l_c is not None
                ):
                    with col_vis_1:
                        st.checkbox(label=l_n, value=True, key="cb_vis_" + l_n)
                    with col_vis_2:
                        st.color_picker(
                            label=l_n,
                            value=l_c,
                            key="cp_" + l_n,
                        )

                    with col_fill:
                        st.checkbox(label=l_n, value=False, key="cb_fill_" + l_n)

            # Check Boxes for annotations
            for anno in [
                anno.name
                for anno in st.session_state["fig_base"].layout.annotations
                if "hline" not in anno.name
            ]:
                with col_anno:
                    st.checkbox(label=anno, value=False, key="cb_anno_" + anno)

            st.markdown("###")
            but_upd_main = st.form_submit_button("Knöpfle")

    st.markdown("###")

    return but_upd_main


# Downloads
@dics.timer()
def downloads(page: str = "graph") -> None:
    """Dateidownloads"""
    if "meteo" in page:
        if st.session_state["meteo_start_year"] == st.session_state["meteo_end_year"]:
            xl_file_name = f"Wetterdaten {st.session_state['meteo_start_year']}.xlsx"
        else:
            start = min(
                st.session_state["meteo_start_year"], st.session_state["meteo_end_year"]
            )
            end = max(
                st.session_state["meteo_start_year"], st.session_state["meteo_end_year"]
            )
            xl_file_name = f"Wetterdaten {start}-{end}.xlsx"
    else:
        xl_file_name = "Datenausgabe.xlsx"

    if "graph" in page and not any(
        [st.session_state.get("but_html"), st.session_state.get("but_xls")]
    ):

        st.markdown("###")
        # st.subheader("Downloads")

        # html-Datei
        st.button(
            label="html-Datei erzeugen",
            key="but_html",
            help="Nach dem Erzeugen der html-Datei erscheint ein Knöpfle zum herunterladen.",
        )

        # Excel-Datei
        st.button(
            "Excel-Datei erzeugen",
            key="but_xls",
            help="Nach dem Erzeugen der Excel-Datei erscheint ein Knöpfle zum herunterladen.",
        )

    if st.session_state.get("but_html"):
        with st.spinner("Momentle bitte - html-Datei wird erzeugt..."):
            fuan.html_exp()

        col1, dl_butt_col, col3 = st.columns(3)

        with dl_butt_col:
            f_pn = "export/interaktive_grafische_Auswertung.html"
            with open(f_pn, "rb") as exfile:
                st.download_button(
                    label="html-Datei herunterladen",
                    data=exfile,
                    file_name=f_pn.rsplit("/", maxsplit=1)[-1],
                    mime="application/xhtml+xml",
                )
            st.button("abbrechen")

        with col1:
            st.success("html-Datei hier herunterladen → → →")
        with col3:
            st.success("← ← ← html-Datei hier herunterladen")

        st.markdown("---")

    if any(
        st.session_state.get(key)
        for key in (
            "but_xls",
            "but_meteo_sidebar",
            "but_meteo_main",
            "excel_download",
            "cancel_excel_download",
        )
    ):

        with st.spinner("Momentle bitte - Excel-Datei wird erzeugt..."):
            if page in ("graph"):
                dic_df_ex = {
                    x.name: {
                        "df": pd.DataFrame(data=x.y, index=x.x, columns=[x.name]),
                        "unit": st.session_state["dic_meta"][x.name].get("unit_data"),
                    }
                    for x in [
                        d
                        for d in st.session_state["fig_base"].data
                        if all(e not in d.name for e in fuan.gv.exclude)
                    ]
                }

                df_ex = st.session_state["df_ex"] = pd.concat(
                    [dic_df_ex.get(df).get("df") for df in dic_df_ex], axis=1
                )
            if page in ("meteo"):
                df_ex = st.session_state.get("meteo_data")

            dat = ex.excel_download(df_ex, page)

        col1, dl_butt_col, col3 = st.columns(3)

        with dl_butt_col:
            st.download_button(
                label="Excel-Datei herunterladen",
                data=dat,
                file_name=xl_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="excel_download",
            )

            if "graph" in page:
                st.button("abbrechen", key="cancel_excel_download")

        with col1:
            st.success("Excel-Datei hier herunterladen → → →")
        with col3:
            st.success("← ← ← Excel-Datei hier herunterladen")
