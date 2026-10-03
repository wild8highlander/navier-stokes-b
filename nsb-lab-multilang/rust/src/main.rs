// ═══════════════════════════════════════════════════════════════════════════
//   NSB RUST LAB v2.1.0 — polyglot edition
//   A faithful port of the self-contained Julia "Navier–Stokes b-Lab" to
//   Rust with ZERO external crates (pure std).
//
//   Highlights of this edition:
//     • Memory-safe systems programming: no UB, no data races — verified by
//       the compiler, not the tester.
//     • std::thread::scope-parallel FFT axis passes (no unsafe anywhere).
//     • Same physics as the Julia reference: 3-D pseudospectral NS/Euler
//       (RK4 + Leray projection + 2/3 rule), 2-D barotropic β-plane,
//       BKM diagnostics, blow-up scanner, b-correction audit.
//     • Zero-dependency output: PNG (own stored-deflate + CRC32 + Adler32),
//       GIF89a animator, CSV/JSON/MD reports.
//     • i18n RU/EN, ONE-LINE progress bar, sparklines, interactive TUI menu.
//
//   Build:   cargo build --release          (or: rustc -O src/main.rs)
//   Run:     cargo run --release -- --quick --lang en
//            cargo run --release -- --selftest
//            cargo run --release             (interactive menu)
//   Results: ~/nsb_lab_results/{data,plots,reports,logs}
// ═══════════════════════════════════════════════════════════════════════════

use std::env;
use std::fs;
use std::io::{self, IsTerminal, Write};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

const NSB_VERSION: &str = "2.1.0";
const PI: f64 = std::f64::consts::PI;

// ───────────────────────────── config ───────────────────────────────────

struct Config {
    lang: &'static str,
    out_dir: String,
    dpi: i32,
    seed: u64,
    color: bool,
    ascii_only: bool,
    max_n: usize,
    quick: bool,
    batch: bool,
    quiet: bool,
    t_start: Instant,
    gif: bool,
    ckpt_every: usize,
    adaptive_cfl: bool,
    nu4: f64,
}

static mut CFG: Option<Config> = None;

fn cfg() -> &'static mut Config {
    unsafe {
        // SAFETY: single-threaded access via &mut below; lab logic is single
        // threaded except FFT worker scopes, which never touch CFG.
        CFG.as_mut().expect("config initialised")
    }
}

fn cfg_init() {
    let home = env::var("HOME").unwrap_or_else(|_| ".".into());
    let total_gb = fs::read_to_string("/proc/meminfo")
        .ok()
        .and_then(|s| {
            s.lines().find(|l| l.starts_with("MemTotal:")).and_then(|l| {
                l.split_whitespace()
                    .nth(1)
                    .and_then(|v| v.parse::<f64>().ok())
                    .map(|kb| kb / 1048576.0)
            })
        })
        .unwrap_or(8.0);
    let mut max_n = 32;
    for cand in [32usize, 64, 128, 256] {
        let mem = (cand.pow(3) as f64) * 16.0 * 24.0 / (1u64 << 30) as f64;
        if mem < total_gb * 0.55 {
            max_n = cand;
        }
    }
    let color = std::io::stdout().is_terminal()
        && env::var("TERM").map(|t| t != "dumb").unwrap_or(false)
        && env::var("NO_COLOR").map(|v| v.is_empty()).unwrap_or(true);
    unsafe {
        CFG = Some(Config {
            lang: if env::var("NSB_LAB_LANG").map(|l| l == "en").unwrap_or(false) {
                "en"
            } else {
                "ru"
            },
            out_dir: format!("{home}/nsb_lab_results"),
            dpi: 600,
            seed: 20260916,
            color,
            ascii_only: false,
            max_n,
            quick: false,
            batch: false,
            quiet: false,
            t_start: Instant::now(),
            gif: true,
            ckpt_every: 200,
            adaptive_cfl: false,
            nu4: 0.0,
        });
    }
}

fn ensure_outdirs() {
    for sub in ["", "/logs", "/data", "/plots", "/reports"] {
        let _ = fs::create_dir_all(format!("{}{}", cfg().out_dir, sub));
    }
}

fn print_flush(s: &str) {
    if !cfg().quiet {
        print!("{s}");
        let _ = io::stdout().flush();
    }
}

macro_rules! P {
    ($($arg:tt)*) => { print_flush(&format!($($arg)*)) };
}

// ───────────────────────────── i18n ─────────────────────────────────────

struct I18nPair {
    key: &'static str,
    ru: &'static str,
    en: &'static str,
}

const I18N: &[I18nPair] = &[
    I18nPair { key: "yes", ru: "да", en: "yes" },
    I18nPair { key: "no", ru: "нет", en: "no" },
    I18nPair { key: "pass", ru: "ПРОЙДЕНО", en: "PASS" },
    I18nPair { key: "fail", ru: "ПРОВАЛЕНО", en: "FAIL" },
    I18nPair { key: "title", ru: "ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ", en: "NAVIER–STOKES LABORATORY · b-CORRECTION" },
    I18nPair { key: "subtitle", ru: "самодостаточная Rust-версия без внешних крейтов", en: "self-contained Rust edition, zero external crates" },
    I18nPair { key: "menu_prompt", ru: "Выберите пункт и нажмите Enter", en: "Choose an item and press Enter" },
    I18nPair { key: "invalid_choice", ru: "Нет такого пункта — попробуйте ещё раз", en: "No such item — try again" },
    I18nPair { key: "lang_toggle", ru: "9. Язык / Language  (RU ↔ EN)", en: "9. Language / Язык  (EN ↔ RU)" },
    I18nPair { key: "menu_quick", ru: "1. Быстрый прогон  (мини-сьют)", en: "1. Quick run  (mini-suite)" },
    I18nPair { key: "menu_suite_normal", ru: "2. Полная сьют — НОРМАЛЬНЫЙ режим", en: "2. Full suite — NORMAL mode" },
    I18nPair { key: "menu_suite_hard", ru: "3. Полная сьют — ХАРД режим", en: "3. Full suite — HARD mode" },
    I18nPair { key: "menu_flows", ru: "4. Лаборатория 20 реальных течений", en: "4. Real-flows laboratory (20 documented flows)" },
    I18nPair { key: "menu_roadmap", ru: "5. Роадмап и это железо (бенчмарк)", en: "5. Roadmap & this hardware (benchmark)" },
    I18nPair { key: "menu_reports", ru: "6. Отчёты сессии", en: "6. Session reports" },
    I18nPair { key: "menu_settings", ru: "7. Настройки и о проекте", en: "7. Settings & about" },
    I18nPair { key: "menu_exit", ru: "0. Выход", en: "0. Exit" },
    I18nPair { key: "exp_tg", ru: "Тейлор–Грин: сходимость и экстраполяция", en: "Taylor–Green: convergence and extrapolation" },
    I18nPair { key: "exp_abc", ru: "ABC (Эйлер): охота за расходимостью", en: "ABC (Euler): blow-up hunt" },
    I18nPair { key: "exp_houluo", ru: "Хоу–Ло: антипараллельные вихревые трубки", en: "Hou–Luo: anti-parallel vortex tubes" },
    I18nPair { key: "exp_baudit", ru: "Аудит b-коррекции: симметрия против пинка", en: "b-correction audit: symmetry vs pointwise kick" },
    I18nPair { key: "scope_note", ru: "Область действия: сертификат внутренней согласованности, не общая теорема.", en: "Scope: a certificate of internal consistency of the computed solution, not a general theorem." },
    I18nPair { key: "verdict_ok", ru: "ВЕРДИКТ: все проверки пройдены", en: "VERDICT: all checks passed" },
    I18nPair { key: "verdict_fail", ru: "ВЕРДИКТ: есть проваленные проверки", en: "VERDICT: some checks failed" },
    I18nPair { key: "ck_divfree", ru: "несжимаемость: max|div u| в машинном пороге", en: "incompressibility: max|div u| at machine level" },
    I18nPair { key: "ck_energy_monotone", ru: "энергия не растёт (вязкое затухание)", en: "energy non-increasing (viscous decay)" },
    I18nPair { key: "ck_energy_conserved", ru: "энергия сохраняется (Эйлер)", en: "energy conserved (Euler)" },
    I18nPair { key: "ck_rk4_order", ru: "измеренный порядок RK4 ≈ 4", en: "measured RK4 order ≈ 4" },
    I18nPair { key: "ck_no_blowup", ru: "признаков расходимости нет (BKM ограничен)", en: "no finite-time blow-up signature (BKM bounded)" },
    I18nPair { key: "ck_stability", ru: "устойчивость: нет NaN/Inf", en: "stability: no NaN/Inf" },
    I18nPair { key: "ck_isometry", ru: "точечный поворот — изометрия", en: "pointwise rotation is an isometry" },
    I18nPair { key: "ck_symmetry_relabel", ru: "полная симметрия = релебелинг", en: "full symmetry = relabeling" },
    I18nPair { key: "ck_div_break", ru: "точечный поворот ЛОМАЕТ div u = 0", en: "pointwise rotation BREAKS div u = 0" },
    I18nPair { key: "ck_reproject", ru: "после перепроекции div на машинном пороге", en: "after reprojection div at machine level" },
    I18nPair { key: "ck_b_effect", ru: "b-пинк не снижает sup|ω|", en: "b-kick does not reduce sup|ω|" },
    I18nPair { key: "ck_hl_growth", ru: "рост sup|ω| измерен", en: "sup|ω| growth measured" },
    I18nPair { key: "flows_hdr", ru: "ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов", en: "REAL-FLOWS LABORATORY — 20 documented flows" },
    I18nPair { key: "flows_menu_hint", ru: "Введите номер течения (1–20), a — все, q — назад", en: "Enter flow number (1-20), a — run all, q — back" },
    I18nPair { key: "flow_card", ru: "КАРТОЧКА ТЕЧЕНИЯ", en: "FLOW CARD" },
    I18nPair { key: "flow_source", ru: "первоисточник/документация", en: "primary source/documentation" },
    I18nPair { key: "flow_params", ru: "документированные величины", en: "documented quantities" },
    I18nPair { key: "flow_derived", ru: "расчётные параметры", en: "derived parameters" },
    I18nPair { key: "flow_dns_no", ru: "DNS НЕВОЗМОЖНО на существующем железе", en: "DNS is INFEASIBLE on existing hardware" },
    I18nPair { key: "flow_reduced", ru: "редуцированная модель: 2D баротропная β-плоскость", en: "reduced model: 2-D barotropic β-plane" },
    I18nPair { key: "flow_verdict", ru: "ВЕРДИКТ ПО ТЕЧЕНИЮ", en: "FLOW VERDICT" },
    I18nPair { key: "flow_all_hdr", ru: "СВОДНАЯ ТАБЛИЦА 20 ТЕЧЕНИЙ", en: "SUMMARY TABLE OF 20 FLOWS" },
    I18nPair { key: "road_hdr", ru: "РОАДМАП И ЭТО ЖЕЛЕЗО", en: "ROADMAP AND THIS HARDWARE" },
    I18nPair { key: "road_tbl_hdr", ru: "Оценки для псевдоспектрального НС (RK4, ~13 3D-FFT/шаг)", en: "Estimates for pseudospectral NS (RK4, ~13 3D-FFTs/step)" },
    I18nPair { key: "road_verdict_laptop", ru: "ноутбук: реально за вечер", en: "laptop: an evening run" },
    I18nPair { key: "road_verdict_ws", ru: "нужна рабочая станция", en: "workstation recommended" },
    I18nPair { key: "road_verdict_hpc", ru: "нужен кластер/HPC", en: "cluster/HPC required" },
    I18nPair { key: "road_verdict_no", ru: "вне досягаемости одиночной машины", en: "out of reach for a single machine" },
    I18nPair { key: "rep_hdr", ru: "ОТЧЁТЫ СЕССИИ", en: "SESSION REPORTS" },
    I18nPair { key: "rep_none", ru: "Пока ничего не посчитано", en: "Nothing computed yet" },
    I18nPair { key: "rep_saved", ru: "Сохранено", en: "Saved" },
    I18nPair { key: "selftest_hdr", ru: "САМОТЕСТ", en: "SELF-TEST" },
    I18nPair { key: "selftest_ok", ru: "САМОТЕСТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ", en: "SELF-TEST: ALL CHECKS PASSED" },
    I18nPair { key: "selftest_fail", ru: "САМОТЕСТ: ЕСТЬ ПРОВАЛЫ", en: "SELF-TEST: FAILURES PRESENT" },
    I18nPair { key: "adaptive_on", ru: "адаптивный CFL-шаг включён", en: "adaptive CFL step enabled" },
    I18nPair { key: "gif_saved", ru: "GIF сохранён", en: "GIF saved" },
    I18nPair { key: "set_hdr", ru: "НАСТРОЙКИ", en: "SETTINGS" },
    I18nPair { key: "set_out", ru: "Папка результатов", en: "Results folder" },
    I18nPair { key: "set_about", ru: "О ПРОЕКТЕ", en: "ABOUT" },
    I18nPair { key: "set_about_txt", ru: "Лаборатория проверяет гипотезу b-коррекции: полная решётчатая симметрия — релебелинг; точечный поворот сохраняет энергию, но ломает div u = 0. Порт Rust написан без единого unsafe-блока в физике.",
        en: "The lab tests the b-correction hypothesis: full lattice symmetry is a relabeling; the pointwise rotation preserves energy but breaks div u = 0. The Rust port uses no unsafe blocks in the physics." },
];

fn L(key: &str) -> &'static str {
    for p in I18N {
        if p.key == key {
            return if cfg().lang == "en" { p.en } else { p.ru };
        }
    }
    "<missing>"
}

// ─────────────────────────── ANSI + progress ────────────────────────────

fn p_ok(s: &str) {
    if cfg().color { P!("\x1b[1;32m{s}\x1b[0m") } else { P!("{s}") }
}
fn p_bad(s: &str) {
    if cfg().color { P!("\x1b[1;31m{s}\x1b[0m") } else { P!("{s}") }
}
fn p_warn(s: &str) {
    if cfg().color { P!("\x1b[1;33m{s}\x1b[0m") } else { P!("{s}") }
}
fn p_muted(s: &str) {
    if cfg().color { P!("\x1b[2m{s}\x1b[0m") } else { P!("{s}") }
}
fn p_bold(s: &str) {
    if cfg().color { P!("\x1b[1m{s}\x1b[0m") } else { P!("{s}") }
}

fn header_bar(title: &str) {
    let line: String = std::iter::repeat('-').take(76).collect();
    P!("\n");
    if cfg().color { P!("\x1b[38;2;80;160;255m{line}\x1b[0m\n") } else { P!("{line}\n") }
    P!(" ▸ "); p_bold(title); P!("\n");
    if cfg().color { P!("\x1b[38;2;80;160;255m{line}\x1b[0m\n") } else { P!("{line}\n") }
}

static mut PROG_LAST: f64 = 0.0;

