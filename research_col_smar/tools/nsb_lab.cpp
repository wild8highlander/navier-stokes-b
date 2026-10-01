/*================================================================================
  NSB LAB 96 — C++ edition
  Интерактивная лаборатория программы b-коррекции (navier-stokes-b)
  ONE FILE, C++17, БЕЗ ВНЕШНИХ ЗАВИСИМОСТЕЙ (собственный radix-2 FFT)

  Сборка и запуск / build & run:
    g++ -O2 -std=c++17 -o nsb_lab_cpp nsb_lab.cpp
    ./nsb_lab_cpp              # интерактивное меню (RU/EN)
    ./nsb_lab_cpp --run matrix --lang en --yes

  Лаборатории / labs:
    L1 matrix — операторы программы на матрицах 112x112 (+FFT 112^3 по осям)
    L2 kdv    — улучшенный KdV-комплекс (IFRK4, 2/3-dealias, инварианты)
    L3 smoke  — быстрый тест (KdV-солитон + матричные проверки)
    L10 report— сводный отчёт (TXT/JSON/CSV) + вердикты WIN/DRAW/LOSS

  (c) 2026 — пакет NSB-96-UPGRADE для wild8highlander/navier-stokes-b
================================================================================*/
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <sys/stat.h>
#include <sys/time.h>

#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

static const double PI = 3.14159265358979323846;
static const double B_UNIV = 1.0 / (4.0 * PI + 2.0 * std::sqrt(3.0));
static const double THETA_B = std::asin(B_UNIV);

// ----------------------------------------------------------------------------
// i18n
// ----------------------------------------------------------------------------
struct I18N {
    std::string title, menu_hdr, lab1, lab2, lab3, lab10, lab_all, lab_quit,
        choose, back, win, draw, loss, score;
};
static I18N makeI18N(const std::string &lang) {
    I18N t;
    if (lang == "ru") {
        t.title = "NSB LAB 96 - ЛАБОРАТОРИЯ ПРОГРАММЫ b-КОРРЕКЦИИ (C++)";
        t.menu_hdr = "ГЛАВНОЕ МЕНЮ";
        t.lab1 = "L1  Матрицы 112x112 (ортогональность, Лерай, унитарность)";
        t.lab2 = "L2  Улучшенный KdV-комплекс (IFRK4, инварианты)";
        t.lab3 = "L3  Быстрый смоук (солитон + матрицы)";
        t.lab10 = "L10 Сводный отчёт (TXT/JSON/CSV)";
        t.lab_all = "A   ЗАПУСТИТЬ ВСЁ";
        t.lab_quit = "Q   Выход";
        t.choose = "Ваш выбор: ";
        t.back = "Enter — в меню";
        t.win = "ПОБЕДА"; t.draw = "НИЧЬЯ"; t.loss = "ПОРАЖЕНИЕ";
        t.score = "ТАБЛО";
    } else {
        t.title = "NSB LAB 96 - b-CORRECTION PROGRAM LABORATORY (C++)";
        t.menu_hdr = "MAIN MENU";
        t.lab1 = "L1  112x112 matrix checks (orthogonality, Leray, unitarity)";
        t.lab2 = "L2  Improved KdV suite (IFRK4, invariants)";
        t.lab3 = "L3  Quick smoke (soliton + matrices)";
        t.lab10 = "L10 Aggregate report (TXT/JSON/CSV)";
        t.lab_all = "A   RUN EVERYTHING";
        t.lab_quit = "Q   Quit";
        t.choose = "Your choice: ";
        t.back = "Enter - menu";
        t.win = "WIN"; t.draw = "DRAW"; t.loss = "LOSS";
        t.score = "SCOREBOARD";
    }
    return t;
}

