#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  termux_setup_and_push.sh — NSB Lab on Android: one-shot toolchain setup,
#  full build + self-test of every CLI edition, and a guided GitHub push.
#
#  Usage (inside Termux):
#      pkg install git curl -y
#      bash scripts/termux_setup_and_push.sh [options]
#
#  Options:
#      --skip-install     do not run `pkg install` (toolchains already there)
#      --skip-build       do not build/selftest (push only)
#      --remote URL       use this origin URL instead of asking
#      --branch NAME      branch to push (default: main)
#      --dry-run          show what would be done, execute nothing
#
#  The script is idempotent: re-running it skips what is already done.
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

SKIP_INSTALL=0; SKIP_BUILD=0; REMOTE=""; BRANCH="main"; DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --skip-install) SKIP_INSTALL=1 ;;
    --skip-build)   SKIP_BUILD=1 ;;
    --remote=*)     REMOTE="${arg#--remote=}" ;;
    --branch=*)     BRANCH="${arg#--branch=}" ;;
    --dry-run)      DRY_RUN=1 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
  esac
done

BGREEN='\033[1;32m'; BRED='\033[1;31m'; BYEL='\033[1;33m'; BCYA='\033[1;36m'; RST='\033[0m'
ok()   { echo -e "  ${BGREEN}✔${RST} $*"; }
fail() { echo -e "  ${BRED}✘${RST} $*"; }
info() { echo -e "  ${BCYA}▸${RST} $*"; }
run()  { if [ "$DRY_RUN" = 1 ]; then info "dry-run: $*"; else "$@"; fi }

cd "$(dirname "$0")/.." || exit 1
echo "════════════════════════════════════════════════════════════"
echo " NSB Lab — Termux setup, build & push"
echo " repo: $(pwd)"
echo "════════════════════════════════════════════════════════════"

IS_TERMUX=0
[ -n "${TERMUX_VERSION:-}" ] && IS_TERMUX=1
if [ "$IS_TERMUX" = 1 ]; then
  ok "Termux $TERMUX_VERSION detected"
else
  info "not Termux — continuing anyway (Linux/macOS paths work too)"
fi

# ─────────────────────────── 1. toolchains ────────────────────────────────
if [ "$SKIP_INSTALL" = 0 ]; then
  echo ""
  echo "── 1. toolchains ──────────────────────────────────────────"
  PKGS="git"
  command -v python3 >/dev/null 2>&1 || PKGS="$PKGS python"
  command -v cc >/dev/null 2>&1 || command -v clang >/dev/null 2>&1 || PKGS="$PKGS clang"
  command -v make >/dev/null 2>&1 || PKGS="$PKGS make"
  command -v cargo >/dev/null 2>&1 || PKGS="$PKGS rust"
  command -v go >/dev/null 2>&1 || PKGS="$PKGS golang"
  command -v php >/dev/null 2>&1 || PKGS="$PKGS php"
  command -v curl >/dev/null 2>&1 || PKGS="$PKGS curl"
  if [ "$IS_TERMUX" = 1 ]; then
    # binutils helps clang link on some Termux versions
    command -v ld >/dev/null 2>&1 || PKGS="$PKGS binutils"
  fi
  if [ "$PKGS" != "git" ] || ! command -v git >/dev/null 2>&1; then
    info "installing:$PKGS"
    if [ "$IS_TERMUX" = 1 ]; then
      run pkg install -y $PKGS
    elif command -v apt-get >/dev/null 2>&1; then
      run sudo apt-get install -y $PKGS
    elif command -v brew >/dev/null 2>&1; then
      for p in $PKGS; do run brew install "$p"; done
    else
      fail "no known package manager; install manually: $PKGS"
    fi
  else
    ok "core toolchains already present"
  fi
  # numpy for the Python edition (Termux ships a prebuilt wheel)
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "import numpy" 2>/dev/null || {
      info "installing numpy for the Python edition"
      run pip install numpy
    }
  fi
  # Julia is optional (community repo); offer, never force
  if ! command -v julia >/dev/null 2>&1; then
    info "Julia is optional: 'pkg install tur-reboot && pkg install julia' adds it"
  fi