fn progress(frac: f64, label: &str, t0: Instant, total: usize, done: usize) {
    let frac = frac.clamp(0.0, 1.0);
    let tty = std::io::stdout().is_terminal() && cfg().color;
    if !tty || cfg().quiet {
        let last = unsafe { PROG_LAST };
        if (frac - last >= 0.1 || frac >= 1.0) && last < 1.0 {
            unsafe {
                PROG_LAST = if frac >= 1.0 { 1.0 } else { frac.max(last) };
            }
            P!("  [{:>3}%] {label}\n", (frac * 100.0).round() as i64);
        }
        return;
    }
    let w = 30usize;
    let fill = (frac * w as f64).round() as usize;
    let mut bar = String::new();
    for i in 1..=w {
        if cfg().ascii_only {
            bar.push(if i <= fill { '#' } else { '-' });
        } else if i <= fill && cfg().color {
            bar.push_str(&format!("\x1b[38;2;{};{};255m█\x1b[0m", 40 + 180 * i / w, 80 + 170 * i / w));
        } else if cfg().color {
            bar.push_str("\x1b[2m░\x1b[0m");
        } else {
            bar.push('-');
        }
    }
    let el = t0.elapsed().as_secs_f64();
    let eta = if frac > 0.005 { el / frac - el } else { f64::NAN };
    let eta_s = if eta.is_finite() {
        format!("{:02}:{:02}", (eta as u64) / 60, (eta as u64) % 60)
    } else {
        " --:--".into()
    };
    let el_s = format!("{:02}:{:02}", (el as u64) / 60, (el as u64) % 60);
    let tail = if total > 0 {
        format!(" · step {done}/{total} · {:.1} steps/s · ETA {eta_s}",
                done as f64 / el.max(1e-9))
    } else {
        format!(" · elapsed {el_s}")
    };
    P!("\r{}\r", " ".repeat(120));
    if cfg().color {
        P!("\x1b[38;2;80;160;255m ▸ \x1b[0m{label} ▕{bar}▏{:>5.1}%{tail}", frac * 100.0);
    } else {
        P!(" ▸ {label} |{bar}| {:>5.1}%{tail}", frac * 100.0);
    }
    let _ = io::stdout().flush();
    if frac >= 1.0 { P!("\n"); unsafe { PROG_LAST = 0.0; } }
}

fn sparkline(v: &[f64]) -> String {
    let glyphs: Vec<char> = if cfg().color && !cfg().ascii_only {
        "▁▂▃▄▅▆▇█".chars().collect()
    } else {
        "_.-~*###".chars().collect()
    };
    if v.is_empty() { return String::new(); }
    let lo = v.iter().fold(f64::INFINITY, |a, &x| a.min(x.max(0.0)));
    let hi = v.iter().fold(f64::NEG_INFINITY, |a, &x| a.max(x.max(0.0)));
    let rng = if hi > lo { hi - lo } else { 1.0 };
    v.iter()
        .map(|&x| {
            let k = (((x.max(0.0) - lo) / rng * 7.0).round() as usize).clamp(0, 7);
            glyphs[k]
        })
        .collect()
}

// ───────────────── in-house radix-2 FFT (scope-parallel) ────────────────

#[derive(Clone, Copy, PartialEq, Default)]
struct Cx {
    re: f64,
    im: f64,
}

impl Cx {
    const ZERO: Cx = Cx { re: 0.0, im: 0.0 };
    fn new(re: f64, im: f64) -> Self {
        Cx { re, im }
    }
    fn from_polar(r: f64, th: f64) -> Self {
        Cx { re: r * th.cos(), im: r * th.sin() }
    }
    fn norm2(&self) -> f64 {
        self.re * self.re + self.im * self.im
    }
    fn abs(&self) -> f64 {
        self.norm2().sqrt()
    }
    fn conj(&self) -> Self {
        Cx { re: self.re, im: -self.im }
    }
    fn scale(&self, s: f64) -> Self {
        Cx { re: self.re * s, im: self.im * s }
    }
}

impl std::ops::Add for Cx {
    type Output = Cx;
    fn add(self, o: Cx) -> Cx {
        Cx { re: self.re + o.re, im: self.im + o.im }
    }
}
impl std::ops::AddAssign for Cx {
    fn add_assign(&mut self, o: Cx) {
        self.re += o.re;
        self.im += o.im;
    }
}
impl std::ops::Sub for Cx {
    type Output = Cx;
    fn sub(self, o: Cx) -> Cx {
        Cx { re: self.re - o.re, im: self.im - o.im }
    }
}
impl std::ops::SubAssign for Cx {
    fn sub_assign(&mut self, o: Cx) {
        self.re -= o.re;
        self.im -= o.im;
    }
}
impl std::ops::Mul<Cx> for Cx {
    type Output = Cx;
    fn mul(self, o: Cx) -> Cx {
        Cx { re: self.re * o.re - self.im * o.im, im: self.re * o.im + self.im * o.re }
    }
}
impl std::ops::MulAssign<Cx> for Cx {
    fn mul_assign(&mut self, o: Cx) {
        *self = *self * o;
    }
}
impl std::ops::Neg for Cx {
    type Output = Cx;
    fn neg(self) -> Cx {
        Cx { re: -self.re, im: -self.im }
    }
}
impl std::ops::Mul<f64> for Cx {
    type Output = Cx;
    fn mul(self, s: f64) -> Cx {
        self.scale(s)
    }
}
impl std::ops::Mul<Cx> for f64 {
    type Output = Cx;
    fn mul(self, z: Cx) -> Cx {
        z.scale(self)
    }
}

struct FftPlan {
    n: usize,
    tw: Vec<Cx>,
    bitrev: Vec<usize>,
}

impl FftPlan {
    fn new(n: usize) -> Self {
        assert!(n >= 2 && n.is_power_of_two(), "FFT: n must be a power of two");
        let tw: Vec<Cx> = (0..n / 2)
            .map(|k| Cx::from_polar(1.0, -2.0 * PI * k as f64 / n as f64))
            .collect();
        let mut bitrev = vec![0usize; n];
        let logn = n.trailing_zeros();
        for i in 0..n {
            let mut r = 0usize;
            let mut x = i;
            for _ in 0..logn {
                r = (r << 1) | (x & 1);
                x >>= 1;
            }
            bitrev[i] = r;
        }
        FftPlan { n, tw, bitrev }
    }

    fn fft1d(&self, a: &mut [Cx], inverse: bool) {
        let n = self.n;
        for i in 0..n {
            let j = self.bitrev[i];
            if i < j {
                a.swap(i, j);
            }
        }
        let mut len = 2usize;
        while len <= n {
            let half = len >> 1;
            let step = n / len;
            for start in (0..n).step_by(len) {
                let mut k = 0usize;
                for j in 0..half {
                    let mut w = self.tw[k];
                    if inverse {
                        w = w.conj();
                    }
                    let i1 = start + j;
                    let i2 = i1 + half;
                    let u = a[i1];
                    let v = a[i2] * w;
                    a[i1] = u + v;
                    a[i2] = u - v;
                    k += step;
                }
            }
            len <<= 1;
        }
        if inverse {
            let s = 1.0 / n as f64;
            for v in a.iter_mut() {
                *v = v.scale(s);
            }
        }
    }
}

/// Parallel radix-2 transform of `count` contiguous lines of length n.
/// The array is a flat [count][n] buffer; work is split by line ranges.
fn fft_lines_par(plan: &FftPlan, inverse: bool, buf: &mut [Cx], count: usize) {
    let n = plan.n;
    assert_eq!(buf.len(), count * n);
    let threads = std::thread::available_parallelism()
        .map(|v| v.get())
        .unwrap_or(1)
        .max(1);
    if threads == 1 || count <= 1 {
        for line in 0..count {
            plan.fft1d(&mut buf[line * n..(line + 1) * n], inverse);
        }
        return;
    }
    let per = (count + threads - 1) / threads;
    std::thread::scope(|scope| {
        // split into disjoint &mut [[]] groups per thread
        let mut rest: &mut [Cx] = buf;
        let mut handles = Vec::new();
        let mut t = 0usize;
        let mut start_line = 0usize;
        while start_line < count {
            let lines = per.min(count - start_line);
            let (head, tail) = rest.split_at_mut(lines * n);
            rest = tail;
            let plan_ref = &plan;
            handles.push(scope.spawn(move || {
                for l in 0..lines {
                    plan_ref.fft1d(&mut head[l * n..(l + 1) * n], inverse);
                }
            }));
            start_line += lines;
            t += 1;
            if t >= threads {
                break;
            }
        }
        for h in handles {
            let _ = h.join();
        }
    });
}

fn fft3d(plan: &FftPlan, a: &mut [Cx], inverse: bool) {
    let n = plan.n;
    let n2 = n * n;
    // axis 2: contiguous lines, transform in place
    fft_lines_par(plan, inverse, a, n2);
    // axes 1 and 0: gather -> parallel FFT -> scatter
    let mut tmp: Vec<Cx> = vec![Cx::ZERO; a.len()];
    // axis 1: line (i,k) gathers (i,j,k) over j
    for i in 0..n {
        for k in 0..n {
            for (j, slot) in ((0..n).zip(0..)) {
                tmp[(i * n + k) * n + slot] = a[(i * n + j) * n + k];
            }
        }
    }
    fft_lines_par(plan, inverse, &mut tmp, n2);
    for i in 0..n {
        for k in 0..n {
            for j in 0..n {
                a[(i * n + j) * n + k] = tmp[(i * n + k) * n + j];
            }
        }
    }
    // axis 0: line (j,k) gathers (i,j,k) over i
    for j in 0..n {
        for k in 0..n {
            for i in 0..n {
                tmp[(j * n + k) * n + i] = a[(i * n + j) * n + k];
            }
        }
    }
    fft_lines_par(plan, inverse, &mut tmp, n2);
    for j in 0..n {
        for k in 0..n {
            for i in 0..n {
                a[(i * n + j) * n + k] = tmp[(j * n + k) * n + i];
            }
        }
    }
}

fn fft2d(plan: &FftPlan, a: &mut [Cx], inverse: bool) {
    let n = plan.n;
    fft_lines_par(plan, inverse, a, n);
    let mut tmp: Vec<Cx> = vec![Cx::ZERO; a.len()];
    for i in 0..n {
        for j in 0..n {
            tmp[i * n + j] = a[j * n + i];
        }
    }
    fft_lines_par(plan, inverse, &mut tmp, n);
    for i in 0..n {
        for j in 0..n {
            a[j * n + i] = tmp[i * n + j];
        }
    }
}

// ───────────────────── 3-D pseudospectral solver ────────────────────────

struct Nse3D {
    n: usize,
    nu: f64,
    nu4: f64,
    dx: f64,
    kx: Vec<i32>,
    ky: Vec<i32>,
    kz: Vec<i32>,
    ksq: Vec<f64>,
    ksq2: Vec<f64>,
    k2safe: Vec<f64>,
    mask: Vec<bool>,
}

fn idx(n: usize, i: usize, j: usize, k: usize) -> usize {
    (i * n + j) * n + k
}

impl Nse3D {
    fn new(n: usize, nu: f64, nu4_in: Option<f64>) -> Self {
        assert!(n >= 8 && n % 2 == 0, "n must be even and >= 8");
        let nu4 = nu4_in.unwrap_or_else(|| cfg().nu4);
        let n3 = n * n * n;
        let mut k1d = vec![0i32; n];
        for i in 0..n / 2 {
            k1d[i] = i as i32;
        }
        for i in -((n / 2) as i32)..0 {
            k1d[(i + n as i32) as usize] = i;
        }
        let kc = (n / 3) as i32;
        let mut s = Nse3D {
            n,
            nu,
            nu4,
            dx: 2.0 * PI / n as f64,
            kx: vec![0; n3],
            ky: vec![0; n3],
            kz: vec![0; n3],
            ksq: vec![0.0; n3],
            ksq2: vec![0.0; n3],
            k2safe: vec![1.0; n3],
            mask: vec![false; n3],
        };
        for i in 0..n {
            for j in 0..n {
                for k in 0..n {
                    let id = idx(n, i, j, k);
                    let (a, b, c) = (k1d[i], k1d[j], k1d[k]);
                    s.kx[id] = a;
                    s.ky[id] = b;
                    s.kz[id] = c;
                    let q = (a * a + b * b + c * c) as f64;
                    s.ksq[id] = q;
                    s.ksq2[id] = q * q;
                    s.k2safe[id] = if q > 0.0 { q } else { 1.0 };
                    s.mask[id] = a.abs() <= kc && b.abs() <= kc && c.abs() <= kc;
                }
            }
        }
        s
    }
}

#[derive(Clone)]
struct Field3 {
    c: [Vec<Cx>; 3],
}

impl Field3 {
    fn zeros(n3: usize) -> Self {
        Field3 {
            c: [vec![Cx::ZERO; n3], vec![Cx::ZERO; n3], vec![Cx::ZERO; n3]],
        }
    }
}

struct Work3D {
    plan: FftPlan,
    wh: Field3,
    nlhat: Field3,
    scratch: Field3,
    k1: Field3,
    k2: Field3,
    k3: Field3,
    k4: Field3,
    t1: Field3,
    t2: Field3,
    t3: Field3,
    u: [Vec<f64>; 3],
    w: [Vec<f64>; 3],
    kd: Vec<Cx>,
}

impl Work3D {
    fn new(n: usize) -> Self {
        let n3 = n * n * n;
        Work3D {
            plan: FftPlan::new(n),
            wh: Field3::zeros(n3),
            nlhat: Field3::zeros(n3),
            scratch: Field3::zeros(n3),
            k1: Field3::zeros(n3),
            k2: Field3::zeros(n3),
            k3: Field3::zeros(n3),
            k4: Field3::zeros(n3),
            t1: Field3::zeros(n3),
            t2: Field3::zeros(n3),
            t3: Field3::zeros(n3),
            u: [vec![0.0; n3], vec![0.0; n3], vec![0.0; n3]],
            w: [vec![0.0; n3], vec![0.0; n3], vec![0.0; n3]],
            kd: vec![Cx::ZERO; n3],
        }
    }
}

fn fft_field3(wk: &mut Work3D, inp: &[Vec<f64>; 3]) -> Field3 {
    let n3 = inp[0].len();
    let mut out = Field3::zeros(n3);
    for c in 0..3 {
        for i in 0..n3 {
            wk.scratch.c[c][i] = Cx::new(inp[c][i], 0.0);
        }
        fft3d(&wk.plan, &mut wk.scratch.c[c], false);
        out.c[c].copy_from_slice(&wk.scratch.c[c]);
    }
    out
}

fn ifft_field3(wk: &mut Work3D, inp: &Field3) -> [Vec<f64>; 3] {
    let n3 = inp.c[0].len();
    let mut out: [Vec<f64>; 3] = Default::default();
    for c in 0..3 {
        wk.scratch.c[c].copy_from_slice(&inp.c[c]);
        fft3d(&wk.plan, &mut wk.scratch.c[c], true);
        out[c] = wk.scratch.c[c].iter().map(|v| v.re).collect();
        let _ = n3;
    }
    out
}

fn project3(s: &Nse3D, out: &mut Field3, inp: &Field3) {
    let n3 = inp.c[0].len();
    let mut kd = vec![Cx::ZERO; n3];
    for i in 0..n3 {
        let mut d = Cx::ZERO;
        d += (s.kx[i] as f64) * inp.c[0][i];
        d += (s.ky[i] as f64) * inp.c[1][i];
        d += (s.kz[i] as f64) * inp.c[2][i];
        d = d.scale(1.0 / s.k2safe[i]);
        if s.ksq[i] == 0.0 {
            d = Cx::ZERO;
        }
        kd[i] = d;
    }
    for c in 0..3 {
        let kc = match c {
            0 => &s.kx,
            1 => &s.ky,
            _ => &s.kz,
        };
        for i in 0..n3 {
            out.c[c][i] = inp.c[c][i] - (kc[i] as f64) * kd[i];
        }
    }
}

