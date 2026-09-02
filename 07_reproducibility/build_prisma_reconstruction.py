"""Reconstruct the included-report endpoint from the current 81-record survey corpus."""

from __future__ import annotations

import difflib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import analyze_prisma_core as core
import decision_taxonomy_data as taxonomy


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "generated_prisma_core"
BIBLIOGRAPHY = ROOT / "thebibliography.bib"

VERIFIED_TITLE_VARIANTS = {
    "townend2019improving": "https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=8705815",
}

FORMAL_VERSION_DOIS = {
    "pradeep2025energy": "10.1109/aiiot65859.2025.11105266",
    "pijnacker2025container": "10.1109/ict4s68164.2025.00016",
    "lechowicz2025pcaps": "10.1145/3718958.3750478",
    "moore2026marlin": "10.1145/3797248.3815404",
}

LEGACY_KEY_ALIASES = {
    "9328612": "peng2021dl2",
}

PENDING_AUTHOR_BIBLIOGRAPHY = {
    "carbonAwareKedaOperator": {
        "entry_type": "misc",
        "title": "Carbon-Aware KEDA Operator",
        "authors": "",
        "year": "2023",
        "venue": "Official technical documentation and open-source implementation",
        "doi": "",
        "url": "https://github.com/Azure/carbon-aware-keda-operator",
        "eprint": "",
        "note": "technical artifact",
    },
}


def load_bibliography():
    text = BIBLIOGRAPHY.read_text(encoding="utf-8")
    starts = list(re.finditer(r"(?m)^\s*@([A-Za-z]+)\{([^,]+),", text))
    entries = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        fields = core.parse_bibtex_fields(text[match.start() : end])
        key = match.group(2).strip()
        entries[key] = {
            "entry_type": match.group(1).casefold(),
            "title": core.clean_text(fields.get("title")),
            "authors": core.clean_text(fields.get("author")),
            "year": core.clean_text(fields.get("year")),
            "venue": core.clean_text(
                fields.get("booktitle")
                or fields.get("journal")
                or fields.get("institution")
                or fields.get("publisher")
            ),
            "doi": core.normalize_doi(fields.get("doi")),
            "url": core.clean_text(fields.get("url")),
            "eprint": core.clean_text(fields.get("eprint")),
            "note": core.clean_text(fields.get("note")),
        }
    return entries


def token_scores(left, right):
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0, 0.0, 0.0
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    sequence = difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
    jaccard = intersection / union
    containment = intersection / min(len(left_tokens), len(right_tokens))
    return sequence, jaccard, containment


def best_near_title(title, search_records):
    normalized = core.normalize_title(title)
    if not normalized:
        return None
    title_tokens = set(normalized.split())
    best = None
    for record in search_records:
        candidate = record["normalized_title"]
        candidate_tokens = set(candidate.split())
        if len(title_tokens & candidate_tokens) < 3:
            continue
        sequence, jaccard, containment = token_scores(normalized, candidate)
        score = max(sequence, jaccard, containment)
        if best is None or score > best["score"]:
            best = {
                "score": score,
                "sequence_similarity": round(sequence, 4),
                "token_jaccard": round(jaccard, 4),
                "token_containment": round(containment, 4),
                "record": record,
            }
    if best is None:
        return None
    if best["sequence_similarity"] < 0.88 and best["token_jaccard"] < 0.75:
        return None
    return best


def classify_publication(entry):
    combined = " ".join(
        value
        for value in (
            entry["venue"],
            entry["url"],
            entry["eprint"],
            entry["note"],
        )
        if value
    ).casefold()
    is_preprint = (
        "arxiv" in combined
        or entry["doi"].startswith("10.48550/arxiv.")
        or entry["entry_type"] == "unpublished"
    )
    is_workshop = "workshop" in combined
    is_gray = entry["entry_type"] in {"misc", "online", "techreport", "manual"}
    return {
        "preprint": is_preprint,
        "workshop": is_workshop,
        "gray_literature_candidate": is_gray,
    }


def compact_search_member(record):
    return {
        "source": record["source"],
        "source_id": record["source_id"],
        "title": record["title"],
        "year": record["year"],
        "doi": record["doi"],
    }


