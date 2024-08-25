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
from model import KnowledgeForImage, StatusInfo, RegistContentResult, TransversalState
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from typing import Optional

import os
import yaml
from logging import config
#config.fileConfig('logging.conf')
config.dictConfig(yaml.load(open("logging.yml", encoding="utf-8").read(), Loader=yaml.SafeLoader))
import logging
LOG = logging.getLogger(__name__)
import traceback
from ImageAdmin import ImageAdmin
from middleware import ErrorHandlingMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import uuid
from utils import formatMessageForLogger

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
        LOG.info(formatMessageForLogger("Image upload completed.[url:" + knowledgeForImage.imageReference.reference.url +"]", transversalState.userId))
        return response
    except Exception as e:
        LOG.error(formatMessageForLogger(traceback.format_exc(), transversalState.userId))
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/uploadTemporaryImage",
          summary='upload image files as temporary')
def uploadTemporaryImage(knowledgeForImage:KnowledgeForImage, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:            
        updatedKnowledgeForImage = imageAdmin.registImage(knowledgeForImage, True)
        response = JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=updatedKnowledgeForImage, statusInfo=StatusInfo(status="OK", message=""))))
        LOG.info(formatMessageForLogger("Image upload completed.[url:" + updatedKnowledgeForImage.imageReference.reference.url +"]", transversalState.userId))
        return response
    except Exception as e:
        LOG.error(formatMessageForLogger(traceback.format_exc(), transversalState.userId))
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/uploadFile")
async def createUploadFile(uploadfile: UploadFile = File(...), X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):   
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    id = str(uuid.uuid1())
    path = f'contents/temporaryUse/{id}-{uploadfile.filename}'
    url = os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + id + "-" + uploadfile.filename
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(uploadfile.file, buffer)
    LOG.info(formatMessageForLogger("Image upload completed.[url:" + url +"]", transversalState.userId))
    return {
        'url': url,        
    }
    