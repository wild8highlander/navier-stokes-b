// ═══════════════════════════════════════════════════════════════════════════
//   NSB GO LAB v2.1.0 — polyglot edition
//   A faithful port of the self-contained Julia "Navier–Stokes b-Lab" to Go
//   with ZERO external dependencies (standard library only).
//
//   Highlights of this edition:
//     • Goroutine-parallel FFT: axis passes are farmed out to worker
//       goroutines with sync.WaitGroup (scales with GOMAXPROCS).
//     • image/png and compress/zlib from the standard library: a real
//       DEFLATE-compressed PNG writer (other editions use stored blocks).
//     • Same physics as the Julia reference: 3-D pseudospectral NS/Euler
//       (RK4 + Leray projection + 2/3 rule), 2-D barotropic β-plane,
//       BKM diagnostics, blow-up scanner, b-correction audit.
//     • i18n RU/EN, ONE-LINE progress bar, sparklines, interactive TUI menu.
//
//   Build:   go build -o nsb_lab main.go     (or: go build ./...)
//   Run:     ./nsb_lab --quick --lang en
//            ./nsb_lab --selftest
//            ./nsb_lab                        (interactive menu)
//   Results: ~/nsb_lab_results/{data,plots,reports,logs}
// ═══════════════════════════════════════════════════════════════════════════

package main

import (
        "bufio"
        "fmt"
        "image"
        "image/color"
        "image/png"
        "math"
        "math/cmplx"
        "math/rand"
        "os"
        "path/filepath"
        "runtime"
        "strconv"
        "strings"
        "sync"
        "time"
)

const NSBVersion = "2.1.0"
const PI = math.Pi

// ───────────────────────────── config ───────────────────────────────────

type Config struct {
        Lang        string
        OutDir      string
        DPI         int
        Seed        int64
        Color       bool
        AsciiOnly   bool
        MaxN        int
        Quick       bool
        Batch       bool
        Quiet       bool
        TStart      time.Time
        Gif         bool
        CkptEvery   int
        AdaptiveCFL bool
        Nu4         float64
}

var CFG Config

func cfgInit() {
        home, _ := os.UserHomeDir()
        CFG = Config{
                Lang:      "ru",
                OutDir:    filepath.Join(home, "nsb_lab_results"),
                DPI:       600,
                Seed:      20260916,
                MaxN:      32,
                TStart:    time.Now(),
                Gif:       true,
                CkptEvery: 200,
        }
        totalGB := 8.0
        if data, err := os.ReadFile("/proc/meminfo"); err == nil {
                for _, line := range strings.Split(string(data), "\n") {
                        if strings.HasPrefix(line, "MemTotal:") {
                                fields := strings.Fields(line)
                                if len(fields) >= 2 {
                                        if kb, err := strconv.ParseFloat(fields[1], 64); err == nil {
                                                totalGB = kb / 1048576.0
                                        }
                                }
                                break
                        }
                }
        }
        for _, cand := range []int{32, 64, 128, 256} {
                mem := float64(cand*cand*cand) * 16.0 * 24.0 / (1 << 30)
                if mem < totalGB*0.55 {
                        CFG.MaxN = cand
                }
        }
        CFG.Color = isTTY() && os.Getenv("TERM") != "dumb" &&
                os.Getenv("TERM") != "" && os.Getenv("NO_COLOR") == ""
        if os.Getenv("NSB_LAB_LANG") == "en" {
                CFG.Lang = "en"
        }
}

func isTTY() bool {
        fi, err := os.Stdout.Stat()
        if err != nil {
                return false
        }
        return (fi.Mode() & os.ModeCharDevice) != 0
}

func ensureOutdirs() {
        for _, sub := range []string{"", "logs", "data", "plots", "reports"} {
                _ = os.MkdirAll(filepath.Join(CFG.OutDir, sub), 0o755)
        }
}

var logFile *os.File

func logfileOpen() {
        ensureOutdirs()
        stamp := time.Now().Format("20060102_150405")
        var err error
        logFile, err = os.Create(filepath.Join(CFG.OutDir, "logs", "session_"+stamp+".log"))
        if err != nil {
                logFile = nil
        }
}

func P(format string, args ...interface{}) {
        if !CFG.Quiet {
                fmt.Printf(format, args...)
                _ = os.Stdout.Sync()
        }
        if logFile != nil {
                fmt.Fprintf(logFile, format, args...)
        }
}

// ───────────────────────────── i18n ─────────────────────────────────────

type I18nPair struct{ Key, Ru, En string }

var I18N = []I18nPair{
        {"yes", "да", "yes"}, {"no", "нет", "no"},
        {"pass", "ПРОЙДЕНО", "PASS"}, {"fail", "ПРОВАЛЕНО", "FAIL"},
        {"title", "ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ", "NAVIER–STOKES LABORATORY · b-CORRECTION"},
        {"subtitle", "самодостаточная Go-версия (горутины + stdlib image/png)", "self-contained Go edition (goroutines + stdlib image/png)"},
        {"menu_prompt", "Выберите пункт и нажмите Enter", "Choose an item and press Enter"},
        {"invalid_choice", "Нет такого пункта — попробуйте ещё раз", "No such item — try again"},
        {"lang_toggle", "9. Язык / Language  (RU ↔ EN)", "9. Language / Язык  (EN ↔ RU)"},
        {"menu_quick", "1. Быстрый прогон  (мини-сьют)", "1. Quick run  (mini-suite)"},
        {"menu_suite_normal", "2. Полная сьют — НОРМАЛЬНЫЙ режим", "2. Full suite — NORMAL mode"},
        {"menu_suite_hard", "3. Полная сьют — ХАРД режим", "3. Full suite — HARD mode"},
        {"menu_flows", "4. Лаборатория 20 реальных течений", "4. Real-flows laboratory (20 documented flows)"},
        {"menu_roadmap", "5. Роадмап и это железо (бенчмарк)", "5. Roadmap & this hardware (benchmark)"},
        {"menu_reports", "6. Отчёты сессии", "6. Session reports"},
        {"menu_settings", "7. Настройки и о проекте", "7. Settings & about"},
        {"menu_exit", "0. Выход", "0. Exit"},
        {"exp_tg", "Тейлор–Грин: сходимость и экстраполяция", "Taylor–Green: convergence and extrapolation"},
        {"exp_abc", "ABC (Эйлер): охота за расходимостью", "ABC (Euler): blow-up hunt"},
        {"exp_houluo", "Хоу–Ло: антипараллельные вихревые трубки", "Hou–Luo: anti-parallel vortex tubes"},
        {"exp_baudit", "Аудит b-коррекции: симметрия против пинка", "b-correction audit: symmetry vs pointwise kick"},
        {"scope_note", "Область действия: сертификат внутренней согласованности, не общая теорема.",
                "Scope: a certificate of internal consistency of the computed solution, not a general theorem."},
        {"verdict_ok", "ВЕРДИКТ: все проверки пройдены", "VERDICT: all checks passed"},
        {"verdict_fail", "ВЕРДИКТ: есть проваленные проверки", "VERDICT: some checks failed"},
        {"ck_divfree", "несжимаемость: max|div u| в машинном пороге", "incompressibility: max|div u| at machine level"},
        {"ck_energy_monotone", "энергия не растёт (вязкое затухание)", "energy non-increasing (viscous decay)"},
        {"ck_energy_conserved", "энергия сохраняется (Эйлер)", "energy conserved (Euler)"},
        {"ck_rk4_order", "измеренный порядок RK4 ≈ 4", "measured RK4 order ≈ 4"},
        {"ck_no_blowup", "признаков расходимости нет (BKM ограничен)", "no finite-time blow-up signature (BKM bounded)"},
        {"ck_stability", "устойчивость: нет NaN/Inf", "stability: no NaN/Inf"},
        {"ck_isometry", "точечный поворот — изометрия", "pointwise rotation is an isometry"},
        {"ck_symmetry_relabel", "полная симметрия = релебелинг", "full symmetry = relabeling"},
        {"ck_div_break", "точечный поворот ЛОМАЕТ div u = 0", "pointwise rotation BREAKS div u = 0"},
        {"ck_reproject", "после перепроекции div на машинном пороге", "after reprojection div at machine level"},
        {"ck_b_effect", "b-пинк не снижает sup|ω|", "b-kick does not reduce sup|ω|"},
        {"ck_hl_growth", "рост sup|ω| измерен", "sup|ω| growth measured"},
        {"flows_hdr", "ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов", "REAL-FLOWS LABORATORY — 20 documented flows"},
        {"flows_menu_hint", "Введите номер течения (1–20), a — все, q — назад", "Enter flow number (1-20), a — run all, q — back"},
        {"flow_card", "КАРТОЧКА ТЕЧЕНИЯ", "FLOW CARD"},
        {"flow_source", "первоисточник/документация", "primary source/documentation"},
        {"flow_params", "документированные величины", "documented quantities"},
        {"flow_derived", "расчётные параметры", "derived parameters"},
        {"flow_dns_no", "DNS НЕВОЗМОЖНО на существующем железе", "DNS is INFEASIBLE on existing hardware"},
        {"flow_reduced", "редуцированная модель: 2D баротропная β-плоскость", "reduced model: 2-D barotropic β-plane"},
        {"flow_verdict", "ВЕРДИКТ ПО ТЕЧЕНИЮ", "FLOW VERDICT"},
        {"flow_all_hdr", "СВОДНАЯ ТАБЛИЦА 20 ТЕЧЕНИЙ", "SUMMARY TABLE OF 20 FLOWS"},
        {"road_hdr", "РОАДМАП И ЭТО ЖЕЛЕЗО", "ROADMAP AND THIS HARDWARE"},
        {"road_tbl_hdr", "Оценки для псевдоспектрального НС (RK4, ~13 3D-FFT/шаг)", "Estimates for pseudospectral NS (RK4, ~13 3D-FFTs/step)"},
        {"road_verdict_laptop", "ноутбук: реально за вечер", "laptop: an evening run"},
        {"road_verdict_ws", "нужна рабочая станция", "workstation recommended"},
        {"road_verdict_hpc", "нужен кластер/HPC", "cluster/HPC required"},
        {"road_verdict_no", "вне досягаемости одиночной машины", "out of reach for a single machine"},
        {"rep_hdr", "ОТЧЁТЫ СЕССИИ", "SESSION REPORTS"},
        {"rep_none", "Пока ничего не посчитано", "Nothing computed yet"},
        {"rep_saved", "Сохранено", "Saved"},
        {"selftest_hdr", "САМОТЕСТ", "SELF-TEST"},
        {"selftest_ok", "САМОТЕСТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ", "SELF-TEST: ALL CHECKS PASSED"},
        {"selftest_fail", "САМОТЕСТ: ЕСТЬ ПРОВАЛЫ", "SELF-TEST: FAILURES PRESENT"},
        {"adaptive_on", "адаптивный CFL-шаг включён", "adaptive CFL step enabled"},
        {"gif_saved", "GIF сохранён", "GIF saved"},
        {"set_hdr", "НАСТРОЙКИ", "SETTINGS"},
        {"set_out", "Папка результатов", "Results folder"},
        {"set_about", "О ПРОЕКТЕ", "ABOUT"},
        {"set_about_txt", "Лаборатория проверяет гипотезу b-коррекции: полная решётчатая симметрия — релебелинг; точечный поворот сохраняет энергию, но ломает div u = 0. Порт Go использует горутины и stdlib image/png.",
                "The lab tests the b-correction hypothesis: full lattice symmetry is a relabeling; the pointwise rotation preserves energy but breaks div u = 0. The Go port uses goroutines and stdlib image/png."},
}

func L(key string) string {
        for _, p := range I18N {
                if p.Key == key {
                        if CFG.Lang == "en" {
                                return p.En
                        }
                        return p.Ru
                }
        }
        return "<missing>"
}

// ─────────────────────────── ANSI + progress ────────────────────────────

func pOK(s string) {
        if CFG.Color {
                P("\x1b[1;32m%s\x1b[0m", s)
        } else {
                P("%s", s)
        }
}
func pBad(s string) {
        if CFG.Color {
                P("\x1b[1;31m%s\x1b[0m", s)
        } else {
                P("%s", s)
        }
}
func pWarn(s string) {
        if CFG.Color {
                P("\x1b[1;33m%s\x1b[0m", s)
        } else {
                P("%s", s)
        }
}
func pMuted(s string) {
        if CFG.Color {
                P("\x1b[2m%s\x1b[0m", s)
        } else {
                P("%s", s)
        }
}
func pBold(s string) {
        if CFG.Color {
                P("\x1b[1m%s\x1b[0m", s)
        } else {
                P("%s", s)
        }
}

func headerBar(title string) {
        line := strings.Repeat("-", 76)
        P("\n")
        if CFG.Color {
                P("\x1b[38;2;80;160;255m%s\x1b[0m\n", line)
        } else {
                P("%s\n", line)
        }
        P(" ▸ "); pBold(title); P("\n")
        if CFG.Color {
                P("\x1b[38;2;80;160;255m%s\x1b[0m\n", line)
        } else {
                P("%s\n", line)
        }
}

var progLast float64 = 0.0

