// p5d_qr.cpp — P5-D C++ verification track (long double core).
//
// Mirrors the statistics part of code/python/p5d_qr_ensemble.py on the SAME
// artifact: the raw f64 point-tensor dump results/p5d_tensors_dns.f64
// (layout: point-major (n, n, n, 9), channels
//  [Sxx, Syy, Szz, Sxy, Sxz, Syz, wx, wy, wz], written by run_case_ens).
// Recomputes, in long double:
//   (1) the P5-C scalar block — s_rms, mean strain eigenvalues (long-double
//       Jacobi), beta_S, <cos^2 theta_i>, alpha mean/std;
//   (2) the P5-D Q-R invariants of the velocity gradient A = S + W with
//       W_ij = -eps_ijk omega_k / 2:
//         Q = 1/4 |omega|^2 - 1/2 S:S = -1/2 tr(A^2),  R = -det A,
//         q = Q/<S:S>, r = R/<S:S>^{3/2},  D_S = (r/2)^2 + (q/3)^3,
//       and the same scalar set as qr_stats (masses, tail proximity with the
//       q < -0.5 restriction, tail population fraction).
// Agreement target with the Python track: 1e-10 (relative).
// Output: results/p5d_cpp.json
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr int kN = 64;
constexpr long kPts = (long)kN * kN * kN;

// --- Jacobi eigen-decomposition of a symmetric 3x3 matrix -------------------
// (identical convention to numpy.linalg.eigh: ascending eigenvalues,
//  eigenvectors as columns of v)
void jacobi3(const long double a[3][3], long double w[3], long double v[3][3]) {
    long double m[3][3];
    long double V[3][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) m[i][j] = a[i][j];
    for (int sweep = 0; sweep < 64; ++sweep) {
        long double off = 0.0L;
        for (int p = 0; p < 3; ++p)
            for (int q = p + 1; q < 3; ++q) off += m[p][q] * m[p][q];
        if (off < 1e-34L) break;
        for (int p = 0; p < 3; ++p) {
            for (int q = p + 1; q < 3; ++q) {
                if (std::fabs(m[p][q]) < 1e-22L) continue;
                long double theta = (m[q][q] - m[p][p]) / (2.0L * m[p][q]);
                long double t = 1.0L /
                    (std::fabs(theta) + std::sqrt(theta * theta + 1.0L));
                if (theta < 0.0L) t = -t;
                long double c = 1.0L / std::sqrt(t * t + 1.0L);
                long double s = t * c;
                for (int k = 0; k < 3; ++k) {
                    long double mkp = m[k][p], mkq = m[k][q];
                    m[k][p] = c * mkp - s * mkq;
                    m[k][q] = s * mkp + c * mkq;
                }
                for (int k = 0; k < 3; ++k) {
                    long double mpk = m[p][k], mqk = m[q][k];
                    m[p][k] = c * mpk - s * mqk;
                    m[q][k] = s * mpk + c * mqk;
                }
                for (int k = 0; k < 3; ++k) {
                    long double vkp = V[k][p], vkq = V[k][q];
                    V[k][p] = c * vkp - s * vkq;
                    V[k][q] = s * vkp + c * vkq;
                }
            }
        }
    }
    for (int i = 0; i < 3; ++i) w[i] = m[i][i];
    for (int i = 0; i < 2; ++i) {
        for (int j = i + 1; j < 3; ++j) {
            if (w[j] < w[i]) {
                long double tw = w[i]; w[i] = w[j]; w[j] = tw;
                for (int k = 0; k < 3; ++k) {
                    long double tv = V[k][i];
                    V[k][i] = V[k][j];
                    V[k][j] = tv;
                }
            }
        }
    }
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) v[i][j] = V[i][j];
}

struct Qr {
    long double s_rms;
    long double mean_lam[3];
    long double beta_S;
    long double cos2[3];
    long double alpha_mean, alpha_std;
    // Q-R block
    long double q_mean, r_mean, r_std;
    long double p_q_pos, p_qneg_node, p_qneg_focal;
    long double p_qp_rn, p_qp_rp, p_qn_rn, p_qn_rp;
    long double tail_rel, tail_pop;
};

