#!/bin/python3
import sys
import csv
import json
import argparse
import re


parser = argparse.ArgumentParser(description='Convertit les données issues du formulaire de référencement de tribunes et motions')
parser.add_argument('csvfile',
                   help='Le fichier csv de réponses au formulaire limesurvey')
parser.add_argument('--zotpress', dest='zotpress', action='store_const',
                   const=True, default=False,
                   help='Formate la sortie pour être compatible avec zotpress')

args = parser.parse_args()

def format_zotpress(s):
    return(
        re.sub(' +', ' ',
        re.sub(r'\s([?.!"](?:\s|$))', r'\1',
        s.replace("« ","").replace(" »","")))
        )


with open(args.csvfile, newline='', encoding="utf-8") as csvfile:
    rows = csv.DictReader(csvfile)
    #print(rows.fieldnames)
    rows.fieldnames[0] = "ID"

    refs = []
    for row in rows:
        if row["objet"] == "Autre": row["objet"] = row['objet[other]']
        if row["type"] == "Autre": row["type"] = row['type[other]']

        ref = {
            "id"              : (row["objet"] + "-" + row["ID"]).replace(' ','_'),
            "type"            : "article-magazine" if row["type"] == "Tribune" else "personal_communication",
            "abstract"        : row["catchphrase"],
            "container-title" : row["publication"],
            "title"           : row["titre"],
            "URL"             : row["url"],
            "author"          : [{"literal":row["auteurs"]}],
            "recipient"       : [{"literal":row["destinataire"]}],
            "issued"          : {"raw":row["date"]},
            "note"            : row["position"]
            }

        if args.zotpress:
            for e in ref:
                if isinstance(ref[e], str) : ref[e] = format_zotpress(ref[e]) 

        refs.append(ref)

print(json.dumps(refs, indent=4, ensure_ascii=False))
