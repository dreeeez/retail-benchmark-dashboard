"""
Benchmark Dashboard - Gruppe 18
Login UI Components

Streamlit-basierter Login-Screen
"""

import streamlit as st
from src.auth.authentication import authenticate_user


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

            /* Login Input Fields - Dark Background für Light Mode Fix */
            .stTextInput > div > div > input,
            .stTextInput input,
            [data-testid="stTextInput"] input,
            input[type="text"],
            input[type="password"] {
                background-color: #1a1f3a !important;
                border: 1px solid rgba(0, 212, 255, 0.3) !important;
                color: white !important;
            }

            .stTextInput > div > div > input::placeholder,
            .stTextInput input::placeholder,
            input::placeholder {
                color: rgba(255, 255, 255, 0.5) !important;
            }

            /* Login Button - Dark Background */
            .stFormSubmitButton > button,
            .stFormSubmitButton button,
            [data-testid="stFormSubmitButton"] button,
            button[kind="primaryFormSubmit"],
            form button {
                background-color: rgba(0, 212, 255, 0.2) !important;
                border: 1px solid rgba(0, 212, 255, 0.5) !important;
                color: white !important;
            }

            .stFormSubmitButton > button:hover,
            .stFormSubmitButton button:hover,
            form button:hover {
                background-color: rgba(0, 212, 255, 0.3) !important;
                border-color: rgba(0, 212, 255, 0.7) !important;
            }

            /* Label Farbe */
            .stTextInput > label,
            .stTextInput label,
            [data-testid="stTextInput"] label {
                color: rgba(255, 255, 255, 0.7) !important;
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

            login_clicked = st.form_submit_button("Anmelden", use_container_width=True)

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
                        st.success(f"✓ {result['message']} (Security Level {result['security_level']})")
                        st.rerun()
                    else:
                        st.error(f"✗ {result['message']}")

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