Qr compute_all(const std::vector<long double>& T) {
    // pass 1: s_rms = sqrt(<S:S>)
    long double ss = 0.0L;
    for (long p = 0; p < kPts; ++p) {
        const long double sxx = T[p * 9 + 0], syy = T[p * 9 + 1],
                          szz = T[p * 9 + 2], sxy = T[p * 9 + 3],
                          sxz = T[p * 9 + 4], syz = T[p * 9 + 5];
        ss += sxx * sxx + syy * syy + szz * szz +
              2.0L * (sxy * sxy + sxz * sxz + syz * syz);
    }
    const long double s2m = ss / kPts;                 // <S:S>
    const long double s_rms = std::sqrt(s2m);
    const long double s2m_15 = s2m * std::sqrt(s2m);   // <S:S>^{3/2}

    long double l1 = 0, l2 = 0, l3 = 0;
    long double c2[3] = {0, 0, 0};
    long double am = 0, am2 = 0;
    long double qm = 0, rm = 0, rm2 = 0;
    long double n_qpos = 0, n_node = 0, n_focal = 0;
    long double n_qp_rn = 0, n_qp_rp = 0, n_qn_rn = 0, n_qn_rp = 0;
    long double tail_sum = 0, tail_cnt = 0, tail_pop = 0;
    for (long p = 0; p < kPts; ++p) {
        const long double sxx = T[p * 9 + 0], syy = T[p * 9 + 1],
                          szz = T[p * 9 + 2], sxy = T[p * 9 + 3],
                          sxz = T[p * 9 + 4], syz = T[p * 9 + 5];
        long double S[3][3] = {
            {sxx, sxy, sxz},
            {sxy, syy, syz},
            {sxz, syz, szz}};
        long double lam[3], v[3][3];
        jacobi3(S, lam, v);
        long double L[3] = {lam[2] / s_rms, lam[1] / s_rms, lam[0] / s_rms};
        long double E[3][3];
        for (int a = 0; a < 3; ++a)
            for (int b = 0; b < 3; ++b) E[a][b] = v[b][2 - a];
        l1 += L[0]; l2 += L[1]; l3 += L[2];
        const long double wx = T[p * 9 + 6], wy = T[p * 9 + 7], wz = T[p * 9 + 8];
        const long double wn = std::sqrt(wx * wx + wy * wy + wz * wz);
        long double wh[3] = {wx / wn, wy / wn, wz / wn};
        for (int a = 0; a < 3; ++a) {
            long double dot = wh[0] * E[a][0] + wh[1] * E[a][1] + wh[2] * E[a][2];
            c2[a] += dot * dot;
        }
        const long double wSw =
            wx * (S[0][0] * wx + S[0][1] * wy + S[0][2] * wz) +
            wy * (S[1][0] * wx + S[1][1] * wy + S[1][2] * wz) +
            wz * (S[2][0] * wx + S[2][1] * wy + S[2][2] * wz);
        const long double alpha = wSw / (wn * wn * s_rms);
        am += alpha;
        am2 += alpha * alpha;
        // ---- velocity gradient A = S + W, W_ij = -eps_ijk w_k / 2 ----
        const long double A11 = sxx,          A12 = sxy - 0.5L * wz,
                          A13 = sxz + 0.5L * wy,
                          A21 = sxy + 0.5L * wz, A22 = syy,
                          A23 = syz - 0.5L * wx,
                          A31 = sxz - 0.5L * wy, A32 = syz + 0.5L * wx,
                          A33 = szz;
        const long double det = A11 * (A22 * A33 - A23 * A32) -
                                A12 * (A21 * A33 - A23 * A31) +
                                A13 * (A21 * A32 - A22 * A31);
        const long double w2 = wx * wx + wy * wy + wz * wz;
        const long double S2 = sxx * sxx + syy * syy + szz * szz +
                               2.0L * (sxy * sxy + sxz * sxz + syz * syz);
        const long double q = (0.25L * w2 - 0.5L * S2) / s2m;
        const long double r = -det / s2m_15;
        qm += q; rm += r; rm2 += r * r;
        const long double d_s = (r / 2.0L) * (r / 2.0L) +
                                (q / 3.0L) * (q / 3.0L) * (q / 3.0L);
        if (q > 0.0L) { n_qpos += 1.0L; }
        if (q < 0.0L) {
            if (d_s >= 0.0L) { n_node += 1.0L; } else { n_focal += 1.0L; }
        }
        if (q > 0.0L && r < 0.0L) n_qp_rn += 1.0L;
        if (q > 0.0L && r > 0.0L) n_qp_rp += 1.0L;
        if (q < 0.0L && r < 0.0L) n_qn_rn += 1.0L;
        if (q < 0.0L && r > 0.0L) n_qn_rp += 1.0L;
        if (q < -0.5L) {
            const long double x = 27.0L * r * r / (-4.0L * q * q * q);
            tail_sum += x;
            tail_cnt += 1.0L;
            if (x >= 0.9L) tail_pop += 1.0L;
        }
    }
    Qr st;
    st.s_rms = s_rms;
    st.mean_lam[0] = l1 / kPts;
    st.mean_lam[1] = l2 / kPts;
    st.mean_lam[2] = l3 / kPts;
    st.beta_S = st.mean_lam[1] / (st.mean_lam[0] - st.mean_lam[2]);
    for (int a = 0; a < 3; ++a) st.cos2[a] = c2[a] / kPts;
    st.alpha_mean = am / kPts;
    st.alpha_std = std::sqrt(am2 / kPts - st.alpha_mean * st.alpha_mean);
    st.q_mean = qm / kPts;
    st.r_mean = rm / kPts;
    st.r_std = std::sqrt(rm2 / kPts - st.r_mean * st.r_mean);
    const long double kp = (long double)kPts;
    st.p_q_pos = n_qpos / kp;
    st.p_qneg_node = n_node / kp;
    st.p_qneg_focal = n_focal / kp;
    st.p_qp_rn = n_qp_rn / kp;
    st.p_qp_rp = n_qp_rp / kp;
    st.p_qn_rn = n_qn_rn / kp;
    st.p_qn_rp = n_qn_rp / kp;
    st.tail_rel = tail_sum / tail_cnt;
    st.tail_pop = tail_pop / tail_cnt;
    return st;
}

