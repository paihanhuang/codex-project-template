$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PassCount = 0
$WarnCount = 0
$FailCount = 0

function Write-Pass {
    param([string] $Message)
    $script:PassCount++
    Write-Output "PASS: $Message"
}

function Write-Warn {
    param([string] $Message)
    $script:WarnCount++
    Write-Output "WARN: $Message"
}

function Write-Fail {
    param([string] $Message)
    $script:FailCount++
    Write-Output "FAIL: $Message"
}

function Resolve-RepoPath {
    param([string] $RelativePath)
    return Join-Path $Root $RelativePath
}

function Get-RepoText {
    param([string] $RelativePath)
    return Get-Content -Raw (Resolve-RepoPath $RelativePath)
}

function Require-File {
    param([string] $RelativePath)

    if (Test-Path (Resolve-RepoPath $RelativePath) -PathType Leaf) {
        Write-Pass "Required file exists: $RelativePath"
    }
    else {
        Write-Fail "Required file is missing: $RelativePath"
    }
}

function Require-Directory {
    param([string] $RelativePath)

    if (Test-Path (Resolve-RepoPath $RelativePath) -PathType Container) {
        Write-Pass "Required directory exists: $RelativePath"
    }
    else {
        Write-Fail "Required directory is missing: $RelativePath"
    }
}

function Require-Text {
    param(
        [string] $RelativePath,
        [string] $Pattern,
        [string] $Description
    )

    if (-not (Test-Path (Resolve-RepoPath $RelativePath) -PathType Leaf)) {
        Write-Fail "Cannot check $Description because $RelativePath is missing."
        return
    }

    $content = Get-RepoText $RelativePath
    if ($content -match $Pattern) {
        Write-Pass $Description
    }
    else {
        Write-Fail "$Description is missing from $RelativePath."
    }
}

