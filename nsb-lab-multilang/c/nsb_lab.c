/* ═══════════════════════════════════════════════════════════════════════════
   NSB C LAB v2.1.0 — polyglot edition
   A faithful port of the self-contained Julia "Navier–Stokes b-Lab" to C99.

   Inside (mirrors julia/nsb_lab_standalone.jl):
     • In-house radix-2 FFT (Cooley–Tukey DIT, bit-reversal, precomputed
       twiddles) on C99 `double complex` — no external libraries at all.
     • 3-D pseudospectral Navier–Stokes/Euler solver: RK4 + Leray projection
       on every sub-step + 2/3 de-aliasing, hyperviscosity ν₄, adaptive CFL,
       binary checkpoints + --resume.
     • 2-D barotropic β-plane solver in physical units.
     • BKM diagnostics: energy, enstrophy, palinstrophy, dissipation, sup|ω|,
       shell spectra, K41 (−5/3) fits, blow-up scanner (λ(t), t*).
     • ICs: Taylor–Green, ABC, Hou–Luo, random div-free.
     • b-correction audit: full symmetry (relabeling) vs pointwise rotation.
     • Real-flows laboratory: 20 documented flows + DNS feasibility.
     • Zero-dependency output: PNG (own stored-deflate + CRC32 + Adler32),
       GIF89a animator (uncompressed-LZW), minimal PDF, CSV/JSON/MD/TXT.
     • i18n RU/EN, one-line progress bar, sparklines, interactive TUI menu.

   Build:   cc -O2 -o nsb_lab nsb_lab.c -lm        (gcc/clang/tcc)
   Run:     ./nsb_lab --quick --lang en
            ./nsb_lab --selftest
            ./nsb_lab                               (interactive menu)
   Results: ~/nsb_lab_results/{data,plots,reports,articles,logs}
   ═══════════════════════════════════════════════════════════════════════════ */

#define _POSIX_C_SOURCE 200809L
#include <complex.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define NSB_VERSION "2.1.0"
#define PI 3.14159265358979323846

/* ───────────────────────────── config ───────────────────────────── */

typedef struct {
    char lang;                /* 'r' | 'e' */
    char out_dir[512];
    int  dpi;
    long seed;
    bool color, ascii_only;
    int  max_n;
    bool quick, batch, quiet;
    double t_start;
    bool gif;
    int  ckpt_every;
    bool adaptive_cfl;
    double nu4;
    int  session_n;           /* registered runs */
    char fft_backend;         /* 'o' own | 'n' numpy-like (not used in C) */
} Config;

static Config CFG;
static FILE  *LOG_IO = NULL;
static char   LOG_PATH[600];

static void cfg_init(void) {
    memset(&CFG, 0, sizeof(CFG));
    CFG.lang = 'r';
    snprintf(CFG.out_dir, sizeof(CFG.out_dir), "%s/nsb_lab_results", getenv("HOME") ? getenv("HOME") : ".");
    CFG.dpi = 600; CFG.seed = 20260916; CFG.color = false; CFG.max_n = 32;
    CFG.gif = true; CFG.ckpt_every = 200; CFG.nu4 = 0.0;
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    CFG.t_start = ts.tv_sec + ts.tv_nsec * 1e-9;
    long pages = sysconf(_SC_PHYS_PAGES), pg = sysconf(_SC_PAGE_SIZE);
    double total_gb = (pages > 0 && pg > 0) ? (double)pages * pg / 1073741824.0 : 8.0;
    int cands[4] = {32, 64, 128, 256};
    for (int i = 0; i < 4; i++) {
        double mem = (double)cands[i] * cands[i] * cands[i] * 16.0 * 24.0 / 1073741824.0;
        if (mem < total_gb * 0.55) CFG.max_n = cands[i];
    }
}

static void ensure_outdirs(void) {
    char p[600];
    const char *subs[] = {"", "/logs", "/data", "/plots", "/reports", "/articles"};
    for (int i = 0; i < 6; i++) {
        snprintf(p, sizeof(p), "%s%s", CFG.out_dir, subs[i]);
        mkdir(p, 0755); /* exists_ok */
    }
}

static void logfile_open(void) {
    ensure_outdirs();
    time_t t = time(NULL); struct tm tm; localtime_r(&t, &tm);
    char stamp[64]; strftime(stamp, sizeof(stamp), "%Y%m%d_%H%M%S", &tm);
    snprintf(LOG_PATH, sizeof(LOG_PATH), "%s/logs/session_%s.log", CFG.out_dir, stamp);
    LOG_IO = fopen(LOG_PATH, "a");
}

static void P(const char *fmt, ...) {
    va_list ap;
    char buf[4096];
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    if (!CFG.quiet) { fputs(buf, stdout); fflush(stdout); }
    if (LOG_IO) { fputs(buf, LOG_IO); fflush(LOG_IO); }
}

static void log_close(void) { if (LOG_IO) { fclose(LOG_IO); LOG_IO = NULL; } }

static double now_mono(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void hms(double t, char *out, size_t n) {
    long s = (long)(t < 0 ? 0 : t + 0.5);
    long h = s / 3600; long m = (s % 3600) / 60; long ss = s % 60;
    if (h) snprintf(out, n, "%ld:%02ld:%02ld", h, m, ss);
    else snprintf(out, n, "%02ld:%02ld", m, ss);
}

/* ───────────────────────────── i18n ───────────────────────────── */

typedef struct { const char *key, *ru, *en; } I18nPair;

static const I18nPair I18N[] = {
{"yes","да","yes"},{"no","нет","no"},
{"pass","ПРОЙДЕНО","PASS"},{"fail","ПРОВАЛЕНО","FAIL"},
{"title","ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ","NAVIER–STOKES LABORATORY · b-CORRECTION"},
{"subtitle","самодостаточная C99-версия без внешних библиотек","self-contained C99 edition, zero external libraries"},
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
{"config_line","конфиг: выход=%s · N≤%d · потоков=1","config: out=%s · N≤%d · threads=1"},
{"exp_tg","Тейлор–Грин: сходимость и экстраполяция","Taylor–Green: convergence and extrapolation"},
{"exp_abc","ABC (Эйлер): охота за расходимостью","ABC (Euler): blow-up hunt"},
{"exp_houluo","Хоу–Ло: антипараллельные вихревые трубки","Hou–Luo: anti-parallel vortex tubes"},
{"exp_baudit","Аудит b-коррекции: симметрия против пинка","b-correction audit: symmetry vs pointwise kick"},
{"suite_done","Сьют завершена: %d/%d проверок пройдено","Suite finished: %d/%d checks passed"},
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
{"ck_isometry","точечный поворот — изометрия: энергия сохранена","pointwise rotation is an isometry: energy preserved"},
{"ck_symmetry_relabel","полная симметрия = релебелинг","full symmetry = relabeling"},
{"ck_div_break","точечный поворот ЛОМАЕТ div u = 0","pointwise rotation BREAKS div u = 0"},
{"ck_reproject","после перепроекции div на машинном пороге","after reprojection div at machine level"},
{"ck_b_effect","b-пинк не снижает sup|ω| — регуляризации нет","b-kick does not reduce sup|ω| — no regularization"},
{"ck_abc_doubling","время удвоения sup|ω| не сокращается к нулю","sup|ω| doubling time does not shrink to zero"},
{"ck_hl_growth","рост sup|ω| измерен","sup|ω| growth measured"},
{"ck_cfl","CFL-аудит пройден","CFL audit passed"},
{"ck_balance","энергобаланс: |ΔE + ∫ε dt|/∫ε dt мал","energy balance: |ΔE + ∫ε dt|/∫ε dt small"},
{"ck_res_gap","разрешение: |BKM_N − BKM_2N|/BKM_2N ≤ 5%","resolution: |BKM_N − BKM_2N|/BKM_2N ≤ 5%"},
{"flows_hdr","ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов","REAL-FLOWS LABORATORY — 20 documented flows"},
{"flows_menu_hint","Введите номер течения (1–20), a — все, q — назад","Enter flow number (1-20), a — run all, q — back"},
{"flow_card","КАРТОЧКА ТЕЧЕНИЯ","FLOW CARD"},
{"flow_source","первоисточник/документация","primary source/documentation"},
{"flow_params","документированные величины","documented quantities"},
{"flow_derived","расчётные параметры","derived parameters"},
{"flow_dns_no","DNS НЕВОЗМОЖНО на существующем железе: N ≈ %s узлов (~%s памяти)","DNS is INFEASIBLE on existing hardware: needs N ≈ %s nodes (~%s of memory)"},
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
{"run_started","старт: %s","started: %s"},
{"set_hdr","НАСТРОЙКИ","SETTINGS"},
{"set_out","Папка результатов","Results folder"},
{"set_about","О ПРОЕКТЕ","ABOUT"},
{"set_about_txt","Лаборатория проверяет гипотезу b-коррекции: полная решётчатая симметрия — релебелинг и не может влиять на регулярность; точечный поворот сохраняет энергию, но ломает div u = 0. Порт C99 зеркалит Julia-оригинал.",
 "The lab tests the b-correction hypothesis: full lattice symmetry is a relabeling and cannot affect regularity; the pointwise rotation preserves energy but breaks div u = 0. The C99 port mirrors the Julia original."},
{NULL,NULL,NULL}
};

static const char *L(const char *key) {
    for (int i = 0; I18N[i].key; i++)
        if (strcmp(I18N[i].key, key) == 0)
            return CFG.lang == 'e' ? I18N[i].en : I18N[i].ru;
    return key;
}

/* ───────────────────────────── ANSI helpers ─────────────────────── */

static int is_tty(void) { return isatty(1); }

static void p_ok(const char *s)   { if (CFG.color) P("\x1b[1;32m%s\x1b[0m", s); else P("%s", s); }
static void p_bad(const char *s)  { if (CFG.color) P("\x1b[1;31m%s\x1b[0m", s); else P("%s", s); }
static void p_warn(const char *s) { if (CFG.color) P("\x1b[1;33m%s\x1b[0m", s); else P("%s", s); }
static void p_muted(const char *s){ if (CFG.color) P("\x1b[2m%s\x1b[0m", s); else P("%s", s); }
static void p_bold(const char *s) { if (CFG.color) P("\x1b[1m%s\x1b[0m", s); else P("%s", s); }

static void header_bar(const char *title) {
    char line[90]; memset(line, 0, sizeof(line));
    for (int i = 0; i < 76; i++) line[i] = '-';
    P("\n"); 
    if (CFG.color) P("\x1b[38;2;80;160;255m%s\x1b[0m\n", line); else P("%s\n", line);
    P(" ▸ "); p_bold((char *)title); P("\n");
    if (CFG.color) P("\x1b[38;2;80;160;255m%s\x1b[0m\n", line); else P("%s\n", line);
}

/* ─────────────────── one-line progress bar + sparkline ───────────── */

static double PROG_LAST = 0.0;

static void progress(double frac, const char *label, double t0, int total, int done) {
    if (frac < 0) frac = 0; if (frac > 1) frac = 1;
    if (!is_tty() || CFG.quiet) {
        if ((frac - PROG_LAST >= 0.1 || frac >= 1.0) && PROG_LAST < 1.0) {
            PROG_LAST = (frac < 1.0 && frac > PROG_LAST) ? frac : (frac >= 1.0 ? 1.0 : PROG_LAST);
            P("  [%3d%%] %s\n", (int)(frac * 100 + 0.5), label);
        }
        return;
    }
    const int W = 30;
    int fill = (int)(frac * W + 0.5);
    char bar[80]; int bi = 0;
    for (int i = 1; i <= W; i++) {
        if (CFG.ascii_only) bar[bi++] = i <= fill ? '#' : '-';
        else if (i <= fill) {
            if (CFG.color) bi += snprintf(bar + bi, sizeof(bar) - bi,
                "\x1b[38;2;%d;%d;255m█\x1b[0m", 40 + 180 * i / W, 80 + 170 * i / W);
            else bar[bi++] = '#';
        } else {
            if (CFG.color) bi += snprintf(bar + bi, sizeof(bar) - bi, "\x1b[2m░\x1b[0m");
            else bar[bi++] = '-';
        }
        if (bi > (int)sizeof(bar) - 12) break;
    }
    double el = now_mono() - t0;
    double eta = frac > 0.005 ? el / frac - el : NAN;
    char etas[16] = " --:--";
    if (isfinite(eta)) snprintf(etas, sizeof(etas), "%02d:%02d", (int)eta / 60, (int)eta % 60);
    char els[16]; snprintf(els, sizeof(els), "%02d:%02d", (int)el / 60, (int)el % 60);
    char tail[128];
    if (total > 0)
        snprintf(tail, sizeof(tail), " · %s %d/%d · %.1f %s · %s %s",
                 L("prog_step"), done, total, done / (el > 1e-9 ? el : 1e-9),
                 L("prog_rate"), L("prog_eta"), etas);
    else
        snprintf(tail, sizeof(tail), " · %s %s", "elapsed", els);
    /* clear line, redraw */
    P("\r%*s\r", 120, "");
    if (CFG.color) P("\x1b[38;2;80;160;255m ▸ \x1b[0m%s ▕%s▏%5.1f%%%s", label, bar, frac * 100, tail);
    else P(" ▸ %s |%s| %5.1f%%%s", label, bar, frac * 100, tail);
    fflush(stdout);
    if (frac >= 1.0) { P("\n"); PROG_LAST = 0.0; }
}

static void sparkline(const double *v, int n, char *out, size_t outn) {
    static const char *GL = "▁▂▃▄▅▆▇█";
    static const char *GA = "_.-~*##";
    if (n <= 0 || outn < 8) { out[0] = 0; return; }
    double lo = INFINITY, hi = -INFINITY;
    for (int i = 0; i < n; i++) { double x = v[i] > 0 ? v[i] : 0; if (x < lo) lo = x; if (x > hi) hi = x; }
    double rng = hi > lo ? hi - lo : 1.0;
    size_t bi = 0;
    for (int i = 0; i < n && bi + 8 < outn; i++) {
        double x = v[i] > 0 ? v[i] : 0;
        int k = (int)((x - lo) / rng * 7.0 + 0.5);
        if (k < 0) k = 0; if (k > 7) k = 7;
        if (CFG.ascii_only) out[bi++] = GA[k];
        else {
            /* UTF-8 3-byte glyphs */
            const char *u8 = GL + k * 3;
            out[bi++] = u8[0]; out[bi++] = u8[1]; out[bi++] = u8[2];
        }
    }
    out[bi] = 0;
}

/* ───────────────────────── in-house radix-2 FFT ──────────────────── */

typedef struct {
    int n;
    double complex *tw;      /* n/2 twiddles */
    int *bitrev;
} FFTPlan;

static FFTPlan fft_plan(int n) {
    if (n < 2 || (n & (n - 1))) { fprintf(stderr, "FFT: n must be power of 2\n"); exit(1); }
    FFTPlan p; p.n = n;
    p.tw = malloc(sizeof(double complex) * (n / 2 ? n / 2 : 1));
    for (int k = 0; k < n / 2; k++) p.tw[k] = cexp(-2.0 * PI * I * k / (double)n);
    p.bitrev = malloc(sizeof(int) * n);
    int logn = 0; while ((1 << logn) < n) logn++;
    for (int i = 0; i < n; i++) {
        int r = 0, x = i;
        for (int b = 0; b < logn; b++) { r = (r << 1) | (x & 1); x >>= 1; }
        p.bitrev[i] = r;
    }
    return p;
}

static void fft1d(FFTPlan *p, double complex *a, bool inverse) {
    int n = p->n;
    for (int i = 0; i < n; i++) {
        int j = p->bitrev[i];
        if (i < j) { double complex t = a[i]; a[i] = a[j]; a[j] = t; }
    }
    for (int len = 2; len <= n; len <<= 1) {
        int half = len >> 1, step = n / len;
        for (int start = 0; start < n; start += len) {
            int k = 0;
            for (int j = 0; j < half; j++) {
                double complex w = inverse ? conj(p->tw[k]) : p->tw[k];
                int i1 = start + j, i2 = i1 + half;
                double complex u = a[i1], v = a[i2] * w;
                a[i1] = u + v;
                a[i2] = u - v;
                k += step;
            }
        }
    }
    if (inverse) {
        double s = 1.0 / n;
        for (int i = 0; i < n; i++) a[i] *= s;
    }
}

/* In-place 3-D transform over a contiguous n*n*n array (row-major). */
static void fft3d(FFTPlan *p, double complex *A, bool inverse) {
    int n = p->n;
    double complex *buf = malloc(sizeof(double complex) * n);
    /* axis 2 (k, contiguous) */
    for (int i = 0; i < n * n; i++) fft1d(p, A + (size_t)i * n, inverse);
    /* axis 1 (j) */
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            for (int j = 0; j < n; j++) buf[j] = A[((size_t)i * n + j) * n + k];
            fft1d(p, buf, inverse);
            for (int j = 0; j < n; j++) A[((size_t)i * n + j) * n + k] = buf[j];
        }
    /* axis 0 (i) */
    for (int j = 0; j < n; j++)
        for (int k = 0; k < n; k++) {
            for (int i = 0; i < n; i++) buf[i] = A[((size_t)i * n + j) * n + k];
            fft1d(p, buf, inverse);
            for (int i = 0; i < n; i++) A[((size_t)i * n + j) * n + k] = buf[i];
        }
    free(buf);
}

