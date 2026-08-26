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


from fastapi import FastAPI, File, UploadFile, Header, Depends
from ToposoidCommon.model import KnowledgeForImage, KnowledgeForTable, StatusInfo, TransversalState, Document, DocumentRegistration, KnowledgeRegisterHistoryCount, DocumentAnalysisResultHistoryRecord, RegisteredImageContentResult, RegisteredTableContentResult, RegisteredDocumentContentResult
from ToposoidCommon.constants import FeatureType
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from typing import Optional
import cv2

import os
import traceback
from middleware import ErrorHandlingMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import uuid
import ToposoidCommon as tc
from ToposoidPdfAnalyzer import Pdf2Knowledge
from ElasiticMQUtils import sendMessage
from RdbUtils import addDocumentAnalysisResultHistory, getKnowledgeRegisterHistoryTotalCountByDocumentId, getKnowledgeRegisterHistoryCountByDocumentId, searchLatestDocumentAnalysisStateByDocumentId, UPLOAD_COMPLETED, ANALYSIS_COMPLETED
import glob
from pathlib import Path
import magic
import pandas as pd
import io
import csv

LOG = tc.LogUtils(__name__)
TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE = os.environ["TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE"]

app = FastAPI(
    title="toposoid-contents-admin-web",
    version="0.6-SNAPSHOT"
)
app.add_middleware(ErrorHandlingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount("/contents", StaticFiles(directory="contents"), name="contents")


@app.post("/transferFile")
async def transferFile(uploadfile: UploadFile = File(...), X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:
        with open(f"contents/temporaryUse/{uploadfile.filename}", 'w+b') as buffer:
            shutil.copyfileobj(uploadfile.file, buffer)    
        LOG.info(f"File transfer was completed. {uploadfile.filename}", transversalState)
        return JSONResponse(content=jsonable_encoder(StatusInfo(status="OK", message="")))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)          
        return JSONResponse(content=jsonable_encoder(StatusInfo(status="ERROR", message=f"{e}")))

@app.post("/registerImage",
          summary='register image file')
def registerImage(knowledgeForImage:KnowledgeForImage, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:                   
        #ファイルはknowledgeForImage.imageReference.reference.urlに保存されている前提
        #if not knowledgeForImage.imageReference.reference.isWholeSentence:
        target, x, y, w, h = convertImageSize(knowledgeForImage)
        #target = "contents/" + knowledgeForImage.imageReference.reference.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
        knowledgeForImage.imageReference.reference.url = save(FeatureType.IMAGE, knowledgeForImage.id, target)
        knowledgeForImage.imageReference.x = x
        knowledgeForImage.imageReference.y = y
        knowledgeForImage.imageReference.width = w
        knowledgeForImage.imageReference.height = h
        response = JSONResponse(content=jsonable_encoder(RegisteredImageContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="OK", message="")) ))
        LOG.info(f"Saving image completed.[url:{knowledgeForImage.imageReference.reference.url}]", transversalState)
        return response
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegisteredImageContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/registerTable",
          summary='register table file')
def registerTable(knowledgeForTable:KnowledgeForTable, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:                   
        #ファイルはknowledgeForTable.tableReference.reference.urlに保存されている前提
        #if not knowledgeForTable.tableReference.reference.isWholeSentence:
        target = convertTable2Tsv(knowledgeForTable, transversalState)
        #target = "contents/" + knowledgeForTable.tableReference.reference.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
        knowledgeForTable.tableReference.reference.url = save(FeatureType.TABLE, knowledgeForTable.id, target)
        response = JSONResponse(content=jsonable_encoder(RegisteredTableContentResult(knowledgeForTable=knowledgeForTable, statusInfo=StatusInfo(status="OK", message="")) ))
        LOG.info(f"Saving table completed.[url:{knowledgeForTable.tableReference.reference.url}]", transversalState)
        return response
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegisteredTableContentResult(knowledgeForTable=knowledgeForTable, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))




