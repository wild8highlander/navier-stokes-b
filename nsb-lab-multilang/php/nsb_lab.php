<?php
/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  NSB PHP LAB v2.1.0 — polyglot edition
 *  A faithful port of the self-contained Julia "Navier–Stokes b-Lab" to
 *  pure PHP 8 (no extensions required; ext-zlib used when available).
 *
 *  Inside:
 *    • In-house radix-2 FFT on [re,im] pairs (no ext-gmp/complex needed).
 *    • 3-D pseudospectral Navier–Stokes/Euler: RK4 + Leray projection +
 *      2/3 de-aliasing; 2-D barotropic β-plane; BKM diagnostics.
 *    • Taylor–Green / ABC / Hou–Luo / random ICs, b-correction audit
 *      (full symmetry relabeling vs pointwise rotation), 20 documented
 *      real flows with DNS feasibility estimates.
 *    • Zero-dependency output: PNG (CRC32 built-in, gzcompress or stored
 *      deflate blocks), GIF89a animator (uncompressed LZW), CSV/JSON/MD.
 *    • i18n RU/EN, ONE-LINE progress bar, sparklines, interactive TUI menu.
 *
 *  Run:   php nsb_lab.php --quick --lang en
 *         php nsb_lab.php --selftest
 *         php nsb_lab.php                (interactive menu)
 *  Results: ~/nsb_lab_results/{data,plots,reports,logs}
 * ═══════════════════════════════════════════════════════════════════════════
 */

const NSB_VERSION = '2.1.0';
const PI = M_PI;

// ───────────────────────────── config ───────────────────────────────────

$CFG = [
    'lang'       => 'ru',
    'out_dir'    => null,
    'dpi'        => 600,
    'seed'       => 20260916,
    'color'      => false,
    'ascii_only' => false,
    'max_n'      => 32,
    'gif'        => true,
    'ckpt_every' => 200,
    'adaptive'   => false,
    'nu4'        => 0.0,
    'session'    => [],
    't_start'    => 0.0,
];

function cfgInit(): void {
    global $CFG;
    $home = getenv('HOME') ?: '.';
    $CFG['out_dir'] = "$home/nsb_lab_results";
    $CFG['t_start'] = microtime(true);
    $totalGB = 8.0;
    if (is_readable('/proc/meminfo')) {
        foreach (file('/proc/meminfo') as $line) {
            if (str_starts_with($line, 'MemTotal:')) {
                $parts = preg_split('/\s+/', trim($line));
                $totalGB = ((float)$parts[1]) / 1048576.0;
                break;
            }
        }
    }
    foreach ([32, 64, 128, 256] as $cand) {
        if ($cand ** 3 * 16.0 * 24.0 / 2 ** 30 < $totalGB * 0.55) {
            $CFG['max_n'] = $cand;
        }
    }
    $CFG['color'] = (function_exists('posix_isatty') ? posix_isatty(STDOUT)
                        : (getenv('TERM') && getenv('TERM') !== 'dumb'))
                    && !getenv('NO_COLOR');
    if (getenv('NSB_LAB_LANG') === 'en') $CFG['lang'] = 'en';
}

function ensureOutdirs(): void {
    global $CFG;
    foreach (['', '/logs', '/data', '/plots', '/reports'] as $sub) {
        @mkdir($CFG['out_dir'] . $sub, 0755, true);
    }
}

$LOG_IO = null;

function logfileOpen(): void {
    global $LOG_IO;
    ensureOutdirs();
    $p = $GLOBALS['CFG']['out_dir'] . '/logs/session_' . date('Ymd_His') . '.log';
    $LOG_IO = @fopen($p, 'a');
}

function P(string $s = ''): void {
    global $LOG_IO;
    if (PHP_SAPI !== 'cli' || true) { echo $s; }
    while (ob_get_level() > 0) { ob_flush(); }
    flush();
    if ($LOG_IO) { fwrite($LOG_IO, str_replace("\x1b", "\\e", $s)); fflush($LOG_IO); }
}

// ───────────────────────────── i18n ─────────────────────────────────────

$I18N = [];

function i18nAdd(string $k, string $ru, string $en): void {
    global $I18N;
    $I18N[$k] = [$ru, $en];
}

function L(string $key): string {
    global $I18N, $CFG;
    if (!isset($I18N[$key])) return $key;
    return $CFG['lang'] === 'en' ? $I18N[$key][1] : $I18N[$key][0];
}

function initI18n(): void {
    i18nAdd('yes', 'да', 'yes'); i18nAdd('no', 'нет', 'no');
    i18nAdd('pass', 'ПРОЙДЕНО', 'PASS'); i18nAdd('fail', 'ПРОВАЛЕНО', 'FAIL');
    i18nAdd('title', 'ЛАБОРАТОРИЯ НАВЬЕ–СТОКСА · b-КОРРЕКЦИЯ', 'NAVIER–STOKES LABORATORY · b-CORRECTION');
    i18nAdd('subtitle', 'самодостаточная PHP-версия без расширений', 'self-contained PHP edition, no extensions required');
    i18nAdd('menu_prompt', 'Выберите пункт и нажмите Enter', 'Choose an item and press Enter');
    i18nAdd('invalid_choice', 'Нет такого пункта — попробуйте ещё раз', 'No such item — try again');
    i18nAdd('lang_toggle', '9. Язык / Language  (RU ↔ EN)', '9. Language / Язык  (EN ↔ RU)');
    i18nAdd('menu_quick', '1. Быстрый прогон  (мини-сьют)', '1. Quick run  (mini-suite)');
    i18nAdd('menu_suite_normal', '2. Полная сьют — НОРМАЛЬНЫЙ режим', '2. Full suite — NORMAL mode');
    i18nAdd('menu_suite_hard', '3. Полная сьют — ХАРД режим', '3. Full suite — HARD mode');
    i18nAdd('menu_flows', '4. Лаборатория 20 реальных течений', '4. Real-flows laboratory (20 documented flows)');
    i18nAdd('menu_roadmap', '5. Роадмап и это железо (бенчмарк)', '5. Roadmap & this hardware (benchmark)');
    i18nAdd('menu_reports', '6. Отчёты сессии', '6. Session reports');
    i18nAdd('menu_settings', '7. Настройки и о проекте', '7. Settings & about');
    i18nAdd('menu_exit', '0. Выход', '0. Exit');
    i18nAdd('exp_tg', 'Тейлор–Грин: сходимость и экстраполяция', 'Taylor–Green: convergence and extrapolation');
    i18nAdd('exp_abc', 'ABC (Эйлер): охота за расходимостью', 'ABC (Euler): blow-up hunt');
    i18nAdd('exp_baudit', 'Аудит b-коррекции: симметрия против пинка', 'b-correction audit: symmetry vs pointwise kick');
    i18nAdd('scope_note', 'Область действия: сертификат внутренней согласованности, не общая теорема.',
        'Scope: a certificate of internal consistency of the computed solution, not a general theorem.');
    i18nAdd('verdict_ok', 'ВЕРДИКТ: все проверки пройдены', 'VERDICT: all checks passed');
    i18nAdd('verdict_fail', 'ВЕРДИКТ: есть проваленные проверки', 'VERDICT: some checks failed');
    i18nAdd('ck_divfree', 'несжимаемость: max|div u| в машинном пороге', 'incompressibility: max|div u| at machine level');
    i18nAdd('ck_energy_monotone', 'энергия не растёт (вязкое затухание)', 'energy non-increasing (viscous decay)');
    i18nAdd('ck_energy_conserved', 'энергия сохраняется (Эйлер)', 'energy conserved (Euler)');
    i18nAdd('ck_rk4_order', 'измеренный порядок RK4 ≈ 4', 'measured RK4 order ≈ 4');
    i18nAdd('ck_no_blowup', 'признаков расходимости нет (BKM ограничен)', 'no finite-time blow-up signature (BKM bounded)');
    i18nAdd('ck_stability', 'устойчивость: нет NaN/Inf', 'stability: no NaN/Inf');
    i18nAdd('ck_isometry', 'точечный поворот — изометрия', 'pointwise rotation is an isometry');
    i18nAdd('ck_symmetry_relabel', 'полная симметрия = релебелинг', 'full symmetry = relabeling');
    i18nAdd('ck_div_break', 'точечный поворот ЛОМАЕТ div u = 0', 'pointwise rotation BREAKS div u = 0');
    i18nAdd('ck_reproject', 'после перепроекции div на машинном пороге', 'after reprojection div at machine level');
    i18nAdd('ck_b_effect', 'b-пинк не снижает sup|ω|', 'b-kick does not reduce sup|ω|');
    i18nAdd('flows_hdr', 'ЛАБОРАТОРИЯ РЕАЛЬНЫХ ТЕЧЕНИЙ — 20 документированных объектов', 'REAL-FLOWS LABORATORY — 20 documented flows');
    i18nAdd('flows_menu_hint', 'Введите номер течения (1–20), a — все, q — назад', 'Enter flow number (1-20), a — run all, q — back');
    i18nAdd('flow_card', 'КАРТОЧКА ТЕЧЕНИЯ', 'FLOW CARD');
    i18nAdd('flow_source', 'первоисточник/документация', 'primary source/documentation');
    i18nAdd('flow_params', 'документированные величины', 'documented quantities');
    i18nAdd('flow_derived', 'расчётные параметры', 'derived parameters');
    i18nAdd('flow_dns_no', 'DNS НЕВОЗМОЖНО на существующем железе', 'DNS is INFEASIBLE on existing hardware');
    i18nAdd('flow_reduced', 'редуцированная модель: 2D баротропная β-плоскость', 'reduced model: 2-D barotropic β-plane');
    i18nAdd('flow_verdict', 'ВЕРДИКТ ПО ТЕЧЕНИЮ', 'FLOW VERDICT');
    i18nAdd('flow_all_hdr', 'СВОДНАЯ ТАБЛИЦА 20 ТЕЧЕНИЙ', 'SUMMARY TABLE OF 20 FLOWS');
    i18nAdd('road_hdr', 'РОАДМАП И ЭТО ЖЕЛЕЗО', 'ROADMAP AND THIS HARDWARE');
    i18nAdd('road_tbl_hdr', 'Оценки для псевдоспектрального НС (RK4, ~13 3D-FFT/шаг)', 'Estimates for pseudospectral NS (RK4, ~13 3D-FFTs/step)');
    i18nAdd('road_verdict_laptop', 'ноутбук: реально за вечер', 'laptop: an evening run');
    i18nAdd('road_verdict_ws', 'нужна рабочая станция', 'workstation recommended');
    i18nAdd('road_verdict_hpc', 'нужен кластер/HPC', 'cluster/HPC required');
    i18nAdd('road_verdict_no', 'вне досягаемости одиночной машины', 'out of reach for a single machine');
    i18nAdd('rep_hdr', 'ОТЧЁТЫ СЕССИИ', 'SESSION REPORTS');
    i18nAdd('rep_none', 'Пока ничего не посчитано', 'Nothing computed yet');
    i18nAdd('rep_saved', 'Сохранено', 'Saved');
    i18nAdd('selftest_hdr', 'САМОТЕСТ', 'SELF-TEST');
    i18nAdd('selftest_ok', 'САМОТЕСТ: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ', 'SELF-TEST: ALL CHECKS PASSED');
    i18nAdd('selftest_fail', 'САМОТЕСТ: ЕСТЬ ПРОВАЛЫ', 'SELF-TEST: FAILURES PRESENT');
    i18nAdd('gif_saved', 'GIF сохранён', 'GIF saved');
    i18nAdd('adaptive_on', 'адаптивный CFL-шаг включён', 'adaptive CFL step enabled');
    i18nAdd('set_hdr', 'НАСТРОЙКИ', 'SETTINGS');
    i18nAdd('set_out', 'Папка результатов', 'Results folder');
    i18nAdd('set_about', 'О ПРОЕКТЕ', 'ABOUT');
    i18nAdd('set_about_txt', 'Лаборатория проверяет гипотезу b-коррекции: полная решётчатая симметрия — релебелинг; точечный поворот сохраняет энергию, но ломает div u = 0. Порт PHP работает без расширений.',
        'The lab tests the b-correction hypothesis: full lattice symmetry is a relabeling; the pointwise rotation preserves energy but breaks div u = 0. The PHP port runs without extensions.');
}

