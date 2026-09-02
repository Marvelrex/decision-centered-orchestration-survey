import json
import re
import unittest
from copy import deepcopy
from pathlib import Path

import analyze_prisma_core as core
import build_prisma_reconstruction as reconstruction
import build_prisma_screening_ledger as ledger


class PrismaScreeningLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = ledger.build_ledger_package()

    def test_frozen_counts_reconcile(self):
        summary = self.package["summary"]
        self.assertEqual(summary["records_identified"], 4986)
        self.assertEqual(summary["duplicate_records_removed"], 512)
        self.assertEqual(summary["superseded_preprint_records_removed"], 10)
        self.assertEqual(summary["records_for_screening"], 4464)
        self.assertEqual(
            summary["records_identified"],
            summary["duplicate_records_removed"]
            + summary["superseded_preprint_records_removed"]
            + summary["records_for_screening"],
        )

    def test_every_raw_record_is_accounted_for_once(self):
        raw_ids = {
            record["record_id"]
            for record in (
                core.load_acm()
                + core.load_ieee()
                + core.load_scopus()
                + core.load_dblp()
                + core.load_arxiv()
            )
        }
        retained_ids = {
            row["representative_record_id"] for row in self.package["records"]
        }
        removed_ids = {
            row["record_id"] for row in self.package["pre_screen_removals"]
        }
        self.assertEqual(len(self.package["records"]), 4464)
        self.assertEqual(len(removed_ids), 522)
        self.assertFalse(retained_ids & removed_ids)
        self.assertEqual(raw_ids, retained_ids | removed_ids)

    def test_screening_ids_and_representatives_are_unique(self):
        rows = self.package["records"]
        self.assertEqual(
            len({row["screening_id"] for row in rows}),
            len(rows),
        )
        self.assertEqual(
            len({row["representative_record_id"] for row in rows}),
            len(rows),
        )
        self.assertTrue(all(row["title"] for row in rows))
        self.assertTrue(all(row["member_record_ids"] for row in rows))

    def test_reviewed_duplicate_decisions_are_applied(self):
        removals = self.package["pre_screen_removals"]
        counts = {}
        for row in removals:
            counts[row["removal_type"]] = counts.get(row["removal_type"], 0) + 1
        self.assertEqual(counts["duplicate"], 512)
        self.assertEqual(counts["superseded preprint"], 10)
        duplicate_group_ids = {
            row["review_group_id"]
            for row in removals
            if row["removal_type"] == "duplicate"
        }
        self.assertTrue(core.CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS <= duplicate_group_ids)
        self.assertFalse(core.KEEP_SEPARATE_NO_DOI_GROUP_IDS & duplicate_group_ids)

    def test_suggestions_are_controlled_and_not_final_decisions(self):
        codebook = self.package["codebook"]
        suggestion_values = set(codebook["automation_suggestions"])
        reason_values = set(codebook["title_abstract_exclusion_reasons"])
        for row in self.package["records"]:
            self.assertIn(row["automation_suggestion"], suggestion_values)
            if row["suggested_primary_reason"]:
                self.assertIn(row["suggested_primary_reason"], reason_values)
            self.assertEqual(row["reviewer_title_abstract_decision"], "")
            self.assertEqual(row["reviewer_exclusion_reason"], "")
            self.assertEqual(row["reviewer_notes"], "")
            self.assertEqual(row["full_text_status"], "")
            self.assertEqual(row["full_text_decision"], "")
            self.assertEqual(row["full_text_exclusion_reason"], "")

    def test_current_corpus_matches_are_flagged(self):
        endpoint_rows = [
            row for row in self.package["records"] if row["current_corpus_cite_keys"]
        ]
        self.assertEqual(len(endpoint_rows), 42)
        added = [
            row
            for row in endpoint_rows
            if "10.1007/978-3-031-26507-5_15" in row["current_corpus_cite_keys"]
        ]
        self.assertEqual(len(added), 1)
        self.assertTrue(
            all(row["automation_suggestion"] == "retain for author review" for row in endpoint_rows)
        )

    def test_conference_review_is_classified_as_non_research(self):
        row = {
            "title": "11th Balkan Conference in Informatics, BCI 2025",
            "venue": "Communications in Computer and Information Science",
            "source_type": "Conference review",
            "source": "Scopus",
            "source_id": "2-s2.0-00000000000",
            "doi": "",
        }
        self.assertEqual(ledger.classify_publication_type(row), "non-research item")

    def test_preprint_survey_is_classified_as_review(self):
        row = {
            "title": "A Survey on Task Scheduling in Carbon-Aware Container Orchestration",
            "venue": "CoRR",
            "source_type": "Informal and Other Publications",
            "source": "arXiv",
            "source_id": "2501.00000",
            "doi": "",
        }
        self.assertEqual(ledger.classify_publication_type(row), "review or survey")

    def test_authorized_screening_uses_title_and_abstract_only(self):
        package = {
            "records": [
                {
                    "title": "Kubernetes scheduling under workload variation",
                    "abstract": "We place container pods across clusters to reduce latency.",
                    "keywords": "carbon; renewable energy",
                    "venue": "Green Computing Workshop",
                    "language": "English",
                    "publication_type": "workshop paper",
                    "current_corpus_cite_keys": [],
                    "reviewer_title_abstract_decision": "",
                    "reviewer_exclusion_reason": "",
                    "reviewer_notes": "",
                    "full_text_status": "",
                    "full_text_decision": "",
                    "full_text_exclusion_reason": "",
                    "full_text_notes": "",
                }
            ],
            "summary": {},
            "codebook": {},
            "pre_screen_removals": [],
        }
        screened = ledger.apply_authorized_abstract_screening(package)
        row = screened["records"][0]
        self.assertEqual(row["reviewer_title_abstract_decision"], "exclude")
        self.assertEqual(
            row["reviewer_exclusion_reason"],
            "E3 No sustainability objective, signal, constraint, or outcome",
        )

    def test_authorized_screening_populates_auditable_decisions_without_mutating_blank_ledger(self):
        screened = ledger.apply_authorized_abstract_screening(self.package)
        original_rows = self.package["records"]
        screened_rows = screened["records"]

        self.assertTrue(
            all(row["reviewer_title_abstract_decision"] == "" for row in original_rows)
        )
        self.assertTrue(
            all(row["reviewer_title_abstract_decision"] for row in screened_rows)
        )
        self.assertEqual(
            sum(bool(row["current_corpus_cite_keys"]) for row in screened_rows),
            42,
        )
        self.assertTrue(
            all(
                row["reviewer_title_abstract_decision"] == "include for full text"
                for row in screened_rows
                if row["current_corpus_cite_keys"]
            )
        )
        self.assertTrue(
            all(
                row["reviewer_exclusion_reason"]
                for row in screened_rows
                if row["reviewer_title_abstract_decision"] == "exclude"
            )
        )
        self.assertTrue(
            all(
                not row["reviewer_exclusion_reason"]
                for row in screened_rows
                if row["reviewer_title_abstract_decision"] != "exclude"
            )
        )
        self.assertTrue(
            all(
                row["full_text_status"] == ""
                and row["full_text_decision"] == ""
                and row["full_text_exclusion_reason"] == ""
                and row["full_text_notes"] == ""
                for row in screened_rows
            )
        )
        self.assertTrue(
            all(
                "automated" in row["reviewer_notes"].casefold()
                and "2026-08-29" in row["reviewer_notes"]
                for row in screened_rows
            )
        )
        decision_counts = screened["summary"]["auto_title_abstract_decision_counts"]
        self.assertEqual(sum(decision_counts.values()), 4464)
        self.assertTrue(screened["summary"]["auto_title_abstract_screening_authorized"])
        self.assertEqual(
            screened["summary"]["auto_title_abstract_screening_date"],
            "2026-08-29",
        )

    def test_missing_abstract_is_uncertain_unless_current_corpus_is_protected(self):
        screened = ledger.apply_authorized_abstract_screening(self.package)
        uncertain_rows = [
            row
            for row in screened["records"]
            if not row["abstract"] and not row["current_corpus_cite_keys"]
            and row["publication_type"] not in {"review or survey", "non-research item"}
            and row["language"].casefold() in {"", "english"}
            and not ledger.title_looks_non_english(row["title"])
        ]
        self.assertTrue(uncertain_rows)
        self.assertTrue(
            all(
                row["reviewer_title_abstract_decision"] == "uncertain"
                for row in uncertain_rows
            )
        )
        self.assertTrue(
            all(row["reviewer_exclusion_reason"] == "" for row in uncertain_rows)
        )

    def test_strict_core_scope_caps_full_text_candidates_at_fifty(self):
        screened = ledger.apply_authorized_abstract_screening(self.package)
        included = [
            row
            for row in screened["records"]
            if row["reviewer_title_abstract_decision"] == "include for full text"
        ]
        protected = [row for row in included if row["current_corpus_cite_keys"]]
        selected_new = [
            row for row in included if not row["current_corpus_cite_keys"]
        ]
        self.assertEqual(len(included), 50)
        self.assertEqual(len(protected), 42)
        self.assertEqual(len(selected_new), 8)
        self.assertEqual(screened["summary"]["core_intervention_cap"], 50)
        self.assertEqual(screened["summary"]["selected_new_core_candidates"], 8)
        self.assertTrue(
            any(
                row["reviewer_exclusion_reason"]
                == "E7 Outside core synthesis but potentially useful as supporting evidence"
                for row in screened["records"]
            )
        )

    def test_strict_new_candidate_selection_is_independent_of_row_order(self):
        forward = ledger.apply_authorized_abstract_screening(self.package)
        reversed_package = deepcopy(self.package)
        reversed_package["records"].reverse()
        backward = ledger.apply_authorized_abstract_screening(reversed_package)

        def selected_new_ids(package):
            return {
                row["screening_id"]
                for row in package["records"]
                if row["reviewer_title_abstract_decision"] == "include for full text"
                and not row["current_corpus_cite_keys"]
            }

        self.assertEqual(selected_new_ids(forward), selected_new_ids(backward))

    def test_selected_new_core_candidates_are_directly_scoped_in_the_title(self):
        screened = ledger.apply_authorized_abstract_screening(self.package)
        selected_new = [
            row
            for row in screened["records"]
            if row["reviewer_title_abstract_decision"] == "include for full text"
            and not row["current_corpus_cite_keys"]
        ]
        platform = re.compile(
            r"\b(kubernetes|k8s|k3s|containers?|containerized|pods?|docker|cloud[ -]?native|[a-z0-9-]*kube[a-z0-9-]*)\b",
            re.IGNORECASE,
        )
        decision = re.compile(
            r"\b(schedul\w*|placement|orchestrat\w*)\b",
            re.IGNORECASE,
        )
        sustainability = re.compile(
            r"\b(carbon\w*|emission\w*|renewable\w*|sustainab\w*|green\w*|electricity|environmental|solar|wind|energy|power|thermal|cooling|watt\w*)\b",
            re.IGNORECASE,
        )
        for row in selected_new:
            self.assertRegex(row["title"], platform)
            self.assertRegex(row["title"], decision)
            self.assertRegex(row["title"], sustainability)
            self.assertNotRegex(row["title"], re.compile(r"\breview\b", re.IGNORECASE))

    def test_written_machine_readable_outputs_match(self):
        ledger.write_outputs(self.package)
        output = Path(ledger.OUTPUT)
        records = json.loads(
            (output / "screening_records.json").read_text(encoding="utf-8")
        )
        removals = json.loads(
            (output / "pre_screen_removals.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(records), 4464)
        self.assertEqual(len(removals), 522)


if __name__ == "__main__":
    unittest.main()
