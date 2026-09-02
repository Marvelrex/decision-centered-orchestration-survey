"""Normalize the five core database exports and audit exact duplicates."""

from __future__ import annotations

import csv
import difflib
import html
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NEW_EXPORTS = (
    ROOT
    / "PRISMA_Core_Exports_2026-08-28"
    / "PRISMA_Core_Exports_2026-08-28"
)
EARLIER_EXPORTS = (
    ROOT
    / "PRISMA_S_retrieval_2026-08-28"
    / "PRISMA_S_retrieval_2026-08-28"
)
OUTPUT = ROOT / "generated_prisma_core"

CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS = {
    "EXACT-0058",
    "EXACT-0095",
    "EXACT-0334",
    "EXACT-0400",
    "EXACT-0406",
}

KEEP_SEPARATE_NO_DOI_GROUP_IDS = {
    "EXACT-0002",
    "EXACT-0055",
    "EXACT-0056",
    "EXACT-0057",
    "EXACT-0059",
    "EXACT-0061",
    "EXACT-0097",
    "EXACT-0379",
}

PREPRINT_DUPLICATE_CONFLICT_IDS = {
    "CONFLICT-0010",
    "CONFLICT-0011",
}

SUPERSEDED_PREPRINT_CONFLICT_IDS = {
    "CONFLICT-0006",
    "CONFLICT-0009",
    "CONFLICT-0010",
    "CONFLICT-0011",
    "CONFLICT-0012",
    "CONFLICT-0016",
    "CONFLICT-0017",
    "CONFLICT-0018",
}

SUPERSEDED_PREPRINT_NEAR_IDS = {
    "NEAR-0002",
    "NEAR-0003",
}


def clean_text(value):
    if value is None:
        return ""
    text = html.unescape(str(value)).replace("\ufffd", " ")
    text = re.sub(r"\s+Less\s*$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi(value):
    text = clean_text(value).casefold()
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text)
    text = re.sub(r"^doi:\s*", "", text)
    return text.rstrip(" .,/")