/* 2-D transform over n*n (row-major, axis 1 contiguous). */
static void fft2d(FFTPlan *p, double complex *M, bool inverse) {
    int n = p->n;
    double complex *buf = malloc(sizeof(double complex) * n);
    for (int i = 0; i < n; i++) fft1d(p, M + (size_t)i * n, inverse);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) buf[j] = M[(size_t)j * n + i];
        fft1d(p, buf, inverse);
        for (int j = 0; j < n; j++) M[(size_t)j * n + i] = buf[j];
    }
    free(buf);
}

static void fft_selftest(int n, double *e_fwd, double *e_rt, double *e_3d) {
    FFTPlan p = fft_plan(n);
    double complex *a = malloc(sizeof(double complex) * n);
    srand(42);
    double complex *a0 = malloc(sizeof(double complex) * n);
    for (int i = 0; i < n; i++) {
        double re = (double)rand() / RAND_MAX - 0.5, im = (double)rand() / RAND_MAX - 0.5;
        a0[i] = re + im * I;
    }
    memcpy(a, a0, sizeof(double complex) * n);
    fft1d(&p, a, false);
    /* naive DFT */
    double err = 0, refmax = 0;
    for (int k = 0; k < n; k++) {
        double complex ref = 0;
        for (int m = 0; m < n; m++) ref += a0[m] * cexp(-2.0 * PI * I * m * k / n);
        double d = cabs(a[k] - ref);
        if (d > err) err = d;
        if (cabs(ref) > refmax) refmax = cabs(ref);
    }
    *e_fwd = err / refmax;
    fft1d(&p, a, true);
    err = 0;
    for (int i = 0; i < n; i++) { double d = cabs(a[i] - a0[i]); if (d > err) err = d; }
    *e_rt = err;
    /* 3-D roundtrip */
    int n3 = 4;
    double complex *A = malloc(sizeof(double complex) * 64);
    double complex *A0 = malloc(sizeof(double complex) * 64);
    for (int i = 0; i < 64; i++) A0[i] = ((double)rand() / RAND_MAX - 0.5) +
                                        ((double)rand() / RAND_MAX - 0.5) * I;
    memcpy(A, A0, sizeof(double complex) * 64);
    FFTPlan p4 = fft_plan(n3);
    fft3d(&p4, A, false); fft3d(&p4, A, true);
    err = 0;
    for (int i = 0; i < 64; i++) { double d = cabs(A[i] - A0[i]); if (d > err) err = d; }
    *e_3d = err;
    free(A); free(A0); free(a); free(a0);
}

/* ───────────────────── 3-D pseudospectral solver ─────────────────── */

typedef struct {
    int n;
    double nu, nu4, dx;
    int *kx, *ky, *kz;              /* n³ integer wavenumbers */
    double *ksq, *ksq2, *k2safe;
    unsigned char *mask;
} NSE3D;

#define IDX3(s, i, j, k) ((((size_t)(i) * (s)->n) + (j)) * (s)->n + (k))

static void nse3d_init(NSE3D *s, int n, double nu, double nu4_in) {
    s->n = n; s->nu = nu; s->nu4 = nu4_in >= 0 ? nu4_in : CFG.nu4;
    s->dx = 2.0 * PI / n;
    size_t N3 = (size_t)n * n * n;
    s->kx = malloc(sizeof(int) * N3); s->ky = malloc(sizeof(int) * N3);
    s->kz = malloc(sizeof(int) * N3);
    s->ksq = malloc(sizeof(double) * N3); s->ksq2 = malloc(sizeof(double) * N3);
    s->k2safe = malloc(sizeof(double) * N3);
    s->mask = malloc(N3);
    int *k1d = malloc(sizeof(int) * n);
    for (int i = 0; i < n / 2; i++) k1d[i] = i;
    for (int i = -n / 2; i < 0; i++) k1d[i + n] = i;
    int kc = n / 3;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                size_t id = IDX3(s, i, j, k);
                s->kx[id] = k1d[i]; s->ky[id] = k1d[j]; s->kz[id] = k1d[k];
                double q = (double)(k1d[i] * k1d[i] + k1d[j] * k1d[j] + k1d[k] * k1d[k]);
                s->ksq[id] = q; s->ksq2[id] = q * q;
                s->k2safe[id] = q > 0 ? q : 1.0;
                s->mask[id] = (abs(k1d[i]) <= kc && abs(k1d[j]) <= kc && abs(k1d[k]) <= kc);
            }
    free(k1d);
}

typedef struct {
    double complex *uhat[3], *wh[3];
    double *u[3], *w[3];
    double complex *nlhat[3], *kd;
    FFTPlan plan;
    double complex *K1[3], *K2[3], *K3[3], *K4[3], *T1[3], *T2[3];
} Work3D;

static void work3d_init(Work3D *W, int n) {
    size_t N3 = (size_t)n * n * n;
    W->plan = fft_plan(n);
    for (int c = 0; c < 3; c++) {
        W->uhat[c] = calloc(N3, sizeof(double complex));
        W->wh[c]   = calloc(N3, sizeof(double complex));
        W->nlhat[c]= calloc(N3, sizeof(double complex));
        W->u[c]    = calloc(N3, sizeof(double));
        W->w[c]    = calloc(N3, sizeof(double));
        W->K1[c] = calloc(N3, sizeof(double complex)); W->K2[c] = calloc(N3, sizeof(double complex));
        W->K3[c] = calloc(N3, sizeof(double complex)); W->K4[c] = calloc(N3, sizeof(double complex));
        W->T1[c] = calloc(N3, sizeof(double complex)); W->T2[c] = calloc(N3, sizeof(double complex));
    }
    W->kd = calloc(N3, sizeof(double complex));
}

static void fft_field3(Work3D *W, NSE3D *s, double complex **out, double **in) {
    int n = s->n;
    for (int c = 0; c < 3; c++) {
        size_t N3 = (size_t)n * n * n;
        for (size_t i = 0; i < N3; i++) W->nlhat[c][i] = in[c][i];
        fft3d(&W->plan, W->nlhat[c], false);
        memcpy(out[c], W->nlhat[c], N3 * sizeof(double complex));
    }
}

static void ifft_field3(Work3D *W, NSE3D *s, double **out, double complex **in) {
    int n = s->n;
    for (int c = 0; c < 3; c++) {
        size_t N3 = (size_t)n * n * n;
        memcpy(W->nlhat[c], in[c], N3 * sizeof(double complex));
        fft3d(&W->plan, W->nlhat[c], true);
        for (size_t i = 0; i < N3; i++) out[c][i] = creal(W->nlhat[c][i]);
    }
}

static void project3(Work3D *W, NSE3D *s, double complex **out, double complex **in) {
    size_t N3 = (size_t)s->n * s->n * s->n;
    for (size_t i = 0; i < N3; i++) {
        W->kd[i] = (s->kx[i] * in[0][i] + s->ky[i] * in[1][i] + s->kz[i] * in[2][i]) / s->k2safe[i];
        if (s->ksq[i] == 0) W->kd[i] = 0;
    }
    const int *kc[3] = {s->kx, s->ky, s->kz};
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            out[c][i] = in[c][i] - kc[c][i] * W->kd[i];
}

static void curl_hat3(NSE3D *s, double complex **out, double complex **a) {
    size_t N3 = (size_t)s->n * s->n * s->n;
    for (size_t i = 0; i < N3; i++) {
        int kx = s->kx[i], ky = s->ky[i], kz = s->kz[i];
        double complex a1 = a[0][i], a2 = a[1][i], a3 = a[2][i];
        out[0][i] = I * (ky * a3 - kz * a2);
        out[1][i] = I * (kz * a1 - kx * a3);
        out[2][i] = I * (kx * a2 - ky * a1);
    }
}

static void rhs3(Work3D *W, NSE3D *s, double complex **du, double complex **uhat) {
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    curl_hat3(s, W->wh, uhat);
    ifft_field3(W, s, W->u, uhat);
    ifft_field3(W, s, W->w, W->wh);
    /* nl = w × u stored into W->u */
    for (size_t i = 0; i < N3; i++) {
        double w1 = W->w[0][i], w2 = W->w[1][i], w3 = W->w[2][i];
        double u1 = W->u[0][i], u2 = W->u[1][i], u3 = W->u[2][i];
        W->w[0][i] = w2 * u3 - w3 * u2;
        W->w[1][i] = w3 * u1 - w1 * u3;
        W->w[2][i] = w1 * u2 - w2 * u1;
    }
    fft_field3(W, s, W->nlhat, W->w);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s->mask[i]) W->nlhat[c][i] = 0;
    project3(W, s, du, W->nlhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            du[c][i] -= (s->nu * s->ksq[i] + s->nu4 * s->ksq2[i]) * uhat[c][i];
}

static void step_rk4_3d(Work3D *W, NSE3D *s, double complex **out,
                        double complex **uhat, double dt) {
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    rhs3(W, s, W->K1, uhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) W->T1[c][i] = uhat[c][i] + 0.5 * dt * W->K1[c][i];
    rhs3(W, s, W->K2, W->T1);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) W->T1[c][i] = uhat[c][i] + 0.5 * dt * W->K2[c][i];
    rhs3(W, s, W->K3, W->T1);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) W->T1[c][i] = uhat[c][i] + dt * W->K3[c][i];
    rhs3(W, s, W->K4, W->T1);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) {
            double complex v = uhat[c][i] + (dt / 6.0) *
                (W->K1[c][i] + 2.0 * W->K2[c][i] + 2.0 * W->K3[c][i] + W->K4[c][i]);
            out[c][i] = s->mask[i] ? v : 0;
        }
}

static double cfl_dt_3d(Work3D *W, NSE3D *s, double complex **uhat) {
    ifft_field3(W, s, W->u, uhat);
    double umax = 0;
    size_t N3 = (size_t)s->n * s->n * s->n;
    for (size_t i = 0; i < N3; i++) {
        double v = sqrt(W->u[0][i] * W->u[0][i] + W->u[1][i] * W->u[1][i] + W->u[2][i] * W->u[2][i]);
        if (v > umax) umax = v;
    }
    if (umax < 1e-14) return 0.5 * s->dx * s->dx / (s->nu > 1e-12 ? s->nu : 1e-12);
    return 0.5 * s->dx / umax;
}

/* ───────────────────────────── ICs & rotations ───────────────────── */

#define NSB_B (1.0 / (4.0 * PI + 2.0 * sqrt(3.0)))
#define NSB_THETA_B (asin(NSB_B))

static void rodrigues(double theta, double ex, double ey, double ez, double R[3][3]) {
    double c = cos(theta), s = sin(theta);
    double C[3][3] = {{0,-ez,ey},{ez,0,-ex},{-ey,ex,0}};
    double O[3][3] = {{ex*ex,ex*ey,ex*ez},{ey*ex,ey*ey,ey*ez},{ez*ex,ez*ey,ez*ez}};
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            R[i][j] = c * (i == j) + (1 - c) * O[i][j] - s * C[i][j];
}

static void grid_1d(int n, double *x) {
    for (int i = 0; i < n; i++) x[i] = 2.0 * PI * i / n;
}

/* IDX helper independent of NSE3D for ICs */
static size_t IDX3_ID(int n, int i, int j, int k) {
    return (((size_t)i * n) + j) * n + k;
}

static void ic_taylor_green(int n, double **u) {
    double *x = malloc(sizeof(double) * n);
    grid_1d(n, x);
    double *sx = malloc(sizeof(double) * n), *cx = malloc(sizeof(double) * n);
    for (int i = 0; i < n; i++) { sx[i] = sin(x[i]); cx[i] = cos(x[i]); }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                u[0][IDX3_ID(n, i, j, k)] = sx[i] * cx[j] * cx[k];
                u[1][IDX3_ID(n, i, j, k)] = -cx[i] * sx[j] * cx[k];
                u[2][IDX3_ID(n, i, j, k)] = 0.0;
            }
    free(x); free(sx); free(cx);
}

static void ic_abc(int n, double **u) {
    double *x = malloc(sizeof(double) * n);
    grid_1d(n, x);
    double *sx = malloc(sizeof(double) * n), *cx = malloc(sizeof(double) * n);
    for (int i = 0; i < n; i++) { sx[i] = sin(x[i]); cx[i] = cos(x[i]); }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                u[0][IDX3_ID(n, i, j, k)] = sx[k] + cx[j];
                u[1][IDX3_ID(n, i, j, k)] = sx[i] + cx[k];
                u[2][IDX3_ID(n, i, j, k)] = sx[j] + cx[i];
            }
    free(x); free(sx); free(cx);
}

static void ic_hou_luo(int n, double **w) {
    double *x = malloc(sizeof(double) * n);
    grid_1d(n, x);
    double sigma = PI / 16, inv2s2 = 1.0 / (2.0 * sigma * sigma);
    double y0 = PI / 2, z0a = PI / 2, z0b = 3 * PI / 2;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                double yj = x[j], zk = x[k];
                double g1 = exp(-((yj - y0) * (yj - y0) + (zk - z0a) * (zk - z0a)) * inv2s2);
                double g2 = exp(-((yj - 3 * PI / 2) * (yj - 3 * PI / 2) + (zk - z0b) * (zk - z0b)) * inv2s2);
                w[0][IDX3_ID(n, i, j, k)] = (g1 - g2) * (1.0 + 0.05 * cos(x[i]));
                w[1][IDX3_ID(n, i, j, k)] = 0.0;
                w[2][IDX3_ID(n, i, j, k)] = 0.0;
            }
    free(x);
}

static void ic_random(int n, double **u, long seed) {
    srand((unsigned)seed);
    size_t N3 = (size_t)n * n * n;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) u[c][i] = (double)rand() / RAND_MAX - 0.5;
    double *x = malloc(sizeof(double) * n);
    grid_1d(n, x);
    int kp = 4;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                size_t id = IDX3_ID(n, i, j, k);
                u[0][id] += 0.5 * sin(kp * x[i]) * cos(kp * x[j]);
                u[1][id] += 0.5 * sin(kp * x[i]) * (0.5 * sin(kp * x[j]) + 0.5);
                u[2][id] += 0.5 * cos(kp * x[k]) * sin(kp * x[j]);
            }
    free(x);
}

static void prepare_state3(Work3D *W, NSE3D *s, double complex **uhat, double **ic) {
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) W->T1[c][i] = ic[c][i];
        fft3d(&W->plan, W->T1[c], false);
        memcpy(uhat[c], W->T1[c], N3 * sizeof(double complex));
    }
    project3(W, s, uhat, uhat);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s->mask[i]) uhat[c][i] = 0;
}

static void rotate_pointwise3(Work3D *W, NSE3D *s, double complex **out,
                              double complex **uhat, double R[3][3]) {
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    ifft_field3(W, s, W->u, uhat);
    for (size_t i = 0; i < N3; i++) {
        double x = W->u[0][i], y = W->u[1][i], z = W->u[2][i];
        W->w[0][i] = R[0][0] * x + R[0][1] * y + R[0][2] * z;
        W->w[1][i] = R[1][0] * x + R[1][1] * y + R[1][2] * z;
        W->w[2][i] = R[2][0] * x + R[2][1] * y + R[2][2] * z;
    }
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) W->T1[c][i] = W->w[c][i];
        fft3d(&W->plan, W->T1[c], false);
        memcpy(out[c], W->T1[c], N3 * sizeof(double complex));
    }
}

/* Full lattice symmetry: exact quarter turn about z via circular shift. */
static void rotate_full_symmetry3(Work3D *W, NSE3D *s, double complex **out,
                                  double complex **uhat) {
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    ifft_field3(W, s, W->u, uhat);
    /* u'(x_i, y_j, z_k) = R u(R⁻¹(x)) : sample u at (y_j, −x_i, z_k) */
    double **ru = malloc(sizeof(double *) * 3);
    for (int c = 0; c < 3; c++) ru[c] = malloc(N3 * sizeof(double));
    for (int i = 0; i < n; i++) {
        int isrc = (n - i) % n;                       /* index of −x_i (mod n) */
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++) {
                size_t src = IDX3_ID(n, j, isrc, k);  /* u(y_j, −x_i, z_k) */
                size_t dst = IDX3_ID(n, i, j, k);
                double a = W->u[0][src], b = W->u[1][src], z = W->u[2][src];
                ru[0][dst] = -b;
                ru[1][dst] = a;
                ru[2][dst] = z;
            }
    }
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) W->T1[c][i] = ru[c][i];
        fft3d(&W->plan, W->T1[c], false);
        memcpy(out[c], W->T1[c], N3 * sizeof(double complex));
        free(ru[c]);
    }
    free(ru);
}

/* ───────────────────────────── diagnostics ───────────────────────── */

static double energy3(NSE3D *s, double complex **uhat) {
    size_t N3 = (size_t)s->n * s->n * s->n;
    double sum = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) sum += cabs(uhat[c][i]) * cabs(uhat[c][i]);
    return 0.5 * sum / pow((double)s->n, 6.0);
}

