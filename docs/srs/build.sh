#!/usr/bin/env bash
# Builds docs/srs/SRS.pdf from the Markdown files in docs/srs/markdown/,
# in filename order according to the updated SRS template,
# compiling Graphviz diagrams in docs/srs/diagrams/ to 300 DPI PNGs first.
set -euo pipefail
cd "$(dirname "$0")"

BUILD_DATE=$(date -u +"%Y-%m-%d")

# Compile Graphviz diagrams from diagrams/ to markdown/images/ at 300 DPI
mkdir -p markdown/images
if [ -d "diagrams" ]; then
  for dotfile in diagrams/*.dot; do
    if [ -f "$dotfile" ]; then
      filename=$(basename "$dotfile" .dot)
      echo "Rendering $dotfile -> markdown/images/$filename.png (300 DPI)"
      dot -Tpng -Gdpi=300 "$dotfile" -o "markdown/images/$filename.png"
    fi
  done
fi

pandoc \
  markdown/metadata.yaml \
  markdown/01-revision-history.md \
  markdown/02-introduction.md \
  markdown/03-overall-description.md \
  markdown/04-external-interface-requirements.md \
  markdown/05-system-features.md \
  markdown/06-nonfunctional-requirements.md \
  markdown/07-quality-attributes-and-acceptance.md \
  markdown/08-system-models-and-diagrams.md \
  markdown/09-requirements-traceability-matrix.md \
  -o SRS.pdf \
  --pdf-engine=xelatex \
  --resource-path=markdown \
  -V date="Generated ${BUILD_DATE}"

echo "Built docs/srs/SRS.pdf"
