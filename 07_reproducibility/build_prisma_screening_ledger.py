"""Build an auditable PRISMA screening ledger for the frozen core exports."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

import analyze_prisma_core as core
import build_prisma_reconstruction as reconstruction


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "generated_prisma_screening"

AUTOMATION_SUGGESTIONS = (
    "retain for author review",
    "exclude candidate",
    "supplementary evidence candidate",
    "insufficient metadata",
)

TITLE_ABSTRACT_DECISIONS = (
    "include for full text",
    "exclude",
    "uncertain",
)

TITLE_ABSTRACT_EXCLUSION_REASONS = (
    "E1 No container or cloud-native orchestration relation",
    "E2 No scheduling or resource-orchestration decision",
    "E3 No sustainability objective, signal, constraint, or outcome",
    "E4 Review or non-primary research item",
    "E5 Non-English record",
    "E6 Insufficient title or abstract information",
    "E7 Outside core synthesis but potentially useful as supporting evidence",
)

FULL_TEXT_STATUSES = (
    "sought",
    "retrieved",
    "not retrieved",
    "not applicable",
)

FULL_TEXT_DECISIONS = (
    "include",
    "exclude",
    "uncertain",
)

FULL_TEXT_EXCLUSION_REASONS = (
    "F1 No container or cloud-native orchestration relation",
    "F2 No scheduling or resource-orchestration decision",
    "F3 No sustainability objective, signal, constraint, or outcome",
    "F4 Review or non-primary research item",
    "F5 Insufficient technical detail for synthesis",
    "F6 Full text unavailable",
    "F7 Outside the predefined core synthesis boundary",
    "F8 Superseded or not an independent report",
)

PLATFORM_PATTERNS = (
    r"\bkubernetes\b",
    r"\bk8s\b",
    r"\bk3s\b",
    r"\bcontainer(?:s|ized|isation|ization)?\b",
    r"\bpod(?:s)?\b",
    r"\bdocker\b",
    r"\bcloud[ -]?native\b",
    r"\bmicroservice(?:s)?\b",
    r"\bserverless\b",
    r"\bfunction as a service\b",
    r"\bfaas\b",
)

DECISION_PATTERNS = (
    r"\bschedul\w*\b",
    r"\bplacement\b",
    r"\borchestrat\w*\b",
    r"\bautoscal\w*\b",
    r"\bauto-scal\w*\b",
    r"\bscaling\b",
    r"\bmigrat\w*\b",
    r"\ballocat\w*\b",
    r"\bprovision\w*\b",
    r"\bconsolidat\w*\b",
    r"\bdispatch\w*\b",
    r"\boffload\w*\b",
    r"\brout(?:e|ing)\b",
    r"\bload balanc\w*\b",
    r"\bresource management\b",
    r"\bresource selection\b",
)

SUSTAINABILITY_PATTERNS = (
    r"\bcarbon\w*\b",
    r"\bemission\w*\b",
    r"\benergy\b",
    r"\bpower\b",
    r"\brenewable\w*\b",
    r"\bsustainab\w*\b",
    r"\bgreen(?:er|ness)?\b",
    r"\belectricity\b",
    r"\benvironmental\b",
    r"\bwater\b",
    r"\bthermal\b",
    r"\bcooling\b",
    r"\bsolar\b",
    r"\bwind\b",
    r"\bwatt\w*\b",
)

STRICT_PLATFORM_PATTERNS = (
    r"\bkubernetes\b",
    r"\bk8s\b",
    r"\bk3s\b",
    r"\bcontainer(?:s|ized|isation|ization)?\b",
    r"\bpod(?:s)?\b",
    r"\bdocker\b",
    r"\bcloud[ -]?native\b",
    r"\b[a-z0-9-]*kube[a-z0-9-]*\b",
)

STRICT_DECISION_PATTERNS = (
    r"\bschedul\w*\b",
    r"\bplacement\b",
    r"\borchestrat\w*\b",
)

STRICT_SUSTAINABILITY_PATTERNS = (
    r"\bcarbon\w*\b",
    r"\bemission\w*\b",
    r"\brenewable\w*\b",
    r"\bsustainab\w*\b",
    r"\bgreen(?:er|ness)?\b",
    r"\belectricity\b",
    r"\benvironmental\b",
    r"\bsolar\b",
    r"\bwind\b",
)

DIRECT_CARBON_PATTERNS = (
    r"\bcarbon\w*\b",
    r"\bemission\w*\b",
)

TITLE_SCOPE_SUSTAINABILITY_PATTERNS = (
    *STRICT_SUSTAINABILITY_PATTERNS,
    r"\benergy\b",
    r"\bpower\b",
    r"\bthermal\b",
    r"\bcooling\b",
    r"\bwatt\w*\b",
)

TITLE_DOMAIN_EXCLUSION_PATTERNS = (
    r"\bcontainer terminal\b",
    r"\bcontainer shipping\b",
    r"\bmaritime\b",
    r"\bhydrodynamic\b",
    r"\breservoir\w*\b",
    r"\brailway\w*\b",
)

REVIEW_PATTERNS = (
    r"\bsystematic review\b",
    r"\bliterature review\b",
    r"\bsurvey of\b",
    r"\ba survey\b",
    r"\bmapping study\b",
    r"\bscoping review\b",
    r"\ba review\b",
)

NON_RESEARCH_PATTERNS = (
    r"^proceedings of\b",
    r"^proceedings$",
    r"^front matter\b",
    r"^preface\b",
    r"^editorial\b",
    r"^welcome message\b",
    r"^message from the\b",
    r"^call for papers\b",
)

NON_RESEARCH_SOURCE_TYPES = {
    "book",
    "conference review",
    "proceedings",
    "review",
}

SOURCE_PRIORITY = {
    "Scopus": 5,
    "IEEE Xplore": 4,
    "ACM Digital Library": 4,
    "arXiv": 3,
    "DBLP": 1,
}

CORE_INTERVENTION_CAP = 50
PROTECTED_CURRENT_CORE_CANDIDATES = 42
NEW_CORE_CANDIDATE_CAP = (
    CORE_INTERVENTION_CAP - PROTECTED_CURRENT_CORE_CANDIDATES
)

def load_raw_records():
    return (
        core.load_acm()
        + core.load_ieee()
        + core.load_scopus()
        + core.load_dblp()
        + core.load_arxiv()
    )


def load_scopus_languages():
    path = (
        core.NEW_EXPORTS
        / "Scopus"
        / "scopus_core_2026-08-28_all_773.csv"
    )
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        return {
            core.clean_text(row.get("EID")): core.clean_text(
                row.get("\u539f\u59cb\u6587\u732e\u8bed\u8a00")
            )
            for row in rows
        }


def is_preprint(record):
    combined = " ".join(
        (
            record.get("source", ""),
            record.get("source_id", ""),
            record.get("source_type", ""),
            record.get("doi", ""),
            record.get("venue", ""),
        )
    ).casefold()
    return (
        record.get("source") == "arXiv"
        or "journals/corr" in combined
        or "preprint" in combined
        or "10.48550/arxiv" in combined
    )


def representative_score(record):
    return (
        0 if is_preprint(record) else 100000,
        20000 if record.get("doi") else 0,
        min(len(record.get("abstract", "")), 10000),
        min(len(record.get("keywords", "")), 3000),
        1000 if record.get("url") else 0,
        500 if record.get("venue") else 0,
        SOURCE_PRIORITY.get(record.get("source"), 0),
        record.get("record_id", ""),
    )


def choose_representative(records):
    if not records:
        raise ValueError("Cannot choose a representative from an empty record set")
    return max(records, key=representative_score)


def compile_patterns(patterns):
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


PLATFORM_REGEXES = compile_patterns(PLATFORM_PATTERNS)
DECISION_REGEXES = compile_patterns(DECISION_PATTERNS)
SUSTAINABILITY_REGEXES = compile_patterns(SUSTAINABILITY_PATTERNS)
STRICT_PLATFORM_REGEXES = compile_patterns(STRICT_PLATFORM_PATTERNS)
STRICT_DECISION_REGEXES = compile_patterns(STRICT_DECISION_PATTERNS)
STRICT_SUSTAINABILITY_REGEXES = compile_patterns(
    STRICT_SUSTAINABILITY_PATTERNS
)
DIRECT_CARBON_REGEXES = compile_patterns(DIRECT_CARBON_PATTERNS)
TITLE_SCOPE_SUSTAINABILITY_REGEXES = compile_patterns(
    TITLE_SCOPE_SUSTAINABILITY_PATTERNS
)
TITLE_DOMAIN_EXCLUSION_REGEXES = compile_patterns(
    TITLE_DOMAIN_EXCLUSION_PATTERNS
)
REVIEW_REGEXES = compile_patterns(REVIEW_PATTERNS)
NON_RESEARCH_REGEXES = compile_patterns(NON_RESEARCH_PATTERNS)


def matched_terms(text, regexes):
    terms = []
    for regex in regexes:
        match = regex.search(text)
        if match:
            terms.append(match.group(0))
    return sorted(set(terms), key=str.casefold)


def title_looks_non_english(title):
    letters = [character for character in title if character.isalpha()]
    if not letters:
        return False
    non_latin = sum(
        ord(character) > 591
        for character in letters
    )
    return non_latin / len(letters) >= 0.15


def classify_publication_type(row):
    text = " ".join(
        (
            row.get("title", ""),
            row.get("venue", ""),
            row.get("source_type", ""),
        )
    ).casefold()
    if any(regex.search(text) for regex in REVIEW_REGEXES):
        return "review or survey"
    if row.get("source_type", "").strip().casefold() in NON_RESEARCH_SOURCE_TYPES:
        return "non-research item"
    if any(regex.search(row.get("title", "")) for regex in NON_RESEARCH_REGEXES):
        return "non-research item"
    if is_preprint(row):
        return "preprint"
    if "workshop" in text or "workshops" in text:
        return "workshop paper"
    return "formal publication or database record"


def suggest_screening(row):
    text = " ".join(
        value
        for value in (
            row.get("title", ""),
            row.get("abstract", ""),
            row.get("keywords", ""),
            row.get("venue", ""),
        )
        if value
    ).casefold()
    platform_terms = matched_terms(text, PLATFORM_REGEXES)
    decision_terms = matched_terms(text, DECISION_REGEXES)
    sustainability_terms = matched_terms(text, SUSTAINABILITY_REGEXES)
    publication_type = row["publication_type"]
    language = row["language"]
    has_abstract = bool(row.get("abstract"))
    known_endpoint = bool(row.get("current_corpus_cite_keys"))

    if known_endpoint:
        suggestion = "retain for author review"
        confidence = "high"
        reason = ""
        rationale = "Protected match to a report already held in the corpus."
    elif language and language.casefold() != "english":
        suggestion = "exclude candidate"
        confidence = "high"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[4]
        rationale = f"Database language metadata states {language}."
    elif title_looks_non_english(row.get("title", "")):
        suggestion = "exclude candidate"
        confidence = "medium"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[4]
        rationale = "The title contains a substantial non-Latin character signal."
    elif publication_type in {"review or survey", "non-research item"}:
        suggestion = "supplementary evidence candidate"
        confidence = "high"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[3]
        rationale = (
            "The record appears to be a review, survey, editorial, or proceedings-level item."
        )
    elif platform_terms and decision_terms and sustainability_terms:
        suggestion = "retain for author review"
        confidence = "high" if has_abstract else "medium"
        reason = ""
        rationale = "Platform, orchestration-decision, and sustainability signals are present."
    elif not row.get("title") or not has_abstract:
        suggestion = "insufficient metadata"
        confidence = "low"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[5]
        missing = "title" if not row.get("title") else "abstract"
        rationale = f"The database export does not provide a usable {missing}."
    elif platform_terms and decision_terms and not sustainability_terms:
        suggestion = "exclude candidate"
        confidence = "medium"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[2]
        rationale = "Platform and decision signals are present, but no sustainability signal was detected."
    elif platform_terms and sustainability_terms and not decision_terms:
        suggestion = "exclude candidate"
        confidence = "medium"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[1]
        rationale = "Platform and sustainability signals are present, but no orchestration decision was detected."
    elif decision_terms and sustainability_terms and not platform_terms:
        suggestion = "exclude candidate"
        confidence = "medium"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[0]
        rationale = "Decision and sustainability signals are present, but no container or cloud-native relation was detected."
    elif not platform_terms:
        suggestion = "exclude candidate"
        confidence = "high"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[0]
        rationale = "No container or cloud-native platform signal was detected in the title or abstract."
    elif not decision_terms:
        suggestion = "exclude candidate"
        confidence = "high"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[1]
        rationale = "No scheduling or resource-orchestration decision signal was detected."
    else:
        suggestion = "exclude candidate"
        confidence = "high"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[2]
        rationale = "No sustainability objective, signal, constraint, or outcome was detected."

    return {
        "automation_suggestion": suggestion,
        "automation_confidence": confidence,
        "suggested_primary_reason": reason,
        "automation_rationale": rationale,
        "platform_signal": ", ".join(platform_terms),
        "decision_signal": ", ".join(decision_terms),
        "sustainability_signal": ", ".join(sustainability_terms),
    }


def compact_removal(record, removal_type, reason, group_id, retained_record_id):
    return {
        "record_id": record["record_id"],
        "source": record["source"],
        "source_id": record["source_id"],
        "title": record["title"],
        "year": record["year"],
        "doi": record["doi"],
        "url": record["url"],
        "removal_type": removal_type,
        "removal_reason": reason,
        "review_group_id": group_id,
        "retained_record_id": retained_record_id,
    }


def build_pre_screen_corpus(raw_records):
    by_id = {record["record_id"]: record for record in raw_records}
    analysis = core.analyze(raw_records)
    near = core.find_near_title_candidates(raw_records, analysis["components"])
    exact_classes = core.classify_exact_groups(analysis["duplicate_groups"])
    resolution = core.resolve_duplicate_review(
        raw_records, analysis, near, exact_classes
    )
    confirmed_exact_groups = (
        exact_classes["shared_doi"]
        + exact_classes["exact_title_with_partial_doi"]
        + [
            group
            for group in exact_classes["exact_title_without_doi"]
            if group["group_id"] in core.CONFIRMED_NO_DOI_DUPLICATE_GROUP_IDS
        ]
    )

    removals = []
    removed_ids = set()
    resolution_map = {record_id: record_id for record_id in by_id}
    consolidated_members = {
        record_id: {record_id} for record_id in by_id
    }

    def remove_record(record_id, removal_type, reason, group_id, retained_id):
        if record_id in removed_ids:
            raise ValueError(f"Record removed more than once: {record_id}")
        removed_ids.add(record_id)
        resolution_map[record_id] = retained_id
        consolidated_members.setdefault(retained_id, {retained_id}).update(
            consolidated_members.get(record_id, {record_id})
        )
        removals.append(
            compact_removal(
                by_id[record_id],
                removal_type,
                reason,
                group_id,
                retained_id,
            )
        )

    for group in confirmed_exact_groups:
        members = [by_id[member["record_id"]] for member in group["members"]]
        representative = choose_representative(members)
        representative_id = representative["record_id"]
        for member in members:
            if member["record_id"] == representative_id:
                continue
            remove_record(
                member["record_id"],
                "duplicate",
                "Confirmed exact DOI or publication-identity duplicate",
                group["group_id"],
                representative_id,
            )

    conflict_by_id = {group["group_id"]: group for group in analysis["title_conflicts"]}
    for group_id in sorted(core.PREPRINT_DUPLICATE_CONFLICT_IDS):
        group = conflict_by_id[group_id]
        candidates = [
            by_id[member["record_id"]]
            for member in group["members"]
            if member["record_id"] not in removed_ids
            and is_preprint(by_id[member["record_id"]])
        ]
        if len(candidates) != 2:
            raise ValueError(
                f"Expected two remaining duplicate preprints in {group_id}, found {len(candidates)}"
            )
        representative = choose_representative(candidates)
        duplicate = next(
            candidate
            for candidate in candidates
            if candidate["record_id"] != representative["record_id"]
        )
        remove_record(
            duplicate["record_id"],
            "duplicate",
            "Two database records describe the same preprint",
            group_id,
            representative["record_id"],
        )

    for group_id in sorted(core.SUPERSEDED_PREPRINT_CONFLICT_IDS):
        group = conflict_by_id[group_id]
        remaining = [
            by_id[member["record_id"]]
            for member in group["members"]
            if member["record_id"] not in removed_ids
        ]
        preprints = [record for record in remaining if is_preprint(record)]
        formal = [record for record in remaining if not is_preprint(record)]
        if len(preprints) != 1 or not formal:
            raise ValueError(
                f"Version review mismatch in {group_id}: preprints={len(preprints)}, formal={len(formal)}"
            )
        formal_representative = choose_representative(formal)
        remove_record(
            preprints[0]["record_id"],
            "superseded preprint",
            "Formal publication retained in preference to the preprint",
            group_id,
            formal_representative["record_id"],
        )

    near_by_id = {candidate["candidate_id"]: candidate for candidate in near}
    for candidate_id in sorted(core.SUPERSEDED_PREPRINT_NEAR_IDS):
        candidate = near_by_id[candidate_id]
        members = candidate["left"]["members"] + candidate["right"]["members"]
        remaining = [
            by_id[member["record_id"]]
            for member in members
            if member["record_id"] not in removed_ids
        ]
        preprints = [record for record in remaining if is_preprint(record)]
        formal = [record for record in remaining if not is_preprint(record)]
        if len(preprints) != 1 or not formal:
            raise ValueError(
                f"Near-title version review mismatch in {candidate_id}: preprints={len(preprints)}, formal={len(formal)}"
            )
        formal_representative = choose_representative(formal)
        remove_record(
            preprints[0]["record_id"],
            "superseded preprint",
            "Formal publication retained in preference to the near-title preprint",
            candidate_id,
            formal_representative["record_id"],
        )

    def resolve_record_id(record_id):
        visited = set()
        while resolution_map[record_id] != record_id:
            if record_id in visited:
                raise ValueError("Cycle detected in pre-screen resolution map")
            visited.add(record_id)
            record_id = resolution_map[record_id]
        return record_id

    for record_id in resolution_map:
        resolution_map[record_id] = resolve_record_id(record_id)

    for removal in removals:
        removal["retained_record_id"] = resolution_map[
            removal["retained_record_id"]
        ]

    duplicate_count = sum(
        removal["removal_type"] == "duplicate" for removal in removals
    )
    superseded_count = sum(
        removal["removal_type"] == "superseded preprint" for removal in removals
    )
    if duplicate_count != resolution["duplicate_records_removed"]:
        raise ValueError(
            f"Duplicate materialization mismatch: {duplicate_count}"
        )
    if superseded_count != resolution["superseded_preprint_records_removed"]:
        raise ValueError(
            f"Superseded-preprint materialization mismatch: {superseded_count}"
        )

    retained = [
        record for record in raw_records if record["record_id"] not in removed_ids
    ]
    if len(retained) != resolution["records_for_screening"]:
        raise ValueError(f"Retained screening count mismatch: {len(retained)}")

    return {
        "retained": retained,
        "removals": sorted(
            removals,
            key=lambda row: (row["removal_type"], row["review_group_id"], row["record_id"]),
        ),
        "resolution": resolution,
        "resolution_map": resolution_map,
        "consolidated_members": consolidated_members,
        "by_id": by_id,
    }


def map_current_corpus(retained, resolution_map):
    retained_ids = {record["record_id"] for record in retained}
    raw_by_source_identity = {
        (record["source"], record["source_id"]): record["record_id"]
        for record in load_raw_records()
    }
    endpoint_map = defaultdict(list)
    confirmed_rows = [
        row
        for row in reconstruction.reconstruct()
        if row["search_match_status"] == "confirmed"
    ]
    for endpoint in confirmed_rows:
        retained_record = endpoint["retained_record"]
        raw_id = raw_by_source_identity.get(
            (retained_record["source"], retained_record["source_id"])
        )
        surviving = []
        if raw_id:
            resolved_id = resolution_map[raw_id]
            if resolved_id in retained_ids:
                surviving = [resolved_id]
        if len(surviving) != 1:
            raise ValueError(
                f"Included-report mapping is not unique for {endpoint['cite_key']}: {surviving}"
            )
        endpoint_map[surviving[0]].append(
            {
                "cite_key": endpoint["cite_key"],
                "analytical_role": endpoint["analytical_role"],
            }
        )
    if len(endpoint_map) != 42:
        raise ValueError(f"Expected 42 database-matched endpoint rows, found {len(endpoint_map)}")
    return endpoint_map


def best_field(records, field):
    values = [record.get(field, "") for record in records if record.get(field, "")]
    if not values:
        return ""
    return max(values, key=lambda value: (len(value), value))


def build_ledger_package():
    raw_records = load_raw_records()
    materialized = build_pre_screen_corpus(raw_records)
    retained = materialized["retained"]
    by_id = materialized["by_id"]
    endpoint_map = map_current_corpus(
        retained, materialized["resolution_map"]
    )
    scopus_languages = load_scopus_languages()
    rows = []
    for index, representative in enumerate(
        sorted(
            retained,
            key=lambda row: (
                row["normalized_title"],
                row["year"],
                row["record_id"],
            ),
        ),
        start=1,
    ):
        representative_id = representative["record_id"]
        member_ids = sorted(
            materialized["consolidated_members"].get(
                representative_id, {representative_id}
            )
        )
        members = [by_id[member_id] for member_id in member_ids]
        sources = sorted({member["source"] for member in members})
        source_ids = sorted({member["source_id"] for member in members})
        source_urls = sorted({member["url"] for member in members if member["url"]})
        language_values = sorted(
            {
                scopus_languages.get(member["source_id"], "")
                for member in members
                if member["source"] == "Scopus"
                and scopus_languages.get(member["source_id"], "")
            }
        )
        language = language_values[0] if len(language_values) == 1 else ""
        endpoints = endpoint_map.get(representative_id, [])
        row = {
            "screening_id": f"SCR-{index:04d}",
            "representative_record_id": representative_id,
            "member_record_ids": member_ids,
            "title": best_field(members, "title"),
            "abstract": best_field(members, "abstract"),
            "authors": best_field(members, "authors"),
            "year": best_field(members, "year"),
            "venue": best_field(members, "venue"),
            "doi": best_field(members, "doi"),
            "source_type": best_field(members, "source_type"),
            "sources": sources,
            "source_ids": source_ids,
            "source_urls": source_urls,
            "keywords": best_field(members, "keywords"),
            "language": language,
            "publication_type": "",
            "current_corpus_cite_keys": sorted(
                endpoint["cite_key"] for endpoint in endpoints
            ),
            "current_corpus_roles": sorted(
                endpoint["analytical_role"] for endpoint in endpoints
            ),
            "reviewer_title_abstract_decision": "",
            "reviewer_exclusion_reason": "",
            "reviewer_notes": "",
            "full_text_status": "",
            "full_text_decision": "",
            "full_text_exclusion_reason": "",
            "full_text_notes": "",
        }
        row["publication_type"] = classify_publication_type(row)
        row.update(suggest_screening(row))
        rows.append(row)

    summary = {
        "search_cutoff": "2026-08-28",
        "screening_reviewers": 1,
        "records_identified": len(raw_records),
        "duplicate_records_removed": sum(
            row["removal_type"] == "duplicate"
            for row in materialized["removals"]
        ),
        "superseded_preprint_records_removed": sum(
            row["removal_type"] == "superseded preprint"
            for row in materialized["removals"]
        ),
        "records_for_screening": len(rows),
        "database_matched_current_corpus_records": sum(
            bool(row["current_corpus_cite_keys"]) for row in rows
        ),
        "automation_suggestion_counts": dict(
            sorted(Counter(row["automation_suggestion"] for row in rows).items())
        ),
        "automation_confidence_counts": dict(
            sorted(Counter(row["automation_confidence"] for row in rows).items())
        ),
        "language_metadata_counts": dict(
            sorted(Counter(row["language"] or "not recorded" for row in rows).items())
        ),
        "author_confirmed_title_abstract_decisions": 0,
        "author_confirmed_full_text_decisions": 0,
        "stage_specific_prisma_counts_ready": False,
    }
    codebook = {
        "automation_suggestions": list(AUTOMATION_SUGGESTIONS),
        "title_abstract_decisions": list(TITLE_ABSTRACT_DECISIONS),
        "title_abstract_exclusion_reasons": list(
            TITLE_ABSTRACT_EXCLUSION_REASONS
        ),
        "full_text_statuses": list(FULL_TEXT_STATUSES),
        "full_text_decisions": list(FULL_TEXT_DECISIONS),
        "full_text_exclusion_reasons": list(FULL_TEXT_EXCLUSION_REASONS),
        "decision_ownership": (
            "Automation suggestions support prioritization only. "
            "The single human reviewer must complete the reviewer and full-text fields."
        ),
    }
    return {
        "records": rows,
        "pre_screen_removals": materialized["removals"],
        "summary": summary,
        "codebook": codebook,
    }


def title_abstract_signals(row):
    text = " ".join(
        value
        for value in (row.get("title", ""), row.get("abstract", ""))
        if value
    ).casefold()
    return {
        "platform": matched_terms(text, PLATFORM_REGEXES),
        "decision": matched_terms(text, DECISION_REGEXES),
        "sustainability": matched_terms(text, SUSTAINABILITY_REGEXES),
    }


def strict_title_abstract_signals(row):
    title = row.get("title", "").casefold()
    abstract = row.get("abstract", "").casefold()
    combined = f"{title} {abstract}".strip()
    return {
        "title_platform": matched_terms(title, STRICT_PLATFORM_REGEXES),
        "title_decision": matched_terms(title, STRICT_DECISION_REGEXES),
        "title_sustainability": matched_terms(
            title, STRICT_SUSTAINABILITY_REGEXES
        ),
        "title_scope_sustainability": matched_terms(
            title, TITLE_SCOPE_SUSTAINABILITY_REGEXES
        ),
        "title_direct_carbon": matched_terms(title, DIRECT_CARBON_REGEXES),
        "title_domain_exclusion": matched_terms(
            title, TITLE_DOMAIN_EXCLUSION_REGEXES
        ),
        "combined_platform": matched_terms(combined, STRICT_PLATFORM_REGEXES),
        "combined_decision": matched_terms(combined, STRICT_DECISION_REGEXES),
        "combined_sustainability": matched_terms(
            combined, STRICT_SUSTAINABILITY_REGEXES
        ),
        "combined_direct_carbon": matched_terms(
            combined, DIRECT_CARBON_REGEXES
        ),
    }


def is_strict_new_core_candidate(row, signals):
    language = row.get("language", "")
    return (
        not row.get("current_corpus_cite_keys")
        and bool(row.get("title"))
        and bool(row.get("abstract"))
        and row.get("publication_type")
        not in {"review or survey", "non-research item"}
        and (not language or language.casefold() == "english")
        and not title_looks_non_english(row.get("title", ""))
        and not signals["title_domain_exclusion"]
        and bool(signals["title_platform"])
        and bool(signals["title_decision"])
        and bool(signals["title_scope_sustainability"])
        and bool(signals["combined_platform"])
        and bool(signals["combined_decision"])
        and bool(signals["combined_sustainability"])
    )


def strict_core_relevance_score(row, signals):
    title_group_count = sum(
        bool(signals[name])
        for name in (
            "title_platform",
            "title_decision",
            "title_scope_sustainability",
        )
    )
    publication_score = {
        "formal publication or database record": 3,
        "workshop paper": 2,
        "preprint": 1,
    }.get(row.get("publication_type", ""), 0)
    return (
        title_group_count * 1000
        + 350 * bool(signals["title_direct_carbon"])
        + 100 * bool(signals["combined_direct_carbon"])
        + 20 * min(len(signals["combined_platform"]), 5)
        + 20 * min(len(signals["combined_decision"]), 5)
        + 20 * min(len(signals["combined_sustainability"]), 5)
        + 10 * publication_score
    )


def strict_candidate_sort_key(row, signals):
    year_match = re.search(r"\b(?:19|20)\d{2}\b", str(row.get("year", "")))
    year = int(year_match.group(0)) if year_match else 0
    return (
        -strict_core_relevance_score(row, signals),
        -year,
        row.get("title", "").casefold(),
        row.get("screening_id", ""),
    )


def automated_title_abstract_decision(row):
    signals = title_abstract_signals(row)
    publication_type = row.get("publication_type", "")
    language = row.get("language", "")
    known_endpoint = bool(row.get("current_corpus_cite_keys"))

    if known_endpoint:
        decision = "include for full text"
        reason = ""
        rationale = "Protected match to a report already held in the corpus."
    elif language and language.casefold() != "english":
        decision = "exclude"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[4]
        rationale = f"Database language metadata states {language}."
    elif title_looks_non_english(row.get("title", "")):
        decision = "exclude"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[4]
        rationale = "The title contains a substantial non-Latin character signal."
    elif publication_type in {"review or survey", "non-research item"}:
        decision = "exclude"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[3]
        rationale = "The record is a review, survey, proceedings-level item, or other non-primary research item."
    elif not row.get("title") or not row.get("abstract"):
        decision = "uncertain"
        reason = ""
        rationale = "The database export does not provide both a usable title and abstract."
    elif not signals["platform"]:
        decision = "exclude"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[0]
        rationale = "No container or cloud-native relation was detected in the title or abstract."
    elif not signals["decision"]:
        decision = "exclude"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[1]
        rationale = "No scheduling or resource-orchestration decision was detected in the title or abstract."
    elif not signals["sustainability"]:
        decision = "exclude"
        reason = TITLE_ABSTRACT_EXCLUSION_REASONS[2]
        rationale = "No sustainability relation was detected in the title or abstract."
    else:
        decision = "include for full text"
        reason = ""
        rationale = "The title or abstract contains platform, orchestration-decision, and sustainability signals."

    return {
        "decision": decision,
        "reason": reason,
        "rationale": rationale,
        "signals": signals,
    }


def apply_authorized_abstract_screening(package):
    screened = deepcopy(package)
    results = {}
    strict_signals_by_id = {}
    strict_candidates = []

    def record_identity(row):
        return (
            row.get("screening_id")
            or row.get("representative_record_id")
            or "|".join(
                (
                    row.get("title", ""),
                    str(row.get("year", "")),
                    row.get("doi", ""),
                )
            )
        )

    for row in screened["records"]:
        identity = record_identity(row)
        result = automated_title_abstract_decision(row)
        strict_signals = strict_title_abstract_signals(row)
        results[identity] = result
        strict_signals_by_id[identity] = strict_signals
        if (
            result["decision"] == "include for full text"
            and is_strict_new_core_candidate(row, strict_signals)
        ):
            strict_candidates.append(row)

    ranked_candidates = sorted(
        strict_candidates,
        key=lambda row: strict_candidate_sort_key(
            row, strict_signals_by_id[record_identity(row)]
        ),
    )
    rank_by_id = {
        record_identity(row): index
        for index, row in enumerate(ranked_candidates, start=1)
    }
    selected_new_ids = {
        record_identity(row)
        for row in ranked_candidates[:NEW_CORE_CANDIDATE_CAP]
    }

    for row in screened["records"]:
        identity = record_identity(row)
        result = results[identity]
        strict_signals = strict_signals_by_id[identity]
        decision = result["decision"]
        reason = result["reason"]
        rationale = result["rationale"]
        strict_candidate = identity in rank_by_id

        if row.get("current_corpus_cite_keys"):
            scope_status = "protected current core candidate"
        elif identity in selected_new_ids:
            decision = "include for full text"
            reason = ""
            scope_status = "selected new core candidate"
            rationale = (
                "The record meets the strict direct-signal boundary and ranks "
                f"{rank_by_id[identity]} within the {NEW_CORE_CANDIDATE_CAP}-paper new-candidate cap."
            )
        elif result["decision"] == "include for full text":
            decision = "exclude"
            reason = TITLE_ABSTRACT_EXCLUSION_REASONS[6]
            if strict_candidate:
                scope_status = "strongly relevant supporting evidence"
                rationale = (
                    "The record meets the strict direct-signal boundary but ranks "
                    f"{rank_by_id[identity]} outside the {NEW_CORE_CANDIDATE_CAP}-paper new-candidate cap."
                )
            else:
                scope_status = "supporting evidence outside strict core boundary"
                rationale = (
                    "The record is broadly relevant but does not meet the stricter "
                    "direct-signal boundary for the capped core synthesis."
                )
        elif decision == "uncertain":
            scope_status = "unresolved metadata"
        else:
            scope_status = "not eligible for strict core synthesis"

        row["reviewer_title_abstract_decision"] = decision
        row["reviewer_exclusion_reason"] = reason
        row["reviewer_notes"] = (
            "Author-authorized automated title and abstract keyword screening "
            "on 2026-08-29. "
            f"{rationale} "
            "Single-reviewer verification remains required."
        )
        row["platform_signal"] = ", ".join(result["signals"]["platform"])
        row["decision_signal"] = ", ".join(result["signals"]["decision"])
        row["sustainability_signal"] = ", ".join(
            result["signals"]["sustainability"]
        )
        row["automation_rationale"] = rationale
        row["strict_core_candidate"] = strict_candidate
        row["strict_core_rank"] = rank_by_id.get(identity, "")
        row["strict_core_relevance_score"] = (
            strict_core_relevance_score(row, strict_signals)
            if strict_candidate
            else ""
        )
        row["core_scope_status"] = scope_status
        if decision == "include for full text":
            row["automation_suggestion"] = "retain for author review"
            row["automation_confidence"] = (
                "high" if row.get("abstract") else "medium"
            )
            row["suggested_primary_reason"] = ""
        elif decision == "exclude":
            row["automation_suggestion"] = (
                "supplementary evidence candidate"
                if reason
                in {
                    TITLE_ABSTRACT_EXCLUSION_REASONS[3],
                    TITLE_ABSTRACT_EXCLUSION_REASONS[6],
                }
                else "exclude candidate"
            )
            row["automation_confidence"] = "high"
            row["suggested_primary_reason"] = reason
        else:
            row["automation_suggestion"] = "insufficient metadata"
            row["automation_confidence"] = "low"
            row["suggested_primary_reason"] = TITLE_ABSTRACT_EXCLUSION_REASONS[5]

    summary = screened["summary"]
    summary["auto_title_abstract_screening_authorized"] = True
    summary["auto_title_abstract_screening_date"] = "2026-08-29"
    summary["core_intervention_cap"] = CORE_INTERVENTION_CAP
    summary["protected_current_core_candidates"] = sum(
        bool(row["current_corpus_cite_keys"]) for row in screened["records"]
    )
    summary["new_core_candidate_cap"] = NEW_CORE_CANDIDATE_CAP
    summary["strict_new_candidate_pool"] = len(ranked_candidates)
    summary["selected_new_core_candidates"] = len(selected_new_ids)
    summary["auto_title_abstract_decision_counts"] = dict(
        sorted(
            Counter(
                row["reviewer_title_abstract_decision"]
                for row in screened["records"]
            ).items()
        )
    )
    summary["auto_title_abstract_reason_counts"] = dict(
        sorted(
            Counter(
                row["reviewer_exclusion_reason"]
                for row in screened["records"]
                if row["reviewer_exclusion_reason"]
            ).items()
        )
    )
    summary["automation_suggestion_counts"] = dict(
        sorted(
            Counter(
                row["automation_suggestion"] for row in screened["records"]
            ).items()
        )
    )
    summary["automation_confidence_counts"] = dict(
        sorted(
            Counter(
                row["automation_confidence"] for row in screened["records"]
            ).items()
        )
    )
    summary["stage_specific_prisma_counts_ready"] = False
    screened["codebook"]["decision_ownership"] = (
        "The author authorized deterministic title and abstract keyword screening "
        "and a 50-paper core-intervention scope cap on 2026-08-29. The single "
        "reviewer retains responsibility for verification and all full-text decisions."
    )
    return screened


def csv_value(value):
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"Cannot write an empty CSV: {path}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {name: csv_value(row.get(name, "")) for name in fieldnames}
            )


def write_outputs(package):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "screening_records.json").write_text(
        json.dumps(package["records"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_csv(OUTPUT / "screening_records.csv", package["records"])
    (OUTPUT / "pre_screen_removals.json").write_text(
        json.dumps(package["pre_screen_removals"], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_csv(
        OUTPUT / "pre_screen_removals.csv",
        package["pre_screen_removals"],
    )
    (OUTPUT / "screening_codebook.json").write_text(
        json.dumps(package["codebook"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT / "suggestion_summary.json").write_text(
        json.dumps(package["summary"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_auto_screened_outputs(package):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "screening_records_auto_screened.json").write_text(
        json.dumps(package["records"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_csv(
        OUTPUT / "screening_records_auto_screened.csv",
        package["records"],
    )
    (OUTPUT / "auto_screening_summary.json").write_text(
        json.dumps(package["summary"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main():
    package = build_ledger_package()
    write_outputs(package)
    auto_package = apply_authorized_abstract_screening(package)
    write_auto_screened_outputs(auto_package)
    print(f"records_identified={package['summary']['records_identified']}")
    print(
        f"duplicate_records_removed={package['summary']['duplicate_records_removed']}"
    )
    print(
        "superseded_preprint_records_removed="
        f"{package['summary']['superseded_preprint_records_removed']}"
    )
    print(f"records_for_screening={package['summary']['records_for_screening']}")
    print(
        "database_matched_current_corpus_records="
        f"{package['summary']['database_matched_current_corpus_records']}"
    )
    for name, count in package["summary"]["automation_suggestion_counts"].items():
        print(f"suggestion_{name.replace(' ', '_')}={count}")
    for name, count in auto_package["summary"][
        "auto_title_abstract_decision_counts"
    ].items():
        print(f"auto_decision_{name.replace(' ', '_')}={count}")


if __name__ == "__main__":
    main()
