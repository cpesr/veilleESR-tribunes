#!/bin/python3
import sys
import csv

if len(sys.argv) < 2:
    print("Usage: python3 csv2jsoncls.py csvfile")
    sys.exit(1)

with open(sys.argv[1], newline='') as csvfile:
    rows = csv.DictReader(csvfile)
    print(rows.fieldnames)
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
            "author"          : {"literal":row["auteurs"]},
            "recipient"       : {"literal":row["destinataire"]},
            "issued"          : {"raw":row["date"]},
            "note"            : row["position"]
            }
        refs.append(ref)

print(refs)