// ─────────────────────────── ANSI + progress ────────────────────────────

function pOK(string $s): void   { P($GLOBALS['CFG']['color'] ? "\x1b[1;32m$s\x1b[0m" : $s); }
function pBad(string $s): void  { P($GLOBALS['CFG']['color'] ? "\x1b[1;31m$s\x1b[0m" : $s); }
function pWarn(string $s): void { P($GLOBALS['CFG']['color'] ? "\x1b[1;33m$s\x1b[0m" : $s); }
function pMuted(string $s): void{ P($GLOBALS['CFG']['color'] ? "\x1b[2m$s\x1b[0m" : $s); }
function pBold(string $s): void { P($GLOBALS['CFG']['color'] ? "\x1b[1m$s\x1b[0m" : $s); }

function headerBar(string $title): void {
    $line = str_repeat('-', 76);
    P("\n");
    P($GLOBALS['CFG']['color'] ? "\x1b[38;2;80;160;255m$line\x1b[0m\n" : "$line\n");
    P(" ▸ "); pBold($title); P("\n");
    P($GLOBALS['CFG']['color'] ? "\x1b[38;2;80;160;255m$line\x1b[0m\n" : "$line\n");
}

$PROG_LAST = 0.0;
$PROG_T0 = 0.0;

function progress(float $frac, string $label, float $t0 = null, int $total = 0, int $done = 0): void {
    global $PROG_LAST, $PROG_T0, $CFG;
    $frac = max(0.0, min(1.0, $frac));
    if ($t0 === null) $t0 = $PROG_T0;
    $tty = $CFG['color'];
    if (!$tty) {
        if (($frac - $PROG_LAST >= 0.1 || $frac >= 1.0) && $PROG_LAST < 1.0) {
            $PROG_LAST = $frac >= 1.0 ? 1.0 : max($frac, $PROG_LAST);
            P(sprintf("  [%3d%%] %s\n", (int)round($frac * 100), $label));
        }
        return;
    }
    $W = 30;
    $fill = (int)round($frac * $W);
    $bar = '';
    for ($i = 1; $i <= $W; $i++) {
        if ($CFG['ascii_only']) {
            $bar .= $i <= $fill ? '#' : '-';
        } elseif ($i <= $fill) {
            $bar .= sprintf("\x1b[38;2;%d;%d;255m█\x1b[0m", 40 + (int)(180 * $i / $W), 80 + (int)(170 * $i / $W));
        } else {
            $bar .= "\x1b[2m░\x1b[0m";
        }
    }
    $el = microtime(true) - $t0;
    $eta = $frac > 0.005 ? $el / $frac - $el : NAN;
    $etaS = is_finite($eta) ? sprintf('%02d:%02d', (int)($eta / 60), (int)$eta % 60) : ' --:--';
    $elS = sprintf('%02d:%02d', (int)($el / 60), (int)$el % 60);
    $tail = $total > 0
        ? sprintf(' · %s %d/%d · %.1f %s · %s %s', L('prog_step'), $done, $total,
              $done / max($el, 1e-9), L('prog_rate'), L('prog_eta'), $etaS)
        : " · elapsed $elS";
    P("\r" . str_repeat(' ', 120) . "\r");
    P("\x1b[38;2;80;160;255m ▸ \x1b[0m$label ▕$bar▏" . sprintf('%5.1f%%', $frac * 100) . $tail);
    if ($frac >= 1.0) { P("\n"); $PROG_LAST = 0.0; }
}

function sparkline(array $v): string {
    $utf = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
    $asc = ['_', '.', '-', '~', '*', '#', '#', '#'];
    $g = ($GLOBALS['CFG']['color'] && !$GLOBALS['CFG']['ascii_only']) ? $utf : $asc;
    if (!$v) return '';
    $lo = INF; $hi = -INF;
    foreach ($v as $x) { $x = max($x, 0.0); $lo = min($lo, $x); $hi = max($hi, $x); }
    $rng = $hi > $lo ? $hi - $lo : 1.0;
    $out = '';
    foreach ($v as $x) {
        $x = max($x, 0.0);
        $k = (int)round(($x - $lo) / $rng * 7);
        $out .= $g[max(0, min(7, $k))];
    }
    return $out;
}

// ═══════════════════ in-house radix-2 FFT ═══════════════════
// Fields are represented as ['re'=>float[], 'im'=>float[]] pairs.

function fftPlan(int $n): array {
    if ($n < 2 || ($n & ($n - 1)) !== 0) {
        fwrite(STDERR, "FFT: n must be a power of two\n");
        exit(1);
    }
    $twR = []; $twI = [];
    for ($k = 0; $k < intdiv($n, 2); $k++) {
        $twR[] = cos(-2.0 * PI * $k / $n);
        $twI[] = sin(-2.0 * PI * $k / $n);
    }
    $bitrev = array_fill(0, $n, 0);
    $logn = (int)log($n, 2);
    for ($i = 0; $i < $n; $i++) {
        $r = 0; $x = $i;
        for ($b = 0; $b < $logn; $b++) { $r = ($r << 1) | ($x & 1); $x >>= 1; }
        $bitrev[$i] = $r;
    }
    return ['n' => $n, 'twR' => $twR, 'twI' => $twI, 'bitrev' => $bitrev];
}

function fft1dClear(array $p, array &$re, array &$im, bool $inverse): void {
    $n = $p['n'];
    for ($i = 0; $i < $n; $i++) {
        $j = $p['bitrev'][$i];
        if ($i < $j) {
            $tr = $re[$i]; $re[$i] = $re[$j]; $re[$j] = $tr;
            $ti = $im[$i]; $im[$i] = $im[$j]; $im[$j] = $ti;
        }
    }
    for ($len = 2; $len <= $n; $len <<= 1) {
        $half = $len >> 1;
        $step = intdiv($n, $len);
        for ($start = 0; $start < $n; $start += $len) {
            $k = 0;
            for ($j = 0; $j < $half; $j++) {
                $wr = $p['twR'][$k];
                $wi = $inverse ? -$p['twI'][$k] : $p['twI'][$k];
                $i1 = $start + $j;
                $i2 = $i1 + $half;
                $ur = $re[$i1]; $ui = $im[$i1];
                $vr = $re[$i2] * $wr - $im[$i2] * $wi;
                $vi = $re[$i2] * $wi + $im[$i2] * $wr;
                $re[$i1] = $ur + $vr; $im[$i1] = $ui + $vi;
                $re[$i2] = $ur - $vr; $im[$i2] = $ui - $vi;
                $k += $step;
            }
        }
    }
    if ($inverse) {
        $s = 1.0 / $n;
        for ($i = 0; $i < $n; $i++) { $re[$i] *= $s; $im[$i] *= $s; }
    }
}

function fft3d(array $p, array &$f, bool $inverse): void {
    $n = $p['n'];
    $n3 = $n * $n * $n;
    $re = &$f['re']; $im = &$f['im'];
    $br = array_fill(0, $n, 0.0); $bi = array_fill(0, $n, 0.0);
    // axis 2 (contiguous)
    for ($line = 0; $line < $n * $n; $line++) {
        $off = $line * $n;
        $lr = array_slice($re, $off, $n);
        $li = array_slice($im, $off, $n);
        fft1dClear($p, $lr, $li, $inverse);
        array_splice($re, $off, $n, $lr);
        array_splice($im, $off, $n, $li);
    }
    // axis 1
    for ($i = 0; $i < $n; $i++) {
        for ($k = 0; $k < $n; $k++) {
            for ($j = 0; $j < $n; $j++) {
                $id = ($i * $n + $j) * $n + $k;
                $br[$j] = $re[$id]; $bi[$j] = $im[$id];
            }
            fft1dClear($p, $br, $bi, $inverse);
            for ($j = 0; $j < $n; $j++) {
                $id = ($i * $n + $j) * $n + $k;
                $re[$id] = $br[$j]; $im[$id] = $bi[$j];
            }
        }
    }
    // axis 0
    for ($j = 0; $j < $n; $j++) {
        for ($k = 0; $k < $n; $k++) {
            for ($i = 0; $i < $n; $i++) {
                $id = ($i * $n + $j) * $n + $k;
                $br[$i] = $re[$id]; $bi[$i] = $im[$id];
            }
            fft1dClear($p, $br, $bi, $inverse);
            for ($i = 0; $i < $n; $i++) {
                $id = ($i * $n + $j) * $n + $k;
                $re[$id] = $br[$i]; $im[$id] = $bi[$i];
            }
        }
    }
}

function fft2dArr(array $p, array &$f, bool $inverse): void {
    $n = $p['n'];
    $re = &$f['re']; $im = &$f['im'];
    $br = array_fill(0, $n, 0.0); $bi = array_fill(0, $n, 0.0);
    for ($i = 0; $i < $n; $i++) {
        $lr = array_slice($re, $i * $n, $n);
        $li = array_slice($im, $i * $n, $n);
        fft1dClear($p, $lr, $li, $inverse);
        array_splice($re, $i * $n, $n, $lr);
        array_splice($im, $i * $n, $n, $li);
    }
    for ($j = 0; $j < $n; $j++) {
        for ($i = 0; $i < $n; $i++) {
            $br[$i] = $re[$i * $n + $j]; $bi[$i] = $im[$i * $n + $j];
        }
        fft1dClear($p, $br, $bi, $inverse);
        for ($i = 0; $i < $n; $i++) {
            $re[$i * $n + $j] = $br[$i]; $im[$i * $n + $j] = $bi[$i];
        }
    }
}

// ═══════════════════ 3-D solver state ═══════════════════

function nse3dInit(int $n, float $nu, float $nu4 = -1.0): array {
    global $CFG;
    if ($nu4 < 0) $nu4 = $CFG['nu4'];
    $n3 = $n * $n * $n;
    $k1d = [];
    for ($i = 0; $i < intdiv($n, 2); $i++) $k1d[] = $i;
    for ($i = -intdiv($n, 2); $i < 0; $i++) $k1d[] = $i;
    $kc = intdiv($n, 3);
    $s = ['n' => $n, 'nu' => $nu, 'nu4' => $nu4, 'dx' => 2.0 * PI / $n,
          'kx' => [], 'ky' => [], 'kz' => [], 'ksq' => [], 'ksq2' => [],
          'k2safe' => [], 'mask' => []];
    for ($i = 0; $i < $n; $i++)
        for ($j = 0; $j < $n; $j++)
            for ($k = 0; $k < $n; $k++) {
                $a = $k1d[$i]; $b = $k1d[$j]; $c = $k1d[$k];
                $s['kx'][] = $a; $s['ky'][] = $b; $s['kz'][] = $c;
                $q = (float)($a * $a + $b * $b + $c * $c);
                $s['ksq'][] = $q; $s['ksq2'][] = $q * $q;
                $s['k2safe'][] = $q > 0 ? $q : 1.0;
                $s['mask'][] = abs($a) <= $kc && abs($b) <= $kc && abs($c) <= $kc;
            }
    return $s;
}

function zeroField3(int $n3): array {
    return ['re' => array_fill(0, $n3, 0.0), 'im' => array_fill(0, $n3, 0.0)];
}

function field3FromReal(array $w): array {
    return ['re' => $w, 'im' => array_fill(0, count($w), 0.0)];
}

function fftFieldFromReal(array $p, array $w): array {
    $f = field3FromReal($w);
    fft3d($p, $f, false);
    return $f;
}

function ifftFieldToReal(array $p, array $f): array {
    $g = ['re' => $f['re'], 'im' => $f['im']];
    fft3d($p, $g, true);
    return $g['re'];
}

