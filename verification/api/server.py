"""FastAPI REST API server for the verification framework.

Each GET /api/verify/{section_id} actually executes the corresponding
Python reference verifier (verification/sectionN_*/python/verify.py) in a
subprocess and returns its real verdict, parsed from the JSON contract
line, together with the full verifier output. A section that fails or
crashes returns all_passed=false with HTTP 200 (the *verdict* failed, the
API itself worked); an unknown section id returns 404.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(title="navier-stokes-b Verification API",
              description="Runs the section verifiers and returns their "
                          "machine-readable verdicts.")

VERIFICATION_DIR = Path(__file__).resolve().parent.parent

SECTION_DIRS = {
    1: "section1_correction_b",
    2: "section2_preprint",
    3: "section3_ab_cloud",
    4: "section4_kdv",
    5: "section5_klein_attractor",
    6: "section6_riemann_zeros",
}


def run_verifier(section_id: int) -> dict:
    verifier = VERIFICATION_DIR / SECTION_DIRS[section_id] / "python" / "verify.py"
    proc = subprocess.run([sys.executable, str(verifier)],
                          capture_output=True, text=True, timeout=120)
    output = proc.stdout or ""
    verdict = None
    for line in output.splitlines():
        if line.startswith("JSON: "):
            try:
                verdict = json.loads(line[len("JSON: "):])
            except json.JSONDecodeError:
                verdict = None
    if verdict is None:
        verdict = {"section": section_id, "language": "python",
                   "values": {}, "all_passed": proc.returncode == 0}
    verdict["output"] = output
    return verdict


@app.get("/api/sections")
def list_sections():
    return {"sections": sorted(SECTION_DIRS)}


@app.get("/api/verify/{section_id}")
def verify(section_id: int):
    if section_id not in SECTION_DIRS:
        raise HTTPException(status_code=404, detail=f"unknown section {section_id}")
    try:
        return run_verifier(section_id)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="verifier timed out")


@app.get("/api/constant")
def constant():
    """The universal polarization constant b and derived angles."""
    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    theta = math.asin(b)
    return {"b": b, "theta_b_rad": theta, "theta_b_deg": math.degrees(theta)}