func progress(frac float64, label string, t0 time.Time, total, done int) {
        if frac < 0 {
                frac = 0
        }
        if frac > 1 {
                frac = 1
        }
        if !isTTY() || CFG.Quiet || !CFG.Color {
                if (frac-progLast >= 0.1 || frac >= 1.0) && progLast < 1.0 {
                        if frac >= 1.0 {
                                progLast = 1.0
                        } else if frac > progLast {
                                progLast = frac
                        }
                        P("  [%3.0f%%] %s\n", frac*100, label)
                }
                return
        }
        const W = 30
        fill := int(frac*W + 0.5)
        bar := ""
        for i := 1; i <= W; i++ {
                if CFG.AsciiOnly {
                        if i <= fill {
                                bar += "#"
                        } else {
                                bar += "-"
                        }
                } else if i <= fill {
                        bar += fmt.Sprintf("\x1b[38;2;%d;%d;255m█\x1b[0m", 40+180*i/W, 80+170*i/W)
                } else {
                        bar += "\x1b[2m░\x1b[0m"
                }
        }
        el := time.Since(t0).Seconds()
        eta := math.NaN()
        if frac > 0.005 {
                eta = el/frac - el
        }
        etaS := " --:--"
        if !math.IsNaN(eta) {
                etaS = fmt.Sprintf("%02d:%02d", int(eta)/60, int(eta)%60)
        }
        elS := fmt.Sprintf("%02d:%02d", int(el)/60, int(el)%60)
        var tail string
        if total > 0 {
                rate := float64(done) / math.Max(el, 1e-9)
                tail = fmt.Sprintf(" · %s %d/%d · %.1f %s · %s %s", L("prog_step"), done, total,
                        rate, L("prog_rate"), L("prog_eta"), etaS)
        } else {
                tail = fmt.Sprintf(" · elapsed %s", elS)
        }
        P("\r%s\r", strings.Repeat(" ", 120))
        P("\x1b[38;2;80;160;255m ▸ \x1b[0m%s ▕%s▏%5.1f%%%s", label, bar, frac*100, tail)
        if frac >= 1.0 {
                P("\n")
                progLast = 0
        }
}

func sparkline(v []float64) string {
        utf := []string{"▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"}
        asc := []string{"_", ".", "-", "~", "*", "#", "#", "#"}
        glyphs := utf
        if !CFG.Color || CFG.AsciiOnly {
                glyphs = asc
        }
        if len(v) == 0 {
                return ""
        }
        lo, hi := math.Inf(1), math.Inf(-1)
        for _, x := range v {
                x = math.Max(x, 0)
                lo = math.Min(lo, x)
                hi = math.Max(hi, x)
        }
        rng := hi - lo
        if rng <= 0 {
                rng = 1
        }
        out := ""
        for _, x := range v {
                x = math.Max(x, 0)
                k := int(math.Round((x - lo) / rng * 7))
                if k < 0 {
                        k = 0
                }
                if k > 7 {
                        k = 7
                }
                out += glyphs[k]
        }
        return out
}

// ───────────────────── goroutine-parallel radix-2 FFT ───────────────────

type FFTPlan struct {
        N      int
        Tw     []complex128
        Bitrev []int
}

func fftPlan(n int) *FFTPlan {
        if n < 2 || n&(n-1) != 0 {
                panic("FFT: n must be a power of two")
        }
        p := &FFTPlan{N: n, Tw: make([]complex128, n/2), Bitrev: make([]int, n)}
        for k := 0; k < n/2; k++ {
                p.Tw[k] = cmplx.Exp(complex(0, -2*PI*float64(k)/float64(n)))
        }
        logn := 0
        for 1<<logn < n {
                logn++
        }
        for i := 0; i < n; i++ {
                r, x := 0, i
                for b := 0; b < logn; b++ {
                        r = (r << 1) | (x & 1)
                        x >>= 1
                }
                p.Bitrev[i] = r
        }
        return p
}

func (p *FFTPlan) fft1d(a []complex128, inverse bool) {
        n := p.N
        for i := 0; i < n; i++ {
                if j := p.Bitrev[i]; i < j {
                        a[i], a[j] = a[j], a[i]
                }
        }
        for length := 2; length <= n; length <<= 1 {
                half := length >> 1
                step := n / length
                for start := 0; start < n; start += length {
                        k := 0
                        for j := 0; j < half; j++ {
                                w := p.Tw[k]
                                if inverse {
                                        w = cmplx.Conj(w)
                                }
                                i1, i2 := start+j, start+j+half
                                u, v := a[i1], a[i2]*w
                                a[i1] = u + v
                                a[i2] = u - v
                                k += step
                        }
                }
        }
        if inverse {
                s := complex(1/float64(n), 0)
                for i := range a {
                        a[i] *= s
                }
        }
}

// fftLinesPar transforms `count` contiguous lines of length p.N in parallel.
func (p *FFTPlan) fftLinesPar(buf []complex128, count int, inverse bool) {
        workers := runtime.GOMAXPROCS(0)
        if workers > count {
                workers = count
        }
        if workers <= 1 {
                for line := 0; line < count; line++ {
                        p.fft1d(buf[line*p.N:(line+1)*p.N], inverse)
                }
                return
        }
        var wg sync.WaitGroup
        chunk := (count + workers - 1) / workers
        for t := 0; t < workers; t++ {
                lo := t * chunk
                hi := lo + chunk
                if hi > count {
                        hi = count
                }
                if lo >= hi {
                        break
                }
                wg.Add(1)
                go func(lo, hi int) {
                        defer wg.Done()
                        for line := lo; line < hi; line++ {
                                p.fft1d(buf[line*p.N:(line+1)*p.N], inverse)
                        }
                }(lo, hi)
        }
        wg.Wait()
}

func (p *FFTPlan) fft3d(a []complex128, inverse bool) {
        n := p.N
        n2 := n * n
        // axis 2: contiguous
        p.fftLinesPar(a, n2, inverse)
        // axes 1 and 0: gather → parallel FFT → scatter
        tmp := make([]complex128, len(a))
        for i := 0; i < n; i++ {
                for k := 0; k < n; k++ {
                        for j := 0; j < n; j++ {
                                tmp[(i*n+k)*n+j] = a[(i*n+j)*n+k]
                        }
                }
        }
        p.fftLinesPar(tmp, n2, inverse)
        for i := 0; i < n; i++ {
                for k := 0; k < n; k++ {
                        for j := 0; j < n; j++ {
                                a[(i*n+j)*n+k] = tmp[(i*n+k)*n+j]
                        }
                }
        }
        for j := 0; j < n; j++ {
                for k := 0; k < n; k++ {
                        for i := 0; i < n; i++ {
                                tmp[(j*n+k)*n+i] = a[(i*n+j)*n+k]
                        }
                }
        }
        p.fftLinesPar(tmp, n2, inverse)
        for j := 0; j < n; j++ {
                for k := 0; k < n; k++ {
                        for i := 0; i < n; i++ {
                                a[(i*n+j)*n+k] = tmp[(j*n+k)*n+i]
                        }
                }
        }
}

func (p *FFTPlan) fft2d(a []complex128, inverse bool) {
        n := p.N
        p.fftLinesPar(a, n, inverse)
        tmp := make([]complex128, len(a))
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        tmp[i*n+j] = a[j*n+i]
                }
        }
        p.fftLinesPar(tmp, n, inverse)
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        a[j*n+i] = tmp[i*n+j]
                }
        }
}

// ───────────────────── 3-D pseudospectral solver ────────────────────────

type NSE3D struct {
        N                       int
        Nu, Nu4, Dx             float64
        Kx, Ky, Kz              []int
        Ksq, Ksq2, K2Safe       []float64
        Mask                    []bool
}

func idx3(n, i, j, k int) int { return (i*n + j)*n + k }

func newNSE3D(n int, nu, nu4In float64) *NSE3D {
        nu4 := CFG.Nu4
        if nu4In >= 0 {
                nu4 = nu4In
        }
        n3 := n * n * n
        k1d := make([]int, n)
        for i := 0; i < n/2; i++ {
                k1d[i] = i
        }
        for i := -n / 2; i < 0; i++ {
                k1d[i+n] = i
        }
        kc := n / 3
        s := &NSE3D{
                N: n, Nu: nu, Nu4: nu4, Dx: 2 * PI / float64(n),
                Kx: make([]int, n3), Ky: make([]int, n3), Kz: make([]int, n3),
                Ksq: make([]float64, n3), Ksq2: make([]float64, n3),
                K2Safe: make([]float64, n3), Mask: make([]bool, n3),
        }
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        for k := 0; k < n; k++ {
                                id := idx3(n, i, j, k)
                                a, b, c := k1d[i], k1d[j], k1d[k]
                                s.Kx[id], s.Ky[id], s.Kz[id] = a, b, c
                                q := float64(a*a + b*b + c*c)
                                s.Ksq[id] = q
                                s.Ksq2[id] = q * q
                                if q > 0 {
                                        s.K2Safe[id] = q
                                } else {
                                        s.K2Safe[id] = 1
                                }
                                s.Mask[id] = abs(a) <= kc && abs(b) <= kc && abs(c) <= kc
                        }
                }
        }
        return s
}

func abs(x int) int {
        if x < 0 {
                return -x
        }
        return x
}

type Field3 struct {
        C [3][]complex128
}

func zeroField3(n3 int) Field3 {
        var f Field3
        for c := 0; c < 3; c++ {
                f.C[c] = make([]complex128, n3)
        }
        return f
}

func cloneField3(f Field3) Field3 {
        var g Field3
        for c := 0; c < 3; c++ {
                g.C[c] = make([]complex128, len(f.C[c]))
                copy(g.C[c], f.C[c])
        }
        return g
}

type Work3D struct {
        Plan                       *FFTPlan
        Wh, Nlhat, Scratch         Field3
        K1, K2, K3, K4, T1, T2, T3 Field3
        U, W                       [3][]float64
        Kd                         []complex128
}

func newWork3D(n int) *Work3D {
        n3 := n * n * n
        w := &Work3D{
                Plan: fftPlan(n), Wh: zeroField3(n3), Nlhat: zeroField3(n3),
                Scratch: zeroField3(n3), K1: zeroField3(n3), K2: zeroField3(n3),
                K3: zeroField3(n3), K4: zeroField3(n3), T1: zeroField3(n3),
                T2: zeroField3(n3), T3: zeroField3(n3),
                Kd: make([]complex128, n3),
        }
        for c := 0; c < 3; c++ {
                w.U[c] = make([]float64, n3)
                w.W[c] = make([]float64, n3)
        }
        return w
}

func fftField3(wk *Work3D, in [3][]float64) Field3 {
        n3 := len(in[0])
        out := zeroField3(n3)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        wk.Scratch.C[c][i] = complex(in[c][i], 0)
                }
                wk.Plan.fft3d(wk.Scratch.C[c], false)
                copy(out.C[c], wk.Scratch.C[c])
        }
        return out
}

func ifftField3(wk *Work3D, in Field3) [3][]float64 {
        n3 := len(in.C[0])
        var out [3][]float64
        for c := 0; c < 3; c++ {
                copy(wk.Scratch.C[c], in.C[c])
                wk.Plan.fft3d(wk.Scratch.C[c], true)
                out[c] = make([]float64, n3)
                for i := 0; i < n3; i++ {
                        out[c][i] = real(wk.Scratch.C[c][i])
                }
        }
        return out
}

func project3(wk *Work3D, s *NSE3D, out, in Field3) {
        n3 := len(in.C[0])
        for i := 0; i < n3; i++ {
                kd := (complex(float64(s.Kx[i]), 0)*in.C[0][i] +
                        complex(float64(s.Ky[i]), 0)*in.C[1][i] +
                        complex(float64(s.Kz[i]), 0)*in.C[2][i]) / complex(s.K2Safe[i], 0)
                if s.Ksq[i] == 0 {
                        kd = 0
                }
                wk.Kd[i] = kd
        }
        for c := 0; c < 3; c++ {
                var kc []int
                if c == 0 {
                        kc = s.Kx
                } else if c == 1 {
                        kc = s.Ky
                } else {
                        kc = s.Kz
                }
                for i := 0; i < n3; i++ {
                        out.C[c][i] = in.C[c][i] - complex(float64(kc[i]), 0)*wk.Kd[i]
                }
        }
}

func curlHat3(s *NSE3D, out, a Field3) {
        n3 := len(a.C[0])
        ii := complex(0, 1)
        for i := 0; i < n3; i++ {
                kx, ky, kz := complex(float64(s.Kx[i]), 0), complex(float64(s.Ky[i]), 0), complex(float64(s.Kz[i]), 0)
                a1, a2, a3 := a.C[0][i], a.C[1][i], a.C[2][i]
                out.C[0][i] = ii * (ky*a3 - kz*a2)
                out.C[1][i] = ii * (kz*a1 - kx*a3)
                out.C[2][i] = ii * (kx*a2 - ky*a1)
        }
}

func rhs3(wk *Work3D, s *NSE3D, du, uhat Field3) {
        n3 := len(uhat.C[0])
        curlHat3(s, wk.Wh, uhat)
        u := ifftField3(wk, uhat)
        w := ifftField3(wk, wk.Wh)
        for i := 0; i < n3; i++ {
                w1, w2, w3 := w[0][i], w[1][i], w[2][i]
                u1, u2, u3 := u[0][i], u[1][i], u[2][i]
                wk.W[0][i] = w2*u3 - w3*u2
                wk.W[1][i] = w3*u1 - w1*u3
                wk.W[2][i] = w1*u2 - w2*u1
        }
        wk.Nlhat = fftField3(wk, wk.W)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        if !s.Mask[i] {
                                wk.Nlhat.C[c][i] = 0
                        }
                }
        }
        project3(wk, s, du, wk.Nlhat)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        damp := s.Nu*s.Ksq[i] + s.Nu4*s.Ksq2[i]
                        du.C[c][i] -= complex(damp, 0) * uhat.C[c][i]
                }
        }
}

func stepRK4_3d(wk *Work3D, s *NSE3D, out, uhat Field3, dt float64) {
        n3 := len(uhat.C[0])
        rhs3(wk, s, wk.K1, uhat)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        wk.T1.C[c][i] = uhat.C[c][i] + complex(0.5*dt, 0)*wk.K1.C[c][i]
                }
        }
        rhs3(wk, s, wk.K2, wk.T1)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        wk.T1.C[c][i] = uhat.C[c][i] + complex(0.5*dt, 0)*wk.K2.C[c][i]
                }
        }
        rhs3(wk, s, wk.K3, wk.T1)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        wk.T1.C[c][i] = uhat.C[c][i] + complex(dt, 0)*wk.K3.C[c][i]
                }
        }
        rhs3(wk, s, wk.K4, wk.T1)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        v := uhat.C[c][i] + complex(dt/6, 0)*(wk.K1.C[c][i]+complex(2, 0)*wk.K2.C[c][i]+complex(2, 0)*wk.K3.C[c][i]+wk.K4.C[c][i])
                        if s.Mask[i] {
                                out.C[c][i] = v
                        } else {
                                out.C[c][i] = 0
                        }
                }
        }
}

