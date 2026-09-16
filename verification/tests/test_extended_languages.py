"""Tests for new verification languages."""
import pytest
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def has_tool(cmd):
    return shutil.which(cmd) is not None

class TestLean4:
    def test_lean4_builds(self):
        if not has_tool("lake"):
            pytest.skip("Lean 4 not installed")
        import subprocess
        result = subprocess.run(["lake", "build"], cwd=PROJECT_ROOT / "lean4",
                                capture_output=True, text=True, timeout=1200)
        assert result.returncode == 0

class TestCoq:
    @pytest.mark.parametrize("section_file", [
        "section1_correction_b/CorrectionB.v",
        "section2_preprint/ProofChain.v",
        "section3_ab_cloud/Hofstadter.v",
        "section4_kdv/KdV.v",
        "section5_klein_attractor/Klein.v",
        "section6_riemann_zeros/RiemannZeros.v",
    ])
    def test_coq_compiles(self, section_file):
        if not has_tool("coqc"):
            pytest.skip("Coq not installed")
        import subprocess
        result = subprocess.run(["coqc", section_file], cwd=PROJECT_ROOT / "coq",
                                capture_output=True, text=True, timeout=600)
        assert result.returncode == 0

class TestRust:
    def test_rust_builds(self):
        if not has_tool("cargo"):
            pytest.skip("Rust not installed")
        import subprocess
        result = subprocess.run(["cargo", "build", "--release"],
                                cwd=PROJECT_ROOT / "rust",
                                capture_output=True, text=True, timeout=600)
        assert result.returncode == 0

class TestCpp:
    def test_cpp_builds(self):
        if not has_tool("cmake"):
            pytest.skip("CMake not installed")
        import subprocess
        build_dir = PROJECT_ROOT / "cpp" / "build"
        build_dir.mkdir(exist_ok=True)
        subprocess.run(["cmake", ".."], cwd=build_dir, capture_output=True)
        result = subprocess.run(["make", "-j4"], cwd=build_dir,
                                capture_output=True, text=True, timeout=600)
        assert result.returncode == 0

class TestHaskell:
    def test_haskell_builds(self):
        if not has_tool("cabal"):
            pytest.skip("Haskell not installed")
        import subprocess
        result = subprocess.run(["cabal", "build", "all"],
                                cwd=PROJECT_ROOT / "haskell",
                                capture_output=True, text=True, timeout=600)
        assert result.returncode == 0
