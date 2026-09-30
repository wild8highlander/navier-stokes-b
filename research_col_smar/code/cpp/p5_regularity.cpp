// p5_regularity.cpp — P5 C++ verification track (long double core).
//
// Mirrors code/python/p5_regularity.py:
//   (1) analytic block: the universal b-correction constants, the
//       generalized Pao normalization beta_b and the universal
//       dissipation-peak prediction x*(b), the hyperdissipation scaling
//       exponents 1/(6b-2), the LPS reciprocal-relation table and the
//       master C_s(C_K) regression of the program;
//   (2) snapshot diagnostics: loads the raw f64 snapshot of the run A
//       field (u, omega) written by the Python protocol and recomputes
//       the physical-space regularity diagnostics (energy, enstrophy,
//       sup-norms, <u^4>, <u^6>) in long double accumulation;
//   (3) miniature 16^3 Taylor-Green DNS with a hand-written radix-2 FFT
//       and the same integrating-factor midpoint RK2 as the Python
//       solver — the dynamical cross-language check.
// Output: results/p5_cpp.json
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

#include "sk_core.hpp"

namespace {

using cd = std::complex<double>;

constexpr double kBUniv = 1.0 / (4.0 * M_PI + 2.0 * std::sqrt(3.0));

// --- generalized Pao normalization (ch. 12.5) ------------------------------
long double beta_b(long double b, long double ck) {
    const long double a = 2.0L * b - 2.0L / 3.0L;
    return std::pow(ck * std::tgammal(a / (2.0L * b)) / b, 2.0L * b / a);
}

long double x_star(long double b, long double ck) {
    const long double bb = beta_b(b, ck);
    return std::pow((2.0L * b - 5.0L / 3.0L) / (2.0L * b * bb),
                    1.0L / (2.0L * b));
}

// --- radix-2 complex FFT (n = 16 per axis) ---------------------------------
void fft1d(cd* a, int n, int sign) {
    // bit-reversal permutation
    for (int i = 1, j = 0; i < n; ++i) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) {
            j ^= bit;
        }
        j ^= bit;
        if (i < j) {
            std::swap(a[i], a[j]);
        }
    }
    for (int len = 2; len <= n; len <<= 1) {
        const double ang = sign * 2.0 * M_PI / len;
        const cd wl(std::cos(ang), std::sin(ang));
        for (int i = 0; i < n; i += len) {
            cd w(1.0, 0.0);
            for (int j = 0; j < len / 2; ++j) {
                const cd u = a[i + j];
                const cd v = a[i + j + len / 2] * w;
                a[i + j] = u + v;
                a[i + j + len / 2] = u - v;
                w *= wl;
            }
        }
    }
}

// --- miniature 16^3 solver (layout [comp][x][y][z], z contiguous) ----------
constexpr int MN = 16;

struct Field {
    std::vector<cd> c;  // 3 * MN^3 complex
    explicit Field(bool zero) : c(3 * MN * MN * MN, cd(0.0, 0.0)) {
        (void)zero;
    }
};

void fft_axis(Field& f, int axis, int sign) {
    std::vector<cd> buf(MN);
    const int n2 = MN * MN;
    for (int comp = 0; comp < 3; ++comp) {
        cd* base = f.c.data() + comp * n2 * MN;
        for (int i = 0; i < MN; ++i) {
            for (int j = 0; j < MN; ++j) {
                for (int k = 0; k < MN; ++k) {
                    int idx;
                    if (axis == 0) {
                        idx = k * n2 + j * MN + i;  // x varies with stride n2
                    } else if (axis == 1) {
                        idx = i * n2 + k * MN + j;  // y varies with stride MN
                    } else {
                        idx = i * n2 + j * MN + k;  // z stride 1
                    }
                    buf[k] = base[idx];
                }
                fft1d(buf.data(), MN, sign);
                for (int k = 0; k < MN; ++k) {
                    int idx;
                    if (axis == 0) {
                        idx = k * n2 + j * MN + i;
                    } else if (axis == 1) {
                        idx = i * n2 + k * MN + j;
                    } else {
                        idx = i * n2 + j * MN + k;
                    }
                    base[idx] = buf[k];
                }
            }
        }
    }
}

