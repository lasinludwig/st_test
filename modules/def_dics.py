"""
Definitions and Dictionaries
"""

import base64
import datetime
import os
import time
from collections import Counter
from typing import Any

import streamlit as st
from github import Github
from pytz import timezone


# timer decorator
def timer() -> None:
    """function-timer for debugging"""

    def decorator(func: Any) -> Any:
        def wrapper(*args, **kwargs) -> None:
            start_time = time.perf_counter()
            if "dic_exe_time" not in st.session_state:
                st.session_state["dic_exe_time"] = {}
            result = func(*args, **kwargs)
            st.session_state["dic_exe_time"][func.__name__] = (
                time.perf_counter() - start_time
            )
            return result

        return wrapper

    return decorator


@timer()
def del_session_state_entry(key: str) -> None:
    """Eintrag in st.session_state löschen"""
    if key in st.session_state:
        del st.session_state[key]


# latest_commit
@timer()
def get_com_date() -> None:
    """commit message and date from GitHub"""
    utc = timezone("UTC")
    eur = timezone("Europe/Berlin")
    date_now = datetime.datetime.now()
    tz_diff = (
        utc.localize(date_now) - eur.localize(date_now).astimezone(utc)
    ).seconds / 3600

    # pat= personal access token - in github
    # click on your profile and go into
    # settings -> developer settings -> personal access tokens
    pat = os.getenv("GITHUB_PAT")
    gith = Github(pat)
    repo = gith.get_user().get_repo("grafische_Datenauswertung")
    branch = repo.get_branch("master")
    sha = branch.commit.sha
    commit = repo.get_commit(sha).commit
    st.session_state["com_date"] = commit.author.date + datetime.timedelta(
        hours=tz_diff
    )
    st.session_state["com_msg"] = commit.message.split("\n")[-1]


# svg in streamlit app darstellen (z.B. UTEC-Logo)
@timer()
def render_svg(svg_path: str = "logo/UTEC_logo_text.svg") -> str:
    """Renders the given svg string."""
    # lines = open(svg_path).readlines()
    with open(svg_path) as lines:
        svg = "".join(lines.readlines())
        b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'


# Einheiten
# @st.experimental_memo(suppress_st_warning=True, show_spinner=False)
@timer()
def units() -> None:
    """Einheiten der Daten"""
    # Einheiten für y-Achse(n)
    all_units = st.session_state["all_units"] = [
        st.session_state["dic_meta"][x].get("unit_graph")
        for x in st.session_state["dic_meta"]
        if st.session_state["dic_meta"][x].get("unit_graph")
    ]

    st.session_state["dic_meta"]["units"] = {
        "all": all_units,
        "set": sorted(Counter(all_units), key=Counter(all_units).get, reverse=True),
    }

    for k_1 in [
        k_2
        for k_2 in st.session_state["dic_meta"]
        if st.session_state["dic_meta"][k_2].get("unit_graph")
    ]:
        ind = st.session_state["dic_meta"]["units"]["set"].index(
            st.session_state["dic_meta"][k_1].get("unit_graph")
        )

        st.session_state["dic_meta"][k_1]["y_axis"] = (
            f"y{str(ind + 1)}" if ind > 0 else "y"
        )


# def allg(files):
#     from modules import run_allgemein as allg
#     allg.main(files)
@timer()
def nachkomma(value: float) -> str:
    """Nachkommastellen je nach Ziffern in Zahl"""
    if abs(value) >= 1000:
        return str(f"{value:,.0f}").replace(",", ".")
    if abs(value) >= 100:
        return str(f"{value:,.0f}").replace(".", ",")
    if abs(value) >= 10:
        return str(f"{value:,.1f}").replace(".", ",")

    return str(f"{value:,.2f}").replace(".", ",")


# negative Werte für Lieferung
LIS_NEG: list = [
    "Lieferung",
    "Einspeisung",
    "Netzeinspeisung",
]


# allgemeine Liste von Einheiten
LIS_UNITS: list = [
    "W",
    "kW",
    "MW",
    "Wh",
    "kWh",
    "MWh",
    "Wh/a",
    "kWh/a",
    "MWh/a",
    "g",
    "kg",
    "Mg",
    "t",
]

# Einheiten, bei denen der Mittelwert gebildet werden muss (statt Summe)
GRP_MEAN: list = [
    " °c",
    " °C",
    " w",
    " W",
    " kw",
    " kW",
    " KW",
    " mw",
    " mW",
    " MW",
    " m³",
    " m³/h",
    " pa/m",
    " Pa/m",
    " m/s",
]

