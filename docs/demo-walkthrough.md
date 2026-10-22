# Demo walkthrough

Run from the toolkit directory with Python 3.10+:

```sh
python3 demo.py
python3 demo.py --json
python3 -m unittest discover -s tests -v
python3 -m py_compile demo.py tests/test_demo.py
```

## 1. Select example context

The caller supplies `backend`. The selection contains `common`, `backend`, and `security` rule modules, with `request-validation` and `safe-config-change` skills. The demo reports the identifiers it actually loaded. Supplying the unsupported `mobile` domain returns no modules. Separate catalog cases deliberately introduce a missing skill reference and a stale catalog; each must be refused.

This lookup represents the result of an explicit domain decision. No task text is sent to a model, and no model response is simulated as real execution.

## 2. Preview and apply

A new temporary root contains two seeded configuration examples and an unmanaged note. Preview reads their bytes and builds a plan. The before and after-preview hashes must match. Apply changes both managed examples; the note's hash remains the same. Previewing and applying the same desired selection again produces zero changes. An explicit rollback then proves both original files are restored byte-for-byte.

## 3. Inject a failure

Another fresh scenario starts with one managed example absent. Apply creates it, then raises a deliberate exception after that first complete write. Rollback removes the newly created file and preserves the original file and unmanaged note. A further scenario starts with both managed files present and fails after the first replacement; its exact original bytes must be restored.

These are actual local example file operations. The exception is deliberately injected; it does not represent a production failure or a provider error.

## 4. Refuse recovery after drift

A final scenario applies both examples, then changes one managed file to represent an external edit. The edited file would be restored last. Rollback must detect the mismatch during prevalidation and refuse before restoring **either** file. Before-attempt and after-attempt hashes must match for the edit, the other managed file, and the unmanaged note.

All scenario directories live below a fresh `TemporaryDirectory` and are cleaned on exit. The only committed output is an explicit evidence artifact generated separately from the CLI output.

## Read the evidence

`--json` emits one object with `demo`, `synthetic`, `provider_calls`, `checks`, and `scenarios`. A nonzero exit status means at least one demonstration check failed. Each check includes state evidence rather than only a success label. The default walkthrough ends with the aggregate result.

To regenerate the stable artifact after a deliberate code change:

```sh
python3 demo.py --json > artifacts/demo-output.json
```

The output uses fixed logical filenames and content hashes. Random temporary paths, timestamps, and host details are excluded, so equivalent runs produce identical JSON.
