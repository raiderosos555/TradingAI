param([switch]$StartNow)
$ErrorActionPreference = 'Stop'
$projectPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonPath = Join-Path $projectPath '.venv\Scripts\pythonw.exe'
$configPath = Join-Path $projectPath 'config.demo.json'
$statePath = Join-Path $projectPath 'state'
$exchangePath = Join-Path $projectPath 'exchange'
if (-not (Test-Path -LiteralPath $pythonPath) -or -not (Test-Path -LiteralPath $configPath)) {
    throw 'Prepared environment/configuration missing'
}
if (-not (Test-Path -LiteralPath (Join-Path $statePath 'runtime-authorization.json'))) {
    throw 'Bounded operator authorization must be recorded before installation'
}
$operatorName = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $operatorName -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable `
    -RestartInterval ([TimeSpan]::FromMinutes(1)) -RestartCount 999 -MultipleInstances IgnoreNew -Hidden
$triggers = @(New-ScheduledTaskTrigger -AtLogOn -User $operatorName)
foreach ($role in @('baseline','engine')) {
    $taskName = 'TradingAI-DEMO-' + $role
    $arguments = '-m trading_ai.runtime --config "' + $configPath + '" --state "' + $statePath +
                 '" --exchange "' + $exchangePath + '" --role ' + $role
    $action = New-ScheduledTaskAction -Execute $pythonPath -Argument $arguments -WorkingDirectory $projectPath
    $description = 'Local bounded DEMO test. New entries only 25-30 Oct 2026; broker/Risk Manager gates remain mandatory. Interactive user session and MT5 required.'
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers `
        -Principal $principal -Settings $settings -Description $description -Force | Out-Null
    if ($StartNow) { Start-ScheduledTask -TaskName $taskName }
}
Get-ScheduledTask -TaskName 'TradingAI-DEMO-*' | Select-Object TaskName,State