PAGES: dict = {
    "login": {
        "page_tit": "UTEC Online Tools",
    },
    "graph": {
        "page_tit": "Grafische Datenauswertung",
    },
    "meteo": {
        "page_tit": "Meteorologische Daten",
    },
}


# Transparenz (Deckungsgrad) 0= durchsichtig, 1= undurchsichtig
ALPHA: dict = {
    "bg": ", 0.5)",  # Hintergrund Beschriftungen
    "fill": ", 0.2)",  # fill von Linien etc.
}


FARBEN: dict = {
    "weiß": "255, 255, 255",
    "schwarz": "0, 0, 0",
    "hellgrau": "200, 200, 200",
    "blau": "99, 110, 250",
    "rot": "239, 85, 59",
    "grün-blau": "0, 204, 150",
    "lila": "171, 99, 250",
    "orange": "255, 161, 90",
    "hellblau": "25, 211, 243",
    "rosa": "255, 102, 146",
    "hellgrün": "182, 232, 128",
    "pink": "255, 151, 255",
    "gelb": "254, 203, 82",
}

PLOTFARBE: dict = {
    "Ost-West": FARBEN["hellgrün"],
    "Süd": FARBEN["gelb"],
    "Bedarf": FARBEN["blau"],
    "Produktion": FARBEN["hellblau"],
    "Eigenverbrauch": FARBEN["rot"],
    "Netzbezug": FARBEN["lila"],
}


# obis Elektrizität (Medium == 1)
OBIS_PATTERN_EL: str = "*1-*:*.*"

