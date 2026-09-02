import unittest

import analyze_prisma_core as core
import build_prisma_reconstruction as reconstruction


class PrismaReconstructionTests(unittest.TestCase):
    def test_indented_bibtex_entries_are_loaded(self):
        bibliography = reconstruction.load_bibliography()
        self.assertIn("11101082", bibliography)
        self.assertEqual(
            bibliography["11101082"]["doi"],
            "10.1109/ecti-con64996.2025.11101082",
        )

    def test_verified_invited_paper_title_variant_is_confirmed(self):
        rows = reconstruction.reconstruct()
        townend = next(row for row in rows if row["cite_key"] == "townend2019improving")
        self.assertEqual(townend["search_match_status"], "confirmed")
        self.assertEqual(townend["matched_records"][0]["doi"], "10.1109/sose.2019.00030")

    def test_formal_version_is_preferred_over_greenpod_preprint(self):
        rows = reconstruction.reconstruct()
        greenpod = next(row for row in rows if row["cite_key"] == "pradeep2025energy")
        self.assertEqual(greenpod["retained_version"], "formal publication")
        self.assertEqual(
            greenpod["retained_record"]["doi"],
            "10.1109/aiiot65859.2025.11105266",
        )

    def test_all_verified_formal_versions_are_retained(self):
        rows = {row["cite_key"]: row for row in reconstruction.reconstruct()}
        for key, doi in reconstruction.FORMAL_VERSION_DOIS.items():
            with self.subTest(key=key):
                self.assertEqual(rows[key]["retained_version"], "formal publication")
                self.assertEqual(rows[key]["retained_record"]["doi"], doi)
                self.assertEqual(
                    rows[key]["version_action"],
                    "replace preprint metadata with formal publication",
                )

    def test_manual_duplicate_review_freezes_screening_input(self):
        records = (
            core.load_acm()
            + core.load_ieee()
            + core.load_scopus()
            + core.load_dblp()
            + core.load_arxiv()
        )
        analysis = core.analyze(records)
        near = core.find_near_title_candidates(records, analysis["components"])
        exact_classes = core.classify_exact_groups(analysis["duplicate_groups"])
        resolution = core.resolve_duplicate_review(
            records, analysis, near, exact_classes
        )
        self.assertEqual(resolution["duplicate_records_removed"], 512)
        self.assertEqual(resolution["superseded_preprint_records_removed"], 10)
        self.assertEqual(resolution["records_for_screening"], 4464)

    def test_prisma_endpoint_reconciliation_is_internally_consistent(self):
        result = reconstruction.build_prisma_result()
        self.assertEqual(result["records_identified"], 4986)
        self.assertEqual(result["duplicate_records_removed"], 512)
        self.assertEqual(result["records_removed_for_other_reasons"], 10)
        self.assertEqual(result["records_screened"], 4464)
        self.assertEqual(result["database_export_matched_included_reports"], 42)
        self.assertEqual(result["unmatched_included_reports"], 42)
        self.assertEqual(result["records_not_retained_aggregate"], 4422)
        self.assertEqual(result["included_reports"], 84)


if __name__ == "__main__":
    unittest.main()
