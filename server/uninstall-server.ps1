param(
    [string]$InstallDir = "$env:ProgramData\PM Tracker"
)
$taskName = "PM Tracker Server"
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Get-NetFirewallRule | Where-Object DisplayName -like "PM Tracker Server TCP *" | Remove-NetFirewallRule -ErrorAction SilentlyContinue
Write-Host "PM Tracker service task and firewall rule removed. Runtime data in $InstallDir was preserved."
