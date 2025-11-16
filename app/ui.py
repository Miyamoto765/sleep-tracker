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
          background: 
            radial-gradient(circle at 10% 20%, rgba(0,223,216,0.08), transparent 20%),
            radial-gradient(circle at 90% 80%, rgba(124,58,237,0.08), transparent 20%),
            radial-gradient(circle at 50% 50%, rgba(0,143,251,0.03), transparent 30%),
            linear-gradient(135deg, #0a0e1a 0%, #0d1526 25%, #0f1a2e 50%, #0a1421 75%, #081428 100%);
          min-height: 100vh;
          padding: 28px 36px;
          position: relative;
        }
        
        [data-testid="stAppViewContainer"]::before {
          content: '';
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: 
            repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,223,216,0.02) 2px, rgba(0,223,216,0.02) 4px),
            repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(124,58,237,0.02) 2px, rgba(124,58,237,0.02) 4px);
          pointer-events: none;
          z-index: 0;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          [data-testid="stAppViewContainer"] {
            padding: 16px 20px;
          }

          .nav-container {
            flex-direction: column !important;
            padding: 12px 16px !important;
            margin-bottom: 16px !important;
          }

          .nav-title {
            margin-bottom: 12px;
            font-size: 18px !important;
          }

          div[data-testid="stButton"] > button {
            padding: 8px 16px !important;
            font-size: 14px !important;
            margin: 2px !important;
          }

          .app-card {
            padding: 16px !important;
            margin-bottom: 16px !important;
          }
        }

        @media (max-width: 480px) {
          [data-testid="stAppViewContainer"] {
            padding: 12px 16px;
          }

          .nav-title .logo {
            width: 32px !important;
            height: 32px !important;
            font-size: 14px !important;
          }
        }

        .nav-container {
          background: linear-gradient(135deg, 
            rgba(0,223,216,0.08) 0%, 
            rgba(124,58,237,0.08) 50%,
            rgba(0,143,251,0.06) 100%);
          border: 1px solid rgba(255,255,255,0.1);
          box-shadow: 
            0 8px 32px rgba(0,0,0,0.4),
            0 0 0 1px rgba(255,255,255,0.05) inset,
            0 2px 8px rgba(0,223,216,0.1);
          padding: 16px 28px;
          border-radius: 16px;
          display:flex;
          align-items:center;
          gap:20px;
          position: sticky;
          top: 8px;
          z-index: 9999;
          backdrop-filter: blur(12px) saturate(180%);
          margin-bottom: 24px;
          flex-wrap: wrap;
          justify-content: space-between;
        }

        .nav-title { 
          display:flex; 
          gap:12px; 
          align-items:center; 
          font-weight:700; 
          color:#ffffff;
          text-shadow: 0 2px 8px rgba(0,223,216,0.3);
          font-size: 20px;
        }
        .nav-title .logo { 
          width:44px; 
          height:44px; 
          display:inline-flex; 
          align-items:center; 
          justify-content:center; 
          border-radius:12px; 
          background: linear-gradient(135deg, rgba(0,223,216,0.2), rgba(124,58,237,0.2)); 
          font-size:20px;
          box-shadow: 
            0 4px 12px rgba(0,223,216,0.2),
            0 0 0 1px rgba(255,255,255,0.1) inset;
          border: 1px solid rgba(255,255,255,0.15);
        }

        /* Enhanced button styles with better mobile support */
        div[data-testid="stButton"] > button {
          background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
          color: #e0f7f8;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.08);
          padding: 12px 28px;
          font-size: 16px;
          font-weight: 600;
          transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
          min-height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 
            0 2px 8px rgba(0,0,0,0.2),
            0 0 0 1px rgba(255,255,255,0.05) inset;
        }

        div[data-testid="stButton"] > button:hover {
          transform: translateY(-3px);
          color: #ffffff;
          background: linear-gradient(135deg, rgba(0,223,216,0.15), rgba(124,58,237,0.12));
          border-color: rgba(0,223,216,0.3);
          box-shadow: 
            0 8px 24px rgba(0,0,0,0.3),
            0 0 20px rgba(0,223,216,0.15),
            0 0 0 1px rgba(255,255,255,0.1) inset;
        }

        div[data-testid="stButton"] > button:focus {
          outline: 2px solid rgba(0,223,216,0.6);
          outline-offset: 3px;
        }

        .nav-active {
          background: linear-gradient(135deg, #00dfd8, #7c3aed) !important;
          color: white !important;
          box-shadow: 
            0 8px 32px rgba(124,58,237,0.3),
            0 4px 16px rgba(0,223,216,0.25),
            0 0 0 1px rgba(255,255,255,0.2) inset !important;
          transform: translateY(-2px) !important;
          border-color: rgba(255,255,255,0.3) !important;
          animation: glow 3s ease-in-out infinite;
        }

        @keyframes glow {
          0% { 
            box-shadow: 
              0 8px 32px rgba(124,58,237,0.3),
              0 4px 16px rgba(0,223,216,0.25),
              0 0 0 1px rgba(255,255,255,0.2) inset;
          }
          50% { 
            box-shadow: 
              0 12px 40px rgba(124,58,237,0.4),
              0 6px 20px rgba(0,223,216,0.35),
              0 0 0 1px rgba(255,255,255,0.3) inset;
          }
          100% { 
            box-shadow: 
              0 8px 32px rgba(124,58,237,0.3),
              0 4px 16px rgba(0,223,216,0.25),
              0 0 0 1px rgba(255,255,255,0.2) inset;
          }
        }

        .page-content {
          opacity: 0;
          transform: translateY(6px);
          transition: opacity 450ms ease-out, transform 450ms ease-out;
        }
        .page-content.fade-in {
          opacity: 1;
          transform: translateY(0px);
        }

        .app-card {
          background: linear-gradient(135deg, 
            rgba(255,255,255,0.06) 0%, 
            rgba(255,255,255,0.03) 100%);
          backdrop-filter: blur(16px) saturate(180%);
          border-radius: 16px;
          padding: 28px;
          margin-bottom: 24px;
          border: 1px solid rgba(255,255,255,0.1);
          box-shadow: 
            0 8px 32px rgba(0,0,0,0.3),
            0 0 0 1px rgba(255,255,255,0.05) inset,
            0 2px 8px rgba(0,223,216,0.05);
          transition: all 350ms cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          overflow: hidden;
        }
        
        .app-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, 
            transparent, 
            rgba(0,223,216,0.3), 
            rgba(124,58,237,0.3), 
            transparent);
          opacity: 0;
          transition: opacity 350ms ease;
        }

        .app-card:hover {
          transform: translateY(-4px);
          box-shadow: 
            0 12px 40px rgba(0,0,0,0.4),
            0 0 0 1px rgba(255,255,255,0.08) inset,
            0 4px 16px rgba(0,223,216,0.1);
          border-color: rgba(0,223,216,0.2);
        }
        
        .app-card:hover::before {
          opacity: 1;
        }

        /* Audio recorder specific styles */
        #audio-recorder {
          max-width: 100%;
          margin: 0 auto;
        }

        #audio-recorder button {
          min-width: 120px;
          min-height: 44px;
          touch-action: manipulation;
        }

        @media (max-width: 768px) {
          #audio-recorder button {
            min-width: 100px;
            font-size: 14px;
            padding: 8px 12px;
          }
        }

        .app-footer {
          margin-top: 48px;
          padding: 20px 16px;
          border-radius: 12px;
          color: #b8dde0;
          background: linear-gradient(135deg, 
            rgba(255,255,255,0.04) 0%, 
            rgba(255,255,255,0.02) 100%);
          border: 1px solid rgba(255,255,255,0.08);
          text-align: center;
          font-size: 14px;
          backdrop-filter: blur(8px);
          box-shadow: 
            0 4px 16px rgba(0,0,0,0.2),
            0 0 0 1px rgba(255,255,255,0.05) inset;
        }

        footer { visibility: hidden; }

        /* Loading animations */
        .loading-spinner {
          border: 3px solid rgba(255,255,255,0.1);
          border-radius: 50%;
          border-top: 3px solid #00dfd8;
          width: 40px;
          height: 40px;
          animation: spin 1s linear infinite;
          margin: 20px auto;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        /* Error state styling */
        .error-container {
          background: rgba(244,67,54,0.1);
          border: 1px solid rgba(244,67,54,0.3);
          border-radius: 8px;
          padding: 16px;
          margin: 16px 0;
        }

        /* Success state styling */
        .success-container {
          background: rgba(76,175,80,0.1);
          border: 1px solid rgba(76,175,80,0.3);
          border-radius: 8px;
          padding: 16px;
          margin: 16px 0;
        }

        /* Chart container responsiveness */
        .js-plotly-plot {
          max-width: 100% !important;
          height: auto !important;
        }

        @media (max-width: 768px) {
          .plotly-graph-div {
            height: 300px !important;
          }
        }

        /* Better form styling for mobile */
        .stSelectbox > div > div {
          min-height: 44px;
        }

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
          min-height: 44px;
          border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def navbar_buttons(pages_dict):
    """Render navbar buttons for keys in pages_dict (dict of page_name->view)."""
    # top container with brand (left) and buttons (centered)
    html = """
    <div class="nav-container">
      <div class="nav-title"><div class="logo">😴</div><div>Sleep Tracker</div></div>
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
          Built with ❤️ • Librosa + Scikit-learn + Streamlit • Sleep Tracker — prototype
        </div>
        """,
        unsafe_allow_html=True,
    )
