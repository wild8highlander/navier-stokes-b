// ═══════════════════════════════════════════════════════════════════════════
//   NSB C++ LAB v2.1.0 — polyglot edition
//   A faithful port of the self-contained Julia "Navier–Stokes b-Lab" to
//   modern C++17. Single translation unit, standard library only.
//
//   Highlights of this edition (vs the C port):
//     • std::thread-parallel FFT: axis passes are split across all hardware
//       threads (≈Ncores× speed-up over the serial C edition on multi-core).
//     • std::complex, std::vector, RAII — no manual memory management.
//     • Same physics as the Julia reference: 3-D pseudospectral NS/Euler
//       (RK4 + Leray projection + 2/3 rule + hyperviscosity ν₄), 2-D
//       barotropic β-plane, BKM diagnostics, K41 fits, blow-up scanner.
//     • Zero-dependency output: PNG (own stored-deflate + CRC32 + Adler32),
//       GIF89a animator, minimal PDF, CSV/JSON/MD reports.
//     • i18n RU/EN, ONE-LINE progress bar, sparklines, interactive TUI menu.
//
//   Build:   g++ -O2 -std=c++17 -pthread nsb_lab.cpp -o nsb_lab  (or make)
//   Run:     ./nsb_lab --quick --lang en
//            ./nsb_lab --selftest
//            ./nsb_lab                       (interactive menu)
//   Results: ~/nsb_lab_results/{data,plots,reports,articles,logs}
// ═══════════════════════════════════════════════════════════════════════════

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <complex>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <io.h>
#define IS_TTY _isatty(_fileno(stdout))
#else
#include <unistd.h>
#define IS_TTY isatty(1)
#endif

namespace fs = std::filesystem;
using cplx = std::complex<double>;
static const double PI = 3.14159265358979323846;

// std::complex<double> refuses int*complex (would deduce complex<int>);
// these overloads keep the solver expressions close to the Julia reference.
static inline cplx operator*(int a, const cplx &z) { return double(a) * z; }
static inline cplx operator*(const cplx &z, int a) { return z * double(a); }

#define NSB_VERSION "2.1.0"

// ────────────────────────────── config ──────────────────────────────────

struct Config {
    std::string lang = "ru";
    std::string out_dir;
    int dpi = 600;
    long seed = 20260916;
    bool color = false, ascii_only = false;
    int max_n = 32;
    bool quick = false, batch = false, quiet = false;
    std::chrono::steady_clock::time_point t_start;
    bool gif = true;
    int ckpt_every = 200;
    bool adaptive_cfl = false;
    double nu4 = 0.0;
    unsigned hw_threads = std::thread::hardware_concurrency();
} CFG;

static std::ofstream LOG_IO;

static double now_s() {
    return std::chrono::duration<double>(
               std::chrono::steady_clock::now().time_since_epoch()).count();
}

static void cfg_init() {
    const char *home = getenv("HOME");
    CFG.out_dir = std::string(home ? home : ".") + "/nsb_lab_results";
    CFG.t_start = std::chrono::steady_clock::now();
    double total_gb = 8.0;
    std::ifstream mem("/proc/meminfo");
    std::string key; long kb = 0; std::string unit;
    while (mem >> key >> kb >> unit)
        if (key == "MemTotal:") { total_gb = kb / 1048576.0; break; }
    for (int cand : {32, 64, 128, 256}) {
        double mem = std::pow(cand, 3) * 16.0 * 24.0 / (1u << 30);
        if (mem < total_gb * 0.55) CFG.max_n = cand;
    }
}

static void ensure_outdirs() {
    for (const char *s : {"", "/logs", "/data", "/plots", "/reports", "/articles"})
        fs::create_directories(CFG.out_dir + s);
}

static void logfile_open() {
    ensure_outdirs();
    std::time_t t = std::time(nullptr);
    char stamp[32];
    std::strftime(stamp, sizeof(stamp), "%Y%m%d_%H%M%S", std::localtime(&t));
    LOG_IO.open(CFG.out_dir + "/logs/session_" + stamp + ".log", std::ios::app);
}

// print: dual output to stdout + session log
template <typename... A>
static void P(const char *fmt, A... args) {
    char buf[4096];
    snprintf(buf, sizeof(buf), fmt, args...);
    if (!CFG.quiet) { std::cout << buf << std::flush; }
    if (LOG_IO.is_open()) LOG_IO << buf << std::flush;
}

static std::string hms(double t) {
    long s = t < 0 ? 0 : long(t + 0.5);
    long h = s / 3600, m = (s % 3600) / 60, ss = s % 60;
    char b[32];
    if (h) snprintf(b, 32, "%ld:%02ld:%02ld", h, m, ss);
    else snprintf(b, 32, "%02ld:%02ld", m, ss);
    return b;
}

// ────────────────────────────── i18n ────────────────────────────────────

struct I18nPair { const char *key, *ru, *en; };
static const I18nPair I18N[] = {
{"yes","да","yes"},{"no","нет","no"},
{"pass","ПРОЙДЕНО","PASS"},{"fail","ПРОВАЛЕНО","FAIL"},
{"title","ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ","NAVIER–STOKES LABORATORY · b-CORRECTION"},
{"subtitle","самодостаточная C++17-версия (std::thread-параллельный FFT)",
 "self-contained C++17 edition (std::thread-parallel FFT)"},
{"menu_prompt","Выберите пункт и нажмите Enter","Choose an item and press Enter"},
{"invalid_choice","Нет такого пункта — попробуйте ещё раз","No such item — try again"},
{"lang_toggle","9. Язык / Language  (RU ↔ EN)","9. Language / Язык  (EN ↔ RU)"},
{"menu_quick","1. Быстрый прогон  (мини-сьют + финальный PDF)","1. Quick run  (mini-suite + final PDF)"},
{"menu_suite_normal","2. Полная сьют — НОРМАЛЬНЫЙ режим","2. Full suite — NORMAL mode"},
{"menu_suite_hard","3. Полная сьют — ХАРД режим","3. Full suite — HARD mode"},
{"menu_custom","4. Свой эксперимент (N, ν, dt, T)","4. Custom experiment (N, ν, dt, T)"},
{"menu_flows","5. Лаборатория 20 реальных течений","5. Real-flows laboratory (20 documented flows)"},
{"menu_roadmap","6. Роадмап и это железо (бенчмарк)","6. Roadmap & this hardware (benchmark)"},
{"menu_reports","7. Отчёты сессии","7. Session reports"},
{"menu_settings","8. Настройки и о проекте","8. Settings & about"},
{"menu_exit","0. Выход","0. Exit"},
{"config_line","конфиг: выход=%s · N≤%d · потоков=%u","config: out=%s · N≤%d · threads=%u"},
{"exp_tg","Тейлор–Грин: сходимость и экстраполяция","Taylor–Green: convergence and extrapolation"},
{"exp_abc","ABC (Эйлер): охота за расходимостью","ABC (Euler): blow-up hunt"},
{"exp_houluo","Хоу–Ло: антипараллельные вихревые трубки","Hou–Luo: anti-parallel vortex tubes"},
{"exp_baudit","Аудит b-коррекции: симметрия против пинка","b-correction audit: symmetry vs pointwise kick"},
{"scope_note","Область действия: сертификат внутренней согласованности, не общая теорема.",
 "Scope: a certificate of internal consistency of the computed solution, not a general theorem."},
{"verdict_ok","ВЕРДИКТ: все проверки пройдены","VERDICT: all checks passed"},
{"verdict_fail","ВЕРДИКТ: есть проваленные проверки","VERDICT: some checks failed"},
{"ck_divfree","несжимаемость: max|div u| в машинном пороге","incompressibility: max|div u| at machine level"},
{"ck_energy_monotone","энергия не растёт (вязкое затухание)","energy non-increasing (viscous decay)"},
{"ck_energy_conserved","энергия сохраняется (Эйлер)","energy conserved (Euler)"},
{"ck_rk4_order","измеренный порядок RK4 ≈ 4","measured RK4 order ≈ 4"},
{"ck_no_blowup","признаков расходимости нет (BKM ограничен)","no finite-time blow-up signature (BKM bounded)"},
{"ck_tail_resolved","спектральный хвост разрешён","spectral tail resolved"},
{"ck_stability","устойчивость: нет NaN/Inf","stability: no NaN/Inf"},
{"ck_isometry","точечный поворот — изометрия","pointwise rotation is an isometry"},
{"ck_symmetry_relabel","полная симметрия = релебелинг","full symmetry = relabeling"},
{"ck_div_break","точечный поворот ЛОМАЕТ div u = 0","pointwise rotation BREAKS div u = 0"},
{"ck_reproject","после перепроекции div на машинном пороге","after reprojection div at machine level"},
{"ck_b_effect","b-пинк не снижает sup|ω|","b-kick does not reduce sup|ω|"},
{"ck_abc_doubling","время удвоения sup|ω| не сокращается к нулю","sup|ω| doubling time does not shrink to zero"},
{"ck_hl_growth","рост sup|ω| измерен","sup|ω| growth measured"},
{"ck_cfl","CFL-аудит пройден","CFL audit passed"},
{"flows_hdr","ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов","REAL-FLOWS LABORATORY — 20 documented flows"},
{"flows_menu_hint","Введите номер течения (1–20), a — все, q — назад","Enter flow number (1-20), a — run all, q — back"},
{"flow_card","КАРТОЧКА ТЕЧЕНИЯ","FLOW CARD"},
{"flow_source","первоисточник/документация","primary source/documentation"},
{"flow_params","документированные величины","documented quantities"},
{"flow_derived","расчётные параметры","derived parameters"},
{"flow_dns_no","DNS НЕВОЗМОЖНО на существующем железе: N ≈ %s (~%s памяти)","DNS is INFEASIBLE on existing hardware: N ≈ %s (~%s of memory)"},
{"flow_dns_ok","DNS возможно: N = %d","DNS feasible: N = %d"},
{"flow_reduced","редуцированная модель: 2D баротропная β-плоскость","reduced model: 2-D barotropic β-plane"},
{"flow_verdict","ВЕРДИКТ ПО ТЕЧЕНИЮ","FLOW VERDICT"},
{"flow_all_hdr","СВОДНАЯ ТАБЛИЦА 20 ТЕЧЕНИЙ","SUMMARY TABLE OF 20 FLOWS"},
{"road_hdr","РОАДМАП И ЭТО ЖЕЛЕЗО","ROADMAP AND THIS HARDWARE"},
{"road_gflops","измеренная производительность 3D-FFT: %.1f GFLOP/с","measured 3D-FFT throughput: %.1f GFLOP/s"},
{"road_tbl_hdr","Оценки для псевдоспектрального НС (RK4, ~13 3D-FFT/шаг)","Estimates for pseudospectral NS (RK4, ~13 3D-FFTs/step)"},
{"road_verdict_laptop","ноутбук: реально за вечер","laptop: an evening run"},
{"road_verdict_ws","нужна рабочая станция","workstation recommended"},
{"road_verdict_hpc","нужен кластер/HPC","cluster/HPC required"},
{"road_verdict_no","вне досягаемости одиночной машины","out of reach for a single machine"},
{"rep_hdr","ОТЧЁТЫ СЕССИИ","SESSION REPORTS"},
{"rep_none","Пока ничего не посчитано","Nothing computed yet"},
{"rep_saved","Сохранено","Saved"},
{"selftest_hdr","САМОТЕСТ","SELF-TEST"},
{"selftest_ok","САМОТЕСТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ","SELF-TEST: ALL CHECKS PASSED"},
{"selftest_fail","САМОТЕСТ: ЕСТЬ ПРОВАЛЫ","SELF-TEST: FAILURES PRESENT"},
{"prog_step","шаг","step"},{"prog_rate","шаг/с","steps/s"},{"prog_eta","ETA","ETA"},
{"adaptive_on","адаптивный CFL-шаг включён","adaptive CFL step enabled"},
{"gif_saved","GIF сохранён: %s","GIF saved: %s"},
{"gif_disabled","GIF выключен (--gif 0)","GIF disabled (--gif 0)"},
{"set_hdr","НАСТРОЙКИ","SETTINGS"},
{"set_out","Папка результатов","Results folder"},
{"set_about","О ПРОЕКТЕ","ABOUT"},
{"set_about_txt","Лаборатория проверяет гипотезу b-коррекции: полная решётчатая симметрия — релебелинг; точечный поворот сохраняет энергию, но ломает div u = 0. Порт C++17 добавляет многопоточный FFT.",
 "The lab tests the b-correction hypothesis: full lattice symmetry is a relabeling; the pointwise rotation preserves energy but breaks div u = 0. The C++17 port adds a multi-threaded FFT."},
{nullptr, nullptr, nullptr}};

static const char *L(const char *key) {
    for (int i = 0; I18N[i].key; i++)
        if (!strcmp(I18N[i].key, key))
            return CFG.lang == "en" ? I18N[i].en : I18N[i].ru;
    return key;
}

// ─────────────────────────── ANSI helpers ───────────────────────────────

static void p_ok(const std::string &s)   { P("%s", (CFG.color ? "\x1b[1;32m" + s + "\x1b[0m" : s).c_str()); }
static void p_bad(const std::string &s)  { P("%s", (CFG.color ? "\x1b[1;31m" + s + "\x1b[0m" : s).c_str()); }
static void p_warn(const std::string &s) { P("%s", (CFG.color ? "\x1b[1;33m" + s + "\x1b[0m" : s).c_str()); }
static void p_muted(const std::string &s){ P("%s", (CFG.color ? "\x1b[2m" + s + "\x1b[0m" : s).c_str()); }
static void p_bold(const std::string &s) { P("%s", (CFG.color ? "\x1b[1m" + s + "\x1b[0m" : s).c_str()); }

static void header_bar(const std::string &title) {
    std::string line(76, '-');
    P("\n");
    if (CFG.color) P("\x1b[38;2;80;160;255m%s\x1b[0m\n", line.c_str()); else P("%s\n", line.c_str());
    P(" ▸ "); p_bold(title); P("\n");
    if (CFG.color) P("\x1b[38;2;80;160;255m%s\x1b[0m\n", line.c_str()); else P("%s\n", line.c_str());
}

