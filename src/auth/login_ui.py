"""
Benchmark Dashboard - Gruppe 18
Login UI Components

Streamlit-basierter Login-Screen
"""

import streamlit as st
from src.auth.authentication import authenticate_user, dev_bypass_login


def render_login_screen():
    """Rendert den Login-Screen und verwaltet den Login-State

    Returns:
        bool: True wenn User eingeloggt, False sonst
    """
    # Initialisiere Session State
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.security_level = None
        st.session_state.username = None
        st.session_state.db_user = None
        st.session_state.db_password = None

    # Wenn bereits eingeloggt, return True
    if st.session_state.authenticated:
        return True

    # CSS um überflüssiges Streamlit-Container-Padding zu entfernen
    st.markdown("""
        <style>
            /* Entferne nur das störende Markdown-Container-Padding */
            .stMarkdownContainer {
                padding: 0 !important;
            }

            /* Verstecke Header für cleanen Login */
            header[data-testid="stHeader"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

    # Login-Screen anzeigen
    st.markdown("""
        <div style="text-align: center; padding: 50px 0 30px 0;">
            <h1 style="color: #00d4ff; font-size: 3em; margin-bottom: 10px;">🚴 Benchmark Dashboard</h1>
            <p style="color: #aaa; font-size: 1.2em;">Gruppe 18 - Filialvergleich</p>
        </div>
    """, unsafe_allow_html=True)

    # Zentriertes Login-Formular
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Überschrift
        st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 30px;'>Anmeldung</h3>",
                   unsafe_allow_html=True)

        # Login-Formular
        with st.form("login_form"):
            username = st.text_input("Benutzername", placeholder="USERNAME")
            password = st.text_input("Passwort", type="password", placeholder="USERPASS")

            col_login, col_dev = st.columns([2, 1])

            with col_login:
                login_clicked = st.form_submit_button("Anmelden", use_container_width=True)

            with col_dev:
                dev_clicked = st.form_submit_button("🔧 Dev", use_container_width=True,
                                                    type="secondary",
                                                    help="Entwickler-Bypass (später entfernen!)")

        # Verarbeite Login
        if login_clicked:
            if not username or not password:
                st.error("Bitte Benutzername und Passwort eingeben")
            else:
                with st.spinner("Authentifizierung läuft..."):
                    result = authenticate_user(username, password)

                    if result['authenticated']:
                        st.session_state.authenticated = True
                        st.session_state.security_level = result['security_level']
                        st.session_state.username = result['username']
                        st.session_state.db_user = username
                        st.session_state.db_password = password
                        st.success(f"✓ {result['message']} (Security Level {result['security_level']})")
                        st.rerun()
                    else:
                        st.error(f"✗ {result['message']}")

        # Dev-Bypass
        if dev_clicked:
            st.warning("⚠️ DEV MODE - Bypass aktiv (später entfernen!)")
            result = dev_bypass_login()
            st.session_state.authenticated = True
            st.session_state.security_level = result['security_level']
            st.session_state.username = result['username']
            st.rerun()

    # Footer
    st.markdown("""
        <div style="text-align: center; padding: 50px 0 20px 0; color: #666;">
            <p style="font-size: 0.9em;">Nur autorisierte Benutzer (Security Level 3 oder 4) haben Zugriff</p>
        </div>
    """, unsafe_allow_html=True)

    return False


def logout():
    """Loggt den User aus"""
    st.session_state.authenticated = False
    st.session_state.security_level = None
    st.session_state.username = None
    st.session_state.db_user = None
    st.session_state.db_password = None
    st.rerun()


def get_current_user() -> dict:
    """Gibt aktuelle User-Info zurück

    Returns:
        dict mit username und security_level, oder None wenn nicht eingeloggt
    """
    if st.session_state.get('authenticated', False):
        return {
            'username': st.session_state.get('username'),
            'security_level': st.session_state.get('security_level')
        }
    return None
