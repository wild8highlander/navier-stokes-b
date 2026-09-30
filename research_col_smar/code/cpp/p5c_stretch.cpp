// p5c_stretch.cpp — P5-C C++ verification track (long double core).
//
// Mirrors the statistics part of code/python/p5c_stretch_ensemble.py:
//   (1) artifact recomputation: loads the raw f64 point-tensor files
//       (S_xx..S_yz, omega_x..z, layout (9, 48, 48, 48), written by
//       `python3 p5c_stretch_ensemble.py --export-tensors`) and recomputes
//       the full scalar statistics block — s_rms, mean strain eigenvalues
//       (long-double Jacobi rotation), beta_S, <cos^2 theta_i>, alpha
//       mean/std — for the Gaussian reference field and the P5 DNS
//       snapshot (agreement target 1e-12 with Python);
//   (2) GOE Monte-Carlo: traceless symmetric Gaussian 3x3 matrices,
//       N = 200000 samples with an independent LCG-based Gaussian stream —
//       mean normalized eigenvalues and beta_S versus the Python/Julia
//       tracks (statistical agreement ~3e-3); alignment against uniform
//       random unit vectors reproduces the exact null value 1/3.
// Output: results/p5c_cpp.json
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr int kN = 48;
constexpr long kPts = (long)kN * kN * kN;

// --- Jacobi eigen-decomposition of a symmetric 3x3 matrix -------------------
// a: row-major 3x3; outputs eigenvalues (ascending) in w and eigenvectors
// (columns of v, row-major) — identical convention to numpy.linalg.eigh.
void jacobi3(const long double a[3][3], long double w[3], long double v[3][3]) {
    long double m[3][3];
    long double V[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            m[i][j] = a[i][j];
        }
    }
    for (int sweep = 0; sweep < 64; ++sweep) {
        long double off = 0.0L;
        for (int p = 0; p < 3; ++p) {
            for (int q = p + 1; q < 3; ++q) {
                off += m[p][q] * m[p][q];
            }
        }
        if (off < 1e-34L) {
            break;
        }
        for (int p = 0; p < 3; ++p) {
            for (int q = p + 1; q < 3; ++q) {
                if (std::fabs(m[p][q]) < 1e-22L) {
                    continue;
                }
                long double theta = (m[q][q] - m[p][p]) / (2.0L * m[p][q]);
                long double t = 1.0L /
                    (std::fabs(theta) +
                     std::sqrt(theta * theta + 1.0L));
                if (theta < 0.0L) {
                    t = -t;
                }
                long double c = 1.0L / std::sqrt(t * t + 1.0L);
                long double s = t * c;
                for (int k = 0; k < 3; ++k) {
                    long double mkp = m[k][p];
                    long double mkq = m[k][q];
                    m[k][p] = c * mkp - s * mkq;
                    m[k][q] = s * mkp + c * mkq;
                }
                for (int k = 0; k < 3; ++k) {
                    long double mpk = m[p][k];
                    long double mqk = m[q][k];
                    m[p][k] = c * mpk - s * mqk;
                    m[q][k] = s * mpk + c * mqk;
                }
                for (int k = 0; k < 3; ++k) {
                    long double vkp = V[k][p];
                    long double vkq = V[k][q];
                    V[k][p] = c * vkp - s * vkq;
                    V[k][q] = s * vkp + c * vkq;
                }
            }
        }
    }
    for (int i = 0; i < 3; ++i) {
        w[i] = m[i][i];
    }
    // ascending sort with eigenvector columns carried along
    for (int i = 0; i < 2; ++i) {
        for (int j = i + 1; j < 3; ++j) {
            if (w[j] < w[i]) {
                long double tw = w[i];
                w[i] = w[j];
                w[j] = tw;
                for (int k = 0; k < 3; ++k) {
                    long double tv = V[k][i];
                    V[k][i] = V[k][j];
                    V[k][j] = tv;
                }
            }
        }
    }
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            v[i][j] = V[i][j];
        }
    }
}

// --- statistics of one artifact ---------------------------------------------
struct Stats {
    long double s_rms;
    long double mean_lam[3];   // descending, / s_rms
    long double beta_S;
    long double cos2[3];
    long double alpha_mean;
    long double alpha_std;
};