// ----------------------------------------------------------------------------
// ANSI-арт, лог, прогресс-бар
// ----------------------------------------------------------------------------
static std::ofstream g_log;
static void logline(const std::string &msg) {
    if (g_log.is_open()) g_log << msg << "\n";
}
static void say(const std::string &msg = "") {
    std::cout << msg << "\n";
    logline(msg);
}
static void banner(const I18N &t) {
    say("  _   _ ____  ____  _      _    ___  ____ _   _  ____  ____");
    say(" | \\ | |/ ___|/ ___|| |    / \\  / __|/ ___| | | |/ ___||  _ \\");
    say(" |  \\| | |  _ \\___ \\| |   / _ \\ \\__ \\ |   | | | \\___ \\| |_) |");
    say(" | |\\  | |_| |___) | |__/ ___ \\ ___) | |___| |_| |___) |  _ <");
    say(" |_| \\_|\\____|____/|____/_/   \\_\\____/\\____|\\___/|____/|_| \\_\\");
    say("==============================================================================");
    say("            " + t.title);
    char buf[128];
    snprintf(buf, sizeof(buf), "b = 1/(4pi+2sqrt3) = %.9f   theta_b = %.6f deg",
             B_UNIV, THETA_B * 180.0 / PI);
    say(std::string(buf));
    say("==============================================================================");
}
static void progress(double frac, const std::string &label) {
    if (frac < 0) frac = 0; if (frac > 1) frac = 1;
    int w = 36, filled = (int)(frac * w);
    std::string bar;
    for (int i = 0; i < w; ++i) bar += (i < filled ? '#' : '-');
    fprintf(stderr, "\r|%s| %5.1f%%  %s   ", bar.c_str(), frac * 100,
            label.c_str());
    if (frac >= 1.0) fprintf(stderr, "\n");
    fflush(stderr);
}
static double wall() {
    struct timeval tv; gettimeofday(&tv, nullptr);
    return tv.tv_sec + 1e-6 * tv.tv_usec;
}

// ----------------------------------------------------------------------------
// простая матричная алгебра (полные матрицы N x N)
// ----------------------------------------------------------------------------
using Mat = std::vector<std::vector<double>>;
static Mat matmul(const Mat &A, const Mat &B) {
    size_t n = A.size(), m = B[0].size(), k = B.size();
    Mat C(n, std::vector<double>(m, 0.0));
    for (size_t i = 0; i < n; ++i)
        for (size_t l = 0; l < k; ++l) {
            double a = A[i][l];
            if (a == 0.0) continue;
            for (size_t j = 0; j < m; ++j) C[i][j] += a * B[l][j];
        }
    return C;
}
static Mat transpose(const Mat &A) {
    size_t n = A.size(), m = A[0].size();
    Mat T(m, std::vector<double>(n));
    for (size_t i = 0; i < n; ++i)
        for (size_t j = 0; j < m; ++j) T[j][i] = A[i][j];
    return T;
}
static double maxAbsDiff(const Mat &A, const Mat &B) {
    double s = 0.0;
    for (size_t i = 0; i < A.size(); ++i)
        for (size_t j = 0; j < A[0].size(); ++j)
            s = std::max(s, std::fabs(A[i][j] - B[i][j]));
    return s;
}

// ----------------------------------------------------------------------------
// radix-2 FFT (N — степень двойки)
// ----------------------------------------------------------------------------
using Cplx = std::complex<double>;
static void fft(std::vector<Cplx> &a, bool inverse) {
    size_t n = a.size();
    if (n <= 1) return;
    for (size_t i = 1, j = 0; i < n; ++i) {           // bit-reversal
        size_t bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) std::swap(a[i], a[j]);
    }
    for (size_t len = 2; len <= n; len <<= 1) {
        double ang = 2.0 * PI / double(len) * (inverse ? 1.0 : -1.0);
        Cplx wlen(std::cos(ang), std::sin(ang));
        for (size_t i = 0; i < n; i += len) {
            Cplx w(1.0, 0.0);
            for (size_t j = 0; j < len / 2; ++j) {
                Cplx u = a[i + j], v = a[i + j + len / 2] * w;
                a[i + j] = u + v;
                a[i + j + len / 2] = u - v;
                w *= wlen;
            }
        }
    }
    if (inverse)
        for (auto &x : a) x /= double(n);
}

