$ErrorActionPreference='Stop'
$projectPath=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$operatorName=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal=New-ScheduledTaskPrincipal -UserId $operatorName -LogonType Interactive -RunLevel Limited
$action=New-ScheduledTaskAction -Execute (Join-Path $projectPath '.venv\Scripts\pythonw.exe') `
    -Argument ('"'+(Join-Path $projectPath 'tools\collect_news.py')+'"') -WorkingDirectory $projectPath
$trigger=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval ([TimeSpan]::FromMinutes(15))
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::FromMinutes(2)) -MultipleInstances IgnoreNew -Hidden
Register-ScheduledTask -TaskName TradingAI-News -Action $action -Trigger $trigger -Principal $principal `
    -Settings $settings -Description 'Public RSS context, every 15 minutes; no broker access or trade permission.' -Force | Out-Null
Start-ScheduledTask -TaskName TradingAI-News
Get-ScheduledTask -TaskName TradingAI-News | Select-Object TaskName,State