@app.post("/convertImage",
          summary='convert image file')
def registerImage(knowledgeForImage:KnowledgeForImage, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:                   
        #ファイルはknowledgeForImage.imageReference.reference.urlに保存されている前提
        #if not knowledgeForImage.imageReference.reference.isWholeSentence:
        target, x, y, w, h = convertImageSize(knowledgeForImage)
        #target = "contents/" + knowledgeForImage.imageReference.reference.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
        knowledgeForImage.imageReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"].replace("contents/", "") + target
        knowledgeForImage.imageReference.x = x
        knowledgeForImage.imageReference.y = y
        knowledgeForImage.imageReference.width = w
        knowledgeForImage.imageReference.height = h
        response = JSONResponse(content=jsonable_encoder(RegisteredImageContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="OK", message="")) ))
        LOG.info(f"Saving image completed.[url:{knowledgeForImage.imageReference.reference.url}]", transversalState)
        return response
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegisteredImageContentResult(knowledgeForImage=knowledgeForImage, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

@app.post("/convertTable",
          summary='convert table file')
def registerTable(knowledgeForTable:KnowledgeForTable, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:                   
        #ファイルはknowledgeForTable.tableReference.reference.urlに保存されている前提
        #if not knowledgeForTable.tableReference.reference.isWholeSentence:
        target = convertTable2Tsv(knowledgeForTable, transversalState)
        #target = "contents/" + knowledgeForTable.tableReference.reference.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
        knowledgeForTable.tableReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"].replace("contents/", "") + target
        response = JSONResponse(content=jsonable_encoder(RegisteredTableContentResult(knowledgeForTable=knowledgeForTable, statusInfo=StatusInfo(status="OK", message="")) ))
        LOG.info(f"Saving table completed.[url:{knowledgeForTable.tableReference.reference.url}]", transversalState)
        return response
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegisteredTableContentResult(knowledgeForTable=knowledgeForTable, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))



@app.post("/registerDocument",
          summary='register document file')
def registerDocument(document: Document, X_TOPOSOID_TRANSVERSAL_STATE: Optional[str] = Header(None, convert_underscores=False)):
    transversalState = TransversalState.parse_raw(X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))
    try:        
        #ファイルはdocument.urlに保存されている前提
        document.documentId = str(uuid.uuid1())
        target = "contents/" + document.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
        originalFilename = getOriginalFilename(FeatureType.DOCUMENT, target)
        document.size = os.path.getsize(target)
        document.url = save(FeatureType.DOCUMENT, document.documentId, target) 
        #filepath = "contents/" + document.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")  
        #document.filename = f"{document.documentId}.{filepath.split('.')[-1]}"        
        if getOriginalFilename == "":
            #TODO:もしURLからドキュメントを取得することがあればそのURLを設定する？
            document.filename = ""
        else:
            document.filename = originalFilename        
        
        #Publish to document-analysis-subscriber. Register information in mysql instead of pushing unnecessary things to MQ
        addDocumentAnalysisResultHistory(UPLOAD_COMPLETED, document.documentId, document.filename, X_TOPOSOID_TRANSVERSAL_STATE.replace("'", "\""))                
        requestJson = str(jsonable_encoder(DocumentRegistration(document=document, transversalState=transversalState))).replace("'", "\"")
        sendMessage(TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE, requestJson)
        LOG.info(f"Saving Document completed.[url:{document.url}]", transversalState)
        return JSONResponse(content=jsonable_encoder(RegisteredDocumentContentResult(document=document, statusInfo=StatusInfo(status="OK", message=""))))
    except Exception as e:
        LOG.error(traceback.format_exc(), transversalState)
        return JSONResponse(content=jsonable_encoder(RegisteredDocumentContentResult(document=document, statusInfo=StatusInfo(status="ERROR", message=traceback.format_exc()))))

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



