param(
    [string[]]$TaskName = @(
        "CourtAuction-Onbid-List",
        "CourtAuction-Onbid-Notice",
        "CourtAuction-Court-Crawl"
    )
)

$ErrorActionPreference = "Stop"

foreach ($name in $TaskName) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Output "MISSING $name"
        continue
    }
    $info = Get-ScheduledTaskInfo -TaskName $name
    Write-Output (@{
        task_name = $name
        state = $task.State.ToString()
        last_run_time = $info.LastRunTime
        last_task_result = $info.LastTaskResult
        next_run_time = $info.NextRunTime
    } | ConvertTo-Json -Compress)
}

Write-Output "Dry-run only. Register tasks manually after reviewing command lines."
