# `docker/rust/` — the Rust stable (edition 2021) image

> **Navigation:** [repository root](../../../README.md) › [verification](../../verification/README.md) › [docker](../README.md) › **`rust`**

![Image](https://img.shields.io/badge/rust-2B579A?style=flat-square) ![Toolchain](https://img.shields.io/badge/Rust_stable_(edition_2021)-informational?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The pinned environment for the rust tier of the verification matrix. The
image installs exactly the toolchain the framework expects — nothing more,
so the build is the environment statement.

```bash
docker build -t nsb-verify-rust .
docker run --rm -v "$PWD/../../..:/repo" -w /repo nsb-verify-rust bash -lc "cargo build --release"
```

Inside the container, the working command for this tier is:

```bash
cargo build --release
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
