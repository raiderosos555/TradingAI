# Prepared only. Requires owner's approval before execution.
$ErrorActionPreference = 'Stop'
$taskName = 'TradingAI-EIA-20261104-Shadow'
$projectRoot = 'C:\TradingAI'
$scriptRoot = Join-Path $projectRoot 'research\eia_data_acceptance'
$protocolPath = Join-Path $scriptRoot 'eia_pilot_20261104.json'
$pilot = Get-Content -LiteralPath $protocolPath -Raw | ConvertFrom-Json
$plannedUtc = [DateTimeOffset]::Parse($pilot.start_utc)
$localStart = $plannedUtc.LocalDateTime
if ($localStart.ToString('yyyy-MM-dd HH:mm') -ne '2026-11-04 16:25') {
    throw 'Local timezone differs from reviewed Warsaw schedule'
}
if ([DateTimeOffset]::UtcNow -ge $plannedUtc) { throw 'Past pilot start; no late registration' }
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw 'Task exists; refuse overwrite' }
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runner = Join-Path $scriptRoot 'run_eia_window.py'
$outputPath = Join-Path $scriptRoot 'private\forward-20261104'
$arguments = '"{0}" --protocol "{1}" --out "{2}"' -f $runner,$protocolPath,$outputPath
$action = New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At $localStart
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 50)
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'One EIA source capture window; SHADOW; no MT5 or orders' | Out-Null
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