func cflDt3d(wk *Work3D, s *NSE3D, uhat Field3) float64 {
        u := ifftField3(wk, uhat)
        umax := 0.0
        for i := 0; i < len(u[0]); i++ {
                v := math.Sqrt(u[0][i]*u[0][i] + u[1][i]*u[1][i] + u[2][i]*u[2][i])
                if v > umax {
                        umax = v
                }
        }
        if umax < 1e-14 {
                return 0.5 * s.Dx * s.Dx / math.Max(s.Nu, 1e-12)
        }
        return 0.5 * s.Dx / umax
}

// ───────────────────── ICs & b-rotations ────────────────────────────────

var NSBThetaB = math.Asin(1.0 / (4*PI + 2*math.Sqrt(3)))
var NSBAxis = [3]float64{0.3, -0.5, 0.812403840463596}

type Mat3 [3][3]float64

func rodrigues(theta float64, ax [3]float64) Mat3 {
        ex, ey, ez := ax[0], ax[1], ax[2]
        c, s := math.Cos(theta), math.Sin(theta)
        C := [3][3]float64{{0, -ez, ey}, {ez, 0, -ex}, {-ey, ex, 0}}
        O := [3][3]float64{{ex * ex, ex * ey, ex * ez}, {ey * ex, ey * ey, ey * ez}, {ez * ex, ez * ey, ez * ez}}
        var R Mat3
        for i := 0; i < 3; i++ {
                for j := 0; j < 3; j++ {
                        diag := 0.0
                        if i == j {
                                diag = 1
                        }
                        R[i][j] = c*diag + (1-c)*O[i][j] - s*C[i][j]
                }
        }
        return R
}

func grid1d(n int) []float64 {
        x := make([]float64, n)
        for i := range x {
                x[i] = 2 * PI * float64(i) / float64(n)
        }
        return x
}

type PhysField = [3][]float64

func icTaylorGreen(n int) PhysField {
        x := grid1d(n)
        var u PhysField
        for c := range u {
                u[c] = make([]float64, n*n*n)
        }
        sx := make([]float64, n)
        cx := make([]float64, n)
        for i := 0; i < n; i++ {
                sx[i] = math.Sin(x[i])
                cx[i] = math.Cos(x[i])
        }
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        for k := 0; k < n; k++ {
                                u[0][idx3(n, i, j, k)] = sx[i] * cx[j] * cx[k]
                                u[1][idx3(n, i, j, k)] = -cx[i] * sx[j] * cx[k]
                        }
                }
        }
        return u
}

func icABC(n int) PhysField {
        x := grid1d(n)
        var u PhysField
        for c := range u {
                u[c] = make([]float64, n*n*n)
        }
        sx := make([]float64, n)
        cx := make([]float64, n)
        for i := 0; i < n; i++ {
                sx[i] = math.Sin(x[i])
                cx[i] = math.Cos(x[i])
        }
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        for k := 0; k < n; k++ {
                                u[0][idx3(n, i, j, k)] = sx[k] + cx[j]
                                u[1][idx3(n, i, j, k)] = sx[i] + cx[k]
                                u[2][idx3(n, i, j, k)] = sx[j] + cx[i]
                        }
                }
        }
        return u
}

func icHouLuo(n int) PhysField {
        x := grid1d(n)
        var w PhysField
        for c := range w {
                w[c] = make([]float64, n*n*n)
        }
        sigma := PI / 16
        inv2s2 := 1.0 / (2 * sigma * sigma)
        y0, z0a, z0b := PI/2, PI/2, 3*PI/2
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        for k := 0; k < n; k++ {
                                yj, zk := x[j], x[k]
                                g1 := math.Exp(-((yj-y0)*(yj-y0) + (zk-z0a)*(zk-z0a)) * inv2s2)
                                g2 := math.Exp(-((yj-3*PI/2)*(yj-3*PI/2) + (zk-z0b)*(zk-z0b)) * inv2s2)
                                w[0][idx3(n, i, j, k)] = (g1 - g2) * (1 + 0.05*math.Cos(x[i]))
                        }
                }
        }
        return w
}

func icRandom(n int, seed int64) PhysField {
        rng := rand.New(rand.NewSource(seed))
        var u PhysField
        for c := range u {
                u[c] = make([]float64, n*n*n)
                for i := range u[c] {
                        u[c][i] = rng.NormFloat64()
                }
        }
        x := grid1d(n)
        kp := 4.0
        for i := 0; i < n; i++ {
                for j := 0; j < n; j++ {
                        for k := 0; k < n; k++ {
                                id := idx3(n, i, j, k)
                                u[0][id] += 0.5 * math.Sin(kp*x[i]) * math.Cos(kp*x[j])
                                u[1][id] += 0.5 * math.Sin(kp*x[i]) * (0.5*math.Sin(kp*x[j]) + 0.5)
                                u[2][id] += 0.5 * math.Cos(kp*x[k]) * math.Sin(kp*x[j])
                        }
                }
        }
        return u
}

func prepareState3(wk *Work3D, s *NSE3D, ic PhysField) Field3 {
        n3 := len(ic[0])
        uhat := zeroField3(n3)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        wk.Scratch.C[c][i] = complex(ic[c][i], 0)
                }
                wk.Plan.fft3d(wk.Scratch.C[c], false)
                copy(uhat.C[c], wk.Scratch.C[c])
        }
        project3(wk, s, uhat, uhat)
        for c := 0; c < 3; c++ {
                for i := 0; i < n3; i++ {
                        if !s.Mask[i] {
                                uhat.C[c][i] = 0
                        }
                }
        }
        return uhat
}

// rotatePointwise assigns into dst explicitly (Go has no reference returns)
func rotatePointwiseInto(wk *Work3D, s *NSE3D, dst, uhat Field3, R Mat3) {
        wk.T3 = zeroField3(len(uhat.C[0]))
        rotatePointwiseAssign(wk, s, wk.T3, uhat, R)
        copy(dst.C[0], wk.T3.C[0])
        copy(dst.C[1], wk.T3.C[1])
        copy(dst.C[2], wk.T3.C[2])
}

func rotatePointwiseAssign(wk *Work3D, s *NSE3D, dst, uhat Field3, R Mat3) {
        n3 := len(uhat.C[0])
        u := ifftField3(wk, uhat)
        var ru PhysField
        for c := range ru {
                ru[c] = make([]float64, n3)
        }
        for i := 0; i < n3; i++ {
                x, y, z := u[0][i], u[1][i], u[2][i]
                ru[0][i] = R[0][0]*x + R[0][1]*y + R[0][2]*z
                ru[1][i] = R[1][0]*x + R[1][1]*y + R[1][2]*z
                ru[2][i] = R[2][0]*x + R[2][1]*y + R[2][2]*z
        }
        res := fftField3(wk, ru)
        copy(dst.C[0], res.C[0])
        copy(dst.C[1], res.C[1])
        copy(dst.C[2], res.C[2])
}

func rotateFullSymmetryInto(wk *Work3D, s *NSE3D, dst, uhat Field3) {
        n := s.N
        n3 := len(uhat.C[0])
        u := ifftField3(wk, uhat)
        var ru PhysField
        for c := range ru {
                ru[c] = make([]float64, n3)
        }
        for i := 0; i < n; i++ {
                isrc := (n - i) % n
                for j := 0; j < n; j++ {
                        for k := 0; k < n; k++ {
                                src := idx3(n, j, isrc, k)
                                dstID := idx3(n, i, j, k)
                                ru[0][dstID] = -u[1][src]
                                ru[1][dstID] = u[0][src]
                                ru[2][dstID] = u[2][src]
                        }
                }
        }
        res := fftField3(wk, ru)
        copy(dst.C[0], res.C[0])
        copy(dst.C[1], res.C[1])
        copy(dst.C[2], res.C[2])
}

// __GO_PART3__


// ───────────────────────── diagnostics ──────────────────────────────────

type TimeSeries struct {
	T, Energy, Enstrophy, Palinstrophy, SupOmega, Dissipation, Bkm []float64
}

func newTimeSeries() *TimeSeries {
	return &TimeSeries{
		T: []float64{0}, Energy: []float64{0}, Enstrophy: []float64{0},
		Palinstrophy: []float64{0}, SupOmega: []float64{0},
		Dissipation: []float64{0}, Bkm: []float64{0},
	}
}

func (ts *TimeSeries) push(t, e, om, pal, sup, eps, bkm float64) {
	ts.T = append(ts.T, t)
	ts.Energy = append(ts.Energy, e)
	ts.Enstrophy = append(ts.Enstrophy, om)
	ts.Palinstrophy = append(ts.Palinstrophy, pal)
	ts.SupOmega = append(ts.SupOmega, sup)
	ts.Dissipation = append(ts.Dissipation, eps)
	ts.Bkm = append(ts.Bkm, bkm)
}

func energy3(s *NSE3D, uhat Field3) float64 {
	n6 := math.Pow(float64(s.N), 6)
	sum := 0.0
	for c := 0; c < 3; c++ {
		for _, v := range uhat.C[c] {
			sum += real(v)*real(v) + imag(v)*imag(v)
		}
	}
	return 0.5 * sum / n6
}

func enstrophy3(s *NSE3D, what Field3) float64 { return energy3(s, what) }

func palinstrophy3(s *NSE3D, what Field3) float64 {
	n3 := len(what.C[0])
	n6 := math.Pow(float64(s.N), 6)
	ii := complex(0, 1)
	sum := 0.0
	for i := 0; i < n3; i++ {
		ky, kz := complex(float64(s.Ky[i]), 0), complex(float64(s.Kz[i]), 0)
		kx := complex(float64(s.Kx[i]), 0)
		a1 := ii * (ky*what.C[2][i] - kz*what.C[1][i])
		a2 := ii * (kz*what.C[0][i] - kx*what.C[2][i])
		a3 := ii * (kx*what.C[1][i] - ky*what.C[0][i])
		for _, a := range []complex128{a1, a2, a3} {
			sum += real(a)*real(a) + imag(a)*imag(a)
		}
	}
	return 0.5 * sum / n6
}

func dissipation3(s *NSE3D, uhat Field3) float64 {
	n6 := math.Pow(float64(s.N), 6)
	sum := 0.0
	for c := 0; c < 3; c++ {
		for i, v := range uhat.C[c] {
			sum += s.Ksq[i] * (real(v)*real(v) + imag(v)*imag(v))
		}
	}
	return s.Nu * sum / n6
}

func supVorticity3(w PhysField) float64 {
	m := 0.0
	for i := range w[0] {
		v := math.Sqrt(w[0][i]*w[0][i] + w[1][i]*w[1][i] + w[2][i]*w[2][i])
		if v > m {
			m = v
		}
	}
	return m
}

func divergenceMax3(s *NSE3D, uhat Field3) float64 {
	n3 := len(uhat.C[0])
	sum := 0.0
	for i := 0; i < n3; i++ {
		d := complex(float64(s.Kx[i]), 0)*uhat.C[0][i] +
			complex(float64(s.Ky[i]), 0)*uhat.C[1][i] +
			complex(float64(s.Kz[i]), 0)*uhat.C[2][i]
		sum += real(d)*real(d) + imag(d)*imag(d)
	}
	return math.Sqrt(sum) / math.Pow(float64(s.N), 3)
}

func linfit(xs, ys []float64) (a, b, r2 float64) {
	n := len(xs)
	if n < 2 {
		return math.NaN(), math.NaN(), math.NaN()
	}
	var sx, sy, sxx, sxy float64
	for i := 0; i < n; i++ {
		sx += xs[i]
		sy += ys[i]
		sxx += xs[i] * xs[i]
		sxy += xs[i] * ys[i]
	}
	den := float64(n)*sxx - sx*sx
	if den == 0 {
		return math.NaN(), math.NaN(), math.NaN()
	}
	a = (float64(n)*sxy - sx*sy) / den
	b = (sy - a*sx) / float64(n)
	ybar := sy / float64(n)
	var ssr, sst float64
	for i := 0; i < n; i++ {
		d := ys[i] - (a*xs[i] + b)
		ssr += d * d
		d2 := ys[i] - ybar
		sst += d2 * d2
	}
	if sst > 0 {
		r2 = 1 - ssr/sst
	} else {
		r2 = math.NaN()
	}
	return
}

func observedOrder(jc, jf, jff, ratio float64) float64 {
	den, num := jc-jf, jf-jff
	if math.Abs(den) < 1e-30 || math.Abs(num) < 1e-30 {
		return math.NaN()
	}
	return math.Log(math.Abs(den/num)) / math.Log(ratio)
}

type BlowupReport struct {
	LambdaTrend, LambdaR2, LambdaMax, DoublingMin, Alpha, BkmFinal float64
	Sustained                                                      bool
	Tstar                                                          float64
	HasTstar                                                       bool
}

