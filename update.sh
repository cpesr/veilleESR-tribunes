#!/bin/bash

lastid=`cat positionnements.json | grep '"id"' | tail -1 | sed -r 's/.*-([0-9]*)",/\1/g'`
minid=$(( lastid + 1))

python3 depotools.py results-survey435945.csv --zotpress --zotero `cat zotero.key` 2348553 75KBP7II --minid $minid
python3 depotools.py results-survey435945.csv --json-csl > positionnements.json
python3 depotools.py results-survey435945.csv --chart 'LPPR/LPR Loi de programmation de la recherche (2020)'
git add results-survey435945.csv positionnements.json *.png
git commit -m"Mise à jour des références"
git push
