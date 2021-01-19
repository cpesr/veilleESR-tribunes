#!/bin/bash

if [ -z "$1" ]; then
  lastid=`cat positionnements.json | grep '"id"' | tail -1 | sed -r 's/.*-([0-9]*)",/\1/g'`
else
  lastid=$1
fi

if [ -z "$lastid" ]; then
  minid="0"
else
  minid=$(( lastid + 1))
fi

python3 depotools.py results-survey435945.csv --import-limesurvey

python3 depotools.py results-survey435945.csv --zotpress --zotero `cat zotero.key` 2348553 75KBP7II --minid $minid
python3 depotools.py results-survey435945.csv --storefiles --minid $minid
python3 depotools.py results-survey435945.csv --json-csl > positionnements.json
python3 depotools.py results-survey435945.csv --chart 'LPPR/LPR Loi de programmation de la recherche (2020)'
python3 depotools.py results-survey435945.csv --chart 'Confinement Covid19'
python3 depotools.py results-survey435945.csv --twitter --minid $minid

git add results-survey435945.csv positionnements.json *.png
git commit -m"Mise à jour des références"
git push
