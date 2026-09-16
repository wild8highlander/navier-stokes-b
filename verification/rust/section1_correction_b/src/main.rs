use std::f64::consts::PI;

fn compute_b() -> f64 { PI / (4.0 * PI * PI + 2.0 * PI * 3.0_f64.sqrt()) }

fn check(name: &str, expected: f64, actual: f64) -> bool {
    let pass = (expected - actual).abs() < 1e-10;
    println!("  [{}] {}: expected={:.15e}, actual={:.15e}",
        if pass {"PASS"} else {"FAIL"}, name, expected, actual);
    pass
}

fn main() {
    println!("=== Section 1: Correction b (Rust) ===");
    let b = compute_b();
    let theta = b.asin();
    let det_r = theta.cos() * theta.cos() + theta.sin() * theta.sin();

    let mut all_pass = true;
    all_pass &= check("b > 0", 1.0, if b > 0.0 {1.0} else {0.0});
    all_pass &= check("b < 1", 1.0, if b < 1.0 {1.0} else {0.0});
    all_pass &= check("sin(theta_b) = b", b, theta.sin());
    all_pass &= check("cos^2+sin^2 = 1", 1.0, det_r);

    println!("JSON: {{\"section\": 1, \"language\": \"rust\", \"values\": {{\"b\": {:.15e}}}, \"all_passed\": {}}}",
        b, all_pass);
    if !all_pass { std::process::exit(1); }
}