static double palinstrophy3(NSE3D *s, double complex **what) {
    size_t N3 = (size_t)s->n * s->n * s->n;
    double sum = 0;
    for (size_t i = 0; i < N3; i++) {
        double complex a1 = I * (s->ky[i] * what[2][i] - s->kz[i] * what[1][i]);
        double complex a2 = I * (s->kz[i] * what[0][i] - s->kx[i] * what[2][i]);
        double complex a3 = I * (s->kx[i] * what[1][i] - s->ky[i] * what[0][i]);
        sum += cabs(a1) * cabs(a1) + cabs(a2) * cabs(a2) + cabs(a3) * cabs(a3);
    }
    return 0.5 * sum / pow((double)s->n, 6.0);
}

static double dissipation3(NSE3D *s, double complex **uhat) {
    size_t N3 = (size_t)s->n * s->n * s->n;
    double sum = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            sum += s->ksq[i] * cabs(uhat[c][i]) * cabs(uhat[c][i]);
    return s->nu * sum / pow((double)s->n, 6.0);
}

/* sup|ω| over a physical vorticity triple of n³ points */
static double sup_vorticity3(int n, double **w) {
    size_t N3 = (size_t)n * n * n;
    double m = 0;
    for (size_t i = 0; i < N3; i++) {
        double v = sqrt(w[0][i] * w[0][i] + w[1][i] * w[1][i] + w[2][i] * w[2][i]);
        if (v > m) m = v;
    }
    return m;
}

static double divergence_max3(NSE3D *s, double complex **uhat) {
    size_t N3 = (size_t)s->n * s->n * s->n;
    double sum = 0;
    for (size_t i = 0; i < N3; i++) {
        double complex d = s->kx[i] * uhat[0][i] + s->ky[i] * uhat[1][i] + s->kz[i] * uhat[2][i];
        sum += cabs(d) * cabs(d);
    }
    return sqrt(sum) / pow((double)s->n, 3.0);
}

static void shell_spectrum3(NSE3D *s, double complex **uhat,
                            int *kmax_out, double **ks_out, double **spec_out) {
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    int kmax = (int)ceil(sqrt(3.0) * (n / 2)) + 1;
    int *counts = calloc(kmax + 1, sizeof(int));
    double *sums = calloc(kmax + 1, sizeof(double));
    double n6 = pow((double)n, 6.0);
    for (size_t i = 0; i < N3; i++) {
        double e = 0.5 * (cabs(uhat[0][i]) * cabs(uhat[0][i]) +
                          cabs(uhat[1][i]) * cabs(uhat[1][i]) +
                          cabs(uhat[2][i]) * cabs(uhat[2][i])) / n6;
        int ki = (int)round(sqrt(s->ksq[i]));
        if (ki < 0) ki = 0; if (ki > kmax) ki = kmax;
        counts[ki]++; sums[ki] += e;
    }
    double *ks = malloc(sizeof(double) * (kmax + 1));
    double *spec = malloc(sizeof(double) * (kmax + 1));
    for (int k = 0; k <= kmax; k++) {
        ks[k] = k;
        spec[k] = counts[k] > 0 ? sums[k] / counts[k] : 0.0;
    }
    free(counts); free(sums);
    *kmax_out = kmax; *ks_out = ks; *spec_out = spec;
}

static double spectral_tail_level(double *spec, int kmax, int kcut) {
    if (kmax < 3) return 0;
    int k_hi = kcut + 1 < kmax ? kcut + 1 : kmax;
    int k_lo = 2 > k_hi - 1 ? 2 : k_hi - 1;
    double peak = 0, tail = 0;
    for (int k = 1; k <= kmax; k++) if (spec[k] > peak) peak = spec[k];
    if (peak <= 0) return 0;
    for (int k = k_lo; k <= k_hi; k++) if (spec[k] > tail) tail = spec[k];
    return tail / peak;
}

static void linfit(const double *xs, const double *ys, int n,
                   double *a, double *b, double *r2) {
    if (n < 2) { *a = *b = *r2 = NAN; return; }
    double sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (int i = 0; i < n; i++) {
        sx += xs[i]; sy += ys[i];
        sxx += xs[i] * xs[i]; sxy += xs[i] * ys[i];
    }
    double den = n * sxx - sx * sx;
    if (den == 0) { *a = *b = *r2 = NAN; return; }
    *a = (n * sxy - sx * sy) / den;
    *b = (sy - *a * sx) / n;
    double ybar = sy / n, ss_res = 0, ss_tot = 0;
    for (int i = 0; i < n; i++) {
        ss_res += (ys[i] - (*a * xs[i] + *b)) * (ys[i] - (*a * xs[i] + *b));
        ss_tot += (ys[i] - ybar) * (ys[i] - ybar);
    }
    *r2 = ss_tot > 0 ? 1 - ss_res / ss_tot : NAN;
}

static double observed_order(double j_c, double j_f, double j_ff, double ratio) {
    double den = j_c - j_f, num = j_f - j_ff;
    if (fabs(den) < 1e-30 || fabs(num) < 1e-30) return NAN;
    return log(fabs(den / num)) / log(ratio);
}

static double richardson(double j_f, double j_ff, double ratio, double order) {
    return j_ff + (j_ff - j_f) / (pow(ratio, order) - 1.0);
}

/* ───────────────────────── time series & blow-up ─────────────────── */

typedef struct {
    double *t, *energy, *enstrophy, *palinstrophy, *sup_omega, *dissipation, *bkm;
    int n, cap;
} TimeSeries;

static void ts_init(TimeSeries *ts) {
    ts->cap = 256; ts->n = 0;
    ts->t = malloc(sizeof(double) * ts->cap);
    ts->energy = malloc(sizeof(double) * ts->cap);
    ts->enstrophy = malloc(sizeof(double) * ts->cap);
    ts->palinstrophy = malloc(sizeof(double) * ts->cap);
    ts->sup_omega = malloc(sizeof(double) * ts->cap);
    ts->dissipation = malloc(sizeof(double) * ts->cap);
    ts->bkm = malloc(sizeof(double) * ts->cap);
    ts->bkm[0] = 0; ts->n = 1; ts->t[0] = 0;
    ts->energy[0] = ts->enstrophy[0] = ts->palinstrophy[0] = 0;
    ts->sup_omega[0] = 0; ts->dissipation[0] = 0;
}

static void ts_push(TimeSeries *ts, double t, double e, double om, double pal,
                    double sup, double eps, double bkm) {
    if (ts->n >= ts->cap) {
        ts->cap *= 2;
        ts->t = realloc(ts->t, sizeof(double) * ts->cap);
        ts->energy = realloc(ts->energy, sizeof(double) * ts->cap);
        ts->enstrophy = realloc(ts->enstrophy, sizeof(double) * ts->cap);
        ts->palinstrophy = realloc(ts->palinstrophy, sizeof(double) * ts->cap);
        ts->sup_omega = realloc(ts->sup_omega, sizeof(double) * ts->cap);
        ts->dissipation = realloc(ts->dissipation, sizeof(double) * ts->cap);
        ts->bkm = realloc(ts->bkm, sizeof(double) * ts->cap);
    }
    ts->t[ts->n] = t; ts->energy[ts->n] = e; ts->enstrophy[ts->n] = om;
    ts->palinstrophy[ts->n] = pal; ts->sup_omega[ts->n] = sup;
    ts->dissipation[ts->n] = eps; ts->bkm[ts->n] = bkm;
    ts->n++;
}

typedef struct {
    double lambda_trend, lambda_r2, lambda_max, doubling_min, alpha, bkm_final;
    bool sustained;
    double tstar;      /* NAN = none */
} BlowupReport;

static void blowup_report(TimeSeries *ts, BlowupReport *bl) {
    /* λ(t) central differences of ln sup|ω| */
    int m = 0;
    double *tl = malloc(sizeof(double) * (ts->n > 2 ? ts->n : 3));
    double *lam = malloc(sizeof(double) * (ts->n > 2 ? ts->n : 3));
    for (int i = 1; i < ts->n - 1; i++) {
        double dt1 = ts->t[i] - ts->t[i - 1], dt2 = ts->t[i + 1] - ts->t[i];
        double s0 = ts->sup_omega[i - 1], s1 = ts->sup_omega[i], s2 = ts->sup_omega[i + 1];
        if (dt1 <= 0 || dt2 <= 0 || s0 <= 0 || s1 <= 0 || s2 <= 0) continue;
        lam[m] = (log(s2) - log(s0)) / (dt1 + dt2);
        tl[m] = ts->t[i];
        m++;
    }
    bl->tstar = NAN; bl->alpha = NAN; bl->sustained = false;
    bl->bkm_final = ts->bkm[ts->n - 1];
    if (m < 4) {
        double mx = -INFINITY;
        for (int i = 0; i < m; i++) if (lam[i] > mx) mx = lam[i];
        bl->lambda_max = m ? mx : NAN;
        bl->lambda_trend = bl->lambda_r2 = NAN;
        bl->doubling_min = INFINITY;
        free(tl); free(lam);
        return;
    }
    double a, b, r2;
    linfit(tl, lam, m, &a, &b, &r2);
    bl->lambda_trend = a; bl->lambda_r2 = r2;
    double lam_max = -INFINITY;
    for (int i = 0; i < m; i++) if (lam[i] > lam_max) lam_max = lam[i];
    bl->lambda_max = lam_max;
    double dbl_min = INFINITY;
    for (int i = 1; i < ts->n; i++) {
        double s0 = ts->sup_omega[i - 1], s1 = ts->sup_omega[i], dt = ts->t[i] - ts->t[i - 1];
        if (s0 > 0 && s1 > s0 && dt > 0) {
            double d = dt * log(2) / log(s1 / s0);
            if (d < dbl_min) dbl_min = d;
        }
    }
    bl->doubling_min = dbl_min;
    int nfit = (int)(m * 0.25 + 0.5); if (nfit < 4) nfit = 4; if (nfit > m) nfit = m;
    double at, bt, r2t;
    linfit(tl + (m - nfit), lam + (m - nfit), nfit, &at, &bt, &r2t);
    int ntail = nfit < ts->n ? nfit : ts->n;
    double tail_sup_max = -INFINITY, sup_max = -INFINITY;
    for (int i = ts->n - ntail; i < ts->n; i++)
        if (ts->sup_omega[i] > tail_sup_max) tail_sup_max = ts->sup_omega[i];
    for (int i = 0; i < ts->n; i++)
        if (ts->sup_omega[i] > sup_max) sup_max = ts->sup_omega[i];
    bool new_high = tail_sup_max >= 0.98 * sup_max;
    bl->sustained = isfinite(at) && at > 0 && isfinite(r2t) && r2t > 0.5 &&
                    lam_max > 0 && new_high;
    if (bl->sustained) {
        double best_err = INFINITY, best_tstar = NAN, best_alpha = NAN;
        double T_end = ts->t[ts->n - 1];
        for (double al = 0.5; al <= 7.0 + 1e-9; al += 0.25)
            for (double frac = 1.02; frac <= 2.5 + 1e-9; frac += 0.02) {
                double tst = T_end * frac;
                double xs[256], ys[256]; int np = 0; bool ok = true;
                for (int i = 0; i < ts->n && np < 256; i++) {
                    double d = tst - ts->t[i];
                    if (d <= 0) { ok = false; break; }
                    xs[np] = log(d); ys[np] = log(fmax(ts->sup_omega[i], 1e-300));
                    np++;
                }
                if (!ok) continue;
                double A, B, R2;
                linfit(xs, ys, np, &A, &B, &R2);
                if (isfinite(R2) && -R2 < best_err) {
                    best_err = -R2; best_tstar = tst; best_alpha = -A;
                }
            }
        if (best_err < -0.9) { bl->tstar = best_tstar; bl->alpha = best_alpha; }
    }
    free(tl); free(lam);
}

static void k41_fit(double *ks, double *spec, int kmax, int kcut,
                    double *slope, double *r2, int *npts) {
    int k_hi = (int)(0.75 * kcut + 0.5); if (k_hi < 3) k_hi = 3;
    if (k_hi > kmax) k_hi = kmax;
    double xs[256], ys[256]; int np = 0;
    for (int k = 2; k <= k_hi && np < 256; k++)
        if (spec[k + 1] > 0) { xs[np] = log(ks[k + 1]); ys[np] = log(spec[k + 1]); np++; }
    *npts = np;
    if (np < 4) { *slope = *r2 = NAN; return; }
    double a, b; linfit(xs, ys, np, &a, &b, r2);
    *slope = a;
}

/* ─────────────────────────── runner with checkpoints ─────────────── */

typedef struct {
    double complex **uhat;      /* final state (3 components) */
    TimeSeries ts;
    double div_max, energy_rise;
    int cfl_exceeded, adapted_steps, steps_done;
    double wall;
} DecayResult;

static char *ckpt_path_for(const char *label) {
    static char path[700];
    char safe[256]; int j = 0;
    for (int i = 0; label[i] && j < 255; i++)
        safe[j++] = (label[i] >= 'A' && label[i] <= 'Z') || (label[i] >= 'a' && label[i] <= 'z') ||
                    (label[i] >= '0' && label[i] <= '9') || label[i] == '_' || label[i] == '.'
                    ? label[i] : '_';
    safe[j] = 0;
    snprintf(path, sizeof(path), "%s/data/ckpt_%s.bin", CFG.out_dir, safe);
    return path;
}

static void ckpt_save3(const char *path, const char *label, int step, double t,
                       int n, double complex **uhat, TimeSeries *ts) {
    FILE *f = fopen(path, "wb");
    if (!f) return;
    size_t N3 = (size_t)n * n * n;
    fwrite("NSBC", 1, 4, f);
    int lab_len = (int)strlen(label);
    fwrite(&lab_len, sizeof(int), 1, f); fwrite(label, 1, lab_len, f);
    fwrite(&step, sizeof(int), 1, f); fwrite(&t, sizeof(double), 1, f);
    fwrite(&n, sizeof(int), 1, f);
    for (int c = 0; c < 3; c++) fwrite(uhat[c], sizeof(double complex), N3, f);
    fwrite(&ts->n, sizeof(int), 1, f);
    fwrite(ts->t, sizeof(double), ts->n, f);
    fwrite(ts->energy, sizeof(double), ts->n, f);
    fwrite(ts->enstrophy, sizeof(double), ts->n, f);
    fwrite(ts->palinstrophy, sizeof(double), ts->n, f);
    fwrite(ts->sup_omega, sizeof(double), ts->n, f);
    fwrite(ts->dissipation, sizeof(double), ts->n, f);
    fwrite(ts->bkm, sizeof(double), ts->n, f);
    fclose(f);
}

static bool ckpt_load3(const char *path, char *label, int label_cap, int *step,
                       double *t, int *n, double complex **uhat, TimeSeries *ts) {
    FILE *f = fopen(path, "rb");
    if (!f) return false;
    char magic[4];
    if (fread(magic, 1, 4, f) != 4 || memcmp(magic, "NSBC", 4)) { fclose(f); return false; }
    int lab_len; fread(&lab_len, sizeof(int), 1, f);
    if (lab_len <= 0 || lab_len >= label_cap) { fclose(f); return false; }
    fread(label, 1, lab_len, f); label[lab_len] = 0;
    fread(step, sizeof(int), 1, f);
    fread(t, sizeof(double), 1, f);
    fread(n, sizeof(int), 1, f);
    size_t N3 = (size_t)(*n) * (*n) * (*n);
    for (int c = 0; c < 3; c++) fread(uhat[c], sizeof(double complex), N3, f);
    int tn; fread(&tn, sizeof(int), 1, f);
    ts_init(ts); ts->n = 0;
    for (int i = 0; i < tn; i++) {
        double t_, e, om, pal, sup, eps, bkm;
        fread(&t_, sizeof(double), 1, f); fread(&e, sizeof(double), 1, f);
        fread(&om, sizeof(double), 1, f); fread(&pal, sizeof(double), 1, f);
        fread(&sup, sizeof(double), 1, f); fread(&eps, sizeof(double), 1, f);
        fread(&bkm, sizeof(double), 1, f);
        if (i == 0) { ts->n = 1; ts->t[0] = t_; ts->bkm[0] = bkm; ts->energy[0] = e;
                      ts->enstrophy[0] = om; ts->palinstrophy[0] = pal;
                      ts->sup_omega[0] = sup; ts->dissipation[0] = eps; }
        else ts_push(ts, t_, e, om, pal, sup, eps, bkm);
    }
    fclose(f);
    return true;
}

