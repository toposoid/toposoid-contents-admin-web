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

from fastapi import FastAPI, File, UploadFile, Form
from model import KnowledgeForImage, StatusInfo, RegistContentResult
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

import os
from logging import config
config.fileConfig('logging.conf')
import logging
LOG = logging.getLogger(__name__)
import traceback
from ImageAdmin import ImageAdmin
from middleware import ErrorHandlingMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import uuid

app = FastAPI(
    title="toposoid-contents-admin-web",
    version="0.5-SNAPSHOT"
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
def registImage(knowledgeForImage:KnowledgeForImage):
    try:                
        updatedKnowledgeForImage = imageAdmin.registImage(knowledgeForImage, False)
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=updatedKnowledgeForImage, statusInfo=StatusInfo(status="OK", message="")) ))
    except Exception as e:
        LOG.error(traceback.format_exc())
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/uploadTemporaryImage",
          summary='upload image files as temporary')
def uploadTemporaryImage(knowledgeForImage:KnowledgeForImage):
    try:                
        updatedKnowledgeForImage = imageAdmin.registImage(knowledgeForImage, True)
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=updatedKnowledgeForImage, statusInfo=StatusInfo(status="OK", message="")) ))
    except Exception as e:
        LOG.error(traceback.format_exc())
        return JSONResponse(content=jsonable_encoder(RegistContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/uploadFile")
async def createUploadFile(uploadfile: UploadFile = File(...)):   
    id = str(uuid.uuid1())
    path = f'contents/temporaryUse/{id}-{uploadfile.filename}'
    url = os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + id + "-" + uploadfile.filename
    with open(path, 'w+b') as buffer:
        shutil.copyfileobj(uploadfile.file, buffer)
    return {
        'url': url,        
    }
    