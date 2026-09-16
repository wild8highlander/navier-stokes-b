#!/bin/bash
# run_all.sh — вся цепочка прогонов P1–P6 + графики (последовательно).
# P3 разбит на два вызова (каждый режим ~450 с); повторный вызов подхватывает
# выполненные режимы и финализирует критерии.
set -u
cd "$(dirname "$0")"

echo "=== P1: 3D-микрофизика камеры Вильсона ==="
python3 p1_3d_microphysics.py || echo "P1: FAIL (см. data/results/p1_3d_microphysics.json)"

echo "=== P5: обратная связь капель на поток ==="
python3 p5_droplet_feedback.py || echo "P5: FAIL"

echo "=== P6: универсальность θ_b ==="
python3 p6_b_universality.py || echo "P6: FAIL"

echo "=== P3: Рэлей–Бенар Gr=1e6 (режим 1/2) ==="
python3 p3_buoyancy.py true_nse || echo "P3 true_nse: FAIL"
echo "=== P3: Рэлей–Бенар Gr=1e6 (режим 2/2) ==="
python3 p3_buoyancy.py b_rotation || echo "P3 b_rotation: FAIL"
python3 p3_buoyancy.py            # финализация критериев

echo "=== P2: сеточная сходимость ==="
python3 p2_grid_convergence.py || echo "P2: FAIL"

echo "=== P4: ансамбль σ_y (Re=2000, T=4) ==="
python3 p4_ensemble_sigma_y.py || echo "P4: FAIL"

echo "=== Графики ==="
python3 make_plots.py || echo "plots: FAIL"

echo "=== ГОТОВО: результаты в ../data/results, графики в ../data/plots ==="
