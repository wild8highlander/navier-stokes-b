#!/usr/bin/env bash
# ============================================================================
#  NSB LAB 96 — универсальный лаунчер / universal launcher
#  Запускает лабораторию на доступном языке: Python → Julia → C++
#  Launches the lab in an available language: Python -> Julia -> C++
#
#  ./nsb_lab.sh                 # интерактивное меню / interactive menu
#  ./nsb_lab.sh --run all       # все лаборатории
#  ./nsb_lab.sh --lang julia    # выбрать язык / pick language
#  ./nsb_lab.sh --help
# ============================================================================
set -u

LANG_PREF=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang) LANG_PREF="$2"; shift 2 ;;
        --help|-h)
            echo "NSB LAB 96 launcher"
            echo "  ./nsb_lab.sh                    # auto language, menu"
            echo "  ./nsb_lab.sh --run all          # run all labs"
            echo "  ./nsb_lab.sh --lang julia --run main96"
            echo "  ./nsb_lab.sh --lang python --run matrix"
            echo "  ./nsb_lab.sh --lang cpp    --run kdv"
            exit 0 ;;
        *) ARGS+=("$1"); shift ;;
    esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

have() { command -v "$1" >/dev/null 2>&1; }

# проверка python-зависимости
py_ok() {
    have python3 || return 1
    python3 -c "import numpy" >/dev/null 2>&1 || return 1
    return 0
}

pick() {
    case "$LANG_PREF" in
        python|py)    py_ok     && { echo "python3 nsb_lab.py";  return 0 ;;
                                 echo "python3/numpy не найдены" >&2; return 1 ;; } ;;
        julia|jl)     have julia && { echo "julia nsb_lab.jl";    return 0 ;;
                                 echo "julia не найдена / not found" >&2; return 1 ;; } ;;
        cpp|c++)      [[ -x ./nsb_lab_cpp ]] && { echo "./nsb_lab_cpp"; return 0 ;;
                       have g++ && { echo "BUILD_FIRST"; return 0 ;;
                                     echo "g++ не найден" >&2; return 1 ;; } ;; } ;;
        *)
            py_ok     && { echo "python3 nsb_lab.py";  return 0 ;; }
            have julia && { echo "julia nsb_lab.jl";   return 0 ;; }
            [[ -x ./nsb_lab_cpp ]] && { echo "./nsb_lab_cpp"; return 0 ;; }
            have g++  && { echo "BUILD_FIRST"; return 0 ;; }
            echo "Ни python3+numpy, ни julia, ни g++ не найдены." >&2
            return 1 ;;
    esac
}

CMD="$(pick)" || exit 1
if [[ "$CMD" == "BUILD_FIRST" ]]; then
    echo "Сборка C++-версии... / building C++ edition..."
    g++ -O2 -std=c++17 -o nsb_lab_cpp nsb_lab.cpp || exit 1
    CMD="./nsb_lab_cpp"
fi

echo "==> $CMD ${ARGS[*]:-}"
exec $CMD "${ARGS[@]}"