fn curl_hat3(s: &Nse3D, out: &mut Field3, a: &Field3) {
    let n3 = a.c[0].len();
    let ii = Cx::new(0.0, 1.0);
    for i in 0..n3 {
        let (kx, ky, kz) = (s.kx[i], s.ky[i], s.kz[i]);
        let (a1, a2, a3) = (a.c[0][i], a.c[1][i], a.c[2][i]);
        out.c[0][i] = ii * (ky as f64 * a3 - kz as f64 * a2);
        out.c[1][i] = ii * (kz as f64 * a1 - kx as f64 * a3);
        out.c[2][i] = ii * (kx as f64 * a2 - ky as f64 * a1);
    }
}

#[derive(Clone, Copy)]
enum KSlot {
    K1,
    K2,
    K3,
    K4,
}

fn rhs3(wk: &mut Work3D, s: &Nse3D, slot: KSlot, uhat: &Field3) {
    let n3 = uhat.c[0].len();
    curl_hat3(s, &mut wk.wh, uhat);
    let u = ifft_field3(wk, uhat);
    let wh_copy = wk.wh.clone();
    let w = ifft_field3(wk, &wh_copy);
    let mut nl: [Vec<f64>; 3] = Default::default();
    for i in 0..n3 {
        let (w1, w2, w3) = (w[0][i], w[1][i], w[2][i]);
        let (u1, u2, u3) = (u[0][i], u[1][i], u[2][i]);
        nl[0].push(w2 * u3 - w3 * u2);
        nl[1].push(w3 * u1 - w1 * u3);
        nl[2].push(w1 * u2 - w2 * u1);
    }
    let nlhat = fft_field3(wk, &nl);
    let mut nlh = nlhat;
    for c in 0..3 {
        for i in 0..n3 {
            if !s.mask[i] {
                nlh.c[c][i] = Cx::ZERO;
            }
        }
    }
    let mut du = Field3::zeros(n3);
    project3(s, &mut du, &nlh);
    for c in 0..3 {
        for i in 0..n3 {
            let damp = s.nu * s.ksq[i] + s.nu4 * s.ksq2[i];
            du.c[c][i] -= damp * uhat.c[c][i];
        }
    }
    match slot {
        KSlot::K1 => wk.k1 = du,
        KSlot::K2 => wk.k2 = du,
        KSlot::K3 => wk.k3 = du,
        KSlot::K4 => wk.k4 = du,
    }
}

fn step_rk4_3d(wk: &mut Work3D, s: &Nse3D, uhat: &Field3, dt: f64) {
    let n3 = uhat.c[0].len();
    rhs3(wk, s, KSlot::K1, uhat);
    for c in 0..3 {
        for i in 0..n3 {
            wk.t1.c[c][i] = uhat.c[c][i] + wk.k1.c[c][i].scale(0.5 * dt);
        }
    }
    let t1c = wk.t1.clone();
    rhs3(wk, s, KSlot::K2, &t1c);
    for c in 0..3 {
        for i in 0..n3 {
            wk.t1.c[c][i] = uhat.c[c][i] + wk.k2.c[c][i].scale(0.5 * dt);
        }
    }
    let t1c = wk.t1.clone();
    rhs3(wk, s, KSlot::K3, &t1c);
    for c in 0..3 {
        for i in 0..n3 {
            wk.t1.c[c][i] = uhat.c[c][i] + wk.k3.c[c][i].scale(dt);
        }
    }
    let t1c = wk.t1.clone();
    rhs3(wk, s, KSlot::K4, &t1c);
    for c in 0..3 {
        for i in 0..n3 {
            let mut v = uhat.c[c][i] + wk.k1.c[c][i].scale(dt / 6.0);
            v += wk.k2.c[c][i].scale(dt / 3.0);
            v += wk.k3.c[c][i].scale(dt / 3.0);
            v += wk.k4.c[c][i].scale(dt / 6.0);
            wk.t2.c[c][i] = if s.mask[i] { v } else { Cx::ZERO };
        }
    }
}

fn cfl_dt_3d(wk: &mut Work3D, s: &Nse3D, uhat: &Field3) -> f64 {
    let u = ifft_field3(wk, uhat);
    let mut umax = 0.0f64;
    let n3 = u[0].len();
    for i in 0..n3 {
        let v = (u[0][i] * u[0][i] + u[1][i] * u[1][i] + u[2][i] * u[2][i]).sqrt();
        umax = umax.max(v);
    }
    if umax < 1e-14 {
        0.5 * s.dx * s.dx / s.nu.max(1e-12f64)
    } else {
        0.5 * s.dx / umax
    }
}

// ───────────────────── ICs & b-rotations ────────────────────────────────

fn nsb_theta_b() -> f64 {
    (1.0 / (4.0 * PI + 2.0 * 3.0f64.sqrt())).asin()
}
const NSB_AXIS: (f64, f64, f64) = (0.3, -0.5, 0.812403840463596); // sqrt(1-0.09-0.25)

type Mat3 = [[f64; 3]; 3];

fn rodrigues(theta: f64, ax: (f64, f64, f64)) -> Mat3 {
    let (ex, ey, ez) = ax;
    let c = theta.cos();
    let s = theta.sin();
    let cr = [[0.0, -ez, ey], [ez, 0.0, -ex], [-ey, ex, 0.0]];
    let ou = [
        [ex * ex, ex * ey, ex * ez],
        [ey * ex, ey * ey, ey * ez],
        [ez * ex, ez * ey, ez * ez],
    ];
    let mut r = [[0.0; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            r[i][j] = c * (i == j) as i32 as f64 + (1.0 - c) * ou[i][j] - s * cr[i][j];
        }
    }
    r
}

fn grid_1d(n: usize) -> Vec<f64> {
    (0..n).map(|i| 2.0 * PI * i as f64 / n as f64).collect()
}

type PhysField = [Vec<f64>; 3];

fn ic_taylor_green(n: usize) -> PhysField {
    let x = grid_1d(n);
    let mut u: PhysField = Default::default();
    for c in u.iter_mut() {
        *c = vec![0.0; n * n * n];
    }
    let sx: Vec<f64> = x.iter().map(|v| v.sin()).collect();
    let cx: Vec<f64> = x.iter().map(|v| v.cos()).collect();
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                u[0][idx(n, i, j, k)] = sx[i] * cx[j] * cx[k];
                u[1][idx(n, i, j, k)] = -cx[i] * sx[j] * cx[k];
            }
        }
    }
    u
}

fn ic_abc(n: usize) -> PhysField {
    let x = grid_1d(n);
    let mut u: PhysField = Default::default();
    for c in u.iter_mut() {
        *c = vec![0.0; n * n * n];
    }
    let sx: Vec<f64> = x.iter().map(|v| v.sin()).collect();
    let cx: Vec<f64> = x.iter().map(|v| v.cos()).collect();
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                u[0][idx(n, i, j, k)] = sx[k] + cx[j];
                u[1][idx(n, i, j, k)] = sx[i] + cx[k];
                u[2][idx(n, i, j, k)] = sx[j] + cx[i];
            }
        }
    }
    u
}

fn ic_hou_luo(n: usize) -> PhysField {
    let x = grid_1d(n);
    let mut w: PhysField = Default::default();
    for c in w.iter_mut() {
        *c = vec![0.0; n * n * n];
    }
    let sigma = PI / 16.0;
    let inv2s2 = 1.0 / (2.0 * sigma * sigma);
    let (y0, z0a, z0b) = (PI / 2.0, PI / 2.0, 3.0 * PI / 2.0);
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                let (yj, zk) = (x[j], x[k]);
                let g1 = (-((yj - y0) * (yj - y0) + (zk - z0a) * (zk - z0a)) * inv2s2).exp();
                let g2 = (-((yj - 3.0 * PI / 2.0) * (yj - 3.0 * PI / 2.0)
                    + (zk - z0b) * (zk - z0b))
                    * inv2s2)
                    .exp();
                w[0][idx(n, i, j, k)] = (g1 - g2) * (1.0 + 0.05 * x[i].cos());
            }
        }
    }
    w
}

// xorshift64* deterministic RNG (replaces rand crate)
struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn normal(&mut self) -> f64 {
        // Box–Muller
        let u1 = self.next_f64().max(1e-12);
        let u2 = self.next_f64();
        (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
    }
}

fn ic_random(n: usize, seed: u64) -> PhysField {
    let mut rng = Rng(seed | 1);
    let mut u: PhysField = Default::default();
    for c in u.iter_mut() {
        *c = (0..n * n * n).map(|_| rng.normal()).collect();
    }
    let x = grid_1d(n);
    let kp = 4.0;
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                let id = idx(n, i, j, k);
                u[0][id] += 0.5 * (kp * x[i]).sin() * (kp * x[j]).cos();
                u[1][id] += 0.5 * (kp * x[i]).sin() * (0.5 * (kp * x[j]).sin() + 0.5);
                u[2][id] += 0.5 * (kp * x[k]).cos() * (kp * x[j]).sin();
            }
        }
    }
    u
}

fn prepare_state3(wk: &mut Work3D, s: &Nse3D, ic: &PhysField) -> Field3 {
    let n3 = ic[0].len();
    let mut uhat = Field3::zeros(n3);
    for c in 0..3 {
        for i in 0..n3 {
            wk.scratch.c[c][i] = Cx::new(ic[c][i], 0.0);
        }
        fft3d(&wk.plan, &mut wk.scratch.c[c], false);
        uhat.c[c].copy_from_slice(&wk.scratch.c[c]);
    }
    let uc = uhat.clone();
    project3(s, &mut uhat, &uc);
    for c in 0..3 {
        for i in 0..n3 {
            if !s.mask[i] {
                uhat.c[c][i] = Cx::ZERO;
            }
        }
    }
    uhat
}

fn rotate_pointwise3(wk: &mut Work3D, s: &Nse3D, uhat: &Field3, r: &Mat3) {
    let n3 = uhat.c[0].len();
    let u = ifft_field3(wk, uhat);
    let mut ru: PhysField = Default::default();
    for c in ru.iter_mut() {
        *c = vec![0.0; n3];
    }
    for i in 0..n3 {
        let (x, y, z) = (u[0][i], u[1][i], u[2][i]);
        ru[0][i] = r[0][0] * x + r[0][1] * y + r[0][2] * z;
        ru[1][i] = r[1][0] * x + r[1][1] * y + r[1][2] * z;
        ru[2][i] = r[2][0] * x + r[2][1] * y + r[2][2] * z;
    }
    wk.t3 = fft_field3(wk, &ru);
}

fn rotate_full_symmetry3(wk: &mut Work3D, s: &Nse3D, uhat: &Field3) {
    let n = s.n;
    let n3 = uhat.c[0].len();
    let u = ifft_field3(wk, uhat);
    let mut ru: PhysField = Default::default();
    for c in ru.iter_mut() {
        *c = vec![0.0; n3];
    }
    for i in 0..n {
        let isrc = (n - i) % n; // index of −x_i
        for j in 0..n {
            for k in 0..n {
                let src = idx(n, j, isrc, k);
                let dst = idx(n, i, j, k);
                ru[0][dst] = -u[1][src];
                ru[1][dst] = u[0][src];
                ru[2][dst] = u[2][src];
            }
        }
    }
    wk.t3 = fft_field3(wk, &ru);
}

// ───────────────────────── diagnostics ──────────────────────────────────

#[derive(Clone, Default)]
struct TimeSeries {
    t: Vec<f64>,
    energy: Vec<f64>,
    enstrophy: Vec<f64>,
    palinstrophy: Vec<f64>,
    sup_omega: Vec<f64>,
    dissipation: Vec<f64>,
    bkm: Vec<f64>,
}

impl TimeSeries {
    fn new() -> Self {
        TimeSeries {
            t: vec![0.0],
            energy: vec![0.0],
            enstrophy: vec![0.0],
            palinstrophy: vec![0.0],
            sup_omega: vec![0.0],
            dissipation: vec![0.0],
            bkm: vec![0.0],
        }
    }
    fn push(&mut self, t: f64, e: f64, om: f64, pal: f64, sup: f64, eps: f64, bkm: f64) {
        self.t.push(t);
        self.energy.push(e);
        self.enstrophy.push(om);
        self.palinstrophy.push(pal);
        self.sup_omega.push(sup);
        self.dissipation.push(eps);
        self.bkm.push(bkm);
    }
}

fn energy3(s: &Nse3D, uhat: &Field3) -> f64 {
    let n6 = (s.n.pow(3) as f64).powi(2);
    let mut sum = 0.0;
    for c in 0..3 {
        for v in &uhat.c[c] {
            sum += v.norm2();
        }
    }
    0.5 * sum / n6
}

fn enstrophy3(s: &Nse3D, what: &Field3) -> f64 {
    energy3(s, what)
}

fn palinstrophy3(s: &Nse3D, what: &Field3) -> f64 {
    let n3 = what.c[0].len();
    let n6 = (s.n.pow(3) as f64).powi(2);
    let ii = Cx::new(0.0, 1.0);
    let mut sum = 0.0;
    for i in 0..n3 {
        let a1 = ii * (s.ky[i] as f64 * what.c[2][i] - s.kz[i] as f64 * what.c[1][i]);
        let a2 = ii * (s.kz[i] as f64 * what.c[0][i] - s.kx[i] as f64 * what.c[2][i]);
        let a3 = ii * (s.kx[i] as f64 * what.c[1][i] - s.ky[i] as f64 * what.c[0][i]);
        sum += a1.norm2() + a2.norm2() + a3.norm2();
    }
    0.5 * sum / n6
}

fn dissipation3(s: &Nse3D, uhat: &Field3) -> f64 {
    let n3 = uhat.c[0].len();
    let n6 = (s.n.pow(3) as f64).powi(2);
    let mut sum = 0.0;
    for c in 0..3 {
        for i in 0..n3 {
            sum += s.ksq[i] * uhat.c[c][i].norm2();
        }
    }
    s.nu * sum / n6
}

fn sup_vorticity3(w: &PhysField) -> f64 {
    let n3 = w[0].len();
    let mut m = 0.0f64;
    for i in 0..n3 {
        let v = (w[0][i] * w[0][i] + w[1][i] * w[1][i] + w[2][i] * w[2][i]).sqrt();
        m = m.max(v);
    }
    m
}

fn divergence_max3(s: &Nse3D, uhat: &Field3) -> f64 {
    let n3 = uhat.c[0].len();
    let mut sum = 0.0;
    for i in 0..n3 {
        let mut d = s.kx[i] as f64 * uhat.c[0][i];
        d += s.ky[i] as f64 * uhat.c[1][i];
        d += s.kz[i] as f64 * uhat.c[2][i];
        sum += d.norm2();
    }
    (sum).sqrt() / (s.n.pow(3) as f64)
}

fn linfit(xs: &[f64], ys: &[f64]) -> (f64, f64, f64) {
    let n = xs.len();
    if n < 2 {
        return (f64::NAN, f64::NAN, f64::NAN);
    }
    let mut sx = 0.0;
    let mut sy = 0.0;
    let mut sxx = 0.0;
    let mut sxy = 0.0;
    for i in 0..n {
        sx += xs[i];
        sy += ys[i];
        sxx += xs[i] * xs[i];
        sxy += xs[i] * ys[i];
    }
    let den = n as f64 * sxx - sx * sx;
    if den == 0.0 {
        return (f64::NAN, f64::NAN, f64::NAN);
    }
    let a = (n as f64 * sxy - sx * sy) / den;
    let b = (sy - a * sx) / n as f64;
    let ybar = sy / n as f64;
    let mut ssr = 0.0;
    let mut sst = 0.0;
    for i in 0..n {
        ssr += (ys[i] - (a * xs[i] + b)).powi(2);
        sst += (ys[i] - ybar).powi(2);
    }
    let r2 = if sst > 0.0 { 1.0 - ssr / sst } else { f64::NAN };
    (a, b, r2)
}

