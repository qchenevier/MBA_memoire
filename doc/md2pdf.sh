
FILE=$1
FONT=${2:-"FreeSans"}
BIB=${3:-"/home/quentin/documents/bibliography/library"}
CSL=${4:-"apa"}

command="pandoc -N --template=mytemplate.tex --variable mainfont=\""$FONT"\" --variable sansfont=\""$FONT"\" --variable monofont=\"DejaVu Sans Mono\" --variable fontsize=12pt --variable version=1.17.2 "$FILE"*.md --latex-engine=xelatex --toc --filter=pandoc-include --filter=pandoc-citeproc --biblio="$BIB".bib --csl="$CSL".csl --tab-stop=2 -o "$FILE".pdf"

eval $command && evince "$FILE".pdf