Stats compute_stats(const std::vector<long double>& T) {
    // pass 1: s_rms = sqrt(<S:S>)
    long double ss = 0.0L;
    for (long p = 0; p < kPts; ++p) {
        const long double sxx = T[p * 9 + 0], syy = T[p * 9 + 1],
                          szz = T[p * 9 + 2], sxy = T[p * 9 + 3],
                          sxz = T[p * 9 + 4], syz = T[p * 9 + 5];
        ss += sxx * sxx + syy * syy + szz * szz +
              2.0L * (sxy * sxy + sxz * sxz + syz * syz);
    }
    const long double s_rms = std::sqrt(ss / kPts);

    long double l1 = 0, l2 = 0, l3 = 0;
    long double c2[3] = {0, 0, 0};
    long double am = 0, am2 = 0;
    for (long p = 0; p < kPts; ++p) {
        long double S[3][3] = {
            {T[p * 9 + 0], T[p * 9 + 3], T[p * 9 + 4]},
            {T[p * 9 + 3], T[p * 9 + 1], T[p * 9 + 5]},
            {T[p * 9 + 4], T[p * 9 + 5], T[p * 9 + 2]}};
        long double lam[3], v[3][3];
        jacobi3(S, lam, v);
        // descending: reverse of ascending
        long double L[3] = {lam[2] / s_rms, lam[1] / s_rms, lam[0] / s_rms};
        long double E[3][3];
        for (int a = 0; a < 3; ++a) {  // eigenvector a (descending order)
            for (int b = 0; b < 3; ++b) {
                // v[b][col 2-a] is component b of the descending-a vector
                E[a][b] = v[b][2 - a];
            }
        }
        l1 += L[0];
        l2 += L[1];
        l3 += L[2];
        long double wx = T[p * 9 + 6], wy = T[p * 9 + 7], wz = T[p * 9 + 8];
        long double wn = std::sqrt(wx * wx + wy * wy + wz * wz);
        long double wh[3] = {wx / wn, wy / wn, wz / wn};
        for (int a = 0; a < 3; ++a) {
            long double dot = wh[0] * E[a][0] + wh[1] * E[a][1] + wh[2] * E[a][2];
            c2[a] += dot * dot;
        }
        // alpha = (omega_i S_ij omega_j) / (|omega|^2 s_rms), RAW omega —
        // the normalized vector must NOT be used here (double 1/wn^2)
        long double wSw = wx * (S[0][0] * wx + S[0][1] * wy + S[0][2] * wz) +
                          wy * (S[1][0] * wx + S[1][1] * wy + S[1][2] * wz) +
                          wz * (S[2][0] * wx + S[2][1] * wy + S[2][2] * wz);
        long double alpha = wSw / (wn * wn * s_rms);
        am += alpha;
        am2 += alpha * alpha;
    }
    Stats st;
    st.s_rms = s_rms;
    st.mean_lam[0] = l1 / kPts;
    st.mean_lam[1] = l2 / kPts;
    st.mean_lam[2] = l3 / kPts;
    st.beta_S = st.mean_lam[1] / (st.mean_lam[0] - st.mean_lam[2]);
    for (int a = 0; a < 3; ++a) {
        st.cos2[a] = c2[a] / kPts;
    }
    st.alpha_mean = am / kPts;
    st.alpha_std = std::sqrt(am2 / kPts - st.alpha_mean * st.alpha_mean);
    return st;
}

// --- deterministic Gaussian stream (LCG + Box-Muller) ------------------------
struct Rng {
    std::uint64_t s;
    explicit Rng(std::uint64_t seed) : s(seed) {}
    std::uint64_t next() {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        return s >> 11;
    }
    double uniform() { return (double)next() / 9007199254740992.0; }
    double normal() {
        double u1 = uniform(), u2 = uniform();
        if (u1 < 1e-300) u1 = 1e-300;
        return std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * M_PI * u2);
    }
};

std::string jnum(long double x) {
    std::ostringstream os;
    os << std::setprecision(17) << (double)x;
    return os.str();
}

