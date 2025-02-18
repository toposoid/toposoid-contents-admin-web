import os
import requests
from fastapi.encoders import jsonable_encoder
from ToposoidCommon.model import DocumentAnalysisResultHistoryRecord
from typing import List
from pydantic import parse_obj_as

UPLOAD_COMPLETED = 3
VALIDATION_COMPLETED = 4
ANALYSIS_COMPLETED = 5

def addDocumentAnalysisResultHistory(stateId, documentId, originalFilename, transversalStateJson, totalSeparatedNumber=-1):
    documentAnalysisResultHistoryRecord = DocumentAnalysisResultHistoryRecord(
        stateId = stateId, documentId=documentId, originalFilename=originalFilename, totalSeparatedNumber = totalSeparatedNumber
    )
    requestJson = str(jsonable_encoder(documentAnalysisResultHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/addDocumentAnalysisResultHistory'
    response = requests.post(url , data=requestJson, headers=requestHeaders) 

def searchDocumentAnalysisResultHistoryByDocumentIdAndStateId(documentId, stateId, transversalStateJson):
    documentAnalysisResultHistoryRecord = DocumentAnalysisResultHistoryRecord(
        stateId = stateId, documentId=documentId, originalFilename="", totalSeparatedNumber = -1
    )
    requestJson = str(jsonable_encoder(documentAnalysisResultHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/searchDocumentAnalysisResultHistoryByDocumentIdAndStateId'
    response = requests.post(url , data=requestJson, headers=requestHeaders)     
    return parse_obj_as(List[DocumentAnalysisResultHistoryRecord], response.json())
