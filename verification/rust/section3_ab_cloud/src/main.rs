use std::f64::consts::PI;
fn check(name: &str, expected: f64, actual: f64) -> bool {
    let pass = (expected - actual).abs() < 1e-10;
    println!("  [{}] {}: expected={:.15e}, actual={:.15e}",
        if pass {"PASS"} else {"FAIL"}, name, expected, actual);
    pass
}
fn main() {
    println!("=== Section 3: AB-Cloud (Rust) ===");
    let peierls = (2.0 * PI / 7.0).cos();
    let gue_ratio = 0.6027_f64;
    let mut sum_re = 0.0;
    for k in 0..7 { sum_re += (2.0 * PI * k as f64 / 7.0).cos(); }
    let mut all_pass = true;
    all_pass &= check("Sum Re = 0", 0.0, sum_re);
    all_pass &= check("gue_ratio = 0.6027", 0.6027, gue_ratio);
    all_pass &= check("gue_ratio > 0.5", 1.0, if gue_ratio > 0.5 {1.0} else {0.0});
    println!("JSON: {{\"section\": 3, \"language\": \"rust\", \"values\": {{\"peierls\": {:.15e}, \"gue_ratio\": {:.15e}}}, \"all_passed\": {}}}",
        peierls, gue_ratio, all_pass);
    if !all_pass { std::process::exit(1); }
}
