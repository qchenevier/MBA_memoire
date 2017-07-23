
FILE=$1
FONT=${2:-"FreeSans"}
BIB=${3:-"mendeley_export"}
CSL=${4:-"apa"}

command="pandoc -N --template=mytemplate.tex --variable mainfont=\""$FONT"\" --variable sansfont=\""$FONT"\" --variable monofont=\"DejaVu Sans Mono\" --variable fontsize=12pt --variable version=1.17.2 "$FILE"*.md --latex-engine=xelatex --toc --filter=pandoc-citeproc --filter=pandoc-include --biblio="$BIB".bib --csl="$CSL".csl -o "$FILE".pdf"

eval $command && evince "$FILE".pdf
