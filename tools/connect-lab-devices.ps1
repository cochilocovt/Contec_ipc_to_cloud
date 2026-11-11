#Requires -Version 5.1
#Requires -RunAsAdministrator
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$devices = @(
    @{ Name = 'ipc'; Address = '100.89.184.100' },
    @{ Name = 'laptop'; Address = '100.100.157.108' }
)
if (-not (Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -eq '100.73.242.65')) {
    throw 'Run this only on home-desktop, signed in as the same Windows user running Codex.'
}

# DPAPI protects each saved password for this Windows user on this PC.
$accessDir = Join-Path $env:LOCALAPPDATA 'IPC-HomeLab\access'
New-Item -ItemType Directory -Path $accessDir -Force | Out-Null
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = New-Object System.Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true, $false)
$acl.SetOwner($identity)
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    $identity, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')))
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    ([System.Security.Principal.SecurityIdentifier]'S-1-5-18'), 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')))
Set-Acl -LiteralPath $accessDir -AclObject $acl

Start-Service WinRM
$trustPath = 'WSMan:\localhost\Client\TrustedHosts'
$oldTrust = [string](Get-Item -Path $trustPath).Value
$trustBackup = Join-Path $accessDir 'trusted-hosts-before.txt'
if (-not (Test-Path -LiteralPath $trustBackup)) {
    [System.IO.File]::WriteAllText($trustBackup, $oldTrust)
}
$hostsToTrust = @($oldTrust -split ',' | Where-Object { $_ }) + @($devices | ForEach-Object { $_.Address })
Set-Item -Path $trustPath -Value (($hostsToTrust | Select-Object -Unique) -join ',') -Force

foreach ($device in $devices) {
    $session = $null
    $credential = Get-Credential -Message "Administrator WINDOWS password for $($device.Name). Use COMPUTER\username, not a PIN."
    if ($null -eq $credential) { throw 'Credential entry cancelled.' }
    try {
        $session = New-PSSession -ComputerName $device.Address -Authentication Negotiate -Credential $credential
        $check = Invoke-Command -Session $session -ScriptBlock {
            $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
                [Security.Principal.WindowsBuiltInRole]::Administrator)
            if (-not $admin) { throw 'The connected account does not have an administrator token.' }
            @{ Computer = $env:COMPUTERNAME; PowerShell = $PSVersionTable.PSVersion.ToString() }
        }
        $credential | Export-Clixml -LiteralPath (Join-Path $accessDir ($device.Name + '.credential.xml'))
        Write-Output "CONNECTED: $($device.Name), computer $($check.Computer), PowerShell $($check.PowerShell)"
    } finally {
        if ($session) { Remove-PSSession -Session $session }
        $credential = $null
    }
}
Write-Output 'Both connections verified. Tell Codex: access is ready. Do not send passwords.'
