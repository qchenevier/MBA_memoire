
source activate python2

mendeley_library="/home/quentin/.local/share/data/Mendeley Ltd./Mendeley Desktop/quentin.chenevier@gmail.com@www.mendeley.com.sqlite"
output_folder="/home/quentin/documents/MBA/3_devoirs/memoire/doc/sources/menotexport"


rm -frv "$output_folder"/*

menotexport.py -ms "$mendeley_library" "$output_folder"

for f in "$output_folder"/*/*
do
  echo "Processing $f file..."
  # take action on each file. $f store current file name
  cat "$f" | sed 's/\t//g' | sed 's/^-\ .*//g' | sed 's/>\ //g' | sed '/^$/d' > "$f"
done
