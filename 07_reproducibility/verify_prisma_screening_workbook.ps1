param(
    [string]$WorkbookPath = "E:\SurveyRevision\outputs\prisma_screening_2026-08-29\PRISMA_screening_ledger_2026-08-29.xlsx"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$qaDirectory = Join-Path $projectRoot "tmp\prisma_screening_visual_qa"
New-Item -ItemType Directory -Path $qaDirectory -Force | Out-Null
$reportPath = Join-Path $qaDirectory "verification.json"

$excel = $null
$workbook = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $true
    $workbook = $excel.Workbooks.Open($WorkbookPath)
    $excel.CalculateFullRebuild()
    $workbook.Save()

    $sheetInfo = @()
    $formulaErrors = @()
    foreach ($sheet in $workbook.Worksheets) {
        $used = $sheet.UsedRange
        $sheetInfo += [ordered]@{
            name = $sheet.Name
            used_rows = $used.Rows.Count
            used_columns = $used.Columns.Count
            tables = $sheet.ListObjects.Count
        }
        try {
            $errors = $used.SpecialCells(-4123, 16)
            foreach ($area in $errors.Areas) {
                $formulaErrors += "$($sheet.Name)!$($area.Address($false, $false))"
            }
        }
        catch {
            if ($_.Exception.HResult -ne -2146827284) {
                throw
            }
        }
    }

    $summary = $workbook.Worksheets.Item("Summary")
    $ledger = $workbook.Worksheets.Item("Screening Ledger")
    $codebook = $workbook.Worksheets.Item("Codebook")
    $removals = $workbook.Worksheets.Item("Pre-screen Removals")
    $readyRow = 0
    for ($row = 1; $row -le $summary.UsedRange.Rows.Count; $row++) {
        if ([string]$summary.Cells.Item($row, 1).Value2 -eq "Stage-specific PRISMA counts ready") {
            $readyRow = $row
            break
        }
    }
    if ($readyRow -eq 0) {
        throw "Could not locate the PRISMA readiness row"
    }
    $checks = [ordered]@{
        summary_records_identified = $summary.Range("B5").Value2
        summary_duplicates_removed = $summary.Range("B6").Value2
        summary_superseded_removed = $summary.Range("B7").Value2
        summary_ledger_records = $summary.Range("B8").Value2
        summary_current_corpus_matches = $summary.Range("B9").Value2
        summary_title_abstract_included = $summary.Range("B12").Value2
        summary_title_abstract_excluded = $summary.Range("B13").Value2
        summary_title_abstract_pending = $summary.Range("B14").Value2
        summary_title_abstract_missing_reasons = $summary.Range("B15").Value2
        summary_full_text_pending = $summary.Range("B23").Value2
        summary_core_candidate_cap = $summary.Range("B27").Value2
        summary_ready = $summary.Cells.Item($readyRow, 2).Value2
        ledger_rows = $ledger.UsedRange.Rows.Count - 1
        ledger_columns = $ledger.UsedRange.Columns.Count
        ledger_formula_count = $ledger.Range("O2:O4465").SpecialCells(-4123).Count
        ledger_protected_core_candidates = $excel.WorksheetFunction.CountIf($ledger.Range("AI2:AI4465"), "protected current core candidate")
        ledger_selected_new_core_candidates = $excel.WorksheetFunction.CountIf($ledger.Range("AI2:AI4465"), "selected new core candidate")
        ledger_strict_candidates_outside_cap = $excel.WorksheetFunction.CountIf($ledger.Range("AI2:AI4465"), "strongly relevant supporting evidence")
        ledger_title_decision_validation_type = $ledger.Range("H2").Validation.Type
        ledger_exclusion_reason_validation_type = $ledger.Range("I2").Validation.Type
        ledger_full_text_status_validation_type = $ledger.Range("K2").Validation.Type
        ledger_full_text_decision_validation_type = $ledger.Range("L2").Validation.Type
        ledger_full_text_reason_validation_type = $ledger.Range("M2").Validation.Type
        codebook_value_rows = $codebook.UsedRange.Rows.Count - 4
        pre_screen_removal_rows = $removals.UsedRange.Rows.Count - 1
        formula_error_count = $formulaErrors.Count
    }

    $snapshots = [ordered]@{
        README = "A1:H32"
        Summary = "A1:F$readyRow"
        "Screening Ledger" = "A1:O9"
        Codebook = "A1:D34"
        "Pre-screen Removals" = "A1:K9"
    }
    $snapshotPaths = @()
    foreach ($sheetName in $snapshots.Keys) {
        $sheet = $workbook.Worksheets.Item($sheetName)
        $sheet.Activate()
        $range = $sheet.Range($snapshots[$sheetName])
        $range.Select()
        $range.CopyPicture(1, 2)
        Start-Sleep -Milliseconds 250
        $safeName = $sheetName.Replace(" ", "_").Replace("-", "_")
        $imagePath = Join-Path $qaDirectory ($safeName + ".png")
        $chartObject = $sheet.ChartObjects().Add(0, 0, $range.Width, $range.Height)
        $chartObject.Activate()
        $chartObject.Chart.Paste()
        Start-Sleep -Milliseconds 250
        $chartObject.Chart.Export($imagePath, "PNG") | Out-Null
        $chartObject.Delete()
        $snapshotPaths += $imagePath
    }

    $report = [ordered]@{
        workbook = $WorkbookPath
        sheets = $sheetInfo
        checks = $checks
        formula_errors = $formulaErrors
        snapshots = $snapshotPaths
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    $report | ConvertTo-Json -Depth 6
    $workbook.Close($false)
    $workbook = $null
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