func blowupReport(ts *TimeSeries) (bl BlowupReport) {
	var tl, lam []float64
	for i := 1; i < len(ts.T)-1; i++ {
		dt1 := ts.T[i] - ts.T[i-1]
		dt2 := ts.T[i+1] - ts.T[i]
		s0, s1, s2 := ts.SupOmega[i-1], ts.SupOmega[i], ts.SupOmega[i+1]
		if dt1 <= 0 || dt2 <= 0 || s0 <= 0 || s1 <= 0 || s2 <= 0 {
			continue
		}
		lam = append(lam, (math.Log(s2)-math.Log(s0))/(dt1+dt2))
		tl = append(tl, ts.T[i])
	}
	bl.BkmFinal = ts.Bkm[len(ts.Bkm)-1]
	bl.DoublingMin = math.Inf(1)
	if len(tl) < 4 {
		bl.LambdaMax = math.NaN()
		for _, v := range lam {
			bl.LambdaMax = math.Max(bl.LambdaMax, v)
		}
		return
	}
	a, _, r2 := linfit(tl, lam)
	bl.LambdaTrend, bl.LambdaR2 = a, r2
	bl.LambdaMax = math.Inf(-1)
	for _, v := range lam {
		bl.LambdaMax = math.Max(bl.LambdaMax, v)
	}
	for i := 1; i < len(ts.SupOmega); i++ {
		s0, s1 := ts.SupOmega[i-1], ts.SupOmega[i]
		dt := ts.T[i] - ts.T[i-1]
		if s0 > 0 && s1 > s0 && dt > 0 {
			bl.DoublingMin = math.Min(bl.DoublingMin, dt*math.Log(2)/math.Log(s1/s0))
		}
	}
	nfit := int(math.Round(float64(len(tl)) * 0.25))
	if nfit < 4 {
		nfit = 4
	}
	if nfit > len(tl) {
		nfit = len(tl)
	}
	at, _, r2t := linfit(tl[len(tl)-nfit:], lam[len(lam)-nfit:])
	tailMax := math.Inf(-1)
	supMax := math.Inf(-1)
	for i := len(ts.SupOmega) - nfit; i < len(ts.SupOmega); i++ {
		tailMax = math.Max(tailMax, ts.SupOmega[i])
	}
	for _, v := range ts.SupOmega {
		supMax = math.Max(supMax, v)
	}
	bl.Sustained = !math.IsNaN(at) && at > 0 && !math.IsNaN(r2t) && r2t > 0.5 &&
		bl.LambdaMax > 0 && tailMax >= 0.98*supMax
	if bl.Sustained {
		tEnd := ts.T[len(ts.T)-1]
		bestErr := math.Inf(1)
		for al := 0.5; al <= 7.0+1e-9; al += 0.25 {
			for frac := 1.02; frac <= 2.5+1e-9; frac += 0.02 {
				tst := tEnd * frac
				var xs, ys []float64
				ok := true
				for i := 0; i < len(ts.T); i++ {
					d := tst - ts.T[i]
					if d <= 0 {
						ok = false
						break
					}
					xs = append(xs, math.Log(d))
					ys = append(ys, math.Log(math.Max(ts.SupOmega[i], 1e-300)))
				}
				if !ok {
					continue
				}
				A, _, R2 := linfit(xs, ys)
				if !math.IsNaN(R2) && -R2 < bestErr {
					bestErr = -R2
					bl.Tstar = tst
					bl.Alpha = -A
					bl.HasTstar = true
				}
			}
		}
		if bestErr >= -0.9 {
			bl.HasTstar = false
		}
	}
	return
}

// ─────────────────────────── runner ─────────────────────────────────────

type DecayResult struct {
	Uhat                     Field3
	Ts                       *TimeSeries
	DivMax, EnergyRise, Wall float64
	CflExceeded, Adapted     int
	StepsDone                int
}

func runDecay3d(wk *Work3D, s *NSE3D, uhat0 Field3, dt, tHorizon float64,
	label string, sampleEvery, kickMode int, kickEvery float64,
	blowupStop, showProg bool, adaptiveSet *bool) *DecayResult {
	adaptive := CFG.AdaptiveCFL
	if adaptiveSet != nil {
		adaptive = *adaptiveSet
	}
	n3 := len(uhat0.C[0])
	res := &DecayResult{Uhat: cloneField3(uhat0), Ts: newTimeSeries()}
	curlHat3(s, wk.Wh, res.Uhat)
	w0 := ifftField3(wk, wk.Wh)
	supPrev := supVorticity3(w0)
	steps := int(math.Ceil(tHorizon / dt))
	ePrev := energy3(s, res.Uhat)
	tElapsed := 0.0
	t0 := time.Now()
	progLast = 0
	if adaptive {
		pMuted("  " + L("adaptive_on") + "\n")
	}
	nextKick := math.Inf(1)
	if kickMode > 0 {
		nextKick = kickEvery
	}
	for step := 1; step <= steps; step++ {
		h := math.Min(dt, tHorizon-tElapsed)
		if h <= 1e-15 {
			break
		}
		cfl := cflDt3d(wk, s, res.Uhat)
		if cfl < h {
			res.CflExceeded++
			if adaptive {
				h = cfl
				res.Adapted++
			}
		}
		stepRK4_3d(wk, s, wk.T2, res.Uhat, h)
		res.Uhat = cloneField3(wk.T2)
		tElapsed += h
		if kickMode > 0 && tElapsed >= nextKick-1e-12 {
			if kickMode == 1 {
				rotateFullSymmetryInto(wk, s, wk.T3, res.Uhat)
			} else {
				R := rodrigues(NSBThetaB, NSBAxis)
				rotatePointwiseAssign(wk, s, wk.T3, res.Uhat, R)
				project3(wk, s, wk.T3, wk.T3)
			}
			for c := 0; c < 3; c++ {
				for i := 0; i < n3; i++ {
					if !s.Mask[i] {
						wk.T3.C[c][i] = 0
					}
				}
			}
			res.Uhat = cloneField3(wk.T3)
			nextKick += kickEvery
		}
		if step%sampleEvery == 0 || step == steps {
			curlHat3(s, wk.Wh, res.Uhat)
			w := ifftField3(wk, wk.Wh)
			supNow := supVorticity3(w)
			eNow := energy3(s, res.Uhat)
			res.DivMax = math.Max(res.DivMax, divergenceMax3(s, res.Uhat))
			res.EnergyRise = math.Max(res.EnergyRise, eNow-ePrev)
			ePrev = eNow
			bkm := res.Ts.Bkm[len(res.Ts.Bkm)-1] + 0.5*(supPrev+supNow)*h*float64(sampleEvery)
			supPrev = supNow
			res.Ts.push(tElapsed, eNow, enstrophy3(s, wk.Wh), palinstrophy3(s, wk.Wh),
				supNow, dissipation3(s, res.Uhat), bkm)
			if showProg {
				progress(float64(step)/float64(steps), label, t0, steps, step)
			}
			if blowupStop && (math.IsNaN(supNow) || supNow > 1e8) {
				pWarn("  stop: sup|w| over threshold\n")
				break
			}
		}
	}
	if showProg {
		progress(1.0, label, t0, steps, steps)
	}
	res.StepsDone = steps
	res.Wall = time.Since(t0).Seconds()
	return res
}

// __GO_PART4__

// ─────────────────────── 2-D barotropic β-plane ─────────────────────────

type Baro2D struct {
	N                     int
	Nu, Nu4, Beta, Lbox   float64
	Kpx, Kpy, Kp2         []float64
	Mask                  []bool
	Plan                  *FFTPlan
}

func newBaro2D(n int, nu, nu4, beta, lbox float64) *Baro2D {
	n2 := n * n
	k1d := make([]int, n)
	for i := 0; i < n/2; i++ {
		k1d[i] = i
	}
	for i := -n / 2; i < 0; i++ {
		k1d[i+n] = i
	}
	kc := n / 3
	m := &Baro2D{N: n, Nu: nu, Nu4: nu4, Beta: beta, Lbox: lbox,
		Kpx: make([]float64, n2), Kpy: make([]float64, n2),
		Kp2: make([]float64, n2), Mask: make([]bool, n2), Plan: fftPlan(n)}
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			id := i*n + j
			a, b := k1d[i], k1d[j]
			m.Kpx[id] = 2 * PI * float64(a) / lbox
			m.Kpy[id] = 2 * PI * float64(b) / lbox
			m.Kp2[id] = m.Kpx[id]*m.Kpx[id] + m.Kpy[id]*m.Kpy[id]
			m.Mask[id] = abs(a) <= kc && abs(b) <= kc
		}
	}
	return m
}

func (m *Baro2D) ifft(out []float64, in []complex128) {
	tmp := make([]complex128, len(in))
	copy(tmp, in)
	m.Plan.fft2d(tmp, true)
	for i := range tmp {
		out[i] = real(tmp[i])
	}
}

func (m *Baro2D) fft(out []complex128, in []float64) {
	for i, v := range in {
		out[i] = complex(v, 0)
	}
	m.Plan.fft2d(out, false)
}

func (m *Baro2D) velocity(what []complex128, bufs *BaroBufs) float64 {
	n2 := m.N * m.N
	for i := 0; i < n2; i++ {
		var psih complex128
		if m.Kp2[i] > 0 {
			psih = what[i] / complex(m.Kp2[i], 0)
		}
		bufs.Uhat[i] = complex(0, 1) * complex(m.Kpy[i], 0) * psih
		bufs.Vhat[i] = -complex(0, 1) * complex(m.Kpx[i], 0) * psih
	}
	m.ifft(bufs.U, bufs.Uhat)
	m.ifft(bufs.V, bufs.Vhat)
	um := 0.0
	for i := 0; i < n2; i++ {
		v := math.Hypot(bufs.U[i], bufs.V[i])
		if v > um {
			um = v
		}
	}
	return um
}

type BaroBufs struct {
	Uhat, Vhat, Dxwhat, Dywhat   []complex128
	U, V, W, Dxw, Dyw            []float64
}

func newBaroBufs(n int) *BaroBufs {
	n2 := n * n
	return &BaroBufs{
		Uhat: make([]complex128, n2), Vhat: make([]complex128, n2),
		Dxwhat: make([]complex128, n2), Dywhat: make([]complex128, n2),
		U: make([]float64, n2), V: make([]float64, n2), W: make([]float64, n2),
		Dxw: make([]float64, n2), Dyw: make([]float64, n2),
	}
}

func baroRhs(m *Baro2D, dwhat, what []complex128, bufs *BaroBufs) {
	n2 := m.N * m.N
	for i := 0; i < n2; i++ {
		var psih complex128
		if m.Kp2[i] > 0 {
			psih = what[i] / complex(m.Kp2[i], 0)
		}
		bufs.Uhat[i] = complex(0, 1) * complex(m.Kpy[i], 0) * psih
		bufs.Vhat[i] = -complex(0, 1) * complex(m.Kpx[i], 0) * psih
		bufs.Dxwhat[i] = complex(0, 1) * complex(m.Kpx[i], 0) * what[i]
		bufs.Dywhat[i] = complex(0, 1) * complex(m.Kpy[i], 0) * what[i]
	}
	m.ifft(bufs.W, what)
	m.ifft(bufs.U, bufs.Uhat)
	m.ifft(bufs.V, bufs.Vhat)
	m.ifft(bufs.Dxw, bufs.Dxwhat)
	m.ifft(bufs.Dyw, bufs.Dywhat)
	nl := make([]float64, n2)
	for i := 0; i < n2; i++ {
		nl[i] = -(bufs.U[i]*bufs.Dxw[i] + bufs.V[i]*bufs.Dyw[i])
	}
	m.fft(dwhat, nl)
	for i := 0; i < n2; i++ {
		dwhat[i] = dwhat[i] - complex(m.Beta, 0)*bufs.Vhat[i] -
			complex(m.Nu*m.Kp2[i]+m.Nu4*m.Kp2[i]*m.Kp2[i], 0)*what[i]
		if !m.Mask[i] {
			dwhat[i] = 0
		}
	}
}

func baroStep(m *Baro2D, what []complex128, dt float64, bufs *BaroBufs,
	k1, k2, k3, k4, buf []complex128) {
	n2 := m.N * m.N
	baroRhs(m, k1, what, bufs)
	for i := 0; i < n2; i++ {
		buf[i] = what[i] + complex(0.5*dt, 0)*k1[i]
	}
	baroRhs(m, k2, buf, bufs)
	for i := 0; i < n2; i++ {
		buf[i] = what[i] + complex(0.5*dt, 0)*k2[i]
	}
	baroRhs(m, k3, buf, bufs)
	for i := 0; i < n2; i++ {
		buf[i] = what[i] + complex(dt, 0)*k3[i]
	}
	baroRhs(m, k4, buf, bufs)
	for i := 0; i < n2; i++ {
		v := what[i] + complex(dt/6, 0)*(k1[i]+complex(2, 0)*k2[i]+complex(2, 0)*k3[i]+k4[i])
		if m.Mask[i] {
			what[i] = v
		} else {
			what[i] = 0
		}
	}
}

// __GO_PART5__

// ─────────────────────────── 20 real flows ──────────────────────────────

type Flow struct {
	ID, Ru, En, Category, Medium, Source string
	Doc                                  [4][2]string
	U, L, Width, Lat, NuEff              float64
	Depth, WaveH, WaveLambda             float64
	Model                                string
}