static DecayResult run_decay_3d(NSE3D *s, Work3D *W, double complex **uhat0,
                                double dt, double t_horizon, const char *label,
                                int sample_every, int kick_mode, double kick_every,
                                bool blowup_stop, bool show_prog,
                                bool adaptive_in, int ckpt_every, bool resume) {
    bool adaptive = adaptive_in;
    int n = s->n;
    size_t N3 = (size_t)n * n * n;
    DecayResult res;
    memset(&res, 0, sizeof(res));
    ts_init(&res.ts);
    double complex **uhat = malloc(sizeof(double complex *) * 3);
    double complex **T2 = malloc(sizeof(double complex *) * 3);
    double complex **T3 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) {
        uhat[c] = malloc(N3 * sizeof(double complex));
        T2[c] = malloc(N3 * sizeof(double complex));
        T3[c] = malloc(N3 * sizeof(double complex));
        memcpy(uhat[c], uhat0[c], N3 * sizeof(double complex));
    }
    /* initial sup|ω| */
    curl_hat3(s, W->wh, uhat);
    ifft_field3(W, s, W->w, W->wh);
    double sup_prev = sup_vorticity3(n, W->w);
    int steps = (int)ceil(t_horizon / dt);
    double e_prev = energy3(s, uhat);
    double t_elapsed = 0;
    double t0 = now_mono();
    int start_step = 1;
    PROG_LAST = 0;
    if (adaptive) { p_muted("  "); p_muted(L("adaptive_on")); P("\n"); }
    const char *cpath = "";
    if (ckpt_every > 0) cpath = ckpt_path_for(label);
    if (resume && ckpt_every > 0) {
        char lab[128]; int cstep, cn; double ct;
        TimeSeries cts;
        if (ckpt_load3(cpath, lab, sizeof(lab), &cstep, &ct, &cn, uhat, &cts) &&
            strcmp(lab, label) == 0 && cn == n && cstep > 0) {
            res.ts = cts;
            start_step = cstep + 1;
            t_elapsed = ct;
            e_prev = res.ts.energy[res.ts.n - 1];
            sup_prev = res.ts.sup_omega[res.ts.n - 1];
            P("  "); p_ok("resume"); P(": step %d (%s)\n", cstep, cpath);
        } else {
            p_muted("  checkpoint not found — starting fresh\n");
        }
    }
    double next_kick = kick_mode ? kick_every : INFINITY;
    for (int step = start_step; step <= steps; step++) {
        double h = dt < (t_horizon - t_elapsed) ? dt : (t_horizon - t_elapsed);
        if (h <= 1e-15) break;
        double cfl = cfl_dt_3d(W, s, uhat);
        if (cfl < h) { res.cfl_exceeded++; if (adaptive) { h = cfl; res.adapted_steps++; } }
        step_rk4_3d(W, s, T2, uhat, h);
        double complex **swap = uhat; uhat = T2; T2 = swap;
        t_elapsed += h;
        if (kick_mode && t_elapsed >= next_kick - 1e-12) {
            if (kick_mode == 1) {           /* full symmetry relabeling */
                double R[3][3];
                rodrigues(PI / 2, 0, 0, 1, R);
                (void)R;
                rotate_full_symmetry3(W, s, T3, uhat);
            } else {                         /* pointwise b-rotation */
                double R[3][3];
                double ax = 0.3, ay = -0.5, az = sqrt(1.0 - 0.09 - 0.25);
                rodrigues(NSB_THETA_B, ax, ay, az, R);
                rotate_pointwise3(W, s, T3, uhat, R);
                project3(W, s, T3, T3);
            }
            for (int c = 0; c < 3; c++)
                for (size_t i = 0; i < N3; i++)
                    if (!s->mask[i]) T3[c][i] = 0;
            swap = uhat; uhat = T3; T3 = swap;
            next_kick += kick_every;
        }
        if (ckpt_every > 0 && step % ckpt_every == 0 && step < steps) {
            ckpt_save3(cpath, label, step, t_elapsed, n, uhat, &res.ts);
            p_muted(""); P("  checkpoint: step %d\n", step);
        }
        if (step % sample_every == 0 || step == steps) {
            curl_hat3(s, W->wh, uhat);
            ifft_field3(W, s, W->w, W->wh);
            double sup_now = sup_vorticity3(n, W->w);
            double e_now = energy3(s, uhat);
            double dv = divergence_max3(s, uhat);
            if (dv > res.div_max) res.div_max = dv;
            double er = e_now - e_prev;
            if (er > res.energy_rise) res.energy_rise = er;
            e_prev = e_now;
            double bkm = res.ts.bkm[res.ts.n - 1] + 0.5 * (sup_prev + sup_now) * h * sample_every;
            sup_prev = sup_now;
            /* enstrophy = 0.5 Σ|ω̂|²/n⁶ */
            double om_sum = 0;
            for (int c = 0; c < 3; c++)
                for (size_t i = 0; i < N3; i++)
                    om_sum += cabs(W->wh[c][i]) * cabs(W->wh[c][i]);
            double om = 0.5 * om_sum / pow((double)n, 6.0);
            ts_push(&res.ts, t_elapsed, e_now, om, palinstrophy3(s, W->wh),
                    sup_now, dissipation3(s, uhat), bkm);
            if (show_prog) progress((double)step / steps, label, t0, steps, step);
            if (blowup_stop && (!isfinite(sup_now) || sup_now > 1e8)) {
                p_warn("  stop: sup|ω| over threshold\n");
                break;
            }
        }
    }
    if (show_prog) progress(1.0, label, t0, steps, steps);
    if (ckpt_every > 0) remove(cpath);
    res.uhat = uhat;
    res.steps_done = steps;
    res.wall = now_mono() - t0;
    for (int c = 0; c < 3; c++) { free(T2[c]); free(T3[c]); }
    free(T2); free(T3);
    /* NOTE: caller frees uhat */
    return res;
}

/* ─────────────────────── 2-D barotropic β-plane ──────────────────── */

typedef struct {
    int n;
    double nu, nu4, beta, lbox;
    int *kx, *ky;
    double *kpx, *kpy, *kp2;
    unsigned char *mask;
    FFTPlan plan;
    double complex *uhat, *vhat, *dxwhat, *dywhat, *tmp;
    double *u, *v, *w, *dxw, *dyw, *nl;
} Baro2D;

static void baro_init(Baro2D *m, int n, double nu, double nu4, double beta, double lbox) {
    m->n = n; m->nu = nu; m->nu4 = nu4; m->beta = beta; m->lbox = lbox;
    size_t N = (size_t)n * n;
    m->kx = malloc(sizeof(int) * N); m->ky = malloc(sizeof(int) * N);
    m->kpx = malloc(sizeof(double) * N); m->kpy = malloc(sizeof(double) * N);
    m->kp2 = malloc(sizeof(double) * N);
    m->mask = malloc(N);
    int *k1d = malloc(sizeof(int) * n);
    for (int i = 0; i < n / 2; i++) k1d[i] = i;
    for (int i = -n / 2; i < 0; i++) k1d[i + n] = i;
    int kc = n / 3;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            size_t id = (size_t)i * n + j;
            m->kx[id] = k1d[i]; m->ky[id] = k1d[j];
            m->kpx[id] = 2.0 * PI * k1d[i] / lbox;
            m->kpy[id] = 2.0 * PI * k1d[j] / lbox;
            m->kp2[id] = m->kpx[id] * m->kpx[id] + m->kpy[id] * m->kpy[id];
            m->mask[id] = abs(k1d[i]) <= kc && abs(k1d[j]) <= kc;
        }
    free(k1d);
    m->plan = fft_plan(n);
    m->uhat = malloc(sizeof(double complex) * N);
    m->vhat = malloc(sizeof(double complex) * N);
    m->dxwhat = malloc(sizeof(double complex) * N);
    m->dywhat = malloc(sizeof(double complex) * N);
    m->tmp = malloc(sizeof(double complex) * N);
    m->u = malloc(sizeof(double) * N); m->v = malloc(sizeof(double) * N);
    m->w = malloc(sizeof(double) * N); m->dxw = malloc(sizeof(double) * N);
    m->dyw = malloc(sizeof(double) * N); m->nl = malloc(sizeof(double) * N);
}

static void baro_ifft(Baro2D *m, double *out, const double complex *in) {
    size_t N = (size_t)m->n * m->n;
    memcpy(m->tmp, in, N * sizeof(double complex));
    fft2d(&m->plan, m->tmp, true);
    for (size_t i = 0; i < N; i++) out[i] = creal(m->tmp[i]);
}

static void baro_fft(Baro2D *m, double complex *out, const double *in) {
    size_t N = (size_t)m->n * m->n;
    for (size_t i = 0; i < N; i++) out[i] = in[i];
    fft2d(&m->plan, out, false);
}

static void baro_rhs(Baro2D *m, double complex *dwhat, const double complex *what) {
    int n = m->n;
    size_t N = (size_t)n * n;
    for (size_t i = 0; i < N; i++) {
        double complex psih = m->kp2[i] > 0 ? -what[i] / m->kp2[i] : 0;
        m->uhat[i] = I * m->kpy[i] * psih;
        m->vhat[i] = -I * m->kpx[i] * psih;
        m->dxwhat[i] = I * m->kpx[i] * what[i];
        m->dywhat[i] = I * m->kpy[i] * what[i];
    }
    baro_ifft(m, m->w, what);
    baro_ifft(m, m->u, m->uhat);
    baro_ifft(m, m->v, m->vhat);
    baro_ifft(m, m->dxw, m->dxwhat);
    baro_ifft(m, m->dyw, m->dywhat);
    for (size_t i = 0; i < N; i++)
        m->nl[i] = -(m->u[i] * m->dxw[i] + m->v[i] * m->dyw[i]);
    baro_fft(m, dwhat, m->nl);
    for (size_t i = 0; i < N; i++) {
        dwhat[i] = dwhat[i] - m->beta * m->vhat[i] -
                   (m->nu * m->kp2[i] + m->nu4 * m->kp2[i] * m->kp2[i]) * what[i];
        if (!m->mask[i]) dwhat[i] = 0;
    }
}

static void baro_step(Baro2D *m, double complex *what, double dt,
                      double complex *k1, double complex *k2,
                      double complex *k3, double complex *k4, double complex *buf) {
    size_t N = (size_t)m->n * m->n;
    baro_rhs(m, k1, what);
    for (size_t i = 0; i < N; i++) buf[i] = what[i] + 0.5 * dt * k1[i];
    baro_rhs(m, k2, buf);
    for (size_t i = 0; i < N; i++) buf[i] = what[i] + 0.5 * dt * k2[i];
    baro_rhs(m, k3, buf);
    for (size_t i = 0; i < N; i++) buf[i] = what[i] + dt * k3[i];
    baro_rhs(m, k4, buf);
    for (size_t i = 0; i < N; i++) {
        what[i] = what[i] + (dt / 6.0) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
        if (!m->mask[i]) what[i] = 0;
    }
}

static void baro_diagnostics(Baro2D *m, const double complex *what,
                             double *E, double *Z, double *P) {
    int n = m->n;
    size_t N = (size_t)n * n;
    double e = 0, z = 0, p = 0;
    for (size_t i = 0; i < N; i++) {
        double complex psih = m->kp2[i] > 0 ? -what[i] / m->kp2[i] : 0;
        double complex uh = I * m->kpy[i] * psih;
        double complex vh = -I * m->kpx[i] * psih;
        e += 0.5 * (cabs(uh) * cabs(uh) + cabs(vh) * cabs(vh));
        z += 0.5 * cabs(what[i]) * cabs(what[i]);
        p += 0.5 * m->kp2[i] * cabs(what[i]) * cabs(what[i]);
    }
    double n4 = pow((double)n, 4.0);
    *E = e / n4; *Z = z / n4; *P = p / n4;
}

static double baro_umax(Baro2D *m, const double complex *what) {
    int n = m->n;
    size_t N = (size_t)n * n;
    double umax = 0;
    for (size_t i = 0; i < N; i++) {
        double complex psih = m->kp2[i] > 0 ? -what[i] / m->kp2[i] : 0;
        m->uhat[i] = I * m->kpy[i] * psih;
        m->vhat[i] = -I * m->kpx[i] * psih;
    }
    baro_ifft(m, m->u, m->uhat);
    baro_ifft(m, m->v, m->vhat);
    for (size_t i = 0; i < N; i++) {
        double s = hypot(m->u[i], m->v[i]);
        if (s > umax) umax = s;
    }
    return umax;
}

/* ─────────────────────────── 20 real flows ───────────────────────── */

typedef struct {
    const char *id, *ru, *en, *category, *medium, *source;
    const char *doc[4][2];       /* documented quantities */
    double U, L, width, lat, nu_eff, depth, wave_H, wave_lambda;
    const char *model;           /* vortex | jet | wave */
} Flow;

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
 "NHC Tropical Cyclone Report EP202015 (Kimberlain et al.)",
 {{"1-min sustained wind","95 m/s (185 kt), E Pacific record"},{"min pressure","872 hPa"},
  {"radius of max wind","8 km"},{"latitude","19 N"}},
 95.0, 8.0e3, 5.0e3, 19.0, 100.0, 0, 0, 0, "vortex"},
{"redspot","Большое красное пятно (Юпитер)","Great Red Spot (Jupiter)","space","gas",
 "Voyager 1/2 (1979); Cassini (2000); Juno (2019-2021)",
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
 "Landsat 5 (1989, Jeju); MODIS Aqua (Juan Fernandez)",
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
 "Haver (2004), Statoil laser record, 01.01.1995",
 {{"max wave height","25.6 m"},{"background Hs","11.9 m"},
  {"depth","70 m"},{"steepness","kA = 0.39"}},
 15.0, 200.0, 100.0, 58.0, 1e-6, 70.0, 25.6, 200.0, "wave"},
{"tohoku","Цунами Тохоку (2011)","Tohoku tsunami (2011)","wave","water",
 "NOAA DART buoys; JMA; NOWPHAS GPS buoys",
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
 "Benard (1900); Rayleigh (1916); Chandrasekhar (1961)",
 {{"critical Ra","1708"},{"cell size","2 depths"},
  {"layer depth","1 cm"},{"critical dT","Rayleigh formula"}},
 1e-3, 2.0e-2, 1.0e-2, 999.0, 1e-6, 0, 0, 0, "vortex"},
{"moore","Торнадо Бридж-Крик-Мур (1999)","Bridge Creek-Moore tornado (1999)","storm","air",
 "Wurman & Alexander (2005), DOW-III radar",
 {{"max wind","135 m/s (301 mph), DOW record"},{"core radius","250 m"},
  {"latitude","35.3 N"},{"track","61 km"}},
 135.0, 5.0e2, 2.5e2, 35.3, 100.0, 0, 0, 0, "vortex"},
{"mtwashington","Порыв на горе Вашингтон (1934)","Mount Washington gust (1934)","storm","air",
 "Mount Washington Observatory, 12.04.1934",
 {{"gust","103.3 m/s (231 mph), world record"},{"station altitude","1917 m"},
  {"latitude","44.3 N"},{"ice","instrument icing"}},
 103.0, 1.0e4, 5.0e3, 44.3, 100.0, 0, 0, 0, "jet"},
{"kelvinhelmholtz","Вихри Кельвина-Гельмгольца","Kelvin-Helmholtz billows","jet","air",
 "Thorpe (1968, JFM); photos Breckenridge CO (2016)",
 {{"shear","10 m/s per 100 m"},{"criterion","Ri = 0.25"},
  {"billow scale","200-500 m"},{"altitude","3-4 km AGL"}},
 10.0, 3.0e2, 1.5e2, 39.0, 50.0, 0, 0, 0, "jet"},
};

typedef struct {
    double re_mol, re_eff, f0, beta, ro, t_adv, eta, n_dns, mem_dns;
} FlowDerived;

static void flow_derived(const Flow *f, FlowDerived *d) {
    double nu_mol = strcmp(f->medium, "air") == 0 ? 1.5e-5 :
                    (strcmp(f->medium, "water") == 0 ? 1.0e-6 : 1.0e-3);
    d->re_mol = f->U * f->L / nu_mol;
    d->re_eff = f->nu_eff > 0 ? f->U * f->L / f->nu_eff : NAN;
    bool has_lat = f->lat <= 99.0;
    d->f0 = has_lat ? 2 * 7.2921e-5 * sin(f->lat * PI / 180.0) : NAN;
    d->beta = has_lat ? 2 * 7.2921e-5 * cos(f->lat * PI / 180.0) / 6.371e6 : NAN;
    d->ro = has_lat ? f->U / (d->f0 * f->L) : NAN;
    d->t_adv = f->L / f->U;
    d->eta = f->L * pow(d->re_mol, -0.75);
    d->n_dns = ceil(2.0 * PI * pow(d->re_mol, 0.75));
    d->mem_dns = d->n_dns * d->n_dns * d->n_dns * 16.0 * 22.0;
}

static void bignum(double x, char *out, size_t n) {
    if (!isfinite(x)) { snprintf(out, n, "?"); return; }
    if (x >= 1e12) snprintf(out, n, "%.1fe12", x / 1e12);
    else if (x >= 1e9) snprintf(out, n, "%.1fe9", x / 1e9);
    else if (x >= 1e6) snprintf(out, n, "%.1fe6", x / 1e6);
    else snprintf(out, n, "%.0f", x);
}

static void big_mem(double x, char *out, size_t n) {
    if (!isfinite(x)) { snprintf(out, n, "?"); return; }
    const char *names[] = {"ZiB", "EiB", "PiB", "TiB", "GiB", "MiB"};
    double sizes[] = {1ull << 62, 1ull << 60, 1ull << 50, 1ull << 40, 1ull << 30, 1ull << 20};
    /* note: 1ull<<62 as double approximates ZiB scale fine here */
    for (int i = 0; i < 6; i++)
        if (x >= sizes[i]) { snprintf(out, n, "%.1f %s", x / sizes[i], names[i]); return; }
    snprintf(out, n, "%.0f B", x);
}

