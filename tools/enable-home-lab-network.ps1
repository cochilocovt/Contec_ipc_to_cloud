#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory = $true)]
    [string]$InterfaceAlias,
    [Parameter(Mandatory = $true)]
    [System.Net.IPAddress]$LanAddress
)

$ErrorActionPreference = 'Stop'
$address = $LanAddress.IPAddressToString
$adapter = Get-NetAdapter -Name $InterfaceAlias
if ($adapter.Status -ne 'Up') { throw 'The selected network adapter is not connected.' }
$local = Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -eq $address }
if (-not $local) { throw 'The supplied LAN address does not belong to this adapter.' }

# Run only for the trusted home network; this also enables the Private MQTT rule.
Set-NetConnectionProfile -InterfaceIndex $adapter.InterfaceIndex -NetworkCategory Private
$name = 'IPC-HomeLab-MQTT'
$rule = Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue
if ($rule) {
    $rule | Set-NetFirewallRule -Enabled True -Direction Inbound -Action Allow -Profile Private
    $rule | Get-NetFirewallPortFilter | Set-NetFirewallPortFilter -Protocol TCP -LocalPort 1883
    $rule | Get-NetFirewallAddressFilter |
        Set-NetFirewallAddressFilter -LocalAddress $address -RemoteAddress LocalSubnet
    $rule | Get-NetFirewallInterfaceFilter |
        Set-NetFirewallInterfaceFilter -InterfaceAlias $InterfaceAlias
} else {
    New-NetFirewallRule -Name $name -DisplayName 'IPC home lab MQTT (home LAN only)' `
        -Direction Inbound -Action Allow -Enabled True -Profile Private `
        -Protocol TCP -LocalPort 1883 -LocalAddress $address `
        -RemoteAddress LocalSubnet -InterfaceAlias $InterfaceAlias | Out-Null
}
Write-Output "Home-lab MQTT firewall configured for $InterfaceAlias at ${address}:1883."