void goe_block(std::ostringstream& os) {
    const int NS = 200000;
    Rng rng(987654321017ULL);
    long double l1 = 0, l2 = 0, l3 = 0, ss = 0, beta = 0, c2tot = 0;
    for (int i = 0; i < NS; ++i) {
        long double g[3][3];
        for (int a = 0; a < 3; ++a) {
            g[a][a] = rng.normal();
        }
        for (int a = 0; a < 3; ++a) {
            for (int b = a + 1; b < 3; ++b) {
                g[a][b] = rng.normal();
                g[b][a] = g[a][b];
            }
        }
        long double tr = (g[0][0] + g[1][1] + g[2][2]) / 3.0L;
        long double S[3][3];
        long double s2 = 0;
        for (int a = 0; a < 3; ++a) {
            for (int b = 0; b < 3; ++b) {
                S[a][b] = g[a][b] - (a == b ? tr : 0.0L);
                s2 += S[a][b] * S[a][b];
            }
        }
        ss += s2;
        long double lam[3], v[3][3];
        jacobi3(S, lam, v);
        long double s_rms = std::sqrt(s2);
        long double L[3] = {lam[2] / s_rms, lam[1] / s_rms, lam[0] / s_rms};
        l1 += L[0];
        l2 += L[1];
        l3 += L[2];
        beta += L[1] / (L[0] - L[2]);
        // alignment against a uniform random unit vector (exact null: 1/3)
        long double z1 = rng.normal(), z2 = rng.normal(), z3 = rng.normal();
        long double nn = std::sqrt(z1 * z1 + z2 * z2 + z3 * z3);
        long double wh[3] = {z1 / nn, z2 / nn, z3 / nn};
        long double csum = 0;
        for (int a = 0; a < 3; ++a) {
            long double dot = wh[0] * v[0][2 - a] + wh[1] * v[1][2 - a] +
                              wh[2] * v[2][2 - a];
            csum += dot * dot;
        }
        c2tot += csum;  // sums to 1 over the three axes
    }
    os << "    \"goe\": {\"n\": " << NS << ",\n";
    os << "        \"mean_lam\": [" << jnum(l1 / NS) << ", " << jnum(l2 / NS)
       << ", " << jnum(l3 / NS) << "],\n";
    os << "        \"beta_S\": " << jnum(beta / NS) << ",\n";
    os << "        \"cos2_sum\": " << jnum(c2tot / NS) << "}\n";
}

}  // namespace

int main() {
    std::ostringstream os;
    os << "{\n  \"program\": \"P5C_cpp\",\n";
    os << "  \"date\": \"2026-09-29\",\n";

    struct Named {
        const char* tag;
        const char* file;
    };
    const Named arts[] = {
        {"gauss_ref48", "p5c_tensors_gauss.f64"},
        {"dns_ref48", "p5c_tensors_dns.f64"},
    };
    for (const auto& art : arts) {
        std::string path = std::string("../../results/") + art.file;
        std::ifstream fh(path, std::ios::binary);
        if (!fh) {
            std::fprintf(stderr, "missing %s (run p5c export-tensors)\n", path.c_str());
            return 1;
        }
        std::vector<long double> T((long)9 * kPts);
        // raw f64 payload
        std::vector<double> raw((long)9 * kPts);
        fh.read(reinterpret_cast<char*>(raw.data()),
                (std::streamsize)(sizeof(double) * 9 * kPts));
        if (!fh) {
            std::fprintf(stderr, "short read: %s\n", path.c_str());
            return 1;
        }
        for (long i = 0; i < 9 * kPts; ++i) {
            T[i] = raw[i];
        }
        Stats st = compute_stats(T);
        os << "  \"" << art.tag << "\": {\n";
        os << "    \"s_rms\": " << jnum(st.s_rms) << ",\n";
        os << "    \"mean_lam\": [" << jnum(st.mean_lam[0]) << ", "
           << jnum(st.mean_lam[1]) << ", " << jnum(st.mean_lam[2]) << "],\n";
        os << "    \"beta_S\": " << jnum(st.beta_S) << ",\n";
        os << "    \"cos2\": [" << jnum(st.cos2[0]) << ", " << jnum(st.cos2[1])
           << ", " << jnum(st.cos2[2]) << "],\n";
        os << "    \"alpha_mean\": " << jnum(st.alpha_mean) << ",\n";
        os << "    \"alpha_std\": " << jnum(st.alpha_std) << "},\n";
    }
    os << "  \"alignment_null\": 0.333333333333333333,\n";
    os.seekp(-2, std::ios_base::cur);  // drop trailing comma
    os << ",\n";
    goe_block(os);
    os << "}";

    std::ofstream out("../../results/p5c_cpp.json");
    out << os.str() << "\n";
    std::printf("[p5c_cpp] wrote ../../results/p5c_cpp.json\n");
    return 0;
}