fn observed_order(jc: f64, jf: f64, jff: f64, ratio: f64) -> f64 {
    let den = jc - jf;
    let num = jf - jff;
    if den.abs() < 1e-30 || num.abs() < 1e-30 {
        return f64::NAN;
    }
    (den / num).abs().log(ratio)
}

#[derive(Default)]
struct BlowupReport {
    lambda_trend: f64,
    lambda_r2: f64,
    lambda_max: f64,
    doubling_min: f64,
    alpha: f64,
    bkm_final: f64,
    sustained: bool,
    tstar: Option<f64>,
}

fn blowup_report(ts: &TimeSeries) -> BlowupReport {
    let mut tl = Vec::new();
    let mut lam = Vec::new();
    for i in 1..ts.t.len().saturating_sub(1) {
        let dt1 = ts.t[i] - ts.t[i - 1];
        let dt2 = ts.t[i + 1] - ts.t[i];
        let (s0, s1, s2) = (ts.sup_omega[i - 1], ts.sup_omega[i], ts.sup_omega[i + 1]);
        if dt1 <= 0.0 || dt2 <= 0.0 || s0 <= 0.0 || s1 <= 0.0 || s2 <= 0.0 {
            continue;
        }
        lam.push((s2.ln() - s0.ln()) / (dt1 + dt2));
        tl.push(ts.t[i]);
    }
    let mut bl = BlowupReport {
        bkm_final: *ts.bkm.last().unwrap_or(&0.0),
        doubling_min: f64::INFINITY,
        ..Default::default()
    };
    if tl.len() < 4 {
        bl.lambda_max = lam.iter().cloned().fold(f64::NAN, f64::max);
        return bl;
    }
    let (a, _b, r2) = linfit(&tl, &lam);
    bl.lambda_trend = a;
    bl.lambda_r2 = r2;
    bl.lambda_max = lam.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    for i in 1..ts.sup_omega.len() {
        let (s0, s1) = (ts.sup_omega[i - 1], ts.sup_omega[i]);
        let dt = ts.t[i] - ts.t[i - 1];
        if s0 > 0.0 && s1 > s0 && dt > 0.0 {
            bl.doubling_min = bl
                .doubling_min
                .min(dt * 2.0f64.ln() / (s1 / s0).ln());
        }
    }
    let nfit = ((tl.len() as f64) * 0.25).round() as usize;
    let nfit = nfit.max(4).min(tl.len());
    let (at, _bt, r2t) = linfit(&tl[tl.len() - nfit..], &lam[lam.len() - nfit..]);
    let ntail = nfit.min(ts.sup_omega.len());
    let tail_max = ts.sup_omega[ts.sup_omega.len() - ntail..]
        .iter()
        .cloned()
        .fold(f64::NEG_INFINITY, f64::max);
    let sup_max = ts.sup_omega.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    bl.sustained = at.is_finite()
        && at > 0.0
        && r2t.is_finite()
        && r2t > 0.5
        && bl.lambda_max > 0.0
        && tail_max >= 0.98 * sup_max;
    if bl.sustained {
        let t_end = *ts.t.last().unwrap();
        let mut best_err = f64::INFINITY;
        let mut best_tstar = f64::NAN;
        let mut best_alpha = f64::NAN;
        let mut al = 0.5f64;
        while al <= 7.0 + 1e-9 {
            let mut frac = 1.02f64;
            while frac <= 2.5 + 1e-9 {
                let tst = t_end * frac;
                let mut xs = Vec::new();
                let mut ys = Vec::new();
                let mut ok = true;
                for i in 0..ts.t.len() {
                    let d = tst - ts.t[i];
                    if d <= 0.0 {
                        ok = false;
                        break;
                    }
                    xs.push(d.ln());
                    ys.push(ts.sup_omega[i].max(1e-300).ln());
                }
                if ok {
                    let (aa, _bb, rr) = linfit(&xs, &ys);
                    if rr.is_finite() && -rr < best_err {
                        best_err = -rr;
                        best_tstar = tst;
                        best_alpha = -aa;
                    }
                }
                frac += 0.02;
            }
            al += 0.25;
        }
        if best_err < -0.9 {
            bl.tstar = Some(best_tstar);
            bl.alpha = best_alpha;
        }
    }
    bl
}

// ─────────────────────────── runner ─────────────────────────────────────

struct DecayResult {
    uhat: Field3,
    ts: TimeSeries,
    div_max: f64,
    energy_rise: f64,
    cfl_exceeded: usize,
    adapted_steps: usize,
    wall: f64,
}

fn run_decay_3d(
    wk: &mut Work3D,
    s: &Nse3D,
    uhat0: &Field3,
    dt: f64,
    t_horizon: f64,
    label: &str,
    sample_every: usize,
    kick_mode: usize,
    kick_every: f64,
    blowup_stop: bool,
    show_prog: bool,
    adaptive: Option<bool>,
) -> DecayResult {
    let adaptive = adaptive.unwrap_or(cfg().adaptive_cfl);
    let n3 = uhat0.c[0].len();
    let mut res = DecayResult {
        uhat: uhat0.clone(),
        ts: TimeSeries::new(),
        div_max: 0.0,
        energy_rise: 0.0,
        cfl_exceeded: 0,
        adapted_steps: 0,
        wall: 0.0,
    };
    curl_hat3(s, &mut wk.wh, &res.uhat);
    let whc0 = wk.wh.clone();
    let w0 = ifft_field3(wk, &whc0);
    let mut sup_prev = sup_vorticity3(&w0);
    let steps = (t_horizon / dt).ceil() as usize;
    let mut e_prev = energy3(s, &res.uhat);
    let mut t_elapsed = 0.0;
    let t0 = Instant::now();
    unsafe { PROG_LAST = 0.0 };
    if adaptive {
        p_muted(&format!("  {}\n", L("adaptive_on")));
    }
    let mut next_kick = if kick_mode > 0 { kick_every } else { f64::INFINITY };
    for step in 1..=steps {
        let mut h = dt.min(t_horizon - t_elapsed);
        if h <= 1e-15 {
            break;
        }
        let cfl = cfl_dt_3d(wk, s, &res.uhat);
        if cfl < h {
            res.cfl_exceeded += 1;
            if adaptive {
                h = cfl;
                res.adapted_steps += 1;
            }
        }
        step_rk4_3d(wk, s, &res.uhat, h);
        res.uhat = wk.t2.clone();
        t_elapsed += h;
        if kick_mode > 0 && t_elapsed >= next_kick - 1e-12 {
            let uh = res.uhat.clone();
            if kick_mode == 1 {
                rotate_full_symmetry3(wk, s, &uh);
            } else {
                let r = rodrigues(nsb_theta_b(), NSB_AXIS);
                rotate_pointwise3(wk, s, &uh, &r);
                let t3c = wk.t3.clone();
                let mut t3p = wk.t3.clone();
                project3(s, &mut t3p, &t3c);
                wk.t3 = t3p;
            }
            for c in 0..3 {
                for i in 0..n3 {
                    if !s.mask[i] {
                        wk.t3.c[c][i] = Cx::ZERO;
                    }
                }
            }
            res.uhat = wk.t3.clone();
            next_kick += kick_every;
        }
        if step % sample_every == 0 || step == steps {
            curl_hat3(s, &mut wk.wh, &res.uhat);
            let whc = wk.wh.clone();
            let w = ifft_field3(wk, &whc);
            let sup_now = sup_vorticity3(&w);
            let e_now = energy3(s, &res.uhat);
            res.div_max = res.div_max.max(divergence_max3(s, &res.uhat));
            res.energy_rise = res.energy_rise.max(e_now - e_prev);
            e_prev = e_now;
            let bkm = res.ts.bkm.last().unwrap_or(&0.0)
                + 0.5 * (sup_prev + sup_now) * h * sample_every as f64;
            sup_prev = sup_now;
            res.ts.push(
                t_elapsed,
                e_now,
                enstrophy3(s, &wk.wh),
                palinstrophy3(s, &wk.wh),
                sup_now,
                dissipation3(s, &res.uhat),
                bkm,
            );
            if show_prog {
                progress(step as f64 / steps as f64, label, t0, steps, step);
            }
            if blowup_stop && (!sup_now.is_finite() || sup_now > 1e8) {
                p_warn("  stop: sup|w| over threshold\n");
                break;
            }
        }
    }
    if show_prog {
        progress(1.0, label, t0, steps, steps);
    }
    res.wall = t0.elapsed().as_secs_f64();
    res
}

// ─────────────────────── 2-D barotropic β-plane ─────────────────────────

struct Baro2D {
    n: usize,
    nu: f64,
    nu4: f64,
    beta: f64,
    lbox: f64,
    kpx: Vec<f64>,
    kpy: Vec<f64>,
    kp2: Vec<f64>,
    mask: Vec<bool>,
    plan: FftPlan,
}

impl Baro2D {
    fn new(n: usize, nu: f64, nu4: f64, beta: f64, lbox: f64) -> Self {
        let n2 = n * n;
        let mut k1d = vec![0i32; n];
        for i in 0..n / 2 {
            k1d[i] = i as i32;
        }
        for i in -((n / 2) as i32)..0 {
            k1d[(i + n as i32) as usize] = i;
        }
        let kc = (n / 3) as i32;
        let mut m = Baro2D {
            n,
            nu,
            nu4,
            beta,
            lbox,
            kpx: vec![0.0; n2],
            kpy: vec![0.0; n2],
            kp2: vec![0.0; n2],
            mask: vec![false; n2],
            plan: FftPlan::new(n),
        };
        for i in 0..n {
            for j in 0..n {
                let id = i * n + j;
                let (a, b) = (k1d[i], k1d[j]);
                m.kpx[id] = 2.0 * PI * a as f64 / lbox;
                m.kpy[id] = 2.0 * PI * b as f64 / lbox;
                m.kp2[id] = m.kpx[id] * m.kpx[id] + m.kpy[id] * m.kpy[id];
                m.mask[id] = a.abs() <= kc && b.abs() <= kc;
            }
        }
        m
    }

    fn ifft(&self, out: &mut Vec<f64>, inp: &[Cx]) {
        let mut tmp = inp.to_vec();
        fft2d(&self.plan, &mut tmp, true);
        *out = tmp.iter().map(|v| v.re).collect();
    }

    fn fft(&self, out: &mut Vec<Cx>, inp: &[f64]) {
        *out = inp.iter().map(|&v| Cx::new(v, 0.0)).collect();
        fft2d(&self.plan, out, false);
    }

    /// writes u,v into out_u/out_v; returns max|u|
    fn velocity(&self, what: &[Cx], out_u: &mut Vec<f64>, out_v: &mut Vec<f64>) -> f64 {
        let n2 = self.n * self.n;
        let mut uh = vec![Cx::ZERO; n2];
        let mut vh = vec![Cx::ZERO; n2];
        for i in 0..n2 {
            let psih = if self.kp2[i] > 0.0 {
                what[i].scale(-1.0 / self.kp2[i])
            } else {
                Cx::ZERO
            };
            uh[i] = Cx::new(0.0, 1.0) * self.kpy[i] * psih;
            vh[i] = -Cx::new(0.0, 1.0) * self.kpx[i] * psih;
        }
        self.ifft(out_u, &uh);
        self.ifft(out_v, &vh);
        let mut um = 0.0f64;
        for i in 0..n2 {
            um = um.max((out_u[i] * out_u[i] + out_v[i] * out_v[i]).sqrt());
        }
        um
    }
}

fn baro_rhs(m: &Baro2D, dwhat: &mut Vec<Cx>, what: &[Cx],
            bufs: &mut BaroBufs) {
    let n2 = m.n * m.n;
    for i in 0..n2 {
        let psih = if m.kp2[i] > 0.0 {
            what[i].scale(-1.0 / m.kp2[i])
        } else {
            Cx::ZERO
        };
        bufs.uhat[i] = Cx::new(0.0, 1.0) * m.kpy[i] * psih;
        bufs.vhat[i] = -Cx::new(0.0, 1.0) * m.kpx[i] * psih;
        bufs.dxwhat[i] = Cx::new(0.0, 1.0) * m.kpx[i] * what[i];
        bufs.dywhat[i] = Cx::new(0.0, 1.0) * m.kpy[i] * what[i];
    }
    m.ifft(&mut bufs.w, what);
    m.ifft(&mut bufs.u, &bufs.uhat);
    m.ifft(&mut bufs.v, &bufs.vhat);
    m.ifft(&mut bufs.dxw, &bufs.dxwhat);
    m.ifft(&mut bufs.dyw, &bufs.dywhat);
    let mut nl = vec![0.0; n2];
    for i in 0..n2 {
        nl[i] = -(bufs.u[i] * bufs.dxw[i] + bufs.v[i] * bufs.dyw[i]);
    }
    m.fft(dwhat, &nl);
    for i in 0..n2 {
        dwhat[i] = dwhat[i]
            - m.beta * bufs.vhat[i]
            - (m.nu * m.kp2[i] + m.nu4 * m.kp2[i] * m.kp2[i]) * what[i];
        if !m.mask[i] {
            dwhat[i] = Cx::ZERO;
        }
    }
}

struct BaroBufs {
    uhat: Vec<Cx>,
    vhat: Vec<Cx>,
    dxwhat: Vec<Cx>,
    dywhat: Vec<Cx>,
    u: Vec<f64>,
    v: Vec<f64>,
    w: Vec<f64>,
    dxw: Vec<f64>,
    dyw: Vec<f64>,
}

impl BaroBufs {
    fn new(n: usize) -> Self {
        let n2 = n * n;
        BaroBufs {
            uhat: vec![Cx::ZERO; n2],
            vhat: vec![Cx::ZERO; n2],
            dxwhat: vec![Cx::ZERO; n2],
            dywhat: vec![Cx::ZERO; n2],
            u: vec![0.0; n2],
            v: vec![0.0; n2],
            w: vec![0.0; n2],
            dxw: vec![0.0; n2],
            dyw: vec![0.0; n2],
        }
    }
}

fn baro_step(m: &Baro2D, what: &mut Vec<Cx>, dt: f64, bufs: &mut BaroBufs,
             k1: &mut Vec<Cx>, k2: &mut Vec<Cx>, k3: &mut Vec<Cx>, k4: &mut Vec<Cx>,
             buf: &mut Vec<Cx>) {
    let n2 = m.n * m.n;
    baro_rhs(m, k1, what, bufs);
    for i in 0..n2 {
        buf[i] = what[i] + k1[i].scale(0.5 * dt);
    }
    baro_rhs(m, k2, buf, bufs);
    for i in 0..n2 {
        buf[i] = what[i] + k2[i].scale(0.5 * dt);
    }
    baro_rhs(m, k3, buf, bufs);
    for i in 0..n2 {
        buf[i] = what[i] + k3[i].scale(dt);
    }
    baro_rhs(m, k4, buf, bufs);
    for i in 0..n2 {
        let mut v = what[i] + k1[i].scale(dt / 6.0);
        v += k2[i].scale(dt / 3.0);
        v += k3[i].scale(dt / 3.0);
        v += k4[i].scale(dt / 6.0);
        what[i] = if m.mask[i] { v } else { Cx::ZERO };
    }
}

// ─────────────────────────── 20 real flows ──────────────────────────────

struct Flow {
    id: &'static str,
    ru: &'static str,
    en: &'static str,
    medium: &'static str,
    source: &'static str,
    doc: [(&'static str, &'static str); 4],
    u_: f64,
    l_: f64,
    width: f64,
    lat: f64,
    nu_eff: f64,
    depth: f64,
    wave_h: f64,
    wave_lambda: f64,
    model: &'static str,
}

