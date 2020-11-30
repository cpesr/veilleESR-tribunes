#!/bin/python3
import sys
import csv
import json
import argparse
import re
import os
from pyzotero import zotero
import pandas as pd
import matplotlib.pyplot as plt
from slugify import slugify
from sanitize_filename import sanitize

#>>> zot.item_template('letter')
#{'itemType': 'letter', 'title': '', 'creators': [{'creatorType': 'author', 'firstName': '', 'lastName': ''}], 'abstractNote': '', 'letterType': '', 'date': '', 'language': '', 'shortTitle': '', 'url': '', 'accessDate': '', 'archive': '', 'archiveLocation': '', 'libraryCatalog': '', 'callNumber': '', 'rights': '', 'extra': '', 'tags': [], 'collections': [], 'relations': {}}
#>>> zot.item_template('newspaperArticle')
#{'itemType': 'newspaperArticle', 'title': '', 'creators': [{'creatorType': 'author', 'firstName': '', 'lastName': ''}], 'abstractNote': '', 'publicationTitle': '', 'place': '', 'edition': '', 'date': '', 'section': '', 'pages': '', 'language': '', 'shortTitle': '', 'ISSN': '', 'url': '', 'accessDate': '', 'archive': '', 'archiveLocation': '', 'libraryCatalog': '', 'callNumber': '', 'rights': '', 'extra': '', 'tags': [], 'collections': [], 'relations': {}}

storage_host = 'www.cpesr.fr'
storage_url = 'uploads/motions'
storage_limesurvey = 'limesurvey/upload/surveys/435945/files'

parser = argparse.ArgumentParser(description='Convertit les données issues du formulaire de référencement de tribunes et motions')
parser.add_argument('csvfile',
                   help='Le fichier csv de réponses au formulaire limesurvey')
parser.add_argument('--zotpress', dest='zotpress', action='store_const',
                   const=True, default=False,
                   help='Formate la sortie pour être compatible avec zotpress')
parser.add_argument('--zotero', dest='zotero', nargs=3,
                   help='Synchronise les données avec zotero',
                   metavar=('api_key','library_id','collection_id'))
parser.add_argument('--storefiles', dest='storefiles', action='store_const',
                   const=True, default=False,
                   help='Stocke les textes sur le serveur web (nécessite ssh configuré)')
parser.add_argument('--json-csl', dest='json', action='store_const',
                   const=True, default=False,
                   help='Convertit les données au format json-csl')
parser.add_argument('--chart', dest='chart', nargs=1,
                   help='Produit un graphique avec les statistiques concernant un objet',
                   metavar=('objet'))
parser.add_argument('--mindate',
                   default='0000',
                   help='Date de soumision du formulaire à partir de laquelle convertir les données (format yyyy-mm-dd)')
parser.add_argument('--minid',
                   default=0, type=int,
                   help='Identifiant de la réponse à partir duquel convertir les données')

def ref2filename(ref):
    return(sanitize(
        ref['date']+'_'+slugify(ref['titre'])+'_'+slugify(ref['auteurs'])+'.'+ref['upload'][0]['ext']
    ))

def ref2url(ref):
    return(
        'https://'+storage_host+'/'+storage_url+'/'+ref2filename(ref)
    )

def format_zotpress(s):
    return(
        re.sub(' +', ' ',
        re.sub(r'\s([?.!:"](?:\s|$))', r'\1',
        s.replace('« ','').replace(' »','')))
    )

def read_csv(csvfile, zotpress=False, mindate='0', minid=0):
    refs = []
    with open(csvfile, newline='', encoding='utf-8') as csvfile:
        rows = csv.DictReader(csvfile)
        #print(rows.fieldnames)

        rows.fieldnames[0] = 'ID'

        for row in rows:
            if row['submitdate'] < mindate: continue
            if int(row['ID']) < minid: continue

            row['titre'] = row['titre'].strip('" «»')
            if row['objet'] == 'Autre': row['objet'] = row['objet[other]']
            if row['type'] == 'Autre': row['type'] = row['type[other]']
            if row['type'] != 'Tribune' and row['publication'] !=  '':
                row['auteurs'] = row['auteurs'] + ' (' + row['publication'] + ' )'

            row['date'] = row['date'][0:10]

            if row['typeurl'] == 'Téléchargement de fichier':
                row['upload'] = json.loads(row['upload'])
                row['url'] = ref2url(row)

            if zotpress:
                for e in row:
                    if isinstance(row[e], str) : row[e] = format_zotpress(row[e])

            refs.append(row)

    return(refs)

