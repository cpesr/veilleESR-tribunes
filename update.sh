#!/bin/bash

lastid=`cat positionnements.json | grep '"id"' | tail -1 | sed -r 's/.*-([0-9]*)",/\1/g'`
minid=$(( lastid + 1))

python3 csv2jsoncsl.py results-survey435945.csv --zotpress > positionnements.json
python3 csv2jsoncsl.py results-survey435945.csv --zotpress --minid $minid > positionnements-derniers.json
git add results-survey435945.csv positionnements.json positionnements-derniers.json
git commit -m"Mise à jour des références"
git push