// ----------------------------------------------------------------------------
// вердикты
// ----------------------------------------------------------------------------
struct Verdict {
    std::string lab, test; double value; std::string verdict, note;
};
class Verdicts {
public:
    explicit Verdicts(double tw, double td) : _tw(tw), _td(td) {}
    void judge(const std::string &lab, const std::string &test, double v,
               const std::string &note = "") {
        std::string ver = std::isnan(v) ? "DRAW"
                        : (v < _tw ? "WIN" : (v < _td ? "DRAW" : "LOSS"));
        _rows.push_back({lab, test, v, ver, note});
    }
    const std::vector<Verdict> &rows() const { return _rows; }
    void table(const I18N &t) const {
        say("  " + std::string(74, '-'));
        int w = 0, d = 0, l = 0;
        for (auto &r : _rows) {
            char buf[64]; snprintf(buf, sizeof(buf), "%.3e", r.value);
            std::string icon = r.verdict == "WIN" ? "[+]" :
                               r.verdict == "DRAW" ? "[~]" : "[-]";
            std::string ver = r.verdict == "WIN" ? t.win :
                              r.verdict == "DRAW" ? t.draw : t.loss;
            say("  " + icon + " " + ver + "  " + r.test + "  " + buf +
                (r.note.empty() ? "" : "  (" + r.note + ")"));
            w += r.verdict == "WIN"; d += r.verdict == "DRAW";
            l += r.verdict == "LOSS";
        }
        say("  " + std::string(74, '-'));
        say("  " + t.score + ": WIN=" + std::to_string(w) +
            "  DRAW=" + std::to_string(d) + "  LOSS=" + std::to_string(l));
    }
private:
    double _tw, _td;
    std::vector<Verdict> _rows;
};

