<#
Examples:
  # File-based lab-pack
  $state = Join-Path $env:TEMP "state.md"
  "hello`nworld" | Set-Content -Encoding UTF8 -NoNewline $state
  & "$PSScriptRoot\prox-mesh.ps1" lab-pack "Linux privesc via SUID" --state-file $state --host proxkb --sources cpts --limit 10 --queries 6

  # Piped lab-pack (IMPORTANT: use -Raw so it is ONE pipeline object)
  Get-Content -Raw -Encoding UTF8 $state |
    & "$PSScriptRoot\prox-mesh.ps1" lab-pack "Linux privesc via SUID" --state-file - --host proxkb --sources cpts --limit 10 --queries 6
#>

[CmdletBinding(PositionalBinding = $false)]
param(
    # Pipeline text (only used when something is piped)
    [Parameter(ValueFromPipeline = $true)]
    [AllowEmptyString()]
    [string] $StdinText,

    # Everything else goes straight through to prox_mesh.py
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $PassthruArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Resolve-Path -Path (Join-Path $scriptDir ".")
$proxMeshPath = Join-Path $repoRoot "nextgen-mesh\ProxOffensive-LocalMesh\agents\prox_mesh.py"

Push-Location $repoRoot
try {
    if ($PSBoundParameters.ContainsKey("StdinText")) {
        # Forward piped state to python stdin
        $StdinText | & python $proxMeshPath @PassthruArgs
    }
    else {
        & python $proxMeshPath @PassthruArgs
    }

    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