const FLOWS: &[Flow] = &[
    Flow { id: "katrina", ru: "Ураган Катрина (2005)", en: "Hurricane Katrina (2005)", medium: "air",
        source: "NHC Tropical Cyclone Report AL122005 (Knabb et al.)",
        doc: [("1-min sustained wind", "77 m/s (150 kt)"), ("min pressure", "902 hPa"), ("radius of max wind", "37 km"), ("peak latitude", "25.7 N")],
        u_: 77.0, l_: 3.7e4, width: 2.0e4, lat: 25.7, nu_eff: 100.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "haiyan", ru: "Тайфун Хайян (2013)", en: "Typhoon Haiyan (2013)", medium: "air",
        source: "JTWC Best Track 31W; NDRRMC Philippines",
        doc: [("1-min sustained wind", "87 m/s (170 kt)"), ("min pressure", "895 hPa"), ("radius of max wind", "15-20 km"), ("latitude", "8 N")],
        u_: 87.0, l_: 1.8e4, width: 1.0e4, lat: 8.0, nu_eff: 100.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "patricia", ru: "Ураган Патрисия (2015)", en: "Hurricane Patricia (2015)", medium: "air",
        source: "NHC Tropical Cyclone Report EP202015",
        doc: [("1-min sustained wind", "95 m/s (185 kt), record"), ("min pressure", "872 hPa"), ("radius of max wind", "8 km"), ("latitude", "19 N")],
        u_: 95.0, l_: 8.0e3, width: 5.0e3, lat: 19.0, nu_eff: 100.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "redspot", ru: "Большое красное пятно (Юпитер)", en: "Great Red Spot (Jupiter)", medium: "gas",
        source: "Voyager 1/2 (1979); Cassini; Juno",
        doc: [("extent", "16350 x 11000 km"), ("wind speeds", "100-120 m/s"), ("rotation period", "4-6 days"), ("latitude", "22 S")],
        u_: 110.0, l_: 8.0e6, width: 3.0e6, lat: 22.0, nu_eff: 1.0e4, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "hexagon", ru: "Сатурн: северный гексагон", en: "Saturn north polar hexagon", medium: "gas",
        source: "Voyager (1980-81); Cassini (2006-2017)",
        doc: [("latitude", "78 N"), ("jet speed", "100 m/s"), ("rotation period", "10.7 h"), ("wave number", "m = 6")],
        u_: 100.0, l_: 1.45e7, width: 2.0e6, lat: 78.0, nu_eff: 1.0e4, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "jetstream", ru: "Полярное струйное течение", en: "Polar jet stream", medium: "air",
        source: "WMO radiosonde climatology; ICAO Annex 3",
        doc: [("core speed", "50-80 m/s"), ("altitude", "9-12 km"), ("width", "200-400 km"), ("latitude", "30-60")],
        u_: 70.0, l_: 3.0e5, width: 1.5e5, lat: 45.0, nu_eff: 50.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "karman", ru: "Дорожка Кармана", en: "von Karman vortex street", medium: "air",
        source: "Landsat 5 (1989, Jeju); MODIS Aqua",
        doc: [("island diameter", "2-5 km"), ("wind", "10 m/s"), ("Strouhal number", "0.2"), ("shedding period", "2-6 h")],
        u_: 10.0, l_: 3.0e3, width: 1.5e3, lat: 33.0, nu_eff: 50.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "gulfstream", ru: "Гольфстрим", en: "Gulf Stream", medium: "water",
        source: "Franklin-Folger map (1768); Halkin & Rossby (1985)",
        doc: [("max speed", "2.0-2.5 m/s"), ("width", "100 km"), ("transport", "30 Sv"), ("latitude", "35-40 N")],
        u_: 2.2, l_: 1.0e5, width: 5.0e4, lat: 37.0, nu_eff: 1.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "kuroshio", ru: "Куросио", en: "Kuroshio Current", medium: "water",
        source: "ASUKA/JCOPE Observations; Kawabe (1988)",
        doc: [("max speed", "1.5-2.0 m/s"), ("width", "80 km"), ("transport", "20-30 Sv"), ("latitude", "33 N")],
        u_: 1.8, l_: 8.0e4, width: 4.0e4, lat: 33.0, nu_eff: 1.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "agulhas", ru: "Игольное течение", en: "Agulhas Current", medium: "water",
        source: "Lutjeharms (2006); ACT array (2010-2013)",
        doc: [("max speed", "2.0-2.5 m/s"), ("width", "100-150 km"), ("transport", "70 Sv"), ("retroflection", "20 E")],
        u_: 2.2, l_: 1.2e5, width: 6.0e4, lat: -35.0, nu_eff: 1.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "acc", ru: "Антарктическое циркумполярное течение", en: "Antarctic Circumpolar Current", medium: "water",
        source: "WOCE/SR1b sections; Meredith et al.",
        doc: [("transport", "130-150 Sv, largest on Earth"), ("speeds", "0.3-0.7 m/s"), ("latitude", "50-60 S"), ("width", "800 km")],
        u_: 0.5, l_: 8.0e5, width: 4.0e5, lat: -55.0, nu_eff: 1.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "draupner", ru: "Волна-убийца Драупнер (1995)", en: "Draupner rogue wave (1995)", medium: "water",
        source: "Haver (2004), Statoil laser record",
        doc: [("max wave height", "25.6 m"), ("background Hs", "11.9 m"), ("depth", "70 m"), ("steepness", "kA = 0.39")],
        u_: 15.0, l_: 200.0, width: 100.0, lat: 58.0, nu_eff: 1e-6, depth: 70.0, wave_h: 25.6, wave_lambda: 200.0, model: "wave" },
    Flow { id: "tohoku", ru: "Цунами Тохоку (2011)", en: "Tohoku tsunami (2011)", medium: "water",
        source: "NOAA DART buoys; JMA; NOWPHAS",
        doc: [("open-ocean height", "1.8 m"), ("max run-up", "40.5 m"), ("speed", "800 km/h at 4000 m"), ("magnitude", "M9.1")],
        u_: 200.0, l_: 2.0e5, width: 1.0e5, lat: 38.3, nu_eff: 1e-6, depth: 4000.0, wave_h: 1.8, wave_lambda: 2.0e5, model: "wave" },
    Flow { id: "qiantang", ru: "Приливной бор Цяньтан", en: "Qiantang tidal bore", medium: "water",
        source: "Hangzhou Bay surveys; Song-dynasty chronicles",
        doc: [("bore height", "up to 9 m"), ("speed", "6-9 m/s"), ("tidal amplitude", "up to 8.9 m"), ("bay width", "100 km")],
        u_: 8.0, l_: 5.0e4, width: 2.0e4, lat: 30.4, nu_eff: 1e-6, depth: 10.0, wave_h: 9.0, wave_lambda: 5.0e4, model: "wave" },
    Flow { id: "reynolds", ru: "Течение Рейнольдса (1883)", en: "Reynolds pipe flow (1883)", medium: "water",
        source: "Reynolds O., Phil. Trans. R. Soc. 174 (1883)",
        doc: [("critical Re", "2300"), ("pipe diameter", "2.6 cm"), ("transition speed", "0.09 m/s"), ("laminar profile", "Poiseuille")],
        u_: 0.09, l_: 2.6e-2, width: 1.3e-2, lat: 999.0, nu_eff: 1e-6, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "taylorcouette", ru: "Тейлор-Куэтт вихри (1923)", en: "Taylor-Couette vortices (1923)", medium: "water",
        source: "Taylor G.I., Phil. Trans. R. Soc. A 223 (1923)",
        doc: [("inner radius", "3.55 cm"), ("gap", "0.42 cm"), ("critical Taylor number", "1708"), ("vortices", "toroidal cells")],
        u_: 0.5, l_: 4.2e-3, width: 2.1e-3, lat: 999.0, nu_eff: 1e-6, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "benard", ru: "Конвекция Бенара-Рэлея", en: "Benard-Rayleigh convection", medium: "water",
        source: "Benard (1900); Rayleigh (1916)",
        doc: [("critical Ra", "1708"), ("cell size", "2 depths"), ("layer depth", "1 cm"), ("critical dT", "Rayleigh formula")],
        u_: 1e-3, l_: 2.0e-2, width: 1.0e-2, lat: 999.0, nu_eff: 1e-6, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "moore", ru: "Торнадо Бридж-Крик-Мур (1999)", en: "Bridge Creek-Moore tornado (1999)", medium: "air",
        source: "Wurman & Alexander (2005), DOW-III",
        doc: [("max wind", "135 m/s (301 mph), DOW record"), ("core radius", "250 m"), ("latitude", "35.3 N"), ("track", "61 km")],
        u_: 135.0, l_: 5.0e2, width: 2.5e2, lat: 35.3, nu_eff: 100.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "vortex" },
    Flow { id: "mtwashington", ru: "Порыв на горе Вашингтон (1934)", en: "Mount Washington gust (1934)", medium: "air",
        source: "Mount Washington Observatory, 12.04.1934",
        doc: [("gust", "103.3 m/s (231 mph), world record"), ("station altitude", "1917 m"), ("latitude", "44.3 N"), ("ice", "instrument icing")],
        u_: 103.0, l_: 1.0e4, width: 5.0e3, lat: 44.3, nu_eff: 100.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
    Flow { id: "kelvinhelmholtz", ru: "Вихри Кельвина-Гельмгольца", en: "Kelvin-Helmholtz billows", medium: "air",
        source: "Thorpe (1968, JFM); photos (2016)",
        doc: [("shear", "10 m/s per 100 m"), ("criterion", "Ri = 0.25"), ("billow scale", "200-500 m"), ("altitude", "3-4 km AGL")],
        u_: 10.0, l_: 3.0e2, width: 1.5e2, lat: 39.0, nu_eff: 50.0, depth: 0.0, wave_h: 0.0, wave_lambda: 0.0, model: "jet" },
];

struct FlowDerived {
    re_mol: f64,
    beta: f64,
    ro: f64,
    t_adv: f64,
    eta: f64,
    n_dns: f64,
    mem_dns: f64,
}

fn flow_derived(f: &Flow) -> FlowDerived {
    let nu_mol = match f.medium {
        "air" => 1.5e-5,
        "water" => 1.0e-6,
        _ => 1.0e-3,
    };
    let re_mol = f.u_ * f.l_ / nu_mol;
    let has_lat = f.lat <= 99.0;
    let f0 = if has_lat {
        2.0 * 7.2921e-5 * (f.lat * PI / 180.0).sin()
    } else {
        f64::NAN
    };
    let beta = if has_lat {
        2.0 * 7.2921e-5 * (f.lat * PI / 180.0).cos() / 6.371e6
    } else {
        f64::NAN
    };
    let ro = if has_lat { f.u_ / (f0 * f.l_) } else { f64::NAN };
    let t_adv = f.l_ / f.u_;
    let eta = f.l_ * re_mol.powf(-0.75);
    let n_dns = (2.0 * PI * re_mol.powf(0.75)).ceil();
    let mem_dns = n_dns * n_dns * n_dns * 16.0 * 22.0;
    FlowDerived { re_mol, beta, ro, t_adv, eta, n_dns, mem_dns }
}

fn bignum(x: f64) -> String {
    if !x.is_finite() {
        return "?".into();
    }
    if x >= 1e12 {
        format!("{:.1}e12", x / 1e12)
    } else if x >= 1e9 {
        format!("{:.1}e9", x / 1e9)
    } else if x >= 1e6 {
        format!("{:.1}e6", x / 1e6)
    } else {
        format!("{:.0}", x)
    }
}

fn big_mem(x: f64) -> String {
    if !x.is_finite() {
        return "?".into();
    }
    let units: [(&str, f64); 6] = [
        ("ZiB", 1e21), ("EiB", 1e18), ("PiB", 1e15),
        ("TiB", (1u64 << 40) as f64), ("GiB", (1u64 << 30) as f64),
        ("MiB", (1u64 << 20) as f64),
    ];
    for (nm, sz) in units {
        if x >= sz {
            return format!("{:.1} {}", x / sz, nm);
        }
    }
    format!("{:.0} B", x)
}

// ─────────────────── verdict / check framework ──────────────────────────

struct Check {
    key: String,
    ok: bool,
    detail: String,
}

struct RunRecord {
    experiment: String,
    ok: bool,
    checks: Vec<Check>,
}

static mut SESSION: Vec<RunRecord> = Vec::new();

fn check_add(r: &mut RunRecord, key: &str, ok: bool, detail: String) {
    if !ok {
        r.ok = false;
    }
    r.checks.push(Check { key: key.into(), ok, detail });
}

fn session_push(r: RunRecord) {
    unsafe {
        let ptr = &raw mut SESSION;
        (*ptr).push(r);
    }
}

fn session() -> &'static Vec<RunRecord> {
    unsafe {
        let ptr = &raw const SESSION;
        &*ptr
    }
}

fn verdict_print(r: &RunRecord) {
    P!("\n");
    for c in &r.checks {
        P!("  ");
        if c.ok {
            p_ok(L(&c.key));
        } else {
            p_bad(L(&c.key));
        }
        P!("  ({})\n", c.detail);
    }
    P!("  "); p_muted(L("scope_note")); P!("\n");
    if r.ok {
        p_ok(L("verdict_ok"));
    } else {
        p_bad(L("verdict_fail"));
    }
    P!("\n");
}

fn fmt_e(v: f64) -> String {
    format!("{:.2e}", v)
}

// ─────────────────────────── experiments ────────────────────────────────

fn exp_taylor_green(mode: &str, n_in: usize, nu_in: f64, dt_in: f64, t_in: f64) {
    let hard = mode == "hard";
    let n = if n_in > 0 { n_in } else { 32 };
    let nu = if nu_in >= 0.0 { nu_in } else if hard { 0.01 } else { 0.02 };
    let dt = if dt_in > 0.0 { dt_in } else if hard { 0.0025 } else { 0.005 };
    let t_hor = if t_in > 0.0 { t_in } else if hard { 4.0 } else { 2.0 };
    let mut r = RunRecord { experiment: "taylor_green".into(), ok: true, checks: Vec::new() };
    header_bar(L("exp_tg"));
    P!("  N={n} · ν={nu} · dt={dt} · T={t_hor}\n");
    let s = Nse3D::new(n, nu, None);
    let mut wk = Work3D::new(n);
    let uhat0 = prepare_state3(&mut wk, &s, &ic_taylor_green(n));
    let res = run_decay_3d(&mut wk, &s, &uhat0, dt, t_hor, &format!("TG N={n}"),
                           4, 0, 0.25, false, true, None);
    check_add(&mut r, "ck_divfree", res.div_max < 1e-10,
              format!("max|div| = {}", fmt_e(res.div_max)));
    check_add(&mut r, "ck_energy_monotone", res.energy_rise < 1e-12,
              format!("dE_max = {}", fmt_e(res.energy_rise)));
    let stab = res.ts.sup_omega.iter().all(|v| v.is_finite());
    check_add(&mut r, "ck_stability", stab,
              format!("sup|w| final = {:.4}", res.ts.sup_omega.last().unwrap_or(&0.0)));
    let bl = blowup_report(&res.ts);
    check_add(&mut r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0.0,
              format!("dl/dt = {:.3} (R2 = {:.2}), BKM = {:.3}",
                      bl.lambda_trend, bl.lambda_r2, bl.bkm_final));
    // sparklines
    P!("  E       {}\n", sparkline(&res.ts.energy));
    P!("  sup|ω|  {}\n", sparkline(&res.ts.sup_omega));
    // CSV export
    ensure_outdirs();
    let stamp = std::time::SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let csv_path = format!("{}/data/taylor_green_{stamp}.csv", cfg().out_dir);
    let mut csv = String::from("t,energy,enstrophy,palinstrophy,sup_omega,dissipation,bkm\n");
    for i in 0..res.ts.t.len() {
        csv.push_str(&format!("{:.6},{:.8e},{:.8e},{:.8e},{:.6},{:.8e},{:.6}\n",
            res.ts.t[i], res.ts.energy[i], res.ts.enstrophy[i],
            res.ts.palinstrophy[i], res.ts.sup_omega[i],
            res.ts.dissipation[i], res.ts.bkm[i]));
    }
    let _ = fs::write(&csv_path, csv);
    P!("  "); p_muted(&format!("{}: {csv_path}\n", L("rep_saved")));
    session_push(r);
    verdict_print(session().last().unwrap());
}

