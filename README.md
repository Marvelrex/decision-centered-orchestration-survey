# Screening and inclusion record

[![DOI](https://zenodo.org/badge/1354209033.svg)](https://doi.org/10.5281/zenodo.22243236)

Companion data for the survey *Sustainability-Aware Container Orchestration: A
Decision-Centered Survey of Signals, Mechanisms, and Action*.

This repository holds the full audit trail behind the Survey Methodology section
and Figure 1 of the paper: how the literature was identified, how every record
was screened, and whether each included paper matches a record in the database exports. Every count printed in the paper can be recomputed from the files here.

## Headline numbers

| Stage | n |
|:--|--:|
| Records identified across five databases | 4,986 |
| ACM Digital Library | 3,327 |
| IEEE Xplore | 668 |
| Scopus | 773 |
| DBLP | 130 |
| arXiv | 88 |
| Duplicates removed before screening | 512 |
| Superseded preprints removed before screening | 10 |
| Records screened on title and abstract | 4,464 |
| Excluded on title and abstract | 4,414 |
| Reports assessed at full text | 50 |
| Included papers | 83 |
| Core papers | 39 |

Title and abstract exclusions by primary reason:

| Reason | n |
|:--|--:|
| E1 no container or cloud-native orchestration relation | 1,632 |
| E4 review or non-primary research item | 837 |
| E3 no sustainability objective, signal, constraint, or outcome | 690 |
| E7 sustainability-aware container orchestration is not the paper's main focus | 667 |
| E2 no scheduling or resource-orchestration decision | 488 |
| E6 title and abstract metadata too thin to decide | 90 |
| E5 non-English record | 10 |

Of the 83 included papers, the five database exports reproduce 41 by DOI,
exact title, or a verified title variant, including 37 of the 39 core papers.
The other 42 were found by reading the reference lists of the retrieved papers
and of the prior surveys, and by hand searching the venues that publish this
work. Their groups show why the Boolean expression cannot return them.

| Of the 42 not reproduced | n |
|:--|--:|
| Transferable mechanisms | 26 |
| Prototypes and emerging deployment settings | 9 |
| Supporting tools | 5 |
| Core papers | 2 |

Twenty-two of the 40 non-core papers act on virtual machines, sites, or other
non-container targets, and 7 study orbital deployment, so no adaptation of the
query syntax matches them. The two core papers among the 42 are Google CICS and
GreenWhisk. Per-paper match status and group are in
`05_included_reconstruction/included_report_crosswalk.json`.

The data files and scripts keep the original group keys. They map to the
paper's group names as follows.

| Key in the files | Group name in the paper |
|:--|:--|
| `core_intervention` | Core Papers |
| `transfer_evidence` | Transferable Mechanisms |
| `enabling_infrastructure` | Supporting Tools |
| `horizon_evidence` | Prototypes and Emerging Deployment Settings |

## Folder guide

- `01_search_strategy/` The search queries and per-database retrieval evidence in
  PRISMA-S form, plus the arXiv and DBLP result sets. The log inside is the
  2026-08-28 snapshot, written before the ACM Digital Library, IEEE Xplore, and
  Scopus exports were complete, so its export columns for those three databases
  read zero. The exports were completed afterwards, and the deduplication and
  screening files carry all 4,986 identified records.
- `03_deduplication/` The exact-duplicate and near-title audits, the manual
  duplicate review, and the resolution that removes 512 duplicates and 10
  superseded preprints.
- `04_screening_ledger/` The 4,464-row screening ledger. One row per unique
  record, carrying its identifiers, its title and abstract decision, and its
  primary exclusion reason. Also the exclusion codebook, the pre-screen removal
  log, the automated suggestion drafts, and the decisions taken on them.
- `05_included_reconstruction/` The crosswalk of all 83 included papers
  against the database exports, with match status, matched sources, retained
  version, and intended discovery route, plus the reconciliation result.
- `06_prisma_figure/` Figure 1 of the paper, in PDF, SVG, and PNG.
- `07_reproducibility/` The scripts that regenerate the ledger, the
  reconstruction, and the workbook, plus their tests.

## How screening was done

Automated title and abstract matching ordered the export and proposed one
primary exclusion reason per record. Every proposal was checked by hand before
it became a decision, and the `reviewer_notes` column of the ledger records
that check. The reproduction script regenerates the automated proposals. The
published ledger differs from that raw output in two places: the reviewer's
confirmation in `reviewer_notes`, and the 90 records with thin title and
abstract metadata, which the reviewer recorded as E6 exclusions. Full-text
assessment, labeling, and grouping by contribution were done by hand
throughout. Screening was not duplicated, so no inter-rater agreement
statistic is available for this corpus.

## What is not in this copy, and why

Two items in the working package are held back here.

- **The raw database exports.** The Scopus and IEEE terms of use do not permit
  redistributing harvested records. Bibliographic facts, that is titles, DOIs,
  venues, and years, are reproduced in the ledger instead.
- **The abstract and keyword columns of the ledger, and the Excel workbooks that
  carry the same text.** Same reason. The 3,878 abstracts came out of publisher
  exports. Every screening decision can still be traced from the title, DOI, and
  reason code that remain.

Anyone reproducing this work can re-fetch the abstracts from the DOIs in the
ledger under their own institutional access.

## Corpus closure

Screening closed on 2026-08-30 with the corpus frozen. Ninety records whose
title and abstract metadata were too thin to decide are recorded as E6
exclusions. Eight further candidates that passed the automated screen were
assessed at full text and did not enter the corpus. The ledger records the
full-text decision of each of the 50 records assessed. See
`CLOSURE_STATEMENT_2026-08-30.md`.

One report changed role after closure. Malla, Metsch, and Townend, *Power Aware
Cluster Orchestration: Taxonomy, Initial Results, and Challenges* (UCC 2026,
`10.1145/3773274.3774698`), is both a taxonomy and a scheduler extension. It is
treated as a prior survey and appears in the paper's comparison of related
surveys rather than among the papers the survey compares, so it is not one of
the 39 core papers. This is why the corpus is 83 rather than the 84 recorded in
the closure statement.
