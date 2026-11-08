#!/usr/bin/env bash
# NSB Julia Lab — быстрый запуск с автопотоками
cd "$(dirname "$0")"
exec julia -t auto navier_stokes_lab.jl "$@"