def save(featureType, featureId, target):
    #ファイルの存在を確認    
    if not os.path.exists(target):
        raise Exception(f"The uploaded file does not exist. {target}")

    #オリジナルファイルの特定
    oldFeatureId = Path(target).stem
    originalFilename = getOriginalFilename(featureType, target)
    newOriginalFilename = f"{featureId}!{originalFilename}"

    #公開URLを新規に確定する。featureIdは、所与の前提
    newFilename = f"{featureId}.{target.split('.')[-1]}"
    if featureType == FeatureType.IMAGE:
        shutil.move(f"contents/temporaryUse/{oldFeatureId}!{originalFilename}",f"contents/images/{newOriginalFilename}")
        shutil.move(target, f"contents/images/{newFilename}")
        return f"{os.environ['TOPOSOID_CONTENTS_URL']}images/{newFilename}"
    elif featureType == FeatureType.TABLE:
        parquetTarget = ".".join(list(target.split('.'))[:-1]) + ".parquet"
        newParquetFilename = f"{featureId}.parquet"
        tsvTarget = ".".join(list(target.split('.'))[:-1]) + ".tsv"
        shutil.move(f"contents/temporaryUse/{oldFeatureId}!{originalFilename}",f"contents/tables/{newOriginalFilename}")
        shutil.move(tsvTarget, f"contents/tables/{newFilename}")
        shutil.move(parquetTarget, f"contents/tables/{newParquetFilename}")
        return f"{os.environ['TOPOSOID_CONTENTS_URL']}tables/{newFilename}"
    elif featureType == FeatureType.DOCUMENT:
        shutil.move(f"contents/temporaryUse/{oldFeatureId}!{originalFilename}",f"contents/documents/{newOriginalFilename}")
        shutil.move(target, f"contents/documents/{newFilename}")
        return f"{os.environ['TOPOSOID_CONTENTS_URL']}documents/{newFilename}"
    else:
        raise Exception("There's something wrong with the featureId.")


def getOriginalFilename(featureType, filepath):
    #拡張子を取り除いたパス
    filePath = Path(filepath)
    #オリジナルファイルとセットで二つあるか
    filelist = glob.glob(f"{filePath.parent}/{filePath.stem}*")
    if featureType == FeatureType.TABLE:
        if not len(filelist) ==  3:
            raise Exception(f"The number of uploaded files is not three. {filelist}")
    else:
        if not len(filelist) ==  2:
            raise Exception(f"The number of uploaded files is not two. {filelist}")


    originalfile = list(filter(lambda x: "!" in  x, filelist))
    if not len(originalfile) == 1:
        raise Exception(f"The original file does not exist. {filelist}")
    return originalfile[0].partition('!')[2]


def convertImageSize(knowledgeForImage:KnowledgeForImage):
    target = "contents/" +knowledgeForImage.imageReference.reference.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
    image = cv2.imread(target)
    if knowledgeForImage.imageReference.width == 0 or knowledgeForImage.imageReference.height == 0:
        h, w, channels = image.shape
        x = 0
        y = 0
    else:
        #イメージサイズが指定されていたら保存ファイルのサイズ変更をする。
        x = knowledgeForImage.imageReference.x
        y = knowledgeForImage.imageReference.y
        w = knowledgeForImage.imageReference.width
        h = knowledgeForImage.imageReference.height
        #上書き
        cv2.imwrite(target, image[y:y+h, x:x+w])
    return target, x, y, w, h


