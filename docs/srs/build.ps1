# Builds docs/srs/SRS.pdf from the Markdown files in docs/srs/markdown/,
# in filename order according to the updated SRS template,
# compiling Graphviz diagrams in docs/srs/diagrams/ to 300 DPI PNGs first.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$BuildDate = Get-Date -Format "yyyy-MM-dd"

# Ensure output image directory exists
New-Item -ItemType Directory -Force -Path "markdown/images" | Out-Null

# Compile Graphviz diagrams from diagrams/ to markdown/images/ at 300 DPI
if (Test-Path "diagrams") {
    Get-ChildItem "diagrams/*.dot" -ErrorAction SilentlyContinue | ForEach-Object {
        $outPng = "markdown/images/" + $_.BaseName + ".png"
        Write-Host "Rendering $($_.Name) -> $outPng (300 DPI)"
        dot -Tpng -Gdpi=300 $_.FullName -o $outPng
    }
}

pandoc `
  markdown/metadata.yaml `
  markdown/01-revision-history.md `
  markdown/02-introduction.md `
  markdown/03-overall-description.md `
  markdown/04-external-interface-requirements.md `
  markdown/05-system-features.md `
  markdown/06-nonfunctional-requirements.md `
  markdown/07-quality-attributes-and-acceptance.md `
  markdown/08-system-models-and-diagrams.md `
  markdown/09-requirements-traceability-matrix.md `
  -o SRS.pdf `
  --pdf-engine=xelatex `
  --resource-path=markdown `
  -V "date=Generated $BuildDate"

Write-Host "Built docs/srs/SRS.pdf"