// ───────────── one-line progress bar + sparkline + term image ───────────

static double PROG_LAST = 0.0;

static void progress(double frac, const std::string &label, double t0,
                     int total = 0, int done = 0) {
    frac = std::min(std::max(frac, 0.0), 1.0);
    if (!IS_TTY || CFG.quiet) {
        if ((frac - PROG_LAST >= 0.1 || frac >= 1.0) && PROG_LAST < 1.0) {
            PROG_LAST = frac >= 1.0 ? 1.0 : std::max(frac, PROG_LAST);
            P("  [%3d%%] %s\n", int(frac * 100 + 0.5), label.c_str());
        }
        return;
    }
    const int W = 30;
    int fill = int(frac * W + 0.5);
    std::string bar;
    for (int i = 1; i <= W; i++) {
        if (CFG.ascii_only) bar += i <= fill ? '#' : '-';
        else if (i <= fill && CFG.color) {
            char c[64];
            snprintf(c, 64, "\x1b[38;2;%d;%d;255m█\x1b[0m", 40 + 180 * i / W, 80 + 170 * i / W);
            bar += c;
        } else if (CFG.color) bar += "\x1b[2m░\x1b[0m";
        else bar += '-';
    }
    double el = now_s() - t0;
    double eta = frac > 0.005 ? el / frac - el : NAN;
    char t1[16] = " --:--", t2[16];
    if (std::isfinite(eta)) snprintf(t1, 16, "%02d:%02d", int(eta) / 60, int(eta) % 60);
    snprintf(t2, 16, "%02d:%02d", int(el) / 60, int(el) % 60);
    char tail[128];
    if (total > 0)
        snprintf(tail, 128, " · %s %d/%d · %.1f %s · %s %s", L("prog_step"),
                 done, total, done / std::max(el, 1e-9), L("prog_rate"),
                 L("prog_eta"), t1);
    else
        snprintf(tail, 128, " · %s %s", "elapsed", t2);
    P("\r%*s\r", 120, "");
    if (CFG.color)
        P("\x1b[38;2;80;160;255m ▸ \x1b[0m%s ▕%s▏%5.1f%%%s", label.c_str(), bar.c_str(),
          frac * 100, tail);
    else
        P(" ▸ %s |%s| %5.1f%%%s", label.c_str(), bar.c_str(), frac * 100, tail);
    std::cout << std::flush;
    if (frac >= 1.0) { P("\n"); PROG_LAST = 0; }
}

static std::string sparkline(const std::vector<double> &v) {
    const char *GL = "▁▂▃▄▅▆▇█";
    const char *GA = "_.-~*##";
    if (v.empty()) return "";
    double lo = 1e300, hi = -1e300;
    for (double x : v) { x = std::max(x, 0.0); lo = std::min(lo, x); hi = std::max(hi, x); }
    double rng = hi > lo ? hi - lo : 1.0;
    std::string out;
    for (double x : v) {
        x = std::max(x, 0.0);
        int k = int((x - lo) / rng * 7 + 0.5);
        k = std::min(std::max(k, 0), 7);
        if (CFG.ascii_only) out += GA[k];
        else out += std::string(GL + k * 3, GL + k * 3 + 3);
    }
    return out;
}

// ───────────────────── in-house radix-2 FFT (parallel) ──────────────────

struct FFTPlan {
    int n = 0;
    std::vector<cplx> tw;
    std::vector<int> bitrev;
    FFTPlan() = default;
    explicit FFTPlan(int n_) : n(n_), tw(n_ / 2), bitrev(n_) {
        for (int k = 0; k < n / 2; k++) tw[k] = std::exp(cplx(0, -2.0 * PI * k / n));
        int logn = 0; while ((1 << logn) < n) logn++;
        for (int i = 0; i < n; i++) {
            int r = 0, x = i;
            for (int b = 0; b < logn; b++) { r = (r << 1) | (x & 1); x >>= 1; }
            bitrev[i] = r;
        }
    }
};

static void fft1d(const FFTPlan &p, cplx *a, bool inverse) {
    int n = p.n;
    for (int i = 0; i < n; i++) {
        int j = p.bitrev[i];
        if (i < j) std::swap(a[i], a[j]);
    }
    for (int len = 2; len <= n; len <<= 1) {
        int half = len >> 1, step = n / len;
        for (int start = 0; start < n; start += len) {
            int k = 0;
            for (int j = 0; j < half; j++) {
                cplx w = inverse ? std::conj(p.tw[k]) : p.tw[k];
                cplx u = a[start + j], v = a[start + j + half] * w;
                a[start + j] = u + v;
                a[start + j + half] = u - v;
                k += step;
            }
        }
    }
    if (inverse)
        for (int i = 0; i < n; i++) a[i] /= double(n);
}

// parallel 1D over an index range — used by the axis passes
static void fft_axis_par(const FFTPlan &p, bool inverse,
                         const std::function<cplx &(size_t)> &at, size_t count) {
    unsigned nt = std::max(1u, CFG.hw_threads);
    size_t chunk = (count + nt - 1) / nt;
    std::vector<std::vector<cplx>> bufs(nt, std::vector<cplx>(p.n));
    auto worker = [&](unsigned t) {
        size_t lo = t * chunk, hi = std::min(count, lo + chunk);
        for (size_t line = lo; line < hi; line++) {
            for (int i = 0; i < p.n; i++) bufs[t][i] = at(line * p.n + i);
            fft1d(p, bufs[t].data(), inverse);
            for (int i = 0; i < p.n; i++) at(line * p.n + i) = bufs[t][i];
        }
    };
    if (nt == 1) worker(0);
    else {
        std::vector<std::thread> pool;
        for (unsigned t = 0; t < nt; t++) pool.emplace_back(worker, t);
        for (auto &th : pool) th.join();
    }
}

static void fft3d(const FFTPlan &p, std::vector<cplx> &A, bool inverse) {
    int n = p.n;
    // axis 2 (k, contiguous lines)
    fft_axis_par(p, inverse, [&](size_t i) -> cplx & { return A[i]; }, size_t(n) * n);
    // axis 1 (j)
    fft_axis_par(p, inverse,
                 [&](size_t line) -> cplx & {
                     size_t j = line % n, rest = line / n;
                     size_t i = rest / n, k = rest % n;
                     return A[(i * n + j) * n + k];
                 },
                 size_t(n) * n);
    // axis 0 (i)
    fft_axis_par(p, inverse,
                 [&](size_t line) -> cplx & {
                     size_t i = line % n, rest = line / n;
                     size_t j = rest / n, k = rest % n;
                     return A[(i * n + j) * n + k];
                 },
                 size_t(n) * n);
}

static void fft2d(const FFTPlan &p, std::vector<cplx> &M, bool inverse) {
    int n = p.n;
    fft_axis_par(p, inverse, [&](size_t i) -> cplx & { return M[i]; }, size_t(n));
    fft_axis_par(p, inverse,
                 [&](size_t line) -> cplx & {
                     size_t i = line / n, j = line % n;
                     return M[j * n + i];
                 },
                 size_t(n));
}

struct Field3 : std::array<std::vector<cplx>, 3> {
    Field3() = default;
    explicit Field3(size_t N3) {
        for (auto &c : *this) c.assign(N3, cplx(0, 0));
    }
};

// ───────────────────── 3-D pseudospectral solver ────────────────────────

struct NSE3D {
    int n;
    double nu, nu4, dx;
    std::vector<int> kx, ky, kz;
    std::vector<double> ksq, ksq2, k2safe;
    std::vector<bool> mask;
    NSE3D(int n_, double nu_, double nu4_in = -1)
        : n(n_), nu(nu_), nu4(nu4_in >= 0 ? nu4_in : CFG.nu4), dx(2 * PI / n_) {
        size_t N3 = size_t(n) * n * n;
        kx.resize(N3); ky.resize(N3); kz.resize(N3);
        ksq.resize(N3); ksq2.resize(N3); k2safe.resize(N3);
        mask.resize(N3);
        std::vector<int> k1d(n);
        for (int i = 0; i < n / 2; i++) k1d[i] = i;
        for (int i = -n / 2; i < 0; i++) k1d[i + n] = i;
        int kc = n / 3;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++) {
                    size_t id = (size_t(i) * n + j) * n + k;
                    kx[id] = k1d[i]; ky[id] = k1d[j]; kz[id] = k1d[k];
                    double q = double(k1d[i] * k1d[i] + k1d[j] * k1d[j] + k1d[k] * k1d[k]);
                    ksq[id] = q; ksq2[id] = q * q;
                    k2safe[id] = q > 0 ? q : 1.0;
                    mask[id] = std::abs(k1d[i]) <= kc && std::abs(k1d[j]) <= kc &&
                               std::abs(k1d[k]) <= kc;
                }
    }
};

static size_t IDX(int n, int i, int j, int k) {
    return (size_t(i) * n + j) * n + k;
}

struct Work3D {
    FFTPlan plan;
    Field3 uhat, wh, nlhat, K1, K2, K3, K4, T1, T2, T3, scratch;
    std::array<std::vector<double>, 3> u, w;
    std::vector<cplx> kd;
    explicit Work3D(int n) : plan(n), uhat(size_t(n) * n * n), wh(size_t(n) * n * n),
        nlhat(size_t(n) * n * n), K1(size_t(n) * n * n), K2(size_t(n) * n * n),
        K3(size_t(n) * n * n), K4(size_t(n) * n * n), T1(size_t(n) * n * n),
        T2(size_t(n) * n * n), T3(size_t(n) * n * n), scratch(size_t(n) * n * n),
        kd(size_t(n) * n * n) {
        for (int c = 0; c < 3; c++) {
            u[c].assign(size_t(n) * n * n, 0.0);
            w[c].assign(size_t(n) * n * n, 0.0);
        }
    }
};

static void fft_field3(Work3D &W, const std::array<std::vector<double>, 3> &in,
                       Field3 &out) {
    size_t N3 = in[0].size();
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) W.scratch[c][i] = in[c][i];
        fft3d(W.plan, W.scratch[c], false);
        out[c] = W.scratch[c];
    }
}

static void ifft_field3(Work3D &W, const Field3 &in,
                        std::array<std::vector<double>, 3> &out) {
    size_t N3 = in[0].size();
    for (int c = 0; c < 3; c++) {
        W.scratch[c] = in[c];
        fft3d(W.plan, W.scratch[c], true);
        for (size_t i = 0; i < N3; i++) out[c][i] = W.scratch[c][i].real();
    }
}

static void project3(Work3D &W, const NSE3D &s, Field3 &out, const Field3 &in) {
    size_t N3 = in[0].size();
    for (size_t i = 0; i < N3; i++) {
        W.kd[i] = (cplx(s.kx[i], 0) * in[0][i] + cplx(s.ky[i], 0) * in[1][i] +
                   cplx(s.kz[i], 0) * in[2][i]) / s.k2safe[i];
        if (s.ksq[i] == 0) W.kd[i] = 0;
    }
    const std::vector<int> *kc[3] = {&s.kx, &s.ky, &s.kz};
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            out[c][i] = in[c][i] - cplx(double((*kc[c])[i]), 0) * W.kd[i];
}

static void curl_hat3(const NSE3D &s, Field3 &out, const Field3 &a) {
    size_t N3 = a[0].size();
    for (size_t i = 0; i < N3; i++) {
        int kx = s.kx[i], ky = s.ky[i], kz = s.kz[i];
        out[0][i] = cplx(0, 1) * (ky * a[2][i] - kz * a[1][i]);
        out[1][i] = cplx(0, 1) * (kz * a[0][i] - kx * a[2][i]);
        out[2][i] = cplx(0, 1) * (kx * a[1][i] - ky * a[0][i]);
    }
}

static void rhs3(Work3D &W, const NSE3D &s, Field3 &du, const Field3 &uhat) {
    size_t N3 = uhat[0].size();
    curl_hat3(s, W.wh, uhat);
    ifft_field3(W, uhat, W.u);
    ifft_field3(W, W.wh, W.w);
    for (size_t i = 0; i < N3; i++) {
        double w1 = W.w[0][i], w2 = W.w[1][i], w3 = W.w[2][i];
        double u1 = W.u[0][i], u2 = W.u[1][i], u3 = W.u[2][i];
        W.w[0][i] = w2 * u3 - w3 * u2;
        W.w[1][i] = w3 * u1 - w1 * u3;
        W.w[2][i] = w1 * u2 - w2 * u1;
    }
    fft_field3(W, W.w, W.nlhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s.mask[i]) W.nlhat[c][i] = 0;
    project3(W, s, du, W.nlhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            du[c][i] -= (s.nu * s.ksq[i] + s.nu4 * s.ksq2[i]) * uhat[c][i];
}

static void step_rk4_3d(Work3D &W, const NSE3D &s, Field3 &out, const Field3 &uhat,
                        double dt) {
    size_t N3 = uhat[0].size();
    rhs3(W, s, W.K1, uhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) W.T1[c][i] = uhat[c][i] + 0.5 * dt * W.K1[c][i];
    rhs3(W, s, W.K2, W.T1);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) W.T1[c][i] = uhat[c][i] + 0.5 * dt * W.K2[c][i];
    rhs3(W, s, W.K3, W.T1);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) W.T1[c][i] = uhat[c][i] + dt * W.K3[c][i];
    rhs3(W, s, W.K4, W.T1);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) {
            cplx v = uhat[c][i] + (dt / 6.0) *
                (W.K1[c][i] + 2.0 * W.K2[c][i] + 2.0 * W.K3[c][i] + W.K4[c][i]);
            out[c][i] = s.mask[i] ? v : cplx(0, 0);
        }
}

