param(
    [string]$OutputPath = "E:\SurveyRevision\outputs\prisma_screening_2026-08-29\PRISMA_screening_ledger_2026-08-29.xlsx",
    [string]$RecordsFileName = "screening_records.json",
    [string]$SummaryFileName = "suggestion_summary.json"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputRoot = Join-Path $projectRoot "generated_prisma_screening"
$records = Get-Content -LiteralPath (Join-Path $inputRoot $RecordsFileName) -Raw -Encoding UTF8 | ConvertFrom-Json
$removals = Get-Content -LiteralPath (Join-Path $inputRoot "pre_screen_removals.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$summary = Get-Content -LiteralPath (Join-Path $inputRoot $SummaryFileName) -Raw -Encoding UTF8 | ConvertFrom-Json
$codebook = Get-Content -LiteralPath (Join-Path $inputRoot "screening_codebook.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$isAutoScreened = $RecordsFileName -like "*auto_screened*"

function Get-OleColor {
    param([string]$Hex)
    $red = [Convert]::ToInt32($Hex.Substring(0, 2), 16)
    $green = [Convert]::ToInt32($Hex.Substring(2, 2), 16)
    $blue = [Convert]::ToInt32($Hex.Substring(4, 2), 16)
    return $red + 256 * $green + 65536 * $blue
}

$navy = Get-OleColor "17324D"
$teal = Get-OleColor "1F6D6A"
$paleTeal = Get-OleColor "DDEDEA"
$paleBlue = Get-OleColor "E8F0F7"
$paleGold = Get-OleColor "FFF1CC"
$paleRed = Get-OleColor "FBE2E2"
$paleGreen = Get-OleColor "DDEEDC"
$white = Get-OleColor "FFFFFF"
$textColor = Get-OleColor "1F2933"
$muted = Get-OleColor "52616B"

function Set-TitleBand {
    param(
        $Sheet,
        [string]$Title,
        [string]$Subtitle,
        [int]$EndColumn
    )
    $titleRange = $Sheet.Range($Sheet.Cells(1, 1), $Sheet.Cells(1, $EndColumn))
    $titleRange.Merge()
    $titleRange.Value2 = $Title
    $titleRange.Interior.Color = $navy
    $titleRange.Font.Name = "Arial"
    $titleRange.Font.Size = 16
    $titleRange.Font.Bold = $true
    $titleRange.Font.Color = $white
    $titleRange.VerticalAlignment = -4108
    $Sheet.Rows.Item(1).RowHeight = 30

    $subtitleRange = $Sheet.Range($Sheet.Cells(2, 1), $Sheet.Cells(2, $EndColumn))
    $subtitleRange.Merge()
    $subtitleRange.Value2 = $Subtitle
    $subtitleRange.Interior.Color = $paleBlue
    $subtitleRange.Font.Name = "Arial"
    $subtitleRange.Font.Size = 10
    $subtitleRange.Font.Italic = $true
    $subtitleRange.Font.Color = $muted
    $subtitleRange.WrapText = $true
    $subtitleRange.VerticalAlignment = -4108
    $Sheet.Rows.Item(2).RowHeight = 32
}

function Set-SectionBand {
    param(
        $Sheet,
        [int]$Row,
        [string]$Text,
        [int]$EndColumn
    )
    $range = $Sheet.Range($Sheet.Cells($Row, 1), $Sheet.Cells($Row, $EndColumn))
    $range.Merge()
    $range.Value2 = $Text
    $range.Interior.Color = $teal
    $range.Font.Name = "Arial"
    $range.Font.Size = 11
    $range.Font.Bold = $true
    $range.Font.Color = $white
    $range.VerticalAlignment = -4108
    $Sheet.Rows.Item($Row).RowHeight = 22
}

function Set-HeaderRow {
    param($Range)
    $Range.Interior.Color = $navy
    $Range.Font.Name = "Arial"
    $Range.Font.Size = 9
    $Range.Font.Bold = $true
    $Range.Font.Color = $white
    $Range.WrapText = $true
    $Range.HorizontalAlignment = -4131
    $Range.VerticalAlignment = -4108
}

function Set-ColumnWidths {
    param($Sheet, [hashtable]$Widths)
    foreach ($column in $Widths.Keys) {
        $Sheet.Columns.Item($column).ColumnWidth = $Widths[$column]
    }
}

function Add-ListValidation {
    param(
        $Range,
        [string]$Formula
    )
    $Range.Validation.Delete()
    $Range.Validation.Add(3, 1, 1, $Formula)
    $Range.Validation.IgnoreBlank = $true
    $Range.Validation.InCellDropdown = $true
    $Range.Validation.ShowError = $true
    $Range.Validation.ErrorTitle = "Controlled value required"
    $Range.Validation.ErrorMessage = "Choose a value from the Codebook list."
}

function Add-Table {
    param(
        $Sheet,
        $Range,
        [string]$Name,
        [string]$Style
    )
    $table = $Sheet.ListObjects.Add(1, $Range, $null, 1)
    $table.Name = $Name
    $table.TableStyle = $Style
    return $table
}

function Convert-ToTsvField {
    param($Value)
    if ($null -eq $Value) {
        return ""
    }
    return ([string]$Value).Replace("`t", " ").Replace("`r", " ").Replace("`n", " ")
}

function Write-TsvFile {
    param(
        [string]$Path,
        [string[]]$Headers,
        [System.Collections.IEnumerable]$Rows
    )
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $encoding = New-Object System.Text.UTF8Encoding($true)
    $writer = New-Object System.IO.StreamWriter($Path, $false, $encoding)
    try {
        $writer.WriteLine(($Headers | ForEach-Object { Convert-ToTsvField $_ }) -join "`t")
        foreach ($row in $Rows) {
            $writer.WriteLine(($row | ForEach-Object { Convert-ToTsvField $_ }) -join "`t")
        }
    }
    finally {
        $writer.Dispose()
    }
}

$excel = $null
$workbook = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false
    $excel.EnableEvents = $false
    $workbook = $excel.Workbooks.Add()
    while ($workbook.Worksheets.Count -gt 1) {
        $workbook.Worksheets.Item($workbook.Worksheets.Count).Delete()
    }

    $removalSheet = $workbook.Worksheets.Item(1)
    $removalSheet.Name = "Pre-screen Removals"
    $codebookSheet = $workbook.Worksheets.Add()
    $codebookSheet.Name = "Codebook"
    $ledger = $workbook.Worksheets.Add()
    $ledger.Name = "Screening Ledger"
    $summarySheet = $workbook.Worksheets.Add()
    $summarySheet.Name = "Summary"
    $readme = $workbook.Worksheets.Add()
    $readme.Name = "README"

    foreach ($sheet in @($readme, $summarySheet, $ledger, $codebookSheet, $removalSheet)) {
        $sheet.Cells.Font.Name = "Arial"
        $sheet.Cells.Font.Size = 10
        $sheet.Cells.Font.Color = $textColor
        $sheet.Activate()
        $excel.ActiveWindow.DisplayGridlines = $false
    }

    $readmeTitle = if ($isAutoScreened) { "PRISMA author-authorized automated screening ledger" } else { "PRISMA single-reviewer screening ledger" }
    $readmeSubtitle = if ($isAutoScreened) { "Deterministic title and abstract keyword screening for the five database exports searched on 2026-08-28" } else { "Retrospective reconstruction for the five database exports searched on 2026-08-28" }
    Set-TitleBand $readme $readmeTitle $readmeSubtitle 8
    Set-SectionBand $readme 4 "Purpose and reporting boundary" 8
    if ($isAutoScreened) {
        $notes = @(
            @("Purpose", "This workbook records the author-authorized automated title and abstract keyword screen of 4,464 post-deduplication records."),
            @("Decision owner", "The script populated title and abstract decisions under author authorization on 2026-08-29. The single reviewer retains responsibility for auditing these decisions and completing full-text assessment."),
            @("Method boundary", "Only title and abstract text supplied by the database exports was used for the three relevance signals. Venue names and database keywords were not used as inclusion evidence."),
            @("Current manuscript", "Full-text assessment is incomplete. Do not report the final included-study count until all advanced and uncertain records are resolved."),
            @("Core scope", "The core route is capped at 50 full-text candidates. It contains 38 protected current matches and at most 12 selected new candidates. Additional relevant records are marked E7 as supporting evidence.")
        )
    }
    else {
        $notes = @(
            @("Purpose", "This workbook supports a new title and abstract screen plus full-text assessment of the 4,464 post-deduplication records."),
            @("Decision owner", "One human reviewer is responsible for every final inclusion or exclusion. Automated fields are suggestions only."),
            @("Current manuscript", "No stage-specific PRISMA count should be copied into the manuscript until the reviewer fields are complete and reconciled."),
            @("Historical endpoint", "Thirty-eight current survey reports are matched to these exports and flagged. Forty-one current reports are outside or unmatched to this five-database route and are not rows in this ledger.")
        )
    }
    for ($index = 0; $index -lt $notes.Count; $index++) {
        $row = 5 + $index
        $readme.Cells.Item($row, 1).Value2 = $notes[$index][0]
        $textRange = $readme.Range($readme.Cells.Item($row, 2), $readme.Cells.Item($row, 8))
        $textRange.Merge()
        $textRange.Value2 = $notes[$index][1]
        $readme.Cells.Item($row, 1).Font.Bold = $true
        $readme.Cells.Item($row, 1).Font.Color = $navy
        $textRange.WrapText = $true
        $textRange.VerticalAlignment = -4160
        $readme.Rows.Item($row).RowHeight = 34
    }
    Set-SectionBand $readme 10 "Frozen pre-screen counts" 8
    $frozenCounts = @(
        @("Records identified", [int]$summary.records_identified),
        @("Duplicate records removed", [int]$summary.duplicate_records_removed),
        @("Superseded preprints removed", [int]$summary.superseded_preprint_records_removed),
        @("Records for screening", [int]$summary.records_for_screening)
    )
    for ($index = 0; $index -lt $frozenCounts.Count; $index++) {
        $row = 11 + $index
        $labelRange = $readme.Range($readme.Cells.Item($row, 1), $readme.Cells.Item($row, 3))
        $labelRange.Merge()
        $labelRange.Value2 = $frozenCounts[$index][0]
        $labelRange.Font.Bold = $true
        $labelRange.Font.Color = $navy
        $readme.Cells.Item($row, 4).Value2 = [double]$frozenCounts[$index][1]
        $readme.Cells.Item($row, 4).Font.Size = 12
        $readme.Cells.Item($row, 4).Font.Bold = $true
        $readme.Cells.Item($row, 4).Font.Color = $teal
        $readme.Cells.Item($row, 4).NumberFormat = "#,##0"
    }
    Set-SectionBand $readme 16 "Recommended review order" 8
    if ($isAutoScreened) {
        $steps = @(
            "Audit rows marked uncertain first. Obtain an abstract or source text before changing their decision.",
            "Spot-check excluded records by E code, especially E1 through E3, to assess keyword-screening error.",
            "Verify the 38 protected current survey matches and keep their cite keys unchanged.",
            "Retrieve and assess every row marked include for full text.",
            "Use exactly one F code when excluding a report after full-text assessment.",
            "Reconcile the Summary sheet before transferring any final count to the manuscript."
        )
    }
    else {
        $steps = @(
            "Filter Current corpus cite key to nonblank and verify the 38 protected endpoint matches first.",
            "Review retain for author review suggestions, then supplementary evidence candidates.",
            "Review exclude candidates in confidence order. Confirm the primary reason rather than accepting it automatically.",
            "For insufficient metadata, use the source URL or obtain the full text before deciding.",
            "Use exactly one primary exclusion reason at each exclusion stage. Put nuance in Reviewer notes.",
            "When title and abstract screening is complete, assess only rows marked include for full text.",
            "Return the completed workbook for final count reconciliation and manuscript update."
        )
    }
    for ($index = 0; $index -lt $steps.Count; $index++) {
        $row = 17 + $index
        $readme.Cells.Item($row, 1).Value2 = [string]($index + 1)
        $readme.Cells.Item($row, 1).Font.Bold = $true
        $readme.Cells.Item($row, 1).Font.Color = $teal
        $stepRange = $readme.Range($readme.Cells.Item($row, 2), $readme.Cells.Item($row, 8))
        $stepRange.Merge()
        $stepRange.Value2 = $steps[$index]
        $stepRange.WrapText = $true
        $stepRange.VerticalAlignment = -4160
        $readme.Rows.Item($row).RowHeight = 30
    }
    Set-SectionBand $readme 25 "Locked eligibility rules" 8
    $rules = @(
        "English records only. No starting-year restriction. Search cutoff is 2026-08-28.",
        "Retain a formal publication over its preprint. A highly relevant arXiv paper is allowed only when no formal version exists.",
        "Workshop papers may be included and must remain marked as workshop papers.",
        "Gray literature is enabling or supporting evidence, not a core intervention by default.",
        "Reviews and surveys support background and citation chasing, not the core intervention synthesis.",
        "Core relevance requires a container or cloud-native relation, an orchestration decision, and a sustainability relation.",
        "The core intervention route is capped at 50 reports, including 38 protected current matches and at most 12 selected new candidates."
    )
    for ($index = 0; $index -lt $rules.Count; $index++) {
        $row = 26 + $index
        $readme.Cells.Item($row, 1).Value2 = "*"
        $ruleRange = $readme.Range($readme.Cells.Item($row, 2), $readme.Cells.Item($row, 8))
        $ruleRange.Merge()
        $ruleRange.Value2 = $rules[$index]
        $ruleRange.WrapText = $true
        $ruleRange.VerticalAlignment = -4160
        $readme.Rows.Item($row).RowHeight = 28
    }
    Set-ColumnWidths $readme @{A = 19; B = 23; C = 18; D = 15; E = 15; F = 15; G = 15; H = 15}
    $readme.Activate()
    $excel.ActiveWindow.SplitRow = 3
    $excel.ActiveWindow.FreezePanes = $true

    Set-TitleBand $codebookSheet "Screening codebook" "Controlled values for author decisions and mutually exclusive primary exclusion reasons" 4
    $codebookHeaders = @("Category", "Allowed value", "When to use", "Owner")
    for ($column = 1; $column -le $codebookHeaders.Count; $column++) {
        $codebookSheet.Cells.Item(4, $column).Value2 = $codebookHeaders[$column - 1]
    }
    Set-HeaderRow $codebookSheet.Range("A4:D4")
    $validationRanges = @{}
    $rowCursor = 5
    $titleAbstractOwner = if ($isAutoScreened) { "Automated screen, reviewer audit" } else { "Reviewer" }
    $groups = @(
        @("automation_suggestions", "Automation suggestion", @($codebook.automation_suggestions), "Prioritization only", "Script"),
        @("title_abstract_decisions", "Title and abstract decision", @($codebook.title_abstract_decisions), "Rule-based decision from title and abstract, subject to reviewer audit", $titleAbstractOwner),
        @("title_abstract_exclusion_reasons", "Title and abstract exclusion reason", @($codebook.title_abstract_exclusion_reasons), "Choose one only when the title and abstract decision is exclude", $titleAbstractOwner),
        @("full_text_statuses", "Full-text retrieval status", @($codebook.full_text_statuses), "Track retrieval after a record advances", "Reviewer"),
        @("full_text_decisions", "Full-text decision", @($codebook.full_text_decisions), "Final decision after assessing the report", "Reviewer"),
        @("full_text_exclusion_reasons", "Full-text exclusion reason", @($codebook.full_text_exclusion_reasons), "Choose one only when the full-text decision is exclude", "Reviewer")
    )
    foreach ($group in $groups) {
        $startRow = $rowCursor
        foreach ($value in $group[2]) {
            $codebookSheet.Cells.Item($rowCursor, 1).Value2 = [string]$group[1]
            $codebookSheet.Cells.Item($rowCursor, 2).Value2 = [string]$value
            $codebookSheet.Cells.Item($rowCursor, 3).Value2 = [string]$group[3]
            $codebookSheet.Cells.Item($rowCursor, 4).Value2 = [string]$group[4]
            $rowCursor++
        }
        $validationRanges[$group[0]] = "='Codebook'!`$B`$$startRow`:`$B`$" + ($rowCursor - 1)
    }
    $codebookEndRow = $rowCursor - 1
    $codebookDataRange = $codebookSheet.Range($codebookSheet.Cells.Item(5, 1), $codebookSheet.Cells.Item($codebookEndRow, 4))
    $codebookDataRange.WrapText = $true
    $codebookDataRange.VerticalAlignment = -4160
    $codebookSheet.Rows.Item("5:$codebookEndRow").RowHeight = 34
    Add-Table $codebookSheet $codebookSheet.Range("A4:D$codebookEndRow") "CodebookTable" "TableStyleMedium4" | Out-Null
    Set-ColumnWidths $codebookSheet @{A = 34; B = 64; C = 66; D = 14}
    $codebookSheet.Activate()
    $excel.ActiveWindow.SplitRow = 4
    $excel.ActiveWindow.FreezePanes = $true

    $ledgerHeaders = @(
        "Screening ID",
        "Title",
        "Year",
        "Current corpus cite key",
        "Automation suggestion",
        "Confidence",
        "Suggested primary reason",
        "Reviewer title and abstract decision",
        "Reviewer exclusion reason",
        "Reviewer notes",
        "Full-text status",
        "Full-text decision",
        "Full-text exclusion reason",
        "Full-text notes",
        "Final status",
        "Abstract",
        "Current corpus role",
        "Publication type",
        "Source databases",
        "Venue",
        "DOI",
        "Language",
        "Platform signal",
        "Decision signal",
        "Sustainability signal",
        "Automation rationale",
        "Authors",
        "Source record IDs",
        "Source URLs",
        "Representative record ID",
        "Consolidated duplicate member IDs",
        "Strict core candidate",
        "Strict core rank",
        "Strict core relevance score",
        "Core scope status"
    )
    $ledgerTsvRows = foreach ($record in $records) {
        ,@(
            [string]$record.screening_id,
            [string]$record.title,
            [string]$record.year,
            (@($record.current_corpus_cite_keys) -join " | "),
            [string]$record.automation_suggestion,
            [string]$record.automation_confidence,
            [string]$record.suggested_primary_reason,
            [string]$record.reviewer_title_abstract_decision,
            [string]$record.reviewer_exclusion_reason,
            [string]$record.reviewer_notes,
            [string]$record.full_text_status,
            [string]$record.full_text_decision,
            [string]$record.full_text_exclusion_reason,
            [string]$record.full_text_notes,
            "",
            [string]$record.abstract,
            (@($record.current_corpus_roles) -join " | "),
            [string]$record.publication_type,
            (@($record.sources) -join " | "),
            [string]$record.venue,
            [string]$record.doi,
            [string]$record.language,
            [string]$record.platform_signal,
            [string]$record.decision_signal,
            [string]$record.sustainability_signal,
            [string]$record.automation_rationale,
            [string]$record.authors,
            (@($record.source_ids) -join " | "),
            (@($record.source_urls) -join " | "),
            [string]$record.representative_record_id,
            (@($record.member_record_ids) -join " | "),
            [string]$record.strict_core_candidate,
            [string]$record.strict_core_rank,
            [string]$record.strict_core_relevance_score,
            [string]$record.core_scope_status
        )
    }
    $ledgerTsv = Join-Path $projectRoot "tmp\prisma_screening_ledger_import.tsv"
    Write-TsvFile $ledgerTsv $ledgerHeaders $ledgerTsvRows
    $ledgerEndRow = $records.Count + 1
    $ledgerDataRange = $ledger.Range($ledger.Cells.Item(2, 1), $ledger.Cells.Item($ledgerEndRow, $ledgerHeaders.Count))
    $ledgerDataRange.NumberFormat = "@"
    $ledgerImport = $ledger.QueryTables.Add("TEXT;$ledgerTsv", $ledger.Range("A1"))
    $ledgerImport.TextFileParseType = 1
    $ledgerImport.TextFilePlatform = 65001
    $ledgerImport.TextFileTabDelimiter = $true
    $ledgerImport.TextFileCommaDelimiter = $false
    $ledgerImport.TextFileSemicolonDelimiter = $false
    $ledgerImport.TextFileSpaceDelimiter = $false
    $ledgerImport.AdjustColumnWidth = $false
    $ledgerImport.RefreshStyle = 0
    $ledgerImport.Refresh($false)
    $ledgerImport.Delete()
    Set-HeaderRow $ledger.Range("A1:AI1")
    $ledger.Range("C2:C$ledgerEndRow").NumberFormat = "@"
    $ledger.Range("O2:O$ledgerEndRow").ClearFormats() | Out-Null
    $ledger.Range("O2:O$ledgerEndRow").FormulaR1C1 = '=IF(RC[-7]="exclude","Excluded at title and abstract",IF(RC[-7]="include for full text",IF(RC[-3]="include","Included",IF(RC[-3]="exclude","Excluded at full text",IF(RC[-4]="not retrieved","Report not retrieved","Pending full-text decision"))),"Pending title and abstract"))'
    $ledger.Range("A2:AI$ledgerEndRow").Font.Name = "Arial"
    $ledger.Range("A2:AI$ledgerEndRow").Font.Size = 9
    $ledger.Range("A2:AI$ledgerEndRow").WrapText = $true
    $ledger.Range("A2:AI$ledgerEndRow").VerticalAlignment = -4160
    $ledger.Rows.Item("2:$ledgerEndRow").RowHeight = 48
    $ledger.Rows.Item(1).RowHeight = 42
    Add-Table $ledger $ledger.Range("A1:AI$ledgerEndRow") "ScreeningLedgerTable" "TableStyleMedium2" | Out-Null
    Add-ListValidation $ledger.Range("H2:H$ledgerEndRow") $validationRanges.title_abstract_decisions
    Add-ListValidation $ledger.Range("I2:I$ledgerEndRow") $validationRanges.title_abstract_exclusion_reasons
    Add-ListValidation $ledger.Range("K2:K$ledgerEndRow") $validationRanges.full_text_statuses
    Add-ListValidation $ledger.Range("L2:L$ledgerEndRow") $validationRanges.full_text_decisions
    Add-ListValidation $ledger.Range("M2:M$ledgerEndRow") $validationRanges.full_text_exclusion_reasons
    Set-ColumnWidths $ledger @{A = 13; B = 46; C = 8; D = 19; E = 24; F = 11; G = 38; H = 26; I = 42; J = 38; K = 18; L = 18; M = 44; N = 38; O = 27; P = 70; Q = 22; R = 28; S = 26; T = 38; U = 23; V = 14; W = 28; X = 28; Y = 28; Z = 54; AA = 42; AB = 46; AC = 54; AD = 54; AE = 68; AF = 18; AG = 16; AH = 23; AI = 42}
    $ledger.Columns.Item("W:AI").Group()
    $ledger.Columns.Item("W:AI").Hidden = $true
    $ledger.Range("D2:D$ledgerEndRow").FormatConditions.Add(2, $null, '=LEN(D2)>0') | Out-Null
    $ledger.Range("D2:D$ledgerEndRow").FormatConditions.Item(1).Interior.Color = $paleTeal
    $ledger.Range("E2:E$ledgerEndRow").FormatConditions.Add(2, $null, '=E2="retain for author review"') | Out-Null
    $ledger.Range("E2:E$ledgerEndRow").FormatConditions.Item(1).Interior.Color = $paleGreen
    $ledger.Range("E2:E$ledgerEndRow").FormatConditions.Add(2, $null, '=E2="exclude candidate"') | Out-Null
    $ledger.Range("E2:E$ledgerEndRow").FormatConditions.Item(2).Interior.Color = $paleRed
    $ledger.Range("E2:E$ledgerEndRow").FormatConditions.Add(2, $null, '=E2="insufficient metadata"') | Out-Null
    $ledger.Range("E2:E$ledgerEndRow").FormatConditions.Item(3).Interior.Color = $paleGold
    $ledger.Range("H2:H$ledgerEndRow").FormatConditions.Add(2, $null, '=H2="include for full text"') | Out-Null
    $ledger.Range("H2:H$ledgerEndRow").FormatConditions.Item(1).Interior.Color = $paleGreen
    $ledger.Range("H2:H$ledgerEndRow").FormatConditions.Add(2, $null, '=H2="exclude"') | Out-Null
    $ledger.Range("H2:H$ledgerEndRow").FormatConditions.Item(2).Interior.Color = $paleRed
    $ledger.Range("H2:H$ledgerEndRow").FormatConditions.Add(2, $null, '=H2="uncertain"') | Out-Null
    $ledger.Range("H2:H$ledgerEndRow").FormatConditions.Item(3).Interior.Color = $paleGold
    $ledger.Activate()
    $excel.ActiveWindow.SplitRow = 1
    $excel.ActiveWindow.SplitColumn = 2
    $excel.ActiveWindow.FreezePanes = $true

    $summarySubtitle = if ($isAutoScreened) { "Counts are formula driven. Title and abstract decisions are automated under author authorization. Full-text fields remain reviewer owned." } else { "Counts below are formula driven. Only completed reviewer fields contribute to stage-specific decisions." }
    Set-TitleBand $summarySheet "PRISMA screening status" $summarySubtitle 6
    Set-SectionBand $summarySheet 4 "Frozen identification and pre-screen counts" 6
    $summaryRows = @(
        @("Records identified", [int]$summary.records_identified, "Five database exports"),
        @("Duplicates removed", [int]$summary.duplicate_records_removed, "Frozen manual duplicate audit"),
        @("Superseded preprints removed", [int]$summary.superseded_preprint_records_removed, "Formal version retained"),
        @("Records in screening ledger", ('=COUNTA(''Screening Ledger''!$A$2:$A$' + $ledgerEndRow + ')'), "Must equal 4,464"),
        @("Current corpus matches in ledger", ('=COUNTIF(''Screening Ledger''!$D$2:$D$' + $ledgerEndRow + ',"<>")'), "Protected retrospective endpoint matches")
    )
    for ($index = 0; $index -lt $summaryRows.Count; $index++) {
        $row = 5 + $index
        $summarySheet.Cells.Item($row, 1).Value2 = $summaryRows[$index][0]
        if ($summaryRows[$index][1] -is [string] -and $summaryRows[$index][1].StartsWith("=")) {
            $summarySheet.Cells.Item($row, 2).Formula = $summaryRows[$index][1]
        }
        else {
            $summarySheet.Cells.Item($row, 2).Value2 = [double]$summaryRows[$index][1]
        }
        $noteRange = $summarySheet.Range($summarySheet.Cells.Item($row, 3), $summarySheet.Cells.Item($row, 6))
        $noteRange.Merge()
        $noteRange.Value2 = $summaryRows[$index][2]
    }
    $screeningSectionTitle = if ($isAutoScreened) { "Author-authorized automated title and abstract screening" } else { "Reviewer title and abstract screening" }
    Set-SectionBand $summarySheet 11 $screeningSectionTitle 6
    $screeningRows = @(
        @("Include for full text", ('=COUNTIF(''Screening Ledger''!$H$2:$H$' + $ledgerEndRow + ',"include for full text")'), "Advances to report retrieval"),
        @("Excluded at title and abstract", ('=COUNTIF(''Screening Ledger''!$H$2:$H$' + $ledgerEndRow + ',"exclude")'), "Requires one E-code reason"),
        @("Uncertain or pending", ('=COUNTA(''Screening Ledger''!$A$2:$A$' + $ledgerEndRow + ')-COUNTIF(''Screening Ledger''!$H$2:$H$' + $ledgerEndRow + ',"include for full text")-COUNTIF(''Screening Ledger''!$H$2:$H$' + $ledgerEndRow + ',"exclude")'), "Must reach zero before finalization"),
        @("Excluded rows missing a reason", ('=COUNTIFS(''Screening Ledger''!$H$2:$H$' + $ledgerEndRow + ',"exclude",''Screening Ledger''!$I$2:$I$' + $ledgerEndRow + ',"")'), "Quality-control warning")
    )
    for ($index = 0; $index -lt $screeningRows.Count; $index++) {
        $row = 12 + $index
        $summarySheet.Cells.Item($row, 1).Value2 = $screeningRows[$index][0]
        $summarySheet.Cells.Item($row, 2).Formula = $screeningRows[$index][1]
        $noteRange = $summarySheet.Range($summarySheet.Cells.Item($row, 3), $summarySheet.Cells.Item($row, 6))
        $noteRange.Merge()
        $noteRange.Value2 = $screeningRows[$index][2]
    }
    Set-SectionBand $summarySheet 17 "Author-confirmed full-text assessment" 6
    $fullTextRows = @(
        @("Reports sought for retrieval", ('=COUNTIF(''Screening Ledger''!$K$2:$K$' + $ledgerEndRow + ',"sought")+COUNTIF(''Screening Ledger''!$K$2:$K$' + $ledgerEndRow + ',"retrieved")+COUNTIF(''Screening Ledger''!$K$2:$K$' + $ledgerEndRow + ',"not retrieved")'), "Use retrieval status for every advanced record"),
        @("Reports not retrieved", ('=COUNTIF(''Screening Ledger''!$K$2:$K$' + $ledgerEndRow + ',"not retrieved")'), "PRISMA retrieval node"),
        @("Reports assessed for eligibility", ('=COUNTIF(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"include")+COUNTIF(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"exclude")'), "Completed full-text decisions"),
        @("Excluded after full text", ('=COUNTIF(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"exclude")'), "Requires one F-code reason"),
        @("Included from database route", ('=COUNTIF(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"include")'), "Database-route included reports"),
        @("Advanced rows pending full-text outcome", ('=COUNTIF(''Screening Ledger''!$H$2:$H$' + $ledgerEndRow + ',"include for full text")-COUNTIF(''Screening Ledger''!$K$2:$K$' + $ledgerEndRow + ',"not retrieved")-COUNTIF(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"include")-COUNTIF(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"exclude")'), "Must reach zero before finalization"),
        @("Full-text exclusions missing a reason", ('=COUNTIFS(''Screening Ledger''!$L$2:$L$' + $ledgerEndRow + ',"exclude",''Screening Ledger''!$M$2:$M$' + $ledgerEndRow + ',"")'), "Quality-control warning")
    )
    for ($index = 0; $index -lt $fullTextRows.Count; $index++) {
        $row = 18 + $index
        $summarySheet.Cells.Item($row, 1).Value2 = $fullTextRows[$index][0]
        $summarySheet.Cells.Item($row, 2).Formula = $fullTextRows[$index][1]
        $noteRange = $summarySheet.Range($summarySheet.Cells.Item($row, 3), $summarySheet.Cells.Item($row, 6))
        $noteRange.Merge()
        $noteRange.Value2 = $fullTextRows[$index][2]
    }
    Set-SectionBand $summarySheet 26 "Endpoint context and readiness" 6
    if ($isAutoScreened) {
        $endpointRows = @(
            @("Core intervention candidate cap", [int]$summary.core_intervention_cap, "Maximum number that can enter the capped full-text candidate route."),
            @("Protected current core candidates", [int]$summary.protected_current_core_candidates, "Database-matched current survey reports protected at this stage."),
            @("Selected new core candidates", [int]$summary.selected_new_core_candidates, "Highest-ranked direct-scope records within the 12-paper new-candidate cap."),
            @("Strict new candidates outside cap", ([int]$summary.strict_new_candidate_pool - [int]$summary.selected_new_core_candidates), "Marked E7 and retained as supporting evidence."),
            @("Other-method or unmatched legacy reports", 41, "Historical context only. These are not automatically included in the PRISMA core route."),
            @("Final included core reports", "=B22", "Populated only through completed full-text inclusion decisions."),
            @("Stage-specific PRISMA counts ready", '=IF(AND(B14=0,B23=0,B15=0,B24=0),"YES","NO")', "YES requires no pending decisions and no missing exclusion reasons.")
        )
    }
    else {
        $endpointRows = @(
            @("Other-method or unmatched legacy reports", 41, "Historical endpoint only. Discovery routes remain incompletely documented."),
            @("Combined included reports if the database route is frozen", "=B22+B27", "This updates with the database-route inclusion count."),
            @("Stage-specific PRISMA counts ready", '=IF(AND(B14=0,B23=0,B15=0,B24=0),"YES","NO")', "YES requires no pending decisions and no missing exclusion reasons.")
        )
    }
    for ($index = 0; $index -lt $endpointRows.Count; $index++) {
        $row = 27 + $index
        $summarySheet.Cells.Item($row, 1).Value2 = $endpointRows[$index][0]
        if ($endpointRows[$index][1] -is [string] -and $endpointRows[$index][1].StartsWith("=")) {
            $summarySheet.Cells.Item($row, 2).Formula = $endpointRows[$index][1]
        }
        else {
            $summarySheet.Cells.Item($row, 2).Value2 = [double]$endpointRows[$index][1]
        }
        $noteRange = $summarySheet.Range($summarySheet.Cells.Item($row, 3), $summarySheet.Cells.Item($row, 6))
        $noteRange.Merge()
        $noteRange.Value2 = $endpointRows[$index][2]
    }
    $endpointEndRow = 26 + $endpointRows.Count
    $summaryValueRows = @(5, 6, 7, 8, 9, 12, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24) + @(27..$endpointEndRow)
    foreach ($row in $summaryValueRows) {
        $summarySheet.Cells.Item($row, 1).Font.Bold = $true
        $summarySheet.Cells.Item($row, 1).Font.Color = $navy
        $summarySheet.Cells.Item($row, 2).Font.Size = 12
        $summarySheet.Cells.Item($row, 2).Font.Bold = $true
        $summarySheet.Cells.Item($row, 2).Font.Color = $teal
        if ($row -ne $endpointEndRow) {
            $summarySheet.Cells.Item($row, 2).NumberFormat = "#,##0"
        }
        $summarySheet.Range($summarySheet.Cells.Item($row, 3), $summarySheet.Cells.Item($row, 6)).WrapText = $true
        $summarySheet.Rows.Item($row).RowHeight = 30
    }
    $summarySheet.Range("B14:B15").FormatConditions.Add(2, $null, '=B14>0') | Out-Null
    $summarySheet.Range("B14:B15").FormatConditions.Item(1).Interior.Color = $paleGold
    $summarySheet.Range("B23:B24").FormatConditions.Add(2, $null, '=B23>0') | Out-Null
    $summarySheet.Range("B23:B24").FormatConditions.Item(1).Interior.Color = $paleGold
    $readyCell = "B$endpointEndRow"
    $summarySheet.Range($readyCell).FormatConditions.Add(2, $null, "=$readyCell=`"YES`"") | Out-Null
    $summarySheet.Range($readyCell).FormatConditions.Item(1).Interior.Color = $paleGreen
    $summarySheet.Range($readyCell).FormatConditions.Add(2, $null, "=$readyCell=`"NO`"") | Out-Null
    $summarySheet.Range($readyCell).FormatConditions.Item(2).Interior.Color = $paleRed
    Set-ColumnWidths $summarySheet @{A = 42; B = 18; C = 27; D = 18; E = 18; F = 18}
    $summarySheet.Activate()
    $excel.ActiveWindow.SplitRow = 3
    $excel.ActiveWindow.FreezePanes = $true

    $removalHeaders = @("Record ID", "Removal type", "Review group ID", "Removal reason", "Title", "Year", "DOI", "Source", "Source record ID", "Source URL", "Retained record ID")
    $removalTsvRows = foreach ($record in $removals) {
        ,@(
            [string]$record.record_id,
            [string]$record.removal_type,
            [string]$record.review_group_id,
            [string]$record.removal_reason,
            [string]$record.title,
            [string]$record.year,
            [string]$record.doi,
            [string]$record.source,
            [string]$record.source_id,
            [string]$record.url,
            [string]$record.retained_record_id
        )
    }
    $removalTsv = Join-Path $projectRoot "tmp\prisma_pre_screen_removals_import.tsv"
    Write-TsvFile $removalTsv $removalHeaders $removalTsvRows
    $removalEndRow = $removals.Count + 1
    $removalDataRange = $removalSheet.Range($removalSheet.Cells.Item(2, 1), $removalSheet.Cells.Item($removalEndRow, $removalHeaders.Count))
    $removalDataRange.NumberFormat = "@"
    $removalImport = $removalSheet.QueryTables.Add("TEXT;$removalTsv", $removalSheet.Range("A1"))
    $removalImport.TextFileParseType = 1
    $removalImport.TextFilePlatform = 65001
    $removalImport.TextFileTabDelimiter = $true
    $removalImport.TextFileCommaDelimiter = $false
    $removalImport.TextFileSemicolonDelimiter = $false
    $removalImport.TextFileSpaceDelimiter = $false
    $removalImport.AdjustColumnWidth = $false
    $removalImport.RefreshStyle = 0
    $removalImport.Refresh($false)
    $removalImport.Delete()
    Set-HeaderRow $removalSheet.Range("A1:K1")
    $removalSheet.Range("A2:K$removalEndRow").Font.Name = "Arial"
    $removalSheet.Range("A2:K$removalEndRow").Font.Size = 9
    $removalSheet.Range("A2:K$removalEndRow").WrapText = $true
    $removalSheet.Range("A2:K$removalEndRow").VerticalAlignment = -4160
    $removalSheet.Rows.Item("2:$removalEndRow").RowHeight = 38
    $removalSheet.Rows.Item(1).RowHeight = 36
    Add-Table $removalSheet $removalSheet.Range("A1:K$removalEndRow") "PreScreenRemovalsTable" "TableStyleMedium4" | Out-Null
    Set-ColumnWidths $removalSheet @{A = 58; B = 24; C = 18; D = 48; E = 65; F = 8; G = 25; H = 22; I = 48; J = 58; K = 58}
    $removalSheet.Activate()
    $excel.ActiveWindow.SplitRow = 1
    $excel.ActiveWindow.SplitColumn = 4
    $excel.ActiveWindow.FreezePanes = $true

    $readme.Activate()
    $excel.CalculateFullRebuild()
    $outputDirectory = Split-Path -Parent $OutputPath
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    if (Test-Path -LiteralPath $OutputPath) {
        Remove-Item -LiteralPath $OutputPath -Force
    }
    $workbook.SaveAs($OutputPath, 51)
    $workbook.Close($true)
    $workbook = $null
    Write-Output $OutputPath
}
finally {
    if ($null -ne $workbook) {
        $workbook.Close($false)
    }
    if ($null -ne $excel) {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
