# 01_i18n.jl — двуязычие RU/EN. Ключ -> (русский, english).
# Переключение языка — цифрой 9 в любом меню (мгновенно).

const NSB_I18N = Dict{String,Tuple{String,String}}()
const NSB_LANG = Ref{Symbol}(:ru)

function nsb_add(k::String, ru::String, en::String)
    NSB_I18N[k] = (ru, en)
    return nothing
end

nsb_setlang!(l::Symbol) = (NSB_LANG[] = (l == :en ? :en : :ru); nothing)
nsb_togglelang!() = (NSB_LANG[] = NSB_LANG[] == :ru ? :en : :ru; nothing)
nsb_lang() = NSB_LANG[]

"Строка по ключу на текущем языке."
function L(k::String)::String
    p = get(NSB_I18N, k, nothing)
    p === nothing && return k
    return NSB_LANG[] == :ru ? p[1] : p[2]
end

"Форматированная строка (Printf-слоты %s %d %.3f …)."
function Lf(k::String, args...)::String
    key = (NSB_LANG[], k)
    fmt = get(NSB_FMT_CACHE, key, nothing)
    if fmt === nothing
        fmt = Printf.Format(L(k))
        NSB_FMT_CACHE[key] = fmt
    end
    return Printf.format(fmt, args...)
end
const NSB_FMT_CACHE = Dict{Tuple{Symbol,String},Printf.Format}()

const NSB_LANGCOL = Dict(:ru => (38, 5, 196), :en => (5, 111, 247))  # (r,g,b) акцент языка