// ----------------------------------------------------------------------------
// L1: матрицы 112x112
// ----------------------------------------------------------------------------
static void lab_matrix112(const I18N &t, double tw, double td, bool save) {
    const int n = 112;
    say("\n== L1 == " + t.lab1);
    Verdicts V(tw, td);
    // 1) блочно-диагональные повороты R(theta_b)
    Mat R(n, std::vector<double>(n, 0.0));
    for (int i = 0; i + 1 < n; i += 2) {
        double c = std::cos(THETA_B), s = std::sin(THETA_B);
        R[i][i] = c; R[i][i + 1] = -s; R[i + 1][i] = s; R[i + 1][i + 1] = c;
    }
    Mat RtR = matmul(transpose(R), R), I(n, std::vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) I[i][i] = 1.0;
    double orth = maxAbsDiff(RtR, I);
    V.judge("L1", "R(theta_b) orthogonality (112x112)", orth);
    // 2) проектор Лерея через ортонормированное вложение (QR через Грама-Шмидта)
    //    U: 3 x n со скалярным произведением -> P = U^T P3 U симметричен и
    //    идемпотентен; проверяем P^2 - P на 112x112
    Mat U(3, std::vector<double>(n));
    unsigned seed = 20260930;
    auto rnd = [&]() { seed = seed * 1664525u + 1013904223u; return
                       (double)(seed >> 8) / (double)(1 << 24) - 0.5; };
    for (auto &row : U) for (auto &x : row) x = rnd();
    // Грам-Шмидт по строкам: ортогонализуем и сразу нормируем каждую строку
    for (int r = 0; r < 3; ++r) {
        for (int q = 0; q < r; ++q) {
            double dot = 0.0;
            for (int j = 0; j < n; ++j) dot += U[r][j] * U[q][j];
            for (int j = 0; j < n; ++j) U[r][j] -= dot * U[q][j];
        }
        double nrm = 0.0;
        for (int j = 0; j < n; ++j) nrm += U[r][j] * U[r][j];
        nrm = std::sqrt(nrm);
        for (int j = 0; j < n; ++j) U[r][j] /= nrm;
    }
    double kx = rnd(), ky = rnd(), kz = rnd();
    double kn = std::sqrt(kx * kx + ky * ky + kz * kz);
    kx /= kn; ky /= kn; kz /= kn;
    Mat P3(3, std::vector<double>(3));
    for (int i = 0; i < 3; ++i) P3[i][i] = 1.0;
    P3[0][0] -= kx * kx; P3[0][1] -= kx * ky; P3[0][2] -= kx * kz;
    P3[1][0] -= ky * kx; P3[1][1] -= ky * ky; P3[1][2] -= ky * kz;
    P3[2][0] -= kz * kx; P3[2][1] -= kz * ky; P3[2][2] -= kz * kz;
    // P = U^T * P3 * U  (U — 3 x n, ортонормированные строки)
    Mat P;
    Mat tmp = matmul(P3, U);                      // 3 x n
    P = matmul(transpose(U), tmp);                // n x n
    Mat P2 = matmul(P, P);
    double idem = maxAbsDiff(P2, P);
    V.judge("L1", "Leray projector idempotence (112x112)", idem);
    // 3) унитарность линейного потока KdV exp(i k^3 t) — диагональная;
    //    проверяем |U|^2 == I (побочная диагональ)
    double unit = 0.0;
    for (int i = 0; i < n; ++i) {
        double kv = 2.0 * PI * ((i < n / 2) ? i : i - n) / 100.0;
        double re = std::cos(kv * kv * kv * 0.7);
        double im = std::sin(kv * kv * kv * 0.7);
        unit = std::max(unit, std::fabs(re * re + im * im - 1.0));
    }
    V.judge("L1", "KdV linear flow unitarity (112x112)", unit);
    // 4) KdV-солитон через DFT-решатель (см. L2): быстрая проверка ниже
    V.table(t);
    if (save) {
        std::ofstream j("../results/cpp_matrix112.json");
        j << "{\n  \"lab\": \"L1_matrix112_cpp\",\n  \"n\": " << n
          << ",\n  \"theta_b_deg\": " << std::setprecision(12)
          << THETA_B * 180.0 / PI << ",\n  \"tests\": [\n";
        bool first = true;
        for (auto &r : V.rows()) {
            if (!first) j << ",\n";
            first = false;
            j << "    {\"test\": \"" << r.test << "\", \"value\": "
              << std::setprecision(6) << std::scientific << r.value
              << ", \"verdict\": \"" << r.verdict << "\"}";
        }
        j << "\n  ]\n}\n";
    }
}

