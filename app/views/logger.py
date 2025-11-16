import streamlit as st
import pandas as pd
import plotly.express as px
import time
import numpy as np

def render():
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="app-card"><h2>📡 Real-Time Sleep Motion Logger</h2>', unsafe_allow_html=True)
    st.write("Simulate motion data logging or connect hardware later.")

    if st.button("▶ Start Simulation"):
        progress = st.progress(0)
        simulated = []
        for i in range(100):
            simulated.append({"time": i, "accel_g": 0.03 + 0.03 * np.sin(i/6) + np.random.normal(0,0.01)})
            progress.progress(i+1)
            time.sleep(0.01)
        df = pd.DataFrame(simulated)
        fig = px.line(df, x="time", y="accel_g", title="Simulated Motion Log")
        st.plotly_chart(fig, width='stretch')

    st.markdown('</div></div>', unsafe_allow_html=True)
