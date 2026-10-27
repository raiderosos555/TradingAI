$ErrorActionPreference='Stop'
$labRoot='C:\TradingAI\research\demo_recovery'
$original=Get-Content -LiteralPath (Join-Path $labRoot 'engine-task.before.xml') -Raw
foreach ($mode in @('Manual','Timed')) {
    $taskName='TradingAI-Lab-Recovery-'+$mode
    if(Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue){throw 'Lab task exists'}
    [xml]$definition=$original
    $definition.Task.RegistrationInfo.URI='\'+$taskName
    $definition.Task.RegistrationInfo.Description='Isolated exit-code fixture. No trading or terminal access.'
    $definition.Task.Actions.Exec.Arguments='"'+(Join-Path $labRoot 'lab_exit.py')+'" --out "'+(Join-Path $labRoot $mode)+'"'
    Register-ScheduledTask -TaskName $taskName -Xml $definition.OuterXml | Out-Null
    if($mode -eq 'Timed') {
        $trigger=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(15))
        Set-ScheduledTask -TaskName $taskName -Trigger $trigger | Out-Null
    } else {Start-ScheduledTask -TaskName $taskName}
    Export-ScheduledTask -TaskName $taskName | Set-Content -LiteralPath (Join-Path $labRoot ($mode+'-task.xml'))
}
Get-Date -Format o
