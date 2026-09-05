param([Parameter(Mandatory)][string]$Executable, [Parameter(Mandatory)][string]$RuleName)
$ErrorActionPreference = 'Stop'
$process = $null
try {
    New-NetFirewallRule -DisplayName $RuleName -Direction Outbound -Program $Executable -Action Block -Profile Any | Out-Null
    & $Executable --headless -- --self-test | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Offline self-test failed: $LASTEXITCODE" }
}
finally {
    Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}