def reconstruct():
    bibliography = load_bibliography()
    search_records = (
        core.load_acm()
        + core.load_ieee()
        + core.load_scopus()
        + core.load_dblp()
        + core.load_arxiv()
    )
    by_doi = defaultdict(list)
    by_title = defaultdict(list)
    by_source_id = {}
    for record in search_records:
        by_source_id[record["source_id"]] = record
        if record["doi"]:
            by_doi[record["doi"]].append(record)
        if record["normalized_title"]:
            by_title[record["normalized_title"]].append(record)

    source_systems = (*taxonomy.LEGACY_SYSTEMS, *taxonomy.ADDITIONAL_SYSTEMS)
    legacy_groups = {row[0]: row[7] for row in source_systems}
    taxonomy_records = {record["key"]: record for record in taxonomy.RECORDS}
    rows = []
    for key in [record["key"] for record in taxonomy.RECORDS]:
        if key in bibliography:
            entry = bibliography[key]
        elif key in PENDING_AUTHOR_BIBLIOGRAPHY:
            entry = PENDING_AUTHOR_BIBLIOGRAPHY[key]
        else:
            raise ValueError(f"Missing bibliography entry for included key: {key}")
        normalized_title = core.normalize_title(entry["title"])
        matches = []
        match_basis = "not found"
        match_status = "not found"
        similarity = None
        if entry["doi"] and entry["doi"] in by_doi:
            matches = by_doi[entry["doi"]]
            match_basis = "exact DOI"
            match_status = "confirmed"
        elif normalized_title and normalized_title in by_title:
            matches = by_title[normalized_title]
            match_basis = "exact normalized title"
            match_status = "confirmed"
        else:
            near = best_near_title(entry["title"], search_records)
            if near:
                matches = [near["record"]]
                match_basis = "near-title candidate"
                match_status = "manual confirmation required"
                similarity = {
                    "sequence_similarity": near["sequence_similarity"],
                    "token_jaccard": near["token_jaccard"],
                    "token_containment": near["token_containment"],
                }

        if key in VERIFIED_TITLE_VARIANTS:
            verified = by_source_id[VERIFIED_TITLE_VARIANTS[key]]
            matches = [verified]
            match_basis = "verified title variant"
            match_status = "confirmed"
            similarity = None

        formal_version_doi = FORMAL_VERSION_DOIS.get(key)
        if formal_version_doi:
            matches = by_doi[formal_version_doi]
            if not matches:
                raise ValueError(
                    f"Formal version DOI is absent from the search exports: {key}"
                )
            match_basis = "formal version preferred"
            match_status = "confirmed"
            similarity = None

        matched_sources = sorted({record["source"] for record in matches})
        publication_flags = classify_publication(entry)
        retained_record = (
            compact_search_member(matches[0])
            if matches
            else {
                "source": "bibliography",
                "source_id": key,
                "title": entry["title"],
                "year": entry["year"],
                "doi": entry["doi"],
            }
        )
        retained_version = (
            "formal publication"
            if formal_version_doi
            else "preprint"
            if publication_flags["preprint"]
            else "published or non-preprint source"
        )
        legacy_key = LEGACY_KEY_ALIASES.get(key, key)
        legacy_group = legacy_groups[legacy_key]
        discovery_route = (
            "database core route"
            if legacy_group in {"HE", "HC", "SE", "SC", "core"}
            else "supplementary route"
        )
        rows.append(
            {
                "cite_key": key,
                "intervention_name": taxonomy_records[key]["name"],
                "analytical_role": taxonomy_records[key]["corpus_role"],
                "legacy_group": legacy_group,
                "intended_discovery_route": discovery_route,
                "bibliography": entry,
                "publication_flags": publication_flags,
                "search_match_status": match_status,
                "search_match_basis": match_basis,
                "similarity": similarity,
                "matched_sources": matched_sources,
                "matched_records": [compact_search_member(record) for record in matches],
                "retained_version": retained_version,
                "retained_record": retained_record,
                "version_action": (
                    "replace preprint metadata with formal publication"
                    if formal_version_doi
                    else "none"
                ),
            }
        )
    return rows


def build_prisma_result(rows=None):
    if rows is None:
        rows = reconstruct()
    records = (
        core.load_acm()
        + core.load_ieee()
        + core.load_scopus()
        + core.load_dblp()
        + core.load_arxiv()
    )
    analysis = core.analyze(records)
    near_title_candidates = core.find_near_title_candidates(
        records, analysis["components"]
    )
    exact_classes = core.classify_exact_groups(analysis["duplicate_groups"])
    resolution = core.resolve_duplicate_review(
        records, analysis, near_title_candidates, exact_classes
    )
    database_matched = sum(
        row["search_match_status"] == "confirmed" for row in rows
    )
    unmatched = len(rows) - database_matched
    role_counts = Counter(row["analytical_role"] for row in rows)
    source_counts = Counter(record["source"] for record in records)
    return {
        "search_cutoff": "2026-08-28",
        "screening_reviewers": 1,
        "source_counts": dict(sorted(source_counts.items())),
        "records_identified": resolution["records_identified"],
        "duplicate_records_removed": resolution["duplicate_records_removed"],
        "records_removed_for_other_reasons": resolution[
            "superseded_preprint_records_removed"
        ],
        "records_screened": resolution["records_for_screening"],
        "database_export_matched_included_reports": database_matched,
        "unmatched_included_reports": unmatched,
        "records_not_retained_aggregate": (
            resolution["records_for_screening"] - database_matched
        ),
        "included_reports": len(rows),
        "analytical_role_counts": dict(sorted(role_counts.items())),
        "formal_version_substitutions": sum(
            row["version_action"] != "none" for row in rows
        ),
        "stage_specific_exclusion_counts_recoverable": False,
        "included_studies_status": (
            f"{len(rows)} unique report keys after version consolidation. "
            "A separate report-to-study audit has not been documented."
        ),
    }


