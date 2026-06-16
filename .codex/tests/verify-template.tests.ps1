$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$verifyPs1 = Join-Path $RepoRoot "verify.ps1"
$verifySh = Join-Path $RepoRoot "verify.sh"

$failures = New-Object System.Collections.Generic.List[string]

function Assert-True {
    param(
        [bool] $Condition,
        [string] $Message
    )

    if (-not $Condition) {
        $failures.Add($Message)
    }
}

function Assert-TextDoesNotContain {
    param(
        [string] $Path,
        [string] $Pattern,
        [string] $Message
    )

    $content = Get-Content -Raw $Path
    Assert-True -Condition ($content -notmatch $Pattern) -Message $Message
}

Assert-True -Condition (Test-Path $verifyPs1 -PathType Leaf) -Message "verify.ps1 must exist."
Assert-True -Condition (Test-Path $verifySh -PathType Leaf) -Message "verify.sh must exist."

Assert-TextDoesNotContain -Path $verifyPs1 -Pattern "No verification configured" -Message "verify.ps1 must perform real checks, not print the placeholder message."
Assert-TextDoesNotContain -Path $verifySh -Pattern "No verification configured" -Message "verify.sh must perform real checks, not print the placeholder message."

$result = & powershell -NoProfile -ExecutionPolicy Bypass -File $verifyPs1 2>&1
$exitCode = $LASTEXITCODE
$output = ($result | Out-String)

Assert-True -Condition ($exitCode -eq 0) -Message "verify.ps1 should exit 0 for the current template. Output: $output"
Assert-True -Condition ($output -match "Template verification summary") -Message "verify.ps1 should print a template verification summary."
Assert-True -Condition ($output -match "\bPASS\b") -Message "verify.ps1 should emit PASS lines."
Assert-True -Condition ($output -notmatch "No verification configured") -Message "verify.ps1 runtime output must not use the placeholder message."

if (Get-Command bash -ErrorAction SilentlyContinue) {
    $bashResult = & bash ./verify.sh 2>&1
    $bashExitCode = $LASTEXITCODE
    $bashOutput = ($bashResult | Out-String)

    Assert-True -Condition ($bashExitCode -eq 0) -Message "verify.sh should run successfully through bash when bash is available. Output: $bashOutput"
    Assert-True -Condition ($bashOutput -match "Template verification summary") -Message "verify.sh should print the shared template verification summary."
}

if ($failures.Count -gt 0) {
    Write-Output "FAIL: template verification tests"
    foreach ($failure in $failures) {
        Write-Output " - $failure"
    }
    exit 1
}

Write-Output "PASS: template verification tests"