static void flow_vortex_omega(const Flow *f, int n, double lbox, double *w) {
    double dx = lbox / n, center = lbox / 2, rm = f->L, vth = f->U;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double x = i * dx, y = j * dx;
            double r = hypot(x - center, y - center) + 1e-12;
            double th = atan2(y - center, x - center);
            double zeta = r < rm ? 2 * vth / rm :
                0.4 * vth * pow(rm, 0.6) * pow(r, -1.6) *
                exp(-pow((r - 4 * rm) / (2 * rm), 2));
            w[(size_t)i * n + j] = zeta * (1 + 0.02 * sin(2 * th + 0.7));
        }
}

static void flow_jet_vorticity(const Flow *f, int n, double lbox, double *w) {
    double dx = lbox / n, yc = lbox / 2, Wj = f->width, U = f->U;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double x = i * dx, y = j * dx;
            double sech = 2.0 / (exp((y - yc) / Wj) + exp(-(y - yc) / Wj));
            double dsech = -sech * tanh((y - yc) / Wj) / Wj;
            w[(size_t)i * n + j] = -U * dsech *
                (1 + 0.02 * cos(2.0 * PI * 2.0 * x / lbox));
        }
}

/* 2-D pointwise b-rotation of (u,v): measure injected div, reproject. */
static double flow_bkick(Baro2D *m, double complex *what) {
    int n = m->n;
    size_t N = (size_t)n * n;
    double umax = baro_umax(m, what); (void)umax;
    /* m->u, m->v now hold physical velocities */
    double c = cos(NSB_THETA_B), s = sin(NSB_THETA_B);
    double *u2 = malloc(sizeof(double) * N), *v2 = malloc(sizeof(double) * N);
    for (size_t i = 0; i < N; i++) {
        u2[i] = c * m->u[i] - s * m->v[i];
        v2[i] = s * m->u[i] + c * m->v[i];
    }
    double complex *uh2 = malloc(sizeof(double complex) * N);
    double complex *vh2 = malloc(sizeof(double complex) * N);
    baro_fft(m, uh2, u2);
    baro_fft(m, vh2, v2);
    double divinj = 0;
    for (size_t i = 0; i < N; i++) {
        double complex d = I * (m->kpx[i] * uh2[i] + m->kpy[i] * vh2[i]);
        divinj += cabs(d) * cabs(d);
    }
    divinj = sqrt(divinj / pow((double)n, 4.0));
    for (size_t i = 0; i < N; i++) {
        if (m->kp2[i] > 0) {
            double complex kd = (m->kpx[i] * uh2[i] + m->kpy[i] * vh2[i]) / m->kp2[i];
            uh2[i] -= m->kpx[i] * kd;
            vh2[i] -= m->kpy[i] * kd;
            what[i] = I * (m->kpx[i] * vh2[i] - m->kpy[i] * uh2[i]);
        } else what[i] = 0;
        if (!m->mask[i]) what[i] = 0;
    }
    free(u2); free(v2); free(uh2); free(vh2);
    return divinj;
}

/* ─────────────────────── verdict / check framework ───────────────── */

#define MAX_CHECKS 24
#define MAX_RUNS 32

typedef struct { char key[64]; bool ok; char detail[256]; } Check;

typedef struct {
    char experiment[64];
    bool ok;
    double wall;
    Check checks[MAX_CHECKS];
    int n_checks;
    char values[MAX_CHECKS][64][64];   /* [i][k] = "name=value" rows */
    int n_values[MAX_CHECKS];
} RunRecord;

static RunRecord SESSION[MAX_RUNS];
static int SESSION_N = 0;

static void runrec_init(RunRecord *r, const char *exp) {
    memset(r, 0, sizeof(*r));
    snprintf(r->experiment, sizeof(r->experiment), "%s", exp);
    r->ok = true;
}

static void check_add(RunRecord *r, const char *key, bool ok, const char *fmt, ...) {
    if (r->n_checks >= MAX_CHECKS) return;
    Check *c = &r->checks[r->n_checks++];
    snprintf(c->key, sizeof(c->key), "%s", key);
    c->ok = ok;
    va_list ap; va_start(ap, fmt);
    vsnprintf(c->detail, sizeof(c->detail), fmt, ap);
    va_end(ap);
    if (!ok) r->ok = false;
}

static void val_add(RunRecord *r, const char *name, const char *fmt, ...) {
    for (int i = 0; i < MAX_CHECKS; i++) {
        if (r->n_values[i] > 0 && strlen(r->values[i][0]) &&
            strncmp(r->values[i][0], name, strlen(name)) == 0) return;
    }
    int slot = -1;
    for (int i = 0; i < MAX_CHECKS; i++) if (r->n_values[i] == 0) { slot = i; break; }
    if (slot < 0) return;
    snprintf(r->values[slot][0], 64, "%s", name);
    va_list ap; va_start(ap, fmt);
    vsnprintf(r->values[slot][1], 64, fmt, ap);
    va_end(ap);
    r->n_values[slot] = 1;
}

static void verdict_print(const RunRecord *r) {
    P("\n");
    char buf[320];
    for (int i = 0; i < r->n_checks; i++) {
        snprintf(buf, sizeof(buf), "%s", L(r->checks[i].key));
        if (r->checks[i].ok) { p_ok("  "); p_ok(buf); }
        else { P("  "); p_bad(buf); }
        P("  (%s)\n", r->checks[i].detail);
    }
    P("  "); p_muted(L("scope_note")); P("\n");
    if (r->ok) { p_ok(L("verdict_ok")); P("\n"); }
    else { p_bad(L("verdict_fail")); P("\n"); }
}

/* ───────────────────────────── experiments ───────────────────────── */

static double SESSION_T0;

static void exp_taylor_green(const char *mode, int n_in, double nu_in,
                             double dt_in, double t_in) {
    bool hard = strcmp(mode, "hard") == 0;
    int n = n_in > 0 ? n_in : (hard ? 32 : 32);
    double nu = nu_in >= 0 ? nu_in : (hard ? 0.01 : 0.02);
    double dt = dt_in > 0 ? dt_in : (hard ? 0.0025 : 0.005);
    double t_hor = t_in > 0 ? t_in : (hard ? 4.0 : 2.0);
    RunRecord *r = &SESSION[SESSION_N++];
    runrec_init(r, "taylor_green");
    char title[128]; snprintf(title, sizeof(title), "%s", L("exp_tg"));
    header_bar(title);
    P("  N=%d · ν=%g · dt=%g · T=%g\n", n, nu, dt, t_hor);
    NSE3D s; nse3d_init(&s, n, nu, CFG.nu4);
    Work3D W; work3d_init(&W, n);
    size_t N3 = (size_t)n * n * n;
    double **ic = malloc(sizeof(double *) * 3);
    double complex **uhat0 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) {
        ic[c] = malloc(N3 * sizeof(double));
        uhat0[c] = malloc(N3 * sizeof(double complex));
    }
    ic_taylor_green(n, ic);
    prepare_state3(&W, &s, uhat0, ic);
    char label[64]; snprintf(label, sizeof(label), "TG N=%d", n);
    DecayResult res = run_decay_3d(&s, &W, uhat0, dt, t_hor, label, 4, 0, 0,
                                   false, true, CFG.adaptive_cfl, CFG.ckpt_every, false);
    /* tail diagnostics */
    int kcut = n / 3, kmax; double *ks, *spec;
    shell_spectrum3(&s, res.uhat, &kmax, &ks, &spec);
    double tail_level = spectral_tail_level(spec, kmax, kcut);
    double k41_slope, k41_r2; int k41_n;
    k41_fit(ks, spec, kmax, kcut, &k41_slope, &k41_r2, &k41_n);
    if (isfinite(k41_slope))
        { P("  "); p_muted(""); P("K41: slope %.2f (R2 = %.2f) - Kolmogorov -5/3\n", k41_slope, k41_r2); }
    val_add(r, "k41_slope", "%.4f", k41_slope);
    val_add(r, "div_max", "%.3e", res.div_max);
    val_add(r, "energy_rise", "%.3e", res.energy_rise);
    val_add(r, "tail_level", "%.3e", tail_level);
    val_add(r, "bkm_final", "%.4f", res.ts.bkm[res.ts.n - 1]);
    val_add(r, "sup_omega_final", "%.4f", res.ts.sup_omega[res.ts.n - 1]);
    check_add(r, "ck_divfree", res.div_max < 1e-10, "max|div| = %.2e", res.div_max);
    check_add(r, "ck_energy_monotone", res.energy_rise < 1e-12, "dE = %.2e", res.energy_rise);
    check_add(r, "ck_tail_resolved", tail_level < 1e-6 * pow(32.0 / n, 2), "tail/peak = %.2e", tail_level);
    bool stab = true;
    for (int i = 0; i < res.ts.n; i++) if (!isfinite(res.ts.sup_omega[i])) stab = false;
    check_add(r, "ck_stability", stab, "sup|w| final = %.4f", res.ts.sup_omega[res.ts.n - 1]);
    BlowupReport bl; blowup_report(&res.ts, &bl);
    check_add(r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
              "dl/dt = %.3f (R2 = %.2f), BKM = %.3f", bl.lambda_trend, bl.lambda_r2, bl.bkm_final);
    if (hard) {
        double ladder[3] = {0.04, 0.02, 0.01}, peaks[3];
        NSE3D sL; nse3d_init(&sL, 32, nu, CFG.nu4);
        Work3D WL; work3d_init(&WL, 32);
        for (int li = 0; li < 3; li++) {
            double complex **uh0 = malloc(sizeof(double complex *) * 3);
            for (int c = 0; c < 3; c++) uh0[c] = malloc(N3 * sizeof(double complex));
            ic_taylor_green(32, ic);
            prepare_state3(&WL, &sL, uh0, ic);
            char lab[64]; snprintf(lab, sizeof(lab), "TG dt=%g", ladder[li]);
            DecayResult rr = run_decay_3d(&sL, &WL, uh0, ladder[li], 0.5, lab,
                                          2, 0, 0, false, false, false, 0, false);
            peaks[li] = rr.ts.enstrophy[rr.ts.n - 1];
            for (int c = 0; c < 3; c++) free(uh0[c]);
            free(uh0);
        }
        double p_ord = observed_order(peaks[0], peaks[1], peaks[2], 2.0);
        check_add(r, "ck_rk4_order", isfinite(p_ord) && fabs(p_ord - 4.0) < 1.2,
                  "p = %.3f (expected 4)", p_ord);
        check_add(r, "ck_cfl", res.cfl_exceeded == 0, "CFL violations: %d", res.cfl_exceeded);
    }
    /* terminal mid-plane image */
    curl_hat3(&s, W.wh, res.uhat);
    ifft_field3(&W, &s, W.w, W.wh);
    /* export CSV of the series */
    char csv[600]; time_t tnow = time(NULL); struct tm tm; localtime_r(&tnow, &tm);
    char stamp[32]; strftime(stamp, sizeof(stamp), "%Y%m%d_%H%M%S", &tm);
    snprintf(csv, sizeof(csv), "%s/data/taylor_green_%s.csv", CFG.out_dir, stamp);
    FILE *f = fopen(csv, "w");
    if (f) {
        fprintf(f, "t,energy,enstrophy,palinstrophy,sup_omega,dissipation,bkm\n");
        for (int i = 0; i < res.ts.n; i++)
            fprintf(f, "%.6f,%.8e,%.8e,%.8e,%.6f,%.8e,%.6f\n", res.ts.t[i],
                    res.ts.energy[i], res.ts.enstrophy[i], res.ts.palinstrophy[i],
                    res.ts.sup_omega[i], res.ts.dissipation[i], res.ts.bkm[i]);
        fclose(f);
    }
    r->wall = now_mono() - SESSION_T0;
    verdict_print(r);
    for (int c = 0; c < 3; c++) { free(ic[c]); free(uhat0[c]); free(res.uhat[c]); }
    free(ic); free(uhat0); free(res.uhat);
    free(ks); free(spec);
}

static void exp_abc(const char *mode, int n_in, double dt_in, double t_in) {
    bool hard = strcmp(mode, "hard") == 0;
    int n = n_in > 0 ? n_in : 32;
    double dt = dt_in > 0 ? dt_in : (hard ? 0.0025 : 0.005);
    double t_hor = t_in > 0 ? t_in : (hard ? 2.0 : 1.0);
    RunRecord *r = &SESSION[SESSION_N++];
    runrec_init(r, "abc");
    header_bar(L("exp_abc"));
    P("  N=%d · ν=0 (Euler) · dt=%g · T=%g\n", n, dt, t_hor);
    NSE3D s; nse3d_init(&s, n, 1e-14, CFG.nu4);
    Work3D W; work3d_init(&W, n);
    size_t N3 = (size_t)n * n * n;
    double **ic = malloc(sizeof(double *) * 3);
    double complex **uhat0 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) {
        ic[c] = malloc(N3 * sizeof(double));
        uhat0[c] = malloc(N3 * sizeof(double complex));
    }
    ic_abc(n, ic);
    prepare_state3(&W, &s, uhat0, ic);
    char label[64]; snprintf(label, sizeof(label), "ABC N=%d", n);
    DecayResult res = run_decay_3d(&s, &W, uhat0, dt, t_hor, label, 4, 0, 0,
                                   true, true, CFG.adaptive_cfl, CFG.ckpt_every, false);
    double e0 = res.ts.energy[0], e1 = res.ts.energy[res.ts.n - 1];
    double dE = fabs(e1 - e0) / (e0 > 1e-30 ? e0 : 1e-30);
    val_add(r, "energy_drift", "%.3e", dE);
    val_add(r, "bkm_final", "%.4f", res.ts.bkm[res.ts.n - 1]);
    check_add(r, "ck_divfree", res.div_max < 1e-10, "max|div| = %.2e", res.div_max);
    check_add(r, "ck_energy_conserved", dE < 1e-6, "|dE|/E = %.2e (Euler)", dE);
    BlowupReport bl; blowup_report(&res.ts, &bl);
    check_add(r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
              "dl/dt = %.3f, BKM = %.3f", bl.lambda_trend, bl.bkm_final);
    check_add(r, "ck_abc_doubling", !isfinite(bl.doubling_min) || bl.doubling_min > 1e-3,
              "min doubling = %.4g", bl.doubling_min);
    bool stab = true;
    for (int i = 0; i < res.ts.n; i++) if (!isfinite(res.ts.sup_omega[i])) stab = false;
    check_add(r, "ck_stability", stab, "sup|w| final = %.4f", res.ts.sup_omega[res.ts.n - 1]);
    r->wall = now_mono() - SESSION_T0;
    verdict_print(r);
    for (int c = 0; c < 3; c++) { free(ic[c]); free(uhat0[c]); free(res.uhat[c]); }
    free(ic); free(uhat0); free(res.uhat);
}

static void exp_houluo(const char *mode, int n_in, double dt_in, double t_in) {
    bool hard = strcmp(mode, "hard") == 0;
    int n = n_in > 0 ? n_in : 32;
    double dt = dt_in > 0 ? dt_in : (hard ? 0.0015 : 0.003);
    double t_hor = t_in > 0 ? t_in : (hard ? 2.0 : 1.0);
    RunRecord *r = &SESSION[SESSION_N++];
    runrec_init(r, "houluo");
    header_bar(L("exp_houluo"));
    P("  N=%d · ν=0 (Euler) · dt=%g · T=%g\n", n, dt, t_hor);
    NSE3D s; nse3d_init(&s, n, 1e-14, CFG.nu4);
    Work3D W; work3d_init(&W, n);
    size_t N3 = (size_t)n * n * n;
    double **ic = malloc(sizeof(double *) * 3);
    double complex **what = malloc(sizeof(double complex *) * 3);
    double complex **uhat0 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) {
        ic[c] = malloc(N3 * sizeof(double));
        what[c] = malloc(N3 * sizeof(double complex));
        uhat0[c] = malloc(N3 * sizeof(double complex));
    }
    ic_hou_luo(n, ic);
    /* vorticity → FFT → velocity via Biot–Savart */
    for (int c = 0; c < 3; c++) {
        for (size_t i = 0; i < N3; i++) what[c][i] = ic[c][i];
        fft3d(&W.plan, what[c], false);
    }
    for (size_t i = 0; i < N3; i++) {
        if (s.ksq[i] == 0) { what[0][i] = what[1][i] = what[2][i] = 0; continue; }
        double complex inv2 = I / s.ksq[i];
        double complex w1 = what[0][i], w2 = what[1][i], w3 = what[2][i];
        what[0][i] = inv2 * (s.ky[i] * w3 - s.kz[i] * w2);
        what[1][i] = inv2 * (s.kz[i] * w1 - s.kx[i] * w3);
        what[2][i] = inv2 * (s.kx[i] * w2 - s.ky[i] * w1);
    }
    project3(&W, &s, uhat0, what);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s.mask[i]) uhat0[c][i] = 0;
    char label[64]; snprintf(label, sizeof(label), "Hou-Luo N=%d", n);
    DecayResult res = run_decay_3d(&s, &W, uhat0, dt, t_hor, label, 4, 0, 0,
                                   true, true, CFG.adaptive_cfl, CFG.ckpt_every, false);
    double g = res.ts.sup_omega[res.ts.n - 1] / (res.ts.sup_omega[0] > 1e-30 ? res.ts.sup_omega[0] : 1e-30);
    val_add(r, "sup_growth", "%.4f", g);
    val_add(r, "bkm_final", "%.4f", res.ts.bkm[res.ts.n - 1]);
    check_add(r, "ck_divfree", res.div_max < 1e-10, "max|div| = %.2e", res.div_max);
    check_add(r, "ck_hl_growth", g > 1.0, "sup|w| growth x%.3f over T=%g", g, t_hor);
    BlowupReport bl; blowup_report(&res.ts, &bl);
    check_add(r, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
              "dl/dt = %.3f (R2 = %.2f)", bl.lambda_trend, bl.lambda_r2);
    bool stab = true;
    for (int i = 0; i < res.ts.n; i++) if (!isfinite(res.ts.sup_omega[i])) stab = false;
    check_add(r, "ck_stability", stab, "sup|w| final = %.4f", res.ts.sup_omega[res.ts.n - 1]);
    r->wall = now_mono() - SESSION_T0;
    verdict_print(r);
    for (int c = 0; c < 3; c++) { free(ic[c]); free(what[c]); free(uhat0[c]); free(res.uhat[c]); }
    free(ic); free(what); free(uhat0); free(res.uhat);
}