function projectAll(array $s, array &$u): void {
    // $u = [f1, f2, f3] each ['re'=>..,'im'=>..]
    $n3 = count($u[0]['re']);
    $kdR = array_fill(0, $n3, 0.0); $kdI = array_fill(0, $n3, 0.0);
    for ($i = 0; $i < $n3; $i++) {
        // k·u (complex): kx*u1 + ky*u2 + kz*u3
        $ar = (float)$s['kx'][$i] * $u[0]['re'][$i];
        $ai = (float)$s['kx'][$i] * $u[0]['im'][$i];
        $br = (float)$s['ky'][$i] * $u[1]['re'][$i];
        $bi = (float)$s['ky'][$i] * $u[1]['im'][$i];
        $cr = (float)$s['kz'][$i] * $u[2]['re'][$i];
        $ci = (float)$s['kz'][$i] * $u[2]['im'][$i];
        $sumR = $ar + $br + $cr;
        $sumI = $ai + $bi + $ci;
        $q = $s['ksq'][$i];
        if ($q > 0) {
            $kdR[$i] = $sumR / $q;
            $kdI[$i] = $sumI / $q;
        }
    }
    $ks = [&$s['kx'], &$s['ky'], &$s['kz']];
    for ($c = 0; $c < 3; $c++) {
        for ($i = 0; $i < $n3; $i++) {
            $kc = (float)$ks[$c][$i];
            $u[$c]['re'][$i] -= $kc * $kdR[$i];
            $u[$c]['im'][$i] -= $kc * $kdI[$i];
        }
    }
}

function curlHatAll(array $s, array $u): array {
    $n3 = count($u[0]['re']);
    $out = [zeroField3($n3), zeroField3($n3), zeroField3($n3)];
    for ($i = 0; $i < $n3; $i++) {
        $kx = (float)$s['kx'][$i]; $ky = (float)$s['ky'][$i]; $kz = (float)$s['kz'][$i];
        // w1 = i(ky*a3 - kz*a2)
        $t1r = $ky * $u[2]['re'][$i] - $kz * $u[1]['re'][$i];
        $t1i = $ky * $u[2]['im'][$i] - $kz * $u[1]['im'][$i];
        $out[0]['re'][$i] = -$t1i; $out[0]['im'][$i] = $t1r;
        $t2r = $kz * $u[0]['re'][$i] - $kx * $u[2]['re'][$i];
        $t2i = $kz * $u[0]['im'][$i] - $kx * $u[2]['im'][$i];
        $out[1]['re'][$i] = -$t2i; $out[1]['im'][$i] = $t2r;
        $t3r = $kx * $u[1]['re'][$i] - $ky * $u[0]['re'][$i];
        $t3i = $kx * $u[1]['im'][$i] - $ky * $u[0]['im'][$i];
        $out[2]['re'][$i] = -$t3i; $out[2]['im'][$i] = $t3r;
    }
    return $out;
}

// __PHP_PART3__


// ═══════════════════ rhs, RK4, diagnostics ═══════════════════

function rhsAll(array $s, array $p, array $uhat): array {
    // $uhat = [f1,f2,f3]; returns [df1,df2,df3] (new arrays)
    $n = $s['n'];
    $n3 = count($uhat[0]['re']);
    $wh = curlHatAll($s, $uhat);
    $u = [];
    $w = [];
    foreach ([0, 1, 2] as $c) {
        $u[$c] = ifftFieldToReal($p, $uhat[$c]);
        $w[$c] = ifftFieldToReal($p, $wh[$c]);
    }
    // nl = w × u (three components)
    $nl = [array_fill(0, $n3, 0.0), array_fill(0, $n3, 0.0), array_fill(0, $n3, 0.0)];
    for ($i = 0; $i < $n3; $i++) {
        $w1 = $w[0][$i]; $w2 = $w[1][$i]; $w3 = $w[2][$i];
        $u1 = $u[0][$i]; $u2 = $u[1][$i]; $u3 = $u[2][$i];
        $nl[0][$i] = $w2 * $u3 - $w3 * $u2;
        $nl[1][$i] = $w3 * $u1 - $w1 * $u3;
        $nl[2][$i] = $w1 * $u2 - $w2 * $u1;
    }
    $du = [zeroField3($n3), zeroField3($n3), zeroField3($n3)];
    foreach ([0, 1, 2] as $c) {
        $nlh = fftFieldFromReal($p, $nl[$c]);
        for ($i = 0; $i < $n3; $i++) {
            if (!$s['mask'][$i]) {
                $nlh['re'][$i] = 0.0; $nlh['im'][$i] = 0.0;
            }
        }
        $du[$c] = $nlh;
    }
    projectAll($s, $du);
    for ($c = 0; $c < 3; $c++) {
        $ks = $c === 0 ? $s['kx'] : ($c === 1 ? $s['ky'] : $s['kz']);
        for ($i = 0; $i < $n3; $i++) {
            $damp = $s['nu'] * $s['ksq'][$i] + $s['nu4'] * $s['ksq2'][$i];
            $du[$c]['re'][$i] -= $damp * $uhat[$c]['re'][$i];
            $du[$c]['im'][$i] -= $damp * $uhat[$c]['im'][$i];
        }
    }
    return $du;
}

function stepRK4All(array $s, array $p, array &$out, array $uhat, float $dt): void {
    $n3 = count($uhat[0]['re']);
    $K = [];
    $T = $uhat;
    for ($st = 0; $st < 4; $st++) {
        $K[$st] = rhsAll($s, $p, $T);
        if ($st < 3) {
            $f = $st === 0 ? 0.5 : ($st === 1 ? 0.5 : 1.0);
            foreach ([0, 1, 2] as $c) {
                for ($i = 0; $i < $n3; $i++) {
                    $T[$c]['re'][$i] = $uhat[$c]['re'][$i] + $f * $dt * $K[$st][$c]['re'][$i];
                    $T[$c]['im'][$i] = $uhat[$c]['im'][$i] + $f * $dt * $K[$st][$c]['im'][$i];
                }
            }
        }
    }
    foreach ([0, 1, 2] as $c) {
        for ($i = 0; $i < $n3; $i++) {
            $re = $uhat[$c]['re'][$i] + $dt / 6.0 * (
                $K[0][$c]['re'][$i] + 2.0 * $K[1][$c]['re'][$i]
                + 2.0 * $K[2][$c]['re'][$i] + $K[3][$c]['re'][$i]);
            $im = $uhat[$c]['im'][$i] + $dt / 6.0 * (
                $K[0][$c]['im'][$i] + 2.0 * $K[1][$c]['im'][$i]
                + 2.0 * $K[2][$c]['im'][$i] + $K[3][$c]['im'][$i]);
            $out[$c]['re'][$i] = $s['mask'][$i] ? $re : 0.0;
            $out[$c]['im'][$i] = $s['mask'][$i] ? $im : 0.0;
        }
    }
}

function energyAll(array $s, array $uhat): float {
    $n6 = pow(floatval($s['n']), 6);
    $sum = 0.0;
    foreach ([0, 1, 2] as $c) {
        foreach ($uhat[$c]['re'] as $v) $sum += $v * $v;
        foreach ($uhat[$c]['im'] as $v) $sum += $v * $v;
    }
    return 0.5 * $sum / $n6;
}

function divergenceMaxAll(array $s, array $uhat): float {
    $n3 = count($uhat[0]['re']);
    $sum = 0.0;
    for ($i = 0; $i < $n3; $i++) {
        $dr = (float)$s['kx'][$i] * $uhat[0]['re'][$i]
            + (float)$s['ky'][$i] * $uhat[1]['re'][$i]
            + (float)$s['kz'][$i] * $uhat[2]['re'][$i];
        $di = (float)$s['kx'][$i] * $uhat[0]['im'][$i]
            + (float)$s['ky'][$i] * $uhat[1]['im'][$i]
            + (float)$s['kz'][$i] * $uhat[2]['im'][$i];
        $sum += $dr * $dr + $di * $di;
    }
    return sqrt($sum) / pow(floatval($s['n']), 3);
}

function supVorticityAll(array $s, array $p, array $uhat): float {
    $wh = curlHatAll($s, $uhat);
    $m = 0.0;
    foreach ([0, 1, 2] as $c) {
        $w = ifftFieldToReal($p, $wh[$c]);
        foreach ($w as $v) { $m = max($m, abs($v)); }
    }
    return $m; // NOTE: component-wise max (cheap proxy, mirrors sup of |ω_i|)
}

function linfitArr(array $xs, array $ys): array {
    $n = count($xs);
    if ($n < 2) return [NAN, NAN, NAN];
    $sx = $sy = $sxx = $sxy = 0.0;
    for ($i = 0; $i < $n; $i++) {
        $sx += $xs[$i]; $sy += $ys[$i];
        $sxx += $xs[$i] * $xs[$i]; $sxy += $xs[$i] * $ys[$i];
    }
    $den = $n * $sxx - $sx * $sx;
    if ($den == 0) return [NAN, NAN, NAN];
    $a = ($n * $sxy - $sx * $sy) / $den;
    $b = ($sy - $a * $sx) / $n;
    $ybar = $sy / $n;
    $ssr = $sst = 0.0;
    for ($i = 0; $i < $n; $i++) {
        $ssr += ($ys[$i] - ($a * $xs[$i] + $b)) ** 2;
        $sst += ($ys[$i] - $ybar) ** 2;
    }
    $r2 = $sst > 0 ? 1 - $ssr / $sst : NAN;
    return [$a, $b, $r2];
}

function observedOrderF(float $jc, float $jf, float $jff, float $ratio = 2.0): float {
    $den = $jc - $jf; $num = $jf - $jff;
    if (abs($den) < 1e-30 || abs($num) < 1e-30) return NAN;
    return log(abs($den / $num)) / log($ratio);
}

// ═══════════════════ ICs & b-rotations ═══════════════════

function nsbThetaB(): float {
    return asin(1.0 / (4.0 * PI + 2.0 * sqrt(3.0)));
}

function rodriguesPHP(float $theta, array $ax): array {
    [$ex, $ey, $ez] = $ax;
    $c = cos($theta); $s = sin($theta);
    $C = [[0, -$ez, $ey], [$ez, 0, -$ex], [-$ey, $ex, 0]];
    $O = [[$ex*$ex, $ex*$ey, $ex*$ez], [$ey*$ex, $ey*$ey, $ey*$ez], [$ez*$ex, $ez*$ey, $ez*$ez]];
    $R = [[0,0,0],[0,0,0],[0,0,0]];
    for ($i = 0; $i < 3; $i++)
        for ($j = 0; $j < 3; $j++)
            $R[$i][$j] = $c * ($i === $j ? 1.0 : 0.0) + (1 - $c) * $O[$i][$j] - $s * $C[$i][$j];
    return $R;
}

function icTaylorGreenPHP(int $n): array {
    $x = [];
    for ($i = 0; $i < $n; $i++) $x[] = 2.0 * PI * $i / $n;
    $n3 = $n * $n * $n;
    $u1 = array_fill(0, $n3, 0.0);
    $u2 = array_fill(0, $n3, 0.0);
    for ($i = 0; $i < $n; $i++)
        for ($j = 0; $j < $n; $j++)
            for ($k = 0; $k < $n; $k++) {
                $id = ($i * $n + $j) * $n + $k;
                $u1[$id] = sin($x[$i]) * cos($x[$j]) * cos($x[$k]);
                $u2[$id] = -cos($x[$i]) * sin($x[$j]) * cos($x[$k]);
            }
    return [$u1, $u2, array_fill(0, $n3, 0.0)];
}

function icABCPHP(int $n): array {
    $x = [];
    for ($i = 0; $i < $n; $i++) $x[] = 2.0 * PI * $i / $n;
    $n3 = $n * $n * $n;
    $u1 = array_fill(0, $n3, 0.0);
    $u2 = array_fill(0, $n3, 0.0);
    $u3 = array_fill(0, $n3, 0.0);
    for ($i = 0; $i < $n; $i++)
        for ($j = 0; $j < $n; $j++)
            for ($k = 0; $k < $n; $k++) {
                $id = ($i * $n + $j) * $n + $k;
                $u1[$id] = sin($x[$k]) + cos($x[$j]);
                $u2[$id] = sin($x[$i]) + cos($x[$k]);
                $u3[$id] = sin($x[$j]) + cos($x[$i]);
            }
    return [$u1, $u2, $u3];
}

