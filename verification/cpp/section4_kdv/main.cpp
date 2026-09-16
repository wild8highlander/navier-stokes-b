#include <cmath>
#include <iostream>
bool check(const std::string& n, double e, double a) {
    bool p = std::abs(e-a) < 1e-10;
    std::cout << "  [" << (p?"PASS":"FAIL") << "] " << n << "\n";
    return p;
}
int main() {
    std::cout << "=== Section 4: KdV (C++) ===\n";
    double c = 1.0;
    double u_peak = (c/2) * std::pow(1.0/std::cosh(0.5*std::sqrt(c)*0.0), 2);
    bool all = true;
    all &= check("soliton peak = c/2", c/2, u_peak);
    all &= check("c = 2*amplitude", c, 2*u_peak);
    std::cout << "JSON: {\"section\": 4, \"language\": \"cpp\", \"values\": {\"soliton_peak\": " << u_peak << "}, \"all_passed\": " << (all?"true":"false") << "}\n";
    return all ? 0 : 1;
}