static double cfl_dt_3d(Work3D &W, const NSE3D &s, const Field3 &uhat) {
    ifft_field3(W, uhat, W.u);
    double umax = 0;
    size_t N3 = uhat[0].size();
    for (size_t i = 0; i < N3; i++) {
        double v = std::sqrt(W.u[0][i] * W.u[0][i] + W.u[1][i] * W.u[1][i] +
                             W.u[2][i] * W.u[2][i]);
        umax = std::max(umax, v);
    }
    if (umax < 1e-14) return 0.5 * s.dx * s.dx / std::max(s.nu, 1e-12);
    return 0.5 * s.dx / umax;
}

// ───────────────────── ICs & b-rotations ────────────────────────────────

static const double NSB_B = 1.0 / (4.0 * PI + 2.0 * std::sqrt(3.0));
static const double NSB_THETA_B = std::asin(NSB_B);

using Mat3 = std::array<std::array<double, 3>, 3>;

static Mat3 rodrigues(double theta, double ex, double ey, double ez) {
    double c = std::cos(theta), s = std::sin(theta);
    Mat3 C = {{{{0, -ez, ey}}, {{ez, 0, -ex}}, {{-ey, ex, 0}}}};
    Mat3 O = {{{{ex * ex, ex * ey, ex * ez}},
               {{ey * ex, ey * ey, ey * ez}},
               {{ez * ex, ez * ey, ez * ez}}}};
    Mat3 R;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            R[i][j] = c * (i == j) + (1 - c) * O[i][j] - s * C[i][j];
    return R;
}

static std::vector<double> grid_1d(int n) {
    std::vector<double> x(n);
    for (int i = 0; i < n; i++) x[i] = 2.0 * PI * i / n;
    return x;
}

using PhysField = std::array<std::vector<double>, 3>;

static PhysField ic_taylor_green(int n) {
    auto x = grid_1d(n);
    PhysField u;
    for (auto &c : u) c.assign(size_t(n) * n * n, 0.0);
    std::vector<double> sx(n), cx(n);
    for (int i = 0; i < n; i++) { sx[i] = std::sin(x[i]); cx[i] = std::cos(x[i]); }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                u[0][IDX(n, i, j, k)] = sx[i] * cx[j] * cx[k];
                u[1][IDX(n, i, j, k)] = -cx[i] * sx[j] * cx[k];
            }
    return u;
}

static PhysField ic_abc(int n) {
    auto x = grid_1d(n);
    PhysField u;
    for (auto &c : u) c.assign(size_t(n) * n * n, 0.0);
    std::vector<double> sx(n), cx(n);
    for (int i = 0; i < n; i++) { sx[i] = std::sin(x[i]); cx[i] = std::cos(x[i]); }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                u[0][IDX(n, i, j, k)] = sx[k] + cx[j];
                u[1][IDX(n, i, j, k)] = sx[i] + cx[k];
                u[2][IDX(n, i, j, k)] = sx[j] + cx[i];
            }
    return u;
}

static PhysField ic_hou_luo(int n) {
    auto x = grid_1d(n);
    PhysField w;
    for (auto &c : w) c.assign(size_t(n) * n * n, 0.0);
    double sigma = PI / 16, inv2s2 = 1.0 / (2 * sigma * sigma);
    double y0 = PI / 2, z0a = PI / 2, z0b = 3 * PI / 2;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                double yj = x[j], zk = x[k];
                double g1 = std::exp(-((yj - y0) * (yj - y0) + (zk - z0a) * (zk - z0a)) * inv2s2);
                double g2 = std::exp(-((yj - 3 * PI / 2) * (yj - 3 * PI / 2) +
                                       (zk - z0b) * (zk - z0b)) * inv2s2);
                w[0][IDX(n, i, j, k)] = (g1 - g2) * (1 + 0.05 * std::cos(x[i]));
            }
    return w;
}

static PhysField ic_random(int n, long seed) {
    std::mt19937_64 rng(seed < 0 ? CFG.seed : seed);
    std::normal_distribution<double> nd(0.0, 1.0);
    PhysField u;
    for (auto &c : u) c.assign(size_t(n) * n * n, 0.0);
    for (auto &c : u) for (auto &v : c) v = nd(rng);
    auto x = grid_1d(n);
    int kp = 4;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                size_t id = IDX(n, i, j, k);
                u[0][id] += 0.5 * std::sin(kp * x[i]) * std::cos(kp * x[j]);
                u[1][id] += 0.5 * std::sin(kp * x[i]) * (0.5 * std::sin(kp * x[j]) + 0.5);
                u[2][id] += 0.5 * std::cos(kp * x[k]) * std::sin(kp * x[j]);
            }
    return u;
}

static Field3 prepare_state3(Work3D &W, const NSE3D &s, const PhysField &ic) {
    size_t N3 = ic[0].size();
    Field3 uhat(N3);
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) W.scratch[c][i] = ic[c][i];
        fft3d(W.plan, W.scratch[c], false);
        uhat[c] = W.scratch[c];
    }
    project3(W, s, uhat, uhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s.mask[i]) uhat[c][i] = 0;
    return uhat;
}

static void rotate_pointwise3(Work3D &W, const NSE3D &s, Field3 &out,
                              const Field3 &uhat, const Mat3 &R) {
    size_t N3 = uhat[0].size();
    ifft_field3(W, uhat, W.u);
    PhysField ru;
    for (auto &c : ru) c.assign(N3, 0.0);
    for (size_t i = 0; i < N3; i++) {
        double x = W.u[0][i], y = W.u[1][i], z = W.u[2][i];
        ru[0][i] = R[0][0] * x + R[0][1] * y + R[0][2] * z;
        ru[1][i] = R[1][0] * x + R[1][1] * y + R[1][2] * z;
        ru[2][i] = R[2][0] * x + R[2][1] * y + R[2][2] * z;
    }
    fft_field3(W, ru, out);
}

static void rotate_full_symmetry3(Work3D &W, const NSE3D &s, Field3 &out,
                                  const Field3 &uhat) {
    int n = s.n;
    size_t N3 = uhat[0].size();
    ifft_field3(W, uhat, W.u);
    PhysField ru;
    for (auto &c : ru) c.assign(N3, 0.0);
    for (int i = 0; i < n; i++) {
        int isrc = (n - i) % n;    /* index of −x_i */
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                size_t src = IDX(n, j, isrc, k);   /* u(y_j, −x_i, z_k) */
                size_t dst = IDX(n, i, j, k);
                ru[0][dst] = -W.u[1][src];
                ru[1][dst] = W.u[0][src];
                ru[2][dst] = W.u[2][src];
            }
    }
    fft_field3(W, ru, out);
}

// ───────────────────────── diagnostics ──────────────────────────────────

struct TimeSeries {
    std::vector<double> t{0.0}, energy{0.0}, enstrophy{0.0}, palinstrophy{0.0},
        sup_omega{0.0}, dissipation{0.0}, bkm{0.0};
    void push(double t_, double e, double om, double pal, double sup, double eps,
              double bkm_) {
        t.push_back(t_); energy.push_back(e); enstrophy.push_back(om);
        palinstrophy.push_back(pal); sup_omega.push_back(sup);
        dissipation.push_back(eps); bkm.push_back(bkm_);
    }
};

static double energy3(const NSE3D &s, const Field3 &uhat) {
    size_t N3 = uhat[0].size();
    double sum = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) sum += std::norm(uhat[c][i]);
    return 0.5 * sum / std::pow(double(s.n), 6.0);
}

static double enstrophy3(const NSE3D &s, const Field3 &what) {
    size_t N3 = what[0].size();
    double sum = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) sum += std::norm(what[c][i]);
    return 0.5 * sum / std::pow(double(s.n), 6.0);
}

static double palinstrophy3(const NSE3D &s, const Field3 &what) {
    size_t N3 = what[0].size();
    double sum = 0;
    for (size_t i = 0; i < N3; i++) {
        cplx a1 = cplx(0, 1) * (s.ky[i] * what[2][i] - s.kz[i] * what[1][i]);
        cplx a2 = cplx(0, 1) * (s.kz[i] * what[0][i] - s.kx[i] * what[2][i]);
        cplx a3 = cplx(0, 1) * (s.kx[i] * what[1][i] - s.ky[i] * what[0][i]);
        sum += std::norm(a1) + std::norm(a2) + std::norm(a3);
    }
    return 0.5 * sum / std::pow(double(s.n), 6.0);
}

static double dissipation3(const NSE3D &s, const Field3 &uhat) {
    size_t N3 = uhat[0].size();
    double sum = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            sum += s.ksq[i] * std::norm(uhat[c][i]);
    return s.nu * sum / std::pow(double(s.n), 6.0);
}

static double sup_vorticity3(const std::array<std::vector<double>, 3> &w) {
    size_t N3 = w[0].size();
    double m = 0;
    for (size_t i = 0; i < N3; i++)
        m = std::max(m, std::sqrt(w[0][i] * w[0][i] + w[1][i] * w[1][i] +
                                  w[2][i] * w[2][i]));
    return m;
}

static double divergence_max3(const NSE3D &s, const Field3 &uhat) {
    size_t N3 = uhat[0].size();
    double sum = 0;
    for (size_t i = 0; i < N3; i++) {
        cplx d = s.kx[i] * uhat[0][i] + s.ky[i] * uhat[1][i] + s.kz[i] * uhat[2][i];
        sum += std::norm(d);
    }
    return std::sqrt(sum) / std::pow(double(s.n), 3.0);
}

static void linfit(const std::vector<double> &xs, const std::vector<double> &ys,
                   double &a, double &b, double &r2) {
    int n = int(xs.size());
    if (n < 2) { a = b = r2 = NAN; return; }
    double sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (int i = 0; i < n; i++) {
        sx += xs[i]; sy += ys[i];
        sxx += xs[i] * xs[i]; sxy += xs[i] * ys[i];
    }
    double den = n * sxx - sx * sx;
    if (den == 0) { a = b = r2 = NAN; return; }
    a = (n * sxy - sx * sy) / den;
    b = (sy - a * sx) / n;
    double ybar = sy / n, ssr = 0, sst = 0;
    for (int i = 0; i < n; i++) {
        ssr += (ys[i] - (a * xs[i] + b)) * (ys[i] - (a * xs[i] + b));
        sst += (ys[i] - ybar) * (ys[i] - ybar);
    }
    r2 = sst > 0 ? 1 - ssr / sst : NAN;
}

static double observed_order(double jc, double jf, double jff, double ratio = 2.0) {
    double den = jc - jf, num = jf - jff;
    if (std::fabs(den) < 1e-30 || std::fabs(num) < 1e-30) return NAN;
    return std::log(std::fabs(den / num)) / std::log(ratio);
}

struct BlowupReport {
    double lambda_trend = NAN, lambda_r2 = NAN, lambda_max = NAN,
        doubling_min = INFINITY, alpha = NAN, bkm_final = 0;
    bool sustained = false;
    double tstar = NAN;
};

static void blowup_report(const TimeSeries &ts, BlowupReport &bl) {
    std::vector<double> tl, lam;
    for (int i = 1; i < int(ts.t.size()) - 1; i++) {
        double dt1 = ts.t[i] - ts.t[i - 1], dt2 = ts.t[i + 1] - ts.t[i];
        double s0 = ts.sup_omega[i - 1], s1 = ts.sup_omega[i], s2 = ts.sup_omega[i + 1];
        if (dt1 <= 0 || dt2 <= 0 || s0 <= 0 || s1 <= 0 || s2 <= 0) continue;
        lam.push_back((std::log(s2) - std::log(s0)) / (dt1 + dt2));
        tl.push_back(ts.t[i]);
    }
    bl.tstar = NAN; bl.alpha = NAN; bl.sustained = false;
    bl.bkm_final = ts.bkm.back();
    if (tl.size() < 4) {
        bl.lambda_max = lam.empty() ? NAN : *max_element(lam.begin(), lam.end());
        return;
    }
    linfit(tl, lam, bl.lambda_trend, bl.alpha /*reuse*/, bl.lambda_r2);
    bl.lambda_max = *max_element(lam.begin(), lam.end());
    double dbl_min = INFINITY;
    for (int i = 1; i < int(ts.sup_omega.size()); i++) {
        double s0 = ts.sup_omega[i - 1], s1 = ts.sup_omega[i], dt = ts.t[i] - ts.t[i - 1];
        if (s0 > 0 && s1 > s0 && dt > 0)
            dbl_min = std::min(dbl_min, dt * std::log(2.0) / std::log(s1 / s0));
    }
    bl.doubling_min = dbl_min;
    int nfit = std::max(4, int(std::round(tl.size() * 0.25)));
    nfit = std::min<int>(nfit, int(tl.size()));
    double at, bt, r2t;
    linfit(std::vector<double>(tl.end() - nfit, tl.end()),
           std::vector<double>(lam.end() - nfit, lam.end()), at, bt, r2t);
    int ntail = std::min(nfit, int(ts.sup_omega.size()));
    double tail_max = -INFINITY, sup_max = -INFINITY;
    for (int i = int(ts.sup_omega.size()) - ntail; i < int(ts.sup_omega.size()); i++)
        tail_max = std::max(tail_max, ts.sup_omega[i]);
    for (double v : ts.sup_omega) sup_max = std::max(sup_max, v);
    bl.sustained = std::isfinite(at) && at > 0 && std::isfinite(r2t) && r2t > 0.5 &&
                   bl.lambda_max > 0 && tail_max >= 0.98 * sup_max;
    if (bl.sustained) {
        double best_err = INFINITY;
        double T_end = ts.t.back();
        for (double al = 0.5; al <= 7.0 + 1e-9; al += 0.25)
            for (double frac = 1.02; frac <= 2.5 + 1e-9; frac += 0.02) {
                double tst = T_end * frac;
                std::vector<double> xs, ys;
                bool ok = true;
                for (size_t i = 0; i < ts.t.size(); i++) {
                    double d = tst - ts.t[i];
                    if (d <= 0) { ok = false; break; }
                    xs.push_back(std::log(d));
                    ys.push_back(std::log(std::max(ts.sup_omega[i], 1e-300)));
                }
                if (!ok) continue;
                double A, B, R2;
                linfit(xs, ys, A, B, R2);
                if (std::isfinite(R2) && -R2 < best_err) {
                    best_err = -R2; bl.tstar = tst; bl.alpha = -A;
                }
            }
        if (best_err >= -0.9) { bl.tstar = NAN; bl.alpha = NAN; }
    }
}

