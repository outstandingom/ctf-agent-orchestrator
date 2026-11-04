# Code Audit — CTF Agent Orchestrator

**Scope:** source-level review of the current `main` snapshot and targeted remediation on `security/remove-exposed-credentials`.
**Review date:** 2026-11-04
**Status:** Partial audit. The code was inspected through GitHub file reads; the application and test suite were not executed in an isolated runtime. Findings below are source-based, not a penetration-test certificate.

## Executive summary

The repository has useful CTF building blocks (RSA weak-key attacks, symbolic solving, web probes, PCAP/forensics dispatch, and a model-driven tool selector), but it is **not safe to expose as an internet-facing autonomous agent**. The largest gap is not solver coverage: it is the control plane around the solvers. Several HTTP routes allow callers to execute arbitrary Python or shell commands without visible authentication or authorization in `server.py`.

The claims of an autonomous, integrated browser agent and a “5/5” benchmark should not be treated as proof of end-to-end capability. The checked-in benchmark constructs toy artifacts and known flags, includes a machine-specific Windows path, and has weak pass criteria. I did not find a Playwright browser tool in the inspected `OPENAI_TOOLS` / `execute_tool` paths, so README claims of browser MCP integration are not verified as an orchestrator feature.

## Findings by severity

### Critical — exposed credentials in tracked source and frontend
- Before remediation, the gateway credential appeared in README/setup scripts and was embedded in browser JavaScript in both dashboard copies. A browser-side bearer credential is public to every user who can load the page; it cannot be protected by minification or CORS.
- A browser extension token and a competition access key were also present in documentation.
- Removing the current copies does **not** remove the secrets from Git history, forks, cached copies, deployed frontend bundles, or logs.
- **Required external action:** revoke/rotate the gateway key and browser-extension token; revoke the competition key if it was real and still valid; inspect gateway logs for unexpected use. Do not reuse the old values.

### Critical — unauthenticated arbitrary code execution
- `server.py` exposes `POST /api/sandbox/run` and `POST /api/sandbox/parallel`, which execute caller-provided Python.
- `POST /api/wsl/exec` reaches a command runner that uses `bash -c`; `run_fullstack_terminal` uses `subprocess.run(..., shell=True)`.
- The inspected routes show no authentication/authorization dependency. CORS restrictions are not an access-control mechanism.
- A timeout is not a sandbox: the child process still has the account's filesystem/network permissions, and subprocess descendants/resource use need separate controls.
- **Required before any network exposure:** authentication, per-tool authorization, default-deny network binding, container/VM isolation, filesystem restrictions, CPU/memory/process quotas, command allowlists, and audit logging.

### High — arbitrary-target network access / SSRF
- The web fuzzer accepts a caller-supplied target URL; the socket probe accepts a host and port; CTFd operations accept a URL. These can potentially reach loopback, private network, link-local, or metadata endpoints if the service has network access.
- **Fix:** enforce an explicit authorized-target allowlist and resolve/validate IPs after DNS resolution; block private, loopback, link-local, multicast, and metadata ranges unless explicitly permitted for a local lab. Revalidate redirects and DNS changes.

### High — upload and file-path boundaries are not enforced at the API layer
- `/api/upload` copies an uploaded file to a temporary directory without a visible byte limit, extension/content validation, or cleanup lifecycle.
- `/api/forensics/scan` accepts an arbitrary local `file_path`; several tools accept paths for binaries and patch operations.
- **Fix:** accept uploaded bytes or server-issued artifact IDs instead of arbitrary paths; impose size limits, store in a dedicated non-executable directory, clean up, and confine all file operations to approved roots.

### High — weak TLS behavior in scanning code
- The dynamic web-probe path uses `verify=False` for HTTPS requests, disabling certificate verification. That can make results vulnerable to interception and can mask TLS findings.
- **Fix:** verify certificates by default; make any intentionally insecure lab mode explicit, opt-in, clearly labelled, and never use it for TLS validation.

### High — CTFd attachment classification crashes on non-empty files (fixed on this branch)
- On `main`, the entropy estimator calls `bit_length()` on a floating-point probability. Python floats do not provide that method, so attachment classification raises an exception for non-empty downloads.
- **Remediation on this branch:** calculate Shannon entropy using `math.log2` and `Counter`, avoiding the exception and repeated full-file scans.

