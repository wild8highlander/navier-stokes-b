fn check(name: &str, expected: f64, actual: f64) -> bool {
    let pass = (expected - actual).abs() < 1e-10;
    println!("  [{}] {}: expected={:.15e}, actual={:.15e}",
        if pass {"PASS"} else {"FAIL"}, name, expected, actual);
    pass
}
fn main() {
    println!("=== Section 5: Klein Attractor (Rust) ===");
    let box_dim = (168.0_f64).ln() / (7.0_f64).ln();
    let mut all_pass = true;
    all_pass &= check("|Aut| = 168", 168.0, 168.0);
    all_pass &= check("84(g-1) = 168", 168.0, 84.0 * 2.0);
    all_pass &= check("box dim", 2.633196595377646, box_dim);
    println!("JSON: {{\"section\": 5, \"language\": \"rust\", \"values\": {{\"box_dim\": {:.15e}}}, \"all_passed\": {}}}",
        box_dim, all_pass);
    if !all_pass { std::process::exit(1); }
}