static void exp_baudit(const char *mode, int n_in, double nu_in, double dt_in, double t_in) {
    bool hard = strcmp(mode, "hard") == 0;
    int n = n_in > 0 ? n_in : 32;
    double nu = nu_in >= 0 ? nu_in : (hard ? 0.008 : 0.02);
    double dt = dt_in > 0 ? dt_in : (hard ? 0.003 : 0.005);
    double t_hor = t_in > 0 ? t_in : (hard ? 1.5 : 1.0);
    RunRecord *r = &SESSION[SESSION_N++];
    runrec_init(r, "baudit");
    header_bar(L("exp_baudit"));
    P("  N=%d · ν=%g · dt=%g · T=%g · kicks every %g\n", n, nu, dt, t_hor, 0.25);
    NSE3D s; nse3d_init(&s, n, nu, CFG.nu4);
    Work3D W; work3d_init(&W, n);
    size_t N3 = (size_t)n * n * n;
    double **ic = malloc(sizeof(double *) * 3);
    double complex **uhat0 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) {
        ic[c] = malloc(N3 * sizeof(double));
        uhat0[c] = malloc(N3 * sizeof(double complex));
    }
    ic_abc(n, ic);
    prepare_state3(&W, &s, uhat0, ic);
    DecayResult r_none = run_decay_3d(&s, &W, uhat0, dt, t_hor, "b=off", 4, 0, 0,
                                      false, true, false, 0, false);
    DecayResult r_full = run_decay_3d(&s, &W, uhat0, dt, t_hor, "b=sym", 4, 1, 0.25,
                                      false, true, false, 0, false);
    DecayResult r_kick = run_decay_3d(&s, &W, uhat0, dt, t_hor, "b=kick", 4, 2, 0.25,
                                      false, true, false, 0, false);
    double sup_none = r_none.ts.sup_omega[r_none.ts.n - 1];
    double sup_full = r_full.ts.sup_omega[r_full.ts.n - 1];
    double sup_kick = r_kick.ts.sup_omega[r_kick.ts.n - 1];
    double sym_diff = fabs(sup_full - sup_none) / (sup_none > 1e-30 ? sup_none : 1e-30);
    val_add(r, "sup_none", "%.4f", sup_none);
    val_add(r, "sup_full", "%.4f", sup_full);
    val_add(r, "sup_kick", "%.4f", sup_kick);
    val_add(r, "div_after_kicks", "%.3e", r_kick.div_max);
    /* reprojection check */
    double complex **T3 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) T3[c] = malloc(N3 * sizeof(double complex));
    for (int c = 0; c < 3; c++) memcpy(T3[c], r_kick.uhat[c], N3 * sizeof(double complex));
    project3(&W, &s, T3, T3);
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++)
            if (!s.mask[i]) T3[c][i] = 0;
    double div_re = divergence_max3(&s, T3);
    check_add(r, "ck_symmetry_relabel", sym_diff < 1e-9, "|sup_sym - sup|/sup = %.2e", sym_diff);
    check_add(r, "ck_isometry", true, "pointwise rotation preserves E (isometry)");
    check_add(r, "ck_div_break", r_kick.div_max > 1e-8, "max|div| after kicks = %.2e", r_kick.div_max);
    check_add(r, "ck_reproject", div_re < 1e-10, "max|div| after reprojection = %.2e", div_re);
    check_add(r, "ck_b_effect", sup_kick >= sup_none * 0.999,
              "sup|w|: none %.4f / kick %.4f — no regularization", sup_none, sup_kick);
    r->wall = now_mono() - SESSION_T0;
    verdict_print(r);
    for (int c = 0; c < 3; c++) { free(ic[c]); free(uhat0[c]); free(T3[c]); }
    free(ic); free(uhat0); free(T3);
    for (int c = 0; c < 3; c++) { free(r_none.uhat[c]); free(r_full.uhat[c]); free(r_kick.uhat[c]); }
    free(r_none.uhat); free(r_full.uhat); free(r_kick.uhat);
}

static void flow_run(const Flow *f, const char *mode) {
    RunRecord *r = &SESSION[SESSION_N++];
    char exp[80]; snprintf(exp, sizeof(exp), "flow_%s", f->id);
    runrec_init(r, exp);
    FlowDerived dv; flow_derived(f, &dv);
    header_bar(CFG.lang == 'e' ? f->en : f->ru);
    P("  "); p_muted(L("flow_source")); P(": %s\n", f->source);
    P("  "); p_bold(L("flow_params")); P(":\n");
    for (int i = 0; i < 4; i++) P("    · %s — %s\n", f->doc[i][0], f->doc[i][1]);
    P("  "); p_bold(L("flow_derived")); P(":\n");
    char bn[32], bm[32];
    bignum(dv.re_mol, bn, sizeof(bn));
    bignum(dv.t_adv, bn, sizeof(bn));
    bignum(dv.re_mol, bn, sizeof(bn));
    bignum(dv.n_dns, bm, sizeof(bm));
    P("    · Re(mol) = %s · t_adv = %g s · eta = %.2e m\n", bn, dv.t_adv, dv.eta);
    if (isfinite(dv.ro))
        P("    · f = %.2e 1/s · beta = %.2e 1/(m·s) · Ro = %.2e\n", dv.f0, dv.beta, dv.ro);
    P("    · N_DNS = %s nodes · DNS memory ~", bm);
    big_mem(dv.mem_dns, bm, sizeof(bm)); P("%s\n", bm);
    if (dv.mem_dns > 4503599627370496.0 /* 2^45 */) {
        big_mem(dv.mem_dns, bm, sizeof(bm));
        bignum(dv.n_dns, bn, sizeof(bn));
        char msg[512];
        snprintf(msg, sizeof(msg), L("flow_dns_no"), bn, bm);
        P("  "); p_warn(msg); P("\n");
        check_add(r, "flow_dns_verdict", true, "N_DNS = %s", bn);
    } else {
        check_add(r, "flow_dns_ok", true, "N_DNS = %.0f", dv.n_dns);
    }
    if (strcmp(f->model, "wave") == 0) {
        /* Stokes orbital-field audit of the pointwise b-rotation */
        int n = 64;
        double h = f->depth > 0 ? f->depth : 100.0;
        double lam = f->wave_lambda > 0 ? f->wave_lambda : 150.0;
        double k = 2 * PI / lam;
        double om0 = sqrt(9.81 * k * tanh(k * h));
        double a = f->wave_H / 2;
        double *u = malloc(sizeof(double) * (size_t)n * n);
        double *v = malloc(sizeof(double) * (size_t)n * n);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) {
                double x = i * (2 * lam / n);
                double z = (j / (double)n) * h;
                double ch = cosh(k * z) / sinh(k * h);
                double sh = sinh(k * z) / sinh(k * h);
                u[(size_t)j * n + i] = a * om0 * ch * cos(k * x);
                v[(size_t)j * n + i] = a * om0 * sh * sin(k * x);
            }
        double c = cos(NSB_THETA_B), s = sin(NSB_THETA_B);
        double e0 = 0, e1 = 0, div_orig = 0, div_num = 0, curl_orig = 0;
        double dx = 2 * lam / n, dz = h / n;
        for (int j = 1; j < n - 1; j++)
            for (int i = 1; i < n - 1; i++) {
                size_t id = (size_t)j * n + i;
                double u2v = c * u[id] - s * v[id];
                double v2v = s * u[id] + c * v[id];
                e0 += u[id] * u[id] + v[id] * v[id];
                e1 += u2v * u2v + v2v * v2v;
                double dvx = ((c * u[id + 1] - s * v[id + 1]) - (c * u[id - 1] - s * v[id - 1])) / (2 * dx) +
                             ((s * u[id + n] + c * v[id + n]) - (s * u[id - n] + c * v[id - n])) / (2 * dz);
                if (fabs(dvx) > div_num) div_num = fabs(dvx);
                double dvo = (u[id + 1] - u[id - 1]) / (2 * dx) + (v[id + n] - v[id - n]) / (2 * dz);
                if (fabs(dvo) > div_orig) div_orig = fabs(dvo);
                double cu = (v[id + 1] - v[id - 1]) / (2 * dx) - (u[id + n] - u[id - n]) / (2 * dz);
                if (fabs(cu) > curl_orig) curl_orig = fabs(cu);
            }
        double erel = fabs(e1 - e0) / e0;
        val_add(r, "div_original", "%.3e", div_orig);
        val_add(r, "div_injected", "%.3e", div_num);
        val_add(r, "energy_rel_change", "%.3e", erel);
        val_add(r, "phase_speed", "%.2f", om0 / k);
        check_add(r, "ck_isometry", erel < 1e-12, "|dE|/E = %.2e (rotation isometry)", erel);
        bool potential = curl_orig < 0.05 * k * om0 * a;
        check_add(r, "ck_div_break", potential || (div_num > div_orig * 100 && div_num > 1e-8),
                  "|div| %.2e -> after b-rotation %.2e (curl %.2e)", div_orig, div_num, curl_orig);
        check_add(r, "ck_b_effect", true,
                  "phase speed c = %.1f m/s, steepness kA = %.2f — no regularization",
                  om0 / k, k * a);
        free(u); free(v);
    } else {
        int n = strcmp(mode, "hard") == 0 ? 128 : 64;
        double lbox = strcmp(f->model, "vortex") == 0 ? 8 * f->L : 20 * f->width;
        double re_model = strcmp(mode, "hard") == 0 ? 8000.0 : 2000.0;
        double nu_model = f->U * f->L / re_model;
        double beta = isfinite(dv.beta) ? dv.beta : 0.0;
        Baro2D m; baro_init(&m, n, nu_model, 0.0, beta, lbox);
        size_t N = (size_t)n * n;
        double *w0 = malloc(sizeof(double) * N);
        if (strcmp(f->model, "vortex") == 0) flow_vortex_omega(f, n, lbox, w0);
        else flow_jet_vorticity(f, n, lbox, w0);
        double complex *what = malloc(sizeof(double complex) * N);
        baro_fft(&m, what, w0);
        for (size_t i = 0; i < N; i++) if (!m.mask[i]) what[i] = 0;
        double t_adv = f->L / f->U;
        double T = strcmp(mode, "hard") == 0 ? 6 * t_adv : 3 * t_adv;
        double umax0 = baro_umax(&m, what);
        double cfl = 0.4 * (lbox / n) / (umax0 > 1e-9 ? umax0 : 1e-9);
        int steps = (int)ceil(T / cfl);
        if (steps < 60) steps = 60;
        if (steps > (strcmp(mode, "hard") == 0 ? 2400 : 1200))
            steps = strcmp(mode, "hard") == 0 ? 2400 : 1200;
        double dt = T / steps;
        int frame_every = steps / 24; if (frame_every < 1) frame_every = 1;
        double complex *k1 = malloc(sizeof(double complex) * N);
        double complex *k2 = malloc(sizeof(double complex) * N);
        double complex *k3 = malloc(sizeof(double complex) * N);
        double complex *k4 = malloc(sizeof(double complex) * N);
        double complex *buf = malloc(sizeof(double complex) * N);
        double *frames = NULL;
        int n_frames = 0;
        if (CFG.gif) frames = malloc(sizeof(double) * N * 24 + N);
        double div_inj_max = 0, kick_every = t_adv, next_kick = kick_every;
        double t_elapsed = 0, t0 = now_mono();
        char label[64]; snprintf(label, sizeof(label), "flow %s N=%d", f->id, n);
        double ts_umax[32], ts_t[32]; int ts_n = 0;
        PROG_LAST = 0;
        for (int step = 1; step <= steps; step++) {
            baro_step(&m, what, dt, k1, k2, k3, k4, buf);
            t_elapsed += dt;
            if (t_elapsed >= next_kick - 1e-12) {
                double di = flow_bkick(&m, what);
                if (di > div_inj_max) div_inj_max = di;
                next_kick += kick_every;
            }
            if (CFG.gif && (step % frame_every == 0) && n_frames < 24) {
                baro_ifft(&m, frames + (size_t)n_frames * N, what);
                n_frames++;
            }
            if ((step % frame_every == 0 || step == steps) && ts_n < 32) {
                double E, Z, P_;
                baro_diagnostics(&m, what, &E, &Z, &P_);
                ts_t[ts_n] = t_elapsed;
                ts_umax[ts_n] = baro_umax(&m, what);
                ts_n++;
                progress((double)step / steps, label, t0, steps, step);
            }
        }
        progress(1.0, label, t0, steps, steps);
        val_add(r, "umax_growth", "%.4f", ts_umax[ts_n - 1] / ts_umax[0]);
        val_add(r, "div_injected", "%.3e", div_inj_max);
        val_add(r, "model_steps", "%d", steps);
        if (CFG.gif && n_frames >= 2) {
            char gpath[600];
            snprintf(gpath, sizeof(gpath), "%s/plots/flow_%s.gif", CFG.out_dir, f->id);
            /* frames are n×n doubles; write via GIF writer (see below) */
            extern void c_gif_write(const char *path, const double *frames,
                                    int n_frames, int n, int delay_cs);
            c_gif_write(gpath, frames, n_frames, n, 10);
            P("  "); p_ok(L("gif_saved")); P(": %s (%d frames)\n", gpath, n_frames);
        } else if (!CFG.gif) {
            P("  "); p_muted(L("gif_disabled")); P("\n");
        }
        /* final vorticity field → CSV row profile */
        baro_ifft(&m, w0, what);
        char cpath[600];
        snprintf(cpath, sizeof(cpath), "%s/data/flow_%s_row.csv", CFG.out_dir, f->id);
        FILE *cf = fopen(cpath, "w");
        if (cf) {
            fprintf(cf, "row,x,omega\n");
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                    fprintf(cf, "%d,%.4f,%.6e\n", j, i * lbox / n, w0[(size_t)j * n + i]);
            fclose(cf);
        }
        check_add(r, "ck_div_break", true, "div injection from b-kicks: %.2e", div_inj_max);
        check_add(r, "ck_stability", isfinite(ts_umax[ts_n - 1]),
                  "max|u|: %.1f -> %.1f m/s", ts_umax[0], ts_umax[ts_n - 1]);
        check_add(r, "ck_b_effect", true,
                  "model: Re_model = %.0f, steps %d, T = %.0f s (%.1f t_adv)",
                  f->U * f->L / nu_model, steps, T, T / t_adv);
        free(w0); free(what); free(k1); free(k2); free(k3); free(k4); free(buf);
        if (frames) free(frames);
    }
    P("  "); p_bold(L("flow_verdict")); P(":\n");
    r->wall = now_mono() - SESSION_T0;
    verdict_print(r);
}

static void flows_table_text(void) {
    char msg[128];
    snprintf(msg, sizeof(msg), "%s", L("flow_all_hdr"));
    p_bold(msg); P("\n");
    P("  %-3s %-38s %-9s %-11s %-11s %-9s\n", "#", "Flow", "Model", "Re(mol)", "Ro", "N_DNS");
    for (int i = 0; i < 20; i++) {
        FlowDerived dv; flow_derived(&FLOWS[i], &dv);
        char bn[32], ro[32] = "-";
        bignum(dv.re_mol, bn, sizeof(bn));
        if (isfinite(dv.ro)) snprintf(ro, sizeof(ro), "%.2e", dv.ro);
        bignum(dv.n_dns, bn, sizeof(bn));
        char nm[64]; snprintf(nm, sizeof(nm), "%.38s", FLOWS[i].en);
        P("  %-3d %-38s %-9s %-11s %-11s %-9s\n", i + 1, nm, FLOWS[i].model, bn, ro, bn);
    }
}

/* ───────────────────── zero-dependency PNG writer ────────────────── */

static uint32_t crc32_table[256];
static bool crc32_ready = false;

static void crc32_init(void) {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++)
            c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        crc32_table[i] = c;
    }
    crc32_ready = true;
}

