"""Streamlit demo app — an interactive front-end over the section verifiers.

Every button click runs the real Python reference verifier
(`verification/sectionN_*/python/verify.py`) in a subprocess and shows its
verbatim contract output. Nothing is pre-computed or cached.

Run:  streamlit run streamlit_app.py   (pip install -r requirements.txt first)
"""
import math
import subprocess
import sys
from pathlib import Path

import streamlit as st

VERIFICATION_DIR = Path(__file__).resolve().parent.parent

SECTION_NAMES = {
    1: "S1 — Correction b",
    2: "S2 — Preprint NSE",
    3: "S3 — AB-Cloud",
    4: "S4 — KdV",
    5: "S5 — Klein attractor",
    6: "S6 — Riemann zeros",
    7: "S7 — Smagorinsky–Kolmogorov",
}

SECTION_DIRS = {
    1: "section1_correction_b",
    2: "section2_preprint",
    3: "section3_ab_cloud",
    4: "section4_kdv",
    5: "section5_klein_attractor",
    6: "section6_riemann_zeros",
    7: "section7_smagorinsky_kolmogorov",
}

st.title("navier-stokes-b — the verification framework, live")
st.caption("Pick a section and run the real reference verifier; the output "
           "is the verbatim contract stream (banner → PASS/FAIL → JSON).")

b = 1.0 / (4 * math.pi + 2 * math.sqrt(3))
st.write(f"Polarization correction **b = {b:.17f}**, "
         f"θ_b = {math.degrees(math.asin(b)):.13f}°")
cs = 1.0 / (math.pi * (3.0 * 1.5 / 2.0) ** 0.75)
st.write(f"Master relation **C_s(C_K = 1.5) = {cs:.17f}** "
         f"(Lilly 1966: 0.17326, Δ = {abs(cs - 0.17326):.2e})")

choice = st.radio("Section", [SECTION_NAMES[i] for i in sorted(SECTION_NAMES)],
                  index=0)
if st.button("Run the verifier"):
    sid = int(choice.split("—")[0].strip()[1:])
    verifier = VERIFICATION_DIR / SECTION_DIRS[sid] / "python" / "verify.py"
    with st.spinner(f"running section {sid}…"):
        proc = subprocess.run([sys.executable, str(verifier)],
                              capture_output=True, text=True, timeout=300)
    st.text(proc.stdout)
    st.code(f"exit code: {proc.returncode} "
            f"({'PASS' if proc.returncode == 0 else 'FAIL'})", language="text")