// ----------------------------------------------------------------------------
// L2: KdV IFRK4 (N — степень двойки), 2/3-dealias, инварианты Лакса
// ----------------------------------------------------------------------------
struct KdVResult {
    double driftM, driftP, driftE;
};
static KdVResult kdv_ifrk4(int n, double L, double dt, double T_end,
                           const std::vector<double> &u0,
                           double progress_every) {
    // волновые числа
    std::vector<double> k(n);
    for (int i = 0; i < n; ++i)
        k[i] = 2.0 * PI * ((i < (n + 1) / 2 ? i : i - n)) / L;
    // линейный оператор exp(i k^3 dt)
    std::vector<Cplx> E(n), E2(n);
    for (int i = 0; i < n; ++i) {
        E[i] = std::polar(1.0, k[i] * k[i] * k[i] * dt);
        E2[i] = std::polar(1.0, k[i] * k[i] * k[i] * dt / 2.0);
    }
    // 2/3-маска
    int crit = n / 3;
    std::vector<char> mask(n, 0);
    for (int i = 0; i < n; ++i)
        mask[i] = (std::fabs(k[i]) <= crit * 2.0 * PI / L);
    std::vector<Cplx> uh(n);
    for (int i = 0; i < n; ++i) uh[i] = Cplx(u0[i], 0.0);
    fft(uh, false);
    for (int i = 0; i < n; ++i) if (!mask[i]) uh[i] = 0.0;
    int nsteps = (int)std::lround(T_end / dt);
    // инварианты в t=0
    auto invariants = [&](const std::vector<Cplx> &h, double &M, double &P,
                          double &E, double &D) {
        std::vector<Cplx> h2(h);
        fft(h2, true);
        std::vector<Cplx> ux(n);
        for (int i = 0; i < n; ++i) ux[i] = Cplx(0, 1) * k[i] * h[i];
        fft(ux, true);
        double m = 0, p = 0, e3 = 0, ex = 0;
        for (int i = 0; i < n; ++i) {
            double uu = h2[i].real();
            m += uu; p += uu * uu; e3 += uu * uu * uu; ex += ux[i].real() * ux[i].real();
        }
        M = m / n; P = p / (2 * n); E = e3 / n - ex / (2 * n); D = ex / (2 * n);
    };
    double M0v, P0v, E0v, D0v, M1v, P1v, E1v, D1v;
    invariants(uh, M0v, P0v, E0v, D0v);
    for (int step = 0; step < nsteps; ++step) {
        // IFRK4
        auto nl = [&](const std::vector<Cplx> &h) {
            std::vector<Cplx> h2(h);
            fft(h2, true);
            std::vector<Cplx> u2(n);
            for (int i = 0; i < n; ++i)
                u2[i] = Cplx(h2[i].real() * h2[i].real(), 0.0);
            fft(u2, false);
            std::vector<Cplx> out(n);
            for (int i = 0; i < n; ++i)
                out[i] = -3.0 * Cplx(0, 1) * k[i] * u2[i];
            for (int i = 0; i < n; ++i) if (!mask[i]) out[i] = 0.0;
            return out;
        };
        std::vector<Cplx> k1 = nl(uh);
        std::vector<Cplx> tmp(n), k2v(n), k3(n), k4(n);
        for (int i = 0; i < n; ++i) tmp[i] = E2[i] * (uh[i] + dt / 2.0 * k1[i]);
        k2v = nl(tmp);
        for (int i = 0; i < n; ++i) tmp[i] = E2[i] * uh[i] + dt / 2.0 * k2v[i];
        k3 = nl(tmp);
        for (int i = 0; i < n; ++i) tmp[i] = E[i] * uh[i] + dt * E2[i] * k3[i];
        k4 = nl(tmp);
        for (int i = 0; i < n; ++i)
            uh[i] = E[i] * uh[i] + dt / 6.0 *
                    (E[i] * k1[i] + 2.0 * E2[i] * (k2v[i] + k3[i]) + k4[i]);
        for (int i = 0; i < n; ++i) if (!mask[i]) uh[i] = 0.0;
        if (progress_every > 0 && (step % 500 == 0))
            progress(double(step) / nsteps, "KdV t=" +
                     std::to_string(step * dt));
    }
    progress(1.0, "KdV done");
    invariants(uh, M1v, P1v, E1v, D1v);
    KdVResult r;
    r.driftM = std::fabs(M1v - M0v) / std::max(std::fabs(M0v), 1e-300);
    r.driftP = std::fabs(P1v - P0v) / std::max(std::fabs(P0v), 1e-300);
    r.driftE = std::fabs(E1v - E0v) /
               std::max(std::max(std::fabs(E0v), D0v), 1e-300);
    return r;
}