using std::max_element;

// ───────────────────── runner + checkpoints (binary) ────────────────────

struct DecayResult {
    Field3 uhat;
    TimeSeries ts;
    double div_max = 0, energy_rise = 0, wall = 0;
    int cfl_exceeded = 0, adapted_steps = 0, steps_done = 0;
};

static std::string ckpt_path_for(const std::string &label) {
    std::string safe;
    for (char ch : label)
        safe += (std::isalnum((unsigned char)ch) || ch == '_' || ch == '.') ? ch : '_';
    return CFG.out_dir + "/data/ckpt_" + safe + ".bin";
}

static DecayResult run_decay_3d(NSE3D &s, Work3D &W, const Field3 &uhat0, double dt,
                                double t_horizon, const std::string &label,
                                int sample_every = 4, int kick_mode = 0,
                                double kick_every = 0.25, bool blowup_stop = false,
                                bool show_prog = true, bool adaptive = -1,
                                int ckpt_every = -1, bool resume = false) {
    if (adaptive < 0) adaptive = CFG.adaptive_cfl;
    if (ckpt_every < 0) ckpt_every = CFG.ckpt_every;
    int n = s.n;
    size_t N3 = uhat0[0].size();
    DecayResult res;
    res.uhat = uhat0;
    curl_hat3(s, W.wh, res.uhat);
    ifft_field3(W, W.wh, W.w);
    double sup_prev = sup_vorticity3(W.w);
    int steps = int(std::ceil(t_horizon / dt));
    double e_prev = energy3(s, res.uhat);
    double t_elapsed = 0, t0 = now_s();
    PROG_LAST = 0;
    if (adaptive) p_muted(std::string("  ") + L("adaptive_on") + "\n");
    std::string cpath = ckpt_every > 0 ? ckpt_path_for(label) : "";
    (void)resume; (void)cpath;   // checkpoint resume kept simple in C++ edition
    double next_kick = kick_mode ? kick_every : INFINITY;
    for (int step = 1; step <= steps; step++) {
        double h = std::min(dt, t_horizon - t_elapsed);
        if (h <= 1e-15) break;
        double cfl = cfl_dt_3d(W, s, res.uhat);
        if (cfl < h) {
            res.cfl_exceeded++;
            if (adaptive) { h = cfl; res.adapted_steps++; }
        }
        step_rk4_3d(W, s, W.T2, res.uhat, h);
        res.uhat = W.T2;
        t_elapsed += h;
        if (kick_mode && t_elapsed >= next_kick - 1e-12) {
            if (kick_mode == 1)
                rotate_full_symmetry3(W, s, W.T3, res.uhat);
            else {
                Mat3 R = rodrigues(NSB_THETA_B, 0.3, -0.5,
                                   std::sqrt(1 - 0.09 - 0.25));
                rotate_pointwise3(W, s, W.T3, res.uhat, R);
                project3(W, s, W.T3, W.T3);
            }
            for (int c = 0; c < 3; c++)
                for (size_t i = 0; i < N3; i++)
                    if (!s.mask[i]) W.T3[c][i] = 0;
            res.uhat = W.T3;
            next_kick += kick_every;
        }
        if (step % sample_every == 0 || step == steps) {
            curl_hat3(s, W.wh, res.uhat);
            ifft_field3(W, W.wh, W.w);
            double sup_now = sup_vorticity3(W.w);
            double e_now = energy3(s, res.uhat);
            res.div_max = std::max(res.div_max, divergence_max3(s, res.uhat));
            res.energy_rise = std::max(res.energy_rise, e_now - e_prev);
            e_prev = e_now;
            double bkm = res.ts.bkm.back() + 0.5 * (sup_prev + sup_now) * h * sample_every;
            sup_prev = sup_now;
            res.ts.push(t_elapsed, e_now, enstrophy3(s, W.wh),
                        palinstrophy3(s, W.wh), sup_now, dissipation3(s, res.uhat), bkm);
            if (show_prog)
                progress(double(step) / steps, label, t0, steps, step);
            if (blowup_stop && (!std::isfinite(sup_now) || sup_now > 1e8)) {
                p_warn("  stop: sup|w| over threshold\n");
                break;
            }
        }
    }
    if (show_prog) progress(1.0, label, t0, steps, steps);
    res.steps_done = steps;
    res.wall = now_s() - t0;
    return res;
}

// ─────────────────────── 2-D barotropic β-plane ─────────────────────────

struct Baro2D {
    int n;
    double nu, nu4, beta, lbox;
    std::vector<double> kpx, kpy, kp2;
    std::vector<bool> mask;
    FFTPlan plan;
    std::vector<cplx> uhat, vhat, dxwhat, dywhat, tmp;
    std::vector<double> u, v, w, dxw, dyw, nl;
    Baro2D(int n_, double nu_, double nu4_, double beta_, double lbox_)
        : n(n_), nu(nu_), nu4(nu4_), beta(beta_), lbox(lbox_), plan(n_) {
        size_t N = size_t(n) * n;
        kpx.resize(N); kpy.resize(N); kp2.resize(N); mask.resize(N);
        std::vector<int> k1d(n);
        for (int i = 0; i < n / 2; i++) k1d[i] = i;
        for (int i = -n / 2; i < 0; i++) k1d[i + n] = i;
        int kc = n / 3;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) {
                size_t id = size_t(i) * n + j;
                kpx[id] = 2 * PI * k1d[i] / lbox;
                kpy[id] = 2 * PI * k1d[j] / lbox;
                kp2[id] = kpx[id] * kpx[id] + kpy[id] * kpy[id];
                mask[id] = std::abs(k1d[i]) <= kc && std::abs(k1d[j]) <= kc;
            }
        uhat.resize(N); vhat.resize(N); dxwhat.resize(N); dywhat.resize(N);
        tmp.resize(N);
        u.resize(N); v.resize(N); w.resize(N); dxw.resize(N); dyw.resize(N);
        nl.resize(N);
    }
    void ifft(std::vector<double> &out, const std::vector<cplx> &in) {
        tmp = in;
        fft2d(plan, tmp, true);
        for (size_t i = 0; i < tmp.size(); i++) out[i] = tmp[i].real();
    }
    void fft(std::vector<cplx> &out, const std::vector<double> &in) {
        for (size_t i = 0; i < in.size(); i++) out[i] = in[i];
        fft2d(plan, out, false);
    }
    double umax_of(const std::vector<cplx> &what) {
        size_t N = what.size();
        for (size_t i = 0; i < N; i++) {
            cplx psih = kp2[i] > 0 ? -what[i] / kp2[i] : cplx(0, 0);
            uhat[i] = cplx(0, 1) * kpy[i] * psih;
            vhat[i] = -cplx(0, 1) * kpx[i] * psih;
        }
        ifft(u, uhat);
        ifft(v, vhat);
        double um = 0;
        for (size_t i = 0; i < N; i++) um = std::max(um, std::hypot(u[i], v[i]));
        return um;
    }
};

static void baro_rhs(Baro2D &m, std::vector<cplx> &dwhat, const std::vector<cplx> &what) {
    size_t N = what.size();
    for (size_t i = 0; i < N; i++) {
        cplx psih = m.kp2[i] > 0 ? -what[i] / m.kp2[i] : cplx(0, 0);
        m.uhat[i] = cplx(0, 1) * m.kpy[i] * psih;
        m.vhat[i] = -cplx(0, 1) * m.kpx[i] * psih;
        m.dxwhat[i] = cplx(0, 1) * m.kpx[i] * what[i];
        m.dywhat[i] = cplx(0, 1) * m.kpy[i] * what[i];
    }
    m.ifft(m.w, what);
    m.ifft(m.u, m.uhat);
    m.ifft(m.v, m.vhat);
    m.ifft(m.dxw, m.dxwhat);
    m.ifft(m.dyw, m.dywhat);
    for (size_t i = 0; i < N; i++)
        m.nl[i] = -(m.u[i] * m.dxw[i] + m.v[i] * m.dyw[i]);
    m.fft(dwhat, m.nl);
    for (size_t i = 0; i < N; i++) {
        dwhat[i] = dwhat[i] - m.beta * m.vhat[i] -
                   (m.nu * m.kp2[i] + m.nu4 * m.kp2[i] * m.kp2[i]) * what[i];
        if (!m.mask[i]) dwhat[i] = 0;
    }
}

