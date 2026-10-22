#!/usr/bin/env python3
"""Synthetic, standard-library reference demo. No provider integration."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


class Refused(ValueError):
    """Input or recorded state does not satisfy the bounded demo contract."""


def identifier(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-z][a-z0-9-]{0,39}", value) is None:
        raise Refused("malformed identifier")
    return value


# Fictional teaching content; these are not real vendor configurations.
RULES = {
    "common": "Work within the supplied task scope.",
    "backend": "Validate request input and preserve state on failure.",
    "security": "Keep credentials out of output.",
}
SKILLS = {
    "request-validation": "Check the shape of fictional request input.",
    "safe-config-change": "Preview, apply, and recover a bounded file change.",
}
DOMAIN_SELECTION = {
    "backend": {
        "rules": ("common", "backend", "security"),
        "skills": ("request-validation", "safe-config-change"),
    },
}


def generate_catalog(selection: dict, skills: dict) -> dict:
    """Validate references and generate a deterministic example skill catalog."""
    for name in skills:
        identifier(name)
    rows = {}
    for domain, entry in sorted(selection.items()):
        identifier(domain)
        for name in entry["skills"]:
            identifier(name)
            if name not in skills:
                raise Refused("missing skill reference: " + name)
        rows[domain] = [
            {"id": name, "description": skills[name]}
            for name in entry["skills"]
        ]
    return rows


def check_catalog(catalog: dict, selection: dict, skills: dict) -> None:
    if catalog != generate_catalog(selection, skills):
        raise Refused("stale generated catalog")


def load_domain(domain: str, catalog: dict, selection: dict, skills: dict) -> dict:
    """Explicit domain lookup, not task classification or model execution."""
    identifier(domain)
    if domain not in selection:
        return {"outcome": "unsupported", "domain": domain, "rules": [], "skills": []}
    check_catalog(catalog, selection, skills)
    entry = selection[domain]
    for name in entry["rules"]:
        identifier(name)
        if name not in RULES:
            raise Refused("missing rule reference: " + name)
    return {
        "outcome": "selected",
        "domain": domain,
        "rules": [{"id": name, "content": RULES[name]} for name in entry["rules"]],
        "skills": [{"id": row["id"], "content": skills[row["id"]]} for row in catalog[domain]],
    }


ADAPTERS = {
    "lumen": "lumen-example.json",
    "orbit": "orbit-example.json",
}
SENTINEL = "unmanaged-note.txt"


def digest(content: bytes | None) -> str | None:
    return None if content is None else hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class Change:
    adapter: str
    before: bytes | None
    after: bytes


class ConfigTransaction:
    """In-memory journal over fixed filenames in a caller-created temporary root.

    This class is an internal teaching primitive, not a migration or sandbox API.
    Only run_demo creates its root. The CLI cannot choose a filesystem target.
    """

    def __init__(self, root: Path):
        self.root = root
        self.applied: list[Change] = []

    def path(self, adapter: str) -> Path:
        identifier(adapter)
        if adapter not in ADAPTERS:
            raise Refused("unknown example adapter")
        return self.root / ADAPTERS[adapter]

    def read(self, adapter: str) -> bytes | None:
        path = self.path(adapter)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise Refused("unsupported target type")
        return path.read_bytes() if path.exists() else None

    def preview(self, selected: dict) -> tuple[Change, ...]:
        # Construct all proposals before any write; rule content is illustrative.
        changes = []
        for adapter in ADAPTERS:
            content = {
                "schema": "fictional-toolkit-example-v1",
                "adapter": adapter,
                "rule_modules": [row["id"] for row in selected["rules"]],
                "skill_modules": [row["id"] for row in selected["skills"]],
            }
            after = (json.dumps(content, indent=2, sort_keys=True) + "\n").encode()
            before = self.read(adapter)
            if before != after:
                changes.append(Change(adapter, before, after))
        return tuple(changes)

    def apply(self, plan: tuple[Change, ...], fail_after: int | None = None) -> None:
        if self.applied:
            raise Refused("transaction already has an active journal")
        seen = set()
        # Validate every target before writing any of them.
        for change in plan:
            if change.adapter in seen:
                raise Refused("duplicate adapter in plan")
            seen.add(change.adapter)
            if self.read(change.adapter) != change.before:
                raise Refused("target changed since preview")
        try:
            for change in plan:
                # Record before writing so a partial write can also be recovered.
                self.applied.append(change)
                self.path(change.adapter).write_bytes(change.after)
                if fail_after == len(self.applied):
                    raise RuntimeError("deliberate synthetic write failure")
        except Exception:
            # A real failed write may leave partial bytes. Recovery below is only
            # automatic for the injected failure after a complete write.
            self.rollback()
            raise

    def rollback(self) -> None:
        # No restore begins until ALL managed targets match the recorded result.
        for change in self.applied:
            if self.read(change.adapter) != change.after:
                raise Refused("managed target drift; rollback refused")
        for change in reversed(self.applied):
            path = self.path(change.adapter)
            if change.before is None:
                path.unlink()
            else:
                path.write_bytes(change.before)
        self.applied.clear()


def seed(root: Path, both: bool = True) -> None:
    (root / ADAPTERS["orbit"]).write_bytes(b'{"example": "original orbit"}\r\n')
    if both:
        (root / ADAPTERS["lumen"]).write_bytes(b'{"example": "original lumen"}\n')
    (root / SENTINEL).write_bytes(b"Unmanaged teaching note.\n")


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(root.iterdir())}


def hashes(state: dict[str, bytes]) -> dict[str, str]:
    return {name: digest(content) for name, content in state.items()}


def run_demo() -> dict:
    checks = []
    scenarios = []

    def check(name: str, passed: bool, evidence: dict) -> None:
        checks.append({"id": name, "passed": bool(passed), "evidence": evidence})

    catalog = generate_catalog(DOMAIN_SELECTION, SKILLS)
    selected = load_domain("backend", catalog, DOMAIN_SELECTION, SKILLS)
    check("explicit-domain-selection", selected["outcome"] == "selected" and
          [row["id"] for row in selected["rules"]] == ["common", "backend", "security"] and
          [row["id"] for row in selected["skills"]] == list(SKILLS),
          {"domain": "backend", "rule_ids": [row["id"] for row in selected["rules"]],
           "skill_ids": [row["id"] for row in selected["skills"]]})
    unsupported = load_domain("mobile", catalog, DOMAIN_SELECTION, SKILLS)
    check("unsupported-domain", unsupported["outcome"] == "unsupported" and
          not unsupported["rules"] and not unsupported["skills"], unsupported)
    missing = {"backend": {"rules": ("common",), "skills": ("missing-example",)}}
    refused = False
    try:
        generate_catalog(missing, SKILLS)
    except Refused:
        refused = True
    check("missing-skill-reference", refused, {"outcome": "refused" if refused else "accepted"})
    stale = False
    try:
        check_catalog({}, DOMAIN_SELECTION, SKILLS)
    except Refused:
        stale = True
    check("stale-catalog", stale, {"outcome": "refused" if stale else "accepted"})
    scenarios.append({"id": "selection", "events": [
        "Caller supplies backend; deterministic example lookup loads three rules and two skills.",
        "Unsupported mobile loads nothing; missing references and stale catalogs are refused.",
    ]})

    with tempfile.TemporaryDirectory(prefix="toolkit-example-") as temporary:
        root = Path(temporary)
        success = root / "success"
        success.mkdir()
        seed(success)
        before = snapshot(success)
        transaction = ConfigTransaction(success)
        plan = transaction.preview(selected)
        check("preview-zero-mutations", snapshot(success) == before,
              {"before": hashes(before), "after_preview": hashes(snapshot(success)),
               "planned_adapters": [change.adapter for change in plan]})
        transaction.apply(plan)
        after = snapshot(success)
        check("apply-managed-only", len(plan) == 2 and all(
            after[ADAPTERS[c.adapter]] == c.after and c.before != c.after for c in plan
        ) and after[SENTINEL] == before[SENTINEL] and set(after) == set(before),
              {"before": hashes(before), "after_apply": hashes(after)})
        repeat = ConfigTransaction(success)
        repeat_plan = repeat.preview(selected)
        repeat.apply(repeat_plan)
        check("repeat-apply-no-op", not repeat_plan and snapshot(success) == after,
              {"planned_changes": len(repeat_plan), "state_preserved": snapshot(success) == after})
        # A successful explicit rollback demonstrates exact restoration of both files.
        transaction.rollback()
        check("successful-rollback", snapshot(success) == before,
              {"restored": hashes(snapshot(success)), "expected": hashes(before)})

        failure = root / "failure"
        failure.mkdir()
        seed(failure, both=False)
        original = snapshot(failure)
        failed_transaction = ConfigTransaction(failure)
        failed_plan = failed_transaction.preview(selected)
        injected = False
        try:
            failed_transaction.apply(failed_plan, fail_after=1)
        except RuntimeError:
            injected = True
        restored = snapshot(failure)
        check("injected-failure-rollback", injected and restored == original and
              ADAPTERS["lumen"] not in restored and not failed_transaction.applied,
              {"failure_after_writes": 1, "new_artifact_removed": ADAPTERS["lumen"] not in restored,
               "before": hashes(original), "after_rollback": hashes(restored)})
        # Also fail after replacing a pre-existing target, proving byte restoration.
        existing = root / "existing-failure"
        existing.mkdir()
        seed(existing)
        existing_before = snapshot(existing)
        existing_transaction = ConfigTransaction(existing)
        existing_failed = False
        try:
            existing_transaction.apply(existing_transaction.preview(selected), fail_after=1)
        except RuntimeError:
            existing_failed = True
        check("existing-file-failure-rollback", existing_failed and snapshot(existing) == existing_before,
              {"before": hashes(existing_before), "after_rollback": hashes(snapshot(existing))})

        drift = root / "drift"
        drift.mkdir()
        seed(drift)
        drift_transaction = ConfigTransaction(drift)
        drift_transaction.apply(drift_transaction.preview(selected))
        # Lumen would be restored last in reverse order; Orbit must stay untouched
        # even though it would otherwise be restored before drift is encountered.
        (drift / ADAPTERS["lumen"]).write_bytes(b"Synthetic external edit; preserve me.\n")
        drift_before = snapshot(drift)
        drift_refused = False
        try:
            drift_transaction.rollback()
        except Refused:
            drift_refused = True
        check("drift-refuses-before-restore", drift_refused and snapshot(drift) == drift_before,
              {"outcome": "refused" if drift_refused else "restored",
               "before_attempt": hashes(drift_before), "after_attempt": hashes(snapshot(drift))})
        scenarios.append({"id": "configuration", "events": [
            "Fresh temporary examples: preview leaves all bytes unchanged.",
            "Apply updates two managed examples and preserves the unmanaged note; repeat is a no-op.",
            "Injected failures restore original bytes and remove a newly created managed example.",
            "External managed-target edit makes rollback refuse before restoring any file.",
            "All temporary example directories are cleaned on exit.",
        ]})
    return {"demo": "agent-engineering-toolkit", "synthetic": True, "provider_calls": 0,
            "checks": checks, "scenarios": scenarios}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit stable synthetic evidence")
    arguments = parser.parse_args()
    result = run_demo()
    if arguments.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Agent Engineering Toolkit — synthetic reference walkthrough")
        print("No providers or vendor configuration are used.\n")
        for scenario in result["scenarios"]:
            for event in scenario["events"]:
                print("  " + event)
        print()
        for check in result["checks"]:
            print(("PASS " if check["passed"] else "FAIL ") + check["id"])
        print("\nFinal result: " + ("PASS" if all(c["passed"] for c in result["checks"]) else "FAIL"))
    return 0 if all(check["passed"] for check in result["checks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
