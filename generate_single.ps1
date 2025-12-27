# PowerShell script to generate a single article asynchronously
# Simpler version for testing individual articles

$headers = @{
    "Authorization" = "Bearer test-api-key-12345"
    "Content-Type" = "application/json"
}

# Article configuration
$keyword = "Schenkungssteuer Deutschland"
$companyUrl = "https://braun-kollegen.de/"
$slug = "schenkungssteuer-regelung-deutschland"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Generating Single Article" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keyword: $keyword" -ForegroundColor Yellow
Write-Host "Company: $companyUrl" -ForegroundColor Yellow
Write-Host "Slug: $slug" -ForegroundColor Yellow
Write-Host ""

# Build request body
$body = @{
    # REQUIRED
    primary_keyword = $keyword
    company_url = $companyUrl

    # LOCALIZATION
    language = "de"
    country = "DE"

    # COMPANY CONTEXT
    company_name = "Braun & Kollegen"

    # SEO
    slug = $slug
    index = $true

    # CONTENT SETTINGS
    word_count = 2000
    tone = "professional"

    # COMPANY DATA (including author information)
    company_data = @{
        author_name = "Rechtsanwalt Alexander Braun"
        author_bio = "Rechtsanwalt Alexander Braun ist Gründer und Seniorpartner der bundesweit tätigen Kanzlei Braun & Kollegen in München sowie Vorstandsvorsitzender der Arbeitsgemeinschaft Familie und Erbrecht e.V. Mit über 25 Jahren Erfahrung seit seiner Zulassung 1995 ist er spezialisiert auf Erbrecht, Unternehmensnachfolge und Vermögensplanung. Er hat über 200 Fachvorträge gehalten und mehr als tausend Mandanten in erbrechtlichen Fragen beraten. Als gefragter Experte tritt er regelmäßig in Rundfunk- und Fernsehanstalten auf und referiert bundesweit für Stiftungen und Organisationen."
        author_url = "https://braun-kollegen.de/team/alexander-braun"
        description = "Bundesweit tätige Rechtsanwaltskanzlei spezialisiert auf Erbrecht, Unternehmensnachfolge und Vermögensplanung"
        industry = "Rechtsberatung"
        target_audience = @()
        competitors = @()
    }

} | ConvertTo-Json -Depth 10

# Submit async job
Write-Host "Submitting article generation job..." -ForegroundColor Cyan

try {
    # Convert to UTF8 bytes to handle German umlauts correctly
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

    $job = Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/write-async" `
        -Method Post `
        -Headers $headers `
        -Body $bodyBytes

    Write-Host "✅ Job submitted successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Job ID: $($job.job_id)" -ForegroundColor White
    Write-Host "Status: $($job.status)" -ForegroundColor Gray
    Write-Host ""
}
catch {
    Write-Host "❌ Failed to submit job: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Monitor progress
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Monitoring Progress" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring (job will continue in background)" -ForegroundColor Gray
Write-Host ""

$jobId = $job.job_id
$completed = $false

while (-not $completed) {
    Start-Sleep -Seconds 15

    try {
        $status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/$jobId/status" -Method Get

        # Format progress bar
        $progress = $status.progress_percentage
        $barLength = 30
        $filled = [math]::Floor($progress / 100 * $barLength)
        $bar = ("#" * $filled).PadRight($barLength, "-")

        # Color based on status
        $color = switch ($status.status) {
            "completed" { "Green" }
            "failed" { "Red" }
            "running" { "Yellow" }
            default { "Gray" }
        }

        # Display status
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] [$bar] $($progress)%" -ForegroundColor $color -NoNewline
        Write-Host " - $($status.status)" -ForegroundColor $color -NoNewline
        if ($status.current_stage) {
            Write-Host " - $($status.current_stage)" -ForegroundColor Gray
        } else {
            Write-Host ""
        }

        # Check if completed or failed
        if ($status.status -eq "completed" -or $status.status -eq "failed") {
            $completed = $true
        }
    }
    catch {
        Write-Host "Error checking status: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 5
    }
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Job Finished!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Get final results
try {
    $finalStatus = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/$jobId/status" -Method Get

    if ($finalStatus.status -eq "completed" -and $finalStatus.result) {
        Write-Host "Status: COMPLETED ✅" -ForegroundColor Green
        Write-Host ""
        Write-Host "Article Details:" -ForegroundColor Yellow
        Write-Host "  Headline: $($finalStatus.result.headline)" -ForegroundColor White
        Write-Host "  Slug: $($finalStatus.result.slug)" -ForegroundColor White
        Write-Host "  Word Count: $($finalStatus.result.word_count)" -ForegroundColor White
        Write-Host "  Read Time: $($finalStatus.result.read_time_minutes) minutes" -ForegroundColor White
        Write-Host ""

        # Display sections
        if ($finalStatus.result.sections) {
            Write-Host "Sections ($($finalStatus.result.sections.Count)):" -ForegroundColor Yellow
            foreach ($section in $finalStatus.result.sections) {
                Write-Host "  • $($section.title)" -ForegroundColor Gray
            }
            Write-Host ""
        }

        # Display FAQ count
        if ($finalStatus.result.faq) {
            Write-Host "FAQ Questions: $($finalStatus.result.faq.Count)" -ForegroundColor Yellow
        }

        # Display internal links
        if ($finalStatus.result.internal_links) {
            Write-Host "Internal Links: $($finalStatus.result.internal_links.Count)" -ForegroundColor Yellow
            foreach ($link in $finalStatus.result.internal_links) {
                Write-Host "  → $($link.title): $($link.url)" -ForegroundColor Gray
            }
            Write-Host ""
        }

        # Display quality metrics
        if ($finalStatus.result.quality_report) {
            Write-Host "Quality Report:" -ForegroundColor Yellow
            $qr = $finalStatus.result.quality_report
            if ($qr.metrics) {
                Write-Host "  AEO Score: $($qr.metrics.aeo_score)/100" -ForegroundColor $(if ($qr.metrics.aeo_score -ge 70) { "Green" } else { "Yellow" })
            }
            if ($qr.passed) {
                Write-Host "  Status: PASSED ✅" -ForegroundColor Green
            } else {
                Write-Host "  Status: Below target (non-blocking)" -ForegroundColor Yellow
            }
            Write-Host ""
        }

        # Save HTML to file
        $filename = "$slug.html"
        $finalStatus.result.html | Out-File -FilePath $filename -Encoding UTF8
        Write-Host "💾 Saved HTML to: $filename" -ForegroundColor Green
        Write-Host ""

        # Save JSON metadata
        $jsonFilename = "$slug.json"
        $finalStatus.result | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFilename -Encoding UTF8
        Write-Host "💾 Saved metadata to: $jsonFilename" -ForegroundColor Green
        Write-Host ""

        Write-Host "Done! Open $filename in your browser to view the article." -ForegroundColor Green
    }
    elseif ($finalStatus.status -eq "failed") {
        Write-Host "Status: FAILED ❌" -ForegroundColor Red
        Write-Host ""
        if ($finalStatus.error_message) {
            Write-Host "Error: $($finalStatus.error_message)" -ForegroundColor Red
        }
        if ($finalStatus.error_details) {
            Write-Host "Details: $($finalStatus.error_details)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Status: $($finalStatus.status)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Error retrieving final results: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