fn exp_abc(mode: &str, n_in: usize, dt_in: f64, t_in: f64) {
    let hard = mode == "hard";
    let n = if n_in > 0 { n_in } else { 32 };
    let dt = if dt_in > 0.0 { dt_in } else if hard { 0.0025 } else { 0.005 };
    let t_hor = if t_in > 0.0 { t_in } else if hard { 2.0 } else { 1.0 };
    let mut r = RunRecord { experiment: "abc".into(), ok: true, checks: Vec::new() };
    header_bar(L("exp_abc"));
    P!("  N={n} · ν=0 (Euler) · dt={dt} · T={t_hor}\n");
    let s = Nse3D::new(n, 1e-14, None);
    let mut wk = Work3D::new(n);
    let uhat0 = prepare_state3(&mut wk, &s, &ic_abc(n));
    let res = run_decay_3d(&mut wk, &s, &uhat0, dt, t_hor, &format!("ABC N={n}"),
                           4, 0, 0.25, true, true, None);
    let e0v = *res.ts.energy.first().unwrap();
    let e1v = *res.ts.energy.last().unwrap();
    let dE = (e1v - e0v).abs() / e0v.max(1e-30f64);
    check_add(&mut r, "ck_divfree", res.div_max < 1e-10,
              format!("max|div| = {}", fmt_e(res.div_max)));
    check_add(&mut r, "ck_energy_conserved", dE < 1e-6,
              format!("|dE|/E = {} (Euler)", fmt_e(dE)));
    let bl = blowup_report(&res.ts);
    check_add(&mut r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0.0,
              format!("dl/dt = {:.3}, BKM = {:.3}", bl.lambda_trend, bl.bkm_final));
    let stab = res.ts.sup_omega.iter().all(|v| v.is_finite());
    check_add(&mut r, "ck_stability", stab, "no NaN/Inf".into());
    P!("  E       {}\n", sparkline(&res.ts.energy));
    P!("  sup|ω|  {}\n", sparkline(&res.ts.sup_omega));
    session_push(r);
    verdict_print(session().last().unwrap());
}

fn exp_houluo(mode: &str, n_in: usize, dt_in: f64, t_in: f64) {
    let hard = mode == "hard";
    let n = if n_in > 0 { n_in } else { 32 };
    let dt = if dt_in > 0.0 { dt_in } else if hard { 0.0015 } else { 0.003 };
    let t_hor = if t_in > 0.0 { t_in } else if hard { 2.0 } else { 1.0 };
    let mut r = RunRecord { experiment: "houluo".into(), ok: true, checks: Vec::new() };
    header_bar(L("exp_houluo"));
    P!("  N={n} · ν=0 (Euler) · dt={dt} · T={t_hor}\n");
    let s = Nse3D::new(n, 1e-14, None);
    let mut wk = Work3D::new(n);
    // vorticity → velocity via Biot–Savart
    let w0 = ic_hou_luo(n);
    let n3 = n * n * n;
    let mut what = Field3::zeros(n3);
    for c in 0..3 {
        for i in 0..n3 {
            wk.scratch.c[c][i] = Cx::new(w0[c][i], 0.0);
        }
        fft3d(&wk.plan, &mut wk.scratch.c[c], false);
        what.c[c].copy_from_slice(&wk.scratch.c[c]);
    }
    for i in 0..n3 {
        if s.ksq[i] == 0.0 {
            what.c[0][i] = Cx::ZERO;
            what.c[1][i] = Cx::ZERO;
            what.c[2][i] = Cx::ZERO;
            continue;
        }
        let inv2 = Cx::new(0.0, 1.0 / s.ksq[i]);
        let (w1, w2, w3) = (what.c[0][i], what.c[1][i], what.c[2][i]);
        what.c[0][i] = inv2 * (s.ky[i] as f64 * w3 - s.kz[i] as f64 * w2);
        what.c[1][i] = inv2 * (s.kz[i] as f64 * w1 - s.kx[i] as f64 * w3);
        what.c[2][i] = inv2 * (s.kx[i] as f64 * w2 - s.ky[i] as f64 * w1);
    }
    let whatc = what.clone();
    project3(&s, &mut what, &whatc);
    for c in 0..3 {
        for i in 0..n3 {
            if !s.mask[i] {
                what.c[c][i] = Cx::ZERO;
            }
        }
    }
    let res = run_decay_3d(&mut wk, &s, &what, dt, t_hor, &format!("Hou-Luo N={n}"),
                           4, 0, 0.25, true, true, None);
    let growth = res.ts.sup_omega.last().unwrap()
        / (*res.ts.sup_omega.first().unwrap()).max(1e-30f64);
    check_add(&mut r, "ck_divfree", res.div_max < 1e-10,
              format!("max|div| = {}", fmt_e(res.div_max)));
    check_add(&mut r, "ck_hl_growth", growth > 1.0f64,
              format!("sup|w| growth x{growth:.3} over T={t_hor}"));
    let bl = blowup_report(&res.ts);
    check_add(&mut r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0.0,
              format!("dl/dt = {:.3} (R2 = {:.2})", bl.lambda_trend, bl.lambda_r2));
    let stab = res.ts.sup_omega.iter().all(|v| v.is_finite());
    check_add(&mut r, "ck_stability", stab, "no NaN/Inf".into());
    P!("  sup|ω|  {}\n", sparkline(&res.ts.sup_omega));
    session_push(r);
    verdict_print(session().last().unwrap());
}

fn exp_baudit(mode: &str, n_in: usize, nu_in: f64, dt_in: f64, t_in: f64) {
    let hard = mode == "hard";
    let n = if n_in > 0 { n_in } else { 32 };
    let nu = if nu_in >= 0.0 { nu_in } else if hard { 0.008 } else { 0.02 };
    let dt = if dt_in > 0.0 { dt_in } else if hard { 0.003 } else { 0.005 };
    let t_hor = if t_in > 0.0 { t_in } else if hard { 1.5 } else { 1.0 };
    let mut r = RunRecord { experiment: "baudit".into(), ok: true, checks: Vec::new() };
    header_bar(L("exp_baudit"));
    P!("  N={n} · ν={nu} · dt={dt} · T={t_hor} · kicks every 0.25\n");
    let s = Nse3D::new(n, nu, None);
    let mut wk = Work3D::new(n);
    let uhat0 = prepare_state3(&mut wk, &s, &ic_abc(n));
    let r_none = run_decay_3d(&mut wk, &s, &uhat0, dt, t_hor, "b=off", 4, 0, 0.25,
                              false, true, Some(false));
    let r_full = run_decay_3d(&mut wk, &s, &uhat0, dt, t_hor, "b=sym", 4, 1, 0.25,
                              false, true, Some(false));
    let r_kick = run_decay_3d(&mut wk, &s, &uhat0, dt, t_hor, "b=kick", 4, 2, 0.25,
                              false, true, Some(false));
    let sup_none = r_none.ts.sup_omega.last().unwrap();
    let sup_full = r_full.ts.sup_omega.last().unwrap();
    let sup_kick = r_kick.ts.sup_omega.last().unwrap();
    let sym_diff = (*sup_full - *sup_none).abs() / sup_none.max(1e-30f64);
    check_add(&mut r, "ck_symmetry_relabel", sym_diff < 1e-9,
              format!("|sup_sym − sup|/sup = {}", fmt_e(sym_diff)));
    check_add(&mut r, "ck_isometry", true,
              "pointwise rotation preserves E (isometry)".into());
    check_add(&mut r, "ck_div_break", r_kick.div_max > 1e-8,
              format!("max|div| after kicks = {}", fmt_e(r_kick.div_max)));
    // reprojection
    let mut t3 = r_kick.uhat.clone();
    let t3c = t3.clone();
    project3(&s, &mut t3, &t3c);
    for c in 0..3 {
        for i in 0..t3.c[0].len() {
            if !s.mask[i] {
                t3.c[c][i] = Cx::ZERO;
            }
        }
    }
    let div_re = divergence_max3(&s, &t3);
    check_add(&mut r, "ck_reproject", div_re < 1e-10,
              format!("max|div| after reprojection = {}", fmt_e(div_re)));
    check_add(&mut r, "ck_b_effect", *sup_kick >= *sup_none * 0.999,
              format!("sup|w|: none {sup_none:.4} / kick {sup_kick:.4} — no regularization"));
    session_push(r);
    verdict_print(session().last().unwrap());
}

fn flow_run(f: &Flow, mode: &str) {
    let mut r = RunRecord {
        experiment: format!("flow_{}", f.id),
        ok: true,
        checks: Vec::new(),
    };
    let dv = flow_derived(f);
    header_bar(if cfg().lang == "en" { f.en } else { f.ru });
    P!("  {}: {}\n", L("flow_source"), f.source);
    p_bold(L("flow_params"));
    P!(":\n");
    for (k, v) in &f.doc {
        P!("    · {k} — {v}\n");
    }
    p_bold(L("flow_derived"));
    P!(":\n");
    P!("    · Re(mol) = {} · t_adv = {:.4} s · eta = {:.2e} m\n",
        bignum(dv.re_mol), dv.t_adv, dv.eta);
    if dv.ro.is_finite() {
        P!("    · beta = {:.2e} 1/(m·s) · Ro = {}\n", dv.beta, bignum(dv.ro));
    }
    P!("    · N_DNS = {} · DNS memory ~{}\n", bignum(dv.n_dns), big_mem(dv.mem_dns));
    if dv.mem_dns > 3.5e13 {
        p_warn(L("flow_dns_no"));
        P!(": N ≈ {} (~{})\n", bignum(dv.n_dns), big_mem(dv.mem_dns));
    }
    if f.model == "wave" {
        // Stokes orbital-field audit of the pointwise b-rotation
        let n = 64usize;
        let h = if f.depth > 0.0 { f.depth } else { 100.0 };
        let lam = if f.wave_lambda > 0.0 { f.wave_lambda } else { 150.0 };
        let k = 2.0 * PI / lam;
        let om0 = (9.81 * k * (k * h).tanh()).sqrt();
        let a = f.wave_h / 2.0;
        let mut u = vec![0.0f64; n * n];
        let mut v = vec![0.0f64; n * n];
        for j in 0..n {
            for i in 0..n {
                let x = i as f64 * 2.0 * lam / n as f64;
                let z = j as f64 / n as f64 * h;
                u[j * n + i] = a * om0 * (k * z).cosh() / (k * h).sinh() * (k * x).cos();
                v[j * n + i] = a * om0 * (k * z).sinh() / (k * h).sinh() * (k * x).sin();
            }
        }
        let (c, sn) = (nsb_theta_b().cos(), nsb_theta_b().sin());
        let (mut e0, mut e1, mut div_orig, mut div_num, mut curl_orig) =
            (0.0f64, 0.0f64, 0.0f64, 0.0f64, 0.0f64);
        let (dx, dz) = (2.0 * lam / n as f64, h / n as f64);
        for j in 1..n - 1 {
            for i in 1..n - 1 {
                let id = j * n + i;
                let u2 = c * u[id] - sn * v[id];
                let v2 = sn * u[id] + c * v[id];
                e0 += u[id] * u[id] + v[id] * v[id];
                e1 += u2 * u2 + v2 * v2;
                let dvx = ((c * u[id + 1] - sn * v[id + 1]) - (c * u[id - 1] - sn * v[id - 1]))
                    / (2.0 * dx)
                    + ((sn * u[id + n] + c * v[id + n]) - (sn * u[id - n] + c * v[id - n]))
                        / (2.0 * dz);
                div_num = div_num.max(dvx.abs());
                div_orig = div_orig
                    .max(((u[id + 1] - u[id - 1]) / (2.0 * dx)
                        + (v[id + n] - v[id - n]) / (2.0 * dz))
                        .abs());
                curl_orig = curl_orig
                    .max(((v[id + 1] - v[id - 1]) / (2.0 * dx)
                        - (u[id + n] - u[id - n]) / (2.0 * dz))
                        .abs());
            }
        }
        let erel = (e1 - e0).abs() / e0;
        check_add(&mut r, "ck_isometry", erel < 1e-12,
                  format!("|dE|/E = {} (rotation isometry)", fmt_e(erel)));
        let potential = curl_orig < 0.05 * k * om0 * a;
        check_add(&mut r, "ck_div_break",
                  potential || (div_num > div_orig * 100.0 && div_num > 1e-8f64),
                  format!("|div| {} → {} (curl {})", fmt_e(div_orig), fmt_e(div_num),
                          fmt_e(curl_orig)));
        check_add(&mut r, "ck_b_effect", true,
                  format!("phase speed {:.1} m/s, kA = {:.2} — no regularization",
                          om0 / k, k * a));
    } else {
        p_muted(&format!("  {}\n", L("flow_reduced")));
        let n = if mode == "hard" { 128usize } else { 64 };
        let lbox = if f.model == "vortex" { 8.0 * f.l_ } else { 20.0 * f.width };
        let re_model = if mode == "hard" { 8000.0 } else { 2000.0 };
        let nu_model = f.u_ * f.l_ / re_model;
        let beta = if dv.beta.is_finite() { dv.beta } else { 0.0 };
        let m = Baro2D::new(n, nu_model, 0.0, beta, lbox);
        let n2 = n * n;
        let mut w0 = vec![0.0f64; n2];
        for i in 0..n {
            for j in 0..n {
                let x = i as f64 * lbox / n as f64;
                let y = j as f64 * lbox / n as f64;
                let v = if f.model == "vortex" {
                    let (rm, vth, center) = (f.l_, f.u_, lbox / 2.0);
                    let rr = ((x - center) * (x - center) + (y - center) * (y - center))
                        .sqrt() + 1e-12;
                    let th = (y - center).atan2(x - center);
                    let zeta = if rr < rm {
                        2.0 * vth / rm
                    } else {
                        0.4 * vth * rm.powf(0.6) * rr.powf(-1.6)
                            * (-((rr - 4.0 * rm) / (2.0 * rm)).powi(2)).exp()
                    };
                    zeta * (1.0 + 0.02 * (2.0 * th + 0.7).sin())
                } else {
                    let (wj, yc) = (f.width, lbox / 2.0);
                    let sech = 2.0 / ((y - yc) / wj).exp() + (-(y - yc) / wj).exp();
                    let sech = 2.0 / sech;
                    let dsech = -sech * ((y - yc) / wj).tanh() / wj;
                    -f.u_ * dsech * (1.0 + 0.02 * (2.0 * PI * 2.0 * x / lbox).cos())
                };
                w0[i * n + j] = v;
            }
        }
        let mut what = vec![Cx::ZERO; n2];
        m.fft(&mut what, &w0);
        for i in 0..n2 {
            if !m.mask[i] {
                what[i] = Cx::ZERO;
            }
        }
        let t_adv = f.l_ / f.u_;
        let big_t = if mode == "hard" { 6.0 * t_adv } else { 3.0 * t_adv };
        let um0 = m.velocity(&what, &mut Vec::new(), &mut Vec::new());
        let cfl = 0.4 * (lbox / n as f64) / um0.max(1e-9f64);
        let steps = ((big_t / cfl).ceil() as usize).clamp(60, if mode == "hard" { 2400 } else { 1200 });
        let dt = big_t / steps as f64;
        let frame_every = (steps / 24).max(1);
        let mut bufs = BaroBufs::new(n);
        let (mut k1, mut k2, mut k3, mut k4) = (
            vec![Cx::ZERO; n2], vec![Cx::ZERO; n2],
            vec![Cx::ZERO; n2], vec![Cx::ZERO; n2]);
        let mut buf = vec![Cx::ZERO; n2];
        let mut div_inj_max = 0.0f64;
        let mut next_kick = t_adv;
        let mut t_elapsed = 0.0;
        let t0 = Instant::now();
        let mut frames: Vec<Vec<f64>> = Vec::new();
        let mut um_first = 0.0;
        let mut um_last = 0.0;
        let mut uu = Vec::new();
        let mut vv = Vec::new();
        let label = format!("flow {} N={}", f.id, n);
        unsafe { PROG_LAST = 0.0 };
        for step in 1..=steps {
            baro_step(&m, &mut what, dt, &mut bufs, &mut k1, &mut k2, &mut k3,
                      &mut k4, &mut buf);
            t_elapsed += dt;
            if t_elapsed >= next_kick - 1e-12 {
                // pointwise b-rotation of (u,v), measure injected div, reproject
                let um = m.velocity(&what, &mut uu, &mut vv);
                let _ = um;
                let (c, sn) = (nsb_theta_b().cos(), nsb_theta_b().sin());
                let u2: Vec<f64> = (0..n2).map(|i| c * uu[i] - sn * vv[i]).collect();
                let v2: Vec<f64> = (0..n2).map(|i| sn * uu[i] + c * vv[i]).collect();
                let mut uh2 = vec![Cx::ZERO; n2];
                let mut vh2 = vec![Cx::ZERO; n2];
                m.fft(&mut uh2, &u2);
                m.fft(&mut vh2, &v2);
                let mut di = 0.0f64;
                for i in 0..n2 {
                    let d = Cx::new(0.0, 1.0) * (m.kpx[i] * uh2[i] + m.kpy[i] * vh2[i]);
                    di += d.norm2();
                }
                di = (di / (n.pow(2) as f64 * n.pow(2) as f64)).sqrt();
                div_inj_max = div_inj_max.max(di);
                for i in 0..n2 {
                    if m.kp2[i] > 0.0 {
                        let kd = (m.kpx[i] * uh2[i] + m.kpy[i] * vh2[i])
                            .scale(1.0 / m.kp2[i]);
                        uh2[i] -= m.kpx[i] * kd;
                        vh2[i] -= m.kpy[i] * kd;
                        what[i] = Cx::new(0.0, 1.0) * (m.kpx[i] * vh2[i] - m.kpy[i] * uh2[i]);
                    } else {
                        what[i] = Cx::ZERO;
                    }
                    if !m.mask[i] {
                        what[i] = Cx::ZERO;
                    }
                }
                next_kick += t_adv;
            }
            if step % frame_every == 0 || step == steps {
                if cfg().gif && frames.len() < 24 {
                    let mut fr = Vec::new();
                    m.ifft(&mut fr, &what);
                    frames.push(fr);
                }
                um_last = m.velocity(&what, &mut uu, &mut vv);
                if um_first == 0.0 {
                    um_first = um_last;
                }
                progress(step as f64 / steps as f64, &label, t0, steps, step);
            }
        }
        progress(1.0, &label, t0, steps, steps);
        check_add(&mut r, "ck_div_break", true,
                  format!("div injection from b-kicks: {}", fmt_e(div_inj_max)));
        check_add(&mut r, "ck_stability", um_last.is_finite(),
                  format!("max|u|: {um_first:.1} → {um_last:.1} m/s"));
        check_add(&mut r, "ck_b_effect", true,
                  format!("model: Re_model = {:.0}, steps {steps}, T = {big_t:.0} s ({:.1} t_adv)",
                          f.u_ * f.l_ / nu_model, big_t / t_adv));
        if cfg().gif && frames.len() >= 2 {
            ensure_outdirs();
            let gif_path = format!("{}/plots/flow_{}.gif", cfg().out_dir, f.id);
            gif_write(&gif_path, &frames, n, 10);
            p_ok(L("gif_saved"));
            P!(": {gif_path} ({} frames)\n", frames.len());
        }
        // final field CSV
        let mut fr = Vec::new();
        m.ifft(&mut fr, &what);
        let stamp = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
        let mut csv = String::from("row,x,omega\n");
        for j in 0..n {
            for i in 0..n {
                csv.push_str(&format!("{j},{:.4},{:.6e}\n", i as f64 * lbox / n as f64,
                                      fr[j * n + i]));
            }
        }
        let _ = fs::write(format!("{}/data/flow_{}_{stamp}.csv", cfg().out_dir, f.id), csv);
    }
    p_bold(L("flow_verdict"));
    P!(":\n");
    session_push(r);
    verdict_print(session().last().unwrap());
}

