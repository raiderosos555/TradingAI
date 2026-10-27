$ErrorActionPreference='Stop'
foreach($kind in @('crash','healthy')) {
    $taskName='TradingAI-Lab-RecoveryV2-'+$kind
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if($task) {
        if($task.Actions.Arguments -notlike '*demo_recovery_v2*supervisor.py*'){throw 'Unexpected task action; refuse cleanup'}
        # Disable this LAB trigger only. No production tasks are addressed.
        Disable-ScheduledTask -TaskName $taskName | Out-Null
        Get-ScheduledTaskInfo -TaskName $taskName | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('evidence\scheduler-'+$kind+'\task-final.json'))
        $labState=Join-Path $PSScriptRoot ('evidence\scheduler-'+$kind+'\state\runtime')
        New-Item -ItemType Directory -Path $labState -Force | Out-Null
        New-Item -ItemType File -Path (Join-Path $labState 'DISABLED') -Force | Out-Null
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
}