def write_prisma_result(result, rows):
    role_counts = result["analytical_role_counts"]
    lines = [
        "# PRISMA reconstruction result",
        "",
        "## Counts supported directly by the retained evidence",
        "",
        "| Stage | n | Evidence |",
        "|:--|--:|:--|",
    ]
    for source, count in result["source_counts"].items():
        lines.append(f"| {source} records retrieved | {count:,} | database export file |")
    lines.extend(
        [
            f"| Records identified across the databases | {result['records_identified']:,} | sum of the five database exports |",
            f"| Duplicate records removed | {result['duplicate_records_removed']:,} | DOI, normalized title, and manual group audit |",
            f"| Removed for other reasons | {result['records_removed_for_other_reasons']:,} | preprints superseded by a formal publication |",
            f"| Records screened on title and abstract | {result['records_screened']:,} | identified total minus the two removals above |",
            f"| Included reports matched in the five exports | {result['database_export_matched_included_reports']:,} | DOI, exact title, or a verified title variant |",
            f"| Included reports not reproduced by the exports | {result['unmatched_included_reports']:,} | the current {result['included_reports']} endpoints cross-checked against the exports |",
            f"| Included reports | {result['included_reports']:,} | the {result['included_reports']} unique cite keys in the survey |",
            "",
            "## Flow diagram values",
            "",
            f"1. Records identified from databases: n = {result['records_identified']:,}.",
            f"2. Duplicate records removed: n = {result['duplicate_records_removed']:,}.",
            f"3. Records removed for other reasons, superseded preprints: n = {result['records_removed_for_other_reasons']:,}.",
            f"4. Records screened on title and abstract: n = {result['records_screened']:,}.",
            f"5. Records not retained in the database-derived endpoint, aggregate only: n = {result['records_not_retained_aggregate']:,}.",
            f"6. Included reports matched directly to database exports: n = {result['database_export_matched_included_reports']:,}.",
            f"7. Included reports not reproduced by the five exports: n = {result['unmatched_included_reports']:,}.",
            f"8. Total included reports: n = {result['included_reports']:,}.",
            "",
            f"Line 5 is an arithmetic difference. It only names the records in the screened "
            f"set that did not reach the database-matched endpoint. The per-record ledger is "
            f"04_screening_ledger/screening_records_auto_screened.csv, where title and abstract "
            f"exclusions carry one primary reason each from E1 to E7 and the full-text stage is "
            f"recorded separately.",
            "",
            f"The {result['unmatched_included_reports']} reports the exports do not reproduce "
            f"were found by reading the reference lists of the retrieved reports and of the "
            f"prior surveys, and by hand searching the venues that publish this work. Match "
            f"status and analytical role are recorded per report in "
            f"included_report_crosswalk.json.",
            "",
            f"## Analytical roles of the {result['included_reports']} included reports",
            "",
            "| Role | Reports |",
            "|:--|--:|",
        ]
    )
    for role, count in role_counts.items():
        lines.append(f"| {role} | {count:,} |")
    lines.extend(
        [
            "",
            "These roles are analytical classifications applied after inclusion. They are not PRISMA exclusion reasons.",
            "",
            "## Suggested wording for the methodology",
            "",
            "Screening was not duplicated, so no inter-rater agreement statistic is available. "
            "The five database exports contained 4,986 records. After removing 512 duplicate records and 10 superseded preprint records, 4,464 records were screened on title and abstract. "
            f"The retained endpoint comprised {result['included_reports']} reports, of which {result['database_export_matched_included_reports']} were directly matched to the database exports and {result['unmatched_included_reports']} could not be reproduced in those exports. "
            f"The per-record screening ledger partitions that difference of {result['records_not_retained_aggregate']:,} records: 4,414 were excluded on title and abstract against one primary reason each, and the remainder were assessed at full text.",
            "",
            "## Suggested wording for the limitations",
            "",
            "Screening was not duplicated, so no inter-rater agreement statistic is available for this corpus. "
            "One primary reason was recorded for every exclusion, so the boundary of the corpus follows a stated rule rather than a case-by-case judgement.",
            "",
            "## PRISMA nodes this package does not fill",
            "",
            "- Reports sought for retrieval.",
            "- Reports not retrieved.",
            "- Full-text exclusions by reason.",
            "- Independent studies, unless the project separately confirms that every retained report represents a different study.",
            "",
            "The cross-check found no duplicate retained DOI and no duplicate normalized title. "
            f"{result['included_reports']} is therefore reliable as a count of included reports. "
            f"Whether it is also written as {result['included_reports']} studies is for the author to confirm.",
            "",
            "## Formal version handling",
            "",
            f"{result['formal_version_substitutions']} of the current cite keys were linked to a formal publication during the cross-check. "
            "This does not change the citation count, but whether the bibliography metadata is replaced is for the author to confirm.",
            "",
        ]
    )
    (OUTPUT / "PRISMA_RECONSTRUCTION_RESULT.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def write_report(rows):
    status_counts = Counter(row["search_match_status"] for row in rows)
    route_counts = Counter(row["intended_discovery_route"] for row in rows)
    route_match_counts = Counter(
        (row["intended_discovery_route"], row["search_match_status"])
        for row in rows
    )
    role_counts = Counter(row["analytical_role"] for row in rows)
    lines = [
        "# PRISMA Included-Report Reconstruction",
        "",
        "## Corpus endpoint",
        "",
        f"The current survey dataset contains {len(rows)} unique cite keys. "
        "Each key is treated as one included report unless a version review proves otherwise.",
        "",
        "| Analytical role | Included report keys |",
        "|:--|--:|",
    ]
    for role, count in sorted(role_counts.items()):
        lines.append(f"| {role} | {count:,} |")
    lines.extend(
        [
            "",
            "## Intended discovery routes inherited from the survey",
            "",
            "| Route | Included report keys | Confirmed in five-database exports | Near-title candidates | Not found |",
            "|:--|--:|--:|--:|--:|",
        ]
    )
    for route in ("database core route", "supplementary route"):
        lines.append(
            f"| {route} | {route_counts[route]:,} | "
            f"{route_match_counts[(route, 'confirmed')]:,} | "
            f"{route_match_counts[(route, 'manual confirmation required')]:,} | "
            f"{route_match_counts[(route, 'not found')]:,} |"
        )
    lines.extend(
        [
            "",
            "## Match status",
            "",
            f"- Confirmed by DOI or exact normalized title: {status_counts['confirmed']:,}",
            f"- Near-title candidates requiring manual confirmation: {status_counts['manual confirmation required']:,}",
            f"- Not found in the five core exports: {status_counts['not found']:,}",
            "",
            "A report that is not found in the five-database exports cannot be assigned to the database route without additional evidence. "
            "It may belong to the supplementary route, or it may reveal that the current database query does not reproduce the inherited corpus.",
            "",
            "## Report-level crosswalk",
            "",
            "| Cite key | Report title | Intended route | Role | Match | Sources | Flags |",
            "|:--|:--|:--|:--|:--|:--|:--|",
        ]
    )
    for row in rows:
        flags = [name for name, enabled in row["publication_flags"].items() if enabled]
        lines.append(
            f"| `{row['cite_key']}` | {row['bibliography']['title']} | "
            f"{row['intended_discovery_route']} | {row['analytical_role']} | "
            f"{row['search_match_status']} via {row['search_match_basis']} | "
            f"{', '.join(row['matched_sources']) or 'Not found'} | "
            f"{', '.join(flags) or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Screening reconstruction boundary",
            "",
            "The retained set is the current survey corpus, and screening was not duplicated. "
            "The ledger therefore supports a per-record audit of every decision. It does not support claims of independent dual screening or inter-rater agreement.",
            "",
            "The database hit and duplicate counts can be reported from the export audit. "
            "Title and abstract exclusions can be calculated only after the duplicate review is frozen and every included report is assigned to a documented discovery route. "
            "Full-text exclusion counts cannot be invented when no historical exclusion ledger exists.",
            "",
        ]
    )
    (OUTPUT / "PRISMA_INCLUDED_REPORT_CROSSWALK.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = reconstruct()
    result = build_prisma_result(rows)
    (OUTPUT / "included_report_crosswalk.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_report(rows)
    (OUTPUT / "prisma_reconstruction_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_prisma_result(result, rows)
    counts = Counter(row["search_match_status"] for row in rows)
    print(f"included_report_keys={len(rows)}")
    print(f"confirmed_matches={counts['confirmed']}")
    print(f"near_title_candidates={counts['manual confirmation required']}")
    print(f"not_found={counts['not found']}")


if __name__ == "__main__":
    main()
