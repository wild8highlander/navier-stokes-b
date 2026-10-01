"""Gradio demo app — an interactive front-end over the section verifiers.

Every button click runs the real Python reference verifier
(`verification/sectionN_*/python/verify.py`) in a subprocess and shows its
verbatim contract output (banner -> [PASS]/[FAIL] lines -> JSON verdict).
Nothing is pre-computed or cached: the demo is as honest as the framework.

Run:  python gradio_app.py          (pip install -r requirements.txt first)
"""
import math
import subprocess
import sys
from pathlib import Path

import gradio as gr

VERIFICATION_DIR = Path(__file__).resolve().parent.parent

SECTION_NAMES = {
    1: "S1 — Correction b (the universal polarization constant)",
    2: "S2 — Preprint NSE (the regularity chain)",
    3: "S3 — AB-Cloud (the Hofstadter Hamiltonian)",
    4: "S4 — KdV (soliton interactions)",
    5: "S5 — Klein attractor (ergodic dynamics)",
    6: "S6 — Riemann zeros (the Hilbert–Pólya programme)",
    7: "S7 — Smagorinsky–Kolmogorov (the master relation)",
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


def compute_b():
    """The constant itself, recomputed on the fly (the S1 teaser)."""
    return (f"b = 1/(4π + 2√3) = {math.pi / (4 * math.pi**2 + 2 * math.pi * math.sqrt(3)):.17f}\n"
            f"θ_b = arcsin(b) = {math.degrees(math.asin(1 / (4 * math.pi + 2 * math.sqrt(3)))):,.13f} deg".replace(",", ""))


def run_section(section_label):
    sid = int(section_label.split("—")[0].strip()[1:])
    verifier = VERIFICATION_DIR / SECTION_DIRS[sid] / "python" / "verify.py"
    proc = subprocess.run([sys.executable, str(verifier)],
                          capture_output=True, text=True, timeout=300)
    verdict = "FAILED TO PARSE"
    for line in (proc.stdout or "").splitlines():
        if line.startswith("JSON: "):
            verdict = line[6:]
    exit_line = f"exit code: {proc.returncode} ({'PASS' if proc.returncode == 0 else 'FAIL'})"
    return f"{proc.stdout}\n{exit_line}\n\nJSON verdict: {verdict}"


def compute_cs():
    """The S7 teaser: the master relation at the experimental C_K."""
    ck = 1.5
    cs = 1.0 / (math.pi * (3.0 * ck / 2.0) ** 0.75)
    return (f"C_s(C_K = 1.5) = 1/(π·(3·C_K/2)^(3/4)) = {cs:.17f}\n"
            f"Lilly (1966): 0.17326 — agreement Δ = {abs(cs - 0.17326):.2e}")


with gr.Blocks(title="navier-stokes-b verification demo") as demo:
    gr.Markdown("# navier-stokes-b — the verification framework, live\n"
                "Pick a section and run the *real* reference verifier; the "
                "output is the verbatim contract stream.")
    with gr.Tab("Sections 1–7"):
        sec = gr.Radio(choices=[SECTION_NAMES[i] for i in sorted(SECTION_NAMES)],
                       value=SECTION_NAMES[1], label="Section")
        btn = gr.Button("Run the verifier")
        out = gr.Textbox(label="Contract output", lines=24)
        btn.click(run_section, inputs=sec, outputs=out)
    with gr.Tab("Constants"):
        gr.Button("Recompute the constants").click(lambda: compute_b(), inputs=[], outputs=gr.Textbox(label="b"))
        gr.Button("Recompute the master relation").click(lambda: compute_cs(), inputs=[], outputs=gr.Textbox(label="C_s"))

if __name__ == "__main__":
    demo.launch()
