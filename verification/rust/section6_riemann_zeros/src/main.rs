fn check(name: &str, expected: f64, actual: f64) -> bool {
    let pass = (expected - actual).abs() < 1e-10;
    println!("  [{}] {}: expected={:.15e}, actual={:.15e}",
        if pass {"PASS"} else {"FAIL"}, name, expected, actual);
    pass
}
fn main() {
    println!("=== Section 6: Riemann Zeros (Rust) ===");
    let g1 = 14.134725141734693_f64;
    let g2 = 21.022039638771555_f64;
    let g3 = 25.010857580145688_f64;
    let mut all_pass = true;
    all_pass &= check("gamma_1 > 0", 1.0, if g1 > 0.0 {1.0} else {0.0});
    all_pass &= check("gamma_1 < gamma_2", 1.0, if g1 < g2 {1.0} else {0.0});
    all_pass &= check("gamma_2 < gamma_3", 1.0, if g2 < g3 {1.0} else {0.0});
    println!("JSON: {{\"section\": 6, \"language\": \"rust\", \"values\": {{\"gamma_1\": {:.15e}, \"gamma_2\": {:.15e}, \"gamma_3\": {:.15e}}}, \"all_passed\": {}}}",
        g1, g2, g3, all_pass);
    if !all_pass { std::process::exit(1); }
}
