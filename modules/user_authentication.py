"""
user authentication
"""

import datetime
import os
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth
from deta import Deta
from dotenv import load_dotenv

from modules import def_dics as dics
from modules import global_variables as gv

load_dotenv(".streamlit/secrets.toml")
gv.deta_key = os.getenv("DETA_KEY")
gv.deta = Deta(gv.deta_key)
gv.deta_db = gv.deta.Base("UTEC_users")

ERRORS_AND_WARNINGS = {
    "no_access": (
        """
        Mit diesem Benutzerkonto haben Sie keinen Zugriff auf dieses Modul.  \n  \n
        Bitte nehmen Sie Kontakt mit UTEC auf.
        """
    ),
    "no_login": (
        """
        Bitte anmelden! (login auf der linken Seite)
        """
    ),
    "too_late": (
        f"""
        Zugriff war nur bis {st.session_state.get('access_until')} gestattet.  \n  \n
        Bitte nehmen Sie Kontakt mit UTEC auf.
        """
    ),
}

# user authentication
@dics.timer()
def authentication(page: str) -> bool:
    """Authentication object"""

    if not st.session_state.get("authentication_status"):
        st.warning(ERRORS_AND_WARNINGS["no_login"])
        return False
    if page not in st.session_state.get("access_pages"):
        st.error(ERRORS_AND_WARNINGS["no_access"])
        return False
    if st.session_state.get("access_until") < datetime.date.today():
        st.error(ERRORS_AND_WARNINGS["too_late"])
        return False

    return True


@dics.timer()
def insert_new_user(
    username: str,
    name: str,
    email: str,
    password: str,
    access_lvl: str or list,
    access_until: str = str(datetime.date.today() + datetime.timedelta(weeks=3)),
) -> None:

    """
    bei Aufrufen der Funktion, Passwort als Klartext angeben -> wird in hash umgewandelt
    """
    # password muss eine liste sein, deshalb wird hier für einezelnen user das pw in eine Liste geschrieben
    hashed_pw = stauth.Hasher([password]).generate()

    gv.deta_db.put(
        {
            "key": username,  # Benutzername für login
            "name": name,  # Klartext name
            "email": email,  # e-Mail-Adresse
            "password": hashed_pw[0],  # erstes Element aus der Passwort-"Liste"
            "access_lvl": access_lvl,  # "god" | "full" | list of allowed pages e.g. ["graph", "meteo"] ...page options: dics.pages.keys()
            "access_until": access_until,
        }
    )

    st.markdown("###")
    st.info(
        f"""
        Benutzer "{st.session_state.get('new_user_username')}" zur Datenbank hinzugefügt.
        ("{st.session_state.get("new_user_name")}" hat Zugriff bis zum 
        {st.session_state.get("new_user_until"):%d.%m.%Y})  \n
        Achtung: Passwort merken (wird nicht wieder angezeigt):  \n
        __{st.session_state.get('new_user_pw')}__
        """
    )

    st.button("ok", key="insert_ok_butt")


@dics.timer()
def update_user(username: str, updates: dict) -> Any:
    """existierendes Benutzerkonto ändern"""
    return gv.deta_db.update(updates, username)


@dics.timer()
def delete_user(usernames: str = None) -> None:
    """Benutzer löschen"""
    all_users = gv.deta_db.fetch().items

    if (
        usernames is None
        and any(
            admin in st.session_state.get("ms_del_user")
            for admin in ["utec (UTEC Allgemein)", "fl (Florian)"]
        )
        or (usernames is not None and any(user in ["utec", "fl"] for user in usernames))
    ):
        st.warning("Admin-Konten können nicht gelöscht werden!")

    if usernames is not None:
        del_users = [user for user in usernames if user not in ["utec", "fl"]]
    else:
        del_users = [
            user["key"]
            for user in all_users
            if f"{user['key']} ({user['name']})" in st.session_state.get("ms_del_user")
            and user["key"] not in ["utec", "fl"]
        ]

    # del_users = (
    #     [user for user in usernames if user not in ["utec", "fl"]]
    #     if usernames is not None
    #     else [
    #         user["key"]
    #         for user in all_users
    #         if f"{user['key']} ({user['name']})" in st.session_state.get("ms_del_user")
    #         and user["key"] not in ["utec", "fl"]
    #     ]
    # )

    if not del_users:
        st.error("Es wurden keine Benutzerkonten gelöscht.")
    else:
        for user in del_users:
            gv.deta_db.delete(user)

        st.markdown("###")

        if len(del_users) > 1:
            lis_u = f"  \n- {del_users[0]} ({[user['name'] for user in all_users if user['key'] == del_users[0]][0]})"
            for inst in range(1, len(del_users)):
                lis_u += f"  \n- {del_users[inst]} ({[user['name'] for user in all_users if user['key'] == del_users[inst]][0]})"

            st.info(
                f"""
                Folgende Benutzer wurden aus der Datenbank entfernt: {lis_u}"
                """
            )
        else:
            st.info(
                f"""
                Der Benutzer 
                {del_users[0]} ({[user['name'] for user in all_users if user['key'] == del_users[0]][0]}) 
                wurde aus der Datenbank entfernt.
                """
            )

    st.button("ok", key="del_ok_butt")


@dics.timer()
def list_all_users() -> list:
    """alle Benutzer auflisten"""

    users = gv.deta_db.fetch().items
    if del_users := [
        user["key"]
        for user in users
        if datetime.datetime.strptime(user["access_until"], "%Y-%m-%d")
        < datetime.datetime.now()
    ]:
        for user in del_users:
            gv.deta_db.delete(user)
    return gv.deta_db.fetch().items


# neuer Benutzer: Kommentar einer der Funktionen entfernen, Passwort (als Klartext) nicht vergessen und Datei in Terminal ausführen - neuer Benutzer wird in Datenbank geschrieben

# insert_new_user("utec", "UTEC allgemein", "", "full")
# insert_new_user("fl", "Florian", "", "god")

# insert_new_user("some_username", "some_name", "some_password", ["meteo"])


# update_user("fl", {"access_until": str(datetime.date.max)})
# update_user("utec", {"access_until": str(datetime.date.max)})