function nsb_init_i18n!()
    empty!(NSB_I18N)
    # ---------- общие ----------
    nsb_add("yes", "да", "yes")
    nsb_add("no", "нет", "no")
    nsb_add("pass", "ПРОЙДЕНО", "PASS")
    nsb_add("fail", "ПРОВАЛЕНО", "FAIL")
    nsb_add("skip", "ПРОПУЩЕНО", "SKIP")
    nsb_add("warn", "ВНИМАНИЕ", "WARN")
    nsb_add("back", "назад", "back")
    nsb_add("exit", "выход", "exit")
    nsb_add("menu_prompt", "Выберите пункт и нажмите Enter", "Choose an item and press Enter")
    nsb_add("invalid_choice", "Нет такого пункта — попробуйте ещё раз", "No such item — try again")
    nsb_add("press_enter", "Enter — продолжить", "Enter — continue")
    nsb_add("lang_toggle", "9. Язык / Language  (RU ↔ EN)", "9. Language / Язык  (EN ↔ RU)")
    nsb_add("lang_switched_ru", "Язык: РУССКИЙ (9 — переключить)", "Language: RUSSIAN (9 — toggle)")
    nsb_add("lang_switched_en", "Language: ENGLISH (9 — toggle)", "Язык: АНГЛИЙСКИЙ (9 — переключить)")
    # ---------- главное меню ----------
    nsb_add("title", "ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ", "NAVIER–STOKES LABORATORY · b-CORRECTION")
    nsb_add("subtitle", "самодостаточная Julia-версия без внешних пакетов", "self-contained Julia edition, zero external packages")
    nsb_add("menu_quick", "1. Быстрый прогон  (≈1–2 мин: мини-сьют + финальный PDF)", "1. Quick run  (≈1–2 min: mini-suite + final PDF)")
    nsb_add("menu_suite_normal", "2. Полная сьют — НОРМАЛЬНЫЙ режим", "2. Full suite — NORMAL mode")
    nsb_add("menu_suite_hard", "3. Полная сьют — ХАРД режим (больше критериев)", "3. Full suite — HARD mode (more criteria)")
    nsb_add("menu_custom", "4. Свой эксперимент (любые N, ν, dt, T, b-коррекция)", "4. Custom experiment (any N, ν, dt, T, b-correction)")
    nsb_add("menu_flows", "5. Лаборатория 20 реальных течений (ураганы, волны, течения)", "5. Real-flows laboratory (20 documented flows)")
    nsb_add("menu_roadmap", "6. Роадмап и это железо (бенчмарк + время расчётов)", "6. Roadmap & this hardware (benchmark + run-time estimates)")
    nsb_add("menu_reports", "7. Отчёты, графики и логи сессии", "7. Session reports, plots and logs")
    nsb_add("menu_settings", "8. Настройки и о проекте", "8. Settings & about")
    nsb_add("menu_exit", "0. Выход", "0. Exit")
    nsb_add("config_line", "конфиг: выход=%s · DPI=%d · зерно=%d · N≤%d · потоков=%d", "config: out=%s · DPI=%d · seed=%d · N≤%d · threads=%d")
    # ---------- сьюты/эксперименты ----------
    nsb_add("exp_tg", "Тейлор–Грин: сходимость и экстраполяция", "Taylor–Green: convergence and extrapolation")
    nsb_add("exp_abc", "ABC (Эйлер): охота за расходимостью", "ABC (Euler): blow-up hunt")
    nsb_add("exp_houluo", "Хоу–Ло: антипараллельные вихревые трубки", "Hou–Luo: anti-parallel vortex tubes")
    nsb_add("exp_baudit", "Аудит b-коррекции: симметрия против точечного пинка", "b-correction audit: symmetry vs pointwise kick")
    nsb_add("exp_scan", "Сканер «сходимость в бесконечность» (λ(t), экстраполяция t*)", "Convergence-to-infinity scanner (λ(t), t* extrapolation)")
    nsb_add("suite_start", "Старт сьюты: режим=%s", "Starting suite: mode=%s")
    nsb_add("suite_done", "Сьют завершена: %d/%d проверок пройдено · %s", "Suite finished: %d/%d checks passed · %s")
    nsb_add("running", "выполняется", "running")
    nsb_add("criterion", "критерий", "criterion")
    nsb_add("criteria_header", "Критерии", "Criteria")
    nsb_add("scope_note", "Область действия: сертификат внутренней согласованности вычисленного решения в расчётном окне, не общая теорема.", "Scope: a certificate of internal consistency of the computed solution within the window, not a general theorem.")
    nsb_add("verdict_ok", "ВЕРДИКТ: все проверки пройдены", "VERDICT: all checks passed")
    nsb_add("verdict_fail", "ВЕРДИКТ: есть проваленные проверки", "VERDICT: some checks failed")
    # ---------- критерии ----------
    nsb_add("ck_divfree", "несжимаемость: max|div u| в машинном пороге", "incompressibility: max|div u| at machine level")
    nsb_add("ck_energy_monotone", "энергия не растёт (вязкое затухание)", "energy non-increasing (viscous decay)")
    nsb_add("ck_energy_conserved", "энергия сохраняется (Эйлер)", "energy conserved (Euler)")
    nsb_add("ck_rk4_order", "измеренный порядок RK4 ≈ 4", "measured RK4 order ≈ 4")
    nsb_add("ck_no_blowup", "признаков конечновременной расходимости нет (BKM ограничен, λ(t) не ускоряется)", "no finite-time blow-up signature (BKM bounded, λ(t) not accelerating)")
    nsb_add("ck_tail_resolved", "спектральный хвост разрешён (уровень ниже порога)", "spectral tail resolved (level below threshold)")
    nsb_add("ck_tail_steepen", "хвост крутеет при N↑ (спектральная сходимость)", "tail steepens with N (spectral convergence)")
    nsb_add("ck_palin_growth", "рост палинстрофии согласован с энстрофией", "palinstrophy growth consistent with enstrophy")
    nsb_add("ck_cfl", "CFL-аудит: dt ≤ 0.5·dx/max|u| на всех шагах", "CFL audit: dt ≤ 0.5·dx/max|u| at all steps")
    nsb_add("ck_symmetry_relabel", "полная симметрия = релебелинг: диагностики совпадают до 1e-12", "full symmetry = relabeling: diagnostics match to 1e-12")
    nsb_add("ck_isometry", "точечный поворот — изометрия: энергия сохранена", "pointwise rotation is an isometry: energy preserved")
    nsb_add("ck_div_break", "точечный поворот ЛОМАЕТ div u = 0 (инъекция задокументирована)", "pointwise rotation BREAKS div u = 0 (injection documented)")
    nsb_add("ck_reproject", "после перепроекции div снова на машинном пороге", "after reprojection div back at machine level")
    nsb_add("ck_b_effect", "b-пинк не снижает sup|ω| — регуляризации нет", "b-kick does not reduce sup|ω| — no regularization")
    nsb_add("ck_abc_doubling", "время удвоения sup|ω| не сокращается к нулю", "sup|ω| doubling time does not shrink to zero")
    nsb_add("ck_hl_growth", "рост sup|ω| измерен; λ(t) оценивается на всю длину окна", "sup|ω| growth measured; λ(t) assessed across the window")
    nsb_add("ck_res_gap", "разрешение: |J_N − J_2N| ≤ 5% J (лестница N→2N)", "resolution: |J_N − J_2N| ≤ 5% of J (N→2N ladder)")
    nsb_add("ck_lambda_fit", "подгонка λ(t): линейный тренд с R² указан честно", "λ(t) fit: linear trend reported with honest R²")
    nsb_add("ck_tstar", "экстраполяция t*: найдена только при устойчивом росте λ", "t* extrapolation: reported only for sustained λ growth")
    nsb_add("ck_stability", "устойчивость: нет NaN/Inf, sup|ω| ограничен", "stability: no NaN/Inf, sup|ω| bounded")
    nsb_add("ck_balance", "баланс энстрофии: dΩ/dt ≈ −2ν·P (остаток мал)", "enstrophy balance: dΩ/dt ≈ −2ν·P (small residual)")
    # ---------- эксперимент: кастом ----------
    nsb_add("custom_hdr", "Свой эксперимент — параметры через Enter (Enter = значение по умолчанию)", "Custom experiment — enter parameters (Enter = default)")
    nsb_add("custom_prompt_n", "сетка N (16/32/64/…) [%d]", "grid N (16/32/64/…) [%d]")
    nsb_add("custom_prompt_nu", "вязкость ν [%.4g]", "viscosity ν [%.4g]")
    nsb_add("custom_prompt_dt", "шаг dt [%.4g]", "time step dt [%.4g]")
    nsb_add("custom_prompt_t", "горизонт T [%.4g]", "horizon T [%.4g]")
    nsb_add("custom_prompt_ic", "начальное поле: 1=Тейлор–Грин 2=ABC 3=Хоу–Ло 4=случайное [1]", "initial field: 1=Taylor–Green 2=ABC 3=Hou–Luo 4=random [1]")
    nsb_add("custom_prompt_b", "b-коррекция: 0=нет 1=полная симметрия 2=точечный пин [0]", "b-correction: 0=none 1=full symmetry 2=pointwise kick [0]")
    nsb_add("custom_prompt_euler", "Эйлер (ν→0 игнорировать вязкость)? 1=да 0=нет [0]", "Euler (ignore viscosity, ν→0)? 1=yes 0=no [0]")
    # ---------- реальные течения ----------
    nsb_add("flows_hdr", "ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов", "REAL-FLOWS LABORATORY — 20 documented flows")
    nsb_add("flows_menu_hint", "Введите номер течения (1–20), a — все по кругу, q — назад", "Enter flow number (1–20), a — run all, q — back")
    nsb_add("flow_card", "КАРТОЧКА ТЕЧЕНИЯ", "FLOW CARD")
    nsb_add("flow_source", "первоисточник/документация", "primary source/documentation")
    nsb_add("flow_params", "документированные величины", "documented quantities")
    nsb_add("flow_derived", "расчётные параметры (модель репозитория)", "derived parameters (repository model)")
    nsb_add("flow_dns", "прямое численное моделирование (DNS)", "direct numerical simulation (DNS)")
    nsb_add("flow_dns_no", "DNS НЕВОЗМОЖНО на любом существующем железе: нужно N ≈ %s узлов (~%s памяти)", "DNS is INFEASIBLE on any existing hardware: requires N ≈ %s grid points (~%s of memory)")
    nsb_add("flow_dns_verdict", "DNS недостижим — редуцированная модель обязательна", "DNS infeasible — reduced model required")
    nsb_add("flow_dns_ok", "DNS возможно: N = %d укладывается в память", "DNS feasible: N = %d fits in memory")
    nsb_add("flow_reduced", "редуцированная модель запускается", "reduced model launched")
    nsb_add("flow_bcorr", "b-коррекция ON/OFF", "b-correction ON/OFF")
    nsb_add("flow_verdict", "ВЕРДИКТ ПО ТЕЧЕНИЮ", "FLOW VERDICT")
    nsb_add("flow_all_hdr", "СВОДНАЯ ТАБЛИЦА 20 ТЕЧЕНИЙ", "SUMMARY TABLE OF 20 FLOWS")
    nsb_add("flow_missing_data", "частично: параметр(ы) вне документации — отмечены «?»", "partial: parameter(s) outside documentation — marked «?»")
    # ---------- роадмап ----------
    nsb_add("road_hdr", "РОАДМАП v0.2–v0.5 И ЭТО ЖЕЛЕЗО", "ROADMAP v0.2–v0.5 AND THIS HARDWARE")
    nsb_add("road_bench", "Бенчмарк собственного FFT (radix-2, потоки=%d)", "In-house FFT benchmark (radix-2, threads=%d)")
    nsb_add("road_gflops", "измеренная производительность 3D-FFT: %.1f GFLOP/с", "measured 3D-FFT throughput: %.1f GFLOP/s")
    nsb_add("road_tbl_hdr", "Оценки для псевдоспектрального НС (RK4, ~13 3D-FFT/шаг)", "Estimates for pseudospectral NS (RK4, ~13 3D-FFTs/step)")
    nsb_add("road_mem", "память", "memory")
    nsb_add("road_per_step", "сек/шаг", "s/step")
    nsb_add("road_verdict_laptop", "ноутбук: реально за вечер", "laptop: an evening run")
    nsb_add("road_verdict_ws", "нужна рабочая станция (или ночь на ноутбуке)", "workstation recommended (or overnight on a laptop)")
    nsb_add("road_verdict_hpc", "нужен кластер/HPC", "cluster/HPC required")
    nsb_add("road_verdict_no", "вне досягаемости одиночной машины", "out of reach for a single machine")
    nsb_add("road_github", "GitHub Actions (2 ядра): только смоук N≤32", "GitHub Actions (2 cores): smoke N≤32 only")
    # ---------- отчёты ----------
    nsb_add("rep_hdr", "ОТЧЁТЫ СЕССИИ", "SESSION REPORTS")
    nsb_add("rep_none", "Пока ничего не посчитано — запустите быстрый прогон (п. 1)", "Nothing computed yet — start the quick run (item 1)")
    nsb_add("rep_saved", "Сохранено", "Saved")
    nsb_add("rep_final_pdf", "финальный мини-отчёт (PDF)", "final mini-article (PDF)")
    nsb_add("rep_formats", "форматы: TXT · MD · CSV · JSON · HTML+SVG · PDF", "formats: TXT · MD · CSV · JSON · HTML+SVG · PDF")
    nsb_add("rep_generating", "Генерация финального отчёта…", "Generating final report…")
    nsb_add("rep_done", "Готово.", "Done.")
    # ---------- настройки ----------
    nsb_add("set_hdr", "НАСТРОЙКИ", "SETTINGS")
    nsb_add("set_dpi", "Текущее DPI графиков", "Current plots DPI")
    nsb_add("set_dpi_new", "Новое DPI (300/600/1200)", "New DPI (300/600/1200)")
    nsb_add("set_out", "Папка результатов", "Results folder")
    nsb_add("set_about", "О ПРОЕКТЕ", "ABOUT")
    nsb_add("set_about_txt", "Лаборатория проверяет гипотезу b-коррекции репозитория navier-stokes-b:\nполная решётчатая симметрия u' = R u(R⁻¹x) — релебелинг и не может влиять\nна единственность/регулярность; точечный поворот u' = R u(x) сохраняет энергию,\nно ломает div u = 0. Всё считается без единого внешнего пакета.", "The lab tests the navier-stokes-b repository's b-correction hypothesis:\nfull lattice symmetry u' = R u(R⁻¹x) is a relabeling and cannot affect\nuniqueness/regularity; the pointwise rotation u' = R u(x) preserves energy\nbut breaks div u = 0. Everything is computed without a single external package.")
    # ---------- pager ----------
    nsb_add("pager_hint", "── Enter/пробел: дальше · b: назад · q: завершить просмотр ──", "── Enter/space: next · b: back · q: quit view ──")
    nsb_add("pager_more", "… ещё %d строк", "… %d more lines")
    nsb_add("pager_end", "── конец (%d строк) ──", "── end (%d lines) ──")
    # ---------- прогресс ----------
    nsb_add("prog_step", "шаг", "step")
    nsb_add("prog_rate", "шаг/с", "steps/s")
    nsb_add("prog_eta", "осталось", "ETA")
    nsb_add("prog_elapsed", "прошло", "elapsed")
    # ---------- терминальная картинка ----------
    nsb_add("termimg_caption", "срез завихренности |ω|(x,y), терминальный превью", "vorticity slice |ω|(x,y), terminal preview")
    # ---------- финальный PDF ----------
    nsb_add("art_title", "Вычислительная проверка гипотезы b-коррекции", "Computational audit of the b-correction hypothesis")
    nsb_add("art_sub", "автономная Julia-лаборатория репозитория navier-stokes-b", "self-contained Julia laboratory of the navier-stokes-b repository")
    nsb_add("art_abstract", "Аннотация", "Abstract")
    nsb_add("art_methods", "Методы", "Methods")
    nsb_add("art_results", "Результаты", "Results")
    nsb_add("art_flows", "Реальные течения", "Real flows")
    nsb_add("art_roadmap", "Вычислительные потребности роадмапа", "Computational needs of the roadmap")
    nsb_add("art_concl", "Выводы", "Conclusions")
    nsb_add("art_appendix", "Приложение: параметры прогонов", "Appendix: run parameters")
    # ---------- прочее ----------
    nsb_add("quit_bye", "Лаборатория завершена. Отчёты: %s", "Laboratory finished. Reports: %s")
    nsb_add("interrupted", "Прервано пользователем.", "Interrupted by user.")
    nsb_add("enter_number", "→ число", "→ number")
    nsb_add("bad_number", "не число — повторите", "not a number — retry")
    return nothing
end
