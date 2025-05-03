import os
from fastapi.encoders import jsonable_encoder
from ToposoidCommon.model import DocumentAnalysisResultHistoryRecord, KnowledgeRegisterHistoryRecord, KnowledgeRegisterHistoryCount
from typing import List
from pydantic import parse_obj_as
#import requests
#Changed to httpx because there was a problem with requests.
#addKnowledgeRegisterHistory gives 501 error.
import httpx

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
    response = httpx.post(url , data=requestJson, headers=requestHeaders) 
    print(response)

def addKnowledgeRegisterHistory(stateId, documentId, sequentialNumber, propositionId, sentences, json, transversalStateJson):
    knowledgeRegisterHistoryRecord = KnowledgeRegisterHistoryRecord(
        stateId = stateId, documentId=documentId, sequentialNumber=sequentialNumber, propositionId=propositionId, sentences=sentences, json=json)
    requestJson = str(jsonable_encoder(knowledgeRegisterHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/addKnowledgeRegisterHistory'
    response = httpx.post(url , data=requestJson, headers=requestHeaders) 
    print(response)

def searchDocumentAnalysisResultHistoryByDocumentIdAndStateId(documentId, stateId, transversalStateJson):
    documentAnalysisResultHistoryRecord = DocumentAnalysisResultHistoryRecord(
        stateId = stateId, documentId=documentId, originalFilename="", totalSeparatedNumber = -1
    )
    requestJson = str(jsonable_encoder(documentAnalysisResultHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/searchDocumentAnalysisResultHistoryByDocumentIdAndStateId'
    response = httpx.post(url , data=requestJson, headers=requestHeaders)     
    return parse_obj_as(List[DocumentAnalysisResultHistoryRecord], response.json())

def getKnowledgeRegisterHistoryTotalCountByDocumentId(knowledgeRegisterHistoryCount, transversalStateJson):
    requestJson = str(jsonable_encoder(knowledgeRegisterHistoryCount)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/getKnowledgeRegisterHistoryTotalCountByDocumentId'
    response = httpx.post(url , data=requestJson, headers=requestHeaders)     
    return parse_obj_as(KnowledgeRegisterHistoryCount, response.json())

def getKnowledgeRegisterHistoryCountByDocumentId(knowledgeRegisterHistoryCount, transversalStateJson):
    requestJson = str(jsonable_encoder(knowledgeRegisterHistoryCount)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/getKnowledgeRegisterHistoryCountByDocumentId'
    response = httpx.post(url , data=requestJson, headers=requestHeaders)     
    return parse_obj_as(KnowledgeRegisterHistoryCount, response.json())

def searchLatestDocumentAnalysisStateByDocumentId(documentAnalysisResultHistoryRecord, transversalStateJson):
    requestJson = str(jsonable_encoder(documentAnalysisResultHistoryRecord)).replace("'", "\"")
    requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': transversalStateJson.replace("'", "\"")}
    url =  f'http://{os.environ["TOPOSOID_RDB_WEB_HOST"]}:{os.environ["TOPOSOID_RDB_WEB_PORT"]}/searchLatestDocumentAnalysisStateByDocumentId'
    response = httpx.post(url , data=requestJson, headers=requestHeaders)     
    return parse_obj_as(List[DocumentAnalysisResultHistoryRecord], response.json())
