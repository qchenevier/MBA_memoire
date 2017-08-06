
FILE=$1
FONT=${2:-"FreeSans"}
BIB=${3:-"/home/quentin/documents/bibliography/library"}
CSL=${4:-"apa"}

generate_report="pandoc -N --template=mytemplate.tex --variable mainfont=\""$FONT"\" --variable sansfont=\""$FONT"\" --variable monofont=\"DejaVu Sans Mono\" --variable fontsize=12pt --variable version=1.17.2 "$FILE"*.md --latex-engine=xelatex --toc --filter=pandoc-include --filter=pandoc-citeproc --biblio="$BIB".bib --csl="$CSL".csl --tab-stop=2 --top-level-division=chapter -o "$FILE".pdf"

if eval $generate_report; then
  if ! pgrep -f "qpdfview "$FILE".pdf"; then
    echo process not found
    qpdfview "$FILE".pdf &
  else
    echo process found
    qpdfview_pid=`pgrep -f "qpdfview "$FILE".pdf"`
    xdotool windowactivate `xdotool search --pid "$qpdfview_pid" | tail -1`
  fi
fi