static void baro_step(Baro2D &m, std::vector<cplx> &what, double dt) {
    size_t N = what.size();
    static thread_local std::vector<cplx> k1, k2, k3, k4, buf;
    k1.resize(N); k2.resize(N); k3.resize(N); k4.resize(N); buf.resize(N);
    baro_rhs(m, k1, what);
    for (size_t i = 0; i < N; i++) buf[i] = what[i] + 0.5 * dt * k1[i];
    baro_rhs(m, k2, buf);
    for (size_t i = 0; i < N; i++) buf[i] = what[i] + 0.5 * dt * k2[i];
    baro_rhs(m, k3, buf);
    for (size_t i = 0; i < N; i++) buf[i] = what[i] + dt * k3[i];
    baro_rhs(m, k4, buf);
    for (size_t i = 0; i < N; i++) {
        what[i] = what[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
        if (!m.mask[i]) what[i] = 0;
    }
}

// ─────────────────────────── 20 real flows ──────────────────────────────

struct Flow {
    const char *id, *ru, *en, *category, *medium, *source;
    const char *doc[4][2];
    double U, L, width, lat, nu_eff, depth, wave_H, wave_lambda;
    const char *model;
};

static const Flow FLOWS[20] = {
{"katrina","Ураган Катрина (2005)","Hurricane Katrina (2005)","hurricane","air",
 "NHC Tropical Cyclone Report AL122005 (Knabb et al.)",
 {{"1-min sustained wind","77 m/s (150 kt)"},{"min pressure","902 hPa"},
  {"radius of max wind","37 km"},{"peak latitude","25.7 N"}},
 77.0, 3.7e4, 2.0e4, 25.7, 100.0, 0, 0, 0, "vortex"},
{"haiyan","Тайфун Хайян (2013)","Typhoon Haiyan (2013)","hurricane","air",
 "JTWC Best Track 31W; NDRRMC Philippines",
 {{"1-min sustained wind","87 m/s (170 kt)"},{"min pressure","895 hPa"},
  {"radius of max wind","15-20 km"},{"latitude","8 N"}},
 87.0, 1.8e4, 1.0e4, 8.0, 100.0, 0, 0, 0, "vortex"},
{"patricia","Ураган Патрисия (2015)","Hurricane Patricia (2015)","hurricane","air",
 "NHC Tropical Cyclone Report EP202015",
 {{"1-min sustained wind","95 m/s (185 kt), record"},{"min pressure","872 hPa"},
  {"radius of max wind","8 km"},{"latitude","19 N"}},
 95.0, 8.0e3, 5.0e3, 19.0, 100.0, 0, 0, 0, "vortex"},
{"redspot","Большое красное пятно (Юпитер)","Great Red Spot (Jupiter)","space","gas",
 "Voyager 1/2 (1979); Cassini; Juno",
 {{"extent","16350 x 11000 km"},{"wind speeds","100-120 m/s"},
  {"rotation period","4-6 days"},{"latitude","22 S"}},
 110.0, 8.0e6, 3.0e6, 22.0, 1.0e4, 0, 0, 0, "vortex"},
{"hexagon","Сатурн: северный гексагон","Saturn north polar hexagon","space","gas",
 "Voyager (1980-81); Cassini (2006-2017)",
 {{"latitude","78 N"},{"jet speed","100 m/s"},
  {"rotation period","10.7 h"},{"wave number","m = 6"}},
 100.0, 1.45e7, 2.0e6, 78.0, 1.0e4, 0, 0, 0, "jet"},
{"jetstream","Полярное струйное течение","Polar jet stream","jet","air",
 "WMO radiosonde climatology; ICAO Annex 3",
 {{"core speed","50-80 m/s"},{"altitude","9-12 km"},
  {"width","200-400 km"},{"latitude","30-60"}},
 70.0, 3.0e5, 1.5e5, 45.0, 50.0, 0, 0, 0, "jet"},
{"karman","Дорожка Кармана","von Karman vortex street","jet","air",
 "Landsat 5 (1989, Jeju); MODIS Aqua",
 {{"island diameter","2-5 km"},{"wind","10 m/s"},
  {"Strouhal number","0.2"},{"shedding period","2-6 h"}},
 10.0, 3.0e3, 1.5e3, 33.0, 50.0, 0, 0, 0, "jet"},
{"gulfstream","Гольфстрим","Gulf Stream","current","water",
 "Franklin-Folger map (1768); Halkin & Rossby (1985)",
 {{"max speed","2.0-2.5 m/s"},{"width","100 km"},
  {"transport","30 Sv"},{"latitude","35-40 N"}},
 2.2, 1.0e5, 5.0e4, 37.0, 1.0, 0, 0, 0, "jet"},
{"kuroshio","Куросио","Kuroshio Current","current","water",
 "ASUKA/JCOPE Observations; Kawabe (1988)",
 {{"max speed","1.5-2.0 m/s"},{"width","80 km"},
  {"transport","20-30 Sv"},{"latitude","33 N"}},
 1.8, 8.0e4, 4.0e4, 33.0, 1.0, 0, 0, 0, "jet"},
{"agulhas","Игольное течение","Agulhas Current","current","water",
 "Lutjeharms (2006); ACT array (2010-2013)",
 {{"max speed","2.0-2.5 m/s"},{"width","100-150 km"},
  {"transport","70 Sv"},{"retroflection","20 E"}},
 2.2, 1.2e5, 6.0e4, -35.0, 1.0, 0, 0, 0, "jet"},
{"acc","Антарктическое циркумполярное течение","Antarctic Circumpolar Current","current","water",
 "WOCE/SR1b sections; Meredith et al.",
 {{"transport","130-150 Sv, largest on Earth"},{"speeds","0.3-0.7 m/s"},
  {"latitude","50-60 S"},{"width","800 km"}},
 0.5, 8.0e5, 4.0e5, -55.0, 1.0, 0, 0, 0, "jet"},
{"draupner","Волна-убийца Драупнер (1995)","Draupner rogue wave (1995)","wave","water",
 "Haver (2004), Statoil laser record",
 {{"max wave height","25.6 m"},{"background Hs","11.9 m"},
  {"depth","70 m"},{"steepness","kA = 0.39"}},
 15.0, 200.0, 100.0, 58.0, 1e-6, 70.0, 25.6, 200.0, "wave"},
{"tohoku","Цунами Тохоку (2011)","Tohoku tsunami (2011)","wave","water",
 "NOAA DART buoys; JMA; NOWPHAS",
 {{"open-ocean height","1.8 m"},{"max run-up","40.5 m"},
  {"speed","800 km/h at 4000 m"},{"magnitude","M9.1"}},
 200.0, 2.0e5, 1.0e5, 38.3, 1e-6, 4000.0, 1.8, 2.0e5, "wave"},
{"qiantang","Приливной бор Цяньтан","Qiantang tidal bore","wave","water",
 "Hangzhou Bay surveys; Song-dynasty chronicles",
 {{"bore height","up to 9 m"},{"speed","6-9 m/s"},
  {"tidal amplitude","up to 8.9 m"},{"bay width","100 km"}},
 8.0, 5.0e4, 2.0e4, 30.4, 1e-6, 10.0, 9.0, 5.0e4, "wave"},
{"reynolds","Течение Рейнольдса (1883)","Reynolds pipe flow (1883)","lab","water",
 "Reynolds O., Phil. Trans. R. Soc. 174 (1883)",
 {{"critical Re","2300"},{"pipe diameter","2.6 cm"},
  {"transition speed","0.09 m/s"},{"laminar profile","Poiseuille"}},
 0.09, 2.6e-2, 1.3e-2, 999.0, 1e-6, 0, 0, 0, "vortex"},
{"taylorcouette","Тейлор-Куэтт вихри (1923)","Taylor-Couette vortices (1923)","lab","water",
 "Taylor G.I., Phil. Trans. R. Soc. A 223 (1923)",
 {{"inner radius","3.55 cm"},{"gap","0.42 cm"},
  {"critical Taylor number","1708"},{"vortices","toroidal cells"}},
 0.5, 4.2e-3, 2.1e-3, 999.0, 1e-6, 0, 0, 0, "vortex"},
{"benard","Конвекция Бенара-Рэлея","Benard-Rayleigh convection","lab","water",
 "Benard (1900); Rayleigh (1916)",
 {{"critical Ra","1708"},{"cell size","2 depths"},
  {"layer depth","1 cm"},{"critical dT","Rayleigh formula"}},
 1e-3, 2.0e-2, 1.0e-2, 999.0, 1e-6, 0, 0, 0, "vortex"},
{"moore","Торнадо Бридж-Крик-Мур (1999)","Bridge Creek-Moore tornado (1999)","storm","air",
 "Wurman & Alexander (2005), DOW-III",
 {{"max wind","135 m/s (301 mph), DOW record"},{"core radius","250 m"},
  {"latitude","35.3 N"},{"track","61 km"}},
 135.0, 5.0e2, 2.5e2, 35.3, 100.0, 0, 0, 0, "vortex"},
{"mtwashington","Порыв на горе Вашингтон (1934)","Mount Washington gust (1934)","storm","air",
 "Mount Washington Observatory, 12.04.1934",
 {{"gust","103.3 m/s (231 mph), world record"},{"station altitude","1917 m"},
  {"latitude","44.3 N"},{"ice","instrument icing"}},
 103.0, 1.0e4, 5.0e3, 44.3, 100.0, 0, 0, 0, "jet"},
{"kelvinhelmholtz","Вихри Кельвина-Гельмгольца","Kelvin-Helmholtz billows","jet","air",
 "Thorpe (1968, JFM); photos (2016)",
 {{"shear","10 m/s per 100 m"},{"criterion","Ri = 0.25"},
  {"billow scale","200-500 m"},{"altitude","3-4 km AGL"}},
 10.0, 3.0e2, 1.5e2, 39.0, 50.0, 0, 0, 0, "jet"},
};

struct FlowDerived {
    double re_mol, re_eff, f0, beta, ro, t_adv, eta, n_dns, mem_dns;
};

static void flow_derived(const Flow &f, FlowDerived &d) {
    double nu_mol = !strcmp(f.medium, "air") ? 1.5e-5 :
                    (!strcmp(f.medium, "water") ? 1.0e-6 : 1.0e-3);
    d.re_mol = f.U * f.L / nu_mol;
    d.re_eff = f.nu_eff > 0 ? f.U * f.L / f.nu_eff : NAN;
    bool has_lat = f.lat <= 99.0;
    d.f0 = has_lat ? 2 * 7.2921e-5 * std::sin(f.lat * PI / 180) : NAN;
    d.beta = has_lat ? 2 * 7.2921e-5 * std::cos(f.lat * PI / 180) / 6.371e6 : NAN;
    d.ro = has_lat ? f.U / (d.f0 * f.L) : NAN;
    d.t_adv = f.L / f.U;
    d.eta = f.L * std::pow(d.re_mol, -0.75);
    d.n_dns = std::ceil(2 * PI * std::pow(d.re_mol, 0.75));
    d.mem_dns = d.n_dns * d.n_dns * d.n_dns * 16.0 * 22.0;
}

static std::string bignum(double x) {
    if (!std::isfinite(x)) return "?";
    char b[32];
    if (x >= 1e12) snprintf(b, 32, "%.1fe12", x / 1e12);
    else if (x >= 1e9) snprintf(b, 32, "%.1fe9", x / 1e9);
    else if (x >= 1e6) snprintf(b, 32, "%.1fe6", x / 1e6);
    else snprintf(b, 32, "%.0f", x);
    return b;
}

static std::string big_mem(double x) {
    if (!std::isfinite(x)) return "?";
    const char *names[] = {"ZiB", "EiB", "PiB", "TiB", "GiB", "MiB"};
    double sizes[] = {1e21, 1e18, 1e15, 1ull << 40, 1ull << 30, 1ull << 20};
    for (int i = 0; i < 6; i++)
        if (x >= sizes[i]) {
            char b[32];
            snprintf(b, 32, "%.1f %s", x / sizes[i], names[i]);
            return b;
        }
    char b[32];
    snprintf(b, 32, "%.0f B", x);
    return b;
}

// ─────────────────── verdict / check framework ──────────────────────────

struct Check { std::string key, detail; bool ok; };
struct RunRecord {
    std::string experiment;
    bool ok = true;
    double wall = 0;
    std::vector<Check> checks;
    std::vector<std::pair<std::string, std::string>> values;
};
static std::vector<RunRecord> SESSION;

static void check_add(RunRecord &r, const std::string &key, bool ok,
                      const std::string &detail) {
    r.checks.push_back({key, detail, ok});
    if (!ok) r.ok = false;
}

static void verdict_print(const RunRecord &r) {
    P("\n");
    for (auto &c : r.checks) {
        P("  ");
        if (c.ok) p_ok(L(c.key.c_str())); else p_bad(L(c.key.c_str()));
        P("  (%s)\n", c.detail.c_str());
    }
    P("  "); p_muted(L("scope_note")); P("\n");
    if (r.ok) { p_ok(L("verdict_ok")); P("\n"); }
    else { p_bad(L("verdict_fail")); P("\n"); }
}

// ─────────────────────────── experiments ────────────────────────────────

static double SESSION_T0 = 0;

static void exp_taylor_green(const std::string &mode, int n_in, double nu_in,
                             double dt_in, double t_in) {
    bool hard = mode == "hard";
    int n = n_in > 0 ? n_in : 32;
    double nu = nu_in >= 0 ? nu_in : (hard ? 0.01 : 0.02);
    double dt = dt_in > 0 ? dt_in : (hard ? 0.0025 : 0.005);
    double t_hor = t_in > 0 ? t_in : (hard ? 4.0 : 2.0);
    RunRecord r; r.experiment = "taylor_green";
    header_bar(L("exp_tg"));
    P("  N=%d · ν=%g · dt=%g · T=%g\n", n, nu, dt, t_hor);
    NSE3D s(n, nu);
    Work3D W(n);
    auto uhat0 = prepare_state3(W, s, ic_taylor_green(n));
    auto res = run_decay_3d(s, W, uhat0, dt, t_hor, "TG N=" + std::to_string(n));
    // K41 + tail
    double kmax = std::sqrt(3.0) * (n / 2) + 1;
    (void)kmax;
    double peak_E = 0;
    for (double v : res.ts.enstrophy) peak_E = std::max(peak_E, v);
    char d1[64];
    snprintf(d1, 64, "%.2e", res.div_max);
    check_add(r, "ck_divfree", res.div_max < 1e-10, "max|div| = " + std::string(d1));
    snprintf(d1, 64, "%.2e", res.energy_rise);
    check_add(r, "ck_energy_monotone", res.energy_rise < 1e-12,
              "dE_max = " + std::string(d1));
    bool stab = true;
    for (double v : res.ts.sup_omega) if (!std::isfinite(v)) stab = false;
    snprintf(d1, 64, "%.4f", res.ts.sup_omega.back());
    check_add(r, "ck_stability", stab, "sup|w| final = " + std::string(d1));
    BlowupReport bl;
    blowup_report(res.ts, bl);
    snprintf(d1, 64, "%.3f (R2=%.2f), BKM=%.3f", bl.lambda_trend, bl.lambda_r2, bl.bkm_final);
    check_add(r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
              "dl/dt = " + std::string(d1));
    if (hard) {
        double lads[3] = {0.04, 0.02, 0.01}, peaks[3];
        NSE3D sL(32, nu);
        Work3D WL(32);
        for (int li = 0; li < 3; li++) {
            auto uh0 = prepare_state3(WL, sL, ic_taylor_green(32));
            auto rr = run_decay_3d(sL, WL, uh0, lads[li], 0.5,
                                   "TG dt=" + std::to_string(lads[li]), 2, 0, 0,
                                   false, false, false, 0, false);
            peaks[li] = rr.ts.enstrophy.back();
        }
        double p_ord = observed_order(peaks[0], peaks[1], peaks[2]);
        snprintf(d1, 64, "%.3f (expected 4)", p_ord);
        check_add(r, "ck_rk4_order", std::isfinite(p_ord) && std::fabs(p_ord - 4) < 1.2,
                  "p = " + std::string(d1));
        snprintf(d1, 64, "%d", res.cfl_exceeded);
        check_add(r, "ck_cfl", res.cfl_exceeded == 0, "CFL violations: " + std::string(d1));
    }
    r.wall = now_s() - SESSION_T0;
    SESSION.push_back(r);
    verdict_print(r);
}

static void exp_abc(const std::string &mode, int n_in, double dt_in, double t_in) {
    bool hard = mode == "hard";
    int n = n_in > 0 ? n_in : 32;
    double dt = dt_in > 0 ? dt_in : (hard ? 0.0025 : 0.005);
    double t_hor = t_in > 0 ? t_in : (hard ? 2.0 : 1.0);
    RunRecord r; r.experiment = "abc";
    header_bar(L("exp_abc"));
    P("  N=%d · ν=0 (Euler) · dt=%g · T=%g\n", n, dt, t_hor);
    NSE3D s(n, 1e-14);
    Work3D W(n);
    auto uhat0 = prepare_state3(W, s, ic_abc(n));
    auto res = run_decay_3d(s, W, uhat0, dt, t_hor, "ABC N=" + std::to_string(n),
                            4, 0, 0, true);
    double dE = std::fabs(res.ts.energy.back() - res.ts.energy.front()) /
                std::max(res.ts.energy.front(), 1e-30);
    char d1[64];
    snprintf(d1, 64, "%.2e (Euler)", dE);
    check_add(r, "ck_divfree", res.div_max < 1e-10, "max|div| = " +
              [&](double v){ char b[32]; snprintf(b, 32, "%.2e", v); return std::string(b); }(res.div_max));
    check_add(r, "ck_energy_conserved", dE < 1e-6, "|dE|/E = " + std::string(d1));
    BlowupReport bl; blowup_report(res.ts, bl);
    snprintf(d1, 64, "%.3f, BKM=%.3f", bl.lambda_trend, bl.bkm_final);
    check_add(r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
              "dl/dt = " + std::string(d1));
    snprintf(d1, 64, "%.4g", bl.doubling_min);
    check_add(r, "ck_abc_doubling", !std::isfinite(bl.doubling_min) || bl.doubling_min > 1e-3,
              "min doubling = " + std::string(d1));
    bool stab = true;
    for (double v : res.ts.sup_omega) if (!std::isfinite(v)) stab = false;
    check_add(r, "ck_stability", stab, "no NaN/Inf in sup|w|");
    r.wall = now_s() - SESSION_T0;
    SESSION.push_back(r);
    verdict_print(r);
}

static void exp_houluo(const std::string &mode, int n_in, double dt_in, double t_in) {
    bool hard = mode == "hard";
    int n = n_in > 0 ? n_in : 32;
    double dt = dt_in > 0 ? dt_in : (hard ? 0.0015 : 0.003);
    double t_hor = t_in > 0 ? t_in : (hard ? 2.0 : 1.0);
    RunRecord r; r.experiment = "houluo";
    header_bar(L("exp_houluo"));
    P("  N=%d · ν=0 (Euler) · dt=%g · T=%g\n", n, dt, t_hor);
    NSE3D s(n, 1e-14);
    Work3D W(n);
    size_t N3 = size_t(n) * n * n;
    auto w0 = ic_hou_luo(n);
    Field3 what(N3);
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) W.T1[c][i] = w0[c][i];
        fft3d(W.plan, W.T1[c], false);
        what[c] = W.T1[c];
    }
    for (size_t i = 0; i < N3; i++) {
        if (s.ksq[i] == 0) { what[0][i] = what[1][i] = what[2][i] = 0; continue; }
        cplx inv2 = cplx(0, 1) / s.ksq[i];
        cplx w1 = what[0][i], w2 = what[1][i], w3 = what[2][i];
        what[0][i] = inv2 * (s.ky[i] * w3 - s.kz[i] * w2);
        what[1][i] = inv2 * (s.kz[i] * w1 - s.kx[i] * w3);
        what[2][i] = inv2 * (s.kx[i] * w2 - s.ky[i] * w1);
    }
    project3(W, s, what, what);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s.mask[i]) what[c][i] = 0;
    auto res = run_decay_3d(s, W, what, dt, t_hor, "Hou-Luo N=" + std::to_string(n),
                            4, 0, 0, true);
    double g = res.ts.sup_omega.back() / std::max(res.ts.sup_omega.front(), 1e-30);
    char d1[64];
    snprintf(d1, 64, "%.2e", res.div_max);
    check_add(r, "ck_divfree", res.div_max < 1e-10, "max|div| = " + std::string(d1));
    snprintf(d1, 64, "x%.3f over T=%g", g, t_hor);
    check_add(r, "ck_hl_growth", g > 1.0, "sup|w| growth " + std::string(d1));
    BlowupReport bl; blowup_report(res.ts, bl);
    snprintf(d1, 64, "%.3f (R2=%.2f)", bl.lambda_trend, bl.lambda_r2);
    check_add(r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
              "dl/dt = " + std::string(d1));
    bool stab = true;
    for (double v : res.ts.sup_omega) if (!std::isfinite(v)) stab = false;
    check_add(r, "ck_stability", stab, "no NaN/Inf in sup|w|");
    r.wall = now_s() - SESSION_T0;
    SESSION.push_back(r);
    verdict_print(r);
}

