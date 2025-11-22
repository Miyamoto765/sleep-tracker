# app/views/main.py
import streamlit as st

def render():
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)

    # --- HERO / INTRO ---
    st.markdown("""
    <div class="app-card">
      <div style="display:flex; gap:18px; align-items:center;">
        <div style="font-size:48px">😴</div>
        <div>
          <h1 style="margin:0;">Sleep Pattern Tracker</h1>
          <p style="margin:6px 0 0 0; color:#d9f1f1;">
            Quick, private sleep insights using only your breathing & motion data —
            upload a short clip or connect live sensors and get an instant sleep-stage snapshot.
          </p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- GET STARTED SECTION ---
    # Note: this uses a URL query param navigation on click (reliable).
    st.markdown("""
    <div class="app-card">
      <h2>Get started in 1–2–3</h2>
      <ol style="line-height:1.9;">
        <li><b>Upload</b> — Add a 30–60s audio (WAV/MP3) and we'll extract acoustic features.</li>
        <li><b>Analyze</b> — A trained model scores the recording and returns a sleep-cluster & quality score.</li>
        <li><b>Track</b> — Head to <b>Real-time</b> to connect Arduino sensors and monitor trends instantly in Analytics.</li>
      </ol>
    </div>
    """, unsafe_allow_html=True)

    # --- PRIVACY SECTION ---
    st.markdown("""
    <div class="app-card">
      <h2>Privacy first</h2>
      <p style="color:#cfeff0;">
        All audio and motion data are processed locally in this prototype (no cloud upload).
        You can download or delete session results at any time.
      </p>
      <p style="margin-top:10px; color:#b7e9e8;">
        This is a research prototype — not medical advice. Use as a baseline,
        and consult a clinician for clinical concerns.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Optional Streamlit fallback (visible) - remove if you don't want it:
    # if st.button("Start Upload (fallback)"):
    #     st.session_state["page"] = "Upload"
    #     st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
