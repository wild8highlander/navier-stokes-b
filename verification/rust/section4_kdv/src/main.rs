fn check(name: &str, expected: f64, actual: f64) -> bool {
    let pass = (expected - actual).abs() < 1e-10;
    println!("  [{}] {}: expected={:.15e}, actual={:.15e}",
        if pass {"PASS"} else {"FAIL"}, name, expected, actual);
    pass
}
fn main() {
    println!("=== Section 4: KdV (Rust) ===");
    let c = 1.0_f64;
    let u_peak = (c / 2.0) * (1.0 / (0.5 * c.sqrt() * 0.0).cosh()).powi(2);
    let mut all_pass = true;
    all_pass &= check("soliton peak = c/2", c / 2.0, u_peak);
    all_pass &= check("c = 2*amplitude", c, 2.0 * u_peak);
    println!("JSON: {{\"section\": 4, \"language\": \"rust\", \"values\": {{\"soliton_peak\": {:.15e}}}, \"all_passed\": {}}}",
        u_peak, all_pass);
    if !all_pass { std::process::exit(1); }
}