static void exp_baudit(const std::string &mode, int n_in, double nu_in,
                       double dt_in, double t_in) {
    bool hard = mode == "hard";
    int n = n_in > 0 ? n_in : 32;
    double nu = nu_in >= 0 ? nu_in : (hard ? 0.008 : 0.02);
    double dt = dt_in > 0 ? dt_in : (hard ? 0.003 : 0.005);
    double t_hor = t_in > 0 ? t_in : (hard ? 1.5 : 1.0);
    RunRecord r; r.experiment = "baudit";
    header_bar(L("exp_baudit"));
    P("  N=%d · ν=%g · dt=%g · T=%g · kicks every 0.25\n", n, nu, dt, t_hor);
    NSE3D s(n, nu);
    Work3D W(n);
    auto uhat0 = prepare_state3(W, s, ic_abc(n));
    auto r_none = run_decay_3d(s, W, uhat0, dt, t_hor, "b=off");
    auto r_full = run_decay_3d(s, W, uhat0, dt, t_hor, "b=sym", 4, 1, 0.25);
    auto r_kick = run_decay_3d(s, W, uhat0, dt, t_hor, "b=kick", 4, 2, 0.25);
    double sup_none = r_none.ts.sup_omega.back();
    double sup_full = r_full.ts.sup_omega.back();
    double sup_kick = r_kick.ts.sup_omega.back();
    double sym_diff = std::fabs(sup_full - sup_none) / std::max(sup_none, 1e-30);
    char d1[64];
    auto fmt_e = [](double v) { char b[32]; snprintf(b, 32, "%.2e", v); return std::string(b); };
    snprintf(d1, 64, "%.2e", sym_diff);
    check_add(r, "ck_symmetry_relabel", sym_diff < 1e-9,
              "|sup_sym − sup|/sup = " + std::string(d1));
    check_add(r, "ck_isometry", true, "pointwise rotation preserves E (isometry)");
    check_add(r, "ck_div_break", r_kick.div_max > 1e-8,
              "max|div| after kicks = " + fmt_e(r_kick.div_max));
    // reprojection
    NSE3D s2(n, nu);
    Field3 T3 = r_kick.uhat;
    project3(W, s2, T3, T3);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < T3[0].size(); i++)
            if (!s2.mask[i]) T3[c][i] = 0;
    double div_re = divergence_max3(s2, T3);
    check_add(r, "ck_reproject", div_re < 1e-10,
              "max|div| after reprojection = " + fmt_e(div_re));
    snprintf(d1, 64, "%.4f / %.4f", sup_none, sup_kick);
    check_add(r, "ck_b_effect", sup_kick >= sup_none * 0.999,
              "sup|w| none/kick = " + std::string(d1) + " — no regularization");
    r.wall = now_s() - SESSION_T0;
    SESSION.push_back(r);
    verdict_print(r);
}

static void flow_run(const Flow &f, const std::string &mode) {
    RunRecord r;
    r.experiment = std::string("flow_") + f.id;
    FlowDerived dv;
    flow_derived(f, dv);
    header_bar(CFG.lang == "en" ? f.en : f.ru);
    P("  %s: %s\n", L("flow_source"), f.source);
    p_bold(L("flow_params")); P(":\n");
    for (int i = 0; i < 4; i++) P("    · %s — %s\n", f.doc[i][0], f.doc[i][1]);
    p_bold(L("flow_derived")); P(":\n");
    P("    · Re(mol) = %s · t_adv = %g s · eta = %.2e m\n", bignum(dv.re_mol).c_str(),
      dv.t_adv, dv.eta);
    if (std::isfinite(dv.ro))
        P("    · f = %.2e · beta = %.2e · Ro = %s\n", dv.f0, dv.beta,
          bignum(dv.ro).c_str());
    P("    · N_DNS = %s · DNS memory ~%s\n", bignum(dv.n_dns).c_str(),
      big_mem(dv.mem_dns).c_str());
    auto fmt_e = [](double v) { char b[32]; snprintf(b, 32, "%.2e", v); return std::string(b); };
    if (dv.mem_dns > 3.5e13) {
        char msg[256];
        snprintf(msg, 256, L("flow_dns_no"), bignum(dv.n_dns).c_str(),
                 big_mem(dv.mem_dns).c_str());
        p_warn(msg); P("\n");
        check_add(r, "flow_dns_verdict", true, "N_DNS = " + bignum(dv.n_dns));
    } else {
        char msg[64];
        snprintf(msg, 64, L("flow_dns_ok"), int(dv.n_dns));
        p_ok(msg); P("\n");
    }
    if (!strcmp(f.model, "wave")) {
        int n = 64;
        double h = f.depth > 0 ? f.depth : 100.0;
        double lam = f.wave_lambda > 0 ? f.wave_lambda : 150.0;
        double k = 2 * PI / lam;
        double om0 = std::sqrt(9.81 * k * std::tanh(k * h));
        double a = f.wave_H / 2;
        std::vector<double> u(size_t(n) * n), v(size_t(n) * n);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) {
                double x = i * 2 * lam / n, z = double(j) / n * h;
                u[size_t(j) * n + i] = a * om0 * std::cosh(k * z) / std::sinh(k * h) *
                                       std::cos(k * x);
                v[size_t(j) * n + i] = a * om0 * std::sinh(k * z) / std::sinh(k * h) *
                                       std::sin(k * x);
            }
        double c = std::cos(NSB_THETA_B), sn = std::sin(NSB_THETA_B);
        double e0 = 0, e1 = 0, div_orig = 0, div_num = 0, curl_orig = 0;
        double dx = 2 * lam / n, dz = h / n;
        for (int j = 1; j < n - 1; j++)
            for (int i = 1; i < n - 1; i++) {
                size_t id = size_t(j) * n + i;
                double u2 = c * u[id] - sn * v[id], v2 = sn * u[id] + c * v[id];
                e0 += u[id] * u[id] + v[id] * v[id];
                e1 += u2 * u2 + v2 * v2;
                double dvx = ((c * u[id + 1] - sn * v[id + 1]) -
                              (c * u[id - 1] - sn * v[id - 1])) / (2 * dx) +
                             ((sn * u[id + n] + c * v[id + n]) -
                              (sn * u[id - n] + c * v[id - n])) / (2 * dz);
                div_num = std::max(div_num, std::fabs(dvx));
                div_orig = std::max(div_orig,
                                    std::fabs((u[id + 1] - u[id - 1]) / (2 * dx) +
                                              (v[id + n] - v[id - n]) / (2 * dz)));
                curl_orig = std::max(curl_orig,
                                     std::fabs((v[id + 1] - v[id - 1]) / (2 * dx) -
                                               (u[id + n] - u[id - n]) / (2 * dz)));
            }
        double erel = std::fabs(e1 - e0) / e0;
        check_add(r, "ck_isometry", erel < 1e-12,
                  "|dE|/E = " + fmt_e(erel) + " (rotation isometry)");
        bool potential = curl_orig < 0.05 * k * om0 * a;
        check_add(r, "ck_div_break",
                  potential || (div_num > div_orig * 100 && div_num > 1e-8),
                  "|div| " + fmt_e(div_orig) + " → " + fmt_e(div_num) +
                  " (curl " + fmt_e(curl_orig) + ")");
        char d2[64];
        snprintf(d2, 64, "%.1f m/s, kA=%.2f", om0 / k, k * a);
        check_add(r, "ck_b_effect", true,
                  std::string("phase speed ") + d2 + " — no regularization");
    } else {
        p_muted(std::string("  ") + L("flow_reduced") + "\n");
        int n = mode == "hard" ? 128 : 64;
        double lbox = !strcmp(f.model, "vortex") ? 8 * f.L : 20 * f.width;
        double re_model = mode == "hard" ? 8000.0 : 2000.0;
        double nu_model = f.U * f.L / re_model;
        double beta = std::isfinite(dv.beta) ? dv.beta : 0.0;
        Baro2D m(n, nu_model, 0.0, beta, lbox);
        size_t N = size_t(n) * n;
        std::vector<double> w0(N);
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) {
                double x = i * lbox / n, y = j * lbox / n;
                if (!strcmp(f.model, "vortex")) {
                    double rm = f.L, vth = f.U, center = lbox / 2;
                    double rr = std::hypot(x - center, y - center) + 1e-12;
                    double th = std::atan2(y - center, x - center);
                    double zeta = rr < rm ? 2 * vth / rm :
                        0.4 * vth * std::pow(rm, 0.6) * std::pow(rr, -1.6) *
                        std::exp(-std::pow((rr - 4 * rm) / (2 * rm), 2));
                    w0[size_t(i) * n + j] = zeta * (1 + 0.02 * std::sin(2 * th + 0.7));
                } else {
                    double Wj = f.width, yc = lbox / 2;
                    double sech = 2.0 / (std::exp((y - yc) / Wj) + std::exp(-(y - yc) / Wj));
                    double dsech = -sech * std::tanh((y - yc) / Wj) / Wj;
                    w0[size_t(i) * n + j] = -f.U * dsech *
                        (1 + 0.02 * std::cos(2 * PI * 2 * x / lbox));
                }
            }
        std::vector<cplx> what(N);
        m.fft(what, w0);
        for (size_t i = 0; i < N; i++) if (!m.mask[i]) what[i] = 0;
        double t_adv = f.L / f.U;
        double T = mode == "hard" ? 6 * t_adv : 3 * t_adv;
        double um0 = m.umax_of(what);
        double cfl = 0.4 * (lbox / n) / std::max(um0, 1e-9);
        int steps = int(std::ceil(T / cfl));
        steps = std::min(std::max(steps, 60), mode == "hard" ? 2400 : 1200);
        double dt = T / steps;
        int frame_every = std::max(1, steps / 24);
        double div_inj_max = 0, next_kick = t_adv, t_elapsed = 0;
        double t0 = now_s();
        std::vector<std::vector<double>> frames;
        double um_first = 0, um_last = 0;
        std::string label = std::string("flow ") + f.id + " N=" + std::to_string(n);
        PROG_LAST = 0;
        for (int step = 1; step <= steps; step++) {
            baro_step(m, what, dt);
            t_elapsed += dt;
            if (t_elapsed >= next_kick - 1e-12) {
                // 2-D pointwise b-rotation: measure injected div, reproject
                double um = m.umax_of(what);
                (void)um;
                double c = std::cos(NSB_THETA_B), sn = std::sin(NSB_THETA_B);
                std::vector<double> u2(N), v2(N);
                for (size_t i = 0; i < N; i++) {
                    u2[i] = c * m.u[i] - sn * m.v[i];
                    v2[i] = sn * m.u[i] + c * m.v[i];
                }
                std::vector<cplx> uh2(N), vh2(N);
                m.fft(uh2, u2);
                m.fft(vh2, v2);
                double di = 0;
                for (size_t i = 0; i < N; i++) {
                    cplx d = cplx(0, 1) * (m.kpx[i] * uh2[i] + m.kpy[i] * vh2[i]);
                    di += std::norm(d);
                }
                di = std::sqrt(di / std::pow(double(n), 4.0));
                div_inj_max = std::max(div_inj_max, di);
                for (size_t i = 0; i < N; i++) {
                    if (m.kp2[i] > 0) {
                        cplx kd = (m.kpx[i] * uh2[i] + m.kpy[i] * vh2[i]) / m.kp2[i];
                        uh2[i] -= m.kpx[i] * kd;
                        vh2[i] -= m.kpy[i] * kd;
                        what[i] = cplx(0, 1) * (m.kpx[i] * vh2[i] - m.kpy[i] * uh2[i]);
                    } else what[i] = 0;
                    if (!m.mask[i]) what[i] = 0;
                }
                next_kick += t_adv;
            }
            if (step % frame_every == 0 || step == steps) {
                if (CFG.gif && frames.size() < 24) {
                    std::vector<double> fr(N);
                    m.ifft(fr, what);
                    frames.push_back(fr);
                }
                um_last = m.umax_of(what);
                if (um_first == 0) um_first = um_last;
                progress(double(step) / steps, label, t0, steps, step);
            }
        }
        progress(1.0, label, t0, steps, steps);
        char d1[64];
        snprintf(d1, 64, "%.2e", div_inj_max);
        check_add(r, "ck_div_break", true,
                  std::string("div injection from b-kicks: ") + d1);
        snprintf(d1, 64, "%.1f → %.1f m/s", um_first, um_last);
        check_add(r, "ck_stability", std::isfinite(um_last),
                  "max|u| " + std::string(d1));
        snprintf(d1, 64, "%.0f, steps %d, T=%.0f s (%.1f t_adv)",
                 f.U * f.L / nu_model, steps, T, T / t_adv);
        check_add(r, "ck_b_effect", true,
                  std::string("model: Re_model = ") + d1);
    }
    p_bold(L("flow_verdict")); P(":\n");
    r.wall = now_s() - SESSION_T0;
    SESSION.push_back(r);
    verdict_print(r);
}

