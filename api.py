'''
  Copyright (C) 2025  Linked Ideal LLC.[https://linked-ideal.com/]
 
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation, version 3.
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


from fastapi import FastAPI, File, UploadFile, Header
from ToposoidCommon.model import KnowledgeForImage, StatusInfo, TransversalState, Document, DocumentRegistration, KnowledgeRegisterHistoryCount, DocumentAnalysisResultHistoryRecord
from model import RegistContentResult
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from typing import Optional

import os
import traceback
from ImageAdmin import ImageAdmin
from middleware import ErrorHandlingMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import uuid
import ToposoidCommon as tc
from ToposoidPdfAnalyzer import Pdf2Knowledge
from ElasiticMQUtils import sendMessage
from RdbUtils import addDocumentAnalysisResultHistory, getKnowledgeRegisterHistoryTotalCountByDocumentId, getKnowledgeRegisterHistoryCountByDocumentId, searchLatestDocumentAnalysisStateByDocumentId, UPLOAD_COMPLETED, ANALYSIS_COMPLETED


LOG = tc.LogUtils(__name__)
TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE = os.environ["TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE"]

app = FastAPI(
    title="toposoid-contents-admin-web",
    version="0.6-SNAPSHOT"
)
app.add_middleware(ErrorHandlingMiddleware)
imageAdmin = ImageAdmin()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount("/contents", StaticFiles(directory="contents"), name="contents")

@app.post("/registImage",
          summary='register image files')
def registImage(knowledgeForImage:KnowledgeForImage, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:           
        updatedKnowledgeForImage = imageAdmin.registImage(knowledgeForImage, False)
        response = JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=updatedKnowledgeForImage, statusInfo=StatusInfo(status="OK", message="")) ))
        LOG.info(f"Image upload completed.[url:{knowledgeForImage.imageReference.reference.url}]", transversalState)
        return response
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/uploadTemporaryImage",
          summary='upload image files as temporary')
def uploadTemporaryImage(knowledgeForImage:KnowledgeForImage, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:            
        updatedKnowledgeForImage = imageAdmin.registImage(knowledgeForImage, True)
        response = JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=updatedKnowledgeForImage, statusInfo=StatusInfo(status="OK", message=""))))
        LOG.info(f"Image upload completed.[url:{updatedKnowledgeForImage.imageReference.reference.url}]", transversalState)
        return response
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/uploadImageFile")
async def createUploadImageFile(uploadfile: UploadFile = File(...), X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):   
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    id = str(uuid.uuid1())
    path = f'tmp/{id}-{uploadfile.filename}'
    #url = os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + id + "-" + uploadfile.filename
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(uploadfile.file, buffer)    
    #TODO:check File
    url = imageAdmin.convertJpeg(path, id)
    LOG.info(f"Image upload completed.[url:{url}", transversalState)
    return {
        'url': url,        
    }

@app.post("/uploadDocumentFile")
async def createUploadDocumentFile(uploadfile: UploadFile = File(...), X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):   
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    #TODO:tryブロックをつけて例外の時は、mysqlに書き込む。
    id = str(uuid.uuid1())
    elements = uploadfile.filename.split(".")
    ext = ""
    if len(elements) > 1:
        ext = "." + elements[-1]

    path = f'tmp/{id}-{uploadfile.filename}'    
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(uploadfile.file, buffer)    
    size = os.path.getsize(path)
    #TODO:check File
    shutil.move(path, "contents/documents/%s-%s" % (id, uploadfile.filename))    
    shutil.copy("contents/documents/%s-%s" % (id, uploadfile.filename),"contents/documents/%s%s" % (id, ext) )
    url = os.environ["TOPOSOID_CONTENTS_URL"] + "documents/" + id + ext

    #Publish to document-analysis-subscriber. Register information in mysql instead of pushing unnecessary things to MQ
    addDocumentAnalysisResultHistory(UPLOAD_COMPLETED, id, uploadfile.filename, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    document = Document(documentId=id, filename=uploadfile.filename, url=url, size=size)
    requestJson = str(jsonable_encoder(DocumentRegistration(document=document, transversalState=transversalState))).replace("'", "\"")
    sendMessage(TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE, requestJson)
    LOG.info(f"Document upload completed.[url:{url}]", transversalState)
    return JSONResponse(content=jsonable_encoder(Document(documentId=id, filename=uploadfile.filename, url=url, size=size)))

@app.post("/analyzePdfDocument")
def analyzePdfDocument(document: Document, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:   
        filename = f"contents/documents/{document.documentId}.pdf"
        pdf2Knowledge = Pdf2Knowledge()
        propositions = pdf2Knowledge.pdf2Knowledge(document.documentId, filename, transversalState, 0.03, 0.03, isTest=False)        
        addDocumentAnalysisResultHistory(ANALYSIS_COMPLETED, document.documentId, document.filename, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""), totalSeparatedNumber=len(propositions.propositions))
        LOG.info(f"Pdf Analysis completed.", transversalState)
        return JSONResponse(content=jsonable_encoder(propositions))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)          


@app.post("/getTotalPropositionCount")
def getTotalPropositionCount(knowledgeRegisterHistoryCount:KnowledgeRegisterHistoryCount, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:
        result = getKnowledgeRegisterHistoryTotalCountByDocumentId(knowledgeRegisterHistoryCount, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
        LOG.info(f"Get the total count of propositions completed.[documentId:{knowledgeRegisterHistoryCount.documentId}]", transversalState)
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)          
    
@app.post("/getAnalyzedPropositionCount")
def getAnalyzedPropositionCount(knowledgeRegisterHistoryCount:KnowledgeRegisterHistoryCount, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:
        result = getKnowledgeRegisterHistoryCountByDocumentId(knowledgeRegisterHistoryCount, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
        LOG.info(f"Get the analyzed count of propositions completed.[documentId:{knowledgeRegisterHistoryCount.documentId}]", transversalState)
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)          

@app.post("/getLatestDocumentAnalysisState")
def getLatestDocumentAnalysisState(documentAnalysisResultHistoryRecord:DocumentAnalysisResultHistoryRecord, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:
        result = searchLatestDocumentAnalysisStateByDocumentId(documentAnalysisResultHistoryRecord, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
        LOG.info(f"Get the analyzed state completed.[documentId:{documentAnalysisResultHistoryRecord.documentId}]", transversalState)
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)          

