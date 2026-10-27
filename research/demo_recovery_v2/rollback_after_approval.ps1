param([switch]$Approved)
$ErrorActionPreference='Stop'
if(-not $Approved){throw 'Rollback requires operator approval; no state will be changed.'}
$projectPath='C:\TradingAI';$pythonPath=Join-Path $projectPath '.venv\Scripts\python.exe'
$taskName='TradingAI-DEMO-Recovery';$disabledPath=Join-Path $projectPath 'state\runtime\DISABLED'
$migrationLock=[System.IO.File]::Open((Join-Path $PSScriptRoot 'deployment\migration.lock'),'OpenOrCreate','ReadWrite','None')
try {
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if($task) {
        if($task.Actions.Arguments -notlike '*demo_recovery_v2*release*supervisor.py*'){throw 'Unexpected task; refuse rollback'}
        Disable-ScheduledTask -TaskName $taskName | Out-Null
    }
    if(Test-Path -LiteralPath $disabledPath){throw 'Existing DISABLED requires operator review; never remove an unowned stop marker'}
    New-Item -ItemType File -Path $disabledPath | Out-Null
    $deadline=(Get-Date).AddSeconds(180);$free=$false
    do {
        Start-Sleep -Seconds 2
        & $pythonPath (Join-Path $PSScriptRoot 'deployment_guard.py') --locks-free *> (Join-Path $PSScriptRoot 'evidence\rollback-lock-check.txt')
        $free=$LASTEXITCODE -eq 0
    } while((-not $free) -and (Get-Date) -lt $deadline)
    if(-not $free){throw 'Cannot establish safe shutdown. Never kill a hung owner; manual diagnosis required.'}
    # Source, config, journal and authorizations were never replaced: no DB restore.
    Remove-Item -LiteralPath $disabledPath
    Enable-ScheduledTask -TaskName 'TradingAI-DEMO-engine' | Out-Null
    Start-ScheduledTask -TaskName 'TradingAI-DEMO-engine'
    Write-Output 'Original task restarted; journal, quarantine and all permissions preserved.'
} finally {$migrationLock.Dispose()}