void forward(Field& f) {
    fft_axis(f, 0, -1);
    fft_axis(f, 1, -1);
    fft_axis(f, 2, -1);
}

void inverse(Field& f) {
    fft_axis(f, 0, +1);
    fft_axis(f, 1, +1);
    fft_axis(f, 2, +1);
    const double s = 1.0 / (MN * MN * MN);
    for (auto& z : f.c) {
        z *= s;
    }
}

// wavenumber value at flat index along one axis (FFTW ordering)
inline double kval(int i) {
    return i <= MN / 2 ? double(i) : double(i - MN);
}

struct MiniDiag {
    double E = 0.0;
    double Omega = 0.0;
    double wmax = 0.0;
};

MiniDiag diag_of(const Field& uh) {
    const int n3 = MN * MN * MN;
    MiniDiag d;
    double se = 0.0, sw = 0.0;
    for (int comp = 0; comp < 3; ++comp) {
        for (int i = 0; i < n3; ++i) {
            se += std::norm(uh.c[comp * n3 + i]);
        }
    }
    d.E = se / double(n3) / double(n3);  // sum |uh|^2 / n^6
    // enstrophy from the vorticity spectrum
    Field wh(true);
    const int n2 = MN * MN;
    for (int ix = 0; ix < MN; ++ix) {
        for (int iy = 0; iy < MN; ++iy) {
            for (int iz = 0; iz < MN; ++iz) {
                const int id = ix * n2 + iy * MN + iz;
                const double kx = kval(ix), ky = kval(iy), kz = kval(iz);
                const cd iu(0.0, 1.0);
                wh.c[0 * n3 + id] = iu * (ky * uh.c[2 * n3 + id] - kz * uh.c[1 * n3 + id]);
                wh.c[1 * n3 + id] = iu * (kz * uh.c[0 * n3 + id] - kx * uh.c[2 * n3 + id]);
                wh.c[2 * n3 + id] = iu * (kx * uh.c[1 * n3 + id] - ky * uh.c[0 * n3 + id]);
            }
        }
    }
    for (int comp = 0; comp < 3; ++comp) {
        for (int i = 0; i < n3; ++i) {
            sw += std::norm(wh.c[comp * n3 + i]);
        }
    }
    d.Omega = sw / double(n3) / double(n3);
    return d;
}

// nonlinear term N(u) = P[u x omega] (2/3-dealised, mean-free)
void nonlinear(const Field& uh, Field& out) {
    const int n3 = MN * MN * MN;
    Field u(true), w(true);
    // physical fields
    u = uh;
    inverse(u);
    Field wh(true);
    {
        const int n2 = MN * MN;
        for (int ix = 0; ix < MN; ++ix) {
            for (int iy = 0; iy < MN; ++iy) {
                for (int iz = 0; iz < MN; ++iz) {
                    const int id = ix * n2 + iy * MN + iz;
                    const double kx = kval(ix), ky = kval(iy), kz = kval(iz);
                    wh.c[0 * n3 + id] =
                        cd(0.0, 1.0) * (ky * uh.c[2 * n3 + id] - kz * uh.c[1 * n3 + id]);
                    wh.c[1 * n3 + id] =
                        cd(0.0, 1.0) * (kz * uh.c[0 * n3 + id] - kx * uh.c[2 * n3 + id]);
                    wh.c[2 * n3 + id] =
                        cd(0.0, 1.0) * (kx * uh.c[1 * n3 + id] - ky * uh.c[0 * n3 + id]);
                }
            }
        }
    }
    w = wh;
    inverse(w);
    // u, w are now complex containers holding (real up to fp) fields
    Field cr(true);
    for (int i = 0; i < n3; ++i) {
        const double ux = u.c[0 * n3 + i].real();
        const double uy = u.c[1 * n3 + i].real();
        const double uz = u.c[2 * n3 + i].real();
        const double wx = w.c[0 * n3 + i].real();
        const double wy = w.c[1 * n3 + i].real();
        const double wz = w.c[2 * n3 + i].real();
        cr.c[0 * n3 + i] = cd(uy * wz - uz * wy, 0.0);
        cr.c[1 * n3 + i] = cd(uz * wx - ux * wz, 0.0);
        cr.c[2 * n3 + i] = cd(ux * wy - uy * wx, 0.0);
    }
    forward(cr);
    // projection P = I - k k / k^2 with k2e guard, 2/3 mask, mean removal
    const int n2 = MN * MN;
    const double crit = MN / 3;
    for (int ix = 0; ix < MN; ++ix) {
        for (int iy = 0; iy < MN; ++iy) {
            for (int iz = 0; iz < MN; ++iz) {
                const int id = ix * n2 + iy * MN + iz;
                const double kx = kval(ix), ky = kval(iy), kz = kval(iz);
                const double kk = kx * kx + ky * ky + kz * kz;
                const double k2e = kk > 0.0 ? kk : 1.0;
                const cd div = (kx * cr.c[0 * n3 + id] + ky * cr.c[1 * n3 + id] +
                                kz * cr.c[2 * n3 + id]) / k2e;
                const bool pass = std::fabs(kx) <= crit && std::fabs(ky) <= crit &&
                                  std::fabs(kz) <= crit;
                for (int comp = 0; comp < 3; ++comp) {
                    const double K = (comp == 0) ? kx : (comp == 1) ? ky : kz;
                    out.c[comp * n3 + id] =
                        pass ? (cr.c[comp * n3 + id] - K * div) : cd(0.0, 0.0);
                }
            }
        }
    }
    out.c[0] = out.c[1] = out.c[2] = cd(0.0, 0.0);
}

}  // namespace