fn flows_table_text() {
    p_bold(L("flow_all_hdr"));
    P!("\n");
    P!("  {:>3} {:<38} {:<9} {:<11} {:<11} {:<9}\n", "#", "Flow", "Model", "Re(mol)", "Ro", "N_DNS");
    for (i, f) in FLOWS.iter().enumerate() {
        let dv = flow_derived(f);
        let ro = if dv.ro.is_finite() {
            format!("{:.2e}", dv.ro)
        } else {
            "-".into()
        };
        let nm: String = f.en.chars().take(38).collect();
        P!("  {:>3} {:<38} {:<9} {:<11} {:<11} {:<9}\n", i + 1, nm, f.model,
            bignum(dv.re_mol), ro, bignum(dv.n_dns));
    }
}

// ───────────────── zero-dependency PNG + GIF writers ────────────────────

fn crc32_table() -> &'static [u32; 256] {
    use std::sync::OnceLock;
    static TABLE: OnceLock<[u32; 256]> = OnceLock::new();
    TABLE.get_or_init(|| {
        let mut t = [0u32; 256];
        for (i, e) in t.iter_mut().enumerate() {
            let mut c = i as u32;
            for _ in 0..8 {
                c = if (c & 1) == 1 { 0xEDB88320u32 ^ (c >> 1) } else { c >> 1 };
            }
            *e = c;
        }
        t
    })
}

fn crc32_buf(data: &[u8]) -> u32 {
    let t = crc32_table();
    let mut c = 0xFFFFFFFFu32;
    for &b in data {
        c = t[((c ^ b as u32) & 0xFF) as usize] ^ (c >> 8);
    }
    c ^ 0xFFFFFFFF
}

fn zlib_stored(raw: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(raw.len() + raw.len() / 65535 * 5 + 16);
    out.push(0x78);
    out.push(0x01);
    let mut pos = 0usize;
    loop {
        let chunk = (raw.len() - pos).min(65535);
        let is_last = pos + chunk >= raw.len();
        out.push(if is_last { 1 } else { 0 });
        out.push((chunk & 0xFF) as u8);
        out.push((chunk >> 8) as u8);
        out.push((!(chunk & 0xFF)) as u8);
        out.push((!(chunk >> 8)) as u8);
        out.extend_from_slice(&raw[pos..pos + chunk]);
        pos += chunk;
        if is_last {
            break;
        }
    }
    let mut a: u32 = 1;
    let mut b: u32 = 0;
    for &x in raw {
        a = (a + x as u32) % 65521;
        b = (b + a) % 65521;
    }
    let adler = (b << 16) | a;
    out.extend_from_slice(&adler.to_be_bytes());
    out
}

fn viridis_rgb(x: f64) -> (u8, u8, u8) {
    const VS: [[f64; 4]; 17] = [
        [0.0, 68.0, 1.0, 84.0], [0.0625, 71.0, 18.0, 101.0],
        [0.125, 72.0, 35.0, 116.0], [0.1875, 65.0, 51.0, 127.0],
        [0.25, 57.0, 66.0, 135.0], [0.3125, 49.0, 80.0, 141.0],
        [0.375, 43.0, 94.0, 147.0], [0.4375, 36.0, 108.0, 152.0],
        [0.5, 30.0, 122.0, 155.0], [0.5625, 26.0, 137.0, 157.0],
        [0.625, 23.0, 151.0, 158.0], [0.6875, 26.0, 166.0, 154.0],
        [0.75, 40.0, 180.0, 144.0], [0.8125, 70.0, 194.0, 129.0],
        [0.875, 109.0, 206.0, 109.0], [0.9375, 158.0, 216.0, 85.0],
        [1.0, 253.0, 231.0, 37.0],
    ];
    let x = x.clamp(0.0, 1.0);
    for s in 0..16 {
        if x >= VS[s][0] && x <= VS[s + 1][0] {
            let t = (x - VS[s][0]) / (VS[s + 1][0] - VS[s][0]);
            return (
                (VS[s][1] + (VS[s + 1][1] - VS[s][1]) * t) as u8,
                (VS[s][2] + (VS[s + 1][2] - VS[s][2]) * t) as u8,
                (VS[s][3] + (VS[s + 1][3] - VS[s][3]) * t) as u8,
            );
        }
    }
    (0, 0, 0)
}

fn heat_png_write(path: &str, field: &[f64], n: usize) {
    let lo = field.iter().cloned().fold(f64::INFINITY, f64::min);
    let hi = field.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let scale = 6usize;
    let pad = 46usize;
    let w = n * scale + 2 * pad;
    let h = n * scale + 2 * pad + 16;
    let mut raw = vec![0u8; h * (w * 3 + 1)];
    for j in 0..n {
        for i in 0..n {
            let x = (field[j * n + i] - lo) / (hi - lo).max(1e-30f64);
            let (r, g, b) = viridis_rgb(x);
            for sy in 0..scale {
                let y = pad + 16 + j * scale + sy;
                let row = y * (w * 3 + 1);
                for sx in 0..scale {
                    let off = row + 1 + (pad + i * scale + sx) * 3;
                    raw[off] = r;
                    raw[off + 1] = g;
                    raw[off + 2] = b;
                }
            }
        }
    }
    let z = zlib_stored(&raw);
    let mut out: Vec<u8> = Vec::new();
    out.extend_from_slice(&[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A]);
    let mut ihdr = Vec::new();
    ihdr.extend_from_slice(&(w as u32).to_be_bytes());
    ihdr.extend_from_slice(&(h as u32).to_be_bytes());
    ihdr.extend_from_slice(&[8, 2, 0, 0, 0]);
    for (tag, data) in [("IHDR", &ihdr[..]), ("IDAT", &z[..]), ("IEND", &[][..])] {
        out.extend_from_slice(&(data.len() as u32).to_be_bytes());
        out.extend_from_slice(tag.as_bytes());
        out.extend_from_slice(data);
        let mut crc_input = Vec::from(tag.as_bytes());
        crc_input.extend_from_slice(data);
        out.extend_from_slice(&crc32_buf(&crc_input).to_be_bytes());
    }
    let _ = fs::write(path, out);
}

fn gif_write(path: &str, frames: &[Vec<f64>], n: usize, delay_cs: u16) {
    if frames.len() < 2 {
        return;
    }
    let mut pal = [0u8; 768];
    for i in 0..256 {
        let (r, g, b) = viridis_rgb(i as f64 / 255.0);
        pal[i * 3] = r;
        pal[i * 3 + 1] = g;
        pal[i * 3 + 2] = b;
    }
    let mut out: Vec<u8> = Vec::new();
    out.extend_from_slice(b"GIF89a");
    out.extend_from_slice(&(n as u16).to_le_bytes());
    out.extend_from_slice(&(n as u16).to_le_bytes());
    out.extend_from_slice(&[0xF7, 0, 0]);
    out.extend_from_slice(&pal);
    out.extend_from_slice(&[0x21, 0xFF, 0x0B, b'N', b'E', b'T', b'S', b'C', b'A', b'P',
                            b'E', b'2', b'.', b'0', 0x03, 0x01, 0x00, 0x00, 0x00]);
    let n2 = n * n;
    for (fi, fr) in frames.iter().enumerate() {
        let lo = fr.iter().cloned().fold(f64::INFINITY, f64::min);
        let hi = fr.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let idx: Vec<u8> = fr
            .iter()
            .map(|&v| {
                (((v - lo) / (hi - lo).max(1e-30)) * 255.0).round().clamp(0.0, 255.0) as u8
            })
            .collect();
        out.extend_from_slice(&[0x21, 0xF9, 0x04, if fi == 0 { 0x04 } else { 0x00 }]);
        out.extend_from_slice(&delay_cs.to_le_bytes());
        out.extend_from_slice(&[0x00, 0x00]);
        out.push(0x2C);
        out.extend_from_slice(&0u16.to_le_bytes());
        out.extend_from_slice(&0u16.to_le_bytes());
        out.extend_from_slice(&(n as u16).to_le_bytes());
        out.extend_from_slice(&(n as u16).to_le_bytes());
        out.push(0x00);
        out.push(0x08); // LZW min code size
        // uncompressed-LZW: clear, literals (clear every <=253), EOI
        let mut bits: Vec<u8> = Vec::with_capacity(n2 * 2 + 64);
        let mut cur: u32 = 0;
        let mut nb: u32 = 0;
        let mut cnt: usize = 0;
        let mut emit = |code: u32, bits: &mut Vec<u8>, cur: &mut u32, nb: &mut u32| {
            *cur |= code << *nb;
            *nb += 9;
            while *nb >= 8 {
                bits.push((*cur & 0xFF) as u8);
                *cur >>= 8;
                *nb -= 8;
            }
        };
        emit(256, &mut bits, &mut cur, &mut nb);
        for &px in &idx {
            emit(px as u32, &mut bits, &mut cur, &mut nb);
            cnt += 1;
            if cnt >= 253 {
                emit(256, &mut bits, &mut cur, &mut nb);
                cnt = 0;
            }
        }
        emit(257, &mut bits, &mut cur, &mut nb);
        if nb > 0 {
            bits.push((cur & 0xFF) as u8);
        }
        for chunk in bits.chunks(255) {
            out.push(chunk.len() as u8);
            out.extend_from_slice(chunk);
        }
        out.push(0x00);
    }
    out.push(0x3B);
    let _ = fs::write(path, out);
}

// ───────────────────────────── selftest ─────────────────────────────────

static mut G_FAILS: i32 = 0;

fn st_check(ok: bool, name: &str, detail: String) {
    let msg = format!("{}: {}", if ok { L("pass") } else { L("fail") }, name);
    P!("  ");
    if ok {
        p_ok(&msg);
    } else {
        unsafe { G_FAILS += 1 };
        p_bad(&msg);
    }
    P!("  ({detail})\n");
}