fi

# ─────────────────────────── 2. build + selftest ──────────────────────────
PASS=0; FAIL=0; MISSING=0
declare -a RESULTS
check() { # name, command
  local name="$1"; shift
  if [ "$SKIP_BUILD" = 1 ]; then RESULTS+=("$name  skipped"); return; fi
  info "selftest: $name"
  if eval "$@" > "/tmp/nsb_st_$name.log" 2>&1; then
    ok "$name selftest PASS"; RESULTS+=("$name  PASS"); PASS=$((PASS+1))
  else
    fail "$name selftest FAIL (log: /tmp/nsb_st_$name.log)"; RESULTS+=("$name  FAIL"); FAIL=$((FAIL+1))
  fi
}

if [ "$SKIP_BUILD" = 0 ]; then
  echo ""
  echo "── 2. build + selftest ────────────────────────────────────"
  mkdir -p /tmp

  # Python
  if command -v python3 >/dev/null 2>&1 && python3 -c "import numpy" 2>/dev/null; then
    check python "python3 python/nsb_lab.py --selftest --no-color --ascii --out /tmp/nsb_st_py"
  else
    MISSING=$((MISSING+1)); RESULTS+=("python  missing toolchain/numpy")
  fi

  # C
  if command -v cc >/dev/null 2>&1 || command -v clang >/dev/null 2>&1; then
    CC_BIN=$(command -v cc || command -v clang)
    if run "$CC_BIN" -O2 -std=c99 c/nsb_lab.c -o /tmp/nsb_c -lm; then
      check c "/tmp/nsb_c --selftest --no-color --ascii --out /tmp/nsb_st_c"
    else
      FAIL=$((FAIL+1)); RESULTS+=("c       build FAIL")
    fi
  else
    MISSING=$((MISSING+1)); RESULTS+=("c       missing clang")
  fi

  # C++
  if command -v clang++ >/dev/null 2>&1 || command -v g++ >/dev/null 2>&1; then
    CXX_BIN=$(command -v clang++ || command -v g++)
    if run "$CXX_BIN" -O2 -std=c++17 -pthread cpp/nsb_lab.cpp -o /tmp/nsb_cpp; then
      check cpp "/tmp/nsb_cpp --selftest --no-color --ascii --out /tmp/nsb_st_cpp"
    else
      FAIL=$((FAIL+1)); RESULTS+=("cpp     build FAIL")
    fi
  else
    MISSING=$((MISSING+1)); RESULTS+=("cpp     missing clang++/g++")
  fi

  # Rust
  if command -v cargo >/dev/null 2>&1; then
    if run cargo build --release --manifest-path rust/Cargo.toml; then
      check rust "./rust/target/release/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_st_rs"
    else
      FAIL=$((FAIL+1)); RESULTS+=("rust    build FAIL")
    fi
  else
    MISSING=$((MISSING+1)); RESULTS+=("rust    missing cargo")
  fi

  # Go
  if command -v go >/dev/null 2>&1; then
    if run go -C go build -o /tmp/nsb_go .; then
      check go "/tmp/nsb_go --selftest --no-color --ascii --out /tmp/nsb_st_go"
    else
      FAIL=$((FAIL+1)); RESULTS+=("go      build FAIL")
    fi
  else
    MISSING=$((MISSING+1)); RESULTS+=("go      missing golang")
  fi

  # PHP
  if command -v php >/dev/null 2>&1; then
    check php "php php/nsb_lab.php --selftest --no-color --ascii --out /tmp/nsb_st_php"
  else
    MISSING=$((MISSING+1)); RESULTS+=("php     missing php")
  fi

  # Julia (optional)
  if command -v julia >/dev/null 2>&1; then
    check julia "julia -t auto julia/nsb_lab_standalone.jl --selftest --no-color"
  else
    MISSING=$((MISSING+1)); RESULTS+=("julia   optional, not installed")
  fi

  echo ""
  echo "── selftest summary ───────────────────────────────────────"
  for r in "${RESULTS[@]:-}"; do [ -n "$r" ] && echo "  $r"; done
  echo "  ── PASS: $PASS  FAIL: $FAIL  missing/optional: $MISSING ──"
  if [ "$FAIL" -gt 0 ]; then
    fail "fix the failing editions before pushing (see logs in /tmp)"
    exit 1
  fi