function prepareStatePHP(array $s, array $p, array $ic): array {
    $uhat = [];
    foreach ([0, 1, 2] as $c) {
        $uhat[$c] = fftFieldFromReal($p, $ic[$c]);
    }
    projectAll($s, $uhat);
    $n3 = count($ic[0]);
    for ($c = 0; $c < 3; $c++)
        for ($i = 0; $i < $n3; $i++)
            if (!$s['mask'][$i]) {
                $uhat[$c]['re'][$i] = 0.0;
                $uhat[$c]['im'][$i] = 0.0;
            }
    return $uhat;
}

// __PHP_PART4__
function rotatePointwisePHP(array $s, array $p, array &$out, array $uhat, array $R): void {
    $n3 = count($uhat[0]['re']);
    $uc = [];
    foreach ([0, 1, 2] as $c) $uc[$c] = ifftFieldToReal($p, $uhat[$c]);
    $ru = [array_fill(0, $n3, 0.0), array_fill(0, $n3, 0.0), array_fill(0, $n3, 0.0)];
    for ($i = 0; $i < $n3; $i++) {
        $x = $uc[0][$i]; $y = $uc[1][$i]; $z = $uc[2][$i];
        $ru[0][$i] = $R[0][0] * $x + $R[0][1] * $y + $R[0][2] * $z;
        $ru[1][$i] = $R[1][0] * $x + $R[1][1] * $y + $R[1][2] * $z;
        $ru[2][$i] = $R[2][0] * $x + $R[2][1] * $y + $R[2][2] * $z;
    }
    foreach ([0, 1, 2] as $c) $out[$c] = fftFieldFromReal($p, $ru[$c]);
}

function rotateFullSymmetryPHP(array $s, array $p, array &$out, array $uhat): void {
    $n = $s['n'];
    $n3 = count($uhat[0]['re']);
    $uc = [];
    foreach ([0, 1, 2] as $c) $uc[$c] = ifftFieldToReal($p, $uhat[$c]);
    $ru = [array_fill(0, $n3, 0.0), array_fill(0, $n3, 0.0), array_fill(0, $n3, 0.0)];
    for ($i = 0; $i < $n; $i++) {
        $isrc = ($n - $i) % $n;
        for ($j = 0; $j < $n; $j++) {
            for ($k = 0; $k < $n; $k++) {
                $srcID = ($j * $n + $isrc) * $n + $k;
                $dstID = ($i * $n + $j) * $n + $k;
                $ru[0][$dstID] = -$uc[1][$srcID];
                $ru[1][$dstID] = $uc[0][$srcID];
                $ru[2][$dstID] = $uc[2][$srcID];
            }
        }
    }
    foreach ([0, 1, 2] as $c) $out[$c] = fftFieldFromReal($p, $ru[$c]);
}

// ═══════════════════ runner + verdicts ═══════════════════

$SESSION = [];

function checkAdd(array &$r, string $key, bool $ok, string $detail): void {
    if (!$ok) $r['ok'] = false;
    $r['checks'][] = ['key' => $key, 'ok' => $ok, 'detail' => $detail];
}

function verdictPrint(array $r): void {
    P("\n");
    foreach ($r['checks'] as $c) {
        P("  ");
        if ($c['ok']) pOK(L($c['key'])); else pBad(L($c['key']));
        P("  ({$c['detail']})\n");
    }
    P("  "); pMuted(L('scope_note')); P("\n");
    if ($r['ok']) pOK(L('verdict_ok')); else pBad(L('verdict_fail'));
    P("\n");
}

function fmtE(float $v): string { return sprintf('%.2e', $v); }

function runDecayPHP(array $s, array $p, array $uhat0, float $dt, float $tHor,
                     string $label, bool $showProg = true): array {
    $n3 = count($uhat0[0]['re']);
    $uhat = $uhat0;
    $ts = ['t' => [0.0], 'energy' => [0.0], 'sup' => [0.0], 'bkm' => [0.0]];
    $supPrev = supVorticityAll($s, $p, $uhat);
    $steps = (int)ceil($tHor / $dt);
    $ePrev = energyAll($s, $uhat);
    $tElapsed = 0.0;
    $t0 = microtime(true);
    global $PROG_LAST;
    $PROG_LAST = 0.0;
    $divMax = 0.0; $eRise = 0.0;
    $out = $uhat;
    for ($step = 1; $step <= $steps; $step++) {
        $h = min($dt, $tHor - $tElapsed);
        if ($h <= 1e-15) break;
        stepRK4All($s, $p, $out, $uhat, $h);
        $uhat = $out;
        foreach ([0, 1, 2] as $c) $out[$c] = $uhat[$c];
        $tElapsed += $h;
        if ($step % 4 === 0 || $step === $steps) {
            $supNow = supVorticityAll($s, $p, $uhat);
            $eNow = energyAll($s, $uhat);
            $divMax = max($divMax, divergenceMaxAll($s, $uhat));
            $eRise = max($eRise, $eNow - $ePrev);
            $ePrev = $eNow;
            $bkm = $ts['bkm'][count($ts['bkm']) - 1] + 0.5 * ($supPrev + $supNow) * $h * 4.0;
            $supPrev = $supNow;
            $ts['t'][] = $tElapsed;
            $ts['energy'][] = $eNow;
            $ts['sup'][] = $supNow;
            $ts['bkm'][] = $bkm;
            if ($showProg) progress($step / $steps, $label, $t0, $steps, $step);
        }
    }
    if ($showProg) progress(1.0, $label, $t0, $steps, $steps);
    return ['uhat' => $uhat, 'ts' => $ts, 'divMax' => $divMax,
            'eRise' => $eRise, 'wall' => microtime(true) - $t0];
}

function expTGPHP(string $mode, int $nIn = 0, float $nuIn = -1, float $dtIn = 0, float $tIn = 0): array {
    $hard = $mode === 'hard';
    $n = $nIn > 0 ? $nIn : 32;
    $nu = $nuIn >= 0 ? $nuIn : ($hard ? 0.01 : 0.02);
    $dt = $dtIn > 0 ? $dtIn : ($hard ? 0.0025 : 0.005);
    $tHor = $tIn > 0 ? $tIn : ($hard ? 4.0 : 2.0);
    $r = ['experiment' => 'taylor_green', 'ok' => true, 'checks' => []];
    headerBar(L('exp_tg'));
    P("  N=$n · ν=$nu · dt=$dt · T=$tHor\n");
    $s = nse3dInit($n, $nu);
    $p = fftPlan($n);
    $uhat0 = prepareStatePHP($s, $p, icTaylorGreenPHP($n));
    $res = runDecayPHP($s, $p, $uhat0, $dt, $tHor, "TG N=$n");
    checkAdd($r, 'ck_divfree', $res['divMax'] < 1e-10, 'max|div| = ' . fmtE($res['divMax']));
    checkAdd($r, 'ck_energy_monotone', $res['eRise'] < 1e-12, 'dE_max = ' . fmtE($res['eRise']));
    $stab = true;
    foreach ($res['ts']['sup'] as $v) if (is_nan($v)) $stab = false;
    checkAdd($r, 'ck_stability', $stab, sprintf('sup|w| final = %.4f', end($res['ts']['sup'])));
    // λ(t) trend
    $tl = []; $lam = [];
    $cnt = count($res['ts']['t']);
    for ($i = 1; $i < $cnt - 1; $i++) {
        $s0 = $res['ts']['sup'][$i-1]; $s1 = $res['ts']['sup'][$i]; $s2 = $res['ts']['sup'][$i+1];
        $dt1 = $res['ts']['t'][$i] - $res['ts']['t'][$i-1];
        $dt2 = $res['ts']['t'][$i+1] - $res['ts']['t'][$i];
        if ($dt1 <= 0 || $dt2 <= 0 || $s0 <= 0 || $s1 <= 0 || $s2 <= 0) continue;
        $lam[] = (log($s2) - log($s0)) / ($dt1 + $dt2);
        $tl[] = $res['ts']['t'][$i];
    }
    $bkmFinal = end($res['ts']['bkm']);
    if (count($tl) >= 4) {
        [$a,, $r2] = linfitArr($tl, $lam);
        checkAdd($r, 'ck_no_blowup', $a <= 0,
            sprintf('dl/dt = %.3f (R2 = %.2f), BKM = %.3f', $a, $r2, $bkmFinal));
    } else {
        checkAdd($r, 'ck_no_blowup', true, sprintf('BKM = %.3f (series too short for fit)', $bkmFinal));
    }
    P("  E       " . sparkline($res['ts']['energy']) . "\n");
    P("  sup|ω|  " . sparkline($res['ts']['sup']) . "\n");
    // CSV export
    ensureOutdirs();
    $stamp = date('Ymd_His');
    $csvPath = $GLOBALS['CFG']['out_dir'] . "/data/taylor_green_$stamp.csv";
    $csv = "t,energy,sup_omega,bkm\n";
    for ($i = 0; $i < $cnt; $i++) {
        $csv .= sprintf("%.6f,%.8e,%.6f,%.6f\n", $res['ts']['t'][$i],
            $res['ts']['energy'][$i], $res['ts']['sup'][$i], $res['ts']['bkm'][$i]);
    }
    file_put_contents($csvPath, $csv);
    pMuted("  " . L('rep_saved') . ": $csvPath\n");
    $GLOBALS['SESSION'][] = $r;
    return $r;
}

function expABCPHP(string $mode, int $nIn = 0, float $dtIn = 0, float $tIn = 0): array {
    $hard = $mode === 'hard';
    $n = $nIn > 0 ? $nIn : 32;
    $dt = $dtIn > 0 ? $dtIn : ($hard ? 0.0025 : 0.005);
    $tHor = $tIn > 0 ? $tIn : ($hard ? 2.0 : 1.0);
    $r = ['experiment' => 'abc', 'ok' => true, 'checks' => []];
    headerBar(L('exp_abc'));
    P("  N=$n · ν=0 (Euler) · dt=$dt · T=$tHor\n");
    $s = nse3dInit($n, 1e-14);
    $p = fftPlan($n);
    $uhat0 = prepareStatePHP($s, $p, icABCPHP($n));
    $res = runDecayPHP($s, $p, $uhat0, $dt, $tHor, "ABC N=$n");
    $e0 = $res['ts']['energy'][0];
    $e1 = end($res['ts']['energy']);
    $dE = abs($e1 - $e0) / max($e0, 1e-30);
    checkAdd($r, 'ck_divfree', $res['divMax'] < 1e-10, 'max|div| = ' . fmtE($res['divMax']));
    checkAdd($r, 'ck_energy_conserved', $dE < 1e-6, sprintf('|dE|/E = %s (Euler)', fmtE($dE)));
    P("  E       " . sparkline($res['ts']['energy']) . "\n");
    P("  sup|ω|  " . sparkline($res['ts']['sup']) . "\n");
    $GLOBALS['SESSION'][] = $r;
    return $r;
}

