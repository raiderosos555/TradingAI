$ErrorActionPreference='Stop'
$labRoot=$PSScriptRoot
$pythonPath='C:\TradingAI\.venv\Scripts\python.exe'
$operatorName=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal=New-ScheduledTaskPrincipal -UserId $operatorName -LogonType Interactive -RunLevel Limited
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden
foreach($kind in @('crash','healthy')) {
    $taskName='TradingAI-Lab-RecoveryV2-'+$kind
    if(Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue){throw 'Lab task exists; inspect instead of overwriting'}
    $scenarioRoot=Join-Path $labRoot ('evidence\scheduler-'+$kind)
    & $pythonPath (Join-Path $labRoot 'make_config.py') $scenarioRoot --scenario $kind --real-backoff
    if($LASTEXITCODE -ne 0){throw 'Config preparation failed'}
    $configPath=Join-Path $scenarioRoot 'supervise.json'
    if($kind -eq 'healthy') {
        $config=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        $config.lifetime=240
        $config.heartbeat_timeout=180
        $config | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $configPath -Encoding utf8
    }
    & $pythonPath (Join-Path $labRoot 'supervisor.py') --config $configPath --initialize
    if($LASTEXITCODE -ne 0){throw 'Initialization failed'}
    $action=New-ScheduledTaskAction -Execute $pythonPath -Argument ('"'+(Join-Path $labRoot 'supervisor.py')+'" --config "'+$configPath+'"') -WorkingDirectory $labRoot
    $triggers=@((New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(10)) -RepetitionInterval ([TimeSpan]::FromMinutes(1))), (New-ScheduledTaskTrigger -AtLogOn -User $operatorName))
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description 'OFFLINE Recovery v2 integration; no MT5 import, no real orders.' | Out-Null
    Export-ScheduledTask -TaskName $taskName | Set-Content -LiteralPath (Join-Path $scenarioRoot 'task.xml')
}
Get-ScheduledTask -TaskName 'TradingAI-Lab-RecoveryV2-*' | Select-Object TaskName,State
