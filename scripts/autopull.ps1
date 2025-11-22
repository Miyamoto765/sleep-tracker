# Auto Git Pull for local repo
# Usage: run this script in background or register as Scheduled Task.
# It safely fetches and pulls remote if local is behind and there are no uncommitted changes.

param(
    [string]$RepoPath = "C:\Users\ahmed\OneDrive\Desktop\sleep-tracker",
    [int]$IntervalSeconds = 30,
    [switch]$Once
)

# Log file inside the repo scripts folder
$LogPath = Join-Path -Path $RepoPath -ChildPath "scripts\autopull.log"

function Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$timestamp] $Message"
    try { Add-Content -Path $LogPath -Value $line } catch {}
    Write-Host $line
}

function Find-Git {
    # Try to find git in common Windows installation locations
    $gitPaths = @(
        "git.exe",
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe",
        "$env:ProgramFiles\Git\cmd\git.exe",
        "$env:ProgramFiles(x86)\Git\cmd\git.exe"
    )
    
    foreach ($path in $gitPaths) {
        if ($path -eq "git.exe") {
            # Try using git from PATH first
            try {
                $null = Get-Command git -ErrorAction Stop
                return "git"
            } catch {
                continue
            }
        } elseif (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function Run-Once {
    Set-Location -LiteralPath $RepoPath

    # Find git executable
    $gitExe = Find-Git
    if (-not $gitExe) {
        Log "git not found. Please install Git or add it to PATH. Exiting."; return
    }
    
    # Test git works
    try {
        $null = & $gitExe --version 2>&1
    } catch {
        Log "git found but not working: $($_.Exception.Message). Exiting."; return
    }

    # Make sure repo path exists
    if (-not (Test-Path $RepoPath)) {
        Write-Host "Repo path not found: $RepoPath"; return
    }

    # Fetch remote updates
    Log "Fetching origin..."
    & $gitExe fetch origin --prune

    # Determine status between local and remote
    $local = & $gitExe rev-parse "@" 2>$null
    $remote = & $gitExe rev-parse "@{u}" 2>$null
    $base = & $gitExe merge-base "@" "@{u}" 2>$null

    if (-not $remote) {
        Log "No upstream configured for current branch. Skipping pull."; return
    }

    if ($local -eq $remote) {
        Log "Up-to-date. Nothing to do."; return
    }

    if ($local -eq $base) {
        # local is behind remote
        $porcelain = & $gitExe status --porcelain
        if ([string]::IsNullOrEmpty($porcelain)) {
            Log "Local clean and behind remote — pulling..."
            # Use fast-forward only to avoid unexpected merges
            $branch = & $gitExe rev-parse --abbrev-ref HEAD
            $res = & $gitExe pull --ff-only origin $branch 2>&1
            if ($LASTEXITCODE -eq 0) { Log "Pulled changes successfully: $res" } else { Log "Pull failed: $res" }
            return
        } else {
            Log "Local has uncommitted changes — skipping auto-pull to avoid conflicts."; return
        }
    }

    if ($remote -eq $base) {
        Log "Local has commits ahead of remote. Skipping auto-pull."; return
    }

    Log "Branches have diverged. Manual intervention required."; return
}

# If running in one-shot mode, just execute Run-Once and exit.
if ($Once) {
    Log "Run-Once mode requested. Executing single check."
    try { Run-Once } catch { Log "Error during run: $_" }
    Log "Run-Once completed. Exiting."
    exit 0
}

# Simple infinite loop with interval
Log "Starting autopull loop (interval ${IntervalSeconds}s)."
while ($true) {
    try { Run-Once } catch { Log "Error during run: $_" }
    Start-Sleep -Seconds $IntervalSeconds
}