function Validate-Agent {
    param([string] $AgentName)

    $relativePath = ".codex/agents/$AgentName.toml"
    $path = Resolve-RepoPath $relativePath

    if (-not (Test-Path $path -PathType Leaf)) {
        Write-Fail "Agent definition is missing: $relativePath"
        return
    }

    $content = Get-Content -Raw $path
    $requiredFields = @(
        "name",
        "description",
        "model_reasoning_effort",
        "sandbox_mode",
        "developer_instructions"
    )

    foreach ($field in $requiredFields) {
        if ($content -match "(?m)^$field\s*=") {
            Write-Pass "$AgentName agent defines $field."
        }
        else {
            Write-Fail "$AgentName agent is missing required field: $field."
        }
    }

    if ($content -match "(?m)^name\s*=\s*`"$([regex]::Escape($AgentName))`"") {
        Write-Pass "$AgentName agent name matches its filename."
    }
    else {
        Write-Fail "$AgentName agent name must match its filename."
    }

    if ($content -match "## Memory Entry") {
        Write-Pass "$AgentName agent includes the required Memory Entry contract."
    }
    else {
        Write-Fail "$AgentName agent must require a ## Memory Entry block."
    }
}

Write-Output "Template verification starting: $Root"

$requiredFiles = @(
    "AGENTS.md",
    ".codex/config.toml",
    ".codex/docs/workflow-reference.md",
    ".codex/docs/prompt-templates.md",
    ".codex/rules/default.rules",
    ".codex/research/INDEX.md",
    "verify.ps1",
    "verify.sh"
)

$requiredDirectories = @(
    ".codex/agents",
    ".codex/agent-memory",
    ".codex/plans",
    ".agents/skills"
)

foreach ($file in $requiredFiles) {
    Require-File $file
}

foreach ($directory in $requiredDirectories) {
    Require-Directory $directory
}

$agentNames = @(
    "research",
    "architect",
    "engineer",
    "qa-robustness",
    "qa-quality"
)

foreach ($agentName in $agentNames) {
    Validate-Agent $agentName
    Require-Directory ".codex/agent-memory/$agentName"
}

Require-Text "AGENTS.md" "workflow-reference\.md" "AGENTS.md points to the workflow reference."
Require-Text "AGENTS.md" "prompt-templates\.md" "AGENTS.md points to the prompt templates."
Require-Text "AGENTS.md" "small clear tasks" "AGENTS.md preserves the lightweight direct-implementation route."
Require-Text "AGENTS.md" "Dual-verdict gate" "AGENTS.md documents the dual-verdict QA gate."
Require-Text "AGENTS.md" "Memory Entry" "AGENTS.md documents the custom-agent memory contract."

$workflowSections = @(
    "Phase 0\.5",
    "Phase 0\.6",
    "Review Flow",
    "Phase 1",
    "Phase 2 & 3",
    "\.codex/plans/\.approved",
    "\.codex/plans/\.stage"
)

foreach ($section in $workflowSections) {
    Require-Text ".codex/docs/workflow-reference.md" $section "Workflow reference contains $section."
}

$promptSections = @(
    "Architect - Design Mode",
    "Research - Investigation Mode",
    "Architect - Review Mode",
    "Engineer - Review Mode",
    "Engineer - Implementation Mode",
    "QA-Robustness - Review Mode",
    "QA-Quality - Review Mode",
    "QA-Robustness - Verification Mode",
    "QA-Quality - Verification Mode"
)

foreach ($section in $promptSections) {
    Require-Text ".codex/docs/prompt-templates.md" ([regex]::Escape($section)) "Prompt templates contain $section."
}

$rulesPath = ".codex/rules/default.rules"
Require-Text $rulesPath 'pattern\s*=\s*\["git",\s*"reset",\s*"--hard"\]' "Rules forbid git reset --hard."
Require-Text $rulesPath 'pattern\s*=\s*\["git",\s*"clean",\s*"-fd"\]' "Rules forbid git clean -fd."
Require-Text $rulesPath 'pattern\s*=\s*\["git",\s*"push",\s*"--force"\]' "Rules forbid git push --force."
Require-Text $rulesPath 'pattern\s*=\s*\["git",\s*"push",\s*"-f"\]' "Rules forbid git push -f."

$approvedPath = Resolve-RepoPath ".codex/plans/.approved"
$stagePath = Resolve-RepoPath ".codex/plans/.stage"
$currentPlanPath = Resolve-RepoPath ".codex/plans/current.md"
$approvedExists = Test-Path $approvedPath -PathType Leaf
$stageExists = Test-Path $stagePath -PathType Leaf
$currentPlanExists = Test-Path $currentPlanPath -PathType Leaf

if ($stageExists -and -not $approvedExists) {
    Write-Fail ".codex/plans/.stage exists without .codex/plans/.approved."
}
else {
    Write-Pass "Plan stage marker is consistent with approval marker."
}

if ($approvedExists -and -not $currentPlanExists) {
    Write-Fail ".codex/plans/.approved exists without .codex/plans/current.md."
}
else {
    Write-Pass "Approval marker is consistent with current plan state."
}

if ($currentPlanExists -and -not $approvedExists) {
    Write-Warn ".codex/plans/current.md exists without .approved; treat it as unapproved planning state."
}

$configPath = ".codex/config.toml"
if (Test-Path (Resolve-RepoPath $configPath) -PathType Leaf) {
    $config = Get-RepoText $configPath

    if ($config -match 'sandbox_mode\s*=\s*"danger-full-access"') {
        Write-Warn "Project config forces danger-full-access; use only for intentionally trusted/yolo sessions."
    }

    if ($config -match 'approval_policy\s*=\s*"never"') {
        Write-Warn "Project config disables approval prompts; use only for intentionally trusted/yolo sessions."
    }

    Require-Text $configPath 'multi_agent\s*=\s*true' "Project config enables multi-agent workflows."
    Require-Text $configPath 'max_depth\s*=\s*1' "Project config keeps subagent depth bounded."
}

Write-Output "Template verification summary: $PassCount passed, $WarnCount warning(s), $FailCount failure(s)."

if ($FailCount -gt 0) {
    exit 1
}

exit 0
