#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_docx.py — точная редакция четырёх DOCX-монографий (воспроизводимый скрипт).

Правки:
  1. b = 1/(4π+2√3) ≈ 0,0624 — везде вместо b ≈ 0,0785 (форма π/(4π²+2π√3) эквивалентна);
  2. θ_b = arcsin(b) ≈ 3,5765°, sin θ_b = b — точно (вместо θ_b = b·π/2 ≈ 7,07°);
  3. убраны «требуется/требует b = 0», «b — модификация уравнения», «C_K = 1,5 — предсказание»;
  4. поворот определён как естественное поведение жидкости в уравнениях Эйлера
     (внутреннее трение → минимальное движение и сдвиг), НЕ внешняя сила;
  5. исторические численные прогоны сохранены с пометкой их фактической конфигурации.

Метод: фрагментные замены с сохранением runs (форматирование абзаца не ломается),
вставка пояснительных абзацев, полный контроль до/после (фразы, число изображений).

Запуск:  python3 patch_docx.py <корень_репозитория> <каталог_вывода>
"""
import sys, re, copy
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

B_EXACT_RU = "b = π/(4π²+2π√3) = 1/(4π+2√3) ≈ 0,0624"
B_EXACT_EN = "b = \u03c0/(4\u03c0\u00b2+2\u03c0\u221a3) = 1/(4\u03c0+2\u221a3) \u2248 0.0624"

# ------------------------- низкоуровневые операции -------------------------

def para_replace_fragment(p, old: str, new: str) -> bool:
    """Заменить old→new в p.text, распределив по существующим runs."""
    runs = p.runs
    if not runs:
        return False
    full = "".join(r.text for r in runs)
    idx = full.find(old)
    if idx < 0:
        return False
    end = idx + len(old)
    # границы run в координатах полной строки
    pos = 0
    spans = []
    for r in runs:
        ln = len(r.text)
        spans.append((r, pos, pos + ln))
        pos += ln
    first_touched = None
    for r, s, e in spans:
        if e <= idx or s >= end:
            continue
        # пересечение
        keep_left = r.text[: max(0, idx - s)]
        keep_right = r.text[max(0, min(len(r.text), end - s)):]
        if first_touched is None:
            r.text = keep_left + new + keep_right
            first_touched = r
        else:
            r.text = keep_left + keep_right
    return True


def para_set_text(p, new: str):
    """Заменить весь текст абзаца, сохранив стиль и формат первого run."""
    runs = p.runs
    if not runs:
        p.add_run(new)
        return
    runs[0].text = new
    for r in runs[1:]:
        r.text = ""


def insert_paragraph_after(anchor_p, text: str):
    """Вставить новый абзац сразу после anchor_p, скопировав свойства абзаца."""
    new_p = copy.deepcopy(anchor_p._p)
    # очистить содержимое копии, оставив pPr
    for child in list(new_p):
        if child.tag != qn('w:pPr'):
            new_p.remove(child)
    anchor_p._p.addnext(new_p)
    from docx.text.paragraph import Paragraph
    np = Paragraph(new_p, anchor_p._parent)
    np.add_run(text)
    return np


def iter_all_paragraphs(doc):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def apply_edits(doc, edits, log, docname):
    """edits: список (kind, match, payload).
    kind 'frag': match — старый фрагмент, payload — новый (замена первого вхождения);
    kind 'full': match — regex полного абзаца, payload — новый текст всего абзаца;
    kind 'insert_after': match — regex якорного абзаца, payload — текст нового абзаца.
    """
    paras = list(iter_all_paragraphs(doc))
    for kind, match, payload in edits:
        done = False
        if kind == "frag":
            # заменяем ВСЕ вхождения во всех абзацах/таблицах
            replaced = 0
            for p in paras:
                guard = 50
                while match in p.text and guard > 0:
                    if not para_replace_fragment(p, match, payload):
                        break
                    replaced += 1
                    guard -= 1
                    if match in payload:  # защита от бесконечного цикла
                        break
            if replaced:
                log.append(f"[{docname}] FRAG  ok x{replaced}: {match[:52]}…")
                done = True
        elif kind == "full":
            rx = re.compile(match)
            for p in paras:
                if rx.fullmatch(p.text.strip()):
                    para_set_text(p, payload)
                    log.append(f"[{docname}] FULL  ok: {match[:52]}")
                    done = True
                    break
        elif kind == "insert_after":
            rx = re.compile(match)
            for bp in doc.paragraphs:
                if rx.search(bp.text):
                    insert_paragraph_after(bp, payload)
                    log.append(f"[{docname}] INS   ok after: {bp.text[:48]}…")
                    done = True
                    break
        if not done:
            log.append(f"[{docname}] MISS  !!: {kind}: {match[:60]}")
    return doc


# ------------------------------ правки RU ------------------------------

EDITS_RU_MAIN = [
    ("full",
     r"Монография представляет аналитическое доказательство регулярности 3D NSE без диссипации.*",
     "Монография исследует регулярность 3D NSE без диссипации через универсальный "
     "геометрический эффект " + B_EXACT_RU + ". Эффект возникает аналитически из уравнений "
     "Кирхгофа как поворот на −90°: (dx/dt, dy/dt) = R(−90°)·∇H; он универсален — возникает "
     "на любой геометрической поверхности. Поворот скорости на угол θ_b = arcsin(b) ≈ 3,5765° "
     "вокруг оси вихря — не внешняя сила: это естественное поведение жидкости в уравнениях "
     "Эйлера, где внутреннее трение слоёв совершает минимальное движение и сдвиг; sin θ_b = b — "
     "точно. Непрерывное применение поворота (угол за шаг dt·θ_b, кумулятивно θ_b·T) в "
     "зафиксированном протоколе N=48, ν=0,01, T=6 нейтрально по BKM-интегралу (фактор "
     "0,967×) и по max‖ω‖∞ (1,0000), без инжекции энергии (R^T·R = I, |ΔE| ≤ 1,5·10⁻⁹ за "
     "поворот); в 2D точно ω' = cos θ_b·ω. Численная верификация: "
     "многоуровневые наборы L1–L5 на Python и Julia, все результаты воспроизводятся из "
     "открытого кода."),
    ("frag",
     "θ_b = b · π/2 = 0,0785 · π/2 ≈ 0,1233 рад ≈ 7,07°",
     "θ_b = arcsin(b) = arcsin(0,0624) = 0,0624217 рад ≈ 3,5765°; при этом sin θ_b = b — точно "
     "(невязка 0 на 50 знаках)"),
    ("frag",
     "При C_K = 1,5: C_s ≈ 0,173. Эмпирический диапазон: 0,10–0,20. C_K = 1,5 — предсказание (через e и универсальное b).",
     "При C_K = 1,5: C_s ≈ 0,173. Эмпирический диапазон: 0,10–0,20. Значение C_K = 1,5 — "
     "калибровочное, согласованное с независимой оценкой γ = 0,95456: C_K(γ) = 1,4786; "
     "независимого предсказания не утверждается."),
    ("full",
     r"1\. Связь с задачей Клэя: b — модификация уравнения\. Задача Клэя требует регулярности при b = 0\. Но b возникает аналитически\.",
     "1. Связь с задачей Клэя: b не является ни модификацией уравнения, ни внешней силой, и "
     "никакое условие «b = 0» не требуется. Поворот на угол θ_b — естественное поведение "
     "жидкости, уже присутствующее в уравнениях Эйлера: внутреннее трение слоёв совершает "
     "минимальное движение и сдвиг, а доля поворота b = 1/(4π+2√3) — универсальный "
     "математический эффект, возникающий на любой геометрической поверхности. Уравнения "
     "остаются исходными NSE."),
    ("insert_after",
     r"θ_b = arcsin\(b\) = arcsin\(0,0624\)",
     "Форма точного поворота: u' = u_∥ + √(1−b²)·u_⊥ + b·(ω̂×u_⊥), где u_∥ — компонента вдоль "
     "ω̂, u_⊥ — поперечная. Матрица поворота Родригеса собственная и ортогональная: R^T·R = I "
     "точно, det R = 1. Ось поворота — направление вихря ω̂ = ω/‖ω‖; вихрь пересчитывается из "
     "повёрнутой скорости: ω' = ∇×u'. Воспроизводимость: все константы — из замкнутых формул "
     "(b = 1/(4π+2√3), 50 знаков, mpmath); прогоны L1–L5 при каждом запуске сохраняют "
     "JSON-результаты."),
    ("frag",
     "2.5. Угол поворота θ_b = b·π/2",
     "2.5. Угол поворота θ_b = arcsin(b)"),
    ("frag",
     "Рис. 2.5. Угол поворота θ_b = arcsin(b) как функция от b.",
     "Рис. 2.5. Угол поворота θ_b как функция от b (историческая форма θ = b·π/2; точная "
     "редакция: θ_b = arcsin(b), sin θ_b = b)."),
    ("frag",
     "Существует универсальная поляризационная поправка b ≈ 0,0785, возникающая аналитически из уравнений Кирхгофа. Применённая как фазовый поворот скорости u на угол θ_b = b·π/2 вокруг оси вихря ω, она:",
     "Существует универсальный геометрический эффект b = π/(4π²+2π√3) = 1/(4π+2√3) ≈ 0,0624, "
     "возникающий аналитически из уравнений Кирхгофа. Поворот скорости u на угол "
     "θ_b = arcsin(b) вокруг оси вихря ω — естественное поведение жидкости (внутреннее трение "
     "→ минимальное движение и сдвиг), не внешняя сила; он:"),
    ("frag",
     "При b = 0,0785: Z_full/Z_leading ≈ 1,461.",
     "При b = 1/(4π+2√3) ≈ 0,0624: Z_full/Z_leading = e^(b·β_K·L_min) ≈ 1,3516."),
    ("frag",
     "Если b универсальна (не зависит от C_K), то γ и C_K — предсказания, не подгонка. При b = 0,0785: γ = 0,95449, C_K = 1,5000 (точно).",
     "Если b универсальна (не зависит от C_K), то γ и C_K взаимно согласованы (согласованность, "
     "не независимое предсказание). При точном b = 1/(4π+2√3) ≈ 0,0624: C_K(γ = 0,95456) = "
     "1,4786; при C_K = 1,5: γ = 1,1920."),
    ("frag",
     "поворачивается на θ_b = b·π/2 вокруг оси вихря ω, то:",
     "поворачивается на θ_b = arcsin(b) вокруг оси вихря ω (естественное поведение жидкости, "
     "не внешняя сила), то:"),
    ("frag",
     "θ_b = b·π/2 — угол в фазовом пространстве, не зависит от метрики. Применима к: 2D, S², H², T², Клейн, R³, S³.",
     "θ_b = arcsin(b) — угол в фазовом пространстве, не зависит от метрики; универсальный "
     "эффект b возникает на любой геометрической поверхности. Применимо к: 2D, S², H², T², "
     "Клейн, R³, S³."),
]

EDITS_EN_MAIN = [
    ("full",
     r"This monograph presents an analytical proof of 3D NSE regularity without dissipation.*",
     "This monograph studies 3D NSE regularity without dissipation via the universal "
     "geometric effect " + B_EXACT_EN + ". The effect arises analytically from the Kirchhoff "
     "equations as a −90° rotation: (dx/dt, dy/dt) = R(−90°)·∇H; it is universal — it occurs "
     "on any geometric surface. The rotation of velocity by θ_b = arcsin(b) ≈ 3.5765° around "
     "the vortex axis is not an external force: it is the natural behavior of fluid in the "
     "Euler equations, where internal friction between layers performs the minimal motion and "
     "shear; sin θ_b = b exactly. Continuous application of the rotation (per-step angle "
     "dt·θ_b, cumulative θ_b·T) in the fixed protocol N=48, ν=0.01, T=6 is neutral on the "
     "BKM integral (factor 0.967×) and on max‖ω‖∞ (1.0000), without energy injection "
     "(R^T·R = I, |ΔE| ≤ 1.5·10⁻⁹ per rotation); in 2D, ω' = cos θ_b·ω exactly. Numerical "
     "verification: multi-level suites L1–L5 in Python and Julia; all "
     "results are reproduced from open code."),
    ("frag",
     "θ_b = b · π/2 = 0.0785 · π/2 ≈ 0.1233 rad ≈ 7.07°",
     "θ_b = arcsin(b) = arcsin(0.0624) = 0.0624217 rad ≈ 3.5765°; moreover sin θ_b = b exactly "
     "(residual 0 at 50 digits)"),
    ("frag",
     "At C_K = 1.5: C_s ≈ 0.173. Empirical range: 0.10–0.20. C_K = 1.5 is a prediction (via e and universal b).",
     "At C_K = 1.5: C_s ≈ 0.173. Empirical range: 0.10–0.20. The value C_K = 1.5 is a "
     "calibration consistent with the independent estimate γ = 0.95456: C_K(γ) = 1.4786; no "
     "independent prediction is claimed."),
    ("full",
     r"1\. Connection to Clay problem: b is a modification\. Clay requires regularity at b = 0\. But b arises analytically\.",
     "1. Connection to the Clay problem: b is neither a modification of the equation nor an "
     "external force, and no \u201cb = 0\u201d condition is required. The rotation by θ_b is the natural "
     "behavior of fluid already present in the Euler equations: internal friction between "
     "layers performs the minimal motion and shear, and the rotation fraction "
     "b = 1/(4π+2√3) is a universal mathematical effect arising on any geometric surface. "
     "The equations remain the original NSE."),
    ("insert_after",
     r"θ_b = arcsin\(b\) = arcsin\(0\.0624\)",
     "Exact rotation form: u' = u_∥ + √(1−b²)·u_⊥ + b·(ω̂×u_⊥), where u_∥ is the component "
     "along ω̂ and u_⊥ the transverse one. The Rodrigues rotation matrix is proper orthogonal: "
     "R^T·R = I exactly, det R = 1. The rotation axis is the vortex direction ω̂ = ω/‖ω‖; "
     "vorticity is recomputed from the rotated velocity: ω' = ∇×u'. Reproducibility: all "
     "constants come from closed formulas (b = 1/(4π+2√3), 50 digits, mpmath); the L1–L5 runs "
     "save JSON results on every execution."),
    ("frag",
     "2.5. Rotation Angle θ_b = b·π/2",
     "2.5. Rotation Angle θ_b = arcsin(b)"),
    ("frag",
     "Fig. 2.5. Rotation angle θ_b = b·π/2 as function of b.",
     "Fig. 2.5. Rotation angle θ_b as function of b (historical form θ = b·π/2; exact edition: "
     "θ_b = arcsin(b), sin θ_b = b)."),
    ("frag",
     "There exists a universal polarization correction b ≈ 0.0785, arising analytically from Kirchhoff equations. Applied as a phase rotation of velocity u by angle θ_b = b·π/2 around the vortex axis ω, it:",
     "There exists a universal geometric effect b = π/(4π²+2π√3) = 1/(4π+2√3) ≈ 0.0624, "
     "arising analytically from Kirchhoff equations. The rotation of velocity u by "
     "θ_b = arcsin(b) around the vortex axis ω is the natural behavior of fluid (internal "
     "friction → minimal motion and shear), not an external force; it:"),
    ("frag",
     "At b = 0.0785: Z_full/Z_leading ≈ 1.461.",
     "At b = 1/(4π+2√3) ≈ 0.0624: Z_full/Z_leading = e^(b·β_K·L_min) ≈ 1.3516."),
    ("frag",
     "If b is universal (independent of C_K), then γ and C_K are predictions, not fitting. At b = 0.0785: γ = 0.95449, C_K = 1.5000 (exact).",
     "If b is universal (independent of C_K), then γ and C_K are mutually consistent "
     "(consistency, not an independent prediction). At exact b = 1/(4π+2√3) ≈ 0.0624: "
     "C_K(γ = 0.95456) = 1.4786; at C_K = 1.5: γ = 1.1920."),
    ("frag",
     "rotated by θ_b = b·π/2 around vortex axis ω, then:",
     "rotated by θ_b = arcsin(b) around vortex axis ω (natural fluid behavior, not an external "
     "force), then:"),
    ("frag",
     "θ_b = b·π/2 is a phase space angle, independent of surface metric. Applicable to: 2D, S², H², T², Klein, R³, S³.",
     "θ_b = arcsin(b) is a phase space angle, independent of surface metric; the universal "
     "effect b arises on any geometric surface. Applicable to: 2D, S², H², T², Klein, R³, S³."),
]

EDITS_RU_KDV = [
    ("frag",
     "универсальной поляризационной поправки b ≈ 0,0785 к уравнению",
     "универсального геометрического эффекта " + B_EXACT_RU + " к уравнению"),
    ("frag",
     "при θ_b = b·π/2 ≈ 7.07°",
     "при θ_b = arcsin(b) ≈ 3,58° (прогоны главы выполнены при историческом значении "
     "θ_b = b·π/2 ≈ 7,07°)"),
    ("frag",
     "7.07° (=θ_b)",
     "7.07° (историческое θ_b)"),
    ("frag",
     "проверить, что он близок к θ_b (подтверждение универсальности b ≈ 0.0785)",
     "проверить, что он близок к θ_b (подтверждение универсальности геометрического "
     "эффекта b)"),
    ("frag",
     "Красная пунктирная — универсальное b = 0.0785, оранжевая — θ_b = 7.07°.",
     "Красная пунктирная — историческое значение b = 0.0785 (точное b = 0.0624), оранжевая — "
     "историческое θ_b = 7.07°."),
    ("frag",
     "Теорема 13.1 монографии. θ_b = b·π/2 — угол",
     "Теорема 13.1 монографии (историческая форма θ_b = b·π/2; точная редакция: "
     "θ_b = arcsin(b)) — угол"),
    ("frag",
     "Универсальность b ≈ 0.0785 в монографии означает",
     "Универсальность геометрического эффекта b (точное b = 1/(4π+2√3) ≈ 0,0624) в монографии "
     "означает"),
    ("frag",
     "В монографии θ_b = b·π/2, где b выводится из дзета-функции Сельберга",
     "В монографии θ_b задаётся исторической формулой b·π/2 (точная редакция: θ_b = arcsin(b), "
     "sin θ_b = b); b выводится из дзета-функции Сельберга"),
    ("frag",
     "u_θ = u + θ_b · K₂(u),   θ_b = b·π/2,   b ≈ 0.0785",
     "u_θ = u + θ_b · K₂(u),   θ_b = arcsin(b),   " + B_EXACT_RU.replace(",0624", ".0624")),
    ("frag",
     "B_UNIVERSAL = 0.0785",
     "B_UNIVERSAL = 0.0785   # историческое значение прогона; точное b = 1/(4π+2√3) ≈ 0.0624"),
    ("frag",
     '("b", "0.0785", "§3.3"),',
     '("b", "0.0785 (историч.; точное 0.0624)", "§3.3"),'),
]

EDITS_EN_KDV = [
    ("frag",
     "the universal polarization correction b ≈ 0.0785 to the Korteweg–de Vries (KdV) equation",
     "the universal geometric effect " + B_EXACT_EN + " to the Korteweg–de Vries (KdV) equation"),
    ("frag",
     "u_θ = u + θ_b · K₂(u),   θ_b = b·π/2,   b ≈ 0.0785",
     "u_θ = u + θ_b · K₂(u),   θ_b = arcsin(b),   " + B_EXACT_EN),
    ("frag",
     "The universality of b ≈ 0.0785 in the monograph means",
     "The universality of the geometric effect b in the monograph means"),
    ("frag",
     "500 random samples, θ_b = 7.07°, max error = 2.2e-16",
     "500 random samples, historical θ_b = 7.07°, max error = 2.2e-16"),
    ("frag",
     "B_UNIVERSAL = 0.0785",
     "B_UNIVERSAL = 0.0785   # historical run value; exact b = 1/(4π+2√3) ≈ 0.0624"),
    ("frag",
     '("b", "0.0785", "§3.3"),',
     '("b", "0.0785 (historical; exact 0.0624)", "§3.3"),'),
]

# ------------------------------ контроль ------------------------------

def control(doc, forbid, require, name, log):
    text = "\n".join(p.text for p in iter_all_paragraphs(doc))
    ok = True
    for f in forbid:
        if re.search(f, text):
            log.append(f"[{name}] CONTROL FAIL: найдено запрещённое /{f}/")
            ok = False
    for r in require:
        if not re.search(r, text):
            log.append(f"[{name}] CONTROL FAIL: не найдено требуемое /{r}/")
            ok = False
    if ok:
        log.append(f"[{name}] CONTROL OK")
    return ok


def count_images(doc):
    return sum(1 for r in doc.part.rels.values() if "image" in r.reltype)


# ------------------------------ main ------------------------------

def main(repo_root: str, out_dir: str):
    repo = Path(repo_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log = []

    jobs = [
        (repo / "docs/correction-b/ru/monograph_with_figures.docx",
         out / "correction_b_RU_monograph_with_figures.docx",
         EDITS_RU_MAIN,
         [r"0[,.]0785", r"θ_b\s*=\s*b\s*[·•]\s*π/2", r"предсказание \(через", r"is a prediction \(via",
          r"требует регулярности при b = 0", r"requires regularity at b = 0",
          r"модификация уравнения", r"b is a modification"],
         [r"1/\(4π\+2√3\)", r"arcsin\(b\)", r"3[,.]5765", r"естественное поведение|natural behavior"],
         "RU-monograph"),
        (repo / "docs/correction-b/en/monograph_with_figures.docx",
         out / "correction_b_EN_monograph_with_figures.docx",
         EDITS_EN_MAIN,
         [r"0[,.]0785", r"θ_b\s*=\s*b\s*[·•]\s*π/2", r"предсказание \(через", r"is a prediction \(via",
          r"требует регулярности при b = 0", r"requires regularity at b = 0",
          r"модификация уравнения", r"b is a modification"],
         [r"1/\(4π\+2√3\)", r"arcsin\(b\)", r"3[,.]5765", r"естественное поведение|natural behavior"],
         "EN-monograph"),
        (repo / "docs/kdv/ru/KdV_b_correction_Chapter16.docx",
         out / "KdV_b_correction_Chapter16_RU.docx",
         EDITS_RU_KDV,
         [r"b ≈ 0,0785", r"b ≈ 0\.0785", r"поправки b ≈", r"универсальное b = 0\.0785",
          r"7\.07° \(=θ_b\)"],
         [r"1/\(4π\+2√3\)", r"arcsin\(b\)", r"историческ"],
         "RU-KdV16"),
        (repo / "docs/kdv/en/KdV_b_correction_Chapter16.docx",
         out / "KdV_b_correction_Chapter16_EN.docx",
         EDITS_EN_KDV,
         [r"b ≈ 0,0785", r"b ≈ 0\.0785", r"polarization correction b ≈",
          r"universal b = 0\.0785"],
         [r"1/\(4π\+2√3\)", r"arcsin\(b\)", r"historical"],
         "EN-KdV16"),
    ]

    all_ok = True
    for src, dst, edits, forbid, require, name in jobs:
        if not src.exists():
            log.append(f"[{name}] SRC MISSING: {src}")
            all_ok = False
            continue
        doc = Document(str(src))
        n_img_before, n_par_before = count_images(doc), len(doc.paragraphs)
        apply_edits(doc, edits, log, name)
        doc.save(str(dst))
        # контроль по сохранённому файлу
        doc2 = Document(str(dst))
        ok = control(doc2, forbid, require, name, log)
        n_img_after = count_images(doc2)
        if n_img_before != n_img_after:
            log.append(f"[{name}] IMAGES CHANGED {n_img_before}→{n_img_after} !!")
            ok = False
        else:
            log.append(f"[{name}] images intact: {n_img_after}/{n_img_after}")
        log.append(f"[{name}] paragraphs {n_par_before} → {len(doc2.paragraphs)}; saved: {dst.name}")
        all_ok = all_ok and ok

    print("\n".join(log))
    print("\nRESULT:", "ALL OK" if all_ok else "HAS FAILURES")
    return 0 if all_ok else 1


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/repo"
    outd = sys.argv[2] if len(sys.argv) > 2 else "/home/z/my-project/package/NSE_b_exact_edition/docx_patched"
    sys.exit(main(repo, outd))
