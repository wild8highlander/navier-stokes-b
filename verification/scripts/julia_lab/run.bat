@echo off
rem NSB Julia Lab - quick start
cd /d "%~dp0"
julia --threads=auto navier_stokes_lab.jl %*