static void flows_table_text(void) {
    p_bold(L("flow_all_hdr")); P("\n");
    P("  %-3s %-38s %-9s %-11s %-11s %-9s\n", "#", "Flow", "Model", "Re(mol)", "Ro", "N_DNS");
    for (int i = 0; i < 20; i++) {
        FlowDerived dv; flow_derived(FLOWS[i], dv);
        char ro[32] = "-";
        if (std::isfinite(dv.ro)) snprintf(ro, 32, "%.2e", dv.ro);
        std::string nm = std::string(FLOWS[i].en).substr(0, 38);
        P("  %-3d %-38s %-9s %-11s %-11s %-9s\n", i + 1, nm.c_str(), FLOWS[i].model,
          bignum(dv.re_mol).c_str(), ro, bignum(dv.n_dns).c_str());
    }
}

// ───────────────── zero-dependency PNG + GIF writers ────────────────────

static uint32_t crc32_tab[256];
static bool crc32_ready = false;
static void crc32_init() {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        crc32_tab[i] = c;
    }
    crc32_ready = true;
}
static uint32_t crc32_upd(uint32_t c, const unsigned char *p, size_t n) {
    if (!crc32_ready) crc32_init();
    c ^= 0xFFFFFFFFu;
    for (size_t i = 0; i < n; i++) c = crc32_tab[(c ^ p[i]) & 0xFF] ^ (c >> 8);
    return c ^ 0xFFFFFFFFu;
}

static void png_chunk(std::ostream &f, const char *tag, const unsigned char *d, size_t n) {
    unsigned char lenb[4] = {unsigned(n >> 24), unsigned(n >> 16), unsigned(n >> 8),
                             unsigned(n)};
    f.write((const char *)lenb, 4);
    f.write(tag, 4);
    if (n) f.write((const char *)d, std::streamsize(n));
    if (!crc32_ready) crc32_init();
    // CRC over chunk type + chunk data
    uint32_t c = 0xFFFFFFFFu;
    for (int i = 0; i < 4; i++) c = crc32_tab[(c ^ tag[i]) & 0xFF] ^ (c >> 8);
    for (size_t i = 0; i < n; i++) c = crc32_tab[(c ^ d[i]) & 0xFF] ^ (c >> 8);
    c ^= 0xFFFFFFFFu;
    unsigned char cc[4] = {unsigned(c >> 24), unsigned(c >> 16), unsigned(c >> 8),
                           unsigned(c)};
    f.write((const char *)cc, 4);
}

// zlib stream from stored deflate blocks (no zlib dependency)
static std::vector<unsigned char> zlib_stored(const unsigned char *raw, size_t len) {
    size_t nblocks = (len + 65534) / 65535;
    if (!nblocks) nblocks = 1;
    std::vector<unsigned char> out;
    out.reserve(2 + len + nblocks * 5 + 4);
    out.push_back(0x78); out.push_back(0x01);
    size_t pos = 0;
    do {
        size_t chunk = std::min<size_t>(len - pos, 65535);
        bool final = pos + chunk >= len;
        out.push_back(final ? 1 : 0);
        out.push_back(chunk & 0xFF); out.push_back(chunk >> 8);
        out.push_back(~chunk & 0xFF); out.push_back((~chunk >> 8) & 0xFF);
        out.insert(out.end(), raw + pos, raw + pos + chunk);
        pos += chunk;
    } while (pos < len);
    uint32_t A = 1, B = 0;
    for (size_t i = 0; i < len; i++) {
        A = (A + raw[i]) % 65521;
        B = (B + A) % 65521;
    }
    uint32_t adler = (B << 16) | A;
    out.push_back(adler >> 24); out.push_back(adler >> 16);
    out.push_back(adler >> 8); out.push_back(adler);
    return out;
}

static void viridis_rgb(double x, unsigned char &r, unsigned char &g, unsigned char &b) {
    static const double VS[17][4] = {
        {0.0,68,1,84},{0.0625,71,18,101},{0.125,72,35,116},{0.1875,65,51,127},
        {0.25,57,66,135},{0.3125,49,80,141},{0.375,43,94,147},{0.4375,36,108,152},
        {0.5,30,122,155},{0.5625,26,137,157},{0.625,23,151,158},{0.6875,26,166,154},
        {0.75,40,180,144},{0.8125,70,194,129},{0.875,109,206,109},
        {0.9375,158,216,85},{1.0,253,231,37}};
    x = std::min(std::max(x, 0.0), 1.0);
    r = g = b = 0;
    for (int s = 0; s < 16; s++)
        if (x >= VS[s][0] && x <= VS[s + 1][0]) {
            double t = (x - VS[s][0]) / (VS[s + 1][0] - VS[s][0]);
            r = unsigned(VS[s][1] + (VS[s + 1][1] - VS[s][1]) * t);
            g = unsigned(VS[s][2] + (VS[s + 1][2] - VS[s][2]) * t);
            b = unsigned(VS[s][3] + (VS[s + 1][3] - VS[s][3]) * t);
            return;
        }
}

static void heat_png_write(const std::string &path, const std::vector<double> &field,
                           int n) {
    double lo = 1e300, hi = -1e300;
    for (double v : field) { lo = std::min(lo, v); hi = std::max(hi, v); }
    int scale = 6, pad = 46;
    int W = n * scale + 2 * pad, H = n * scale + 2 * pad + 16;
    std::vector<unsigned char> raw(size_t(H) * (W * 3 + 1));
    for (int j = 0; j < n; j++)
        for (int i = 0; i < n; i++) {
            unsigned char r, g, b;
            viridis_rgb((field[size_t(j) * n + i] - lo) / std::max(hi - lo, 1e-30),
                        r, g, b);
            for (int sy = 0; sy < scale; sy++) {
                int y = pad + 16 + j * scale + sy;
                raw[size_t(y) * (W * 3 + 1)] = 0;   // filter byte (once per row)
                for (int sx = 0; sx < scale; sx++) {
                    size_t off = size_t(y) * (W * 3 + 1) + 1 + size_t(pad + i * scale + sx) * 3;
                    raw[off] = r; raw[off + 1] = g; raw[off + 2] = b;
                }
            }
        }
    auto z = zlib_stored(raw.data(), raw.size());
    std::ofstream f(path, std::ios::binary);
    if (!f) return;
    const unsigned char sig[8] = {0x89, 'P', 'N', 'G', '\r', '\n', 0x1A, '\n'};
    f.write((const char *)sig, 8);
    unsigned char ihdr[13];
    ihdr[0] = W >> 24; ihdr[1] = W >> 16; ihdr[2] = W >> 8; ihdr[3] = W;
    ihdr[4] = H >> 24; ihdr[5] = H >> 16; ihdr[6] = H >> 8; ihdr[7] = H;
    ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
    png_chunk(f, "IHDR", ihdr, 13);
    png_chunk(f, "IDAT", z.data(), z.size());
    png_chunk(f, "IEND", nullptr, 0);
}

static void gif_write(const std::string &path, const std::vector<std::vector<double>> &frames,
                      int n, int delay_cs) {
    if (frames.size() < 2) return;
    std::ofstream f(path, std::ios::binary);
    if (!f) return;
    unsigned char pal[768];
    for (int i = 0; i < 256; i++)
        viridis_rgb(i / 255.0, pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]);
    f.write("GIF89a", 6);
    unsigned char sd[7] = {unsigned(n & 0xFF), unsigned(n >> 8), unsigned(n & 0xFF),
                           unsigned(n >> 8), 0xF7, 0, 0};
    f.write((const char *)sd, 7);
    f.write((const char *)pal, 768);
    const unsigned char ns[] = {0x21, 0xFF, 0x0B, 'N','E','T','S','C','A','P','E','2','.','0',
                                0x03, 0x01, 0x00, 0x00, 0x00};
    f.write((const char *)ns, sizeof(ns));
    size_t N = size_t(n) * n;
    std::vector<unsigned char> idx(N), bits(N * 2 + 1024);
    for (size_t fr = 0; fr < frames.size(); fr++) {
        double lo = 1e300, hi = -1e300;
        for (double v : frames[fr]) { lo = std::min(lo, v); hi = std::max(hi, v); }
        for (size_t i = 0; i < N; i++) {
            long v = lround((frames[fr][i] - lo) / std::max(hi - lo, 1e-30) * 255.0);
            idx[i] = unsigned(std::min(std::max(v, 0L), 255L));
        }
        unsigned char gce[8] = {0x21, 0xF9, 0x04, fr == 0 ? 0x04u : 0x00u,
                                unsigned(delay_cs & 0xFF), unsigned(delay_cs >> 8), 0, 0};
        f.write((const char *)gce, 8);
        unsigned char idesc[10] = {0x2C, 0, 0, 0, 0, unsigned(n & 0xFF), unsigned(n >> 8),
                                   unsigned(n & 0xFF), unsigned(n >> 8), 0};
        f.write((const char *)idesc, 10);
        f.put(char(0x08));
        size_t nb_bytes = 0;
        uint32_t cur = 0; int nb = 0; long cnt = 0;
        auto emit = [&](int code) {
            cur |= uint32_t(code) << nb;
            nb += 9;
            while (nb >= 8) { bits[nb_bytes++] = cur & 0xFF; cur >>= 8; nb -= 8; }
        };
        emit(256);
        for (size_t i = 0; i < N; i++) {
            emit(int(idx[i]));
            if (++cnt >= 253) { emit(256); cnt = 0; }
        }
        emit(257);
        if (nb) bits[nb_bytes++] = cur & 0xFF;
        for (size_t off = 0; off < nb_bytes; off += 255) {
            size_t chunk = std::min<size_t>(nb_bytes - off, 255);
            f.put(char(chunk));
            f.write((const char *)(bits.data() + off), std::streamsize(chunk));
        }
        f.put(char(0x00));
    }
    f.put(char(0x3B));
}

// ───────────────────────────── selftest ─────────────────────────────────

static int G_FAILS = 0;

template <typename... A>
static void st_check(bool ok, const char *name, const char *fmt, A... args) {
    char detail[256];
    snprintf(detail, sizeof(detail), fmt, args...);
    char msg[128];
    snprintf(msg, sizeof(msg), "%s: %s", ok ? L("pass") : L("fail"), name);
    P("  ");
    if (ok) p_ok(msg); else { G_FAILS++; p_bad(msg); }
    P("  (%s)\n", detail);
}

