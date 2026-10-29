# Runs the automated QA stages in Docker (host needs only Docker). Windows twin of qa.sh.
#   .\qa.ps1 <stage...>     stages: consistency unit static integration perf zap e2e uat docs demo report   |   all   |   down
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Stages)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$env:UAT_COMMIT = (git rev-parse --short HEAD 2>$null)
$compose = @("compose", "-f", "docker-compose.qa.yml")
New-Item -ItemType Directory -Force "qa/reports/k6", "qa/reports/zap", "demo/videos" | Out-Null

function Invoke-Stage([string]$name) {
    switch ($name) {
        { $_ -in "consistency", "unit", "static", "integration", "e2e", "uat", "docs", "demo", "report" } {
            & docker @compose run --rm --build qa python qa/run.py $name; return $LASTEXITCODE
        }
        "perf" { & docker @compose run --rm --build k6; return $LASTEXITCODE }
        "zap"  { & docker @compose run --rm --build zap; return $LASTEXITCODE }
        default { Write-Host "unknown stage: $name"; return 2 }
    }
}

function Stop-Stack { & docker @compose --profile qa --profile perf --profile zap down -v --remove-orphans 2>&1 | Out-Null }

if (-not $Stages) { Write-Host "usage: .\qa.ps1 <consistency|unit|static|integration|perf|zap|e2e|docs|demo|report|all|down> ..."; exit 2 }
if ($Stages[0] -eq "down") { Stop-Stack; exit 0 }
$runAll = $Stages[0] -eq "all"
if ($runAll) { $Stages = @("consistency", "unit", "static", "integration", "perf", "zap", "e2e") }

$results = [ordered]@{}
foreach ($stage in $Stages) {
    Write-Host "`n=================== $stage ==================="
    $results[$stage] = Invoke-Stage $stage
}
if ($runAll) {
    Write-Host "`n=================== report ==================="
    $results["report"] = Invoke-Stage "report"
    Stop-Stack
}

Write-Host "`n============================================================"
$overall = 0
foreach ($entry in $results.GetEnumerator()) {
    if ($entry.Value -eq 0) { Write-Host "PASS  $($entry.Key)" } else { Write-Host "FAIL  $($entry.Key)"; $overall = 1 }
}
Write-Host "============================================================"
exit $overall
