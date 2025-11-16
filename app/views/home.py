import streamlit as st

def render():
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="app-card">
            <h1>😴 AI Sleep Tracker</h1>
            <p>
                Track your sleep patterns and breathing with the power of AI.  
                This project combines audio analysis 🎧 and motion logging 📡 to help you 
                visualize and improve your sleep quality.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="app-card">
            <h2>🌙 Features</h2>
            <ul style="line-height:1.8;">
                <li>🎵 <b>Audio Sleep Analysis</b> – Upload recordings to detect sleep stage clusters using ML.</li>
                <li>📡 <b>Motion Logger</b> – Capture movement data in real time or simulate logs.</li>
                <li>📊 <b>Sleep Quality Insights</b> – View charts and trends based on AI predictions.</li>
                <li>🧠 <b>Smart Feature Extraction</b> – MFCCs, rolloff, zcr and more.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="app-card">
            <h2>🚀 Getting Started</h2>
            <p>Go to <b>Upload</b> to analyze audio, or open <b>Logger</b> for motion simulation. Use <b>Analytics</b> to view trends.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