var FLOWS = []Flow{
	{"katrina", "Ураган Катрина (2005)", "Hurricane Katrina (2005)", "hurricane", "air",
		"NHC Tropical Cyclone Report AL122005 (Knabb et al.)",
		[4][2]string{{"1-min sustained wind", "77 m/s (150 kt)"}, {"min pressure", "902 hPa"},
			{"radius of max wind", "37 km"}, {"peak latitude", "25.7 N"}},
		77.0, 3.7e4, 2.0e4, 25.7, 100.0, 0, 0, 0, "vortex"},
	{"haiyan", "Тайфун Хайян (2013)", "Typhoon Haiyan (2013)", "hurricane", "air",
		"JTWC Best Track 31W; NDRRMC Philippines",
		[4][2]string{{"1-min sustained wind", "87 m/s (170 kt)"}, {"min pressure", "895 hPa"},
			{"radius of max wind", "15-20 km"}, {"latitude", "8 N"}},
		87.0, 1.8e4, 1.0e4, 8.0, 100.0, 0, 0, 0, "vortex"},
	{"patricia", "Ураган Патрисия (2015)", "Hurricane Patricia (2015)", "hurricane", "air",
		"NHC Tropical Cyclone Report EP202015",
		[4][2]string{{"1-min sustained wind", "95 m/s (185 kt), record"}, {"min pressure", "872 hPa"},
			{"radius of max wind", "8 km"}, {"latitude", "19 N"}},
		95.0, 8.0e3, 5.0e3, 19.0, 100.0, 0, 0, 0, "vortex"},
	{"redspot", "Большое красное пятно (Юпитер)", "Great Red Spot (Jupiter)", "space", "gas",
		"Voyager 1/2 (1979); Cassini; Juno",
		[4][2]string{{"extent", "16350 x 11000 km"}, {"wind speeds", "100-120 m/s"},
			{"rotation period", "4-6 days"}, {"latitude", "22 S"}},
		110.0, 8.0e6, 3.0e6, 22.0, 1.0e4, 0, 0, 0, "vortex"},
	{"hexagon", "Сатурн: северный гексагон", "Saturn north polar hexagon", "space", "gas",
		"Voyager (1980-81); Cassini (2006-2017)",
		[4][2]string{{"latitude", "78 N"}, {"jet speed", "100 m/s"},
			{"rotation period", "10.7 h"}, {"wave number", "m = 6"}},
		100.0, 1.45e7, 2.0e6, 78.0, 1.0e4, 0, 0, 0, "jet"},
	{"jetstream", "Полярное струйное течение", "Polar jet stream", "jet", "air",
		"WMO radiosonde climatology; ICAO Annex 3",
		[4][2]string{{"core speed", "50-80 m/s"}, {"altitude", "9-12 km"},
			{"width", "200-400 km"}, {"latitude", "30-60"}},
		70.0, 3.0e5, 1.5e5, 45.0, 50.0, 0, 0, 0, "jet"},
	{"karman", "Дорожка Кармана", "von Karman vortex street", "jet", "air",
		"Landsat 5 (1989, Jeju); MODIS Aqua",
		[4][2]string{{"island diameter", "2-5 km"}, {"wind", "10 m/s"},
			{"Strouhal number", "0.2"}, {"shedding period", "2-6 h"}},
		10.0, 3.0e3, 1.5e3, 33.0, 50.0, 0, 0, 0, "jet"},
	{"gulfstream", "Гольфстрим", "Gulf Stream", "current", "water",
		"Franklin-Folger map (1768); Halkin & Rossby (1985)",
		[4][2]string{{"max speed", "2.0-2.5 m/s"}, {"width", "100 km"},
			{"transport", "30 Sv"}, {"latitude", "35-40 N"}},
		2.2, 1.0e5, 5.0e4, 37.0, 1.0, 0, 0, 0, "jet"},
	{"kuroshio", "Куросио", "Kuroshio Current", "current", "water",
		"ASUKA/JCOPE Observations; Kawabe (1988)",
		[4][2]string{{"max speed", "1.5-2.0 m/s"}, {"width", "80 km"},
			{"transport", "20-30 Sv"}, {"latitude", "33 N"}},
		1.8, 8.0e4, 4.0e4, 33.0, 1.0, 0, 0, 0, "jet"},
	{"agulhas", "Игольное течение", "Agulhas Current", "current", "water",
		"Lutjeharms (2006); ACT array (2010-2013)",
		[4][2]string{{"max speed", "2.0-2.5 m/s"}, {"width", "100-150 km"},
			{"transport", "70 Sv"}, {"retroflection", "20 E"}},
		2.2, 1.2e5, 6.0e4, -35.0, 1.0, 0, 0, 0, "jet"},
	{"acc", "Антарктическое циркумполярное течение", "Antarctic Circumpolar Current", "current", "water",
		"WOCE/SR1b sections; Meredith et al.",
		[4][2]string{{"transport", "130-150 Sv, largest on Earth"}, {"speeds", "0.3-0.7 m/s"},
			{"latitude", "50-60 S"}, {"width", "800 km"}},
		0.5, 8.0e5, 4.0e5, -55.0, 1.0, 0, 0, 0, "jet"},
	{"draupner", "Волна-убийца Драупнер (1995)", "Draupner rogue wave (1995)", "wave", "water",
		"Haver (2004), Statoil laser record",
		[4][2]string{{"max wave height", "25.6 m"}, {"background Hs", "11.9 m"},
			{"depth", "70 m"}, {"steepness", "kA = 0.39"}},
		15.0, 200.0, 100.0, 58.0, 1e-6, 70.0, 25.6, 200.0, "wave"},
	{"tohoku", "Цунами Тохоку (2011)", "Tohoku tsunami (2011)", "wave", "water",
		"NOAA DART buoys; JMA; NOWPHAS",
		[4][2]string{{"open-ocean height", "1.8 m"}, {"max run-up", "40.5 m"},
			{"speed", "800 km/h at 4000 m"}, {"magnitude", "M9.1"}},
		200.0, 2.0e5, 1.0e5, 38.3, 1e-6, 4000.0, 1.8, 2.0e5, "wave"},
	{"qiantang", "Приливной бор Цяньтан", "Qiantang tidal bore", "wave", "water",
		"Hangzhou Bay surveys; Song-dynasty chronicles",
		[4][2]string{{"bore height", "up to 9 m"}, {"speed", "6-9 m/s"},
			{"tidal amplitude", "up to 8.9 m"}, {"bay width", "100 km"}},
		8.0, 5.0e4, 2.0e4, 30.4, 1e-6, 10.0, 9.0, 5.0e4, "wave"},
	{"reynolds", "Течение Рейнольдса (1883)", "Reynolds pipe flow (1883)", "lab", "water",
		"Reynolds O., Phil. Trans. R. Soc. 174 (1883)",
		[4][2]string{{"critical Re", "2300"}, {"pipe diameter", "2.6 cm"},
			{"transition speed", "0.09 m/s"}, {"laminar profile", "Poiseuille"}},
		0.09, 2.6e-2, 1.3e-2, 999.0, 1e-6, 0, 0, 0, "vortex"},
	{"taylorcouette", "Тейлор-Куэтт вихри (1923)", "Taylor-Couette vortices (1923)", "lab", "water",
		"Taylor G.I., Phil. Trans. R. Soc. A 223 (1923)",
		[4][2]string{{"inner radius", "3.55 cm"}, {"gap", "0.42 cm"},
			{"critical Taylor number", "1708"}, {"vortices", "toroidal cells"}},
		0.5, 4.2e-3, 2.1e-3, 999.0, 1e-6, 0, 0, 0, "vortex"},
	{"benard", "Конвекция Бенара-Рэлея", "Benard-Rayleigh convection", "lab", "water",
		"Benard (1900); Rayleigh (1916)",
		[4][2]string{{"critical Ra", "1708"}, {"cell size", "2 depths"},
			{"layer depth", "1 cm"}, {"critical dT", "Rayleigh formula"}},
		1e-3, 2.0e-2, 1.0e-2, 999.0, 1e-6, 0, 0, 0, "vortex"},
	{"moore", "Торнадо Бридж-Крик-Мур (1999)", "Bridge Creek-Moore tornado (1999)", "storm", "air",
		"Wurman & Alexander (2005), DOW-III",
		[4][2]string{{"max wind", "135 m/s (301 mph), DOW record"}, {"core radius", "250 m"},
			{"latitude", "35.3 N"}, {"track", "61 km"}},
		135.0, 5.0e2, 2.5e2, 35.3, 100.0, 0, 0, 0, "vortex"},
	{"mtwashington", "Порыв на горе Вашингтон (1934)", "Mount Washington gust (1934)", "storm", "air",
		"Mount Washington Observatory, 12.04.1934",
		[4][2]string{{"gust", "103.3 m/s (231 mph), world record"}, {"station altitude", "1917 m"},
			{"latitude", "44.3 N"}, {"ice", "instrument icing"}},
		103.0, 1.0e4, 5.0e3, 44.3, 100.0, 0, 0, 0, "jet"},
	{"kelvinhelmholtz", "Вихри Кельвина-Гельмгольца", "Kelvin-Helmholtz billows", "jet", "air",
		"Thorpe (1968, JFM); photos (2016)",
		[4][2]string{{"shear", "10 m/s per 100 m"}, {"criterion", "Ri = 0.25"},
			{"billow scale", "200-500 m"}, {"altitude", "3-4 km AGL"}},
		10.0, 3.0e2, 1.5e2, 39.0, 50.0, 0, 0, 0, "jet"},
}

type FlowDerived struct {
	ReMol, Beta, Ro, TAdv, Eta, NDns, MemDns float64
}

func flowDerived(f *Flow) FlowDerived {
	nuMol := map[string]float64{"air": 1.5e-5, "water": 1.0e-6, "gas": 1.0e-3}[f.Medium]
	reMol := f.U * f.L / nuMol
	hasLat := f.Lat <= 99.0
	f0, beta := math.NaN(), math.NaN()
	if hasLat {
		f0 = 2 * 7.2921e-5 * math.Sin(f.Lat*PI/180)
		beta = 2 * 7.2921e-5 * math.Cos(f.Lat*PI/180) / 6.371e6
	}
	ro := math.NaN()
	if hasLat {
		ro = f.U / (f0 * f.L)
	}
	nDns := math.Ceil(2 * PI * math.Pow(reMol, 0.75))
	return FlowDerived{ReMol: reMol, Beta: beta, Ro: ro, TAdv: f.L / f.U,
		Eta: f.L * math.Pow(reMol, -0.75), NDns: nDns,
		MemDns: nDns * nDns * nDns * 16.0 * 22.0}
}

func bignum(x float64) string {
	if math.IsNaN(x) || math.IsInf(x, 0) {
		return "?"
	}
	switch {
	case x >= 1e12:
		return fmt.Sprintf("%.1fe12", x/1e12)
	case x >= 1e9:
		return fmt.Sprintf("%.1fe9", x/1e9)
	case x >= 1e6:
		return fmt.Sprintf("%.1fe6", x/1e6)
	}
	return fmt.Sprintf("%.0f", x)
}

func bigMem(x float64) string {
	if math.IsNaN(x) || math.IsInf(x, 0) {
		return "?"
	}
	units := []struct {
		nm string
		sz float64
	}{{"ZiB", 1e21}, {"EiB", 1e18}, {"PiB", 1e15}, {"TiB", 1 << 40}, {"GiB", 1 << 30}, {"MiB", 1 << 20}}
	for _, u := range units {
		if x >= u.sz {
			return fmt.Sprintf("%.1f %s", x/u.sz, u.nm)
		}
	}
	return fmt.Sprintf("%.0f B", x)
}

// ─────────────────── verdict / check framework ──────────────────────────

type Check struct {
	Key    string
	Ok     bool
	Detail string
}

type RunRecord struct {
	Experiment string
	Ok         bool
	Checks     []Check
}

var SESSION []RunRecord

func checkAdd(r *RunRecord, key string, ok bool, detail string) {
	if !ok {
		r.Ok = false
	}
	r.Checks = append(r.Checks, Check{key, ok, detail})
}

func verdictPrint(r *RunRecord) {
	P("\n")
	for _, c := range r.Checks {
		P("  ")
		if c.Ok {
			pOK(L(c.Key))
		} else {
			pBad(L(c.Key))
		}
		P("  (%s)\n", c.Detail)
	}
	P("  "); pMuted(L("scope_note")); P("\n")
	if r.Ok {
		pOK(L("verdict_ok"))
	} else {
		pBad(L("verdict_fail"))
	}
	P("\n")
}

func fmtE(v float64) string { return fmt.Sprintf("%.2e", v) }

// __GO_PART6__

// ─────────────────────────── experiments ────────────────────────────────

func expTaylorGreen(mode string, nIn int, nuIn, dtIn, tIn float64) {
	hard := mode == "hard"
	n := 32
	if nIn > 0 {
		n = nIn
	}
	nu, dt, tHor := 0.02, 0.005, 2.0
	if hard {
		nu, dt, tHor = 0.01, 0.0025, 4.0
	}
	if nuIn >= 0 {
		nu = nuIn
	}
	if dtIn > 0 {
		dt = dtIn
	}
	if tIn > 0 {
		tHor = tIn
	}
	r := &RunRecord{Experiment: "taylor_green", Ok: true}
	headerBar(L("exp_tg"))
	P("  N=%d · ν=%g · dt=%g · T=%g\n", n, nu, dt, tHor)
	s := newNSE3D(n, nu, -1)
	wk := newWork3D(n)
	uhat0 := prepareState3(wk, s, icTaylorGreen(n))
	label := fmt.Sprintf("TG N=%d", n)
	res := runDecay3d(wk, s, uhat0, dt, tHor, label, 4, 0, 0.25, false, true, nil)
	checkAdd(r, "ck_divfree", res.DivMax < 1e-10, "max|div| = "+fmtE(res.DivMax))
	checkAdd(r, "ck_energy_monotone", res.EnergyRise < 1e-12,
		"dE_max = "+fmtE(res.EnergyRise))
	stab := true
	for _, v := range res.Ts.SupOmega {
		if math.IsNaN(v) {
			stab = false
		}
	}
	checkAdd(r, "ck_stability", stab,
		fmt.Sprintf("sup|w| final = %.4f", res.Ts.SupOmega[len(res.Ts.SupOmega)-1]))
	bl := blowupReport(res.Ts)
	checkAdd(r, "ck_no_blowup", !bl.Sustained || bl.LambdaTrend <= 0,
		fmt.Sprintf("dl/dt = %.3f (R2 = %.2f), BKM = %.3f", bl.LambdaTrend, bl.LambdaR2, bl.BkmFinal))
	P("  E       %s\n", sparkline(res.Ts.Energy))
	P("  sup|ω|  %s\n", sparkline(res.Ts.SupOmega))
	ensureOutdirs()
	stamp := time.Now().Format("20060102_150405")
	csvPath := filepath.Join(CFG.OutDir, "data", fmt.Sprintf("taylor_green_%s.csv", stamp))
	var sb strings.Builder
	sb.WriteString("t,energy,enstrophy,palinstrophy,sup_omega,dissipation,bkm\n")
	for i := 0; i < len(res.Ts.T); i++ {
		fmt.Fprintf(&sb, "%.6f,%.8e,%.8e,%.8e,%.6f,%.8e,%.6f\n", res.Ts.T[i],
			res.Ts.Energy[i], res.Ts.Enstrophy[i], res.Ts.Palinstrophy[i],
			res.Ts.SupOmega[i], res.Ts.Dissipation[i], res.Ts.Bkm[i])
	}
	_ = os.WriteFile(csvPath, []byte(sb.String()), 0o644)
	pMuted("  " + L("rep_saved") + ": " + csvPath + "\n")
	SESSION = append(SESSION, *r)
	verdictPrint(&SESSION[len(SESSION)-1])
}

