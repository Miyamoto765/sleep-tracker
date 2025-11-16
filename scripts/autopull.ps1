# Auto Git Pull for local repo
# Usage: run this script in background or register as Scheduled Task.
# It safely fetches and pulls remote if local is behind and there are no uncommitted changes.

param(
    [string]$RepoPath = "C:\Users\ahmed\OneDrive\Desktop\sleep-tracker",
    [int]$IntervalSeconds = 300
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
function Run-Once {
    Set-Location -LiteralPath $RepoPath

    # Ensure git is available
    try {
        git --version > $null 2>&1
    } catch {
        Log "git not found in PATH. Exiting."; return
    }

    # Make sure repo path exists
    if (-not (Test-Path $RepoPath)) {
        Write-Host "Repo path not found: $RepoPath"; return
    }

    # Fetch remote updates
    Log "Fetching origin..."
    git fetch origin --prune

    # Determine status between local and remote
    $local = git rev-parse @ 2>$null
    $remote = git rev-parse @{u} 2>$null
    $base = git merge-base @ @{u} 2>$null

    if (-not $remote) {
        Log "No upstream configured for current branch. Skipping pull."; return
    }

    if ($local -eq $remote) {
        Log "Up-to-date. Nothing to do."; return
    }

    if ($local -eq $base) {
        # local is behind remote
        $porcelain = git status --porcelain
        if ([string]::IsNullOrEmpty($porcelain)) {
            Log "Local clean and behind remote — pulling..."
            # Use fast-forward only to avoid unexpected merges
            $branch = git rev-parse --abbrev-ref HEAD
            $res = git pull --ff-only origin $branch 2>&1
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

# Simple infinite loop with interval
while ($true) {
    try { Run-Once } catch { Log "Error during run: $_" }
    Start-Sleep -Seconds $IntervalSeconds
}