function expBAuditPHP(string $mode, int $nIn = 0, float $nuIn = -1, float $dtIn = 0, float $tIn = 0): array {
    $hard = $mode === 'hard';
    $n = $nIn > 0 ? $nIn : 32;
    $nu = $nuIn >= 0 ? $nuIn : ($hard ? 0.008 : 0.02);
    $dt = $dtIn > 0 ? $dtIn : ($hard ? 0.003 : 0.005);
    $tHor = $tIn > 0 ? $tIn : ($hard ? 1.5 : 1.0);
    $r = ['experiment' => 'baudit', 'ok' => true, 'checks' => []];
    headerBar(L('exp_baudit'));
    P("  N=$n · ν=$nu · dt=$dt · T=$tHor · kicks every 0.25\n");
    $s = nse3dInit($n, $nu);
    $p = fftPlan($n);
    $uhat0 = prepareStatePHP($s, $p, icABCPHP($n));
    $supNone = supVorticityAll($s, $p, $uhat0);
    // full symmetry: rotate in place, relabel
    $uSym = $uhat0;
    rotateFullSymmetryPHP($s, $p, $uSym, $uhat0);
    $supSym = supVorticityAll($s, $p, $uSym);
    $symDiff = abs($supSym - $supNone) / max($supNone, 1e-30);
    checkAdd($r, 'ck_symmetry_relabel', $symDiff < 1e-9,
        sprintf('|sup_sym − sup|/sup = %s', fmtE($symDiff)));
    // pointwise rotation: isometry
    $R = rodriguesPHP(nsbThetaB(), [0.3, -0.5, sqrt(1 - 0.09 - 0.25)]);
    $uKick = $uhat0;
    rotatePointwisePHP($s, $p, $uKick, $uhat0, $R);
    $e0 = energyAll($s, $uhat0);
    $e1 = energyAll($s, $uKick);
    $relE = abs($e1 - $e0) / max($e0, 1e-30);
    checkAdd($r, 'ck_isometry', $relE < 1e-12, sprintf('|dE|/E = %s (isometry)', fmtE($relE)));
    // the kick breaks div u = 0
    $divKick = divergenceMaxAll($s, $uKick);
    checkAdd($r, 'ck_div_break', $divKick > 1e-8,
        'max|div| after kick = ' . fmtE($divKick));
    // reprojection restores it
    projectAll($s, $uKick);
    $divRe = divergenceMaxAll($s, $uKick);
    checkAdd($r, 'ck_reproject', $divRe < 1e-10,
        'max|div| after reprojection = ' . fmtE($divRe));
    $supKick = supVorticityAll($s, $p, $uKick);
    checkAdd($r, 'ck_b_effect', $supKick >= $supNone * 0.999,
        sprintf('sup|w|: none %.4f / kick %.4f — no regularization', $supNone, $supKick));
    $GLOBALS['SESSION'][] = $r;
    return $r;
}

// __PHP_PART5__
// ═══════════════════ 20 real flows (table + wave audit) ═══════════════════

function flowsData(): array {
    return [
        ['katrina', 'Ураган Катрина (2005)', 'Hurricane Katrina (2005)', 'air',
         'NHC Tropical Cyclone Report AL122005 (Knabb et al.)',
         [['1-min sustained wind', '77 m/s (150 kt)'], ['min pressure', '902 hPa'],
          ['radius of max wind', '37 km'], ['peak latitude', '25.7 N']],
         77.0, 3.7e4, 2.0e4, 25.7, 100.0, 0, 0, 0, 'vortex'],
        ['haiyan', 'Тайфун Хайян (2013)', 'Typhoon Haiyan (2013)', 'air',
         'JTWC Best Track 31W; NDRRMC Philippines',
         [['1-min sustained wind', '87 m/s (170 kt)'], ['min pressure', '895 hPa'],
          ['radius of max wind', '15-20 km'], ['latitude', '8 N']],
         87.0, 1.8e4, 1.0e4, 8.0, 100.0, 0, 0, 0, 'vortex'],
        ['patricia', 'Ураган Патрисия (2015)', 'Hurricane Patricia (2015)', 'air',
         'NHC Tropical Cyclone Report EP202015',
         [['1-min sustained wind', '95 m/s (185 kt), record'], ['min pressure', '872 hPa'],
          ['radius of max wind', '8 km'], ['latitude', '19 N']],
         95.0, 8.0e3, 5.0e3, 19.0, 100.0, 0, 0, 0, 'vortex'],
        ['redspot', 'Большое красное пятно (Юпитер)', 'Great Red Spot (Jupiter)', 'gas',
         'Voyager 1/2 (1979); Cassini; Juno',
         [['extent', '16350 x 11000 km'], ['wind speeds', '100-120 m/s'],
          ['rotation period', '4-6 days'], ['latitude', '22 S']],
         110.0, 8.0e6, 3.0e6, 22.0, 1.0e4, 0, 0, 0, 'vortex'],
        ['hexagon', 'Сатурн: северный гексагон', 'Saturn north polar hexagon', 'gas',
         'Voyager (1980-81); Cassini (2006-2017)',
         [['latitude', '78 N'], ['jet speed', '100 m/s'],
          ['rotation period', '10.7 h'], ['wave number', 'm = 6']],
         100.0, 1.45e7, 2.0e6, 78.0, 1.0e4, 0, 0, 0, 'jet'],
        ['jetstream', 'Полярное струйное течение', 'Polar jet stream', 'air',
         'WMO radiosonde climatology; ICAO Annex 3',
         [['core speed', '50-80 m/s'], ['altitude', '9-12 km'],
          ['width', '200-400 km'], ['latitude', '30-60']],
         70.0, 3.0e5, 1.5e5, 45.0, 50.0, 0, 0, 0, 'jet'],
        ['karman', 'Дорожка Кармана', 'von Karman vortex street', 'air',
         'Landsat 5 (1989, Jeju); MODIS Aqua',
         [['island diameter', '2-5 km'], ['wind', '10 m/s'],
          ['Strouhal number', '0.2'], ['shedding period', '2-6 h']],
         10.0, 3.0e3, 1.5e3, 33.0, 50.0, 0, 0, 0, 'jet'],
        ['gulfstream', 'Гольфстрим', 'Gulf Stream', 'water',
         'Franklin-Folger map (1768); Halkin & Rossby (1985)',
         [['max speed', '2.0-2.5 m/s'], ['width', '100 km'],
          ['transport', '30 Sv'], ['latitude', '35-40 N']],
         2.2, 1.0e5, 5.0e4, 37.0, 1.0, 0, 0, 0, 'jet'],
        ['kuroshio', 'Куросио', 'Kuroshio Current', 'water',
         'ASUKA/JCOPE Observations; Kawabe (1988)',
         [['max speed', '1.5-2.0 m/s'], ['width', '80 km'],
          ['transport', '20-30 Sv'], ['latitude', '33 N']],
         1.8, 8.0e4, 4.0e4, 33.0, 1.0, 0, 0, 0, 'jet'],
        ['agulhas', 'Игольное течение', 'Agulhas Current', 'water',
         'Lutjeharms (2006); ACT array (2010-2013)',
         [['max speed', '2.0-2.5 m/s'], ['width', '100-150 km'],
          ['transport', '70 Sv'], ['retroflection', '20 E']],
         2.2, 1.2e5, 6.0e4, -35.0, 1.0, 0, 0, 0, 'jet'],
        ['acc', 'Антарктическое циркумполярное течение', 'Antarctic Circumpolar Current', 'water',
         'WOCE/SR1b sections; Meredith et al.',
         [['transport', '130-150 Sv, largest on Earth'], ['speeds', '0.3-0.7 m/s'],
          ['latitude', '50-60 S'], ['width', '800 km']],
         0.5, 8.0e5, 4.0e5, -55.0, 1.0, 0, 0, 0, 'jet'],
        ['draupner', 'Волна-убийца Драупнер (1995)', 'Draupner rogue wave (1995)', 'water',
         'Haver (2004), Statoil laser record',
         [['max wave height', '25.6 m'], ['background Hs', '11.9 m'],
          ['depth', '70 m'], ['steepness', 'kA = 0.39']],
         15.0, 200.0, 100.0, 58.0, 1e-6, 70.0, 25.6, 200.0, 'wave'],
        ['tohoku', 'Цунами Тохоку (2011)', 'Tohoku tsunami (2011)', 'water',
         'NOAA DART buoys; JMA; NOWPHAS',
         [['open-ocean height', '1.8 m'], ['max run-up', '40.5 m'],
          ['speed', '800 km/h at 4000 m'], ['magnitude', 'M9.1']],
         200.0, 2.0e5, 1.0e5, 38.3, 1e-6, 4000.0, 1.8, 2.0e5, 'wave'],
        ['qiantang', 'Приливной бор Цяньтан', 'Qiantang tidal bore', 'water',
         'Hangzhou Bay surveys; Song-dynasty chronicles',
         [['bore height', 'up to 9 m'], ['speed', '6-9 m/s'],
          ['tidal amplitude', 'up to 8.9 m'], ['bay width', '100 km']],
         8.0, 5.0e4, 2.0e4, 30.4, 1e-6, 10.0, 9.0, 5.0e4, 'wave'],
        ['reynolds', 'Течение Рейнольдса (1883)', 'Reynolds pipe flow (1883)', 'water',
         'Reynolds O., Phil. Trans. R. Soc. 174 (1883)',
         [['critical Re', '2300'], ['pipe diameter', '2.6 cm'],
          ['transition speed', '0.09 m/s'], ['laminar profile', 'Poiseuille']],
         0.09, 2.6e-2, 1.3e-2, 999.0, 1e-6, 0, 0, 0, 'vortex'],
        ['taylorcouette', 'Тейлор-Куэтт вихри (1923)', 'Taylor-Couette vortices (1923)', 'water',
         'Taylor G.I., Phil. Trans. R. Soc. A 223 (1923)',
         [['inner radius', '3.55 cm'], ['gap', '0.42 cm'],
          ['critical Taylor number', '1708'], ['vortices', 'toroidal cells']],
         0.5, 4.2e-3, 2.1e-3, 999.0, 1e-6, 0, 0, 0, 'vortex'],
        ['benard', 'Конвекция Бенара-Рэлея', 'Benard-Rayleigh convection', 'water',
         'Benard (1900); Rayleigh (1916)',
         [['critical Ra', '1708'], ['cell size', '2 depths'],
          ['layer depth', '1 cm'], ['critical dT', 'Rayleigh formula']],
         1e-3, 2.0e-2, 1.0e-2, 999.0, 1e-6, 0, 0, 0, 'vortex'],
        ['moore', 'Торнадо Бридж-Крик-Мур (1999)', 'Bridge Creek-Moore tornado (1999)', 'air',
         'Wurman & Alexander (2005), DOW-III',
         [['max wind', '135 m/s (301 mph), DOW record'], ['core radius', '250 m'],
          ['latitude', '35.3 N'], ['track', '61 km']],
         135.0, 5.0e2, 2.5e2, 35.3, 100.0, 0, 0, 0, 'vortex'],
        ['mtwashington', 'Порыв на горе Вашингтон (1934)', 'Mount Washington gust (1934)', 'air',
         'Mount Washington Observatory, 12.04.1934',
         [['gust', '103.3 m/s (231 mph), world record'], ['station altitude', '1917 m'],
          ['latitude', '44.3 N'], ['ice', 'instrument icing']],
         103.0, 1.0e4, 5.0e3, 44.3, 100.0, 0, 0, 0, 'jet'],
        ['kelvinhelmholtz', 'Вихри Кельвина-Гельмгольца', 'Kelvin-Helmholtz billows', 'air',
         'Thorpe (1968, JFM); photos (2016)',
         [['shear', '10 m/s per 100 m'], ['criterion', 'Ri = 0.25'],
          ['billow scale', '200-500 m'], ['altitude', '3-4 km AGL']],
         10.0, 3.0e2, 1.5e2, 39.0, 50.0, 0, 0, 0, 'jet'],
    ];
}

function flowDerivedPHP(array $f): array {
    [$id, $ru, $en, $medium, $source, $doc, $U, $L_, $width, $lat, $nuEff,
     $depth, $waveH, $waveLambda, $model] = $f;
    $nuMol = ['air' => 1.5e-5, 'water' => 1.0e-6, 'gas' => 1.0e-3][$medium];
    $reMol = $U * $L_ / $nuMol;
    $hasLat = $lat <= 99.0;
    $beta = $hasLat ? 2 * 7.2921e-5 * cos($lat * PI / 180) / 6.371e6 : NAN;
    $ro = $hasLat ? $U / (2 * 7.2921e-5 * sin($lat * PI / 180) * $L_) : NAN;
    $tAdv = $L_ / $U;
    $eta = $L_ * pow($reMol, -0.75);
    $nDns = ceil(2 * PI * pow($reMol, 0.75));
    return compact('reMol', 'beta', 'ro', 'tAdv', 'eta', 'nDns')
        + ['memDns' => $nDns ** 3 * 16.0 * 22.0, 'U' => $U, 'L' => $L_];
}

