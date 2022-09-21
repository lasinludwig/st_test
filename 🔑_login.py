"""
login page
"""

import datetime
import json
import locale

import streamlit as st
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from streamlit_lottie import st_lottie

from modules import def_dics as dics
from modules import global_variables as gv
from modules import streamlit_menus as sm
from modules import user_authentication as uauth

locale.setlocale(locale.LC_ALL, "")

# setup
PAGE = st.session_state["page"] = "login"
sm.page_setup(PAGE)


@dics.timer()
def load_lottie_file(path: str) -> json:
    """Load a Lottie animation by providing a json file"""
    with open(path) as file:
        return json.load(file)


col1, col2 = st.columns(2)

with col1:

    # user authentication
    load_dotenv(".streamlit/secrets.toml")

    if "li_all_users" not in st.session_state:
        st.session_state["li_all_users"] = uauth.list_all_users()
        # users = st.session_state["li_all_users"]

    if "dic_credentials" not in st.session_state:
        st.session_state["dic_credentials"] = {
            "usernames": {
                user["key"]: {
                    "name": user["name"],
                    "email": user["email"],
                    "password": user["password"],
                }
                for user in st.session_state["li_all_users"]
            }
        }

    if "authenticator" not in st.session_state:
        st.session_state["authenticator"] = stauth.Authenticate(
            credentials=st.session_state["dic_credentials"],
            cookie_name="utec_tools",
            key="uauth",
            cookie_expiry_days=30,
        )

    name, authentication_status, username = st.session_state["authenticator"].login(
        "Login", "main"
    )

    if authentication_status:
        gv.users = st.session_state["li_all_users"]
        gv.access_lvl_user = [
            u["access_lvl"]
            for u in gv.users
            if u["key"] == st.session_state.get("username")
        ][0]
        st.session_state["access_lvl"] = gv.access_lvl_user
        if gv.access_lvl_user in ("god", "full"):
            st.session_state["access_pages"] = list(dics.PAGES.keys())
            st.session_state["access_until"] = datetime.date.max
        else:
            st.session_state["access_pages"] = gv.access_lvl_user
            st.session_state["access_until"] = [
                datetime.datetime.strptime(u["access_until"], "%Y-%m-%d").date()
                for u in gv.users
                if u["key"] == st.session_state.get("username")
            ][0]

        if st.session_state.get("username") in ("utec"):

            st.markdown(
                """
                Du bist mit dem allgemeinen UTEC-Account angemeldet.  \n  \n
                Viel Spaß mit den Tools!
                """
            )

        else:
            st.markdown(
                f"""
                Angemeldet als "{st.session_state.get('name')}"
                """
            )

            if st.session_state.get("access_until") < datetime.date.max:
                st.markdown(
                    f"""
                    Mit diesem Account kann auf folgende Module bis zum {st.session_state['access_until']:%d.%m.%Y} zugegriffen werden:
                    """
                )
            else:
                st.markdown(
                    """
                    Mit diesem Account kann auf folgende Module zugegriffen werden:
                    """
                )

            for page in st.session_state["access_pages"]:
                if page != "login":
                    st.markdown(f"- {dics.PAGES[page]['page_tit']}")

        st.markdown("###")
        st.session_state["authenticator"].logout("Logout", "main")

        if not isinstance(gv.access_lvl_user, list) and gv.access_lvl_user in ("god"):
            sm.user_accounts()
            # neuen Benutzer eintragen
            if st.session_state.get("butt_sub_new_user"):
                with st.spinner("Momentle bitte, Benutzer wird hinzugefügt..."):
                    uauth.insert_new_user(
                        st.session_state.get("new_user_user"),
                        st.session_state.get("new_user_name"),
                        st.session_state.get("new_user_email"),
                        st.session_state.get("new_user_pw"),
                        st.session_state.get("new_user_access"),
                        str(st.session_state.get("new_user_until")),
                    )

            # Benutzer löschen
            if st.session_state.get("butt_sub_del_user"):
                uauth.delete_user()

    elif authentication_status is None:
        st.warning("Bitte Benutzernamen und Passwort eingeben")

    elif authentication_status is False:
        st.error("Benutzername oder Passwort falsch")


with col2:
    st_lottie(load_lottie_file("animations/login.json"), height=450, key="lottie_login")
