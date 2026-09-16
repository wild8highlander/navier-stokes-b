"""Streamlit demo app."""
import streamlit as st
import math

st.title("Research Papers Verification")
b = math.pi / (4 * math.pi**2 + 2 * math.pi * math.sqrt(3))
st.write(f"Polarization correction b = {b:.15f}")
