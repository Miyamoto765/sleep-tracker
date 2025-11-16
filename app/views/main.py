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
          <h1 style="margin:0;">AI Sleep Tracker</h1>
          <p style="margin:6px 0 0 0; color:#d9f1f1;">
            Quick, private sleep insights using only your breathing & motion data —
            upload a short clip or simulate motion logs and get an instant sleep-stage snapshot.
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
        <li><b>Track</b> — Use the Logger to record motion or run a simulation and monitor trends in Analytics.</li>
      </ol>

      <div style="margin-top:16px;">
        <form action="#" method="get">
          <button type="submit"
            style="background:linear-gradient(90deg,#00dfd8,#7c3aed);
                   color:white;border:none;padding:10px 18px;
                   border-radius:8px;font-weight:700;
                   box-shadow:0 0 8px rgba(0,223,216,0.4);
                   transition:all 0.3s ease;"
            onmouseover="this.style.boxShadow='0 0 14px rgba(124,58,237,0.6)'"
            onmouseout="this.style.boxShadow='0 0 8px rgba(0,223,216,0.4)'"
            onclick="window.location.href = window.location.pathname + '?page=Upload'; return false;">
            🚀 Start Upload
          </button>
        </form>
      </div>

      <!-- hidden iframe for legacy postMessage (kept as-is but not required) -->
      <iframe style="display:none;">
      <script>
      window.addEventListener('message', (event) => {
        if(event.data && event.data.type === 'NAV_UPLOAD'){
          const streamlit = window.parent || window;
          streamlit.dispatchEvent(new Event('NAV_UPLOAD'));
        }
      });
      </script>
      </iframe>
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