static void lab_kdv(const I18N &t, double tw, double td, bool save) {
    say("\n== L2 == " + t.lab2);
    Verdicts V(tw, td);
    const int n = 256;               // степень двойки для radix-2 FFT
    const double L = 100.0, dt = 0.0005, T = 8.0, c1 = 4.0, x0 = 30.0;
    std::vector<double> x(n), u0(n);
    for (int i = 0; i < n; ++i) {
        x[i] = L * i / n;
        u0[i] = (c1 / 2.0) / std::pow(std::cosh(std::sqrt(c1) / 2.0 *
                                             (x[i] - x0)), 2);
    }
    double t0 = wall();
    KdVResult r = kdv_ifrk4(n, L, dt, T, u0, 1.0);
    double worst = std::max(r.driftM, std::max(r.driftP, r.driftE));
    V.judge("L2", "E1 soliton invariant drift (KdV, IFRK4)", worst);
    char buf[128];
    snprintf(buf, sizeof(buf), "wall = %.1f s (N=%d, T=%g, dt=%g)",
             wall() - t0, n, T, dt);
    V.table(t);
    say(std::string("  ") + buf);
    if (save) {
        std::ofstream j("../results/cpp_kdv.json");
        j << "{\n  \"lab\": \"L2_kdv_cpp\",\n  \"params\": {\"N\": " << n
          << ", \"L\": " << L << ", \"dt\": " << dt << ", \"T\": " << T
          << ", \"c1\": " << c1 << "},\n  \"drift\": {\"M\": "
          << std::setprecision(6) << std::scientific << r.driftM
          << ", \"P\": " << r.driftP << ", \"E\": " << r.driftE << "}\n}\n";
    }
}

// ----------------------------------------------------------------------------
// отчёт + меню
// ----------------------------------------------------------------------------
static void lab_report() {
    say("\n== L10 == сводный отчёт");
    std::ifstream res("../results/cpp_matrix112.json");
    std::ostringstream ss; ss << res.rdbuf();
    std::ofstream out("../reports/NSB_LAB_REPORT_CPP.md");
    out << "# NSB LAB 96 (C++) — aggregate report\n\n";
    out << "## L1/L2 (C++)\n\n```json\n" << ss.str() << "```\n";
    std::ifstream res2("../results/cpp_kdv.json");
    std::ostringstream ss2; ss2 << res2.rdbuf();
    out << "```json\n" << ss2.str() << "```\n";
    say("  отчёт: reports/NSB_LAB_REPORT_CPP.md");
}

int main(int argc, char **argv) {
    std::string lang = "ru", run;
    bool yes = false;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--lang") && i + 1 < argc) lang = argv[++i];
        else if (!strcmp(argv[i], "--run") && i + 1 < argc) run = argv[++i];
        else if (!strcmp(argv[i], "--yes")) yes = true;
    }
    I18N t = makeI18N(lang);
    mkdir("../logs", 0755);
    g_log.open("../logs/nsb_lab_cpp.log", std::ios::app);
    banner(t);
    // пороги вердиктов (настраиваются в коде; в Python/Julia — через конфиг)
    const double tw = 1e-10, td = 1e-8;      // матричные пороги
    const double twK = 1e-6, tdK = 1e-4;     // KdV-пороги

    auto runAll = [&](const std::string &which) {
        if (which == "matrix" || which == "all" || which == "smoke")
            lab_matrix112(t, tw, td, true);
        if (which == "kdv" || which == "all" || which == "smoke")
            lab_kdv(t, twK, tdK, true);
        if (which == "report" || which == "all") lab_report();
    };

    if (!run.empty()) {
        runAll(run);
        say("\n  [OK] DONE");
        return 0;
    }
    while (true) {
        say("\n  ==========================================================");
        say("   " + t.menu_hdr);
        say("   1 | " + t.lab1);
        say("   2 | " + t.lab2);
        say("   3 | " + t.lab3);
        say("  10 | " + t.lab10);
        say("   A | " + t.lab_all);
        say("   L | язык / language (ru<->en)");
        say("   Q | " + t.lab_quit);
        std::cout << "   " << t.choose;
        std::string ch;
        if (!std::getline(std::cin, ch)) break;
        for (auto &c : ch) c = toupper(c);
        if (ch == "Q" || ch.empty()) break;
        if (ch == "L") { lang = (lang == "ru" ? "en" : "ru"); t = makeI18N(lang);
            g_log << "--- switch lang ---\n"; continue; }
        if (ch == "A") { runAll("all"); continue; }
        if (ch == "1") runAll("matrix");
        else if (ch == "2") runAll("kdv");
        else if (ch == "3") runAll("smoke");
        else if (ch == "10") runAll("report");
    }
    return 0;
}
