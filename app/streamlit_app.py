# app/streamlit_app.py  (Option 1: navbar visible everywhere)
import os,sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)
    
import streamlit as st
from app.ui import apply_css, navbar_buttons, footer
from app.views import main, home, upload, logger, analytics, realtime

PAGES = {
    "Home": home,
    "Real-time": realtime,
    "Upload": upload,
    "Logger": logger,
    "Analytics": analytics
}

# read ?page=... early
try:
    query_params = st.query_params()
except Exception:
    query_params = {}

if "page" in query_params:
    requested = query_params.get("page", [""])[0] or ""
    VALID = {"Main", "Home", "Real-time", "Upload", "Logger", "Analytics"}
    if requested in VALID:
        st.session_state["page"] = requested
    try:
        st.experimental_set_query_params()
    except Exception:
        pass

if "page" not in st.session_state:
    st.session_state["page"] = "Main"

st.set_page_config(page_title="AI Sleep Tracker", layout="wide")
apply_css()

# ---- IMPORTANT: show navbar always ----
navbar_buttons(PAGES)

# route pages
if st.session_state["page"] == "Main":
    try:
        main.render()
    except Exception as e:
        st.error(f"Error rendering Main: {e}")
else:
    page = st.session_state.get("page")
    view = PAGES.get(page)
    if view is None:
        st.error(f"Unknown page: {page}")
    else:
        try:
            view.render()
        except Exception as e:
            st.error(f"Error rendering {page}: {e}")

footer()
