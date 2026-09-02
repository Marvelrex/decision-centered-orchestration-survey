# PRISMA Core Export and Exact-Deduplication Audit

## Identification input

| Source | Imported records |
|:--|--:|
| ACM Digital Library | 3,327 |
| DBLP | 130 |
| IEEE Xplore | 668 |
| Scopus | 773 |
| arXiv | 88 |
| Total | 4,986 |

## Search evidence status

The ACM Digital Library, IEEE Xplore, and Scopus evidence pages record each exact query, search date, field scope, filter status, and database-specific raw hit count. The updated IEEE page shows `Showing 1-100 of 668 results`, which identifies 668 total hits while displaying records 1 through 100 on the current page.

## Field completeness

| Source | Title | Authors | Year | Venue | DOI | URL | Abstract | Keywords |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| ACM Digital Library | 3,327 | 2,695 | 3,327 | 2,695 | 2,591 | 2,629 | 2,816 | 2,234 |
| DBLP | 130 | 130 | 130 | 130 | 128 | 130 | 0 | 0 |
| IEEE Xplore | 668 | 668 | 668 | 668 | 649 | 668 | 668 | 650 |
| Scopus | 773 | 677 | 773 | 773 | 655 | 773 | 773 | 673 |
| arXiv | 88 | 88 | 88 | 0 | 21 | 88 | 88 | 88 |

## Exact duplicate audit

- Exact duplicate groups: 462
- Records contained in those groups: 982
- Candidate duplicate records removable after group review: 520
- Records remaining after exact-group consolidation: 4,466
- Groups where every record shares one DOI: 412
- Exact-title groups with DOI present in only some records: 37
- Exact-title groups without DOI: 13
- Same normalized title with conflicting DOI groups: 18
- Near-title candidate pairs requiring human review: 8

Exact matching uses normalized DOI first and exact normalized title second. A title group with more than one distinct DOI is not automatically merged.

## Frozen duplicate review result

- Confirmed exact duplicate groups: 454
- Duplicate records removed from exact groups: 510
- Additional duplicate preprint records removed within version-conflict groups: 2
- Total duplicate records removed: 512
- Superseded preprint records removed for other reasons: 10
- Records entering retrospective screening: 4,464

Five no-DOI groups were confirmed as cross-database duplicates. Eight no-DOI groups were kept separate because their volume, ISBN, year, or proceedings identity differed. Two duplicate preprint records inside title-conflict groups were consolidated before their retained preprint versions were removed in favor of formal publications.

## Duplicate source patterns

| Sources in group | Groups |
|:--|--:|
| IEEE Xplore + Scopus | 326 |
| ACM Digital Library + Scopus | 35 |
| DBLP + IEEE Xplore + Scopus | 22 |
| IEEE Xplore + Scopus + arXiv | 17 |
| Scopus + arXiv | 11 |
| DBLP + Scopus | 10 |
| Scopus | 8 |
| ACM Digital Library + DBLP + Scopus | 6 |
| IEEE Xplore + arXiv | 5 |
| ACM Digital Library + Scopus + arXiv | 4 |
| DBLP + IEEE Xplore | 4 |
| ACM Digital Library + IEEE Xplore | 4 |
| ACM Digital Library + IEEE Xplore + Scopus | 2 |
| DBLP + arXiv | 2 |
| ACM Digital Library | 2 |
| DBLP + IEEE Xplore + Scopus + arXiv | 1 |
| ACM Digital Library + DBLP + Scopus + arXiv | 1 |
| ACM Digital Library + DBLP | 1 |
| ACM Digital Library + arXiv | 1 |

## Author-approved screening protocol

- Include English-language records only.
- Apply no starting-year restriction and use 2026-08-28 as the search cutoff.
- Retain the formal publication when a preprint and formal version coexist.
- Retain a high-relevance arXiv paper only when no formal version exists, and mark it as a preprint.
- Allow workshop papers but mark them explicitly.
- Use technical documents, standards, and industry reports only as enabling or supporting evidence.
- Use reviews and surveys for background and citation chasing, not core intervention synthesis.
- Keep transfer and horizon evidence in a separate supplementary discovery flow.
- Screening was performed by one reviewer.
- Do not report independent dual screening, disagreement resolution, or inter-reviewer agreement.

## Methodological status

The five core exports now support the PRISMA Identification total of 4,986 records. The completed duplicate review supports removal of 512 duplicate records and 10 superseded preprint records, leaving 4,464 records for retrospective screening.

The author confirmed that one reviewer performed screening and that the current 79-record survey corpus is the retained endpoint. Because no historical stage-by-stage exclusion ledger exists, the endpoint may be used to reconstruct the number not retained, but it cannot recover how many exclusions occurred at title and abstract review versus full-text assessment.