### Medium — low-exponent RSA cube root loses precision on larger values (fixed on this branch)
- On `main`, the (e=3) attack uses `c ** (1/3)` floating-point arithmetic. This loses integer precision for sufficiently large ciphertexts and can miss valid textbook low-exponent recoveries.
- **Remediation on this branch:** use an integer-only cube-root routine and verify that the candidate's exact cube matches the ciphertext; a regression case was added to the engine test script.

### High — benchmark does not substantiate competition performance
- `scripts/benchmark_ctf.py` inserts the flag directly into a synthetic HTTP header and PNG metadata, then searches for the flag in raw bytes as a fallback. That tests string extraction more than PCAP parsing or steganography.
- The benchmark imports from a hardcoded `C:\Users\SGI\Downloads\ctf-agent-orchestrator` path, so it is not portable.
- `scripts/test_top01_engines.py` mostly checks whether the response contains the word `factored`; the CTFd test passes on many error-shaped responses, and the PWN test passes if it returns any expected-looking structure. These are smoke checks, not correctness tests.
- **Fix:** use portable paths; test real parser/solver outputs; assert recovered factors/plaintext/flag and negative cases; test malformed inputs and timeouts; run CI on clean Linux and Windows environments; report each case's actual result. Keep benchmark claims scoped to the cases actually tested.

### Medium — tool selection could omit the best RSA solver (fixed on this branch)
- On `main`, `select_relevant_tools()` adds `advanced_crypto_solver` for terms such as “wiener”, “factor”, or “lattice”, but the general cryptography keyword branch for “rsa” does not add it. A plain RSA challenge could therefore be routed without the specialized solver.
- **Remediation on this branch:** RSA/weak-key indicators now add `advanced_crypto_solver`; `scripts/test_tool_selector.py` adds regression tests for RSA, Wiener, PCAP, web, and fallback prompts.

### Medium — logs can capture sensitive tool inputs
- `execute_tool()` prints the entire tool input JSON. Tool inputs can include CTFd tokens, URLs, uploaded paths, or challenge material.
- **Fix:** redact credentials and cookies; log tool name, request ID, duration, status, and sanitized metadata instead.

### Medium — CORS wildcard configuration
- The original server configuration used wildcard origins with credentials enabled. CORS is not authentication, but wildcard origins unnecessarily widen browser access and make future cookie-auth designs dangerous.
- **Remediated on this branch:** CORS is disabled by default for same-origin local use; if configured, it uses explicit `CORS_ORIGINS` and credentials are disabled.

## Changes committed on `security/remove-exposed-credentials`

- Removed committed gateway/browser/competition credentials from the current documentation, setup defaults, and frontend code.
- Removed the direct browser-to-MCP fallback that exposed the gateway credential; repository listing now relies on the backend endpoint.
- Changed the documented manual Uvicorn command to bind to `127.0.0.1`.
- Restricted CORS to explicit configured origins and disabled credentialed CORS.
- Expanded `.gitignore` for local environment and runtime artifacts.
- Fixed RSA tool selection so plain RSA prompts include the advanced crypto solver; added tool-selector regression tests.
- Fixed CTFd attachment entropy calculation and low-exponent RSA cube-root precision; added a large-integer regression case.
- Replaced machine-specific Windows paths in the two reviewed benchmark/test scripts with paths relative to the script. (The benchmark's weak assertions and synthetic challenge design still need redesign.)
- Added security notes to the README.

These changes are **not merged into `main`**. They do not fix every critical issue listed above and do not make the service safe to deploy publicly.

## Validation still required

1. Rotate all previously exposed credentials and verify the old credentials no longer work.
2. Search all branches, tags, commit history, releases, deployed bundles, and logs for old credentials; rewrite history only if appropriate, then coordinate with collaborators.
3. Run secret scanning and dependency scanning.
4. Add API auth/authorization and sandbox isolation before exposing any dangerous endpoint.
5. Replace the benchmark's hardcoded path and weak assertions; run the suite on a clean machine.
6. Run `python -m unittest scripts.test_tool_selector` and `python scripts/test_top01_engines.py`; add tests for malformed solver inputs, URL/IP allowlists, upload limits, and authentication.
7. Verify the real TCS HackQuest rules before using any automation against the live competition.

## Bottom line

The repo is a useful **experimental CTF copilot**, not yet a verified autonomous competition-winning system. Improve security boundaries and the benchmark first; then measure solver accuracy on a diverse, held-out set of legitimate practice challenges.