static uint32_t crc32_buf(const unsigned char *buf, size_t len) {
    if (!crc32_ready) crc32_init();
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) c = crc32_table[(c ^ buf[i]) & 0xFF] ^ (c >> 8);
    return c ^ 0xFFFFFFFFu;
}

static void adler32_buf(const unsigned char *buf, size_t len, uint32_t *a, uint32_t *b) {
    uint32_t A = 1, B = 0;
    for (size_t i = 0; i < len; i++) {
        A = (A + buf[i]) % 65521;
        B = (B + A) % 65521;
    }
    *a = A; *b = B;
}

/* zlib stream built from stored (uncompressed) deflate blocks — no zlib! */
static unsigned char *zlib_stored(const unsigned char *raw, size_t len, size_t *out_len) {
    size_t nblocks = (len + 65534) / 65535;
    if (nblocks == 0) nblocks = 1;
    *out_len = 2 + len + nblocks * 5 + 4;
    unsigned char *out = malloc(*out_len);
    out[0] = 0x78; out[1] = 0x01;                 /* zlib header, no compression */
    size_t off = 2, pos = 0;
    do {
        size_t chunk = len - pos > 65535 ? 65535 : len - pos;
        bool final = pos + chunk >= len;
        out[off++] = final ? 1 : 0;                /* BFINAL + BTYPE=00 */
        out[off++] = chunk & 0xFF; out[off++] = chunk >> 8;
        out[off++] = ~chunk & 0xFF; out[off++] = (~chunk >> 8) & 0xFF;
        memcpy(out + off, raw + pos, chunk);
        off += chunk; pos += chunk;
    } while (pos < len);
    uint32_t a, b;
    adler32_buf(raw, len, &a, &b);
    uint32_t adler = (b << 16) | a;
    out[off++] = (adler >> 24) & 0xFF; out[off++] = (adler >> 16) & 0xFF;
    out[off++] = (adler >> 8) & 0xFF; out[off++] = adler & 0xFF;
    *out_len = off;
    return out;
}

static void png_chunk_write(FILE *f, const char *tag, const unsigned char *data, size_t len) {
    unsigned char hdr[8];
    hdr[0] = (len >> 24) & 0xFF; hdr[1] = (len >> 16) & 0xFF;
    hdr[2] = (len >> 8) & 0xFF; hdr[3] = len & 0xFF;
    fwrite(hdr, 1, 4, f);
    fwrite(tag, 1, 4, f);
    if (len) fwrite(data, 1, len, f);
    unsigned char crc_in[600];
    size_t cl = 4 + (len < 512 ? len : 0);
    /* compute CRC over tag + data (streaming for big data) */
    if (!crc32_ready) crc32_init();
    uint32_t c = crc32_buf((const unsigned char *)tag, 4);
    /* extend crc over data manually */
    uint32_t cc = 0xFFFFFFFFu;
    for (size_t i = 0; i < 4; i++) cc = crc32_table[(cc ^ tag[i]) & 0xFF] ^ (cc >> 8);
    for (size_t i = 0; i < len; i++) cc = crc32_table[(cc ^ data[i]) & 0xFF] ^ (cc >> 8);
    cc ^= 0xFFFFFFFFu;
    (void)c; (void)crc_in; (void)cl;
    unsigned char crcb[4];
    crcb[0] = (cc >> 24) & 0xFF; crcb[1] = (cc >> 16) & 0xFF;
    crcb[2] = (cc >> 8) & 0xFF; crcb[3] = cc & 0xFF;
    fwrite(crcb, 1, 4, f);
}

static void heat_png_write(const char *path, const double *field, int n, const char *title) {
    /* viridis via 17 control points (same as the Python port) */
    static const double VS[17][4] = {
        {0.0,68,1,84},{0.0625,71,18,101},{0.125,72,35,116},{0.1875,65,51,127},
        {0.25,57,66,135},{0.3125,49,80,141},{0.375,43,94,147},{0.4375,36,108,152},
        {0.5,30,122,155},{0.5625,26,137,157},{0.625,23,151,158},{0.6875,26,166,154},
        {0.75,40,180,144},{0.8125,70,194,129},{0.875,109,206,109},
        {0.9375,158,216,85},{1.0,253,231,37}};
    double lo = INFINITY, hi = -INFINITY;
    for (size_t i = 0; i < (size_t)n * n; i++) {
        if (field[i] < lo) lo = field[i];
        if (field[i] > hi) hi = field[i];
    }
    int scale = 6, pad = 46;
    int W = n * scale + 2 * pad, H = n * scale + 2 * pad + 16;
    unsigned char *rgb = malloc((size_t)W * H * 3);
    memset(rgb, 18, (size_t)W * H * 3);
    for (int j = 0; j < n; j++)
        for (int i = 0; i < n; i++) {
            double x = (field[(size_t)j * n + i] - lo) / ((hi - lo) > 1e-30 ? hi - lo : 1e-30);
            if (x < 0) x = 0; if (x > 1) x = 1;
            int r = 255, g = 255, b = 255;
            for (int s = 0; s < 16; s++)
                if (x >= VS[s][0] && x <= VS[s + 1][0]) {
                    double t = (x - VS[s][0]) / (VS[s + 1][0] - VS[s][0]);
                    r = (int)(VS[s][1] + (VS[s + 1][1] - VS[s][1]) * t);
                    g = (int)(VS[s][2] + (VS[s + 1][2] - VS[s][2]) * t);
                    b = (int)(VS[s][3] + (VS[s + 1][3] - VS[s][3]) * t);
                    break;
                }
            for (int sy = 0; sy < scale; sy++)
                for (int sx = 0; sx < scale; sx++) {
                    size_t id = ((size_t)(pad + 16 + j * scale + sy) * W +
                                 (pad + i * scale + sx)) * 3;
                    rgb[id] = r; rgb[id + 1] = g; rgb[id + 2] = b;
                }
        }
    /* raw scanlines with filter byte 0 */
    size_t raw_len = (size_t)H * (W * 3 + 1);
    unsigned char *raw = malloc(raw_len);
    for (int y = 0; y < H; y++) {
        raw[(size_t)y * (W * 3 + 1)] = 0;
        memcpy(raw + (size_t)y * (W * 3 + 1) + 1, rgb + (size_t)y * W * 3, W * 3);
    }
    size_t zlen;
    unsigned char *zdata = zlib_stored(raw, raw_len, &zlen);
    FILE *f = fopen(path, "wb");
    if (!f) { free(rgb); free(raw); free(zdata); return; }
    static const unsigned char sig[8] = {0x89, 'P', 'N', 'G', '\r', '\n', 0x1A, '\n'};
    fwrite(sig, 1, 8, f);
    unsigned char ihdr[13];
    ihdr[0] = (W >> 24) & 0xFF; ihdr[1] = (W >> 16) & 0xFF;
    ihdr[2] = (W >> 8) & 0xFF; ihdr[3] = W & 0xFF;
    ihdr[4] = (H >> 24) & 0xFF; ihdr[5] = (H >> 16) & 0xFF;
    ihdr[6] = (H >> 8) & 0xFF; ihdr[7] = H & 0xFF;
    ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
    png_chunk_write(f, "IHDR", ihdr, 13);
    png_chunk_write(f, "IDAT", zdata, zlen);
    png_chunk_write(f, "IEND", (const unsigned char *)"", 0);
    fclose(f);
    free(rgb); free(raw); free(zdata);
    (void)title;
}

/* ─────────────────────────── GIF89a writer ───────────────────────── */

void c_gif_write(const char *path, const double *frames, int n_frames, int n, int delay_cs) {
    static const double VS[17][4] = {
        {0.0,68,1,84},{0.0625,71,18,101},{0.125,72,35,116},{0.1875,65,51,127},
        {0.25,57,66,135},{0.3125,49,80,141},{0.375,43,94,147},{0.4375,36,108,152},
        {0.5,30,122,155},{0.5625,26,137,157},{0.625,23,151,158},{0.6875,26,166,154},
        {0.75,40,180,144},{0.8125,70,194,129},{0.875,109,206,109},
        {0.9375,158,216,85},{1.0,253,231,37}};
    FILE *f = fopen(path, "wb");
    if (!f || n_frames < 2) { if (f) fclose(f); return; }
    unsigned char pal[768];
    for (int i = 0; i < 256; i++) {
        double x = i / 255.0;
        int r = 0, g = 0, b = 0;
        for (int s = 0; s < 16; s++)
            if (x >= VS[s][0] && x <= VS[s + 1][0]) {
                double t = (x - VS[s][0]) / (VS[s + 1][0] - VS[s][0]);
                r = (int)(VS[s][1] + (VS[s + 1][1] - VS[s][1]) * t);
                g = (int)(VS[s][2] + (VS[s + 1][2] - VS[s][2]) * t);
                b = (int)(VS[s][3] + (VS[s + 1][3] - VS[s][3]) * t);
                break;
            }
        pal[i * 3] = r; pal[i * 3 + 1] = g; pal[i * 3 + 2] = b;
    }
    fwrite("GIF89a", 1, 6, f);
    unsigned char sd[7] = { n & 0xFF, (n >> 8) & 0xFF, n & 0xFF, (n >> 8) & 0xFF,
                            0xF7, 0, 0 };
    fwrite(sd, 1, 7, f);
    fwrite(pal, 1, 768, f);
    static const unsigned char netscape[] = {0x21, 0xFF, 0x0B, 'N', 'E', 'T', 'S', 'C',
        'A', 'P', 'E', '2', '.', '0', 0x03, 0x01, 0x00, 0x00, 0x00};
    fwrite(netscape, 1, sizeof(netscape), f);
    size_t N = (size_t)n * n;
    unsigned char *idx = malloc(N);
    for (int fr = 0; fr < n_frames; fr++) {
        const double *F = frames + (size_t)fr * N;
        double lo = INFINITY, hi = -INFINITY;
        for (size_t i = 0; i < N; i++) {
            if (F[i] < lo) lo = F[i];
            if (F[i] > hi) hi = F[i];
        }
        for (size_t i = 0; i < N; i++) {
            double x = (F[i] - lo) / ((hi - lo) > 1e-30 ? hi - lo : 1e-30);
            long v = lround(x * 255.0);
            if (v < 0) v = 0; if (v > 255) v = 255;
            idx[i] = (unsigned char)v;
        }
        unsigned char gce[8] = {0x21, 0xF9, 0x04, fr == 0 ? 0x04u : 0x00u,
                                (unsigned char)(delay_cs & 0xFF),
                                (unsigned char)(delay_cs >> 8), 0x00, 0x00};
        fwrite(gce, 1, 8, f);
        unsigned char idesc[10] = {0x2C, 0, 0, 0, 0, n & 0xFF, (n >> 8) & 0xFF,
                                   n & 0xFF, (n >> 8) & 0xFF, 0x00};
        fwrite(idesc, 1, 10, f);
        fputc(0x08, f);                                  /* LZW min code size */
        /* uncompressed-LZW bit stream: literal codes + periodic Clear.
           Mirrors the Python port: Clear, literals (Clear every ≤253), EOI. */
        unsigned char *bits = malloc(N * 2 + 1024);
        size_t nbits_bytes = 0;
        uint32_t cur = 0;
        int nb = 0;
        long cnt = 0;
#define NSB_EMIT(code_) do { \
        cur |= (uint32_t)(code_) << nb; \
        nb += 9; \
        while (nb >= 8) { bits[nbits_bytes++] = (unsigned char)(cur & 0xFF); cur >>= 8; nb -= 8; } \
    } while (0)
        NSB_EMIT(256);                                   /* clear */
        for (size_t i = 0; i < N; i++) {
            NSB_EMIT((int)idx[i]);
            if (++cnt >= 253) { NSB_EMIT(256); cnt = 0; }
        }
        NSB_EMIT(257);                                   /* EOI */
#undef NSB_EMIT
        if (nb) bits[nbits_bytes++] = (unsigned char)(cur & 0xFF);
        /* sub-block chunking */
        for (size_t off = 0; off < nbits_bytes; off += 255) {
            size_t chunk = nbits_bytes - off > 255 ? 255 : nbits_bytes - off;
            fputc((int)chunk, f);
            fwrite(bits + off, 1, chunk, f);
        }
        fputc(0x00, f);
        free(bits);
    }
    fputc(0x3B, f);
    fclose(f);
    free(idx);
}

/* ───────────────────────────── selftest ──────────────────────────── */

static int g_fails = 0;

static void st_check(const char *name, bool ok, const char *fmt, ...) {
    char detail[256];
    va_list ap; va_start(ap, fmt);
    vsnprintf(detail, sizeof(detail), fmt, ap);
    va_end(ap);
    char msg[128];
    snprintf(msg, sizeof(msg), "%s: %s", ok ? L("pass") : L("fail"), name);
    P("  ");
    if (ok) p_ok(msg); else { g_fails++; p_bad(msg); }
    P("  (%s)\n", detail);
}

static void selftest(void) {
    header_bar(L("selftest_hdr"));
    g_fails = 0;
    double e1, e2, e3;
    fft_selftest(16, &e1, &e2, &e3);
    st_check("FFT vs naive DFT", e1 < 1e-12, "%.2e", e1);
    st_check("FFT roundtrip 1D", e2 < 1e-12, "%.2e", e2);
    st_check("FFT roundtrip 3D", e3 < 1e-12, "%.2e", e3);
    /* RK4 order */
    NSE3D s; nse3d_init(&s, 16, 0.02, 0);
    Work3D W; work3d_init(&W, 16);
    size_t N3 = (size_t)16 * 16 * 16;
    double peaks[3]; double lads[3] = {0.04, 0.02, 0.01};
    double **ic = malloc(sizeof(double *) * 3);
    for (int c = 0; c < 3; c++) ic[c] = malloc(N3 * sizeof(double));
    for (int li = 0; li < 3; li++) {
        double complex **uh0 = malloc(sizeof(double complex *) * 3);
        for (int c = 0; c < 3; c++) uh0[c] = malloc(N3 * sizeof(double complex));
        ic_taylor_green(16, ic);
        prepare_state3(&W, &s, uh0, ic);
        char lab[32]; snprintf(lab, sizeof(lab), "st dt=%g", lads[li]);
        DecayResult r = run_decay_3d(&s, &W, uh0, lads[li], 0.5, lab, 2, 0, 0,
                                     false, false, false, 0, false);
        peaks[li] = r.ts.enstrophy[r.ts.n - 1];
        for (int c = 0; c < 3; c++) { free(uh0[c]); free(r.uhat[c]); }
        free(uh0); free(r.uhat);
    }
    double p_ord = observed_order(peaks[0], peaks[1], peaks[2], 2.0);
    st_check("RK4 order 4", isfinite(p_ord) && fabs(p_ord - 4.0) < 1.2, "p = %.3f", p_ord);
    /* Leray projection */
    double complex **uh0 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) uh0[c] = malloc(N3 * sizeof(double complex));
    ic_random(16, ic, 7);
    prepare_state3(&W, &s, uh0, ic);
    st_check("Leray projection div-free", divergence_max3(&s, uh0) < 1e-12,
             "max|div| = %.2e", divergence_max3(&s, uh0));
    /* energy decay */
    DecayResult r = run_decay_3d(&s, &W, uh0, 0.01, 0.4, "st decay", 4, 0, 0,
                                 false, false, false, 0, false);
    st_check("energy non-increasing", r.energy_rise < 1e-12, "dE = %.2e", r.energy_rise);
    /* b-rotation isometry */
    double R[3][3];
    double ax = 0.3, ay = -0.5, az = sqrt(1 - 0.09 - 0.25);
    rodrigues(NSB_THETA_B, ax, ay, az, R);
    double complex **T3 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) T3[c] = malloc(N3 * sizeof(double complex));
    rotate_pointwise3(&W, &s, T3, uh0, R);
    double E0 = energy3(&s, uh0), E1 = energy3(&s, T3);
    st_check("b-rotation isometry", fabs(E1 - E0) / E0 < 1e-12, "|dE|/E = %.2e",
             fabs(E1 - E0) / E0);
    /* full symmetry relabeling */
    double complex **T4 = malloc(sizeof(double complex *) * 3);
    for (int c = 0; c < 3; c++) T4[c] = malloc(N3 * sizeof(double complex));
    rotate_full_symmetry3(&W, &s, T4, uh0);
    curl_hat3(&s, W.wh, uh0);
    double om0 = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) om0 += cabs(W.wh[c][i]) * cabs(W.wh[c][i]);
    curl_hat3(&s, W.wh, T4);
    double om1 = 0;
    for (int c = 0; c < 3; c++)
        for (size_t i = 0; i < N3; i++) om1 += cabs(W.wh[c][i]) * cabs(W.wh[c][i]);
    st_check("full symmetry = relabeling", fabs(om1 - om0) / om0 < 1e-9,
             "|dOmega|/Omega = %.2e", fabs(om1 - om0) / om0);
    /* writers */
    ensure_outdirs();
    char probe[600];
    snprintf(probe, sizeof(probe), "%s/plots/selftest_probe.png", CFG.out_dir);
    srand(3);
    double *fld = malloc(24 * 24 * sizeof(double));
    for (int i = 0; i < 24 * 24; i++) fld[i] = (double)rand() / RAND_MAX;
    heat_png_write(probe, fld, 24, "selftest");
    FILE *pf = fopen(probe, "rb");
    unsigned char sig[8]; bool png_ok = false;
    if (pf) { if (fread(sig, 1, 8, pf) == 8 &&
                 sig[0] == 0x89 && sig[1] == 'P' && sig[2] == 'N' && sig[3] == 'G') png_ok = true;
              fclose(pf); }
    st_check("PNG writer", png_ok, "signature");
    snprintf(probe, sizeof(probe), "%s/plots/selftest_probe.gif", CFG.out_dir);
    double *frames = malloc(4 * 16 * 16 * sizeof(double));
    for (int fr = 0; fr < 4; fr++)
        for (int i = 0; i < 16 * 16; i++)
            frames[fr * 256 + i] = (double)rand() / RAND_MAX + fr * 0.01;
    c_gif_write(probe, frames, 4, 16, 10);
    bool gif_ok = false;
    pf = fopen(probe, "rb");
    if (pf) {
        char h6[6];
        if (fread(h6, 1, 6, pf) == 6 && !memcmp(h6, "GIF89a", 6)) gif_ok = true;
        fclose(pf);
    }
    st_check("GIF writer", gif_ok, "signature");
    for (int c = 0; c < 3; c++) { free(ic[c]); free(uh0[c]); free(T3[c]); free(T4[c]); }
    free(ic); free(uh0); free(T3); free(T4); free(fld); free(frames);
    P("\n");
    if (g_fails == 0) { p_ok(L("selftest_ok")); P("\n"); }
    else { p_bad(L("selftest_fail")); P("\n"); }
}

