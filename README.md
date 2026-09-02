# Screening and inclusion record

[![DOI](https://zenodo.org/badge/1354209033.svg)](https://doi.org/10.5281/zenodo.22243236)

Companion data for the survey *Sustainability-Aware Container Orchestration: A
Decision-Centered Survey of Signals, Mechanisms, and Actuation*.

This repository holds the full audit trail behind the Survey Methodology section
and Figure 1 of the paper: how the literature was identified, how every record
was screened, and how each included report maps back to the search that found
it. Every count printed in the paper can be recomputed from the files here.

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
| Included reports | 83 |
| Core interventions | 39 |

Title and abstract exclusions by primary reason:

| Reason | n |
|:--|--:|
| E1 no container or cloud-native orchestration relation | 1,632 |
| E4 review or non-primary research item | 837 |
| E3 no sustainability objective, signal, constraint, or outcome | 690 |
| E7 outside the core boundary, kept visible as supporting evidence | 667 |
| E2 no scheduling or resource-orchestration decision | 488 |
| E6 title and abstract metadata too thin to decide | 90 |
| E5 non-English record | 10 |

Of the 83 included reports, the five database exports reproduce 41 by DOI or
exact title, including 37 of the 39 core interventions. The other 42 were found
by reading the reference lists of the retrieved reports and of the prior surveys,
and by hand searching the venues that publish this work. Their analytical roles
show why the Boolean expression cannot return them.

| Of the 42 not reproduced | n |
|:--|--:|
| transfer evidence | 26 |
| horizon evidence | 9 |
| enabling infrastructure | 5 |
| core interventions | 2 |

Twenty-two of the 40 supporting records act on virtual machines, sites, or other
non-container targets, and 7 sit in frontier deployment settings, so no
adaptation of the query syntax matches them. The two core interventions among
the 42 are Google CICS and GreenWhisk. Per-record match
status and role are in `05_included_reconstruction/included_report_crosswalk.json`.

## Folder guide

- `01_search_strategy/` The search queries and per-database retrieval evidence in
  PRISMA-S form, plus the arXiv and DBLP result sets.
- `03_deduplication/` The exact-duplicate and near-title audits, the manual
  duplicate review, and the resolution that removes 512 duplicates and 10
  superseded preprints.
- `04_screening_ledger/` The 4,464-row screening ledger. One row per unique
  record, carrying its identifiers, its title and abstract decision, and its
  primary exclusion reason. Also the exclusion codebook, the pre-screen removal
  log, the automated suggestion drafts, and the decisions taken on them.
- `05_included_reconstruction/` The crosswalk of all 83 included report keys
  against the database exports, with match status, matched sources, retained
  version, and discovery route, plus the reconciliation result.
- `06_prisma_figure/` Figure 1 of the paper, in PDF, SVG, and PNG.
- `07_reproducibility/` The scripts that regenerate the ledger, the
  reconstruction, and the workbook, plus their tests.

## How screening was done

Automated title and abstract matching ordered the export and proposed one
primary exclusion reason per record. Every proposal was checked by hand before
it became a decision. Full-text assessment, evidence extraction, and analytical
role assignment were done by hand throughout. Screening was not duplicated, so
no inter-rater agreement statistic is available for this corpus.

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

Screening closed on 2026-08-30 with the corpus frozen. Ninety records marked
uncertain at the title and abstract stage were not pursued to full text and
remain excluded. Eight further candidates that passed the automated screen were
not assessed and remain excluded. See `CLOSURE_STATEMENT_2026-08-30.md`.

One report changed role after closure. Malla, Metsch, and Townend, *Power Aware
Cluster Orchestration: Taxonomy, Initial Results, and Challenges* (UCC 2026,
`10.1145/3773274.3774698`), is both a taxonomy and a scheduler extension. It is
treated as a prior survey and appears in the paper's comparison of related
surveys rather than among the interventions the paper surveys, so it is not one
of the 39 core interventions. This is why the corpus is 83 rather than the 84
recorded in the closure statement.