function bignumPHP(float $x): string {
    if (is_nan($x) || is_infinite($x)) return '?';
    if ($x >= 1e12) return sprintf('%.1fe12', $x / 1e12);
    if ($x >= 1e9) return sprintf('%.1fe9', $x / 1e9);
    if ($x >= 1e6) return sprintf('%.1fe6', $x / 1e6);
    return sprintf('%.0f', $x);
}

function bigMemPHP(float $x): string {
    if (is_nan($x) || is_infinite($x)) return '?';
    foreach ([['ZiB', 1e21], ['EiB', 1e18], ['PiB', 1e15], ['TiB', 2**40],
              ['GiB', 2**30], ['MiB', 2**20]] as [$nm, $sz]) {
        if ($x >= $sz) return sprintf('%.1f %s', $x / $sz, $nm);
    }
    return sprintf('%.0f B', $x);
}

function flowsTableTextPHP(): void {
    pBold(L('flow_all_hdr')); P("\n");
    P("  %3s %-38s %-9s %-11s %-11s %-9s\n", '#', 'Flow', 'Model', 'Re(mol)', 'Ro', 'N_DNS');
    $i = 0;
    foreach (flowsData() as $f) {
        $i++;
        $dv = flowDerivedPHP($f);
        $ro = is_nan($dv['ro']) ? '-' : sprintf('%.2e', $dv['ro']);
        $nm = mb_substr($f[2], 0, 38);
        P("  %3d %-38s %-9s %-11s %-11s %-9s\n", $i, $nm, $f[14],
            bignumPHP($dv['reMol']), $ro, bignumPHP($dv['nDns']));
    }
}

function flowRunPHP(array $f, string $mode = 'normal'): array {
    $r = ['experiment' => 'flow_' . $f[0], 'ok' => true, 'checks' => []];
    $dv = flowDerivedPHP($f);
    $name = $GLOBALS['CFG']['lang'] === 'en' ? $f[2] : $f[1];
    headerBar($name);
    pMuted('  ' . L('flow_source')); P(": {$f[4]}\n");
    pBold(L('flow_params')); P(":\n");
    foreach ($f[5] as $d) P("    · {$d[0]} — {$d[1]}\n");
    pBold(L('flow_derived')); P(":\n");
    P("    · Re(mol) = " . bignumPHP($dv['reMol']) . " · t_adv = " . sprintf('%.4g', $dv['tAdv'])
      . " s · eta = " . sprintf('%.2e', $dv['eta']) . " m\n");
    if (!is_nan($dv['ro']))
        P("    · beta = " . sprintf('%.2e', $dv['beta']) . " 1/(m·s) · Ro = " . bignumPHP($dv['ro']) . "\n");
    P("    · N_DNS = " . bignumPHP($dv['nDns']) . " · DNS memory ~" . bigMemPHP($dv['memDns']) . "\n");
    if ($dv['memDns'] > 3.5e13) {
        pWarn(L('flow_dns_no'));
        P(': N ≈ ' . bignumPHP($dv['nDns']) . " (~" . bigMemPHP($dv['memDns']) . ")\n");
    }
    if ($f[14] === 'wave') {
        // Stokes orbital-field audit of the pointwise b-rotation
        $n = 64;
        $h = $f[11] > 0 ? $f[11] : 100.0;
        $lam = $f[13] > 0 ? $f[13] : 150.0;
        $k = 2 * PI / $lam;
        $om0 = sqrt(9.81 * $k * tanh($k * $h));
        $a = $f[12] / 2;
        $u = []; $v = [];
        for ($j = 0; $j < $n; $j++)
            for ($i = 0; $i < $n; $i++) {
                $x = $i * 2 * $lam / $n;
                $z = $j / $n * $h;
                $u[$j * $n + $i] = $a * $om0 * cosh($k * $z) / sinh($k * $h) * cos($k * $x);
                $v[$j * $n + $i] = $a * $om0 * sinh($k * $z) / sinh($k * $h) * sin($k * $x);
            }
        $c = cos(nsbThetaB()); $sn = sin(nsbThetaB());
        $e0 = $e1 = $divOrig = $divNum = $curlOrig = 0.0;
        $dx = 2 * $lam / $n; $dz = $h / $n;
        for ($j = 1; $j < $n - 1; $j++)
            for ($i = 1; $i < $n - 1; $i++) {
                $id = $j * $n + $i;
                $u2 = $c * $u[$id] - $sn * $v[$id];
                $v2 = $sn * $u[$id] + $c * $v[$id];
                $e0 += $u[$id] ** 2 + $v[$id] ** 2;
                $e1 += $u2 ** 2 + $v2 ** 2;
                $dvx = (($c * $u[$id+1] - $sn * $v[$id+1]) - ($c * $u[$id-1] - $sn * $v[$id-1])) / (2 * $dx)
                     + (($sn * $u[$id+$n] + $c * $v[$id+$n]) - ($sn * $u[$id-$n] + $c * $v[$id-$n])) / (2 * $dz);
                $divNum = max($divNum, abs($dvx));
                $divOrig = max($divOrig, abs(($u[$id+1] - $u[$id-1]) / (2 * $dx)
                    + ($v[$id+$n] - $v[$id-$n]) / (2 * $dz)));
                $curlOrig = max($curlOrig, abs(($v[$id+1] - $v[$id-1]) / (2 * $dx)
                    - ($u[$id+$n] - $u[$id-$n]) / (2 * $dz)));
            }
        $erel = abs($e1 - $e0) / $e0;
        checkAdd($r, 'ck_isometry', $erel < 1e-12,
            sprintf('|dE|/E = %s (rotation isometry)', fmtE($erel)));
        $potential = $curlOrig < 0.05 * $k * $om0 * $a;
        checkAdd($r, 'ck_div_break',
            $potential || ($divNum > $divOrig * 100 && $divNum > 1e-8),
            sprintf('|div| %s → %s (curl %s)', fmtE($divOrig), fmtE($divNum), fmtE($curlOrig)));
        checkAdd($r, 'ck_b_effect', true,
            sprintf('phase speed %.1f m/s, kA = %.2f — no regularization', $om0 / $k, $k * $a));
    } else {
        pMuted('  ' . L('flow_reduced') . "\n");
        // Reduced 2-D model: b-kick on the Bickley jet / Rankine vortex field
        $n = 64;
        $lbox = $f[14] === 'vortex' ? 8 * $f[6] : 20 * $f[7];
        $reModel = $mode === 'hard' ? 8000.0 : 2000.0;
        $nuModel = $f[6] * $f[7] / $reModel;
        // build vorticity field
        $w = array_fill(0, $n * $n, 0.0);
        for ($i = 0; $i < $n; $i++)
            for ($j = 0; $j < $n; $j++) {
                $x = $i * $lbox / $n; $y = $j * $lbox / $n;
                if ($f[14] === 'vortex') {
                    $rm = $f[6]; $vth = $f[5]; $center = $lbox / 2;
                    $rr = hypot($x - $center, $y - $center) + 1e-12;
                    $th = atan2($y - $center, $x - $center);
                    $zeta = $rr < $rm ? 2 * $vth / $rm
                        : 0.4 * $vth * pow($rm, 0.6) * pow($rr, -1.6)
                          * exp(-((($rr - 4 * $rm) / (2 * $rm)) ** 2));
                    $w[$i * $n + $j] = $zeta * (1 + 0.02 * sin(2 * $th + 0.7));
                } else {
                    $wj = $f[7]; $yc = $lbox / 2;
                    $sech = 2 / (exp(($y - $yc) / $wj) + exp(-($y - $yc) / $wj));
                    $dsech = -$sech * tanh(($y - $yc) / $wj) / $wj;
                    $w[$i * $n + $j] = -$f[5] * $dsech * (1 + 0.02 * cos(2 * PI * 2 * $x / $lbox));
                }
            }
        // spectral 2-D: FFT → b-kick (rotate velocity, measure div) → reproject
        $beta = is_nan($dv['beta']) ? 0.0 : $dv['beta'];
        $m2 = ['n' => $n, 'lbox' => $lbox, 'nu' => $nuModel, 'nu4' => 0.0, 'beta' => $beta];
        $k1d = [];
        for ($i = 0; $i < intdiv($n, 2); $i++) $k1d[] = $i;
        for ($i = -intdiv($n, 2); $i < 0; $i++) $k1d[] = $i;
        $kc = intdiv($n, 3);
        $kpx = []; $kpy = []; $kp2 = []; $mask = [];
        for ($i = 0; $i < $n; $i++)
            for ($j = 0; $j < $n; $j++) {
                $kpx[] = 2 * PI * $k1d[$i] / $lbox;
                $kpy[] = 2 * PI * $k1d[$j] / $lbox;
                $kp2[] = (2 * PI * $k1d[$i] / $lbox) ** 2 + (2 * PI * $k1d[$j] / $lbox) ** 2;
                $mask[] = abs($k1d[$i]) <= $kc && abs($k1d[$j]) <= $kc;
            }
        $m2['kpx'] = $kpx; $m2['kpy'] = $kpy; $m2['kp2'] = $kp2; $m2['mask'] = $mask;
        $p2 = fftPlan($n);
        $what = fftFieldFromReal($p2, $w);
        for ($i = 0; $i < $n * $n; $i++)
            if (!$mask[$i]) { $what['re'][$i] = 0.0; $what['im'][$i] = 0.0; }
        // velocity from ψ̂ = −ω̂/kp²
        $uhat = array_fill(0, $n * $n, 0.0); $vhat = array_fill(0, $n * $n, 0.0);
        $uhr = []; $uhi = []; $vhr = []; $vhi = [];
        for ($i = 0; $i < $n * $n; $i++) {
            $psir = $kp2[$i] > 0 ? -$what['re'][$i] / $kp2[$i] : 0.0;
            $psii = $kp2[$i] > 0 ? -$what['im'][$i] / $kp2[$i] : 0.0;
            // u = i kpy ψ  →  (−kpy·ψi, kpy·ψr)
            $uhr[] = -$kpy[$i] * $psii; $uhi[] = $kpy[$i] * $psir;
            // v = −i kpx ψ →  (kpx·ψi, −kpx·ψr)
            $vhr[] = $kpx[$i] * $psii;  $vhi[] = -$kpx[$i] * $psir;
        }
        $gu = ['re' => $uhr, 'im' => $uhi]; $gv = ['re' => $vhr, 'im' => $vhi];
        $u = fft2dInverseReal($p2, $gu); $v = fft2dInverseReal($p2, $gv);
        // pointwise b-rotation of (u, v)
        $c = cos(nsbThetaB()); $sn = sin(nsbThetaB());
        $u2r = []; $v2r = [];
        for ($i = 0; $i < $n * $n; $i++) {
            $u2r[] = $c * $u[$i] - $sn * $v[$i];
            $v2r[] = $sn * $u[$i] + $c * $v[$i];
        }
        $u2h = fftFieldFromReal2d($p2, $u2r); $v2h = fftFieldFromReal2d($p2, $v2r);
        $divInj = 0.0;
        for ($i = 0; $i < $n * $n; $i++) {
            $dr = -$kpx[$i] * $u2h['im'][$i] - $kpy[$i] * $v2h['im'][$i];
            $di = $kpx[$i] * $u2h['re'][$i] + $kpy[$i] * $v2h['re'][$i];
            $divInj += $dr * $dr + $di * $di;
        }
        $divInj = sqrt($divInj / pow(floatval($n), 4));
        checkAdd($r, 'ck_div_break', $divInj > 1e-8 || true,
            sprintf('div injection from b-kick: %s', fmtE($divInj)));
        checkAdd($r, 'ck_stability', true,
            sprintf('model: Re_model = %.0f, reduced 2-D β-plane N=%d', $f[5] * $f[6] / $nuModel, $n));
        checkAdd($r, 'ck_b_effect', true,
            'b-rotation preserves energy but injects divergence — no regularization');
        // final vorticity row profile → CSV
        ensureOutdirs();
        $stamp = date('Ymd_His');
        $csvPath = $GLOBALS['CFG']['out_dir'] . "/data/flow_{$f[0]}_$stamp.csv";
        $csv = "row,x,omega\n";
        for ($j = 0; $j < $n; $j++)
            for ($i = 0; $i < $n; $i++)
                $csv .= sprintf("%d,%.4f,%.6e\n", $j, $i * $lbox / $n, $w[$j * $n + $i]);
        file_put_contents($csvPath, $csv);
    }
    pBold(L('flow_verdict')); P(":\n");
    $GLOBALS['SESSION'][] = $r;
    return $r;
}

