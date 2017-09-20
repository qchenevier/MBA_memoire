BEGIN=$(date +%s)

echo Starting watching...
echo Press Q to exit.

while true; do
  make -s

  # In the following line -t for timeout, -N for just 1 character
  read -t 1 -N 1 input
  if [[ $input = "q" ]] || [[ $input = "Q" ]]; then
  # The following line is for the prompt to appear on a new line.
    echo
    break
  fi
done
