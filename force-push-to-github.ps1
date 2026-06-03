# Helper script to force-push the local history over the placeholder remote commit.
# This is safe here because:
# - You own the repo
# - The only remote commit is a trivial "Initial commit" placeholder README
# - Your local history is the real project (full code + good README + features)

$git = "C:\Users\Laine\AppData\Local\GitHubDesktop\app-3.3.4\resources\app\git\cmd\git.exe"

Write-Host "This will FORCE push your local commits to GitHub, replacing the remote history."
Write-Host "The remote only has a single placeholder commit right now."
$confirm = Read-Host "Type YES to continue"

if ($confirm -ne "YES") {
    Write-Host "Aborted."
    exit
}

& $git push --force-with-lease -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Success! Your full project history is now on GitHub."
    Write-Host "Go back to GitHub Desktop and click Fetch (or restart it) to see the updated view."
} else {
    Write-Host ""
    Write-Host "Push failed. Common causes:"
    Write-Host " - Authentication: In the shell that GitHub Desktop opens, it should be logged in."
    Write-Host " - If it asks for password, use a Personal Access Token from https://github.com/settings/tokens (repo scope)."
}