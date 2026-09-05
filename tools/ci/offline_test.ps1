param(
    [Parameter(Mandatory)][string]$Executable,
    [Parameter(Mandatory)][string]$RuleName,
    [Parameter(Mandatory)][ValidateSet('block','remove')][string]$Mode
)
$ErrorActionPreference = 'Stop'
if ($Mode -eq 'block') {
    New-NetFirewallRule -DisplayName $RuleName -Direction Outbound -Program $Executable -Action Block -Profile Any | Out-Null
}
else {
    Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}
