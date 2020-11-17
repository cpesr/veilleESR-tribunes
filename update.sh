#!/bin/bash

python3 csv2jsoncsl.py results-survey435945.csv --zotpress > positionnements.json
python3 csv2jsoncsl.py results-survey435945.csv --zotpress --minid $1 > positionnements-derniers.json
git add results-survey435945.csv positionnements.json positionnements-derniers.json
git commit -m"Mise à jour des références"
git push
