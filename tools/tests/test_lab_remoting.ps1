# Run with Windows PowerShell 5.1. All system mutations below are mocked.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$serverPath = Join-Path $repoRoot 'tools\enable-lab-remoting.ps1'
$clientPath = Join-Path $repoRoot 'tools\connect-lab-devices.ps1'
foreach ($path in @($serverPath, $clientPath)) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
    if ($errors) { throw ($errors | Out-String) }
    Write-Output "PASS: Windows PowerShell parser: $(Split-Path $path -Leaf)"
}
$source = [System.IO.File]::ReadAllText($serverPath)
# Remove only the launcher requirements: tests use mocks without administrator rights.
$body = [scriptblock]::Create(($source -replace '(?m)^#Requires[^\r\n]*', ''))

function Assert($condition, $message) { if (-not $condition) { throw $message } }
function Reset-Test {
    $script:events = [System.Collections.Generic.List[string]]::new()
    $script:blocked = $false
    $script:enabled = $false
    $script:failEnable = $false
    $script:hasAddress = $true
    $script:firewallEnabled = $true
    $script:existingRules = $false
    $script:hasState = $false
}

# Shadow every system/filesystem mutation used by the server script.
function Get-NetIPAddress { if ($script:hasAddress) { [pscustomobject]@{ IPAddress = '100.89.184.100' } } }
function Get-NetFirewallProfile { [pscustomobject]@{ Enabled = $script:firewallEnabled; DefaultInboundAction = 'Block' } }
function Get-NetFirewallRule {
    param($Name, $ErrorAction)
    if ($Name -eq 'WINRM*') {
        [pscustomobject]@{ Name = 'WINRM-HTTP-In-TCP'; Direction = 'Inbound'; Enabled = $(if ($script:existingRules) { 'True' } else { 'False' }) }
    }
}
function Test-Path { param($LiteralPath) $script:hasState }
function Get-ItemProperty { [pscustomobject]@{ Existing = 1 } }
function New-Item { $script:events.Add('snapshot-directory') }
function Set-Content {
    param($LiteralPath, $Encoding, [Parameter(ValueFromPipeline=$true)]$Value)
    process { $script:events.Add('snapshot') }
}
function New-NetFirewallRule {
    param($Name, $DisplayName, $Direction, $Action, $Protocol, $LocalPort, $Profile, $LocalAddress, $RemoteAddress, $Service)
    if ($Action -eq 'Block') { $script:blocked = $true; $script:events.Add('block') }
    if ($Action -eq 'Allow') {
        Assert $script:blocked 'Allow rule created before safety block'
        Assert ($LocalAddress -eq '100.89.184.100') 'Wrong local address'
        Assert ($RemoteAddress -eq '100.73.242.65') 'Wrong manager address'
        Assert ($LocalPort -eq 5985 -and $Service -eq 'WinRM') 'Wrong management port/service'
        $script:enabled = $true
        $script:events.Add('allow')
    }
}
function Enable-PSRemoting {
    Assert $script:blocked 'Enable-PSRemoting ran without safety block'
    if ($script:failEnable) { throw 'simulated enable failure' }
    $script:events.Add('enable-remoting')
}
function Disable-NetFirewallRule {
    param([Parameter(ValueFromPipeline=$true)]$InputObject)
    process { $script:events.Add('disable-rule') }
}
function Set-Item {
    param($Path, $Value)
    Assert $script:blocked 'Authentication configuration changed without safety block'
    if ($Path -like '*AllowUnencrypted' -or $Path -like '*Auth\Basic') {
        Assert ($Value -eq $false) 'Weak authentication setting enabled'
    }
    $script:events.Add('auth-setting')
}
function New-ItemProperty { $script:events.Add('set-token-policy') }
function Remove-NetFirewallRule {
    param($Name, [Parameter(ValueFromPipeline=$true)]$InputObject)
    process {
        if ($Name -eq 'IPC-HomeLab-WinRM-SetupBlock') {
            Assert $script:enabled 'Safety block removed before scoped allow rule'
            $script:blocked = $false
            $script:events.Add('unblock')
        }
    }
}
function Get-Content { '{"policyPresent":false,"policyValue":null}' }
function Remove-ItemProperty { $script:events.Add('restore-token-policy') }
function Set-ItemProperty { $script:events.Add('restore-token-policy') }

Reset-Test
& $body -Device ipc | Out-Null
Assert (-not $script:blocked -and $script:enabled) 'Successful setup did not open scoped access'
Assert ($script:events.IndexOf('disable-rule') -lt $script:events.IndexOf('allow')) 'Defaults disabled too late'
Write-Output 'PASS: successful setup ordering and exact firewall/authentication scope'

Reset-Test
$script:failEnable = $true
try { & $body -Device ipc -WarningAction SilentlyContinue | Out-Null; throw 'Expected failure missing' }
catch { Assert ($_.Exception.Message -eq 'simulated enable failure') 'Unexpected failure' }
Assert ($script:blocked -and -not $script:enabled) 'Failure did not leave safety block active'
Write-Output 'PASS: partial setup fails closed'

foreach ($scenario in @('wrong-address', 'firewall-disabled', 'existing-remoting')) {
    Reset-Test
    if ($scenario -eq 'wrong-address') { $script:hasAddress = $false }
    if ($scenario -eq 'firewall-disabled') { $script:firewallEnabled = $false }
    if ($scenario -eq 'existing-remoting') { $script:existingRules = $true }
    $failed = $false
    try { & $body -Device ipc | Out-Null } catch { $failed = $true }
    Assert $failed "Preflight did not reject $scenario"
    Assert ($script:events.Count -eq 0) "Preflight changed state: $scenario"
    Write-Output "PASS: $scenario rejected without changes"
}

Reset-Test
$script:hasState = $true
& $body -Device ipc -Disable | Out-Null
Assert ($script:events -contains 'restore-token-policy') 'Original token policy was not restored'
Write-Output 'PASS: disable restores original token policy'