fi

# ─────────────────────────── 3. git ───────────────────────────────────────
echo ""
echo "── 3. git ─────────────────────────────────────────────────"
command -v git >/dev/null 2>&1 || { fail "git not installed"; exit 1; }

if [ ! -d .git ]; then
  info "git init"
  run git init -b "$BRANCH"
else
  ok "git repo exists ($(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'no branch'))"
fi

# identity — reuse global config when present, else ask once (repo-local)
if ! git config user.name >/dev/null 2>&1; then
  read -r -p "  git user.name: " GNAME
  run git config user.name "${GNAME:-NSB Lab User}"
fi
if ! git config user.email >/dev/null 2>&1; then
  read -r -p "  git user.email: " GEMAIL
  run git config user.email "${GEMAIL:-nsb@example.com}"
fi

git add -A
if git diff --cached --quiet; then
  ok "nothing new to commit"
else
  info "staging $(git diff --cached --numstat | wc -l) files"
  run git commit -m "NSB Lab: the Navier-Stokes b-Correction Laboratory in 8 languages

- Julia reference v2.1 (standalone, self-contained)
- Python / C99 / C++17 / Rust / Go / PHP editions, same physics, same selftests
- Web app (single index.html): WebWorker pseudospectral solver, 6 UI languages
- One-line progress bar everywhere, ASCII fallback
- CI (GitHub Actions): build + selftest + physics checks
- docs/ (PHYSICS, PORTING, I18N), per-edition encyclopedia READMEs
- MIT license"
fi

# ─────────────────────────── 4. push ──────────────────────────────────────
echo ""
echo "── 4. push to GitHub ──────────────────────────────────────"
if [ -z "$REMOTE" ]; then
  if git remote get-url origin >/dev/null 2>&1; then
    REMOTE=$(git remote get-url origin)
    ok "using existing origin: $REMOTE"
  else
    echo "  A Personal Access Token (classic, repo scope) is needed for HTTPS push."
    echo "  Create one: GitHub → Settings → Developer settings → Tokens (classic)"
    read -r -p "  GitHub username: " GH_USER
    read -r -p "  Repository name [nsb-lab-multilang]: " GH_REPO
    GH_REPO=${GH_REPO:-nsb-lab-multilang}
    read -r -s -p "  Personal access token (input hidden): " GH_TOKEN; echo ""
    [ -n "$GH_USER" ] && [ -n "$GH_TOKEN" ] || { fail "no credentials given"; exit 1; }
    REMOTE="https://${GH_TOKEN}@github.com/${GH_USER}/${GH_REPO}.git"
    # store a clean origin without the token for everyday use
    run git remote add origin "https://github.com/${GH_USER}/${GH_REPO}.git"
  fi
fi

info "pushing to $(echo "$REMOTE" | sed -E 's#https://[^@]+@#https://***@#') (branch $BRANCH)"
run git push -u origin "$BRANCH" || {
  fail "push failed. Checklist:"
  echo "    · repo exists on GitHub and is empty (or accept fast-forward)"
  echo "    · token has 'repo' scope"
  echo "    · try SSH: pkg install openssh && see README §14"
  exit 1
}
ok "pushed."
echo ""
echo "════════════════════════════════════════════════════════════"
echo " Done. Your repository is live."
echo " Everyday pushes now:  git add -A && git commit -m … && git push"
echo "════════════════════════════════════════════════════════════"