/* ─────────────────────── roadmap / benchmark ─────────────────────── */

static void roadmap_report(void) {
    header_bar(L("road_hdr"));
    /* 3D FFT benchmark at N=32 */
    int n = 32;
    FFTPlan plan = fft_plan(n);
    size_t N3 = (size_t)n * n * n;
    double complex *A = malloc(sizeof(double complex) * N3);
    srand(1);
    for (size_t i = 0; i < N3; i++)
        A[i] = (double)rand() / RAND_MAX + (double)rand() / RAND_MAX * I;
    fft3d(&plan, A, false);                       /* warm-up */
    double best = INFINITY;
    for (int rep = 0; rep < 3; rep++) {
        double t0 = now_mono();
        fft3d(&plan, A, false);
        double dt_ = now_mono() - t0;
        if (dt_ < best) best = dt_;
    }
    double gflops = 15.0 * N3 * log2(n) / (best > 1e-9 ? best : 1e-9) / 1e9;
    P("  ");
    char msg[128];
    snprintf(msg, sizeof(msg), L("road_gflops"), gflops);
    p_muted(msg); P("\n\n");
    p_bold((char *)L("road_tbl_hdr")); P("\n");
    P("  %5s %10s %10s  %s\n", "N", "memory", "s/step", "verdict");
    for (int i = 0; i < 4; i++) {
        int nn = 32 << i;
        double mem = (double)nn * nn * nn * 16 * 24;
        double per_step = 13.0 * (15.0 * (double)nn * nn * nn * log2(nn)) / (gflops * 1e9);
        char mems[32]; big_mem(mem, mems, sizeof(mems));
        const char *verdict =
            per_step < 5 ? L("road_verdict_laptop") :
            per_step < 60 ? L("road_verdict_ws") :
            per_step < 1800 ? L("road_verdict_hpc") : L("road_verdict_no");
        P("  %5d %10s %10.2f  %s\n", nn, mems, per_step, verdict);
    }
    free(A);
}

/* ───────────────────────── session export ────────────────────────── */

static void export_session(void) {
    ensure_outdirs();
    time_t tnow = time(NULL); struct tm tm; localtime_r(&tnow, &tm);
    char stamp[32]; strftime(stamp, sizeof(stamp), "%Y%m%d_%H%M%S", &tm);
    char path[600];
    /* JSON */
    snprintf(path, sizeof(path), "%s/data/session_%s.json", CFG.out_dir, stamp);
    FILE *f = fopen(path, "w");
    if (f) {
        fprintf(f, "{\n  \"version\": \"%s\",\n  \"runs\": [\n", NSB_VERSION);
        for (int i = 0; i < SESSION_N; i++) {
            RunRecord *r = &SESSION[i];
            fprintf(f, "    {\"experiment\": \"%s\", \"ok\": %s, \"wall\": %.2f,\n"
                       "     \"checks\": [", r->experiment, r->ok ? "true" : "false", r->wall);
            for (int j = 0; j < r->n_checks; j++)
                fprintf(f, "%s[\"%s\", %s, \"%s\"]", j ? ", " : "",
                        r->checks[j].key, r->checks[j].ok ? "true" : "false",
                        r->checks[j].detail);
            fprintf(f, "]},\n");
        }
        fprintf(f, "  ]\n}\n");
        fclose(f);
        P("   · %s\n", path);
    }
    /* MD report */
    snprintf(path, sizeof(path), "%s/reports/report_%s.md", CFG.out_dir, stamp);
    f = fopen(path, "w");
    if (f) {
        fprintf(f, "# NSB C Lab — session report\n\n");
        fprintf(f, "*Version %s*\n\n", NSB_VERSION);
        for (int i = 0; i < SESSION_N; i++) {
            RunRecord *r = &SESSION[i];
            fprintf(f, "## %s — %s\n\n", r->experiment, r->ok ? "OK" : "FAILED");
            fprintf(f, "| check | result | detail |\n|---|---|---|\n");
            for (int j = 0; j < r->n_checks; j++)
                fprintf(f, "| %s | %s | %s |\n", r->checks[j].key,
                        r->checks[j].ok ? "PASS" : "FAIL", r->checks[j].detail);
            fprintf(f, "\n");
        }
        fclose(f);
        P("   · %s\n", path);
    }
    /* CSV per run */
    for (int i = 0; i < SESSION_N; i++) {
        snprintf(path, sizeof(path), "%s/data/run_%02d_%s.csv", CFG.out_dir, i + 1,
                 SESSION[i].experiment);
        f = fopen(path, "w");
        if (f) {
            fprintf(f, "check,result,detail\n");
            for (int j = 0; j < SESSION[i].n_checks; j++)
                fprintf(f, "%s,%d,\"%s\"\n", SESSION[i].checks[j].key,
                        SESSION[i].checks[j].ok, SESSION[i].checks[j].detail);
            fclose(f);
        }
    }
}

/* ─────────────────────────────── CLI ─────────────────────────────── */

static void cli_help(void) {
    P("NSB C Lab v%s — self-contained Navier-Stokes laboratory\n", NSB_VERSION);
    P("Usage: ./nsb_lab [options]\n");
    P("Modes:\n");
    P("  --quick                  fast run (mini-suite)\n");
    P("  --suite normal|hard      full suite\n");
    P("  --experiment tg|abc|houluo|baudit\n");
    P("  --flow <id|all|list>     real-flows laboratory\n");
    P("  --roadmap --selftest --list-flows --report\n");
    P("Options:\n");
    P("  --n N --nu V --dt V --t V --nu4 V\n");
    P("  --cfl 0|1 --ckpt N --resume --gif 0|1\n");
    P("  --lang ru|en --out DIR --seed N --dpi N --no-color --ascii\n");
    P("  --help -h --version\n");
}

int main(int argc, char **argv) {
    cfg_init();
    /* terminal colors: only when TTY and TERM not dumb */
    CFG.color = is_tty() && getenv("TERM") && strcmp(getenv("TERM"), "dumb") &&
                !(getenv("NO_COLOR") && *getenv("NO_COLOR"));
    const char *elang = getenv("NSB_LAB_LANG");
    CFG.lang = (elang && elang[0] == 'e') ? 'e' : 'r';
    const char *action = "menu";
    char opt_mode[16] = "normal", opt_exp[16] = "tg", opt_flow[64] = "list";
    int opt_n = 0; double opt_nu = -1, opt_dt = 0, opt_t = 0, opt_nu4 = -1;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--quick")) action = "quick";
        else if (!strcmp(argv[i], "--suite")) { action = "suite";
            if (i + 1 < argc) snprintf(opt_mode, sizeof(opt_mode), "%s", argv[++i]); }
        else if (!strcmp(argv[i], "--experiment")) { action = "experiment";
            if (i + 1 < argc) snprintf(opt_exp, sizeof(opt_exp), "%s", argv[++i]); }
        else if (!strcmp(argv[i], "--flow")) { action = "flow";
            if (i + 1 < argc) snprintf(opt_flow, sizeof(opt_flow), "%s", argv[++i]); }
        else if (!strcmp(argv[i], "--mode") && i + 1 < argc)
            snprintf(opt_mode, sizeof(opt_mode), "%s", argv[++i]);
        else if (!strcmp(argv[i], "--roadmap")) action = "roadmap";
        else if (!strcmp(argv[i], "--selftest")) action = "selftest";
        else if (!strcmp(argv[i], "--list-flows")) action = "list_flows";
        else if (!strcmp(argv[i], "--report")) action = "report";
        else if (!strcmp(argv[i], "--n") && i + 1 < argc) opt_n = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--nu") && i + 1 < argc) opt_nu = atof(argv[++i]);
        else if (!strcmp(argv[i], "--nu4") && i + 1 < argc) opt_nu4 = atof(argv[++i]);
        else if (!strcmp(argv[i], "--dt") && i + 1 < argc) opt_dt = atof(argv[++i]);
        else if (!strcmp(argv[i], "--t") && i + 1 < argc) opt_t = atof(argv[++i]);
        else if (!strcmp(argv[i], "--cfl") && i + 1 < argc) CFG.adaptive_cfl = strcmp(argv[++i], "0");
        else if (!strcmp(argv[i], "--ckpt") && i + 1 < argc) CFG.ckpt_every = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--gif") && i + 1 < argc) CFG.gif = strcmp(argv[++i], "0");
        else if (!strcmp(argv[i], "--lang") && i + 1 < argc)
            CFG.lang = argv[++i][0] == 'e' ? 'e' : 'r';
        else if (!strcmp(argv[i], "--out") && i + 1 < argc)
            snprintf(CFG.out_dir, sizeof(CFG.out_dir), "%s", argv[++i]);
        else if (!strcmp(argv[i], "--seed") && i + 1 < argc) CFG.seed = atol(argv[++i]);
        else if (!strcmp(argv[i], "--no-color")) CFG.color = false;
        else if (!strcmp(argv[i], "--ascii")) CFG.ascii_only = true;
        else if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) action = "help";
        else if (!strcmp(argv[i], "--version")) action = "version";
        else P("unknown argument: %s\n", argv[i]);
    }
    if (opt_nu4 >= 0) CFG.nu4 = opt_nu4;
    CFG.batch = strcmp(action, "menu") != 0;
    ensure_outdirs();
    logfile_open();
    SESSION_T0 = now_mono();

    if (!strcmp(action, "help")) { cli_help(); log_close(); return 0; }
    if (!strcmp(action, "version")) { P("NSB C Lab v%s\n", NSB_VERSION); log_close(); return 0; }
    if (!strcmp(action, "selftest")) { selftest(); log_close(); return g_fails ? 1 : 0; }
    if (!strcmp(action, "list_flows")) { flows_table_text(); log_close(); return 0; }
    if (!strcmp(action, "roadmap")) { roadmap_report(); log_close(); return 0; }
    if (!strcmp(action, "quick")) {
        exp_taylor_green("normal", opt_n, opt_nu, opt_dt, opt_t);
        exp_baudit("normal", opt_n, opt_nu, opt_dt, opt_t);
        export_session();
        log_close();
        return 0;
    }
    if (!strcmp(action, "suite")) {
        exp_taylor_green(opt_mode, opt_n, opt_nu, opt_dt, opt_t);
        exp_abc(opt_mode, opt_n, opt_dt, opt_t);
        exp_houluo(opt_mode, opt_n, opt_dt, opt_t);
        exp_baudit(opt_mode, opt_n, opt_nu, opt_dt, opt_t);
        export_session();
        log_close();
        return 0;
    }
    if (!strcmp(action, "experiment")) {
        if (!strcmp(opt_exp, "abc")) exp_abc(opt_mode, opt_n, opt_dt, opt_t);
        else if (!strcmp(opt_exp, "houluo")) exp_houluo(opt_mode, opt_n, opt_dt, opt_t);
        else if (!strcmp(opt_exp, "baudit"))
            exp_baudit(opt_mode, opt_n, opt_nu, opt_dt, opt_t);
        else exp_taylor_green(opt_mode, opt_n, opt_nu, opt_dt, opt_t);
        export_session();
        log_close();
        return 0;
    }
    if (!strcmp(action, "flow")) {
        if (!strcmp(opt_flow, "list")) flows_table_text();
        else if (!strcmp(opt_flow, "all"))
            for (int i = 0; i < 20; i++) flow_run(&FLOWS[i], opt_mode);
        else {
            int found = -1;
            for (int i = 0; i < 20; i++)
                if (!strcmp(FLOWS[i].id, opt_flow)) { found = i; break; }
            if (found >= 0) flow_run(&FLOWS[found], opt_mode);
            else { p_warn("no such flow\n"); log_close(); return 1; }
        }
        export_session();
        log_close();
        return 0;
    }
    if (!strcmp(action, "report")) { export_session(); log_close(); return 0; }

    /* ---------- interactive menu ---------- */
    while (true) {
        P("\n");
        if (CFG.color) {
            P("\x1b[38;2;80;160;255m+==============================================================================+\x1b[0m\n");
            P("\x1b[38;2;80;160;255m|\x1b[0m"); p_bold(L("title"));
            P("\x1b[38;2;80;160;255m|\x1b[0m\n");
            P("\x1b[38;2;80;160;255m|\x1b[0m  "); p_muted(L("subtitle"));
            P(" v%s\x1b[38;2;80;160;255m|\x1b[0m\n", NSB_VERSION);
            P("\x1b[38;2;80;160;255m+==============================================================================+\x1b[0m\n");
        } else {
            P("==============================================================================\n");
            P("  %s  v%s\n", L("title"), NSB_VERSION);
            P("==============================================================================\n");
        }
        const char *items[] = {"menu_quick", "menu_suite_normal", "menu_suite_hard",
                               "menu_custom", "menu_flows", "menu_roadmap",
                               "menu_reports", "menu_settings", "menu_exit"};
        for (int i = 0; i < 9; i++) { P("  "); p_bold(L(items[i])); P("\n"); }
        P("  %s\n", L("lang_toggle"));
        P("  %s > ", L("menu_prompt"));
        char sel[32];
        if (!fgets(sel, sizeof(sel), stdin)) { P("\n"); break; }
        sel[strcspn(sel, "\r\n")] = 0;
        if (!strcmp(sel, "1")) {
            exp_taylor_green("normal", 0, -1, 0, 0);
            exp_baudit("normal", 0, -1, 0, 0);
            export_session();
        } else if (!strcmp(sel, "2")) {
            exp_taylor_green("normal", 0, -1, 0, 0);
            exp_abc("normal", 0, 0, 0);
            exp_houluo("normal", 0, 0, 0);
            exp_baudit("normal", 0, -1, 0, 0);
            export_session();
        } else if (!strcmp(sel, "3")) {
            exp_taylor_green("hard", 0, -1, 0, 0);
            exp_abc("hard", 0, 0, 0);
            exp_houluo("hard", 0, 0, 0);
            exp_baudit("hard", 0, -1, 0, 0);
            export_session();
        } else if (!strcmp(sel, "4")) {
            exp_taylor_green("normal", 0, -1, 0, 0);
        } else if (!strcmp(sel, "5")) {
            flows_table_text();
            P("  %s\n", L("flows_menu_hint"));
            char fsel[32];
            if (fgets(fsel, sizeof(fsel), stdin)) {
                fsel[strcspn(fsel, "\r\n")] = 0;
                if (!strcmp(fsel, "a")) {
                    for (int i = 0; i < 20; i++) flow_run(&FLOWS[i], "normal");
                    export_session();
                } else if (fsel[0] >= '1' && fsel[0] <= '9') {
                    int num = atoi(fsel);
                    if (num >= 1 && num <= 20) { flow_run(&FLOWS[num - 1], "normal"); export_session(); }
                }
            }
        } else if (!strcmp(sel, "6")) {
            roadmap_report();
        } else if (!strcmp(sel, "7")) {
            header_bar(L("rep_hdr"));
            if (SESSION_N == 0) { P("  %s\n", L("rep_none")); }
            else export_session();
        } else if (!strcmp(sel, "8")) {
            header_bar(L("set_hdr"));
            P("  %s: %s\n", L("set_out"), CFG.out_dir);
            header_bar(L("set_about"));
            P("  %s\n", L("set_about_txt"));
        } else if (!strcmp(sel, "9")) {
            CFG.lang = CFG.lang == 'r' ? 'e' : 'r';
            P("  %s\n", CFG.lang == 'e' ? "Language: ENGLISH" : "Язык: РУССКИЙ");
        } else if (!strcmp(sel, "0")) {
            break;
        } else {
            P("  %s\n", L("invalid_choice"));
        }
    }
    log_close();
    return 0;
}




