import requests
import json
import base64
import os


def import_limesurvey(csvfilename="results.csv"):
    username = os.getenv("LS_USERNAME")
    password = os.getenv("LS_PASSWORD")
    url = "https://enquete.cpesr.fr/index.php/admin/remotecontrol"

    payload = {
        "method": "get_session_key",
        "params": {'username':username,'password':password,'plugin':"Authdb"},
        "jsonrpc": "2.0",
        "id": 1 }
    response = requests.post(url, json=payload).json()
    sessionKey = response['result']

    payload = {
        "method": "export_responses",
        "params": { 'sSessionKey':sessionKey, 'iSurveyID':435945,
                    'sDocumentType':"csv", 'sLanguageCode':"", 'sCompletionStatus':"complete",
                    'sHeadingType':"code", 'sResponseType':"long"},
        "jsonrpc": "2.0",
        "id": 1 }
    response = requests.post(url, json=payload).json()
    with open(csvfilename,'w') as f:
        f.write(base64.b64decode(response['result']).decode('utf-8'))

    payload = {
        "method": "release_session_key",
        "params": {'sSessionKey':sessionKey},
        "jsonrpc": "2.0",
        "id": 1 }
    response = requests.post(url, json=payload).json()


if __name__ == "__main__":
    import_limesurvey()