int main() {
    std::ostringstream json;
    json << std::setprecision(12);
    json << "{\n";
    json << "  \"program\": \"p5_cpp\",\n";
    json << "  \"title\": \"P5 C++ verification: analytic core, snapshot "
            "diagnostics, mini-DNS\",\n";
    json << "  \"date\": \"2026-09-29\",\n";

    // ---- analytic block (long double) -------------------------------------
    const long double b = 1.0L / (4.0L * std::acos(-1.0L) +
                                   2.0L * std::sqrt(3.0L));
    const long double theta = std::asin(b);
    const long double ck = 1.5L;
    json << "  \"analytic\": {\n";
    json << "    \"b\": " << (double)b << ",\n";
    json << "    \"theta_b_deg\": " << (double)(theta * 180.0L /
                                                std::acos(-1.0L)) << ",\n";
    json << "    \"lilly_cs_sharp_CK15\": " << sk::lilly_cs_sharp(1.5) << ",\n";
    json << "    \"b_family\": [\n";
    const double bpow[4] = {1.0, 1.25, 1.5, 2.0};
    for (int i = 0; i < 4; ++i) {
        json << "      {\"b_pow\": " << bpow[i]
             << ", \"beta_b\": " << (double)beta_b(bpow[i], ck)
             << ", \"x_star\": " << (double)x_star(bpow[i], ck)
             << ", \"exp_1_over_6b_minus_2\": "
             << (double)(1.0L / (6.0L * (long double)bpow[i] - 2.0L)) << "}";
        json << (i < 3 ? ",\n" : "\n");
    }
    json << "    ],\n";
    json << "    \"lps_table\": [\n";
    const int ptab[3] = {4, 3, 2};
    const int qtab[3] = {4, 6, 3};
    for (int i = 0; i < 3; ++i) {
        json << "      {\"p\": " << ptab[i] << ", \"q\": " << qtab[i]
             << ", \"2/p+3/q\": "
             << 2.0 / ptab[i] + 3.0 / qtab[i] << "}";
        json << (i < 2 ? ",\n" : "\n");
    }
    json << "    ]\n";
    json << "  },\n";

    // ---- snapshot diagnostics ---------------------------------------------
    json << "  \"snapshot\": {\n";
    bool have_snap = false;
    std::vector<double> us(3 * 48 * 48 * 48), ws(3 * 48 * 48 * 48);
    {
        std::ifstream fu("results/p5_snapshot_u.f64", std::ios::binary);
        std::ifstream fw("results/p5_snapshot_w.f64", std::ios::binary);
        if (fu && fw) {
            fu.read(reinterpret_cast<char*>(us.data()),
                    sizeof(double) * us.size());
            fw.read(reinterpret_cast<char*>(ws.data()),
                    sizeof(double) * ws.size());
            have_snap = fu && fw;
        }
    }
    if (have_snap) {
        long double u2 = 0.0L, w2 = 0.0L, u4 = 0.0L, u6 = 0.0L;
        double umax = 0.0, wmax = 0.0;
        const int npts = 48 * 48 * 48;
        for (int i = 0; i < npts; ++i) {
            const double ux = us[i], uy = us[npts + i], uz = us[2 * npts + i];
            const double wx = ws[i], wy = ws[npts + i], wz = ws[2 * npts + i];
            const double uu = ux * ux + uy * uy + uz * uz;
            const double ww = wx * wx + wy * wy + wz * wz;
            u2 += uu;
            w2 += ww;
            u4 += uu * uu;
            u6 += uu * uu * uu;
            umax = std::max(umax, std::sqrt(uu));
            wmax = std::max(wmax, std::sqrt(ww));
        }
        const long double n3 = (long double)npts;
        json << "    \"E_phys\": " << (double)(u2 / n3) << ",\n";
        json << "    \"Omega_phys\": " << (double)(w2 / n3) << ",\n";
        json << "    \"u_inf\": " << umax << ",\n";
        json << "    \"omega_inf\": " << wmax << ",\n";
        json << "    \"u4_mean\": " << (double)(u4 / n3) << ",\n";
        json << "    \"u6_mean\": " << (double)(u6 / n3) << "\n";
    } else {
        json << "    \"available\": false\n";
    }
    json << "  },\n";

    // ---- miniature 16^3 DNS (integrating-factor midpoint RK2) -------------
    const double nu = 0.01, dt = 5.0e-3, t_end = 1.0;
    const int save_every = 10;
    Field uh(true);
    {
        // Taylor-Green initial condition
        std::vector<double> u0(3 * MN * MN * MN, 0.0);
        const double h = 2.0 * M_PI / MN;
        for (int ix = 0; ix < MN; ++ix) {
            for (int iy = 0; iy < MN; ++iy) {
                for (int iz = 0; iz < MN; ++iz) {
                    const double x = (ix + 0.5) * h;
                    const double y = (iy + 0.5) * h;
                    const double z = (iz + 0.5) * h;
                    const int id = ix * MN * MN + iy * MN + iz;
                    u0[0 * MN * MN * MN + id] = std::sin(x) * std::cos(y) * std::cos(z);
                    u0[1 * MN * MN * MN + id] = -std::cos(x) * std::sin(y) * std::cos(z);
                }
            }
        }
        for (int i = 0; i < 3 * MN * MN * MN; ++i) {
            uh.c[i] = cd(u0[i], 0.0);
        }
        forward(uh);
    }
    // project the IC and apply the 2/3 mask + mean removal
    {
        const int n3 = MN * MN * MN, n2 = MN * MN;
        const double crit = MN / 3;
        for (int ix = 0; ix < MN; ++ix) {
            for (int iy = 0; iy < MN; ++iy) {
                for (int iz = 0; iz < MN; ++iz) {
                    const int id = ix * n2 + iy * MN + iz;
                    const double kx = kval(ix), ky = kval(iy), kz = kval(iz);
                    const double kk = kx * kx + ky * ky + kz * kz;
                    const double k2e = kk > 0.0 ? kk : 1.0;
                    const cd div = (kx * uh.c[0 * n3 + id] + ky * uh.c[1 * n3 + id] +
                                    kz * uh.c[2 * n3 + id]) / k2e;
                    const bool pass = std::fabs(kx) <= crit &&
                                      std::fabs(ky) <= crit &&
                                      std::fabs(kz) <= crit;
                    for (int comp = 0; comp < 3; ++comp) {
                        const double K =
                            (comp == 0) ? kx : (comp == 1) ? ky : kz;
                        cd v = uh.c[comp * n3 + id] - K * div;
                        uh.c[comp * n3 + id] = pass ? v : cd(0.0, 0.0);
                    }
                }
            }
        }
        uh.c[0] = uh.c[1] = uh.c[2] = cd(0.0, 0.0);
    }
    // integrating factor coefficients (k^2 dissipation)
    std::vector<double> lam(3 * MN * MN * MN);
    {
        const int n3 = MN * MN * MN, n2 = MN * MN;
        for (int ix = 0; ix < MN; ++ix) {
            for (int iy = 0; iy < MN; ++iy) {
                for (int iz = 0; iz < MN; ++iz) {
                    const int id = ix * n2 + iy * MN + iz;
                    const double kk = kval(ix) * kval(ix) + kval(iy) * kval(iy) +
                                      kval(iz) * kval(iz);
                    for (int comp = 0; comp < 3; ++comp) {
                        lam[comp * n3 + id] = nu * kk;
                    }
                }
            }
        }
    }
    std::vector<double> Dv(3 * MN * MN * MN), Dmv(3 * MN * MN * MN);
    for (size_t i = 0; i < lam.size(); ++i) {
        Dv[i] = std::exp(-lam[i] * dt);
        Dmv[i] = std::sqrt(Dv[i]);
    }

    const int n_steps = int(std::lround(t_end / dt));
    Field k1(true), um(true), k2f(true);
    json << "  \"mini\": {\n";
    json << "    \"convention\": \"full-grid DFT, kz=0 counted once\",\n";
    json << "    \"series\": [\n";
    for (int step = 0; step <= n_steps; ++step) {
        if (step % save_every == 0 || step == n_steps) {
            const MiniDiag d = diag_of(uh);
            // omega_inf from the physical vorticity
            Field wh(true);
            {
                const int n3 = MN * MN * MN, n2 = MN * MN;
                for (int ix = 0; ix < MN; ++ix) {
                    for (int iy = 0; iy < MN; ++iy) {
                        for (int iz = 0; iz < MN; ++iz) {
                            const int id = ix * n2 + iy * MN + iz;
                            const double kx = kval(ix), ky = kval(iy),
                                         kz = kval(iz);
                            wh.c[0 * n3 + id] = cd(0.0, 1.0) *
                                (ky * uh.c[2 * n3 + id] - kz * uh.c[1 * n3 + id]);
                            wh.c[1 * n3 + id] = cd(0.0, 1.0) *
                                (kz * uh.c[0 * n3 + id] - kx * uh.c[2 * n3 + id]);
                            wh.c[2 * n3 + id] = cd(0.0, 1.0) *
                                (kx * uh.c[1 * n3 + id] - ky * uh.c[0 * n3 + id]);
                        }
                    }
                }
            }
            inverse(wh);
            double wmax = 0.0;
            const int n3 = MN * MN * MN;
            for (int i = 0; i < n3; ++i) {
                const double wx = wh.c[0 * n3 + i].real();
                const double wy = wh.c[1 * n3 + i].real();
                const double wz = wh.c[2 * n3 + i].real();
                wmax = std::max(wmax, std::sqrt(wx * wx + wy * wy + wz * wz));
            }
            json << "      {\"t\": " << step * dt << ", \"E\": " << d.E
                 << ", \"Omega\": " << d.Omega << ", \"omega_inf\": " << wmax
                 << "}" << ((step < n_steps) ? ",\n" : "\n");
        }
        if (step < n_steps) {
            nonlinear(uh, k1);
            const int n3 = MN * MN * MN;
            for (int i = 0; i < 3 * n3; ++i) {
                um.c[i] = Dmv[i] * (uh.c[i] + 0.5 * dt * k1.c[i]);
            }
            nonlinear(um, k2f);
            for (int i = 0; i < 3 * n3; ++i) {
                uh.c[i] = Dv[i] * uh.c[i] + dt * Dmv[i] * k2f.c[i];
            }
        }
    }
    json << "    ]\n";
    json << "  }\n";
    json << "}\n";

    std::ofstream fh("results/p5_cpp.json");
    fh << json.str();
    std::printf("[p5_cpp] snapshot: %s\n", have_snap ? "loaded" : "MISSING");
    std::printf("[p5_cpp] wrote results/p5_cpp.json\n");
    return 0;
}
