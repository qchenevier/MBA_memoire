
FILE=$1
FONT=${2:-"FreeSans"}
BIB=${3:-"$HOME/documents/bibliography/library"}
CSL=${4:-"apa"}

generate_report="pandoc -N --template=mytemplate.tex --variable mainfont=\""$FONT"\" --variable sansfont=\""$FONT"\" --variable monofont=\""$FONT"\" --variable fontsize=12pt --variable version=1.17.2 "$FILE"*.md --latex-engine=xelatex --toc --filter=pandoc-include --filter=pandoc-citeproc --biblio="$BIB".bib --csl="$CSL".csl --tab-stop=2 --top-level-division=chapter -o "$FILE".pdf"

echo  $(date -Iseconds): generating pdf: $FILE

if eval $generate_report; then
    if [ "$(uname -s)" != "MSYS_NT-10.0" ]; then
        qpdfview_pid=`pgrep -f "qpdfview "$FILE".pdf"`
        if [ -z "$qpdfview_pid" ]; then
            echo  $(date -Iseconds): opening in new qpdfview
            qpdfview "$FILE".pdf &
        else
            echo  $(date -Iseconds): opening in existing qpdfview with pid: $qpdfview_pid
            xdotool windowactivate `xdotool search --pid "$qpdfview_pid" | tail -1`
        fi
    fi
fi
