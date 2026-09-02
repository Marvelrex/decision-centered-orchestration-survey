import json
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "generated_prisma_screening" / "screening_records_auto_screened.json"
OUTPUT = (
    ROOT
    / "outputs"
    / "prisma_author_review_2026-08-29"
    / "PRISMA_author_screening_review_2026-08-29.xlsx"
)
NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
    "x14": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main",
}


class PrismaAuthorReviewWorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_source_contains_exact_author_review_queues(self):
        uncertain = [
            row
            for row in self.records
            if row["reviewer_title_abstract_decision"] == "uncertain"
        ]
        full_text = [
            row
            for row in self.records
            if row["reviewer_title_abstract_decision"] == "include for full text"
        ]
        self.assertEqual(len(uncertain), 90)
        self.assertEqual(len(full_text), 50)

    def test_workbook_contains_focused_review_sheets_and_rows(self):
        self.assertTrue(OUTPUT.exists(), f"Missing author-review workbook: {OUTPUT}")
        with zipfile.ZipFile(OUTPUT) as archive:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            targets = {
                rel.attrib["Id"]: rel.attrib["Target"]
                for rel in rels.findall("p:Relationship", NS)
            }
            sheet_paths = {}
            for sheet in workbook.findall("m:sheets/m:sheet", NS):
                name = sheet.attrib["name"]
                target = targets[sheet.attrib[f"{{{NS['r']}}}id"]]
                sheet_paths[name] = "xl/" + target.lstrip("/")

            self.assertEqual(
                list(sheet_paths),
                ["Instructions", "Uncertain 90", "Full Text 50", "Decision Codes"],
            )
            uncertain_xml = ET.fromstring(archive.read(sheet_paths["Uncertain 90"]))
            full_text_xml = ET.fromstring(archive.read(sheet_paths["Full Text 50"]))
            self.assertEqual(len(uncertain_xml.findall("m:sheetData/m:row", NS)), 91)
            self.assertEqual(len(full_text_xml.findall("m:sheetData/m:row", NS)), 51)
            self.assertTrue(uncertain_xml.findall(".//x14:dataValidation", NS))
            self.assertTrue(full_text_xml.findall(".//x14:dataValidation", NS))


if __name__ == "__main__":
    unittest.main()