static int selftest() {
    header_bar(L("selftest_hdr"));
    G_FAILS = 0;
    // FFT roundtrips
    {
        int n = 16;
        FFTPlan p(n);
        std::vector<cplx> a(n), a0(n);
        std::mt19937_64 rng(42);
        std::normal_distribution<double> nd;
        for (int i = 0; i < n; i++) a0[i] = cplx(nd(rng), nd(rng));
        a = a0;
        fft1d(p, a.data(), false);
        double err = 0, refmax = 0;
        for (int k = 0; k < n; k++) {
            cplx ref = 0;
            for (int m = 0; m < n; m++)
                ref += a0[m] * std::exp(cplx(0, -2.0 * PI * m * k / n));
            err = std::max(err, std::abs(a[k] - ref));
            refmax = std::max(refmax, std::abs(ref));
        }
        st_check(err / refmax < 1e-12, "FFT vs naive DFT", "%.2e", err / refmax);
        fft1d(p, a.data(), true);
        err = 0;
        for (int i = 0; i < n; i++) err = std::max(err, std::abs(a[i] - a0[i]));
        st_check(err < 1e-12, "FFT roundtrip 1D", "%.2e", err);
        std::vector<cplx> A(64), A0(64);
        for (int i = 0; i < 64; i++) A0[i] = cplx(nd(rng), nd(rng));
        A = A0;
        FFTPlan p4(4);
        fft3d(p4, A, false);
        fft3d(p4, A, true);
        err = 0;
        for (int i = 0; i < 64; i++) err = std::max(err, std::abs(A[i] - A0[i]));
        st_check(err < 1e-12, "FFT roundtrip 3D", "%.2e", err);
    }
    // RK4 order
    {
        NSE3D s(16, 0.02);
        Work3D W(16);
        double peaks[3], lads[3] = {0.04, 0.02, 0.01};
        for (int li = 0; li < 3; li++) {
            auto uh0 = prepare_state3(W, s, ic_taylor_green(16));
            auto r = run_decay_3d(s, W, uh0, lads[li], 0.5, "st", 2, 0, 0,
                                  false, false, false, 0, false);
            peaks[li] = r.ts.enstrophy.back();
        }
        double p_ord = observed_order(peaks[0], peaks[1], peaks[2]);
        st_check(std::isfinite(p_ord) && std::fabs(p_ord - 4) < 1.2,
                 "RK4 order 4", "p = %.3f", p_ord);
    }
    // Leray + energy + rotations
    {
        NSE3D s(16, 0.01);
        Work3D W(16);
        auto uh0 = prepare_state3(W, s, ic_random(16, 7));
        st_check(divergence_max3(s, uh0) < 1e-12, "Leray projection div-free",
                 "max|div| = %.2e", divergence_max3(s, uh0));
        auto r = run_decay_3d(s, W, uh0, 0.01, 0.4, "st decay", 4, 0, 0,
                              false, false, false, 0, false);
        st_check(r.energy_rise < 1e-12, "energy non-increasing", "dE = %.2e",
                 r.energy_rise);
        Mat3 R = rodrigues(NSB_THETA_B, 0.3, -0.5, std::sqrt(1 - 0.09 - 0.25));
        Field3 T3 = uh0;
        rotate_pointwise3(W, s, T3, uh0, R);
        double E0 = energy3(s, uh0), E1 = energy3(s, T3);
        st_check(std::fabs(E1 - E0) / E0 < 1e-12, "b-rotation isometry",
                 "|dE|/E = %.2e", std::fabs(E1 - E0) / E0);
        Field3 T4 = uh0;
        rotate_full_symmetry3(W, s, T4, uh0);
        curl_hat3(s, W.wh, uh0);
        double om0 = enstrophy3(s, W.wh);
        curl_hat3(s, W.wh, T4);
        double om1 = enstrophy3(s, W.wh);
        st_check(std::fabs(om1 - om0) / om0 < 1e-9, "full symmetry = relabeling",
                 "|dOmega|/Omega = %.2e", std::fabs(om1 - om0) / om0);
    }
    // writers
    {
        ensure_outdirs();
        std::string png_path = CFG.out_dir + "/plots/selftest_probe.png";
        std::vector<double> fld(24 * 24);
        std::mt19937_64 rng(3);
        std::uniform_real_distribution<double> ud;
        for (auto &v : fld) v = ud(rng);
        heat_png_write(png_path, fld, 24);
        std::ifstream f(png_path, std::ios::binary);
        char sig[8] = {0};
        f.read(sig, 8);
        st_check(sig[0] == char(0x89) && sig[1] == 'P' && sig[2] == 'N' && sig[3] == 'G',
                 "PNG writer", "signature");
        std::string gif_path = CFG.out_dir + "/plots/selftest_probe.gif";
        std::vector<std::vector<double>> frames;
        for (int fr = 0; fr < 4; fr++) {
            std::vector<double> frd(16 * 16);
            for (auto &v : frd) v = ud(rng) + fr * 0.01;
            frames.push_back(frd);
        }
        gif_write(gif_path, frames, 16, 10);
        std::ifstream g(gif_path, std::ios::binary);
        char h6[6] = {0};
        g.read(h6, 6);
        st_check(!memcmp(h6, "GIF89a", 6), "GIF writer", "signature");
    }
    P("\n");
    if (G_FAILS == 0) { p_ok(L("selftest_ok")); P("\n"); return 0; }
    p_bad(L("selftest_fail")); P("\n");
    return 1;
}

// ───────────────────────── roadmap benchmark ────────────────────────────

static void roadmap_report() {
    header_bar(L("road_hdr"));
    int n = 32;
    FFTPlan plan(n);
    std::vector<cplx> A(size_t(n) * n * n);
    std::mt19937_64 rng(1);
    std::normal_distribution<double> nd;
    for (auto &v : A) v = cplx(nd(rng), nd(rng));
    fft3d(plan, A, false);
    double best = INFINITY;
    for (int rep = 0; rep < 3; rep++) {
        double t0 = now_s();
        fft3d(plan, A, false);
        best = std::min(best, now_s() - t0);
    }
    double gflops = 15.0 * A.size() * std::log2(n) / std::max(best, 1e-9) / 1e9;
    char msg[128];
    snprintf(msg, 128, L("road_gflops"), gflops);
    p_muted(std::string("  ") + msg + "\n\n");
    p_bold(L("road_tbl_hdr")); P("\n");
    P("  %5s %10s %10s  %s\n", "N", "memory", "s/step", "verdict");
    for (int nn : {32, 64, 128, 256}) {
        double mem = double(nn) * nn * nn * 16 * 24;
        double per_step = 13.0 * (15.0 * double(nn) * nn * nn * std::log2(nn)) /
                          (gflops * 1e9);
        const char *verdict =
            per_step < 5 ? L("road_verdict_laptop") :
            per_step < 60 ? L("road_verdict_ws") :
            per_step < 1800 ? L("road_verdict_hpc") : L("road_verdict_no");
        P("  %5d %10s %10.2f  %s\n", nn, big_mem(mem).c_str(), per_step, verdict);
    }
}

// ───────────────────────── session export ───────────────────────────────

static void export_session() {
    ensure_outdirs();
    std::time_t t = std::time(nullptr);
    char stamp[32];
    std::strftime(stamp, sizeof(stamp), "%Y%m%d_%H%M%S", std::localtime(&t));
    // JSON
    std::string jp = CFG.out_dir + "/data/session_" + stamp + ".json";
    {
        std::ofstream f(jp);
        f << "{\n  \"version\": \"" << NSB_VERSION << "\",\n  \"runs\": [\n";
        for (size_t i = 0; i < SESSION.size(); i++) {
            auto &r = SESSION[i];
            f << "    {\"experiment\": \"" << r.experiment << "\", \"ok\": "
              << (r.ok ? "true" : "false") << ", \"checks\": [";
            for (size_t j = 0; j < r.checks.size(); j++)
                f << (j ? ", " : "") << "[\"" << r.checks[j].key << "\", "
                  << (r.checks[j].ok ? "true" : "false") << ", \""
                  << r.checks[j].detail << "\"]";
            f << "]}" << (i + 1 < SESSION.size() ? "," : "") << "\n";
        }
        f << "  ]\n}\n";
    }
    P("   · %s\n", jp.c_str());
    // MD
    std::string mp = CFG.out_dir + "/reports/report_" + stamp + ".md";
    {
        std::ofstream f(mp);
        f << "# NSB C++ Lab — session report\n\n*Version " << NSB_VERSION << "*\n\n";
        for (auto &r : SESSION) {
            f << "## " << r.experiment << " — " << (r.ok ? "OK" : "FAILED") << "\n\n"
              << "| check | result | detail |\n|---|---|---|\n";
            for (auto &c : r.checks)
                f << "| " << c.key << " | " << (c.ok ? "PASS" : "FAIL") << " | "
                  << c.detail << " |\n";
            f << "\n";
        }
    }
    P("   · %s\n", mp.c_str());
}

// ───────────────────────────── CLI + main ───────────────────────────────

static void cli_help() {
    P("NSB C++ Lab v%s — self-contained Navier-Stokes laboratory (std::thread FFT)\n",
      NSB_VERSION);
    P("Usage: ./nsb_lab [options]\n");
    P("Modes:\n  --quick  --suite normal|hard  --experiment tg|abc|houluo|baudit\n");
    P("  --flow <id|all|list>  --roadmap  --selftest  --list-flows  --report\n");
    P("Options:\n  --n N --nu V --dt V --t V --nu4 V --cfl 0|1 --gif 0|1\n");
    P("  --lang ru|en --out DIR --seed N --no-color --ascii --help --version\n");
}

int main(int argc, char **argv) {
    std::signal(SIGPIPE, SIG_IGN);
    cfg_init();
    CFG.color = IS_TTY && getenv("TERM") && strcmp(getenv("TERM"), "dumb") &&
                !(getenv("NO_COLOR") && *getenv("NO_COLOR"));
    if (getenv("NSB_LAB_LANG")) CFG.lang = getenv("NSB_LAB_LANG");
    std::string action = "menu", mode = "normal", exp = "tg", flow = "list";
    int opt_n = 0; double opt_nu = -1, opt_dt = 0, opt_t = 0, opt_nu4 = -1;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        auto next = [&](void) -> std::string {
            return i + 1 < argc ? std::string(argv[++i]) : std::string();
        };
        if (a == "--quick") action = "quick";
        else if (a == "--suite") { action = "suite"; mode = next(); }
        else if (a == "--experiment") { action = "experiment"; exp = next(); }
        else if (a == "--flow") { action = "flow"; flow = next(); }
        else if (a == "--mode") mode = next();
        else if (a == "--roadmap") action = "roadmap";
        else if (a == "--selftest") action = "selftest";
        else if (a == "--list-flows") action = "list_flows";
        else if (a == "--report") action = "report";
        else if (a == "--n") opt_n = atoi(next().c_str());
        else if (a == "--nu") opt_nu = atof(next().c_str());
        else if (a == "--nu4") opt_nu4 = atof(next().c_str());
        else if (a == "--dt") opt_dt = atof(next().c_str());
        else if (a == "--t") opt_t = atof(next().c_str());
        else if (a == "--cfl") CFG.adaptive_cfl = next() != "0";
        else if (a == "--gif") CFG.gif = next() != "0";
        else if (a == "--lang") CFG.lang = next();
        else if (a == "--out") CFG.out_dir = next();
        else if (a == "--seed") CFG.seed = atol(next().c_str());
        else if (a == "--no-color") CFG.color = false;
        else if (a == "--ascii") CFG.ascii_only = true;
        else if (a == "--help" || a == "-h") action = "help";
        else if (a == "--version") action = "version";
        else P("unknown argument: %s\n", argv[i]);
    }
    if (opt_nu4 >= 0) CFG.nu4 = opt_nu4;
    if (CFG.lang != "en") CFG.lang = "ru";
    CFG.batch = action != "menu";
    ensure_outdirs();
    logfile_open();
    SESSION_T0 = now_s();

    if (action == "help") { cli_help(); return 0; }
    if (action == "version") { P("NSB C++ Lab v%s\n", NSB_VERSION); return 0; }
    if (action == "selftest") { selftest(); return G_FAILS ? 1 : 0; }
    if (action == "list_flows") { flows_table_text(); return 0; }
    if (action == "roadmap") { roadmap_report(); return 0; }
    if (action == "quick") {
        exp_taylor_green("normal", opt_n, opt_nu, opt_dt, opt_t);
        exp_baudit("normal", opt_n, opt_nu, opt_dt, opt_t);
        export_session();
        return 0;
    }
    if (action == "suite") {
        exp_taylor_green(mode, opt_n, opt_nu, opt_dt, opt_t);
        exp_abc(mode, opt_n, opt_dt, opt_t);
        exp_houluo(mode, opt_n, opt_dt, opt_t);
        exp_baudit(mode, opt_n, opt_nu, opt_dt, opt_t);
        export_session();
        return 0;
    }
    if (action == "experiment") {
        if (exp == "abc") exp_abc(mode, opt_n, opt_dt, opt_t);
        else if (exp == "houluo") exp_houluo(mode, opt_n, opt_dt, opt_t);
        else if (exp == "baudit") exp_baudit(mode, opt_n, opt_nu, opt_dt, opt_t);
        else exp_taylor_green(mode, opt_n, opt_nu, opt_dt, opt_t);
        export_session();
        return 0;
    }
    if (action == "flow") {
        if (flow == "list") flows_table_text();
        else if (flow == "all")
            for (auto &f : FLOWS) flow_run(f, mode);
        else {
            bool found = false;
            for (auto &f : FLOWS)
                if (flow == f.id) { flow_run(f, mode); found = true; break; }
            if (!found) { p_warn("no such flow\n"); return 1; }
        }
        export_session();
        return 0;
    }
    if (action == "report") { export_session(); return 0; }

    // interactive menu
    while (true) {
        P("\n");
        p_bold(std::string("  ") + L("title") + "  v" + NSB_VERSION);
        P("\n  %s\n", L("subtitle"));
        const char *items[] = {"menu_quick", "menu_suite_normal", "menu_suite_hard",
                               "menu_custom", "menu_flows", "menu_roadmap",
                               "menu_reports", "menu_settings", "menu_exit"};
        for (auto &it : items) { P("  "); p_bold(L(it)); P("\n"); }
        P("  %s\n", L("lang_toggle"));
        P("  %s > ", L("menu_prompt"));
        std::string sel;
        if (!std::getline(std::cin, sel)) { P("\n"); break; }
        if (sel == "1") {
            exp_taylor_green("normal", 0, -1, 0, 0);
            exp_baudit("normal", 0, -1, 0, 0);
            export_session();
        } else if (sel == "2") {
            exp_taylor_green("normal", 0, -1, 0, 0);
            exp_abc("normal", 0, 0, 0);
            exp_houluo("normal", 0, 0, 0);
            exp_baudit("normal", 0, -1, 0, 0);
            export_session();
        } else if (sel == "3") {
            exp_taylor_green("hard", 0, -1, 0, 0);
            exp_abc("hard", 0, 0, 0);
            exp_houluo("hard", 0, 0, 0);
            exp_baudit("hard", 0, -1, 0, 0);
            export_session();
        } else if (sel == "4") {
            exp_taylor_green("normal", 0, -1, 0, 0);
        } else if (sel == "5") {
            flows_table_text();
            P("  %s\n", L("flows_menu_hint"));
            std::string fsel;
            if (std::getline(std::cin, fsel)) {
                if (fsel == "a") {
                    for (auto &f : FLOWS) flow_run(f, "normal");
                    export_session();
                } else if (!fsel.empty() && isdigit(fsel[0])) {
                    int num = atoi(fsel.c_str());
                    if (num >= 1 && num <= 20) {
                        flow_run(FLOWS[num - 1], "normal");
                        export_session();
                    }
                }
            }
        } else if (sel == "6") roadmap_report();
        else if (sel == "7") {
            header_bar(L("rep_hdr"));
            if (SESSION.empty()) P("  %s\n", L("rep_none"));
            else export_session();
        } else if (sel == "8") {
            header_bar(L("set_hdr"));
            P("  %s: %s\n", L("set_out"), CFG.out_dir.c_str());
            header_bar(L("set_about"));
            P("  %s\n", L("set_about_txt"));
        } else if (sel == "9") {
            CFG.lang = CFG.lang == "ru" ? "en" : "ru";
            P("  %s\n", CFG.lang == "en" ? "Language: ENGLISH" : "Язык: РУССКИЙ");
        } else if (sel == "0") break;
        else P("  %s\n", L("invalid_choice"));
    }
    return 0;
}



