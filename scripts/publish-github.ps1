# Publish Machine Eden to GitHub
# Prerequisites: gh auth login (https://github.com/login/device)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
            [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "Checking GitHub authentication..."
gh auth status | Out-Null

$RepoName = "machine-eden"
$Visibility = "public"  # change to "private" if preferred

Write-Host "Creating GitHub repository: $RepoName ($Visibility)..."
gh repo create $RepoName --source=. --remote=origin --$Visibility --description "A self-evolving machine society simulator" --push

Write-Host ""
Write-Host "Done! Repository URL:"
gh repo view --web 2>$null
gh repo view --json url -q .url
