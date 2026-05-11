param(
    [string]$RepoRoot = "E:\ProgrammingWork\Harmes\my-hermes",
    [string]$PythonExe = "E:\ProgrammingSoftware\Anaconda\python.exe",
    [int]$PollSeconds = 15,
    [int]$FirstPassTimeoutSeconds = 900,
    [int]$FinalPassTimeoutSeconds = 1200
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

# Keep this script ASCII-only so Windows PowerShell 5.1 won't misparse it
# when the file is checked out as UTF-8 without BOM.

function Get-ProviderValue {
    param([string]$Name)

    $userValue = [Environment]::GetEnvironmentVariable($Name, "User")
    if ($userValue) {
        return $userValue
    }

    return [Environment]::GetEnvironmentVariable($Name, "Machine")
}

function Quote-WindowsArgument {
    param([string]$Value)

    if ($null -eq $Value) {
        return '""'
    }

    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')

    $backslashCount = 0
    foreach ($char in $Value.ToCharArray()) {
        if ($char -eq '\') {
            $backslashCount++
            continue
        }

        if ($char -eq '"') {
            [void]$builder.Append(('\' * ($backslashCount * 2 + 1)))
            [void]$builder.Append('"')
            $backslashCount = 0
            continue
        }

        if ($backslashCount -gt 0) {
            [void]$builder.Append(('\' * $backslashCount))
            $backslashCount = 0
        }
        [void]$builder.Append($char)
    }

    if ($backslashCount -gt 0) {
        [void]$builder.Append(('\' * ($backslashCount * 2)))
    }

    [void]$builder.Append('"')
    return $builder.ToString()
}

function Invoke-Hermes {
    param(
        [string[]]$CliArgs,
        [hashtable]$EnvMap,
        [switch]$AllowFailure
    )

    $backup = @{}
    foreach ($key in $EnvMap.Keys) {
        $backup[$key] = [Environment]::GetEnvironmentVariable($key, "Process")
        if ($null -eq $EnvMap[$key] -or $EnvMap[$key] -eq "") {
            Remove-Item "Env:$key" -ErrorAction SilentlyContinue
        } else {
            Set-Item "Env:$key" $EnvMap[$key]
        }
    }

    $stdoutPath = Join-Path ([System.IO.Path]::GetTempPath()) ("phase9_gate_" + [guid]::NewGuid().ToString("N") + "_stdout.txt")
    $stderrPath = Join-Path ([System.IO.Path]::GetTempPath()) ("phase9_gate_" + [guid]::NewGuid().ToString("N") + "_stderr.txt")

    try {
        Write-Host (">> hermes " + ($CliArgs -join " ")) -ForegroundColor DarkGray

        $argString = ((@("-m", "hermes_cli.main") + $CliArgs) | ForEach-Object {
            Quote-WindowsArgument ([string]$_)
        }) -join " "

        $proc = Start-Process `
            -FilePath $PythonExe `
            -ArgumentList $argString `
            -NoNewWindow `
            -Wait `
            -PassThru `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath

        $code = $proc.ExitCode
        $stdout = if (Test-Path $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw -Encoding UTF8 } else { "" }
        $stderr = if (Test-Path $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw -Encoding UTF8 } else { "" }
        $pieces = @()
        if ($stdout) { $pieces += $stdout.TrimEnd() }
        if ($stderr) { $pieces += $stderr.TrimEnd() }
        $out = ($pieces -join [Environment]::NewLine)
    } finally {
        foreach ($key in $EnvMap.Keys) {
            if ($null -eq $backup[$key]) {
                Remove-Item "Env:$key" -ErrorAction SilentlyContinue
            } else {
                Set-Item "Env:$key" $backup[$key]
            }
        }
        if (Test-Path $stdoutPath) {
            Remove-Item -LiteralPath $stdoutPath -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path $stderrPath) {
            Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
        }
    }

    if (-not $AllowFailure -and $code -ne 0) {
        throw "hermes command failed ($code): $($CliArgs -join ' ')`n$out"
    }

    return [pscustomobject]@{
        code = $code
        output = $out.Trim()
    }
}

function As-Array {
    param($Value)

    if ($null -eq $Value) {
        return @()
    }
    if ($Value -is [System.Array]) {
        return $Value
    }
    return @($Value)
}

function Get-Tasks {
    param([hashtable]$EnvMap)

    $res = Invoke-Hermes -CliArgs @("kanban", "list", "--json") -EnvMap $EnvMap
    if (-not $res.output) {
        return @()
    }
    return @(As-Array ($res.output | ConvertFrom-Json))
}

function Get-TaskShow {
    param(
        [hashtable]$EnvMap,
        [string]$TaskId
    )

    $res = Invoke-Hermes -CliArgs @("kanban", "show", $TaskId, "--json") -EnvMap $EnvMap
    return $res.output | ConvertFrom-Json
}

function Get-TaskRuns {
    param(
        [hashtable]$EnvMap,
        [string]$TaskId
    )

    $res = Invoke-Hermes -CliArgs @("kanban", "runs", $TaskId, "--json") -EnvMap $EnvMap
    if (-not $res.output) {
        return @()
    }
    return @(As-Array ($res.output | ConvertFrom-Json))
}

function Wait-TaskStatus {
    param(
        [hashtable]$EnvMap,
        [string]$TaskId,
        [string[]]$Wanted,
        [int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $show = Get-TaskShow -EnvMap $EnvMap -TaskId $TaskId
        $status = [string]$show.task.status
        if ($Wanted -contains $status) {
            return $show
        }
        if ($status -eq "archived") {
            throw "task $TaskId archived unexpectedly"
        }
        Start-Sleep -Seconds $PollSeconds
    }

    $last = Get-TaskShow -EnvMap $EnvMap -TaskId $TaskId
    throw "timeout waiting for $TaskId to reach [$($Wanted -join ', ')], last status=$($last.task.status)"
}

function New-OrchestratedTasks {
    param(
        [hashtable]$EnvMap,
        [string]$Prompt,
        [string]$Provider,
        [string]$Model
    )

    $before = Get-Tasks -EnvMap $EnvMap
    $beforeIds = @{}
    foreach ($task in $before) {
        $beforeIds[$task.id] = $true
    }

    $res = Invoke-Hermes `
        -CliArgs @("-p", "orchestrator", "-z", $Prompt, "--provider", $Provider, "-m", $Model, "--toolsets", "kanban") `
        -EnvMap $EnvMap

    $after = Get-Tasks -EnvMap $EnvMap
    $newTasks = @()
    foreach ($task in $after) {
        if (-not $beforeIds.ContainsKey($task.id)) {
            $newTasks += $task
        }
    }

    return [pscustomobject]@{
        message = $res.output
        tasks = $newTasks
    }
}

function Read-Text {
    param([string]$Path)

    if (Test-Path $Path) {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    }
    return ""
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runtime = Join-Path $RepoRoot "tmp\phase9_runtime\$timestamp"
$hermesHome = Join-Path $runtime "hermes_home"
$workspace = Join-Path $runtime "HermesWorkspace"

New-Item -ItemType Directory -Force -Path $hermesHome | Out-Null
New-Item -ItemType Directory -Force -Path $workspace | Out-Null

$deepseekKey = Get-ProviderValue "DEEPSEEK_API_KEY"
$deepseekBase = Get-ProviderValue "DEEPSEEK_BASE_URL"
$xiaomiKey = Get-ProviderValue "XIAOMI_API_KEY"
$xiaomiBase = Get-ProviderValue "XIAOMI_BASE_URL"

if (-not $deepseekKey -and -not $xiaomiKey) {
    throw "No DEEPSEEK_API_KEY or XIAOMI_API_KEY found in User/Machine environment variables."
}

$baseEnv = @{
    HERMES_HOME = $hermesHome
    HERMES_KANBAN_WORKSPACE = $workspace
}

foreach ($profile in @("orchestrator", "scriptwriter", "novelist")) {
    Invoke-Hermes -CliArgs @("profile", "create", $profile, "--no-alias") -EnvMap $baseEnv | Out-Null
    Copy-Item `
        (Join-Path $RepoRoot "plans\text_agent_profiles\$profile.SOUL.md") `
        (Join-Path $hermesHome "profiles\$profile\SOUL.md") `
        -Force
}

Invoke-Hermes -CliArgs @("kanban", "init") -EnvMap $baseEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "bootstrap-text-agent-workspace", "--root", $workspace, "--json") -EnvMap $baseEnv | Out-Null

$provider = $null
$model = $null
$activeEnv = $null
$probeOutput = $null
$probeErrors = @{}

if ($deepseekKey) {
    $envMap = $baseEnv.Clone()
    $envMap["DEEPSEEK_API_KEY"] = $deepseekKey
    if ($deepseekBase) {
        $envMap["DEEPSEEK_BASE_URL"] = $deepseekBase
    }

    $probe = Invoke-Hermes `
        -CliArgs @("-p", "orchestrator", "chat", "-Q", "-q", "Reply with your role name only.", "--provider", "deepseek", "-m", "deepseek-v4-flash") `
        -EnvMap $envMap `
        -AllowFailure

    if ($probe.code -eq 0) {
        $provider = "deepseek"
        $model = "deepseek-v4-flash"
        $activeEnv = $envMap
        $probeOutput = $probe.output
    } else {
        $probeErrors["deepseek"] = $probe.output
    }
}

if (-not $provider -and $xiaomiKey) {
    $envMap = $baseEnv.Clone()
    $envMap["XIAOMI_API_KEY"] = $xiaomiKey
    if ($xiaomiBase) {
        $envMap["XIAOMI_BASE_URL"] = $xiaomiBase
    }

    $probe = Invoke-Hermes `
        -CliArgs @("-p", "orchestrator", "chat", "-Q", "-q", "Reply with your role name only.", "--provider", "xiaomi", "-m", "mimo-v2.5") `
        -EnvMap $envMap `
        -AllowFailure

    if ($probe.code -eq 0) {
        $provider = "xiaomi"
        $model = "mimo-v2.5"
        $activeEnv = $envMap
        $probeOutput = $probe.output
    } else {
        $probeErrors["xiaomi"] = $probe.output
    }
}

if (-not $provider) {
    $failure = [ordered]@{
        runtime = $runtime
        probe_errors = $probeErrors
    } | ConvertTo-Json -Depth 6
    $failurePath = Join-Path $runtime "formal_phase9_probe_failure.json"
    Set-Content -LiteralPath $failurePath -Value $failure -Encoding UTF8
    throw "Neither deepseek-v4-flash nor mimo-v2.5 passed identity smoke. See $failurePath"
}

$identities = @{}
foreach ($profile in @("orchestrator", "scriptwriter", "novelist")) {
    $res = Invoke-Hermes `
        -CliArgs @("-p", $profile, "chat", "-Q", "-q", "Reply with your role name only.", "--provider", $provider, "-m", $model) `
        -EnvMap $activeEnv
    $identities[$profile] = $res.output
}

$scenarioA = @{}
$promptA = "Route this request into a kanban task and create it immediately without follow-up questions: create a funny salon short-video series about employees and the boss, with multiple reversals and no marketing tone."
$newA = New-OrchestratedTasks -EnvMap $activeEnv -Prompt $promptA -Provider $provider -Model $model
if ($newA.tasks.Count -ne 1) {
    throw "Scenario A expected 1 new task, got $($newA.tasks.Count)"
}

$taskA = $newA.tasks[0]
$scenarioA.created_task_id = $taskA.id
$scenarioA.assignee = $taskA.assignee

Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null
$showA1 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $taskA.id -Wanted @("blocked") -TimeoutSeconds $FirstPassTimeoutSeconds
$scenarioA.first_pass_status = $showA1.task.status
$scenarioA.first_pass_comment_count = (As-Array $showA1.comments).Count

Invoke-Hermes -CliArgs @("kanban", "comment", $taskA.id, "Choose direction 2, add a small uplifting ending, deliver a complete shoot-ready version, and update memory plus feedback.") -EnvMap $activeEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "unblock", $taskA.id) -EnvMap $activeEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null

$showA2 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $taskA.id -Wanted @("done") -TimeoutSeconds $FinalPassTimeoutSeconds
$runsA = Get-TaskRuns -EnvMap $activeEnv -TaskId $taskA.id
$projectA = $showA2.task.workspace_path
$scriptFilesA = @()
if ($projectA) {
    $scriptDirA = Join-Path $projectA "scripts"
    if (Test-Path $scriptDirA) {
        $scriptFilesA = @(Get-ChildItem -LiteralPath $scriptDirA -File | Where-Object { $_.Name -ne "README.md" } | Select-Object -ExpandProperty Name)
    }
}
$feedbackA = Read-Text (Join-Path $projectA "feedback_log.md")

$scenarioA.final_status = $showA2.task.status
$scenarioA.workspace_path = $projectA
$scenarioA.script_files = $scriptFilesA
$scenarioA.feedback_mentions_motivation = ($feedbackA -match "uplift|uplifting|motivat|inspir|encourag")
$scenarioA.run_outcomes = @(As-Array $runsA | ForEach-Object { $_.outcome })
$scenarioA.latest_summary = $showA2.latest_summary

$scenarioB = @{}
$promptB = "Route this request into a kanban task and create it immediately without follow-up questions: design a cyber-cultivation novel where the protagonist is not overpowered at the start and the female lead is cold outside but warm inside, then deliver worldbuilding, characters, and the first three chapter outlines."
$newB = New-OrchestratedTasks -EnvMap $activeEnv -Prompt $promptB -Provider $provider -Model $model
if ($newB.tasks.Count -ne 1) {
    throw "Scenario B expected 1 new task, got $($newB.tasks.Count)"
}

$taskB = $newB.tasks[0]
$scenarioB.created_task_id = $taskB.id
$scenarioB.assignee = $taskB.assignee

Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null
$showB1 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $taskB.id -Wanted @("blocked") -TimeoutSeconds $FirstPassTimeoutSeconds
$scenarioB.first_pass_status = $showB1.task.status
$scenarioB.first_pass_comment_count = (As-Array $showB1.comments).Count

Invoke-Hermes -CliArgs @("kanban", "comment", $taskB.id, "Chapter three needs a stronger conflict. Add one sect pursuit or manhunt sequence, then finalize the worldbuilding, character set, and first three chapter outlines.") -EnvMap $activeEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "unblock", $taskB.id) -EnvMap $activeEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null

$showB2 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $taskB.id -Wanted @("done") -TimeoutSeconds $FinalPassTimeoutSeconds
$runsB = Get-TaskRuns -EnvMap $activeEnv -TaskId $taskB.id
$projectB = $showB2.task.workspace_path
$chapterOutline = Read-Text (Join-Path $projectB "04_chapter_outline.md")
$feedbackB = Read-Text (Join-Path $projectB "feedback_log.md")

$scenarioB.final_status = $showB2.task.status
$scenarioB.workspace_path = $projectB
$scenarioB.chapter_outline_mentions_chase = ($chapterOutline -match "pursuit|manhunt|chase|hunt")
$scenarioB.feedback_mentions_chase = ($feedbackB -match "pursuit|manhunt|chase|hunt")
$scenarioB.run_outcomes = @(As-Array $runsB | ForEach-Object { $_.outcome })
$scenarioB.latest_summary = $showB2.latest_summary

$scenarioC = @{}
$promptC = "Route this request into a kanban task and create it immediately without follow-up questions: adapt that cyber-cultivation novel IP into a 3-episode short-video drama plan. Reference novel project path: $projectB. Reuse the locked setting and do not change canon."
$newC = New-OrchestratedTasks -EnvMap $activeEnv -Prompt $promptC -Provider $provider -Model $model
if ($newC.tasks.Count -lt 1) {
    throw "Scenario C expected at least 1 new task."
}

$scriptTaskC = $newC.tasks | Where-Object { $_.assignee -eq "scriptwriter" } | Select-Object -First 1
if (-not $scriptTaskC) {
    throw "Scenario C did not create a scriptwriter task."
}

$scenarioC.created_task_ids = @($newC.tasks | ForEach-Object { $_.id })
$scenarioC.scriptwriter_task_id = $scriptTaskC.id

$showC0 = Get-TaskShow -EnvMap $activeEnv -TaskId $scriptTaskC.id
$scenarioC.body_references_project = ([string]$showC0.task.body).Contains($projectB)

if ($showC0.task.status -eq "todo") {
    $parentTask = $newC.tasks | Where-Object { $_.assignee -eq "novelist" } | Select-Object -First 1
    if (-not $parentTask) {
        throw "Scenario C scriptwriter task is todo without a visible novelist parent."
    }

    Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null
    $showParent1 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $parentTask.id -Wanted @("blocked") -TimeoutSeconds $FirstPassTimeoutSeconds
    Invoke-Hermes -CliArgs @("kanban", "comment", $parentTask.id, "Use direction 1 and finalize the worldbuilding plus character set first so the later 3-episode drama adaptation has stable canon.") -EnvMap $activeEnv | Out-Null
    Invoke-Hermes -CliArgs @("kanban", "unblock", $parentTask.id) -EnvMap $activeEnv | Out-Null
    Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null
    $showParent2 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $parentTask.id -Wanted @("done") -TimeoutSeconds $FinalPassTimeoutSeconds
    $scenarioC.parent_task_id = $parentTask.id
    $scenarioC.parent_final_status = $showParent2.task.status
}

Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null
$showC1 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $scriptTaskC.id -Wanted @("blocked") -TimeoutSeconds $FirstPassTimeoutSeconds
$scenarioC.first_pass_status = $showC1.task.status
$scenarioC.first_pass_comment_count = (As-Array $showC1.comments).Count

Invoke-Hermes -CliArgs @("kanban", "comment", $scriptTaskC.id, "Choose direction 1 and deliver the final 3-episode short-drama plan while preserving the original novel canon.") -EnvMap $activeEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "unblock", $scriptTaskC.id) -EnvMap $activeEnv | Out-Null
Invoke-Hermes -CliArgs @("kanban", "dispatch") -EnvMap $activeEnv | Out-Null

$showC2 = Wait-TaskStatus -EnvMap $activeEnv -TaskId $scriptTaskC.id -Wanted @("done") -TimeoutSeconds $FinalPassTimeoutSeconds
$runsC = Get-TaskRuns -EnvMap $activeEnv -TaskId $scriptTaskC.id
$projectC = $showC2.task.workspace_path
$episodeIdeas = Read-Text (Join-Path $projectC "02_episode_ideas.md")
$feedbackC = Read-Text (Join-Path $projectC "feedback_log.md")

$scenarioC.final_status = $showC2.task.status
$scenarioC.workspace_path = $projectC
$scenarioC.episode_plan_mentions_three = ($episodeIdeas -match "3-episode|3 episode|three-episode|episode 1|ep1")
$scenarioC.feedback_mentions_canon = ($feedbackC -match "canon|locked setting|worldbuilding")
$scenarioC.run_outcomes = @(As-Array $runsC | ForEach-Object { $_.outcome })
$scenarioC.latest_summary = $showC2.latest_summary

$summary = [ordered]@{
    runtime = $runtime
    hermes_home = $hermesHome
    workspace = $workspace
    provider = $provider
    model = $model
    provider_probe_output = $probeOutput
    identities = $identities
    scenario_a = $scenarioA
    scenario_b = $scenarioB
    scenario_c = $scenarioC
}

$summaryJson = $summary | ConvertTo-Json -Depth 8
$summaryPath = Join-Path $runtime "formal_phase9_summary.json"
Set-Content -LiteralPath $summaryPath -Value $summaryJson -Encoding UTF8

Write-Host ""
Write-Host "Formal Phase 9 gate completed."
Write-Host "Summary JSON: $summaryPath"
Write-Host ""
$summaryJson
