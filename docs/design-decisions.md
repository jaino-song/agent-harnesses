# Design decisions

| Choice | Reason | Tradeoff |
| --- | --- | --- |
| Explicit domain argument in the Python API | Makes selective loading reproducible and honest about instruction-guided classification | No natural-language task classifier |
| Validate catalog before supported-domain loading | Prevents a missing reference or stale description from silently selecting incomplete context | Catalog metadata is a tiny in-memory example |
| Return unsupported with empty module lists | Makes the boundary visible without guessing another domain | Callers must supply a supported domain |
| Fixed fictional adapter filenames | Keeps the example small and output understandable | Cannot configure real runtimes |
| Compare bytes and report SHA-256 hashes | Preserves exact prior content, including line endings, while making state comparisons readable | Hashes describe example file state, not provider execution |
| Validate all targets before restoration | Preserves externally edited state and prevents an early restore before later drift is discovered | A refusal requires a person to reconcile the edit; no force option |
| In-memory transaction journal | Makes the recovery algorithm easy to inspect | No durable crash recovery or cross-process lock |
| Standard library only | Makes the sample runnable without setup or credentials | Deliberately limited integration surface |

The unsupported-domain path returns before catalog checking because it loads no content. Supported-domain loading requires a catalog that matches the whole generated example table. Missing references are refused during catalog generation, even if another domain would not need them.

The CLI owns creation of every temporary scenario root. There is no CLI path argument, subprocess execution, network call, environment configuration, or vendor installation step. The internal transaction class accepts a path so tests can exercise it inside their own temporary directories; it is a teaching primitive and does not establish a security sandbox. It refuses symlink and non-file targets but does not implement symlink migration or defend against filesystem races.

Automatic recovery is demonstrated only for an injected exception after a complete file write. If actual I/O fails during a write or restore, rollback can fail or refuse. That limitation is preserved instead of presenting an in-memory example as a complete migration engine.

Human review is part of the described improvement lifecycle. The public sample intentionally has no autonomous instruction rewriting, approval inference, or deployment action. Real adoption would first need concrete target schemas, durable recovery, concurrency semantics, and environment-specific validation.