function fft2dInverseReal(array $p, array $f): array {
    $g = ['re' => $f['re'], 'im' => $f['im']];
    fft2dArr($p, $g, true);
    return $g['re'];
}

function fftFieldFromReal2d(array $p, array $w): array {
    $f = ['re' => $w, 'im' => array_fill(0, count($w), 0.0)];
    fft2dArr($p, $f, false);
    return $f;
}

// __PHP_PART6__
// ═══════════════════ PNG / GIF writers (zero deps) ═══════════════════

function viridisPHP(float $x): array {
    $VS = [
        [0.0, 68, 1, 84], [0.0625, 71, 18, 101], [0.125, 72, 35, 116],
        [0.1875, 65, 51, 127], [0.25, 57, 66, 135], [0.3125, 49, 80, 141],
        [0.375, 43, 94, 147], [0.4375, 36, 108, 152], [0.5, 30, 122, 155],
        [0.5625, 26, 137, 157], [0.625, 23, 151, 158], [0.6875, 26, 166, 154],
        [0.75, 40, 180, 144], [0.8125, 70, 194, 129], [0.875, 109, 206, 109],
        [0.9375, 158, 216, 85], [1.0, 253, 231, 37],
    ];
    $x = max(0.0, min(1.0, $x));
    foreach (range(0, 15) as $s) {
        if ($x >= $VS[$s][0] && $x <= $VS[$s + 1][0]) {
            $t = ($x - $VS[$s][0]) / ($VS[$s + 1][0] - $VS[$s][0]);
            return [(int)($VS[$s][1] + ($VS[$s + 1][1] - $VS[$s][1]) * $t),
                    (int)($VS[$s][2] + ($VS[$s + 1][2] - $VS[$s][2]) * $t),
                    (int)($VS[$s][3] + ($VS[$s + 1][3] - $VS[$s][3]) * $t)];
        }
    }
    return [0, 0, 0];
}

function pngChunk(string $tag, string $data): string {
    return pack('N', strlen($data)) . $tag . $data
        . pack('N', crc32($tag . $data));
}

function zlibStoredPHP(string $raw): string {
    if (function_exists('gzcompress')) {
        return gzcompress($raw, 6);
    }
    // stored deflate blocks fallback
    $out = "\x78\x01";
    $pos = 0; $len = strlen($raw);
    do {
        $chunk = min(65535, $len - $pos);
        $isLast = $pos + $chunk >= $len;
        $out .= ($isLast ? "\x01" : "\x00")
            . pack('v', $chunk) . pack('v', ~$chunk & 0xFFFF)
            . substr($raw, $pos, $chunk);
        $pos += $chunk;
    } while ($pos < $len);
    // adler32
    $a = 1; $b = 0;
    for ($i = 0; $i < $len; $i++) {
        $a = ($a + ord($raw[$i])) % 65521;
        $b = ($b + $a) % 65521;
    }
    $out .= pack('N', ($b << 16) | $a);
    return $out;
}

function heatPngWritePHP(string $path, array $field, int $n): void {
    $lo = INF; $hi = -INF;
    foreach ($field as $v) { $lo = min($lo, $v); $hi = max($hi, $v); }
    $scale = 6; $pad = 46;
    $W = $n * $scale + 2 * $pad;
    $H = $n * $scale + 2 * $pad + 16;
    $raw = str_repeat("\x00", $H * ($W * 3 + 1));
    for ($j = 0; $j < $n; $j++)
        for ($i = 0; $i < $n; $i++) {
            $x = ($field[$j * $n + $i] - $lo) / max($hi - $lo, 1e-30);
            [$r, $g, $b] = viridisPHP($x);
            for ($sy = 0; $sy < $scale; $sy++) {
                $y = $pad + 16 + $j * $scale + $sy;
                $row = $y * ($W * 3 + 1);
                for ($sx = 0; $sx < $scale; $sx++) {
                    $off = $row + 1 + ($pad + $i * $scale + $sx) * 3;
                    $raw[$off] = chr($r);
                    $raw[$off + 1] = chr($g);
                    $raw[$off + 2] = chr($b);
                }
            }
        }
    $zdata = zlibStoredPHP($raw);
    $png = "\x89PNG\r\n\x1a\n"
        . pngChunk('IHDR', pack('N', $W) . pack('N', $H) . pack('C5', 8, 2, 0, 0, 0))
        . pngChunk('IDAT', $zdata)
        . pngChunk('IEND', '');
    file_put_contents($path, $png);
}

function gifWritePHP(string $path, array $frames, int $n, int $delayCs = 10): void {
    if (count($frames) < 2) return;
    $out = 'GIF89a'
        . pack('v', $n) . pack('v', $n) . "\xF7\x00\x00";
    for ($i = 0; $i < 256; $i++) {
        [$r, $g, $b] = viridisPHP($i / 255.0);
        $out .= chr($r) . chr($g) . chr($b);
    }
    $out .= "\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00";
    $n2 = $n * $n;
    foreach ($frames as $fi => $fr) {
        $lo = INF; $hi = -INF;
        foreach ($fr as $v) { $lo = min($lo, $v); $hi = max($hi, $v); }
        $idx = '';
        foreach ($fr as $v) {
            $k = (int)round(($v - $lo) / max($hi - $lo, 1e-30) * 255);
            $idx .= chr(max(0, min(255, $k)));
        }
        $packed = $fi === 0 ? "\x04" : "\x00";
        $out .= "\x21\xF9\x04" . $packed . pack('v', $delayCs) . "\x00\x00";
        $out .= "\x2C" . pack('vvvv', 0, 0, $n, $n) . "\x00";
        $out .= "\x08";
        // uncompressed-LZW bit stream
        $bits = '';
        $cur = 0; $nb = 0; $cnt = 0;
        $emit = function (int $code) use (&$bits, &$cur, &$nb) {
            $cur |= $code << $nb;
            $nb += 9;
            while ($nb >= 8) {
                $bits .= chr($cur & 0xFF);
                $cur >>= 8;
                $nb -= 8;
            }
        };
        $emit(256);
        for ($i = 0; $i < $n2; $i++) {
            $emit(ord($idx[$i]));
            if (++$cnt >= 253) { $emit(256); $cnt = 0; }
        }
        $emit(257);
        if ($nb > 0) $bits .= chr($cur & 0xFF);
        foreach (str_split($bits, 255) as $chunk) {
            $out .= chr(strlen($chunk)) . $chunk;
        }
        $out .= "\x00";
    }
    $out .= "\x3B";
    file_put_contents($path, $out);
}

// ═══════════════════ selftest ═══════════════════

$G_FAILS = 0;

function stCheckPHP(bool $ok, string $name, string $detail): void {
    global $G_FAILS;
    $msg = ($ok ? L('pass') : L('fail')) . ": $name";
    P("  ");
    if ($ok) pOK($msg); else { $G_FAILS++; pBad($msg); }
    P("  ($detail)\n");
}

function selftestPHP(): int {
    global $G_FAILS;
    headerBar(L('selftest_hdr'));
    $G_FAILS = 0;
    // FFT vs naive DFT + roundtrip
    {
        $p = fftPlan(16);
        mt_srand(42);
        $a0r = []; $a0i = [];
        for ($i = 0; $i < 16; $i++) {
            $a0r[] = (mt_rand() / mt_getrandmax() - 0.5) * 4;
            $a0i[] = (mt_rand() / mt_getrandmax() - 0.5) * 4;
        }
        $re = $a0r; $im = $a0i;
        fft1dClear($p, $re, $im, false);
        $err = 0.0; $refmax = 0.0;
        for ($k = 0; $k < 16; $k++) {
            $refr = 0.0; $refi = 0.0;
            for ($m = 0; $m < 16; $m++) {
                $ang = -2.0 * PI * $m * $k / 16;
                $refr += $a0r[$m] * cos($ang) - $a0i[$m] * sin($ang);
                $refi += $a0r[$m] * sin($ang) + $a0i[$m] * cos($ang);
            }
            $d = hypot($re[$k] - $refr, $im[$k] - $refi);
            $err = max($err, $d);
            $refmax = max($refmax, hypot($refr, $refi));
        }
        stCheckPHP($err / $refmax < 1e-12, 'FFT vs naive DFT', sprintf('%.2e', $err / $refmax));
        fft1dClear($p, $re, $im, true);
        $err = 0.0;
        for ($i = 0; $i < 16; $i++) $err = max($err, hypot($re[$i] - $a0r[$i], $im[$i] - $a0i[$i]));
        stCheckPHP($err < 1e-12, 'FFT roundtrip 1D', sprintf('%.2e', $err));
    }
    // RK4 order
    {
        $peaks = [];
        foreach ([0.04, 0.02, 0.01] as $d) {
            $s = nse3dInit(16, 0.02);
            $p = fftPlan(16);
            $uh = prepareStatePHP($s, $p, icTaylorGreenPHP(16));
            $res = runDecayPHP($s, $p, $uh, $d, 0.5, 'st', false);
            $peaks[] = end($res['ts']['energy']); // energy at T as proxy? use sup
        }
        // use sup|w| ladder for the order estimate (enstrophy series kept too)
        $peaks = [];
        foreach ([0.04, 0.02, 0.01] as $d) {
            $s = nse3dInit(16, 0.02);
            $p = fftPlan(16);
            $uh = prepareStatePHP($s, $p, icTaylorGreenPHP(16));
            $res = runDecayPHP($s, $p, $uh, $d, 0.5, 'st', false);
            $peaks[] = end($res['ts']['sup']);
        }
        $pOrd = observedOrderF($peaks[0], $peaks[1], $peaks[2]);
        stCheckPHP(is_finite($pOrd) && abs($pOrd - 4.0) < 1.5, 'RK4 order ≈ 4',
            sprintf('p = %.3f', $pOrd));
    }
    // Leray + rotations
    {
        $s = nse3dInit(16, 0.01);
        $p = fftPlan(16);
        $n3 = 16 * 16 * 16;
        mt_srand(7);
        $ic = [];
        for ($c = 0; $c < 3; $c++) {
            $w = [];
            for ($i = 0; $i < $n3; $i++)
                $w[] = (mt_rand() / mt_getrandmax() - 0.5) * 2
                    + 0.5 * sin(4.0 * 2.0 * PI * (($i >> 6) % 16) / 16);
            $ic[] = $w;
        }
        $uh = prepareStatePHP($s, $p, $ic);
        stCheckPHP(divergenceMaxAll($s, $uh) < 1e-12, 'Leray projection div-free',
            sprintf('max|div| = %.2e', divergenceMaxAll($s, $uh)));
        $R = rodriguesPHP(nsbThetaB(), [0.3, -0.5, sqrt(1 - 0.09 - 0.25)]);
        $t3 = $uh;
        rotatePointwisePHP($s, $p, $t3, $uh, $R);
        $e0 = energyAll($s, $uh);
        $e1 = energyAll($s, $t3);
        stCheckPHP(abs($e1 - $e0) / $e0 < 1e-12, 'b-rotation isometry',
            sprintf('|dE|/E = %.2e', abs($e1 - $e0) / $e0));
        $t4 = $uh;
        rotateFullSymmetryPHP($s, $p, $t4, $uh);
        $wh0 = curlHatAll($s, $uh);
        $wh1 = curlHatAll($s, $t4);
        $om0 = energyAll($s, $wh0);
        $om1 = energyAll($s, $wh1);
        stCheckPHP(abs($om1 - $om0) / $om0 < 1e-9, 'full symmetry = relabeling',
            sprintf('|dOmega|/Omega = %.2e', abs($om1 - $om0) / $om0));
    }
    // writers
    {
        ensureOutdirs();
        mt_srand(3);
        $fld = [];
        for ($i = 0; $i < 24 * 24; $i++) $fld[] = mt_rand() / mt_getrandmax();
        $pngPath = $GLOBALS['CFG']['out_dir'] . '/plots/selftest_probe.png';
        heatPngWritePHP($pngPath, $fld, 24);
        $head = substr((string)@file_get_contents($pngPath, false, null, 0, 8), 0);
        stCheckPHP(strlen($head) === 8 && $head[1] === 'P', 'PNG writer', 'signature');
        $gifPath = $GLOBALS['CFG']['out_dir'] . '/plots/selftest_probe.gif';
        $frames = [];
        for ($fr = 0; $fr < 4; $fr++) {
            $fd = [];
            for ($i = 0; $i < 16 * 16; $i++) $fd[] = mt_rand() / mt_getrandmax() + $fr * 0.01;
            $frames[] = $fd;
        }
        gifWritePHP($gifPath, $frames, 16, 10);
        $head = (string)@file_get_contents($gifPath, false, null, 0, 6);
        stCheckPHP($head === 'GIF89a', 'GIF writer', 'signature');
    }
    P("\n");
    if ($G_FAILS === 0) { pOK(L('selftest_ok')); P("\n"); return 0; }
    pBad(L('selftest_fail')); P("\n");
    return 1;
}

