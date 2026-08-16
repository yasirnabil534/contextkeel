<#
    contextkeel installer - Windows.

        irm https://raw.githubusercontent.com/yasirnabil534/contextkeel/main/bootstrap/install.ps1 | iex

    Requires nothing pre-installed. Non-interactive, idempotent, quiet.

    Targets Windows PowerShell 5.1 (still the default on many machines) as
    well as PowerShell 7+, so it avoids 7-only syntax: no ternaries, no ??,
    no ?. operators.
#>

$ErrorActionPreference = 'Stop'

# Tried in order unless CONTEXTKEEL_REF overrides. PyPI first so publishing
# the package makes this work with no edit; the repository tarball serves
# until then (a tarball, not git+https, so git is not made a requirement).
$Package     = $env:CONTEXTKEEL_REF
$PypiName    = 'contextkeel'
$RepoTarball = 'https://github.com/yasirnabil534/contextkeel/archive/refs/heads/main.tar.gz'
$PythonMin = '3.11'
$BinDir    = Join-Path $env:USERPROFILE '.local\bin'

function Say([string]$Message) { Write-Host $Message }

function Die([string]$Message) {
    Write-Host ''
    Write-Error $Message
    exit 1
}

function Have([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { return $false }
    # Reject the Microsoft Store alias stub: a zero-byte shim under
    # WindowsApps that opens the Store instead of running Python. It reports
    # as present and then silently breaks every install that trusts it.
    if ($cmd.Source -and $cmd.Source -like '*WindowsApps*' -and (Get-Item $cmd.Source).Length -eq 0) {
        return $false
    }
    return $true
}

function Ensure-Uv {
    if (Have 'uv') { return $true }
    Say 'Setting up (1/3): installing the package manager...'
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression | Out-Null
    } catch {
        return $false
    }
    $env:Path = "$BinDir;$env:Path"
    return (Have 'uv')
}

function Ensure-SystemPython {
    if (Have 'python') { return $true }
    Say 'Setting up: installing Python...'
    if (Have 'winget') {
        winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements 2>$null | Out-Null
        $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
        return (Have 'python')
    }
    return $false
}

function Try-Install([string]$Source) {
    # uv fetches a managed CPython when the host has none new enough, so this
    # succeeds on a machine with no Python at all.
    uv tool install --python $PythonMin --force $Source 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { return $true }
    uv tool install --force $Source 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Install-Tool {
    if (Have 'uv') {
        if ($Package) { return (Try-Install $Package) }
        if (Try-Install $PypiName) { return $true }
        if (Try-Install $RepoTarball) { return $true }
        return $false
    }
    if (-not (Ensure-SystemPython)) { return $false }
    $source = if ($Package) { $Package } else { $RepoTarball }
    python -m pip install --user --upgrade $source 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Add-ToPath {
    if ($env:Path -split ';' -contains $BinDir) { return }
    $env:Path = "$BinDir;$env:Path"
    $userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    if ($userPath -notlike "*$BinDir*") {
        # setx truncates above 1024 chars; use the .NET API instead.
        [System.Environment]::SetEnvironmentVariable('Path', "$userPath;$BinDir", 'User')
    }
}

# ---------------------------------------------------------------------------

if ((Have 'ckeel') -and ($env:CONTEXTKEEL_FORCE -ne '1')) {
    Say 'Already installed. Updating...'
} else {
    if (-not (Ensure-Uv)) { Say 'Setting up: falling back to a system Python...' }
    Say 'Setting up (2/3): installing contextkeel...'
    if (-not (Install-Tool)) {
        Die 'Install failed. See https://github.com/yasirnabil534/contextkeel#what-you-need for the manual steps.'
    }
}

Add-ToPath

if (-not (Have 'ckeel')) {
    Die "Installed, but 'ckeel' is not on PATH yet. Open a new terminal and run: ckeel init"
}

Say 'Setting up (3/3): preparing this project...'
ckeel init --auto
if ($LASTEXITCODE -ne 0) {
    Die 'Installed successfully, but setup did not finish. Run: ckeel doctor --fix'
}

Say ''
Say "Done. Your project is set up - run 'ckeel status' any time."
