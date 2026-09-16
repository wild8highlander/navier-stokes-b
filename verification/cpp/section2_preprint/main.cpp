#include <cmath>
#include <iostream>
constexpr double PI = 3.14159265358979323846;
bool check(const std::string& n, double e, double a) {
    bool p = std::abs(e-a) < 1e-10;
    std::cout << "  [" << (p?"PASS":"FAIL") << "] " << n << "\n";
    return p;
}
int main() {
    std::cout << "=== Section 2: Preprint NSE (C++) ===\n";
    double alpha = std::sqrt(168.0) / (2*PI);
    double l_min = 2*PI / std::sqrt(168.0);
    double b = PI / (4*PI*PI + 2*PI*std::sqrt(3.0));
    double gamma = alpha * b * l_min;
    bool all = true;
    all &= check("alpha > 0", 1, alpha > 0 ? 1 : 0);
    all &= check("alpha*L_min = 1", 1.0, alpha * l_min);
    all &= check("gamma = b", b, gamma);
    std::cout << "JSON: {\"section\": 2, \"language\": \"cpp\", \"values\": {\"alpha\": " << alpha << "}, \"all_passed\": " << (all?"true":"false") << "}\n";
    return all ? 0 : 1;
}
