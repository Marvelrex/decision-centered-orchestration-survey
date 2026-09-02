# PRISMA reconstruction result

## Counts supported directly by the retained evidence

| Stage | n | Evidence |
|:--|--:|:--|
| ACM Digital Library records retrieved | 3,327 | database export file |
| DBLP records retrieved | 130 | database export file |
| IEEE Xplore records retrieved | 668 | database export file |
| Scopus records retrieved | 773 | database export file |
| arXiv records retrieved | 88 | database export file |
| Records identified across the databases | 4,986 | sum of the five database exports |
| Duplicate records removed | 512 | DOI, normalized title, and manual group audit |
| Removed for other reasons | 10 | preprints superseded by a formal publication |
| Records screened on title and abstract | 4,464 | identified total minus the two removals above |
| Included reports matched in the five exports | 41 | DOI, exact title, or a verified title variant |
| Included reports not reproduced by the exports | 42 | the current 83 endpoints cross-checked against the exports |
| Included reports | 83 | the 83 unique cite keys in the survey |

## Flow diagram values

1. Records identified from databases: n = 4,986.
2. Duplicate records removed: n = 512.
3. Records removed for other reasons, superseded preprints: n = 10.
4. Records screened on title and abstract: n = 4,464.
5. Records not retained in the database-derived endpoint, aggregate only: n = 4,423.
6. Included reports matched directly to database exports: n = 41.
7. Included reports not reproduced by the five exports: n = 42.
8. Total included reports: n = 83.

Line 5 is an arithmetic difference. It only names the records in the screened set that did not reach the database-matched endpoint. The per-record ledger is 04_screening_ledger/screening_records_auto_screened.csv, where title and abstract exclusions carry one primary reason each from E1 to E7 and the full-text stage is recorded separately.

The 42 reports the exports do not reproduce were found by reading the reference lists of the retrieved reports and of the prior surveys, and by hand searching the venues that publish this work. Match status and analytical role are recorded per report in included_report_crosswalk.json.

## Analytical roles of the 83 included reports

| Role | Reports |
|:--|--:|
| core_intervention | 39 |
| enabling_infrastructure | 8 |
| horizon_evidence | 9 |
| transfer_evidence | 27 |

These roles are analytical classifications applied after inclusion. They are not PRISMA exclusion reasons.

## Suggested wording for the methodology

Screening was not duplicated, so no inter-rater agreement statistic is available. The five database exports contained 4,986 records. After removing 512 duplicate records and 10 superseded preprint records, 4,464 records were screened on title and abstract. The retained endpoint comprised 83 reports, of which 41 were directly matched to the database exports and 42 could not be reproduced in those exports. The per-record screening ledger partitions that difference of 4,423 records: 4,414 were excluded on title and abstract against one primary reason each, and the remainder were assessed at full text.

## Suggested wording for the limitations

Screening was not duplicated, so no inter-rater agreement statistic is available for this corpus. One primary reason was recorded for every exclusion, so the boundary of the corpus follows a stated rule rather than a case-by-case judgement.

## PRISMA nodes this package does not fill

- Reports sought for retrieval.
- Reports not retrieved.
- Full-text exclusions by reason.
- Independent studies, unless the project separately confirms that every retained report represents a different study.

The cross-check found no duplicate retained DOI and no duplicate normalized title. 83 is therefore reliable as a count of included reports. Whether it is also written as 83 studies is for the author to confirm.

## Formal version handling

4 of the current cite keys were linked to a formal publication during the cross-check. This does not change the citation count, but whether the bibliography metadata is replaced is for the author to confirm.
