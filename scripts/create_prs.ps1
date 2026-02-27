<#
Creates GitHub PRs for prepared branches using the GH CLI.

Usage (locally):
  .\scripts\create_prs.ps1

Requirements:
  - GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
  - The branches must already exist on `origin` (we pushed them earlier).
#>
param(
    [string]$remote = 'origin',
    [string[]]$branches = @(
        'fix/enrich-idempotent-web-extract',
        'chore/ci-secrets-checklist',
        'feat/post-deploy-smoke-check'
    )
)

function Get-GhPath {
    return (Get-Command gh -ErrorAction SilentlyContinue).Path
}

$ghPath = Get-GhPath
if ($ghPath) {
    foreach ($b in $branches) {
        Write-Host "Processing branch '$b' using gh..."
        switch ($b) {
            'fix/enrich-idempotent-web-extract' { $title = 'Fix: Enrichment idempotent WebExtract insert' }
            'chore/ci-secrets-checklist' { $title = 'Chore: CI secrets checklist and docs' }
            'feat/post-deploy-smoke-check' { $title = 'Feat: Post-deploy smoke-check workflow' }
            default { $title = "PR: $b" }
        }

        $body = @()
        $body += "This PR was prepared by the automation assistant."
        $body += "Branch: $b"
        $body += ''
        $body += 'Checklist:'
        $body += '- Run CI and confirm checks pass'
        $body += '- Add required GitHub secrets if the workflow needs them (see docs/operations/CI_SECRETS.md)'
        $body += '- Review changes and merge when green'

        $bodyText = $body -join "`n"

        # If a PR already exists for this head, skip creating a new one.
        try {
            $existing = gh pr view --head "$($remote):$b" --json url --jq .url 2>$null
        } catch {
            $existing = $null
        }
        
        if ($existing) {
            Write-Host "PR already exists for '$b': $existing"
            continue
        }

        $createOutput = $null
        try {
            $createOutput = gh pr create --base main --head "$($remote):$b" --title "$title" --body "$bodyText" --json number,url 2>$null
        } catch {
            $createOutput = $null
        }

        if (-not $createOutput) {
            Write-Warning "Failed to create PR for $b (it might already exist or gh returned an error)."
            continue
        }

        $pr = $createOutput | ConvertFrom-Json
        if ($pr.url) { Write-Host "PR created: $($pr.url)" }

        # Try to add automation label; create it if missing.
        try {
            gh pr edit $($pr.number) --add-label automation 2>$null
        } catch {
            Write-Host "Label 'automation' missing; attempting to create it..."
            try {
                gh label create automation --description "Automation-created PRs" --color ffa500 2>$null
                gh pr edit $($pr.number) --add-label automation 2>$null
                Write-Host "Label 'automation' created and applied."
            } catch {
                Write-Warning "Could not create or apply label 'automation'. You can add it manually in the PR UI."
            }
        }
    }
    Write-Host 'Done (gh path: ' $ghPath ')'
} else {
    Write-Warning 'GH CLI not found. Falling back to opening PR URLs in your browser.'
    # Determine remote origin repo (owner/repo)
    $originUrl = git config --get remote.origin.url
    if (-not $originUrl) {
        Write-Error 'Unable to determine remote origin URL. Please run this script from a git repo with origin set.'
        exit 3
    }

    # Parse owner/repo from common git remote URL formats
    function Parse-OwnerRepo($url) {
        if ($url -match 'git@github.com:(?<owner>[^/]+)/(?<repo>[^.]+)(\.git)?') {
            return "$($Matches.owner)/$($Matches.repo)"
        }
        if ($url -match 'https?://github.com/(?<owner>[^/]+)/(?<repo>[^/]+)(\.git)?') {
            return "$($Matches.owner)/$($Matches.repo)"
        }
        return $null
    }

    $ownerRepo = Parse-OwnerRepo $originUrl
    if (-not $ownerRepo) {
        Write-Error "Unsupported origin URL format: $originUrl"
        exit 4
    }

    foreach ($b in $branches) {
        Write-Host "Preparing browser PR for branch '$b'..."
        switch ($b) {
            'fix/enrich-idempotent-web-extract' { $title = 'Fix: Enrichment idempotent WebExtract insert' }
            'chore/ci-secrets-checklist' { $title = 'Chore: CI secrets checklist and docs' }
            'feat/post-deploy-smoke-check' { $title = 'Feat: Post-deploy smoke-check workflow' }
            default { $title = "PR: $b" }
        }

        $body = @()
        $body += "This PR was prepared by the automation assistant."
        $body += "Branch: $b"
        $body += ''
        $body += 'Checklist:'
        $body += '- Run CI and confirm checks pass'
        $body += '- Add required GitHub secrets if the workflow needs them (see docs/operations/CI_SECRETS.md)'
        $body += '- Review changes and merge when green'

        $bodyText = $body -join "`n"

        $titleEnc = [uri]::EscapeDataString($title)
        $bodyEnc = [uri]::EscapeDataString($bodyText)
        $compare = "https://github.com/$ownerRepo/compare/main...$b?expand=1&title=$titleEnc&body=$bodyEnc"

        Write-Host "Opening: $compare"
        Start-Process $compare
    }

    Write-Host 'Opened PR creation pages in your default browser. Review and submit each PR manually.'
}