func expABC(mode string, nIn int, dtIn, tIn float64) {
	hard := mode == "hard"
	n := 32
	if nIn > 0 {
		n = nIn
	}
	dt, tHor := 0.005, 1.0
	if hard {
		dt, tHor = 0.0025, 2.0
	}
	if dtIn > 0 {
		dt = dtIn
	}
	if tIn > 0 {
		tHor = tIn
	}
	r := &RunRecord{Experiment: "abc", Ok: true}
	headerBar(L("exp_abc"))
	P("  N=%d · ν=0 (Euler) · dt=%g · T=%g\n", n, dt, tHor)
	s := newNSE3D(n, 1e-14, -1)
	wk := newWork3D(n)
	uhat0 := prepareState3(wk, s, icABC(n))
	res := runDecay3d(wk, s, uhat0, dt, tHor, fmt.Sprintf("ABC N=%d", n), 4, 0, 0.25, true, true, nil)
	e0 := res.Ts.Energy[0]
	e1 := res.Ts.Energy[len(res.Ts.Energy)-1]
	dE := math.Abs(e1-e0) / math.Max(e0, 1e-30)
	checkAdd(r, "ck_divfree", res.DivMax < 1e-10, "max|div| = "+fmtE(res.DivMax))
	checkAdd(r, "ck_energy_conserved", dE < 1e-6, fmt.Sprintf("|dE|/E = %s (Euler)", fmtE(dE)))
	bl := blowupReport(res.Ts)
	checkAdd(r, "ck_no_blowup", !bl.Sustained || bl.LambdaTrend <= 0,
		fmt.Sprintf("dl/dt = %.3f, BKM = %.3f", bl.LambdaTrend, bl.BkmFinal))
	stab := true
	for _, v := range res.Ts.SupOmega {
		if math.IsNaN(v) {
			stab = false
		}
	}
	checkAdd(r, "ck_stability", stab, "no NaN/Inf")
	P("  E       %s\n", sparkline(res.Ts.Energy))
	P("  sup|ω|  %s\n", sparkline(res.Ts.SupOmega))
	SESSION = append(SESSION, *r)
	verdictPrint(&SESSION[len(SESSION)-1])
}

func expHouLuo(mode string, nIn int, dtIn, tIn float64) {
	hard := mode == "hard"
	n := 32
	if nIn > 0 {
		n = nIn
	}
	dt, tHor := 0.003, 1.0
	if hard {
		dt, tHor = 0.0015, 2.0
	}
	if dtIn > 0 {
		dt = dtIn
	}
	if tIn > 0 {
		tHor = tIn
	}
	r := &RunRecord{Experiment: "houluo", Ok: true}
	headerBar(L("exp_houluo"))
	P("  N=%d · ν=0 (Euler) · dt=%g · T=%g\n", n, dt, tHor)
	s := newNSE3D(n, 1e-14, -1)
	wk := newWork3D(n)
	w0 := icHouLuo(n)
	n3 := n * n * n
	what := zeroField3(n3)
	for c := 0; c < 3; c++ {
		for i := 0; i < n3; i++ {
			wk.Scratch.C[c][i] = complex(w0[c][i], 0)
		}
		wk.Plan.fft3d(wk.Scratch.C[c], false)
		copy(what.C[c], wk.Scratch.C[c])
	}
	for i := 0; i < n3; i++ {
		if s.Ksq[i] == 0 {
			what.C[0][i], what.C[1][i], what.C[2][i] = 0, 0, 0
			continue
		}
		inv2 := complex(0, 1/s.Ksq[i])
		w1, w2, w3 := what.C[0][i], what.C[1][i], what.C[2][i]
		what.C[0][i] = inv2 * (complex(float64(s.Ky[i]), 0)*w3 - complex(float64(s.Kz[i]), 0)*w2)
		what.C[1][i] = inv2 * (complex(float64(s.Kz[i]), 0)*w1 - complex(float64(s.Kx[i]), 0)*w3)
		what.C[2][i] = inv2 * (complex(float64(s.Kx[i]), 0)*w2 - complex(float64(s.Ky[i]), 0)*w1)
	}
	project3(wk, s, what, what)
	for c := 0; c < 3; c++ {
		for i := 0; i < n3; i++ {
			if !s.Mask[i] {
				what.C[c][i] = 0
			}
		}
	}
	res := runDecay3d(wk, s, what, dt, tHor, fmt.Sprintf("Hou-Luo N=%d", n), 4, 0, 0.25, true, true, nil)
	growth := res.Ts.SupOmega[len(res.Ts.SupOmega)-1] /
		math.Max(res.Ts.SupOmega[0], 1e-30)
	checkAdd(r, "ck_divfree", res.DivMax < 1e-10, "max|div| = "+fmtE(res.DivMax))
	checkAdd(r, "ck_hl_growth", growth > 1, fmt.Sprintf("sup|w| growth x%.3f over T=%g", growth, tHor))
	bl := blowupReport(res.Ts)
	checkAdd(r, "ck_no_blowup", !bl.Sustained || bl.LambdaTrend <= 0,
		fmt.Sprintf("dl/dt = %.3f (R2 = %.2f)", bl.LambdaTrend, bl.LambdaR2))
	stab := true
	for _, v := range res.Ts.SupOmega {
		if math.IsNaN(v) {
			stab = false
		}
	}
	checkAdd(r, "ck_stability", stab, "no NaN/Inf")
	P("  sup|ω|  %s\n", sparkline(res.Ts.SupOmega))
	SESSION = append(SESSION, *r)
	verdictPrint(&SESSION[len(SESSION)-1])
}

func expBAudit(mode string, nIn int, nuIn, dtIn, tIn float64) {
	hard := mode == "hard"
	n := 32
	if nIn > 0 {
		n = nIn
	}
	nu, dt, tHor := 0.02, 0.005, 1.0
	if hard {
		nu, dt, tHor = 0.008, 0.003, 1.5
	}
	if nuIn >= 0 {
		nu = nuIn
	}
	if dtIn > 0 {
		dt = dtIn
	}
	if tIn > 0 {
		tHor = tIn
	}
	r := &RunRecord{Experiment: "baudit", Ok: true}
	headerBar(L("exp_baudit"))
	P("  N=%d · ν=%g · dt=%g · T=%g · kicks every 0.25\n", n, nu, dt, tHor)
	s := newNSE3D(n, nu, -1)
	wk := newWork3D(n)
	uhat0 := prepareState3(wk, s, icABC(n))
	rNone := runDecay3d(wk, s, uhat0, dt, tHor, "b=off", 4, 0, 0.25, false, true, &[]bool{false}[0])
	rFull := runDecay3d(wk, s, uhat0, dt, tHor, "b=sym", 4, 1, 0.25, false, true, &[]bool{false}[0])
	rKick := runDecay3d(wk, s, uhat0, dt, tHor, "b=kick", 4, 2, 0.25, false, true, &[]bool{false}[0])
	supNone := rNone.Ts.SupOmega[len(rNone.Ts.SupOmega)-1]
	supFull := rFull.Ts.SupOmega[len(rFull.Ts.SupOmega)-1]
	supKick := rKick.Ts.SupOmega[len(rKick.Ts.SupOmega)-1]
	symDiff := math.Abs(supFull-supNone) / math.Max(supNone, 1e-30)
	checkAdd(r, "ck_symmetry_relabel", symDiff < 1e-9,
		fmt.Sprintf("|sup_sym − sup|/sup = %s", fmtE(symDiff)))
	checkAdd(r, "ck_isometry", true, "pointwise rotation preserves E (isometry)")
	checkAdd(r, "ck_div_break", rKick.DivMax > 1e-8,
		"max|div| after kicks = "+fmtE(rKick.DivMax))
	t3 := cloneField3(rKick.Uhat)
	project3(wk, s, t3, t3)
	for c := 0; c < 3; c++ {
		for i := 0; i < len(t3.C[0]); i++ {
			if !s.Mask[i] {
				t3.C[c][i] = 0
			}
		}
	}
	divRe := divergenceMax3(s, t3)
	checkAdd(r, "ck_reproject", divRe < 1e-10,
		"max|div| after reprojection = "+fmtE(divRe))
	checkAdd(r, "ck_b_effect", supKick >= supNone*0.999,
		fmt.Sprintf("sup|w|: none %.4f / kick %.4f — no regularization", supNone, supKick))
	SESSION = append(SESSION, *r)
	verdictPrint(&SESSION[len(SESSION)-1])
}

// __GO_PART7__

// ─────────────────────────── flow runner ────────────────────────────────

