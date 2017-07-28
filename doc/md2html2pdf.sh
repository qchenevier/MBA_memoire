
FILE=$1
FONT=${2:-"FreeSans"}
BIB=${3:-"/home/quentin/documents/bibliography/library"}
CSL=${4:-"apa"}

command="pandoc -N -c https://gist.githubusercontent.com/ryangray/1882525/raw/2a6e53f645b960f0bed16d686ba3df36505f839f/buttondown.css "$FILE"*.md -t html5 --toc --filter=pandoc-include --filter=pandoc-citeproc --biblio="$BIB".bib --csl="$CSL".csl --tab-stop=2 -o "$FILE".pdf"

eval $command && evince "$FILE".pdf
