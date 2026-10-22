"""Reference implementation tests, not tests of the private project."""
import copy
import tempfile
import unittest
from pathlib import Path

import demo


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = demo.generate_catalog(demo.DOMAIN_SELECTION, demo.SKILLS)

    def test_selection_loads_only_referenced_content(self):
        skills = {**demo.SKILLS, "unrelated": "Must not load"}
        catalog = demo.generate_catalog(demo.DOMAIN_SELECTION, skills)
        result = demo.load_domain("backend", catalog, demo.DOMAIN_SELECTION, skills)
        self.assertEqual({r["id"] for r in result["rules"]}, {"common", "backend", "security"})
        self.assertEqual({s["id"] for s in result["skills"]}, set(demo.SKILLS))
        self.assertNotIn("unrelated", str(result))

    def test_unsupported_does_not_load_any_modules(self):
        result = demo.load_domain("mobile", self.catalog, demo.DOMAIN_SELECTION, demo.SKILLS)
        self.assertEqual(result["outcome"], "unsupported")
        self.assertEqual(result["rules"], [])
        self.assertEqual(result["skills"], [])

    def test_missing_reference_refused_without_mutating_selection(self):
        selection = copy.deepcopy(demo.DOMAIN_SELECTION)
        selection["backend"]["skills"] = ("absent",)
        before = copy.deepcopy(selection)
        with self.assertRaises(demo.Refused):
            demo.generate_catalog(selection, demo.SKILLS)
        self.assertEqual(selection, before)

    def test_catalog_detects_content_staleness(self):
        changed = {**demo.SKILLS, "request-validation": "Changed description"}
        with self.assertRaises(demo.Refused):
            demo.load_domain("backend", self.catalog, demo.DOMAIN_SELECTION, changed)
        demo.check_catalog(demo.generate_catalog(demo.DOMAIN_SELECTION, changed), demo.DOMAIN_SELECTION, changed)

    def test_malformed_identifiers_refused(self):
        for value in ("../backend", "Backend", "", "backend/other", "a\n", 12):
            with self.subTest(value=value), self.assertRaises(demo.Refused):
                demo.load_domain(value, self.catalog, demo.DOMAIN_SELECTION, demo.SKILLS)


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="toolkit-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        demo.seed(self.root)
        catalog = demo.generate_catalog(demo.DOMAIN_SELECTION, demo.SKILLS)
        self.selected = demo.load_domain("backend", catalog, demo.DOMAIN_SELECTION, demo.SKILLS)
        self.transaction = demo.ConfigTransaction(self.root)

    def test_preview_apply_repeat_and_exact_restore(self):
        before = demo.snapshot(self.root)
        plan = self.transaction.preview(self.selected)
        self.assertEqual(demo.snapshot(self.root), before)
        self.assertEqual(len(plan), 2)
        self.transaction.apply(plan)
        after = demo.snapshot(self.root)
        for change in plan:
            self.assertEqual(after[demo.ADAPTERS[change.adapter]], change.after)
        self.assertEqual(after[demo.SENTINEL], before[demo.SENTINEL])
        repeat = demo.ConfigTransaction(self.root)
        self.assertEqual(repeat.preview(self.selected), ())
        repeat.apply(())
        self.assertEqual(demo.snapshot(self.root), after)
        self.transaction.rollback()
        self.assertEqual(demo.snapshot(self.root), before)

    def test_injected_failure_restores_existing_bytes(self):
        before = demo.snapshot(self.root)
        with self.assertRaises(RuntimeError):
            self.transaction.apply(self.transaction.preview(self.selected), fail_after=1)
        self.assertEqual(demo.snapshot(self.root), before)
        self.assertEqual(self.transaction.applied, [])

    def test_injected_failure_removes_new_managed_file(self):
        (self.root / demo.ADAPTERS["lumen"]).unlink()
        before = demo.snapshot(self.root)
        with self.assertRaises(RuntimeError):
            self.transaction.apply(self.transaction.preview(self.selected), fail_after=1)
        self.assertEqual(demo.snapshot(self.root), before)
        self.assertFalse((self.root / demo.ADAPTERS["lumen"]).exists())

    def test_drift_at_last_restore_target_prevents_all_restores(self):
        self.transaction.apply(self.transaction.preview(self.selected))
        (self.root / demo.ADAPTERS["lumen"]).write_bytes(b"External edit\x00\r\n")
        before = demo.snapshot(self.root)
        with self.assertRaises(demo.Refused):
            self.transaction.rollback()
        self.assertEqual(demo.snapshot(self.root), before)
        self.assertEqual(len(self.transaction.applied), 2)

    def test_preview_drift_refuses_before_first_write(self):
        plan = self.transaction.preview(self.selected)
        (self.root / demo.ADAPTERS["orbit"]).write_bytes(b"Changed since preview")
        before = demo.snapshot(self.root)
        with self.assertRaises(demo.Refused):
            self.transaction.apply(plan)
        self.assertEqual(demo.snapshot(self.root), before)
        self.assertEqual(self.transaction.applied, [])

    def test_duplicate_and_unknown_targets_refused_before_writes(self):
        plan = self.transaction.preview(self.selected)
        before = demo.snapshot(self.root)
        for invalid in ((plan[0], plan[0]), (demo.Change("unknown", None, b"x"),),
                        (demo.Change("../outside", None, b"x"),)):
            with self.subTest(plan=invalid), self.assertRaises(demo.Refused):
                self.transaction.apply(invalid)
            self.assertEqual(demo.snapshot(self.root), before)

    def test_directory_target_refused(self):
        target = self.root / demo.ADAPTERS["orbit"]
        target.unlink()
        target.mkdir()
        with self.assertRaises(demo.Refused):
            self.transaction.preview(self.selected)


class DemoTests(unittest.TestCase):
    def test_demo_checks_pass_and_evidence_is_stable(self):
        first = demo.run_demo()
        self.assertTrue(first["synthetic"])
        self.assertEqual(first["provider_calls"], 0)
        self.assertTrue(first["checks"])
        self.assertTrue(all(check["passed"] for check in first["checks"]))
        self.assertEqual(first, demo.run_demo())


if __name__ == "__main__":
    unittest.main()