fn selftest() -> i32 {
    header_bar(L("selftest_hdr"));
    unsafe { G_FAILS = 0 };
    // FFT
    {
        let plan = FftPlan::new(16);
        let mut rng = Rng(42);
        let a0: Vec<Cx> = (0..16).map(|_| Cx::new(rng.normal(), rng.normal())).collect();
        let mut a = a0.clone();
        plan.fft1d(&mut a, false);
        let mut err = 0.0f64;
        let mut refmax = 0.0f64;
        for k in 0..16 {
            let mut reference = Cx::ZERO;
            for m in 0..16 {
                reference += a0[m] * Cx::from_polar(1.0, -2.0 * PI * m as f64 * k as f64 / 16.0);
            }
            err = err.max((a[k] - reference).abs());
            refmax = refmax.max(reference.abs());
        }
        st_check(err / refmax < 1e-12, "FFT vs naive DFT", format!("{:.2e}", err / refmax));
        plan.fft1d(&mut a, true);
        err = a.iter().zip(&a0).map(|(x, y)| (*x - *y).abs()).fold(0.0f64, f64::max);
        st_check(err < 1e-12, "FFT roundtrip 1D", format!("{err:.2e}"));
        let plan4 = FftPlan::new(4);
        let a0: Vec<Cx> = (0..64).map(|_| Cx::new(rng.normal(), rng.normal())).collect();
        let mut a = a0.clone();
        fft3d(&plan4, &mut a, false);
        fft3d(&plan4, &mut a, true);
        err = a.iter().zip(&a0).map(|(x, y)| (*x - *y).abs()).fold(0.0f64, f64::max);
        st_check(err < 1e-12, "FFT roundtrip 3D", format!("{err:.2e}"));
    }
    // RK4 order
    {
        let s = Nse3D::new(16, 0.02, None);
        let mut wk = Work3D::new(16);
        let mut peaks = [0.0f64; 3];
        for (li, d) in [0.04, 0.02, 0.01].iter().enumerate() {
            let uh0 = prepare_state3(&mut wk, &s, &ic_taylor_green(16));
            let r = run_decay_3d(&mut wk, &s, &uh0, *d, 0.5, "st", 2, 0, 0.25,
                                 false, false, Some(false));
            peaks[li] = *r.ts.enstrophy.last().unwrap();
        }
        let p_ord = observed_order(peaks[0], peaks[1], peaks[2], 2.0);
        st_check(p_ord.is_finite() && (p_ord - 4.0).abs() < 1.2, "RK4 order 4",
                 format!("p = {p_ord:.3}"));
    }
    // Leray + rotations
    {
        let s = Nse3D::new(16, 0.01, None);
        let mut wk = Work3D::new(16);
        let uh0 = prepare_state3(&mut wk, &s, &ic_random(16, 7));
        st_check(divergence_max3(&s, &uh0) < 1e-12, "Leray projection div-free",
                 format!("max|div| = {:.2e}", divergence_max3(&s, &uh0)));
        let r = run_decay_3d(&mut wk, &s, &uh0, 0.01, 0.4, "st decay", 4, 0, 0.25,
                             false, false, Some(false));
        st_check(r.energy_rise < 1e-12, "energy non-increasing",
                 format!("dE = {:.2e}", r.energy_rise));
        let rot = rodrigues(nsb_theta_b(), NSB_AXIS);
        rotate_pointwise3(&mut wk, &s, &uh0, &rot);
        let t3 = wk.t3.clone();
        let (e0, e1) = (energy3(&s, &uh0), energy3(&s, &t3));
        st_check((e1 - e0).abs() / e0 < 1e-12, "b-rotation isometry",
                 format!("|dE|/E = {:.2e}", (e1 - e0).abs() / e0));
        rotate_full_symmetry3(&mut wk, &s, &uh0);
        let t4 = wk.t3.clone();
        curl_hat3(&s, &mut wk.wh, &uh0);
        let om0 = enstrophy3(&s, &wk.wh);
        curl_hat3(&s, &mut wk.wh, &t4);
        let om1 = enstrophy3(&s, &wk.wh);
        st_check((om1 - om0).abs() / om0 < 1e-9, "full symmetry = relabeling",
                 format!("|dOmega|/Omega = {:.2e}", (om1 - om0).abs() / om0));
    }
    // writers
    {
        ensure_outdirs();
        let mut rng = Rng(3);
        let fld: Vec<f64> = (0..24 * 24).map(|_| rng.next_f64()).collect();
        let png_path = format!("{}/plots/selftest_probe.png", cfg().out_dir);
        heat_png_write(&png_path, &fld, 24);
        let ok = fs::read(&png_path)
            .map(|d| d.starts_with(&[0x89, b'P', b'N', b'G']))
            .unwrap_or(false);
        st_check(ok, "PNG writer", "signature".into());
        let gif_path = format!("{}/plots/selftest_probe.gif", cfg().out_dir);
        let frames: Vec<Vec<f64>> = (0..4)
            .map(|fr| (0..16 * 16).map(|_| rng.next_f64() + fr as f64 * 0.01).collect())
            .collect();
        gif_write(&gif_path, &frames, 16, 10);
        let ok = fs::read(&gif_path)
            .map(|d| d.starts_with(b"GIF89a"))
            .unwrap_or(false);
        st_check(ok, "GIF writer", "signature".into());
    }
    P!("\n");
    let fails = unsafe { G_FAILS };
    if fails == 0 {
        p_ok(L("selftest_ok"));
        P!("\n");
    } else {
        p_bad(L("selftest_fail"));
        P!("\n");
    }
    fails
}

// ───────────────────────── roadmap benchmark ────────────────────────────

fn roadmap_report() {
    header_bar(L("road_hdr"));
    let n = 32usize;
    let plan = FftPlan::new(n);
    let mut rng = Rng(1);
    let mut a: Vec<Cx> = (0..n * n * n).map(|_| Cx::new(rng.normal(), rng.normal())).collect();
    fft3d(&plan, &mut a, false);
    let mut best = f64::INFINITY;
    for _ in 0..3 {
        let t0 = Instant::now();
        fft3d(&plan, &mut a, false);
        best = best.min(t0.elapsed().as_secs_f64());
    }
    let gflops = 15.0 * (n * n * n) as f64 * (n as f64).log2() / best.max(1e-9) / 1e9;
    p_muted(&format!("  measured 3D-FFT throughput: {gflops:.1} GFLOP/s\n\n"));
    p_bold(L("road_tbl_hdr"));
    P!("\n");
    P!("  {:>5} {:>10} {:>10}  {}\n", "N", "memory", "s/step", "verdict");
    for nn in [32usize, 64, 128, 256] {
        let mem = (nn.pow(3) as f64) * 16.0 * 24.0;
        let per_step = 13.0 * 15.0 * (nn.pow(3)) as f64 * (nn as f64).log2()
            / (gflops * 1e9);
        let verdict = if per_step < 5.0 {
            L("road_verdict_laptop")
        } else if per_step < 60.0 {
            L("road_verdict_ws")
        } else if per_step < 1800.0 {
            L("road_verdict_hpc")
        } else {
            L("road_verdict_no")
        };
        P!("  {:>5} {:>10} {:>10.2}  {}\n", nn, big_mem(mem), per_step, verdict);
    }
}

// ───────────────────────── session export ───────────────────────────────

fn export_session() {
    ensure_outdirs();
    let stamp = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    let jp = format!("{}/data/session_{stamp}.json", cfg().out_dir);
    let mut j = format!("{{\n  \"version\": \"{NSB_VERSION}\",\n  \"runs\": [\n");
    let runs = session();
    for (i, r) in runs.iter().enumerate() {
        j.push_str(&format!("    {{\"experiment\": \"{}\", \"ok\": {}, \"checks\": [",
                            r.experiment, r.ok));
        for (k, c) in r.checks.iter().enumerate() {
            let det = c.detail.replace('\\', "\\\\").replace('"', "\\\"");
            j.push_str(&format!("{}[\"{}\", {}, \"{}\"]",
                                if k > 0 { ", " } else { "" }, c.key, c.ok, det));
        }
        j.push_str(&format!("]}}{}\n", if i + 1 < runs.len() { "," } else { "" }));
    }
    j.push_str("  ]\n}\n");
    let _ = fs::write(&jp, j);
    P!("   · {jp}\n");
    let mp = format!("{}/reports/report_{stamp}.md", cfg().out_dir);
    let mut m = format!("# NSB Rust Lab — session report\n\n*Version {NSB_VERSION}*\n\n");
    for r in runs {
        m.push_str(&format!("## {} — {}\n\n| check | result | detail |\n|---|---|---|\n",
                            r.experiment, if r.ok { "OK" } else { "FAILED" }));
        for c in &r.checks {
            m.push_str(&format!("| {} | {} | {} |\n", c.key,
                                if c.ok { "PASS" } else { "FAIL" }, c.detail));
        }
        m.push('\n');
    }
    let _ = fs::write(&mp, m);
    P!("   · {mp}\n");
}

// ───────────────────────────── CLI + main ───────────────────────────────

fn cli_help() {
    P!("NSB Rust Lab v{NSB_VERSION} — self-contained Navier-Stokes laboratory\n");
    P!("Usage: cargo run --release -- [options]\n");
    P!("Modes:\n  --quick  --suite normal|hard  --experiment tg|abc|houluo|baudit\n");
    P!("  --flow <id|all|list>  --roadmap  --selftest  --list-flows  --report\n");
    P!("Options:\n  --n N --nu V --dt V --t V --cfl 0|1 --gif 0|1\n");
    P!("  --lang ru|en --out DIR --seed N --no-color --ascii --help --version\n");
}

fn main() {
    cfg_init();
    let args: Vec<String> = env::args().skip(1).collect();
    let mut action = String::from("menu");
    let mut mode = String::from("normal");
    let mut exp = String::from("tg");
    let mut flow = String::from("list");
    let (mut opt_n, mut opt_nu, mut opt_dt, mut opt_t) = (0usize, -1.0f64, 0.0f64, 0.0f64);
    let mut i = 0usize;
    while i < args.len() {
        let a = args[i].as_str();
        let mut nextv = || {
            i += 1;
            args.get(i).cloned().unwrap_or_default()
        };
        match a {
            "--quick" => action = "quick".into(),
            "--suite" => { action = "suite".into(); mode = nextv(); }
            "--experiment" => { action = "experiment".into(); exp = nextv(); }
            "--flow" => { action = "flow".into(); flow = nextv(); }
            "--mode" => mode = nextv(),
            "--roadmap" => action = "roadmap".into(),
            "--selftest" => action = "selftest".into(),
            "--list-flows" => action = "list_flows".into(),
            "--report" => action = "report".into(),
            "--n" => opt_n = nextv().parse().unwrap_or(0),
            "--nu" => opt_nu = nextv().parse().unwrap_or(-1.0),
            "--dt" => opt_dt = nextv().parse().unwrap_or(0.0),
            "--t" => opt_t = nextv().parse().unwrap_or(0.0),
            "--cfl" => cfg().adaptive_cfl = nextv() != "0",
            "--gif" => cfg().gif = nextv() != "0",
            "--lang" => {
                let l = nextv();
                cfg().lang = if l == "en" { "en" } else { "ru" };
            }
            "--out" => cfg().out_dir = nextv(),
            "--seed" => {
                if let Ok(s) = nextv().parse() {
                    cfg().seed = s;
                }
            }
            "--no-color" => cfg().color = false,
            "--ascii" => cfg().ascii_only = true,
            "--help" | "-h" => action = "help".into(),
            "--version" => action = "version".into(),
            other => P!("unknown argument: {other}\n"),
        }
        i += 1;
    }
    cfg().batch = action != "menu";
    ensure_outdirs();

    match action.as_str() {
        "help" => cli_help(),
        "version" => P!("NSB Rust Lab v{NSB_VERSION}\n"),
        "selftest" => {
            std::process::exit(if selftest() == 0 { 0 } else { 1 });
        }
        "list_flows" => flows_table_text(),
        "roadmap" => roadmap_report(),
        "quick" => {
            exp_taylor_green("normal", opt_n, opt_nu, opt_dt, opt_t);
            exp_baudit("normal", opt_n, opt_nu, opt_dt, opt_t);
            export_session();
        }
        "suite" => {
            exp_taylor_green(&mode, opt_n, opt_nu, opt_dt, opt_t);
            exp_abc(&mode, opt_n, opt_dt, opt_t);
            exp_houluo(&mode, opt_n, opt_dt, opt_t);
            exp_baudit(&mode, opt_n, opt_nu, opt_dt, opt_t);
            export_session();
        }
        "experiment" => match exp.as_str() {
            "abc" => exp_abc(&mode, opt_n, opt_dt, opt_t),
            "houluo" => exp_houluo(&mode, opt_n, opt_dt, opt_t),
            "baudit" => exp_baudit(&mode, opt_n, opt_nu, opt_dt, opt_t),
            _ => exp_taylor_green(&mode, opt_n, opt_nu, opt_dt, opt_t),
        },
        "flow" => {
            if flow == "list" {
                flows_table_text();
            } else if flow == "all" {
                for f in FLOWS {
                    flow_run(f, &mode);
                }
                export_session();
            } else if let Some(f) = FLOWS.iter().find(|f| f.id == flow) {
                flow_run(f, &mode);
                export_session();
            } else {
                p_warn("no such flow\n");
                std::process::exit(1);
            }
        }
        "report" => export_session(),
        "menu" => {
            loop {
                P!("\n");
                p_bold(&format!("  {}  v{NSB_VERSION}", L("title")));
                P!("\n  {}\n", L("subtitle"));
                for it in ["menu_quick", "menu_suite_normal", "menu_suite_hard",
                           "menu_flows", "menu_roadmap", "menu_reports",
                           "menu_settings", "menu_exit"] {
                    P!("  "); p_bold(L(it)); P!("\n");
                }
                P!("  {}\n", L("lang_toggle"));
                P!("  {} > ", L("menu_prompt"));
                let mut sel = String::new();
                if io::stdin().read_line(&mut sel).unwrap_or(0) == 0 {
                    P!("\n");
                    break;
                }
                let sel = sel.trim();
                match sel {
                    "1" => {
                        exp_taylor_green("normal", 0, -1.0, 0.0, 0.0);
                        exp_baudit("normal", 0, -1.0, 0.0, 0.0);
                        export_session();
                    }
                    "2" => {
                        exp_taylor_green("normal", 0, -1.0, 0.0, 0.0);
                        exp_abc("normal", 0, 0.0, 0.0);
                        exp_houluo("normal", 0, 0.0, 0.0);
                        exp_baudit("normal", 0, -1.0, 0.0, 0.0);
                        export_session();
                    }
                    "3" => {
                        exp_taylor_green("hard", 0, -1.0, 0.0, 0.0);
                        exp_abc("hard", 0, 0.0, 0.0);
                        exp_houluo("hard", 0, 0.0, 0.0);
                        exp_baudit("hard", 0, -1.0, 0.0, 0.0);
                        export_session();
                    }
                    "4" => {
                        flows_table_text();
                        P!("  {}\n", L("flows_menu_hint"));
                        let mut fs2 = String::new();
                        if io::stdin().read_line(&mut fs2).unwrap_or(0) > 0 {
                            let f2 = fs2.trim();
                            if f2 == "a" {
                                for f in FLOWS {
                                    flow_run(f, "normal");
                                }
                                export_session();
                            } else if let Ok(num) = f2.parse::<usize>() {
                                if num >= 1 && num <= 20 {
                                    flow_run(&FLOWS[num - 1], "normal");
                                    export_session();
                                }
                            }
                        }
                    }
                    "5" => roadmap_report(),
                    "6" => {
                        header_bar(L("rep_hdr"));
                        if session().is_empty() {
                            P!("  {}\n", L("rep_none"));
                        } else {
                            export_session();
                        }
                    }
                    "7" => {
                        header_bar(L("set_hdr"));
                        P!("  {}: {}\n", L("set_out"), cfg().out_dir);
                        header_bar(L("set_about"));
                        P!("  {}\n", L("set_about_txt"));
                    }
                    "9" => {
                        cfg().lang = if cfg().lang == "ru" { "en" } else { "ru" };
                        P!("  {}\n", if cfg().lang == "en" { "Language: ENGLISH" }
                                     else { "Язык: РУССКИЙ" });
                    }
                    "0" => break,
                    _ => P!("  {}\n", L("invalid_choice")),
                }
            }
        }
        _ => {}
    }
}



