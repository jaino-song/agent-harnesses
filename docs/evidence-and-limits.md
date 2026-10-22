# Evidence and limits

This package is freshly authored public example code with fictional inputs. It contains no copied private implementation or usable vendor installation configuration.

| Evidence category | What it supports | What it does not establish |
| --- | --- | --- |
| Inspected private source and documentation | Common/domain rule layering, instruction-guided selection, catalog-first skill loading, code-enforced reference and staleness checks, provider-specific adapters, preview/apply/recovery, and human-reviewed improvement proposals | A current production deployment or execution of the private test suite |
| This public demo's executed checks | Explicit example lookup, catalog refusal cases, temporary-file preview/apply, idempotency, injected-failure restoration, and drift-preserving refusal | Parity with the private migration engine or compatibility with real runtimes |
| This public demo's unit tests | Selection isolation, malformed identifier refusal, stale metadata detection, plan prevalidation, exact state preservation, and repeatable synthetic evidence | Private source implementation test results or end-to-end provider behavior |
| Generated JSON artifact | Stable output from a local execution of the reference demo | Operational telemetry, real customer data, or business impact |

Private test definitions covering dry-run, idempotency, conflicts, and drift-preserving recovery were inspected as architectural grounding. That private suite was **not run** for this package. The public tests are separate and exercise only this reference implementation.

## Boundaries

- Domain selection is explicit deterministic example lookup. The private approach is instruction-guided; neither is presented as an autonomous classifier here.
- No LLM, provider, remote endpoint, subprocess, shell, credential, or environment-variable setup participates in the demo. `provider_calls: 0` describes this code path, not a measurement of an external platform.
- All file scenarios use disposable temporary directories. The transaction helper is not a general sandbox or host migration API.
- Recovery uses an in-memory journal and deliberately injected failures after complete writes. Durable crash recovery, disk-write fault tolerance, lock concurrency, filesystem race protection, and symlink migration are not implemented.
- Drift refusal preserves the state observed at the attempted rollback. It does not resolve conflicts, retry a concurrent edit, or offer a force restore.
- Fictional adapters share a small example schema. No real vendor configuration or installation is performed.
- Human-reviewed improvement proposals are described, not executed. There is no session collection, self-modification, deployment, or publishing feature.
- No measured token savings, productivity gains, reliability rates, production usage, or full private-project parity are claimed.

A real integration would need an agreed runtime schema and ownership model, durable journals and recovery rules, locking and concurrency tests, provider-specific integration tests, and review of the deployment environment before touching operational configuration.
