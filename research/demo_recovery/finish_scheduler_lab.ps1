$ErrorActionPreference='Stop'
$labRoot='C:\TradingAI\research\demo_recovery'
$rows=foreach($mode in @('Manual','Timed')) {
    $name='TradingAI-Lab-Recovery-'+$mode
    $info=Get-ScheduledTaskInfo -TaskName $name
    [ordered]@{
        task=$name
        at=(Get-Date).ToUniversalTime().ToString('o')
        last_run=$info.LastRunTime.ToUniversalTime().ToString('o')
        last_result=$info.LastTaskResult
        starts=@(Get-Content -LiteralPath (Join-Path $labRoot ($mode+'\starts.jsonl')) | ForEach-Object {$_ | ConvertFrom-Json})
    }
}
@($rows) | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $labRoot 'scheduler-lab-result.json')
Get-Content -LiteralPath (Join-Path $labRoot 'scheduler-lab-result.json')
foreach($mode in @('Manual','Timed')) {
    Unregister-ScheduledTask -TaskName ('TradingAI-Lab-Recovery-'+$mode) -Confirm:$false
}