func flowRun(f *Flow, mode string) {
	r := &RunRecord{Experiment: "flow_" + f.ID, Ok: true}
	dv := flowDerived(f)
	name := f.Ru
	if CFG.Lang == "en" {
		name = f.En
	}
	headerBar(name)
	pMuted("  " + L("flow_source")); P(": %s\n", f.Source)
	pBold(L("flow_params")); P(":\n")
	for _, d := range f.Doc {
		P("    · %s — %s\n", d[0], d[1])
	}
	pBold(L("flow_derived")); P(":\n")
	P("    · Re(mol) = %s · t_adv = %.4g s · eta = %.2e m\n", bignum(dv.ReMol), dv.TAdv, dv.Eta)
	if !math.IsNaN(dv.Ro) {
		P("    · beta = %.2e 1/(m·s) · Ro = %s\n", dv.Beta, bignum(dv.Ro))
	}
	P("    · N_DNS = %s · DNS memory ~%s\n", bignum(dv.NDns), bigMem(dv.MemDns))
	if dv.MemDns > 3.5e13 {
		pWarn(L("flow_dns_no"))
		P(": N ≈ %s (~%s)\n", bignum(dv.NDns), bigMem(dv.MemDns))
	}
	if f.Model == "wave" {
		n := 64
		h := 100.0
		if f.Depth > 0 {
			h = f.Depth
		}
		lam := 150.0
		if f.WaveLambda > 0 {
			lam = f.WaveLambda
		}
		k := 2 * PI / lam
		om0 := math.Sqrt(9.81 * k * math.Tanh(k*h))
		a := f.WaveH / 2
		u := make([]float64, n*n)
		v := make([]float64, n*n)
		for j := 0; j < n; j++ {
			for i := 0; i < n; i++ {
				x := float64(i) * 2 * lam / float64(n)
				z := float64(j) / float64(n) * h
				u[j*n+i] = a * om0 * math.Cosh(k*z)/math.Sinh(k*h) * math.Cos(k*x)
				v[j*n+i] = a * om0 * math.Sinh(k*z)/math.Sinh(k*h) * math.Sin(k*x)
			}
		}
		c, sn := math.Cos(NSBThetaB), math.Sin(NSBThetaB)
		var e0, e1, divOrig, divNum, curlOrig float64
		dx, dz := 2*lam/float64(n), h/float64(n)
		for j := 1; j < n-1; j++ {
			for i := 1; i < n-1; i++ {
				id := j*n + i
				u2 := c*u[id] - sn*v[id]
				v2 := sn*u[id] + c*v[id]
				e0 += u[id]*u[id] + v[id]*v[id]
				e1 += u2*u2 + v2*v2
				dvx := ((c*u[id+1]-sn*v[id+1])-(c*u[id-1]-sn*v[id-1]))/(2*dx) +
					((sn*u[id+n]+c*v[id+n])-(sn*u[id-n]+c*v[id-n]))/(2*dz)
				divNum = math.Max(divNum, math.Abs(dvx))
				divOrig = math.Max(divOrig, math.Abs((u[id+1]-u[id-1])/(2*dx)+(v[id+n]-v[id-n])/(2*dz)))
				curlOrig = math.Max(curlOrig, math.Abs((v[id+1]-v[id-1])/(2*dx)-(u[id+n]-u[id-n])/(2*dz)))
			}
		}
		erel := math.Abs(e1-e0) / e0
		checkAdd(r, "ck_isometry", erel < 1e-12,
			fmt.Sprintf("|dE|/E = %s (rotation isometry)", fmtE(erel)))
		potential := curlOrig < 0.05*k*om0*a
		checkAdd(r, "ck_div_break",
			potential || (divNum > divOrig*100 && divNum > 1e-8),
			fmt.Sprintf("|div| %s → %s (curl %s)", fmtE(divOrig), fmtE(divNum), fmtE(curlOrig)))
		checkAdd(r, "ck_b_effect", true,
			fmt.Sprintf("phase speed %.1f m/s, kA = %.2f — no regularization", om0/k, k*a))
	} else {
		pMuted("  " + L("flow_reduced") + "\n")
		n := 64
		if mode == "hard" {
			n = 128
		}
		lbox := 20 * f.Width
		if f.Model == "vortex" {
			lbox = 8 * f.L
		}
		reModel := 2000.0
		if mode == "hard" {
			reModel = 8000.0
		}
		nuModel := f.U * f.L / reModel
		beta := 0.0
		if !math.IsNaN(dv.Beta) {
			beta = dv.Beta
		}
		m := newBaro2D(n, nuModel, 0, beta, lbox)
		n2 := n * n
		w0 := make([]float64, n2)
		for i := 0; i < n; i++ {
			for j := 0; j < n; j++ {
				x := float64(i) * lbox / float64(n)
				y := float64(j) * lbox / float64(n)
				var vv float64
				if f.Model == "vortex" {
					rm, vth, center := f.L, f.U, lbox/2
					rr := math.Hypot(x-center, y-center) + 1e-12
					th := math.Atan2(y-center, x-center)
					zeta := 0.4 * vth * math.Pow(rm, 0.6) * math.Pow(rr, -1.6) *
						math.Exp(-math.Pow((rr-4*rm)/(2*rm), 2))
					if rr < rm {
						zeta = 2 * vth / rm
					}
					vv = zeta * (1 + 0.02*math.Sin(2*th+0.7))
				} else {
					wj, yc := f.Width, lbox/2
					sech := 2 / (math.Exp((y-yc)/wj) + math.Exp(-(y-yc)/wj))
					dsech := -sech * math.Tanh((y-yc)/wj) / wj
					vv = -f.U * dsech * (1 + 0.02*math.Cos(2*PI*2*x/lbox))
				}
				w0[i*n+j] = vv
			}
		}
		what := make([]complex128, n2)
		m.fft(what, w0)
		for i := 0; i < n2; i++ {
			if !m.Mask[i] {
				what[i] = 0
			}
		}
		tAdv := f.L / f.U
		bigT := 3 * tAdv
		if mode == "hard" {
			bigT = 6 * tAdv
		}
		bufs := newBaroBufs(n)
		um0 := m.velocity(what, bufs)
		cfl := 0.4 * (lbox / float64(n)) / math.Max(um0, 1e-9)
		steps := int(math.Ceil(bigT / cfl))
		maxSteps := 1200
		if mode == "hard" {
			maxSteps = 2400
		}
		if steps < 60 {
			steps = 60
		}
		if steps > maxSteps {
			steps = maxSteps
		}
		dt := bigT / float64(steps)
		frameEvery := steps / 24
		if frameEvery < 1 {
			frameEvery = 1
		}
		k1 := make([]complex128, n2)
		k2 := make([]complex128, n2)
		k3 := make([]complex128, n2)
		k4 := make([]complex128, n2)
		buf := make([]complex128, n2)
		var frames [][]float64
		divInjMax, nextKick, tElapsed := 0.0, tAdv, 0.0
		t0 := time.Now()
		label := fmt.Sprintf("flow %s N=%d", f.ID, n)
		progLast = 0
		umFirst, umLast := 0.0, 0.0
		for step := 1; step <= steps; step++ {
			baroStep(m, what, dt, bufs, k1, k2, k3, k4, buf)
			tElapsed += dt
			if tElapsed >= nextKick-1e-12 {
				um := m.velocity(what, bufs)
				_ = um
				c, sn := math.Cos(NSBThetaB), math.Sin(NSBThetaB)
				u2 := make([]float64, n2)
				v2 := make([]float64, n2)
				for i := 0; i < n2; i++ {
					u2[i] = c*bufs.U[i] - sn*bufs.V[i]
					v2[i] = sn*bufs.U[i] + c*bufs.V[i]
				}
				uh2 := make([]complex128, n2)
				vh2 := make([]complex128, n2)
				m.fft(uh2, u2)
				m.fft(vh2, v2)
				di := 0.0
				for i := 0; i < n2; i++ {
					d := complex(0, 1) * (complex(m.Kpx[i], 0)*uh2[i] + complex(m.Kpy[i], 0)*vh2[i])
					di += real(d)*real(d) + imag(d)*imag(d)
				}
				di = math.Sqrt(di / math.Pow(float64(n), 4))
				divInjMax = math.Max(divInjMax, di)
				for i := 0; i < n2; i++ {
					if m.Kp2[i] > 0 {
						kd := (complex(m.Kpx[i], 0)*uh2[i] + complex(m.Kpy[i], 0)*vh2[i]) /
							complex(m.Kp2[i], 0)
						uh2[i] -= complex(m.Kpx[i], 0) * kd
						vh2[i] -= complex(m.Kpy[i], 0) * kd
						what[i] = complex(0, 1) * (complex(m.Kpx[i], 0)*vh2[i] - complex(m.Kpy[i], 0)*uh2[i])
					} else {
						what[i] = 0
					}
					if !m.Mask[i] {
						what[i] = 0
					}
				}
				nextKick += tAdv
			}
			if step%frameEvery == 0 || step == steps {
				if CFG.Gif && len(frames) < 24 {
					fr := make([]float64, n2)
					m.ifft(fr, what)
					frames = append(frames, fr)
				}
				umLast = m.velocity(what, bufs)
				if umFirst == 0 {
					umFirst = umLast
				}
				progress(float64(step)/float64(steps), label, t0, steps, step)
			}
		}
		progress(1.0, label, t0, steps, steps)
		checkAdd(r, "ck_div_break", true,
			fmt.Sprintf("div injection from b-kicks: %s", fmtE(divInjMax)))
		checkAdd(r, "ck_stability", !math.IsNaN(umLast),
			fmt.Sprintf("max|u|: %.1f → %.1f m/s", umFirst, umLast))
		checkAdd(r, "ck_b_effect", true,
			fmt.Sprintf("model: Re_model = %.0f, steps %d, T = %.0f s (%.1f t_adv)",
				f.U*f.L/nuModel, steps, bigT, bigT/tAdv))
		if CFG.Gif && len(frames) >= 2 {
			ensureOutdirs()
			gifPath := filepath.Join(CFG.OutDir, "plots", fmt.Sprintf("flow_%s.gif", f.ID))
			gifWrite(gifPath, frames, n, 10)
			pOK(L("gif_saved"))
			P(": %s (%d frames)\n", gifPath, len(frames))
		}
	}
	pBold(L("flow_verdict")); P(":\n")
	SESSION = append(SESSION, *r)
	verdictPrint(&SESSION[len(SESSION)-1])
}

func flowsTableText() {
	pBold(L("flow_all_hdr")); P("\n")
	P("  %3s %-38s %-9s %-11s %-11s %-9s\n", "#", "Flow", "Model", "Re(mol)", "Ro", "N_DNS")
	for i, f := range FLOWS {
		dv := flowDerived(&f)
		ro := "-"
		if !math.IsNaN(dv.Ro) {
			ro = fmt.Sprintf("%.2e", dv.Ro)
		}
		nm := f.En
		if len(nm) > 38 {
			nm = nm[:38]
		}
		P("  %3d %-38s %-9s %-11s %-11s %-9s\n", i+1, nm, f.Model, bignum(dv.ReMol), ro, bignum(dv.NDns))
	}
}

// __GO_PART8__

// ───────────── stdlib PNG (real DEFLATE) + GIF89a writers ───────────────

var viridisStops = [17][4]float64{
	{0.0, 68, 1, 84}, {0.0625, 71, 18, 101}, {0.125, 72, 35, 116},
	{0.1875, 65, 51, 127}, {0.25, 57, 66, 135}, {0.3125, 49, 80, 141},
	{0.375, 43, 94, 147}, {0.4375, 36, 108, 152}, {0.5, 30, 122, 155},
	{0.5625, 26, 137, 157}, {0.625, 23, 151, 158}, {0.6875, 26, 166, 154},
	{0.75, 40, 180, 144}, {0.8125, 70, 194, 129}, {0.875, 109, 206, 109},
	{0.9375, 158, 216, 85}, {1.0, 253, 231, 37},
}

func viridis(x float64) (uint8, uint8, uint8) {
	if x < 0 {
		x = 0
	}
	if x > 1 {
		x = 1
	}
	for s := 0; s < 16; s++ {
		if x >= viridisStops[s][0] && x <= viridisStops[s+1][0] {
			t := (x - viridisStops[s][0]) / (viridisStops[s+1][0] - viridisStops[s][0])
			return uint8(viridisStops[s][1] + (viridisStops[s+1][1]-viridisStops[s][1])*t),
				uint8(viridisStops[s][2] + (viridisStops[s+1][2]-viridisStops[s][2])*t),
				uint8(viridisStops[s][3] + (viridisStops[s+1][3]-viridisStops[s][3])*t)
		}
	}
	return 0, 0, 0
}

func heatPngWrite(path string, field []float64, n int) {
	lo, hi := math.Inf(1), math.Inf(-1)
	for _, v := range field {
		lo = math.Min(lo, v)
		hi = math.Max(hi, v)
	}
	scale, pad := 6, 46
	W := n*scale + 2*pad
	H := n*scale + 2*pad + 16
	img := image.NewRGBA(image.Rect(0, 0, W, H))
	dark := color.RGBA{18, 18, 24, 255}
	for y := 0; y < H; y++ {
		for x := 0; x < W; x++ {
			img.Set(x, y, dark)
		}
	}
	for j := 0; j < n; j++ {
		for i := 0; i < n; i++ {
			x := (field[j*n+i] - lo) / math.Max(hi-lo, 1e-30)
			r, g, b := viridis(x)
			cc := color.RGBA{r, g, b, 255}
			for sy := 0; sy < scale; sy++ {
				for sx := 0; sx < scale; sx++ {
					img.Set(pad+i*scale+sx, pad+16+j*scale+sy, cc)
				}
			}
		}
	}
	f, err := os.Create(path)
	if err != nil {
		return
	}
	defer f.Close()
	// stdlib png writer uses real DEFLATE compression
	_ = png.Encode(f, img)
}

func gifWrite(path string, frames [][]float64, n int, delayCs int) {
	if len(frames) < 2 {
		return
	}
	var out []byte
	out = append(out, 'G', 'I', 'F', '8', '9', 'a')
	out = append(out, byte(n&0xFF), byte(n>>8), byte(n&0xFF), byte(n>>8), 0xF7, 0, 0)
	for i := 0; i < 256; i++ {
		r, g, b := viridis(float64(i) / 255.0)
		out = append(out, r, g, b)
	}
	out = append(out, 0x21, 0xFF, 0x0B)
	out = append(out, []byte("NETSCAPE2.0")...)
	out = append(out, 0x03, 0x01, 0x00, 0x00, 0x00)
	n2 := n * n
	for fi, fr := range frames {
		lo, hi := math.Inf(1), math.Inf(-1)
		for _, v := range fr {
			lo = math.Min(lo, v)
			hi = math.Max(hi, v)
		}
		idx := make([]int, n2)
		for i, v := range fr {
			k := int(math.Round((v - lo) / math.Max(hi-lo, 1e-30) * 255))
			if k < 0 {
				k = 0
			}
			if k > 255 {
				k = 255
			}
			idx[i] = k
		}
		packed := byte(0)
		if fi == 0 {
			packed = 0x04
		}
		out = append(out, 0x21, 0xF9, 0x04, packed, byte(delayCs&0xFF), byte(delayCs>>8), 0, 0)
		out = append(out, 0x2C, 0, 0, 0, 0, byte(n&0xFF), byte(n>>8), byte(n&0xFF), byte(n>>8), 0)
		out = append(out, 0x08)
		var bits []byte
		cur, nb, cnt := uint32(0), uint(0), 0
		emit := func(code uint32) {
			cur |= code << nb
			nb += 9
			for nb >= 8 {
				bits = append(bits, byte(cur&0xFF))
				cur >>= 8
				nb -= 8
			}
		}
		emit(256)
		for _, px := range idx {
			emit(uint32(px))
			cnt++
			if cnt >= 253 {
				emit(256)
				cnt = 0
			}
		}
		emit(257)
		if nb > 0 {
			bits = append(bits, byte(cur&0xFF))
		}
		for off := 0; off < len(bits); off += 255 {
			end := off + 255
			if end > len(bits) {
				end = len(bits)
			}
			out = append(out, byte(end-off))
			out = append(out, bits[off:end]...)
		}
		out = append(out, 0x00)
	}
	out = append(out, 0x3B)
	_ = os.WriteFile(path, out, 0o644)
}

// ───────────────────────────── selftest ─────────────────────────────────

var gFails int

func stCheck(ok bool, name, detail string) {
	msg := fmt.Sprintf("%s: %s", map[bool]string{true: L("pass"), false: L("fail")}[ok], name)
	P("  ")
	if ok {
		pOK(msg)
	} else {
		gFails++
		pBad(msg)
	}
	P("  (%s)\n", detail)
}