DIC_OBIS_EL_KEY: dict = {
    "Medium": {"1": "Elektrizität"},
    "Messgröße": {
        "1": {"bez": "Wirkleistung (+)", "unit": "kWh", "alt_bez": "Bezug"},
        "2": {"bez": "Wirkleistung (-)", "unit": "kWh", "alt_bez": "Lieferung"},
        "3": {"bez": "Blindenergie (+)", "unit": "kvarh", "alt_bez": "Blinden. Bezug"},
        "4": {
            "bez": "Blindenergie (-)",
            "unit": "kvarh",
            "alt_bez": "Blinden. Lieferung",
        },
        "5": {"bez": "Blindenergie QI", "unit": "kvarh", "alt_bez": "Blinden. QI"},
        "6": {"bez": "Blindenergie QII", "unit": "kvarh", "alt_bez": "Blinden. QII"},
        "7": {"bez": "Blindenergie QIII", "unit": "kvarh", "alt_bez": "Blinden. QIII"},
        "8": {"bez": "Blindenergie QIV", "unit": "kvarh", "alt_bez": "Blinden. QIV"},
        "9": {"bez": "Scheinenergie (+)", "unit": "kVA", "alt_bez": "Scheinen. Bezug"},
        "10": {
            "bez": "Scheinenergie (-)",
            "unit": "kVA",
            "alt_bez": "Scheinen. Lieferung",
        },
        "11": {"bez": "Strom", "unit": "A", "alt_bez": "Strom"},
        "12": {"bez": "Spannung", "unit": "V", "alt_bez": "Spannung"},
        "13": {
            "bez": "Leistungsfaktor Durchschnitt",
            "unit": "-",
            "alt_bez": "P-Faktor",
        },
        "14": {"bez": "Frequenz", "unit": "Hz", "alt_bez": "Frequenz"},
        "15": {
            "bez": "Wirkenergie QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "Wirken. QI+QII+QIII+QIV",
        },
        "16": {
            "bez": "Wirkenergie QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "Wirken. QI+QII+QIII+QIV",
        },
        "17": {"bez": "Wirkenergie QI", "unit": "kWh", "alt_bez": "Wirken. QI"},
        "18": {"bez": "Wirkenergie QII", "unit": "kWh", "alt_bez": "Wirken. QII"},
        "19": {"bez": "Wirkenergie QIII", "unit": "kWh", "alt_bez": "Wirken. QIII"},
        "20": {"bez": "Wirkenergie QIV", "unit": "kWh", "alt_bez": "Wirken. QIV"},
        "21": {"bez": "Wirkenergie L1 (+)", "unit": "kWh", "alt_bez": "L1 Bezug"},
        "22": {"bez": "Wirkenergie L1 (-)", "unit": "kWh", "alt_bez": "L1 Lieferung"},
        "23": {
            "bez": "Blindenergie L1 (+)",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. Bezug",
        },
        "24": {
            "bez": "Blindenergie L1 (-)",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. Lieferung",
        },
        "25": {
            "bez": "Blindenergie L1 QI",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QI",
        },
        "26": {
            "bez": "Blindenergie L1 QII",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QII",
        },
        "27": {
            "bez": "Blindenergie L1 QIII",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QIII",
        },
        "28": {
            "bez": "Blindenergie L1 QIV",
            "unit": "kvarh",
            "alt_bez": "L1 Blinden. QIV",
        },
        "29": {
            "bez": "Scheinenergie L1 (+)",
            "unit": "kVA",
            "alt_bez": "L1 Scheinen. Bezug",
        },
        "30": {
            "bez": "Scheinenergie L1 (-)",
            "unit": "kVA",
            "alt_bez": "L1 Scheinen. Lieferung",
        },
        "31": {"bez": "I L1", "unit": "A", "alt_bez": "L1 Strom"},
        "32": {"bez": "U PH-N L1", "unit": "V", "alt_bez": "L1 Spannung"},
        "33": {"bez": "Leistungsfaktor L1", "unit": "-", "alt_bez": "L1 P-Faktor"},
        "34": {"bez": "Frequenz L1", "unit": "Hz", "alt_bez": "L1 Frequenz"},
        "35": {
            "bez": "Wirkenergie L1 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L1 Wirken. QI+QII+QIII+QIV",
        },
        "36": {
            "bez": "Wirkenergie L1 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L1 Wirken. QI+QII+QIII+QIV",
        },
        "37": {"bez": "Wirkenergie L1 QI", "unit": "kWh", "alt_bez": "L1 Wirken. QI"},
        "38": {"bez": "Wirkenergie L1 QII", "unit": "kWh", "alt_bez": "L1 Wirken. QII"},
        "39": {
            "bez": "Wirkenergie L1 QIII",
            "unit": "kWh",
            "alt_bez": "L1 Wirken. QIII",
        },
        "40": {"bez": "Wirkenergie L1 QIV", "unit": "kWh", "alt_bez": "L1 Wirken. QIV"},
        "41": {"bez": "Wirkenergie L2 (+)", "unit": "kWh", "alt_bez": "L2 Bezug"},
        "42": {"bez": "Wirkenergie L2 (-)", "unit": "kWh", "alt_bez": "L2 Lieferung"},
        "43": {
            "bez": "Blindenergie L2 (+)",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. Bezug",
        },
        "44": {
            "bez": "Blindenergie L2 (-)",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. Lieferung",
        },
        "45": {
            "bez": "Blindenergie L2 QI",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QI",
        },
        "46": {
            "bez": "Blindenergie L2 QII",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QII",
        },
        "47": {
            "bez": "Blindenergie L2 QIII",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QIII",
        },
        "48": {
            "bez": "Blindenergie L2 QIV",
            "unit": "kvarh",
            "alt_bez": "L2 Blinden. QIV",
        },
        "49": {
            "bez": "Scheinenergie L2 (+)",
            "unit": "kVA",
            "alt_bez": "L2 Scheinen. Bezug",
        },
        "50": {
            "bez": "Scheinenergie L2 (-)",
            "unit": "kVA",
            "alt_bez": "L2 Scheinen. Lieferung",
        },
        "51": {"bez": "I L2", "unit": "A", "alt_bez": "L2 Strom"},
        "52": {"bez": "U PH-N L2", "unit": "V", "alt_bez": "L2 Spannung"},
        "53": {"bez": "Leistungsfaktor L2", "unit": "-", "alt_bez": "L2 P-Faktor"},
        "54": {"bez": "Frequenz L2", "unit": "Hz", "alt_bez": "L2 Frequenz"},
        "55": {
            "bez": "Wirkenergie L2 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L2 Wirken. QI+QII+QIII+QIV",
        },
        "56": {
            "bez": "Wirkenergie L2 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L2 Wirken. QI+QII+QIII+QIV",
        },
        "57": {"bez": "Wirkenergie L2 QI", "unit": "kWh", "alt_bez": "L2 Wirken. QI"},
        "58": {"bez": "Wirkenergie L2 QII", "unit": "kWh", "alt_bez": "L2 Wirken. QII"},
        "59": {
            "bez": "Wirkenergie L2 QIII",
            "unit": "kWh",
            "alt_bez": "L2 Wirken. QIII",
        },
        "60": {"bez": "Wirkenergie L2 QIV", "unit": "kWh", "alt_bez": "L2 Wirken. QIV"},
        "61": {"bez": "Wirkenergie L3 (+)", "unit": "kWh", "alt_bez": "L3 Bezug"},
        "62": {"bez": "Wirkenergie L3 (-)", "unit": "kWh", "alt_bez": "L3 Lieferung"},
        "63": {
            "bez": "Blindenergie L3 (+)",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. Bezug",
        },
        "64": {
            "bez": "Blindenergie L3 (-)",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. Lieferung",
        },
        "65": {
            "bez": "Blindenergie L3 QI",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QI",
        },
        "66": {
            "bez": "Blindenergie L3 QII",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QII",
        },
        "67": {
            "bez": "Blindenergie L3 QIII",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QIII",
        },
        "68": {
            "bez": "Blindenergie L3 QIV",
            "unit": "kvarh",
            "alt_bez": "L3 Blinden. QIV",
        },
        "69": {
            "bez": "Scheinenergie L3 (+)",
            "unit": "kVA",
            "alt_bez": "L3 Scheinen. Bezug",
        },
        "70": {
            "bez": "Scheinenergie L3 (-)",
            "unit": "kVA",
            "alt_bez": "L3 Scheinen. Lieferung",
        },
        "71": {"bez": "I L3", "unit": "A", "alt_bez": "L3 Strom"},
        "72": {"bez": "U PH-N L3", "unit": "V", "alt_bez": "L3 Spannung"},
        "73": {"bez": "Leistungsfaktor L3", "unit": "-", "alt_bez": "L3 P-Faktor"},
        "74": {"bez": "Frequenz L3", "unit": "Hz", "alt_bez": "L3 Frequenz"},
        "75": {
            "bez": "Wirkenergie L3 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L3 Wirken. QI+QII+QIII+QIV",
        },
        "76": {
            "bez": "Wirkenergie L3 QI+QII+QIII+QIV",
            "unit": "kWh",
            "alt_bez": "L3 Wirken. QI+QII+QIII+QIV",
        },
        "77": {"bez": "Wirkenergie L3 QI", "unit": "kWh", "alt_bez": "L3 Wirken. QI"},
        "78": {"bez": "Wirkenergie L3 QII", "unit": "kWh", "alt_bez": "L3 Wirken. QII"},
        "79": {
            "bez": "Wirkenergie L3 QIII",
            "unit": "kWh",
            "alt_bez": "L3 Wirken. QIII",
        },
        "80": {"bez": "Wirkenergie L3 QIV", "unit": "kWh", "alt_bez": "L3 Wirken. QIV"},
        "81": {"bez": "Phasenwinkel", "unit": "-", "alt_bez": "Phasenwinkel"},
        "82": {
            "bez": "Einheitslose Mengen (z.B. Impulse)",
            "unit": "-",
            "alt_bez": "Einheitslose Mengen",
        },
        "91": {"bez": "I Neutralleiter", "unit": "A", "alt_bez": "N Strom"},
        "92": {"bez": "U Neutralleiter", "unit": "V", "alt_bez": "N Spannung"},
    },
    "Messart": {
        "0": {
            "bez": "Mittelwert Abrechnungsperiode (seit letztem Reset)",
            "alt_bez": "Mittel",
        },
        "1": {"bez": "Kumulativ Minimum 1", "alt_bez": "min"},
        "2": {"bez": "Kumulativ Maximum 1", "alt_bez": "max"},
        "3": {"bez": "Minimum 1", "alt_bez": "min"},
        "4": {"bez": "Aktueller Mittelwert 1", "alt_bez": "Mittel"},
        "5": {"bez": "Letzter Mittelwert 1", "alt_bez": "Mittel"},
        "6": {"bez": "Maximum 1", "alt_bez": "max"},
        "7": {"bez": "Momentanwert", "alt_bez": "Momentanwert"},
        "8": {"bez": "Zeit Integral 1 - Zählerstand", "alt_bez": "Zählerstand"},
        "9": {"bez": "Zeit Integral 2 – Verbrauch / Vorschub", "alt_bez": "Verbrauch"},
        "10": {"bez": "Zeit Integral 3", "alt_bez": "Integral"},
        "11": {"bez": "Kumulativ Minimum 2", "alt_bez": "min"},
        "12": {"bez": "Kumulativ Maximum 2", "alt_bez": "max"},
        "13": {"bez": "Minimum 2", "alt_bez": "min"},
        "14": {"bez": "Aktueller Mittelwert 2", "alt_bez": "Mittel"},
        "15": {"bez": "Letzter Mittelwert 2", "alt_bez": "Mittel"},
        "16": {"bez": "Maximum 2", "alt_bez": "max"},
        "17": {"bez": "Momentanwert 2", "alt_bez": "Momentanwert"},
        "18": {"bez": "Zeit Integral 2 1 - Zählerstand", "alt_bez": "Zählerstand"},
        "19": {
            "bez": "Zeit Integral 2 2 – Verbrauch / Vorschub",
            "alt_bez": "Verbrauch",
        },
        "20": {"bez": "Zeit Integral 3 2", "alt_bez": "Integral"},
        "21": {"bez": "Kumulativ Minimum 3", "alt_bez": "min"},
        "22": {"bez": "Kumulativ Maximum 3", "alt_bez": "max"},
        "23": {"bez": "Minimum 3", "alt_bez": "min"},
        "24": {"bez": "Aktueller Mittelwert 3", "alt_bez": "Mittel"},
        "25": {"bez": "Letzter Mittelwert 3", "alt_bez": "Mittel"},
        "26": {"bez": "Maximum 3", "alt_bez": "max"},
        "27": {"bez": "Aktueller Mittelwert 5", "alt_bez": "Mittel"},
        "28": {"bez": "Aktueller Mittelwert 6", "alt_bez": "Mittel"},
        "29": {
            "bez": "Zeit Integral 5 – Lastprofil Aufzeichnungsperiode 1",
            "alt_bez": "Lastprofil",
        },
        "30": {
            "bez": "Zeit Integral 6 – Lastprofil Aufzeichnungsperiode 2",
            "alt_bez": "Lastprofil",
        },
        "31": {"bez": "Untere Grenzwertschwelle", "alt_bez": "Grenzwertschwelle u"},
        "32": {
            "bez": "Unterer Grenzwert Ereigniszähler",
            "alt_bez": "Grenzwert Zähler u",
        },
        "33": {"bez": "Unterer Grenzwert Dauer", "alt_bez": "Grenzwert Dauer u"},
        "34": {"bez": "Unterer Grenzwert Größe", "alt_bez": "Grenzwert Größe u"},
        "35": {"bez": "Oberer Grenzwertschwelle", "alt_bez": "Grenzwertschwelle o"},
        "36": {
            "bez": "Oberer Grenzwert Ereigniszähler",
            "alt_bez": "Grenzwert Zähler o",
        },
        "37": {"bez": "Oberer Grenzwert Dauer", "alt_bez": "Grenzwert Dauer o"},
        "38": {"bez": "Oberer Grenzwert Größe", "alt_bez": "Grenzwert Größe o"},
        "58": {
            "bez": "Zeit Integral 4 – Test Zeit Integral",
            "alt_bez": "Test Zeit Integral",
        },
        "131": {"bez": "Schichtwert", "alt_bez": "Schichtwert"},
        "132": {"bez": "Tageswert", "alt_bez": "Tageswert"},
        "133": {"bez": "Wochenwert", "alt_bez": "Wochenwert"},
        "134": {"bez": "Monatswert", "alt_bez": "Monatswert"},
        "135": {"bez": "Quartalswert", "alt_bez": "Quartalswert"},
        "136": {"bez": "Jahreswert", "alt_bez": "Jahreswert"},
    },
}