std::string jnum(long double x) {
    std::ostringstream os;
    os << std::setprecision(17) << (double)x;
    return os.str();
}

}  // namespace

int main() {
    std::string path = "../../results/p5d_tensors_dns.f64";
    std::ifstream fh(path, std::ios::binary);
    if (!fh) {
        std::fprintf(stderr, "missing %s (run p5d dns with dump_tensors)\n", path.c_str());
        return 1;
    }
    std::vector<double> raw((long)9 * kPts);
    fh.read(reinterpret_cast<char*>(raw.data()),
            (std::streamsize)(sizeof(double) * 9 * kPts));
    if (!fh) {
        std::fprintf(stderr, "short read: %s\n", path.c_str());
        return 1;
    }
    std::vector<long double> T((long)9 * kPts);
    for (long i = 0; i < 9 * kPts; ++i) T[i] = raw[i];

    Qr st = compute_all(T);
    std::ostringstream os;
    os << "{\n  \"program\": \"P5D_cpp\",\n  \"date\": \"2026-09-30\",\n";
    os << "  \"artifact\": \"p5d_tensors_dns.f64\",\n";
    os << "  \"s_rms\": " << jnum(st.s_rms) << ",\n";
    os << "  \"mean_lam\": [" << jnum(st.mean_lam[0]) << ", "
       << jnum(st.mean_lam[1]) << ", " << jnum(st.mean_lam[2]) << "],\n";
    os << "  \"beta_S\": " << jnum(st.beta_S) << ",\n";
    os << "  \"cos2\": [" << jnum(st.cos2[0]) << ", " << jnum(st.cos2[1])
       << ", " << jnum(st.cos2[2]) << "],\n";
    os << "  \"alpha_mean\": " << jnum(st.alpha_mean) << ",\n";
    os << "  \"alpha_std\": " << jnum(st.alpha_std) << ",\n";
    os << "  \"qr\": {\n";
    os << "    \"q_mean_norm\": " << jnum(st.q_mean) << ",\n";
    os << "    \"r_mean_norm\": " << jnum(st.r_mean) << ",\n";
    os << "    \"r_std_norm\": " << jnum(st.r_std) << ",\n";
    os << "    \"p_q_pos\": " << jnum(st.p_q_pos) << ",\n";
    os << "    \"p_qneg_node\": " << jnum(st.p_qneg_node) << ",\n";
    os << "    \"p_qneg_focal\": " << jnum(st.p_qneg_focal) << ",\n";
    os << "    \"p_qp_rn\": " << jnum(st.p_qp_rn) << ",\n";
    os << "    \"p_qp_rp\": " << jnum(st.p_qp_rp) << ",\n";
    os << "    \"p_qn_rn\": " << jnum(st.p_qn_rn) << ",\n";
    os << "    \"p_qn_rp\": " << jnum(st.p_qn_rp) << ",\n";
    os << "    \"tail_rel_mean\": " << jnum(st.tail_rel) << ",\n";
    os << "    \"tail_pop_frac\": " << jnum(st.tail_pop) << "}\n";
    os << "}";

    std::ofstream out("../../results/p5d_cpp.json");
    out << os.str() << "\n";
    std::printf("[p5d_cpp] wrote ../../results/p5d_cpp.json\n");
    return 0;
}
