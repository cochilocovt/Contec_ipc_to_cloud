#Requires -Version 5.1
#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('ipc', 'laptop')]
    [string]$Device,
    [switch]$Disable
)

$ErrorActionPreference = 'Stop'
$addresses = @{ ipc = '100.89.184.100'; laptop = '100.100.157.108' }
$localAddress = $addresses[$Device]
$managerAddress = '100.73.242.65'
$ruleName = 'IPC-HomeLab-WinRM'
$blockName = 'IPC-HomeLab-WinRM-SetupBlock'
$stateDir = Join-Path $env:ProgramData 'IPC-HomeLab'
$statePath = Join-Path $stateDir 'remoting-state.json'
$policyPath = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
$policyName = 'LocalAccountTokenFilterPolicy'

if ($Disable) {
    # Close access before restoring local-account restrictions.
    Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue |
        Disable-NetFirewallRule | Out-Null
    if (-not (Test-Path -LiteralPath $statePath)) {
        throw 'Access closed, but the original policy snapshot is missing; inspect the policy manually.'
    }
    $saved = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($saved.policyPresent) {
        if ($saved.policyValue -notin @(0, 1)) { throw 'Unexpected saved policy value.' }
        Set-ItemProperty -LiteralPath $policyPath -Name $policyName -Value ([int]$saved.policyValue)
    } else {
        Remove-ItemProperty -LiteralPath $policyPath -Name $policyName -ErrorAction SilentlyContinue
    }
    Write-Output 'Lab remoting firewall access closed; original local-account policy restored.'
    Write-Output 'WinRM remains installed, with the default WinRM firewall rules disabled.'
    return
}

if (-not (Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -eq $localAddress)) {
    throw "This device does not own Tailscale address $localAddress. Check -Device and Tailscale."
}
if (Get-NetFirewallProfile | Where-Object { -not $_.Enabled -or $_.DefaultInboundAction -eq 'Allow' }) {
    throw 'Windows Firewall must be enabled and block unsolicited inbound connections on every profile.'
}

# Refuse to take over an existing remoting setup on first use.
if (-not (Test-Path -LiteralPath $statePath)) {
    if (Get-NetFirewallRule -Name 'WINRM*' -ErrorAction SilentlyContinue |
            Where-Object { $_.Enabled -eq 'True' -and $_.Direction -eq 'Inbound' }) {
        throw 'Existing enabled WinRM firewall rules found. Have the lead inspect them before setup.'
    }
    if (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue) {
        throw 'An existing lab rule has no policy snapshot. Have the lead inspect it before setup.'
    }
    $original = Get-ItemProperty -LiteralPath $policyPath
    $property = $original.PSObject.Properties[$policyName]
    if ($property -and $property.Value -notin @(0, 1)) { throw 'Unexpected local-account policy value.' }
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    @{
        policyPresent = ($null -ne $property)
        policyValue = $(if ($property) { [int]$property.Value } else { $null })
    } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
}

# Block both management ports while Enable-PSRemoting creates its broad default rules.
if (Get-NetFirewallRule -Name $blockName -ErrorAction SilentlyContinue) {
    throw 'A previous setup stopped with the safety block active. Report this before retrying.'
}
New-NetFirewallRule -Name $blockName -DisplayName 'IPC lab remoting setup safety block' `
    -Direction Inbound -Action Block -Protocol TCP -LocalPort 5985,5986 -Profile Any | Out-Null
try {
    Enable-PSRemoting -SkipNetworkProfileCheck -Force
    Get-NetFirewallRule -Name 'WINRM*' -ErrorAction SilentlyContinue |
        Where-Object Direction -eq 'Inbound' | Disable-NetFirewallRule | Out-Null
    Set-Item -Path WSMan:\localhost\Service\AllowUnencrypted -Value $false
    Set-Item -Path WSMan:\localhost\Service\Auth\Basic -Value $false
    Set-Item -Path WSMan:\localhost\Service\Auth\Negotiate -Value $true
    New-ItemProperty -LiteralPath $policyPath -Name $policyName -PropertyType DWord -Value 1 -Force | Out-Null

    $rule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
    if ($rule) { $rule | Remove-NetFirewallRule }
    New-NetFirewallRule -Name $ruleName -DisplayName 'IPC lab WinRM (desktop Tailscale only)' `
        -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5985 -Profile Any `
        -LocalAddress $localAddress -RemoteAddress $managerAddress -Service WinRM | Out-Null
    Remove-NetFirewallRule -Name $blockName
} catch {
    # Leave the block active on any error, including a partially completed setup.
    Write-Warning 'Setup failed. The safety block remains active; report the error to the lead.'
    throw
}

Write-Output "READY: $env:COMPUTERNAME ($localAddress), WinRM 5985 accepts only $managerAddress."
Write-Output "Current Windows account: $env:COMPUTERNAME\$env:USERNAME"
Write-Output 'Use an administrator account with a Windows password (a PIN does not work).'
Write-Output 'Local administrators temporarily receive full remote tokens. Run this script with -Disable after setup.'
