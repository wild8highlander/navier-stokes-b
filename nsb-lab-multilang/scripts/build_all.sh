#!/usr/bin/env bash
# build_all.sh — build every CLI edition of NSB Lab and print a summary.
# Usage: bash scripts/build_all.sh [--smoke]
set -uo pipefail
SMOKE=0; [ "${1:-}" = "--smoke" ] && SMOKE=1
cd "$(dirname "$0")/.."
GRN='\033[1;32m'; RED='\033[1;31m'; CYA='\033[1;36m'; RST='\033[0m'

echo "══ NSB Lab — build all editions ══"

echo -e "${CYA}▸ python${RST} (nothing to build; checking numpy)"
python3 -c "import numpy" 2>/dev/null && echo -e "  ${GRN}ok${RST}" || echo -e "  ${RED}numpy missing — pip install numpy${RST}"

echo -e "${CYA}▸ c${RST}"
CC_BIN=$(command -v cc || command -v clang)
if [ -n "$CC_BIN" ] && "$CC_BIN" -O2 -std=c99 c/nsb_lab.c -o c/nsb_lab -lm 2>/tmp/nsb_build_c.log; then
  echo -e "  ${GRN}built: c/nsb_lab${RST}"
else echo -e "  ${RED}failed (see /tmp/nsb_build_c.log)${RST}"; fi

echo -e "${CYA}▸ cpp${RST}"
CXX_BIN=$(command -v clang++ || command -v g++)
if [ -n "$CXX_BIN" ] && "$CXX_BIN" -O2 -std=c++17 -pthread cpp/nsb_lab.cpp -o cpp/nsb_lab 2>/tmp/nsb_build_cpp.log; then
  echo -e "  ${GRN}built: cpp/nsb_lab${RST}"
else echo -e "  ${RED}failed (see /tmp/nsb_build_cpp.log)${RST}"; fi

echo -e "${CYA}▸ rust${RST}"
if cargo build --release --manifest-path rust/Cargo.toml 2>/tmp/nsb_build_rs.log; then
  echo -e "  ${GRN}built: rust/target/release/nsb_lab${RST}"
else echo -e "  ${RED}failed (see /tmp/nsb_build_rs.log)${RST}"; fi

echo -e "${CYA}▸ go${RST}"
if (cd go && go build -o nsb_lab .) 2>/tmp/nsb_build_go.log; then
  echo -e "  ${GRN}built: go/nsb_lab${RST}"
else echo -e "  ${RED}failed (see /tmp/nsb_build_go.log)${RST}"; fi

echo -e "${CYA}▸ php / julia / webapp${RST}  (interpreted — nothing to build)"

if [ "$SMOKE" = 1 ]; then
  echo ""
  echo "══ smoke: --selftest everywhere ══"
  for name_cmd in \
    "python3 python/nsb_lab.py --selftest --no-color --ascii --out /tmp/nsb_smoke_py" \
    "./c/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_c" \
    "./cpp/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_cpp" \
    "./rust/target/release/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_rs" \
    "./go/nsb_lab --selftest --no-color --ascii --out /tmp/nsb_smoke_go" \
    "php php/nsb_lab.php --selftest --no-color --ascii --out /tmp/nsb_smoke_php"
  do
    name="${name_cmd%% *}"
    if eval "$name_cmd" >/dev/null 2>&1; then
      echo -e "  ${GRN}✔ $name${RST}"
    else
      echo -e "  ${RED}✘ $name${RST}"
    fi
  done
fi
echo "══ done ══"
