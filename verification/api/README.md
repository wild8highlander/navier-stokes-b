# `api/` — the verification REST API

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`api`**

![Service](https://img.shields.io/badge/FastAPI-009485?style=flat-square) ![Contract](https://img.shields.io/badge/same_PASS_%2F_JSON-FF8C00?style=flat-square) ![Sections](https://img.shields.io/badge/1%E2%80%937-2B579A?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The API exposes every section verifier over HTTP with the same PASS/JSON
contract the CLI uses — so monitoring jobs, CI pipelines and reviewers can
audit from any language without installing the toolchains.

## Endpoints

| Endpoint | Effect |
|---|---|
| `GET /api/sections` | the list of section ids (1–7) |
| `GET /api/verify/{section_id}` | **actually executes** the section's Python verifier in a subprocess and returns the parsed verdict plus the full stdout; unknown id → 404; verifier timeout → 504 |
| `GET /api/constant` | the constant `b` and its derived angles, recomputed on the fly |

A failing *verdict* is still a working *API*: the endpoint returns
`all_passed: false` with HTTP 200, because the audit question was answered.

## Run

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
# then: curl http://localhost:8000/api/verify/7
```

`start_api.sh` in [`../scripts/`](../scripts/README.md) wraps the same
launch; the docker image [`../docker/`](../docker/README.md) pins the
environment.

## Files

| File | Role |
|---|---|
| `server.py` | the FastAPI application (executes the real verifiers) |
| `requirements.txt` | fastapi + uvicorn |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
