# app/ui.py
import streamlit as st
import streamlit.components.v1 as components

def safe_rerun():
    """Compatibility wrapper to rerun the Streamlit app across versions."""
    # try recommended API first
    try:
        # new API
        return st.rerun()
    except Exception:
        pass
    # fallback to experimental_rerun if available
    try:
        return st.experimental_rerun()
    except Exception:
        pass
    # Last resort: force a session state change that causes a rerun
    try:
        st.session_state["_force_rerun"] = st.session_state.get("_force_rerun", 0) + 1
    except Exception:
        # if session_state inaccessible, just no-op
        pass

def apply_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; color: #E9F2F3; }

        [data-testid="stAppViewContainer"] {
          background: radial-gradient(circle at 12% 12%, rgba(0,215,178,0.06), transparent 12%),
                      radial-gradient(circle at 90% 88%, rgba(124,58,237,0.04), transparent 12%),
                      linear-gradient(180deg, #071021 0%, #081428 35%, #0b1b2a 100%);
          min-height: 100vh;
          padding: 28px 36px;
        }

        .nav-container {
          background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
          border: 1px solid rgba(255,255,255,0.03);
          box-shadow: 0 10px 30px rgba(2,6,23,0.5);
          padding: 14px 22px;
          border-radius: 14px;
          display:flex;
          align-items:center;
          gap:20px;
          position: sticky;
          top: 8px;
          z-index: 9999;
          backdrop-filter: blur(6px);
          margin-bottom: 18px;
        }
        .nav-title { display:flex; gap:10px; align-items:center; font-weight:700; color:#e6f8f5; }
        .nav-title .logo { width:40px; height:40px; display:inline-flex; align-items:center; justify-content:center; border-radius:8px; background: linear-gradient(90deg,#7c3aed33,#00dfd833); font-size:18px; }

        div[data-testid="stButton"] > button {
          background: transparent;
          color: #cfeff0;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.04);
          padding: 10px 26px;
          font-size: 16px;
          font-weight: 600;
          transition: all 180ms ease;
        }
        div[data-testid="stButton"] > button:hover { transform: translateY(-4px); color: #fff; box-shadow: 0 6px 20px rgba(0,0,0,0.45); }

        .nav-active {
          background: linear-gradient(90deg,#00dfd8,#7c3aed) !important;
          color: white !important;
          box-shadow: 0 10px 30px rgba(124,58,237,0.18) !important;
          transform: translateY(-2px) !important;
          animation: glow 2s infinite;
        }

        @keyframes glow {
          0% { box-shadow: 0 0 6px rgba(0,223,216,0.12); }
          50% { box-shadow: 0 0 18px rgba(124,58,237,0.18); }
          100% { box-shadow: 0 0 6px rgba(0,223,216,0.12); }
        }

        .page-content { opacity: 0; transform: translateY(6px); transition: opacity 450ms ease-out, transform 450ms ease-out; }
        .page-content.fade-in { opacity: 1; transform: translateY(0px); }

        .app-card {
          background: rgba(255,255,255,0.03);
          backdrop-filter: blur(10px);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 20px;
          border:1px solid rgba(255,255,255,0.04);
          box-shadow: 0 8px 26px rgba(0,0,0,0.35);
        }

        .app-footer {
          margin-top: 36px;
          padding: 18px 12px;
          border-radius: 10px;
          color: #bcdfe0;
          background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
          border: 1px solid rgba(255,255,255,0.03);
          text-align: center;
          font-size: 14px;
        }

        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def navbar_buttons(pages_dict):
    """Render navbar buttons for keys in pages_dict (dict of page_name->view)."""
    # top container with brand (left) and buttons (centered)
    html = """
    <div class="nav-container">
      <div class="nav-title"><div class="logo">😴</div><div>AI Sleep Tracker</div></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Create equal-width columns for each page button
    keys = list(pages_dict.keys())
    cols = st.columns(len(keys))
    for i, name in enumerate(keys):
        with cols[i]:
            label = name
            # Render a button; clicking it sets session state and reruns
            if st.button(label, key=f"nav_{name}"):
                st.session_state["page"] = name
                # Use safe rerun to support different Streamlit versions
                safe_rerun()

    # small JS to highlight active nav button by text match
    current = st.session_state.get("page", "Home")
    js = f"""
    <script>
    (function() {{
      try {{
        const txt = {current!r};
        const btns = Array.from(document.querySelectorAll('div[data-testid="stButton"] > button'));
        btns.forEach(b => b.classList.remove('nav-active'));
        let target = btns.find(b => b.innerText.trim().toLowerCase() === String(txt).toLowerCase() ||
                                   b.innerText.trim().toLowerCase().includes(String(txt).toLowerCase()));
        if(target) target.classList.add('nav-active');
      }} catch(e) {{ console.warn("nav highlight script error", e); }}
    }})();
    </script>
    """
    components.html(js, height=0, width=0)

def footer():
    st.markdown(
        """
        <div class="app-footer">
          Built with ❤️ • Librosa + Scikit-learn + Streamlit • AI Sleep Tracker — prototype
        </div>
        """,
        unsafe_allow_html=True,
    )
