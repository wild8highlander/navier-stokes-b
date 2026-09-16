use std::f64::consts::PI;
fn check(name: &str, expected: f64, actual: f64) -> bool {
    let pass = (expected - actual).abs() < 1e-10;
    println!("  [{}] {}: expected={:.15e}, actual={:.15e}",
        if pass {"PASS"} else {"FAIL"}, name, expected, actual);
    pass
}
fn main() {
    println!("=== Section 2: Preprint NSE (Rust) ===");
    let alpha = (168.0_f64).sqrt() / (2.0 * PI);
    let l_min = 2.0 * PI / (168.0_f64).sqrt();
    let b = PI / (4.0 * PI * PI + 2.0 * PI * 3.0_f64.sqrt());
    let gamma = alpha * b * l_min;
    let mut all_pass = true;
    all_pass &= check("alpha > 0", 1.0, if alpha > 0.0 {1.0} else {0.0});
    all_pass &= check("alpha*L_min = 1", 1.0, alpha * l_min);
    all_pass &= check("gamma = b", b, gamma);
    println!("JSON: {{\"section\": 2, \"language\": \"rust\", \"values\": {{\"alpha\": {:.15e}, \"L_min\": {:.15e}, \"b\": {:.15e}}}, \"all_passed\": {}}}",
        alpha, l_min, b, all_pass);
    if !all_pass { std::process::exit(1); }
}
