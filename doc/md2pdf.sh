
FILE=$1
FONT=${2:-"DejaVu Sans"}

command="pandoc -N --template=mytemplate.tex --variable mainfont=\""$FONT"\" --variable sansfont=\""$FONT"\" --variable monofont=\"DejaVu Sans Mono\" --variable fontsize=12pt --variable version=1.17.2 "$FILE".md --latex-engine=xelatex --toc -o "$FILE".pdf"
eval $command

evince "$FILE".pdf