def print_jsoncsl(refs):
    csls = []
    for ref in refs:
        csl = {
            'id'              : sanitize(ref['objet'] + '-' + ref['ID']),
            'type'            : 'article-newspaper' if ref['type'] == 'Tribune' else 'personal_communication',
            'letterType'      : ref['type'],
            'abstract'        : ref['catchphrase'],
            'container-title' : ref['publication'],
            'title'           : ref['titre'],
            'URL'             : ref['url'],
            'author'          : [{'literal':ref['auteurs']}],
            'recipient'       : [{'literal':ref['destinataire']}],
            'issued'          : {'raw':ref['date']},
            'note'            : ref['position']
            }
        csls.append(csl)

    print(json.dumps(csls, indent=4, ensure_ascii=False))


def ref2zot(ref, collections):
    item = {
        #'id'              : (ref['objet'] + '-' + ref['ID']).replace(' ','_'),
        'itemType'        : 'newspaperArticle' if ref['type'] == 'Tribune' else 'letter',
        'abstractNote'    : ref['catchphrase'],
        'title'           : ref['titre'],
        'url'             : ref['url'],
        'creators'        : [{'creatorType':'author', 'name':ref['auteurs']}],
        'date'            : ref['date'],
        'extra'           : ref['position'],
        'collections'     : collections
    }
    if item['itemType'] == "letter":
        item['letterType'] = ref['type']
    else:
        item['publicationTitle'] = ref['publication']
    if ref['destinataire'] != "":
        item['creators'].append({'creatorType':'recipient', 'name':ref['destinataire']})

    return(item)


def update_zotero(refs, libid, colid, apikey):
    zot = zotero.Zotero(libid, 'group', apikey)
    subcols = {}

    zotcols = zot.collections_sub(colid)
    for c in zotcols:
        subcols[ c['data']['name'] ] = c['data']['key']
    #print(subcols)

    def zotero_get_collection_id(colname):
        if colname not in subcols:
            newcols = zot.create_collections([{'name':colname, 'parentCollection':colid}])
            newcol = newcols['successful']['0']
            subcols[ newcol['data']['name']] = newcol['data']['key']

        return(subcols[colname])

    items = []
    for ref in refs:
        subcolid = zotero_get_collection_id(ref['objet'])
        item = ref2zot(ref, [colid,subcolid])

        #items.append(item)

        print("Adding item "+ref['ID'], end='... ')
        addeditems = zot.create_items([item])
        print("DONE") if addeditems['failed'] == {} else print("FAILED")



def make_chart(refs, objet):
    df = pd.DataFrame(refs)
    cat = pd.CategoricalDtype(categories=['Très favorable','Plutôt favorable','Neutre','Plutôt défavorable','Très défavorable'],
                                  ordered = True)
    df.position = df.position.astype(cat)
    counts = df.loc[df['objet'] == objet].position.value_counts(sort=False)
    total = sum(counts)

    cm = plt.cm.get_cmap("RdYlBu").reversed()
    def pctfunc(pct):
        if pct != 0: return '{:.0f}'.format( pct * total / 100 )
        else: return ''

    plot = counts.plot(kind="pie",colormap=cm, figsize=(5,2.8125),
                       labels=counts,
                       #labels=None, autopct=lambda pct: pctfunc(pct),
                       #textprops=dict(color="w", weight='bold',fontsize=14)
                       )

    #box = plot.get_position()
    #plot.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    plt.suptitle(objet,y=0.93)
    plt.legend(loc='center left', bbox_to_anchor=(1.1,0.5), labels=cat.categories.values)
    plt.subplots_adjust(left=0.0, right=0.60, top=0.9, bottom=0.0)
    plt.axis('off')
    #plt.show()
    plt.savefig(sanitize(objet)+'.png', dpi=300)
    print(counts)

def store_files(refs):
    for ref in refs:
        if ref['typeurl'] == 'Téléchargement de fichier':
            src = storage_limesurvey+'/'+ref['upload'][0]['filename']
            dst = 'www/'+storage_url+'/'+ref2filename(ref)
            print('Upload '+dst)
            os.system('ssh'+' '+storage_host+' cp '+src+' '+dst)


if __name__ == "__main__":
    args = parser.parse_args()

    refs = read_csv(args.csvfile, args.zotpress, args.mindate, args.minid)

    if args.json : print_jsoncsl(refs)
    if args.zotero is not None: update_zotero(refs, args.zotero[1], args.zotero[2], args.zotero[0])
    if args.chart is not None: make_chart(refs, args.chart[0])
    if args.storefiles: store_files(refs)