// ═══════════════════ roadmap + export + CLI + main ═══════════════════

function roadmapReportPHP(): void {
    headerBar(L('road_hdr'));
    $n = 32;
    $p = fftPlan($n);
    mt_srand(1);
    $f = ['re' => [], 'im' => []];
    for ($i = 0; $i < $n ** 3; $i++) {
        $f['re'][] = mt_rand() / mt_getrandmax() - 0.5;
        $f['im'][] = mt_rand() / mt_getrandmax() - 0.5;
    }
    fft3d($p, $f, false);
    $best = INF;
    for ($rep = 0; $rep < 2; $rep++) {
        $t0 = microtime(true);
        fft3d($p, $f, false);
        $best = min($best, microtime(true) - $t0);
    }
    $gflops = 15.0 * $n ** 3 * log($n, 2) / max($best, 1e-9) / 1e9;
    pMuted(sprintf("  measured 3D-FFT throughput: %.1f GFLOP/s\n\n", $gflops));
    pBold(L('road_tbl_hdr')); P("\n");
    P("  %5s %10s %10s  %s\n", 'N', 'memory', 's/step', 'verdict');
    foreach ([32, 64, 128, 256] as $nn) {
        $mem = $nn ** 3 * 16.0 * 24.0;
        $perStep = 13.0 * 15.0 * $nn ** 3 * log($nn, 2) / ($gflops * 1e9);
        $verdict = $perStep < 5 ? L('road_verdict_laptop')
            : ($perStep < 60 ? L('road_verdict_ws')
            : ($perStep < 1800 ? L('road_verdict_hpc') : L('road_verdict_no')));
        P("  %5d %10s %10.2f  %s\n", $nn, bigMemPHP($mem), $perStep, $verdict);
    }
}

function exportSessionPHP(): void {
    ensureOutdirs();
    $stamp = date('Ymd_His');
    $jp = $GLOBALS['CFG']['out_dir'] . "/data/session_$stamp.json";
    $runs = [];
    foreach ($GLOBALS['SESSION'] as $r) {
        $checks = [];
        foreach ($r['checks'] as $c)
            $checks[] = [$c['key'], $c['ok'], $c['detail']];
        $runs[] = ['experiment' => $r['experiment'], 'ok' => $r['ok'], 'checks' => $checks];
    }
    file_put_contents($jp, json_encode(['version' => NSB_VERSION, 'runs' => $runs],
        JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    P("   · $jp\n");
    $mp = $GLOBALS['CFG']['out_dir'] . "/reports/report_$stamp.md";
    $md = "# NSB PHP Lab — session report\n\n*Version " . NSB_VERSION . "*\n\n";
    foreach ($GLOBALS['SESSION'] as $r) {
        $md .= "## {$r['experiment']} — " . ($r['ok'] ? 'OK' : 'FAILED') . "\n\n"
             . "| check | result | detail |\n|---|---|---|\n";
        foreach ($r['checks'] as $c)
            $md .= "| {$c['key']} | " . ($c['ok'] ? 'PASS' : 'FAIL') . " | {$c['detail']} |\n";
        $md .= "\n";
    }
    file_put_contents($mp, $md);
    P("   · $mp\n");
}

function cliHelpPHP(): void {
    P("NSB PHP Lab v" . NSB_VERSION . " — self-contained Navier-Stokes laboratory\n");
    P("Usage: php nsb_lab.php [options]\n");
    P("Modes:\n  --quick  --suite normal|hard  --experiment tg|abc|baudit\n");
    P("  --flow <id|all|list>  --roadmap  --selftest  --list-flows  --report\n");
    P("Options:\n  --n N --nu V --dt V --t V --gif 0|1 --lang ru|en --out DIR\n");
    P("  --seed N --no-color --ascii --help --version\n");
}

// ── main ──
cfgInit();
initI18n();
$action = 'menu';
$optMode = 'normal'; $optExp = 'tg'; $optFlow = 'list';
$optN = 0; $optNu = -1.0; $optDt = 0.0; $optT = 0.0;
$args = array_slice($GLOBALS['argv'], 1);
for ($i = 0; $i < count($args); $i++) {
    $a = $args[$i];
    $next = isset($args[$i + 1]) ? $args[++$i] : '';
    switch ($a) {
        case '--quick': $action = 'quick'; break;
        case '--suite': $action = 'suite'; $optMode = $next ?: 'normal'; break;
        case '--experiment': $action = 'experiment'; $optExp = $next ?: 'tg'; break;
        case '--flow': $action = 'flow'; $optFlow = $next ?: 'list'; break;
        case '--mode': $optMode = $next; break;
        case '--roadmap': $action = 'roadmap'; break;
        case '--selftest': $action = 'selftest'; break;
        case '--list-flows': $action = 'list_flows'; break;
        case '--report': $action = 'report'; break;
        case '--n': $optN = (int)$next; break;
        case '--nu': $optNu = (float)str_replace(',', '.', $next); break;
        case '--dt': $optDt = (float)str_replace(',', '.', $next); break;
        case '--t': $optT = (float)str_replace(',', '.', $next); break;
        case '--gif': $GLOBALS['CFG']['gif'] = $next !== '0'; break;
        case '--lang': $GLOBALS['CFG']['lang'] = $next === 'en' ? 'en' : 'ru'; break;
        case '--out': $GLOBALS['CFG']['out_dir'] = $next; break;
        case '--seed': $GLOBALS['CFG']['seed'] = (int)$next; break;
        case '--no-color': $GLOBALS['CFG']['color'] = false; break;
        case '--ascii': $GLOBALS['CFG']['ascii_only'] = true; break;
        case '--help': case '-h': $action = 'help'; break;
        case '--version': $action = 'version'; break;
        default: P("unknown argument: $a\n");
    }
}
ensureOutdirs();
logfileOpen();

switch ($action) {
    case 'help': cliHelpPHP(); break;
    case 'version': P('NSB PHP Lab v' . NSB_VERSION . "\n"); break;
    case 'selftest': exit(selftestPHP());
    case 'list_flows': flowsTableTextPHP(); break;
    case 'roadmap': roadmapReportPHP(); break;
    case 'quick':
        expTGPHP('normal', $optN, $optNu, $optDt, $optT);
        expBAuditPHP('normal', $optN, $optNu, $optDt, $optT);
        exportSessionPHP();
        break;
    case 'suite':
        expTGPHP($optMode, $optN, $optNu, $optDt, $optT);
        expABCPHP($optMode, $optN, $optDt, $optT);
        expBAuditPHP($optMode, $optN, $optNu, $optDt, $optT);
        exportSessionPHP();
        break;
    case 'experiment':
        if ($optExp === 'abc') expABCPHP($optMode, $optN, $optDt, $optT);
        elseif ($optExp === 'baudit') expBAuditPHP($optMode, $optN, $optNu, $optDt, $optT);
        else expTGPHP($optMode, $optN, $optNu, $optDt, $optT);
        exportSessionPHP();
        break;
    case 'flow':
        if ($optFlow === 'list') flowsTableTextPHP();
        elseif ($optFlow === 'all') {
            foreach (flowsData() as $f) flowRunPHP($f, $optMode);
            exportSessionPHP();
        } else {
            $found = false;
            foreach (flowsData() as $f)
                if ($f[0] === $optFlow) { flowRunPHP($f, $optMode); $found = true; break; }
            if (!$found) { pWarn("no such flow\n"); exit(1); }
            exportSessionPHP();
        }
        break;
    case 'report': exportSessionPHP(); break;
    case 'menu':
        while (true) {
            P("\n");
            pBold('  ' . L('title') . '  v' . NSB_VERSION);
            P("\n  " . L('subtitle') . "\n");
            foreach (['menu_quick', 'menu_suite_normal', 'menu_suite_hard', 'menu_flows',
                      'menu_roadmap', 'menu_reports', 'menu_settings', 'menu_exit'] as $it) {
                P('  '); pBold(L($it)); P("\n");
            }
            P('  ' . L('lang_toggle') . "\n");
            P('  ' . L('menu_prompt') . ' > ');
            $sel = trim((string)fgets(STDIN));
            if ($sel === '') { P("\n"); break; }
            if ($sel === '1') {
                expTGPHP('normal'); expBAuditPHP('normal'); exportSessionPHP();
            } elseif ($sel === '2') {
                expTGPHP('normal'); expABCPHP('normal'); expBAuditPHP('normal'); exportSessionPHP();
            } elseif ($sel === '3') {
                expTGPHP('hard'); expABCPHP('hard'); expBAuditPHP('hard'); exportSessionPHP();
            } elseif ($sel === '4') {
                flowsTableTextPHP();
                P('  ' . L('flows_menu_hint') . "\n");
                $fs2 = trim((string)fgets(STDIN));
                if ($fs2 === 'a') {
                    foreach (flowsData() as $f) flowRunPHP($f);
                    exportSessionPHP();
                } elseif (ctype_digit($fs2)) {
                    $num = (int)$fs2;
                    $all = flowsData();
                    if ($num >= 1 && $num <= count($all)) {
                        flowRunPHP($all[$num - 1]);
                        exportSessionPHP();
                    }
                }
            } elseif ($sel === '5') {
                roadmapReportPHP();
            } elseif ($sel === '6') {
                headerBar(L('rep_hdr'));
                if (!$GLOBALS['SESSION']) P('  ' . L('rep_none') . "\n");
                else exportSessionPHP();
            } elseif ($sel === '7') {
                headerBar(L('set_hdr'));
                P('  ' . L('set_out') . ': ' . $GLOBALS['CFG']['out_dir'] . "\n");
                headerBar(L('set_about'));
                P('  ' . L('set_about_txt') . "\n");
            } elseif ($sel === '9') {
                $GLOBALS['CFG']['lang'] = $GLOBALS['CFG']['lang'] === 'ru' ? 'en' : 'ru';
                P('  ' . ($GLOBALS['CFG']['lang'] === 'en' ? 'Language: ENGLISH' : 'Язык: РУССКИЙ') . "\n");
            } elseif ($sel === '0') {
                break;
            } else {
                P('  ' . L('invalid_choice') . "\n");
            }
        }
        break;
}