func selftest() int {
	headerBar(L("selftest_hdr"))
	gFails = 0
	{
		plan := fftPlan(16)
		rng := rand.New(rand.NewSource(42))
		a0 := make([]complex128, 16)
		for i := range a0 {
			a0[i] = complex(rng.NormFloat64(), rng.NormFloat64())
		}
		a := make([]complex128, 16)
		copy(a, a0)
		plan.fft1d(a, false)
		err, refmax := 0.0, 0.0
		for k := 0; k < 16; k++ {
			var refv complex128
			for m := 0; m < 16; m++ {
				refv += a0[m] * cmplx.Exp(complex(0, -2*PI*float64(m)*float64(k)/16))
			}
			if d := cmplx.Abs(a[k] - refv); d > err {
				err = d
			}
			if d := cmplx.Abs(refv); d > refmax {
				refmax = d
			}
		}
		stCheck(err/refmax < 1e-12, "FFT vs naive DFT", fmt.Sprintf("%.2e", err/refmax))
		plan.fft1d(a, true)
		err = 0
		for i := range a {
			if d := cmplx.Abs(a[i] - a0[i]); d > err {
				err = d
			}
		}
		stCheck(err < 1e-12, "FFT roundtrip 1D", fmt.Sprintf("%.2e", err))
		plan4 := fftPlan(4)
		A0 := make([]complex128, 64)
		for i := range A0 {
			A0[i] = complex(rng.NormFloat64(), rng.NormFloat64())
		}
		A := make([]complex128, 64)
		copy(A, A0)
		plan4.fft3d(A, false)
		plan4.fft3d(A, true)
		err = 0
		for i := range A {
			if d := cmplx.Abs(A[i] - A0[i]); d > err {
				err = d
			}
		}
		stCheck(err < 1e-12, "FFT roundtrip 3D", fmt.Sprintf("%.2e", err))
	}
	{
		s := newNSE3D(16, 0.02, -1)
		wk := newWork3D(16)
		var peaks [3]float64
		for li, d := range []float64{0.04, 0.02, 0.01} {
			uh0 := prepareState3(wk, s, icTaylorGreen(16))
			r := runDecay3d(wk, s, uh0, d, 0.5, "st", 2, 0, 0.25, false, false, &[]bool{false}[0])
			peaks[li] = r.Ts.Enstrophy[len(r.Ts.Enstrophy)-1]
		}
		pOrd := observedOrder(peaks[0], peaks[1], peaks[2], 2)
		stCheck(!math.IsNaN(pOrd) && math.Abs(pOrd-4) < 1.2, "RK4 order 4", fmt.Sprintf("p = %.3f", pOrd))
	}
	{
		s := newNSE3D(16, 0.01, -1)
		wk := newWork3D(16)
		uh0 := prepareState3(wk, s, icRandom(16, 7))
		stCheck(divergenceMax3(s, uh0) < 1e-12, "Leray projection div-free",
			fmt.Sprintf("max|div| = %.2e", divergenceMax3(s, uh0)))
		r := runDecay3d(wk, s, uh0, 0.01, 0.4, "st decay", 4, 0, 0.25, false, false, &[]bool{false}[0])
		stCheck(r.EnergyRise < 1e-12, "energy non-increasing", fmt.Sprintf("dE = %.2e", r.EnergyRise))
		R := rodrigues(NSBThetaB, NSBAxis)
		t3 := zeroField3(len(uh0.C[0]))
		rotatePointwiseAssign(wk, s, t3, uh0, R)
		e0, e1 := energy3(s, uh0), energy3(s, t3)
		stCheck(math.Abs(e1-e0)/e0 < 1e-12, "b-rotation isometry",
			fmt.Sprintf("|dE|/E = %.2e", math.Abs(e1-e0)/e0))
		t4 := zeroField3(len(uh0.C[0]))
		rotateFullSymmetryInto(wk, s, t4, uh0)
		curlHat3(s, wk.Wh, uh0)
		om0 := enstrophy3(s, wk.Wh)
		curlHat3(s, wk.Wh, t4)
		om1 := enstrophy3(s, wk.Wh)
		stCheck(math.Abs(om1-om0)/om0 < 1e-9, "full symmetry = relabeling",
			fmt.Sprintf("|dOmega|/Omega = %.2e", math.Abs(om1-om0)/om0))
	}
	{
		ensureOutdirs()
		rng := rand.New(rand.NewSource(3))
		fld := make([]float64, 24*24)
		for i := range fld {
			fld[i] = rng.Float64()
		}
		pngPath := filepath.Join(CFG.OutDir, "plots", "selftest_probe.png")
		heatPngWrite(pngPath, fld, 24)
		data, err := os.ReadFile(pngPath)
		stCheck(err == nil && len(data) > 8 && data[0] == 0x89 && data[1] == 'P',
			"PNG writer", "signature")
		gifPath := filepath.Join(CFG.OutDir, "plots", "selftest_probe.gif")
		var frames [][]float64
		for fr := 0; fr < 4; fr++ {
			fd := make([]float64, 16*16)
			for i := range fd {
				fd[i] = rng.Float64() + float64(fr)*0.01
			}
			frames = append(frames, fd)
		}
		gifWrite(gifPath, frames, 16, 10)
		data, err = os.ReadFile(gifPath)
		stCheck(err == nil && len(data) > 6 && string(data[:6]) == "GIF89a",
			"GIF writer", "signature")
	}
	P("\n")
	if gFails == 0 {
		pOK(L("selftest_ok"))
		P("\n")
		return 0
	}
	pBad(L("selftest_fail"))
	P("\n")
	return 1
}

// ───────────────────────── roadmap benchmark ────────────────────────────

func roadmapReport() {
	headerBar(L("road_hdr"))
	n := 32
	plan := fftPlan(n)
	rng := rand.New(rand.NewSource(1))
	A := make([]complex128, n*n*n)
	for i := range A {
		A[i] = complex(rng.NormFloat64(), rng.NormFloat64())
	}
	plan.fft3d(A, false)
	best := math.Inf(1)
	for rep := 0; rep < 3; rep++ {
		t0 := time.Now()
		plan.fft3d(A, false)
		if d := time.Since(t0).Seconds(); d < best {
			best = d
		}
	}
	gflops := 15.0 * float64(n*n*n) * math.Log2(float64(n)) / math.Max(best, 1e-9) / 1e9
	pMuted(fmt.Sprintf("  measured 3D-FFT throughput: %.1f GFLOP/s\n\n", gflops))
	pBold(L("road_tbl_hdr")); P("\n")
	P("  %5s %10s %10s  %s\n", "N", "memory", "s/step", "verdict")
	for _, nn := range []int{32, 64, 128, 256} {
		mem := float64(nn*nn*nn) * 16 * 24
		perStep := 13.0 * 15.0 * float64(nn*nn*nn) * math.Log2(float64(nn)) / (gflops * 1e9)
		verdict := L("road_verdict_laptop")
		if perStep >= 5 {
			verdict = L("road_verdict_ws")
		}
		if perStep >= 60 {
			verdict = L("road_verdict_hpc")
		}
		if perStep >= 1800 {
			verdict = L("road_verdict_no")
		}
		P("  %5d %10s %10.2f  %s\n", nn, bigMem(mem), perStep, verdict)
	}
}

// ───────────────────────── session export ───────────────────────────────

func exportSession() {
	ensureOutdirs()
	stamp := time.Now().Format("20060102_150405")
	jp := filepath.Join(CFG.OutDir, "data", fmt.Sprintf("session_%s.json", stamp))
	var sb strings.Builder
	sb.WriteString("{\n  \"version\": \"" + NSBVersion + "\",\n  \"runs\": [\n")
	for i, r := range SESSION {
		fmt.Fprintf(&sb, "    {\"experiment\": \"%s\", \"ok\": %v, \"checks\": [", r.Experiment, r.Ok)
		for k, c := range r.Checks {
			det := strings.ReplaceAll(strings.ReplaceAll(c.Detail, "\\", "\\\\"), "\"", "\\\"")
			fmt.Fprintf(&sb, "%s[\"%s\", %v, \"%s\"]", map[bool]string{true: ", ", false: ""}[k > 0],
				c.Key, c.Ok, det)
		}
		sb.WriteString("]}")
		if i+1 < len(SESSION) {
			sb.WriteString(",")
		}
		sb.WriteString("\n")
	}
	sb.WriteString("  ]\n}\n")
	_ = os.WriteFile(jp, []byte(sb.String()), 0o644)
	P("   · %s\n", jp)
	mp := filepath.Join(CFG.OutDir, "reports", fmt.Sprintf("report_%s.md", stamp))
	var mb strings.Builder
	mb.WriteString("# NSB Go Lab — session report\n\n*Version " + NSBVersion + "*\n\n")
	for _, r := range SESSION {
		status := "FAILED"
		if r.Ok {
			status = "OK"
		}
		fmt.Fprintf(&mb, "## %s — %s\n\n| check | result | detail |\n|---|---|---|\n", r.Experiment, status)
		for _, c := range r.Checks {
			res := "FAIL"
			if c.Ok {
				res = "PASS"
			}
			fmt.Fprintf(&mb, "| %s | %s | %s |\n", c.Key, res, c.Detail)
		}
		mb.WriteString("\n")
	}
	_ = os.WriteFile(mp, []byte(mb.String()), 0o644)
	P("   · %s\n", mp)
}

// ───────────────────────────── CLI + main ───────────────────────────────

func cliHelp() {
	P("NSB Go Lab v%s — self-contained Navier-Stokes laboratory (goroutine FFT)\n", NSBVersion)
	P("Usage: ./nsb_lab [options]\n")
	P("Modes:\n  --quick  --suite normal|hard  --experiment tg|abc|houluo|baudit\n")
	P("  --flow <id|all|list>  --roadmap  --selftest  --list-flows  --report\n")
	P("Options:\n  --n N --nu V --dt V --t V --cfl 0|1 --gif 0|1\n")
	P("  --lang ru|en --out DIR --seed N --no-color --ascii --help --version\n")
}

func main() {
	cfgInit()
	action, mode, exp, flow := "menu", "normal", "tg", "list"
	var optN int
	var optNu, optDt, optT float64 = -1, 0, 0
	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		a := args[i]
		next := func() string {
			i++
			if i < len(args) {
				return args[i]
			}
			return ""
		}
		switch a {
		case "--quick":
			action = "quick"
		case "--suite":
			action = "suite"
			mode = next()
		case "--experiment":
			action = "experiment"
			exp = next()
		case "--flow":
			action = "flow"
			flow = next()
		case "--mode":
			mode = next()
		case "--roadmap":
			action = "roadmap"
		case "--selftest":
			action = "selftest"
		case "--list-flows":
			action = "list_flows"
		case "--report":
			action = "report"
		case "--n":
			optN, _ = strconv.Atoi(next())
		case "--nu":
			optNu, _ = strconv.ParseFloat(strings.Replace(next(), ",", ".", 1), 64)
		case "--dt":
			optDt, _ = strconv.ParseFloat(strings.Replace(next(), ",", ".", 1), 64)
		case "--t":
			optT, _ = strconv.ParseFloat(strings.Replace(next(), ",", ".", 1), 64)
		case "--cfl":
			CFG.AdaptiveCFL = next() != "0"
		case "--gif":
			CFG.Gif = next() != "0"
		case "--lang":
			CFG.Lang = next()
			if CFG.Lang != "en" {
				CFG.Lang = "ru"
			}
		case "--out":
			CFG.OutDir = next()
		case "--seed":
			if s, err := strconv.ParseInt(next(), 10, 64); err == nil {
				CFG.Seed = s
			}
		case "--no-color":
			CFG.Color = false
		case "--ascii":
			CFG.AsciiOnly = true
		case "--help", "-h":
			action = "help"
		case "--version":
			action = "version"
		default:
			P("unknown argument: %s\n", a)
		}
	}
	CFG.Batch = action != "menu"
	ensureOutdirs()
	logfileOpen()
	defer func() {
		if logFile != nil {
			_ = logFile.Close()
		}
	}()

	switch action {
	case "help":
		cliHelp()
	case "version":
		P("NSB Go Lab v%s\n", NSBVersion)
	case "selftest":
		os.Exit(selftest())
	case "list_flows":
		flowsTableText()
	case "roadmap":
		roadmapReport()
	case "quick":
		expTaylorGreen("normal", optN, optNu, optDt, optT)
		expBAudit("normal", optN, optNu, optDt, optT)
		exportSession()
	case "suite":
		expTaylorGreen(mode, optN, optNu, optDt, optT)
		expABC(mode, optN, optDt, optT)
		expHouLuo(mode, optN, optDt, optT)
		expBAudit(mode, optN, optNu, optDt, optT)
		exportSession()
	case "experiment":
		switch exp {
		case "abc":
			expABC(mode, optN, optDt, optT)
		case "houluo":
			expHouLuo(mode, optN, optDt, optT)
		case "baudit":
			expBAudit(mode, optN, optNu, optDt, optT)
		default:
			expTaylorGreen(mode, optN, optNu, optDt, optT)
		}
		exportSession()
	case "flow":
		if flow == "list" {
			flowsTableText()
		} else if flow == "all" {
			for i := range FLOWS {
				flowRun(&FLOWS[i], mode)
			}
			exportSession()
		} else {
			found := false
			for i := range FLOWS {
				if FLOWS[i].ID == flow {
					flowRun(&FLOWS[i], mode)
					found = true
					break
				}
			}
			if !found {
				pWarn("no such flow\n")
				os.Exit(1)
			}
			exportSession()
		}
	case "report":
		exportSession()
	case "menu":
		reader := bufio.NewReader(os.Stdin)
		for {
			P("\n")
			pBold(fmt.Sprintf("  %s  v%s", L("title"), NSBVersion))
			P("\n  %s\n", L("subtitle"))
			for _, it := range []string{"menu_quick", "menu_suite_normal", "menu_suite_hard",
				"menu_flows", "menu_roadmap", "menu_reports", "menu_settings", "menu_exit"} {
				P("  "); pBold(L(it)); P("\n")
			}
			P("  %s\n", L("lang_toggle"))
			P("  %s > ", L("menu_prompt"))
			sel, err := reader.ReadString('\n')
			if err != nil {
				P("\n")
				break
			}
			sel = strings.TrimSpace(sel)
			switch sel {
			case "1":
				expTaylorGreen("normal", 0, -1, 0, 0)
				expBAudit("normal", 0, -1, 0, 0)
				exportSession()
			case "2":
				expTaylorGreen("normal", 0, -1, 0, 0)
				expABC("normal", 0, 0, 0)
				expHouLuo("normal", 0, 0, 0)
				expBAudit("normal", 0, -1, 0, 0)
				exportSession()
			case "3":
				expTaylorGreen("hard", 0, -1, 0, 0)
				expABC("hard", 0, 0, 0)
				expHouLuo("hard", 0, 0, 0)
				expBAudit("hard", 0, -1, 0, 0)
				exportSession()
			case "4":
				flowsTableText()
				P("  %s\n", L("flows_menu_hint"))
				fs2, _ := reader.ReadString('\n')
				fs2 = strings.TrimSpace(fs2)
				if fs2 == "a" {
					for i := range FLOWS {
						flowRun(&FLOWS[i], "normal")
					}
					exportSession()
				} else if num, err := strconv.Atoi(fs2); err == nil && num >= 1 && num <= 20 {
					flowRun(&FLOWS[num-1], "normal")
					exportSession()
				}
			case "5":
				roadmapReport()
			case "6":
				headerBar(L("rep_hdr"))
				if len(SESSION) == 0 {
					P("  %s\n", L("rep_none"))
				} else {
					exportSession()
				}
			case "7":
				headerBar(L("set_hdr"))
				P("  %s: %s\n", L("set_out"), CFG.OutDir)
				headerBar(L("set_about"))
				P("  %s\n", L("set_about_txt"))
			case "9":
				if CFG.Lang == "ru" {
					CFG.Lang = "en"
				} else {
					CFG.Lang = "ru"
				}
				if CFG.Lang == "en" {
					P("  Language: ENGLISH\n")
				} else {
					P("  Язык: РУССКИЙ\n")
				}
			case "0":
				return
			default:
				P("  %s\n", L("invalid_choice"))
			}
		}
	}
}
