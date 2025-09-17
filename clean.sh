#!/usr/bin/env bash


venv="vcwk"
vserver=flask_${venv:1}.py
vindex=index_${venv:1}.html

# remove the files that can be installed
echo "Cleaning up the virtual environment"
declare -a rm_folders=("__pycache__" "*/__pycache__" "${venv}")
declare -a rm_files=(".env" "requirements.txt" "flask-server.sh")

echo -n "Removing folders recursively: "
for f in "${rm_folders[@]}"
do
  echo -n "$f/ "
  rm -r $f 2>/dev/null
done

echo
echo -n "Removing files: "
for f in "${rm_files[@]}"
do
  echo -n "$f "
  rm $f 2>/dev/null
done
