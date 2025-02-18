'''
  Copyright 2021 Linked Ideal LLC.[https://linked-ideal.com/]
 
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
 
      http://www.apache.org/licenses/LICENSE-2.0
 
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 '''

from fastapi import FastAPI, File, UploadFile, Header
from ToposoidCommon.model import KnowledgeForImage, StatusInfo, TransversalState, Document, DocumentRegistration
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
from RdbUtils import addDocumentAnalysisResultHistory, UPLOAD_COMPLETED, ANALYSIS_COMPLETED


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
        propositions = Pdf2Knowledge.pdf2Knowledge(document.documentId, filename, transversalState, 0.03, 0.03, isTest=False)        
        addDocumentAnalysisResultHistory(ANALYSIS_COMPLETED, document.documentId, document.filename, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""), totalSeparatedNumber=len(propositions.propositions))
        LOG.info(f"Pdf Analysis completed.", transversalState)
        return JSONResponse(content=jsonable_encoder(propositions))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)          



