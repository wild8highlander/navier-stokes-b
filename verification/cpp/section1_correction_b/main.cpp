#include <cmath>
#include <iostream>
#include <iomanip>
constexpr double PI = 3.14159265358979323846;
bool check(const std::string& n, double e, double a) {
    bool p = std::abs(e-a) < 1e-10;
    std::cout << "  [" << (p?"PASS":"FAIL") << "] " << n << "\n";
    return p;
}
int main() {
    std::cout << "=== Section 1: Correction b (C++) ===\n";
    double b = PI / (4*PI*PI + 2*PI*std::sqrt(3.0));
    double theta = std::asin(b);
    bool all = true;
    all &= check("b > 0", 1, b > 0 ? 1 : 0);
    all &= check("b < 1", 1, b < 1 ? 1 : 0);
    all &= check("sin(theta)=b", b, std::sin(theta));
    all &= check("cos^2+sin^2=1", 1.0, std::pow(std::cos(theta),2)+std::pow(std::sin(theta),2));
    std::cout << "JSON: {\"section\": 1, \"language\": \"cpp\", \"values\": {\"b\": " << b << "}, \"all_passed\": " << (all?"true":"false") << "}\n";
    return all ? 0 : 1;
}
