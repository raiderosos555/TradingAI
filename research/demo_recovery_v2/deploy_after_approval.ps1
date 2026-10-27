param([switch]$Approved)
$ErrorActionPreference='Stop'
if(-not $Approved){throw 'Not deployed. Explicit owner approval is required before invoking -Approved.'}
$projectPath='C:\TradingAI'
$pythonPath=Join-Path $projectPath '.venv\Scripts\python.exe'
$configPath=Join-Path $PSScriptRoot 'deployment\supervise.json'
$releasePath=Join-Path $PSScriptRoot 'release'
$disabledPath=Join-Path $projectPath 'state\runtime\DISABLED'
$taskName='TradingAI-DEMO-Recovery'
$migrationLock=[System.IO.File]::Open((Join-Path $PSScriptRoot 'deployment\migration.lock'),'OpenOrCreate','ReadWrite','None')
try {
    if(Test-Path -LiteralPath $disabledPath){throw 'Existing DISABLED is owned by operator; do not remove it'}
    if(Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue){throw 'Recovery task exists; inspect before another migration'}
    $expected=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'backup\engine-task.xml') -Raw).Trim()
    if((Export-ScheduledTask -TaskName 'TradingAI-DEMO-engine').Trim() -ne $expected){throw 'Engine task changed since review'}
    & $pythonPath (Join-Path $PSScriptRoot 'deployment_guard.py') --preflight
    if($LASTEXITCODE -ne 0){throw 'Migration preflight failed'}
    Disable-ScheduledTask -TaskName 'TradingAI-DEMO-engine' | Out-Null
    New-Item -ItemType File -Path $disabledPath | Out-Null
    # Cooperative shutdown only. No Stop-Process/Stop-ScheduledTask.
    $deadline=(Get-Date).AddSeconds(180)
    $free=$false
    do {
        Start-Sleep -Seconds 2
        & $pythonPath (Join-Path $PSScriptRoot 'deployment_guard.py') --locks-free *> (Join-Path $PSScriptRoot 'evidence\migration-lock-check.txt')
        $free=$LASTEXITCODE -eq 0
    } while((-not $free) -and (Get-Date) -lt $deadline)
    if(-not $free){throw 'Owner has not stopped safely. Leave DISABLED and task disabled; operator diagnosis required, never kill by heartbeat.'}
    & $pythonPath (Join-Path $releasePath 'supervisor.py') --config $configPath --initialize
    if($LASTEXITCODE -ne 0){throw 'Durable supervisor initialization failed; do not reset its state'}
    $operatorName=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal=New-ScheduledTaskPrincipal -UserId $operatorName -LogonType Interactive -RunLevel Limited
    $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden
    $action=New-ScheduledTaskAction -Execute $pythonPath -Argument ('"'+(Join-Path $releasePath 'supervisor.py')+'" --config "'+$configPath+'"') -WorkingDirectory $releasePath
    $triggers=@((New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval ([TimeSpan]::FromMinutes(1))), (New-ScheduledTaskTrigger -AtLogOn -User $operatorName))
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description 'Approved DEMO Recovery v2. Same journal, risk, authorization; no LIVE.' | Out-Null
    Export-ScheduledTask -TaskName $taskName | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence\deployed-task.xml')
    Remove-Item -LiteralPath $disabledPath
    Start-ScheduledTask -TaskName $taskName
    Write-Output 'Recovery started. Operator must verify one owner, clock gates, unchanged quarantine, position protection and collector continuity.'
} finally {$migrationLock.Dispose()}