def normalize_title(value):
    text = clean_text(value)
    text = re.sub(r"\\[A-Za-z]+\s*", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_bibtex_fields(block):
    comma = block.find(",")
    position = comma + 1
    fields = {}
    length = len(block)
    while position < length:
        while position < length and (block[position].isspace() or block[position] == ","):
            position += 1
        if position >= length or block[position] == "}":
            break
        name_start = position
        while position < length and (block[position].isalnum() or block[position] in "_-"):
            position += 1
        name = block[name_start:position].casefold()
        while position < length and block[position].isspace():
            position += 1
        if not name or position >= length or block[position] != "=":
            next_line = block.find("\n", position)
            position = length if next_line < 0 else next_line + 1
            continue
        position += 1
        while position < length and block[position].isspace():
            position += 1
        if position >= length:
            fields[name] = ""
            break
        if block[position] == "{":
            position += 1
            value_start = position
            depth = 1
            while position < length and depth:
                if block[position] == "{":
                    depth += 1
                elif block[position] == "}":
                    depth -= 1
                position += 1
            value = block[value_start : position - 1]
        elif block[position] == '"':
            position += 1
            value_start = position
            escaped = False
            while position < length:
                char = block[position]
                if char == '"' and not escaped:
                    break
                escaped = char == "\\" and not escaped
                if char != "\\":
                    escaped = False
                position += 1
            value = block[value_start:position]
            position += 1
        else:
            value_start = position
            while position < length and block[position] not in ",\n":
                position += 1
            value = block[value_start:position]
        fields[name] = clean_text(value)
    return fields


def load_acm():
    path = NEW_EXPORTS / "ACM" / "acm_core_2026-08-28_combined_3327.bib"
    text = path.read_text(encoding="utf-8")
    starts = list(re.finditer(r"(?m)^@([A-Za-z]+)\{([^,]+),", text))
    records = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        fields = parse_bibtex_fields(text[match.start() : end])
        records.append(
            make_record(
                source="ACM Digital Library",
                source_id=match.group(2).strip(),
                source_type=match.group(1).casefold(),
                title=fields.get("title"),
                authors=fields.get("author"),
                year=fields.get("year"),
                venue=fields.get("booktitle") or fields.get("journal") or fields.get("series"),
                doi=fields.get("doi"),
                url=fields.get("url"),
                abstract=fields.get("abstract"),
                keywords=fields.get("keywords"),
            )
        )
    return records


def load_ieee():
    path = NEW_EXPORTS / "IEEE" / "ieee_core_2026-08-28_all_668.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    records = []
    for index, row in enumerate(rows, start=1):
        records.append(
            make_record(
                source="IEEE Xplore",
                source_id=row.get("PDF Link") or f"row-{index}",
                source_type=row.get("Document Identifier"),
                title=row.get("Document Title"),
                authors=row.get("Authors"),
                year=row.get("Publication Year"),
                venue=row.get("Publication Title"),
                doi=row.get("DOI"),
                url=row.get("PDF Link"),
                abstract=row.get("Abstract"),
                keywords=", ".join(
                    value
                    for value in (row.get("Author Keywords", ""), row.get("IEEE Terms", ""))
                    if value
                ),
            )
        )
    return records


def load_scopus():
    path = NEW_EXPORTS / "Scopus" / "scopus_core_2026-08-28_all_773.csv"
    # Scopus localizes its CSV header row. The export used here came from a
    # Chinese-locale session, so each field is read by its English header first
    # and falls back to the localized header.
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    records = []
    for index, row in enumerate(rows, start=1):
        records.append(
            make_record(
                source="Scopus",
                source_id=row.get("EID") or f"row-{index}",
                source_type=row.get("Document Type") or row.get("\u6587\u732e\u7c7b\u578b"),
                title=row.get("Title") or row.get("\u6587\u732e\u6807\u9898"),
                authors=row.get("Author full names") or row.get("Authors") or row.get("\u4f5c\u8005"),
                year=row.get("Year") or row.get("\u5e74\u4efd"),
                venue=row.get("Source title") or row.get("\u6765\u6e90\u51fa\u7248\u7269\u540d\u79f0"),
                doi=row.get("DOI"),
                url=row.get("Link") or row.get("\u94fe\u63a5"),
                abstract=row.get("Abstract") or row.get("\u6458\u8981"),
                keywords=", ".join(
                    value
                    for value in (row.get("Author Keywords", "") or row.get("\u4f5c\u8005\u5173\u952e\u5b57", ""), row.get("Index Keywords", "") or row.get("\u7d22\u5f15\u5173\u952e\u5b57", ""))
                    if value
                ),
            )
        )
    return records


def load_dblp():
    path = EARLIER_EXPORTS / "dblp_core_2026-08-28.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for row in data["records"]:
        info = row.get("info", {})
        author_data = info.get("authors", {}).get("author", [])
        if isinstance(author_data, dict):
            author_data = [author_data]
        authors = ", ".join(
            clean_text(author.get("text") if isinstance(author, dict) else author)
            for author in author_data
        )
        records.append(
            make_record(
                source="DBLP",
                source_id=info.get("key") or row.get("@id"),
                source_type=info.get("type"),
                title=info.get("title"),
                authors=authors,
                year=info.get("year"),
                venue=info.get("venue"),
                doi=info.get("doi"),
                url=info.get("url") or info.get("ee"),
                abstract="",
                keywords="",
            )
        )
    return records


def load_arxiv():
    path = EARLIER_EXPORTS / "arxiv_core_2026-08-28.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for row in data["records"]:
        year_match = re.search(r"(?:19|20)\d{2}", row.get("submission_history", ""))
        records.append(
            make_record(
                source="arXiv",
                source_id=row.get("arxiv_id"),
                source_type="preprint",
                title=row.get("title"),
                authors=", ".join(row.get("authors") or []),
                year=year_match.group(0) if year_match else "",
                venue=row.get("journal_reference"),
                doi=row.get("doi"),
                url=row.get("url"),
                abstract=row.get("abstract"),
                keywords=", ".join(row.get("categories") or []),
            )
        )
    return records


def make_record(
    source,
    source_id,
    source_type,
    title,
    authors,
    year,
    venue,
    doi,
    url,
    abstract,
    keywords,
):
    record = {
        "source": clean_text(source),
        "source_id": clean_text(source_id),
        "source_type": clean_text(source_type),
        "title": clean_text(title),
        "authors": clean_text(authors),
        "year": clean_text(year),
        "venue": clean_text(venue),
        "doi": normalize_doi(doi),
        "url": clean_text(url),
        "abstract": clean_text(abstract),
        "keywords": clean_text(keywords),
    }
    record["normalized_title"] = normalize_title(record["title"])
    record["record_id"] = f"{record['source']}::{record['source_id']}"
    return record


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def group_members(records, indices):
    return [
        {
            "record_id": records[index]["record_id"],
            "source": records[index]["source"],
            "source_id": records[index]["source_id"],
            "title": records[index]["title"],
            "year": records[index]["year"],
            "doi": records[index]["doi"],
        }
        for index in indices
    ]


def analyze(records):
    union = UnionFind(len(records))
    by_doi = defaultdict(list)
    by_title = defaultdict(list)
    for index, record in enumerate(records):
        if record["doi"]:
            by_doi[record["doi"]].append(index)
        if len(record["normalized_title"]) >= 12:
            by_title[record["normalized_title"]].append(index)

    for indices in by_doi.values():
        for index in indices[1:]:
            union.union(indices[0], index)

    title_conflicts = []
    for title, indices in by_title.items():
        if len(indices) < 2:
            continue
        dois = {records[index]["doi"] for index in indices if records[index]["doi"]}
        if len(dois) > 1:
            title_conflicts.append(
                {
                    "normalized_title": title,
                    "distinct_dois": sorted(dois),
                    "members": group_members(records, indices),
                }
            )
            continue
        for index in indices[1:]:
            union.union(indices[0], index)

    components = defaultdict(list)
    for index in range(len(records)):
        components[union.find(index)].append(index)
    duplicate_components = [indices for indices in components.values() if len(indices) > 1]
    duplicate_components.sort(key=lambda indices: (-len(indices), records[indices[0]]["title"]))
    duplicate_groups = []
    for group_number, indices in enumerate(duplicate_components, start=1):
        sources = sorted({records[index]["source"] for index in indices})
        duplicate_groups.append(
            {
                "group_id": f"EXACT-{group_number:04d}",
                "record_count": len(indices),
                "sources": sources,
                "match_basis": "exact DOI or exact normalized title",
                "members": group_members(records, indices),
            }
        )

    source_patterns = Counter(
        " + ".join(group["sources"])
        for group in duplicate_groups
    )
    return {
        "components": components,
        "duplicate_groups": duplicate_groups,
        "title_conflicts": title_conflicts,
        "source_patterns": source_patterns,
    }


def find_near_title_candidates(records, components):
    component_rows = []
    for root, indices in components.items():
        normalized_titles = sorted(
            {records[index]["normalized_title"] for index in indices},
            key=lambda value: (-len(value), value),
        )
        representative_title = normalized_titles[0]
        tokens = frozenset(representative_title.split())
        component_rows.append(
            {
                "root": root,
                "indices": indices,
                "normalized_title": representative_title,
                "tokens": tokens,
                "sources": sorted({records[index]["source"] for index in indices}),
                "years": sorted({records[index]["year"] for index in indices if records[index]["year"]}),
                "dois": sorted({records[index]["doi"] for index in indices if records[index]["doi"]}),
            }
        )

    token_index = defaultdict(list)
    for component_index, row in enumerate(component_rows):
        if len(row["normalized_title"]) < 24 or len(row["tokens"]) < 4:
            continue
        for token in row["tokens"]:
            if len(token) >= 4:
                token_index[token].append(component_index)

    shared_counts = Counter()
    for component_indices in token_index.values():
        if len(component_indices) > 250:
            continue
        for left_position, left_index in enumerate(component_indices):
            for right_index in component_indices[left_position + 1 :]:
                if left_index > right_index:
                    left_index, right_index = right_index, left_index
                shared_counts[(left_index, right_index)] += 1

    candidates = []
    for (left_index, right_index), shared_count in shared_counts.items():
        left = component_rows[left_index]
        right = component_rows[right_index]
        if left["normalized_title"] == right["normalized_title"]:
            continue
        minimum_tokens = min(len(left["tokens"]), len(right["tokens"]))
        if shared_count < max(3, math.ceil(minimum_tokens * 0.6)):
            continue
        intersection = len(left["tokens"] & right["tokens"])
        union = len(left["tokens"] | right["tokens"])
        jaccard = intersection / union
        containment = intersection / minimum_tokens
        sequence = difflib.SequenceMatcher(
            None,
            left["normalized_title"],
            right["normalized_title"],
            autojunk=False,
        ).ratio()
        if not (
            sequence >= 0.94
            or jaccard >= 0.85
            or (containment >= 0.9 and abs(len(left["tokens"]) - len(right["tokens"])) <= 2)
        ):
            continue
        candidates.append(
            {
                "sequence_similarity": round(sequence, 4),
                "token_jaccard": round(jaccard, 4),
                "token_containment": round(containment, 4),
                "left": {
                    "sources": left["sources"],
                    "years": left["years"],
                    "dois": left["dois"],
                    "members": group_members(records, left["indices"]),
                },
                "right": {
                    "sources": right["sources"],
                    "years": right["years"],
                    "dois": right["dois"],
                    "members": group_members(records, right["indices"]),
                },
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["sequence_similarity"],
            -item["token_jaccard"],
            item["left"]["members"][0]["title"],
        )
    )
    for candidate_number, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = f"NEAR-{candidate_number:04d}"
        candidate["decision"] = "human review required"
    return candidates


def classify_exact_groups(duplicate_groups):
    classes = {
        "shared_doi": [],
        "exact_title_with_partial_doi": [],
        "exact_title_without_doi": [],
    }
    for group in duplicate_groups:
        dois = sorted({member["doi"] for member in group["members"] if member["doi"]})
        doi_members = sum(1 for member in group["members"] if member["doi"])
        if len(dois) == 1 and doi_members == group["record_count"]:
            classes["shared_doi"].append(group)
        elif len(dois) == 1:
            classes["exact_title_with_partial_doi"].append(group)
        else:
            classes["exact_title_without_doi"].append(group)
    return classes


def resolve_duplicate_review(records, analysis, near_title_candidates, exact_classes):
    no_doi_ids = {
        group["group_id"] for group in exact_classes["exact_title_without_doi"]
    }
    resolved_no_doi_ids = (
        CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS | KEEP_SEPARATE_NO_DOI_GROUP_IDS
    )
    if no_doi_ids != resolved_no_doi_ids:
        missing = sorted(no_doi_ids - resolved_no_doi_ids)
        stale = sorted(resolved_no_doi_ids - no_doi_ids)
        raise ValueError(
            f"Exact-title no-DOI review is incomplete or stale. Missing={missing}, stale={stale}"
        )

    conflict_ids = {
        f"CONFLICT-{index:04d}"
        for index, _group in enumerate(analysis["title_conflicts"], start=1)
    }
    required_conflict_ids = (
        PREPRINT_DUPLICATE_CONFLICT_IDS | SUPERSEDED_PREPRINT_CONFLICT_IDS
    )
    if not required_conflict_ids <= conflict_ids:
        raise ValueError("A reviewed title-conflict identifier is absent")

    near_ids = {candidate["candidate_id"] for candidate in near_title_candidates}
    if not SUPERSEDED_PREPRINT_NEAR_IDS <= near_ids:
        raise ValueError("A reviewed near-title identifier is absent")

    for group in exact_classes["exact_title_without_doi"]:
        if group["group_id"] in CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS:
            group["decision"] = "merge as cross-database duplicate"
            group["evidence_note"] = (
                "Title, authors, year, and publication identity are compatible."
            )
        else:
            group["decision"] = "keep separate"
            group["evidence_note"] = (
                "Volume, ISBN, year, or proceedings identity differs."
            )

    for index, group in enumerate(analysis["title_conflicts"], start=1):
        group_id = f"CONFLICT-{index:04d}"
        group["group_id"] = group_id
        if group_id in SUPERSEDED_PREPRINT_CONFLICT_IDS:
            group["decision"] = "retain formal publication and remove preprint"
        else:
            group["decision"] = "keep DOI-distinct reports separate"
        if group_id in PREPRINT_DUPLICATE_CONFLICT_IDS:
            group["duplicate_note"] = (
                "Two records describe the same preprint. Remove one as a duplicate "
                "before removing the retained preprint in favor of the formal publication."
            )

    for candidate in near_title_candidates:
        if candidate["candidate_id"] in SUPERSEDED_PREPRINT_NEAR_IDS:
            candidate["decision"] = (
                "retain formal publication and remove superseded preprint"
            )
        else:
            candidate["decision"] = "keep separate"

    confirmed_exact_groups = (
        exact_classes["shared_doi"]
        + exact_classes["exact_title_with_partial_doi"]
        + [
            group
            for group in exact_classes["exact_title_without_doi"]
            if group["group_id"] in CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS
        ]
    )
    exact_duplicate_removals = sum(
        group["record_count"] - 1 for group in confirmed_exact_groups
    )
    conflict_duplicate_removals = len(PREPRINT_DUPLICATE_CONFLICT_IDS)
    duplicate_records_removed = (
        exact_duplicate_removals + conflict_duplicate_removals
    )
    superseded_preprint_records_removed = (
        len(SUPERSEDED_PREPRINT_CONFLICT_IDS)
        + len(SUPERSEDED_PREPRINT_NEAR_IDS)
    )
    records_for_screening = (
        len(records)
        - duplicate_records_removed
        - superseded_preprint_records_removed
    )
    return {
        "records_identified": len(records),
        "confirmed_exact_duplicate_groups": len(confirmed_exact_groups),
        "exact_duplicate_records_removed": exact_duplicate_removals,
        "preprint_duplicate_records_removed": conflict_duplicate_removals,
        "duplicate_records_removed": duplicate_records_removed,
        "superseded_preprint_records_removed": superseded_preprint_records_removed,
        "records_for_screening": records_for_screening,
        "merged_no_doi_group_ids": sorted(CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS),
        "kept_separate_no_doi_group_ids": sorted(KEEP_SEPARATE_NO_DOI_GROUP_IDS),
        "preprint_duplicate_conflict_ids": sorted(
            PREPRINT_DUPLICATE_CONFLICT_IDS
        ),
        "superseded_preprint_conflict_ids": sorted(
            SUPERSEDED_PREPRINT_CONFLICT_IDS
        ),
        "superseded_preprint_near_ids": sorted(SUPERSEDED_PREPRINT_NEAR_IDS),
    }


def write_manual_review(exact_classes, title_conflicts, near_title_candidates):
    lines = [
        "# PRISMA Duplicate Manual Review Decisions",
        "",
        "This file records the completed decisions for cases that were not safe to remove automatically.",
        "When a preprint and formal publication represent the same work, retain the formal publication. "
        "Retain an arXiv record only when no formal publication exists, and label it as a preprint.",
        "",
        "## A. Exact-title groups without DOI",
        "",
        f"Groups reviewed: {len(exact_classes['exact_title_without_doi']):,}",
        "",
    ]
    for group in exact_classes["exact_title_without_doi"]:
        lines.extend(
            [
                f"### {group['group_id']}: {group['members'][0]['title']}",
                "",
                "| Source | Year | Source identifier |",
                "|:--|:--|:--|",
            ]
        )
        for member in group["members"]:
            lines.append(
                f"| {member['source']} | {member['year'] or 'Not recorded'} | {member['source_id']} |"
            )
        lines.extend(
            [
                "",
                f"Decision: {group['decision']}",
                "",
                f"Evidence note: {group['evidence_note']}",
                "",
            ]
        )

    lines.extend(
        [
            "## B. Same-title groups with conflicting DOI",
            "",
            f"Groups reviewed: {len(title_conflicts):,}",
            "",
        ]
    )
    for group_number, group in enumerate(title_conflicts, start=1):
        lines.extend(
            [
                f"### {group['group_id']}: {group['members'][0]['title']}",
                "",
                "| Source | Year | DOI | Source identifier |",
                "|:--|:--|:--|:--|",
            ]
        )
        for member in group["members"]:
            lines.append(
                f"| {member['source']} | {member['year'] or 'Not recorded'} | "
                f"{member['doi'] or 'Not recorded'} | {member['source_id']} |"
            )
        lines.extend(
            [
                "",
                f"Decision: {group['decision']}",
                "",
                (
                    f"Duplicate note: {group['duplicate_note']}"
                    if group.get("duplicate_note")
                    else "Duplicate note: none"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## C. Near-title candidate pairs",
            "",
            f"Pairs reviewed: {len(near_title_candidates):,}",
            "",
        ]
    )
    for candidate in near_title_candidates:
        left = candidate["left"]["members"][0]
        right = candidate["right"]["members"][0]
        lines.extend(
            [
                f"### {candidate['candidate_id']}",
                "",
                f"Similarity scores: sequence {candidate['sequence_similarity']}, "
                f"token Jaccard {candidate['token_jaccard']}, token containment {candidate['token_containment']}",
                "",
                "| Side | Title | Sources | Years | DOI |",
                "|:--|:--|:--|:--|:--|",
                f"| Left | {left['title']} | {', '.join(candidate['left']['sources'])} | "
                f"{', '.join(candidate['left']['years']) or 'Not recorded'} | "
                f"{', '.join(candidate['left']['dois']) or 'Not recorded'} |",
                f"| Right | {right['title']} | {', '.join(candidate['right']['sources'])} | "
                f"{', '.join(candidate['right']['years']) or 'Not recorded'} | "
                f"{', '.join(candidate['right']['dois']) or 'Not recorded'} |",
                "",
                f"Decision: {candidate['decision']}",
                "",
            ]
        )

    (OUTPUT / "PRISMA_DUPLICATE_MANUAL_REVIEW.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def write_report(
    records, analysis, near_title_candidates, exact_classes, resolution
):
    by_source = Counter(record["source"] for record in records)
    fields = ["title", "authors", "year", "venue", "doi", "url", "abstract", "keywords"]
    completeness = {
        source: {
            field: sum(1 for record in records if record["source"] == source and record[field])
            for field in fields
        }
        for source in by_source
    }
    duplicate_records = sum(group["record_count"] for group in analysis["duplicate_groups"])
    removable = sum(group["record_count"] - 1 for group in analysis["duplicate_groups"])
    unique_after_exact = len(records) - removable

    lines = [
        "# PRISMA Core Export and Exact-Deduplication Audit",
        "",
        "## Identification input",
        "",
        "| Source | Imported records |",
        "|:--|--:|",
    ]
    for source in sorted(by_source):
        lines.append(f"| {source} | {by_source[source]:,} |")
    lines.extend(
        [
            f"| Total | {len(records):,} |",
            "",
            "## Search evidence status",
            "",
            "The ACM Digital Library, IEEE Xplore, and Scopus evidence pages record each exact query, search date, field scope, filter status, and database-specific raw hit count. "
            "The updated IEEE page shows `Showing 1-100 of 668 results`, which identifies 668 total hits while displaying records 1 through 100 on the current page.",
            "",
            "## Field completeness",
            "",
            "| Source | Title | Authors | Year | Venue | DOI | URL | Abstract | Keywords |",
            "|:--|--:|--:|--:|--:|--:|--:|--:|--:|",
        ]
    )
    for source in sorted(by_source):
        values = completeness[source]
        lines.append(
            f"| {source} | {values['title']:,} | {values['authors']:,} | "
            f"{values['year']:,} | {values['venue']:,} | {values['doi']:,} | "
            f"{values['url']:,} | {values['abstract']:,} | {values['keywords']:,} |"
        )
    lines.extend(
        [
            "",
            "## Exact duplicate audit",
            "",
            f"- Exact duplicate groups: {len(analysis['duplicate_groups']):,}",
            f"- Records contained in those groups: {duplicate_records:,}",
            f"- Candidate duplicate records removable after group review: {removable:,}",
            f"- Records remaining after exact-group consolidation: {unique_after_exact:,}",
            f"- Groups where every record shares one DOI: {len(exact_classes['shared_doi']):,}",
            f"- Exact-title groups with DOI present in only some records: {len(exact_classes['exact_title_with_partial_doi']):,}",
            f"- Exact-title groups without DOI: {len(exact_classes['exact_title_without_doi']):,}",
            f"- Same normalized title with conflicting DOI groups: {len(analysis['title_conflicts']):,}",
            f"- Near-title candidate pairs requiring human review: {len(near_title_candidates):,}",
            "",
            "Exact matching uses normalized DOI first and exact normalized title second. "
            "A title group with more than one distinct DOI is not automatically merged.",
            "",
            "## Frozen duplicate review result",
            "",
            f"- Confirmed exact duplicate groups: {resolution['confirmed_exact_duplicate_groups']:,}",
            f"- Duplicate records removed from exact groups: {resolution['exact_duplicate_records_removed']:,}",
            f"- Additional duplicate preprint records removed within version-conflict groups: {resolution['preprint_duplicate_records_removed']:,}",
            f"- Total duplicate records removed: {resolution['duplicate_records_removed']:,}",
            f"- Superseded preprint records removed for other reasons: {resolution['superseded_preprint_records_removed']:,}",
            f"- Records screened on title and abstract: {resolution['records_for_screening']:,}",
            "",
            "Five no-DOI groups were confirmed as cross-database duplicates. "
            "Eight no-DOI groups were kept separate because their volume, ISBN, year, or proceedings identity differed. "
            "Two duplicate preprint records inside title-conflict groups were consolidated before their retained preprint versions were removed in favor of formal publications.",
            "",
            "## Duplicate source patterns",
            "",
            "| Sources in group | Groups |",
            "|:--|--:|",
        ]
    )
    for pattern, count in analysis["source_patterns"].most_common():
        lines.append(f"| {pattern} | {count:,} |")
    lines.extend(
        [
            "",
            "## Author-approved screening protocol",
            "",
            "- Include English-language records only.",
            "- Apply no starting-year restriction and use 2026-08-28 as the search cutoff.",
            "- Retain the formal publication when a preprint and formal version coexist.",
            "- Retain a high-relevance arXiv paper only when no formal version exists, and mark it as a preprint.",
            "- Allow workshop papers but mark them explicitly.",
            "- Use technical documents, standards, and industry reports only as enabling or supporting evidence.",
            "- Use reviews and surveys for background and citation chasing, not core intervention synthesis.",
            "- Keep transfer and horizon evidence in a separate supplementary discovery flow.",
            "- Screening was performed by one reviewer.",
            "- Do not report independent dual screening, disagreement resolution, or inter-reviewer agreement.",
            "",
            "## Methodological status",
            "",
            "The five core exports now support the PRISMA Identification total of 4,986 records. "
            "The completed duplicate review supports removal of 512 duplicate records and 10 superseded preprint records, leaving 4,464 records for title and abstract screening.",
            "",
            "The author confirmed that one reviewer performed screening and that the current 80-record survey corpus is the retained endpoint. "
            "Because no historical stage-by-stage exclusion ledger exists, the endpoint may be used to reconstruct the number not retained, but it cannot recover how many exclusions occurred at title and abstract review versus full-text assessment.",
            "",
        ]
    )
    (OUTPUT / "PRISMA_CORE_EXACT_DEDUP_AUDIT.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records = load_acm() + load_ieee() + load_scopus() + load_dblp() + load_arxiv()
    expected = {
        "ACM Digital Library": 3327,
        "IEEE Xplore": 668,
        "Scopus": 773,
        "DBLP": 130,
        "arXiv": 88,
    }
    actual = Counter(record["source"] for record in records)
    if actual != expected:
        raise ValueError(f"Unexpected source counts: {dict(actual)}")
    if any(not record["title"] for record in records):
        raise ValueError("At least one imported record has no title")

    analysis = analyze(records)
    near_title_candidates = find_near_title_candidates(records, analysis["components"])
    exact_classes = classify_exact_groups(analysis["duplicate_groups"])
    resolution = resolve_duplicate_review(
        records, analysis, near_title_candidates, exact_classes
    )
    (OUTPUT / "core_records_normalized.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT / "exact_duplicate_groups.json").write_text(
        json.dumps(analysis["duplicate_groups"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT / "title_conflict_groups.json").write_text(
        json.dumps(analysis["title_conflicts"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT / "near_title_candidates.json").write_text(
        json.dumps(near_title_candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT / "exact_title_without_doi_groups.json").write_text(
        json.dumps(exact_classes["exact_title_without_doi"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT / "duplicate_review_resolution.json").write_text(
        json.dumps(resolution, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_manual_review(exact_classes, analysis["title_conflicts"], near_title_candidates)
    write_report(
        records, analysis, near_title_candidates, exact_classes, resolution
    )

    removable = sum(group["record_count"] - 1 for group in analysis["duplicate_groups"])
    print(f"records={len(records)}")
    print(f"exact_duplicate_groups={len(analysis['duplicate_groups'])}")
    print(f"candidate_duplicates={removable}")
    print(f"remaining_after_exact={len(records) - removable}")
    print(f"title_conflicts={len(analysis['title_conflicts'])}")
    print(f"near_title_candidates={len(near_title_candidates)}")
    print(f"exact_title_without_doi_groups={len(exact_classes['exact_title_without_doi'])}")
    print(f"duplicate_records_removed={resolution['duplicate_records_removed']}")
    print(
        "superseded_preprint_records_removed="
        f"{resolution['superseded_preprint_records_removed']}"
    )
    print(f"records_for_screening={resolution['records_for_screening']}")


if __name__ == "__main__":
    main()
