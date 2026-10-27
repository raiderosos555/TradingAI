$ErrorActionPreference='Stop'
$projectPath='C:\TradingAI'
$taskName='TradingAI-Forward-Evidence'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw 'Task already exists; inspect before updating' }
$operatorName=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal=New-ScheduledTaskPrincipal -UserId $operatorName -LogonType Interactive -RunLevel Limited
$action=New-ScheduledTaskAction -Execute (Join-Path $projectPath '.venv\Scripts\pythonw.exe') `
    -Argument '"C:\TradingAI\research\forward_validation\collector.py" --root "C:\TradingAI\state\forward_validation\cohort-20261026-v1"' -WorkingDirectory $projectPath
$trigger=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval ([TimeSpan]::FromMinutes(2))
$logon=New-ScheduledTaskTrigger -AtLogOn -User $operatorName
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -Hidden -Priority 7
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($trigger,$logon) -Principal $principal `
    -Settings $settings -Description 'Passive forward evidence: ticks, contracts, calendar/news versions and broker fills. No order API; no model calls.' | Out-Null
Start-ScheduledTask -TaskName $taskName
Get-ScheduledTask -TaskName $taskName | Format-Table TaskName,State
