# Pull Request Checklist

Thanks for improving **navier-stokes-b**. This is a proprietary repository
(IPL-RP-1.0) — by opening this PR you confirm that your contribution is offered to
the copyright holder under the same license (see `CONTRIBUTING.md`, §5).

## Summary

<!-- What does this PR change, and why? One or two sentences. -->

## Type of change

- [ ] 🐞 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (verification port, physics run, tooling)
- [ ] 📝 Documentation (README, site, papers, license text)
- [ ] 🔬 Verification matrix (formal or computational)
- [ ] 🔧 Build system / CI

## Reproducibility contract

Any change that touches **numbers** must keep them reproducible:

- [ ] `make verify-manifest` passes (or `MANIFEST.json` is regenerated for legit changes)
- [ ] `python -m pytest verification/tests/ -v` passes (toolchain-locked tests may skip)
- [ ] If a result changed: the JSON protocol in `data/results/` and the affected
      README/monograph text were updated **together**
- [ ] New directories ship an English `README.md`
- [ ] No Cyrillic was introduced into documentation (English-only policy)

## Screenshots / output (if visual or numerical)

<!-- Paste final verdict lines like `JSON: {...}` or [PASS]/[FAIL] tables. -->
