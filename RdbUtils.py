import os
import requests
from fastapi.encoders import jsonable_encoder
from ToposoidCommon.model import DocumentAnalysisResultHistoryRecord


def addDocumentAnalysisResultHistory(stateId, documentId, originalFilename, transversalStateJson):
    documentAnalysisResultHistoryRecord = DocumentAnalysisResultHistoryRecord(
        stateId = stateId, documentId=documentId, originalFilename=originalFilename, totalSeparatedNumber = -1
    )
    requestJson = str(jsonable_encoder(documentAnalysisResultHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/addDocumentAnalysisResultHistory'
    response = requests.post(url , data=requestJson, headers=requestHeaders) 

def searchDocumentAnalysisResultHistoryByDocumentId(documentId, transversalStateJson):
    documentAnalysisResultHistoryRecord = DocumentAnalysisResultHistoryRecord(
        stateId = 0, documentId=documentId, originalFilename="", totalSeparatedNumber = -1
    )
    requestJson = str(jsonable_encoder(documentAnalysisResultHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/searchDocumentAnalysisResultHistoryByDocumentId'
    response = requests.post(url , data=requestJson, headers=requestHeaders) 
    return DocumentAnalysisResultHistoryRecord.parse_obj(response.json())
