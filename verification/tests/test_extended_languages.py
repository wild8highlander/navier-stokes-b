"""Tests for new verification languages."""
import shutil
from pathlib import Path

import pytest

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
        if not (has_tool("cabal") and has_tool("ghc")):
            pytest.skip("Haskell (cabal/ghc) not installed")
        import subprocess
        from pathlib import Path

        # Fresh environments (e.g. GitHub CI runners) have no Hackage package
        # index yet, and `cabal build` then fails with Cabal-7160
        # ("The package list for 'hackage.haskell.org' does not exist").
        # Detect an existing index (both legacy ~/.cabal and XDG layouts) and
        # run `cabal update` only when it is actually missing.
        home = Path.home()
        has_index = any(
            (base / "packages" / "hackage.haskell.org").exists()
            for base in (home / ".cabal", home / ".config" / "cabal")
        )
        if not has_index:
            upd = subprocess.run(["cabal", "update"],
                                 cwd=PROJECT_ROOT / "haskell",
                                 capture_output=True, text=True, timeout=600)
            assert upd.returncode == 0, (
                "cabal update failed:\n"
                f"stdout: {upd.stdout[-2000:]}\nstderr: {upd.stderr[-2000:]}"
            )
        result = subprocess.run(["cabal", "build", "all"],
                                cwd=PROJECT_ROOT / "haskell",
                                capture_output=True, text=True, timeout=900)
        assert result.returncode == 0, (
            "cabal build all failed:\n"
            f"stdout: {result.stdout[-4000:]}\nstderr: {result.stderr[-4000:]}"
        )
