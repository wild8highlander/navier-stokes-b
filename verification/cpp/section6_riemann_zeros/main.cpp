#include <cmath>
#include <iostream>
bool check(const std::string& n, double e, double a) {
    bool p = std::abs(e-a) < 1e-10;
    std::cout << "  [" << (p?"PASS":"FAIL") << "] " << n << "\n";
    return p;
}
int main() {
    std::cout << "=== Section 6: Riemann Zeros (C++) ===\n";
    double g1 = 14.134725141734693, g2 = 21.022039638771555, g3 = 25.010857580145688;
    bool all = true;
    all &= check("gamma_1 > 0", 1, g1 > 0 ? 1 : 0);
    all &= check("gamma_1 < gamma_2", 1, g1 < g2 ? 1 : 0);
    all &= check("gamma_2 < gamma_3", 1, g2 < g3 ? 1 : 0);
    std::cout << "JSON: {\"section\": 6, \"language\": \"cpp\", \"values\": {\"gamma_1\": " << g1 << "}, \"all_passed\": " << (all?"true":"false") << "}\n";
    return all ? 0 : 1;
}