def convertTable2Tsv(knowledgeForTable:KnowledgeForTable, transversalState):
    target = "contents/" +knowledgeForTable.tableReference.reference.url.replace(os.environ["TOPOSOID_CONTENTS_URL"], "")
    input = knowledgeForTable.tableReference
    #Excelかテキストかそれ以外かを見分ける
    mime = magic.from_file(target, mime=True)    
    if mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        if len(input.skipRowList) == 0:
            try:
                if input.sheetNameForExcel == "":
                    df = pd.read_excel(target, skiprows=input.skipHeaderRows, header=list(range(input.multiHeaderRows))) 
                else:
                    df = pd.read_excel(target, skiprows=input.skipHeaderRows, header=list(range(input.multiHeaderRows)), sheet_name=input.sheetNameForExcel) 
            except Exception as e:
                LOG.warning(f"Failed to load table data using the specified options. Adjusting options to attempt recovery. {e}", transversalState)
                df = pd.read_excel(target, skiprows=input.skipHeaderRows) 
        else: 
            try:
                if input.sheetNameForExcel == "":
                    df = pd.read_excel(target, skiprows=input.skipRowList, header=list(range(input.multiHeaderRows))) 
                else:
                    df = pd.read_excel(target, skiprows=input.skipRowList, header=list(range(input.multiHeaderRows)), sheet_name=input.sheetNameForExcel) 
            except Exception as e:
                LOG.warning(f"Failed to load table data using the specified options. Adjusting options to attempt recovery. {e}", transversalState)
                df = pd.read_excel(target, skiprows=input.skipRowList) 

        os.remove(target)
        convert_filaname = ".".join(list(target.split('.'))[:-1]) + ".tsv"
        df.to_csv(convert_filaname, index = False, sep='\t', header=False, encoding="utf-8")  
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
        df.to_parquet(".".join(list(target.split('.'))[:-1]) + ".parquet")        
        return convert_filaname
            
    elif mime.startswith('text/'):            
        max_length = 0
        is_variable = False
        foundFirstLine = False
        #基本この時点でタブ区切りのファイルに限定される。
        with open(target, 'r', encoding='utf-8', newline='') as f:
            for i, line in enumerate(f):
                if len(input.skipRowList) == 0:
                    if i < input.skipHeaderRows:
                        continue
                else:
                    if i + 1 in input.skipRowList:continue

                if foundFirstLine and not is_variable and max_length != len(line.split("\t")):
                    is_variable = True
                max_length = max(max_length, len(line.split("\t")))
                foundFirstLine = True

            """
            reader = csv.reader(f)            
            for i, row in enumerate(reader):
                if len(input.skipRowList) == 0:
                    if i < input.skipHeaderRows:
                        continue
                else:
                    if i + 1 in input.skipRowList:continue
                if foundFirstLine and not is_variable and max_length != len(row):
                    is_variable = True
                max_length = max(max_length, len(row))
                foundFirstLine = True
            """

        col_names = list(range(max_length))
        if is_variable:
            #列が可変長の場合
            if len(input.skipRowList) == 0:
                df = pd.read_csv(target, skiprows=input.skipHeaderRows, header=None, names=col_names) 
            else:
                df = pd.read_csv(target, skiprows=input.skipRowList, header=None, names=col_names) 
        else:
            #ヘッダを認識させられる時は、そうする。
            if len(input.skipRowList) == 0:
                try:
                    df = pd.read_csv(target, skiprows=input.skipHeaderRows, header=list(range(input.multiHeaderRows)), sep=None, engine='python')                   
                except Exception as e:
                    LOG.warning(f"Failed to load table data using the specified options. Adjusting options to attempt recovery. {e}", transversalState)
                    df = pd.read_csv(target, skiprows=input.skipHeaderRows, sep=None, engine='python')
            else:
                try:
                    df = pd.read_csv(target, skiprows=input.skipRowList, header=list(range(input.multiHeaderRows)), sep=None, engine='python')  
                except Exception as e:
                    LOG.warning(f"Failed to load table data using the specified options. Adjusting options to attempt recovery. {e}", transversalState)
                    df = pd.read_csv(target, skiprows=input.skipRowList, sep=None, engine='python')
                    
        os.remove(target)
        convert_filaname = ".".join(list(target.split('.'))[:-1]) + ".tsv"
        df.to_csv(convert_filaname, index = False, sep='\t', encoding="utf-8")  
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
        df.to_parquet(".".join(list(target.split('.'))[:-1]) + ".parquet")   
             
        return convert_filaname
    else:
        raise Exception(f"Excluded MIME TYPE{mime}")

    
"""
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
"""