@timer()
def trans_obis(code: str) -> dict:
    """Parameter Name und Einheit aus obis-code"""
    dic_obis = {"name": code, "name_lang": code, "unit": ""}
    code_r = code.replace(":", "-").replace(".", "-").replace("~*", "-")
    lis_code = code_r.split("-")
    code_medium = lis_code[0] if lis_code else None
    code_messgr = lis_code[2] if len(lis_code) >= 3 else None
    code_messart = lis_code[3] if len(lis_code) >= 4 else None

    if code_medium == "1" and code_messgr:
        dic_obis["name_kurz"] = DIC_OBIS_EL_KEY["Messgröße"][code_messgr]["alt_bez"]
        dic_obis["name"] = (
            DIC_OBIS_EL_KEY["Messgröße"][code_messgr]["alt_bez"] + " (" + code + ")"
        )
        dic_obis["name_lang"] = (
            DIC_OBIS_EL_KEY["Messgröße"][code_messgr]["bez"]
            + " ["
            + DIC_OBIS_EL_KEY["Messgröße"][code_messgr]["unit"]
            + "] - "
            + DIC_OBIS_EL_KEY["Messart"][code_messart]["bez"]
            + " ("
            + code
            + ")"
        )
        dic_obis["unit"] = DIC_OBIS_EL_KEY["Messgröße"][code_messgr]["unit"]

    return dic_obis
