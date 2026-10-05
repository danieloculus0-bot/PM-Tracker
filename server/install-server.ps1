param(
    [string]$InstallDir = "$env:ProgramData\PM Tracker"
)

$ErrorActionPreference = "Stop"
$exe = Join-Path $InstallDir "PM Tracker.exe"
$config = Join-Path $InstallDir "site_config.json"
$template = Join-Path $InstallDir "PM_Tracker_Import_Template.xlsx"
$data = Join-Path $InstallDir "pm_data.xlsx"

if (-not (Test-Path $exe)) { throw "PM Tracker.exe not found in $InstallDir" }
if (-not (Test-Path $config)) {
    Copy-Item (Join-Path $InstallDir "site_config.example.json") $config
}
if (-not (Test-Path $data) -and (Test-Path $template)) {
    Copy-Item $template $data
}

$cfg = Get-Content $config -Raw | ConvertFrom-Json
$port = [int]$cfg.port

$ruleName = "PM Tracker Server TCP $port"
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -Profile Domain,Private | Out-Null

$taskName = "PM Tracker Server"
$action = New-ScheduledTaskAction -Execute $exe -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Host "PM Tracker server installed and started from $InstallDir"
