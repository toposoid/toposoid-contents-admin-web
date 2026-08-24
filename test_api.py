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

from fastapi.testclient import TestClient
from fastapi import status
from api import app
from ToposoidCommon.model import TransversalState, Propositions, DocumentRegistration, Document, KnowledgeRegisterHistoryCount, DocumentAnalysisResultHistoryRecord, StatusInfo, RegisteredImageContentResult, RegisteredTableContentResult, RegisteredDocumentContentResult
import numpy as np
from time import sleep
import pytest
import uuid
import os
from fastapi.encoders import jsonable_encoder
from RdbUtils import addDocumentAnalysisResultHistory, addKnowledgeRegisterHistory, searchDocumentAnalysisResultHistoryByDocumentIdAndStateId, UPLOAD_COMPLETED, ANALYSIS_COMPLETED
from ElasiticMQUtils import receiveMessage
from typing import List
from pydantic import parse_obj_as
import shutil
import pandas as pd
import urllib
import tempfile
from charset_normalizer import from_bytes
import io

TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE = os.environ["TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE"]

class TestToposoidContentsAdminWeb(object):

    client = TestClient(app)
    vector = list(np.random.rand(768))
    id1 = ""
    id2 = ""
    transversalState = str(jsonable_encoder(TransversalState(userId="test-user", username="guest", roleId=0, csrfToken = "")))

    @classmethod
    def setup_class(cls):    
        cls.id1 = str(uuid.uuid4())
        cls.id2 = str(uuid.uuid4())

    @classmethod
    def teardown_class(cls):
        if os.path.isfile('contents/images/' + cls.id1 + ".jpeg"):
            os.remove('contents/images/' + cls.id1 + ".jpeg")
        if os.path.isfile('contents/images/' + cls.id2 + ".jpeg"):    
            os.remove('contents/images/' + cls.id2 + ".jpeg")

    def test_transferFile(self):
        target = f"tmp/{str(uuid.uuid4())}.jpg"
        shutil.copy("IMAGE_TEST.jpg",target)

        with open(target, "rb") as f:
            response = self.client.post("/transferFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": (target.split('/')[-1], f, "image/jpeg")})
        assert response.status_code == status.HTTP_200_OK
        statusInfo = parse_obj_as(StatusInfo, response.json())
        assert(statusInfo.status == "OK")        
        assert(os.path.exists(f"contents/temporaryUse/{target.split('/')[-1]}"))

    def test_registerImage(self):
        featureId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{featureId}.jpg"        
        shutil.copy("IMAGE_TEST.jpg",target)
        shutil.copy("IMAGE_TEST.jpg",f"contents/temporaryUse/{featureId}!IMAGE_TEST.jpg" )

        response = self.client.post("/registerImage",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": self.id1,
                                "imageReference":{
                                "reference": {
                                    "url": f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{featureId}.jpg",
                                    "surface": "猫が",
                                    "surfaceIndex": "0",
                                    "isWholeSentence": False,
                                    "originalUrlOrReference": "http://images.cocodataset.org/val2017/000000039769.jpg",
                                    "metaInformations": []
                                },
                                "x": 27,
                                "y": 41,
                                "width": 287,
                                "height": 435}
                            })
        assert response.status_code == 200
        registImageContentResult = RegisteredImageContentResult.parse_obj(response.json())
        assert registImageContentResult.statusInfo.status == "OK"        
        assert os.path.exists(f"contents/images/{registImageContentResult.knowledgeForImage.id}.jpg")

    def test_registerImage2(self):
        featureId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{featureId}.jpg"        
        shutil.copy("IMAGE_TEST.jpg",target)
        shutil.copy("IMAGE_TEST.jpg",f"contents/temporaryUse/{featureId}!IMAGE_TEST.jpg" )

        response = self.client.post("/registerImage",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": self.id1,
                                "imageReference":{
                                "reference": {
                                    "url": f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{featureId}.jpg",
                                    "surface": "",
                                    "surfaceIndex": "-1",
                                    "isWholeSentence": True,
                                    "originalUrlOrReference": "http://images.cocodataset.org/val2017/000000039769.jpg",
                                    "metaInformations": []
                                },
                                "x": 0,
                                "y": 0,
                                "width": 0,
                                "height": 0}
                            })
        assert response.status_code == 200
        registImageContentResult = RegisteredImageContentResult.parse_obj(response.json())
        assert registImageContentResult.statusInfo.status == "OK"        
        assert os.path.exists(f"contents/images/{registImageContentResult.knowledgeForImage.id}.jpg")

    
    def test_registerTable(self):
        featureId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{featureId}.xlsx"
        shutil.copy("TABLE_TEST.xlsx",target)
        shutil.copy("TABLE_TEST.xlsx",f"contents/temporaryUse/{featureId}!TABLE_TEST.xlsx" )

        response = self.client.post("/registerTable",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": featureId,
                                "tableReference":{
                                "reference": {
                                    "url": f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{featureId}.xlsx",
                                    "surface": "データが",
                                    "surfaceIndex": "0",
                                    "isWholeSentence": False,
                                    "originalUrlOrReference": "",
                                    "metaInformations": []
                                },
                                "skipHeaderRows":0,
                                "skipRowList":[],
                                "multiHeaderRows":1, 
                                "sheetNameForExcel": ""
                                }
                            })
        assert response.status_code == 200
        registTableContentResult = RegisteredTableContentResult.parse_obj(response.json())
        assert registTableContentResult.statusInfo.status == "OK"        
        assert os.path.exists(f"contents/tables/{registTableContentResult.knowledgeForTable.id}.tsv")
        assert os.path.exists(f"contents/tables/{registTableContentResult.knowledgeForTable.id}.parquet")

    def test_registerTable2(self):
        featureId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{featureId}.xlsx"
        self.saveExcel(url = "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000001086170&fileKind=0", 
                       filename = target,
                       featureId = featureId)
        

        response = self.client.post("/registerTable",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": featureId,
                                "tableReference":{
                                "reference": {
                                    "url": f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{featureId}.xlsx",
                                    "surface": "データが",
                                    "surfaceIndex": "0",
                                    "isWholeSentence": False,
                                    "originalUrlOrReference": "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000001086170&fileKind=0",
                                    "metaInformations": []
                                },
                                "skipHeaderRows":5,
                                "skipRowList":[],
                                "multiHeaderRows":4, 
                                "sheetNameForExcel": "se0101"
                                }
                            })
        assert response.status_code == 200
        registTableContentResult = RegisteredTableContentResult.parse_obj(response.json())
        assert registTableContentResult.statusInfo.status == "OK"        
        assert os.path.exists(f"contents/tables/{registTableContentResult.knowledgeForTable.id}.tsv")
        assert os.path.exists(f"contents/tables/{registTableContentResult.knowledgeForTable.id}.parquet")

    def test_registerTable3(self):
        featureId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{featureId}.tsv"
        self.saveTsv(url = "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040292480&fileKind=1", 
                       filename = target,
                       featureId = featureId)
        

        response = self.client.post("/registerTable",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": featureId,
                                "tableReference":{
                                "reference": {
                                    "url": f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{featureId}.tsv",
                                    "surface": "データが",
                                    "surfaceIndex": "0",
                                    "isWholeSentence": False,
                                    "originalUrlOrReference": "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040292480&fileKind=1",
                                    "metaInformations": []
                                },
                                "skipHeaderRows":8,
                                "skipRowList":[],
                                "multiHeaderRows":2, 
                                "sheetNameForExcel": ""
                                }
                            })
        assert response.status_code == 200
        registTableContentResult = RegisteredTableContentResult.parse_obj(response.json())
        assert registTableContentResult.statusInfo.status == "OK"        
        assert os.path.exists(f"contents/tables/{registTableContentResult.knowledgeForTable.id}.tsv")
        assert os.path.exists(f"contents/tables/{registTableContentResult.knowledgeForTable.id}.parquet")

    def test_registerDocument(self):
        documentId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{documentId}.pdf"
        shutil.copy("JAPANESE_DOCUMENT_FOR_TEST.pdf",target)
        shutil.copy("JAPANESE_DOCUMENT_FOR_TEST.pdf",f"contents/temporaryUse/{documentId}!JAPANESE_DOCUMENT_FOR_TEST.pdf" )
        
        document = Document(documentId = "", filename = "", url=f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{documentId}.pdf", size=0)
        
        response = self.client.post("/registerDocument", 
                                    headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                                    json=jsonable_encoder(document))
        assert response.status_code == status.HTTP_200_OK
        registDocumentContentResult = RegisteredDocumentContentResult.parse_obj(response.json())
        documentAnalysisResultHistories = searchDocumentAnalysisResultHistoryByDocumentIdAndStateId(registDocumentContentResult.document.documentId, UPLOAD_COMPLETED, self.transversalState)
        assert len(documentAnalysisResultHistories) == 1
        assert documentAnalysisResultHistories[0].documentId == registDocumentContentResult.document.documentId
        assert documentAnalysisResultHistories[0].stateId == UPLOAD_COMPLETED
        assert(registDocumentContentResult.statusInfo.status == "OK")
        assert os.path.exists(f"contents/documents/{registDocumentContentResult.document.documentId}.pdf" )
        
    """
    def test_analyzePdfDocument2(self):

        with open("DOCUMENT1.pdf", "rb") as f:
            response = self.client.post("/uploadDocumentFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": ("DOCUMENT1.pdf", f, "application/pdf")})
        assert response.status_code == status.HTTP_200_OK        
        documentRegistrationJson = receiveMessage(TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE)
        documentRegistration = DocumentRegistration.parse_raw(documentRegistrationJson)    
        requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': self.transversalState}                
        response = self.client.post("/analyzePdfDocument" , json=jsonable_encoder(documentRegistration.document) , headers=requestHeaders) 
        assert response.status_code == status.HTTP_200_OK
        propositions = Propositions.parse_obj(response.json())
        print(len(propositions.propositions))
        with open("CONTRACT2.pdf", "rb") as f:
            response = self.client.post("/uploadDocumentFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": ("CONTRACT2.pdf", f, "application/pdf")})
        assert response.status_code == status.HTTP_200_OK        
        documentRegistrationJson = receiveMessage(TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE)
        documentRegistration = DocumentRegistration.parse_raw(documentRegistrationJson)    
        requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': self.transversalState}                
        response = self.client.post("/analyzePdfDocument" , json=jsonable_encoder(documentRegistration.document) , headers=requestHeaders) 
        assert response.status_code == status.HTTP_200_OK
        propositions = Propositions.parse_obj(response.json())
        print(len(propositions.propositions))        
    """
    
    def test_analyzePdfDocument(self):

        #with open("JAPANESE_DOCUMENT_FOR_TEST.pdf", "rb") as f:
        #    response = self.client.post("/uploadDocumentFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": ("DOCUMENT_FOR_TEST.pdf", f, "application/pdf")})
        #assert response.status_code == status.HTTP_200_OK        
        documentId = str(uuid.uuid4())
        target = f"contents/temporaryUse/{documentId}.pdf"
        shutil.copy("JAPANESE_DOCUMENT_FOR_TEST.pdf",target)
        shutil.copy("JAPANESE_DOCUMENT_FOR_TEST.pdf",f"contents/temporaryUse/{documentId}!JAPANESE_DOCUMENT_FOR_TEST.pdf" )        
        document = Document(documentId = "", filename = "", url=f"{os.environ['TOPOSOID_CONTENTS_URL']}temporaryUse/{documentId}.pdf", size=0)
        response = self.client.post("/registerDocument", 
                                    headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                                    json=jsonable_encoder(document))
        assert response.status_code == status.HTTP_200_OK
        registDocumentContentResult = RegisteredDocumentContentResult.parse_obj(response.json())        
        assert(registDocumentContentResult.statusInfo.status == "OK")

        documentRegistrationJson = receiveMessage(TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE)
        documentRegistration = DocumentRegistration.parse_raw(documentRegistrationJson)    
        requestHeaders = {'Content-type': 'application/json', 'X_TOPOSOID_TRANSVERSAL_STATE': self.transversalState}                
        response = self.client.post("/analyzePdfDocument" , json=jsonable_encoder(documentRegistration.document) , headers=requestHeaders) 
        assert response.status_code == status.HTTP_200_OK
        propositions = Propositions.parse_obj(response.json())
        documentAnalysisResultHistories = searchDocumentAnalysisResultHistoryByDocumentIdAndStateId(documentRegistration.document.documentId, ANALYSIS_COMPLETED, self.transversalState)
        assert len(documentAnalysisResultHistories) == 1
        assert documentAnalysisResultHistories[0].documentId == documentRegistration.document.documentId
        assert documentAnalysisResultHistories[0].stateId == ANALYSIS_COMPLETED
        assert documentAnalysisResultHistories[0].totalSeparatedNumber == len(propositions.propositions)
        print("check")    


    def test_propositionCount(self):        
        documentId = str(uuid.uuid4())
        propositionId1 = str(uuid.uuid4())
        propositionId2 = str(uuid.uuid4())
        propositionId3 = str(uuid.uuid4())
        addDocumentAnalysisResultHistory(stateId = 5, documentId = documentId, originalFilename = "test.pdf", transversalStateJson = self.transversalState, totalSeparatedNumber=3)
        addKnowledgeRegisterHistory(stateId = 1, documentId= documentId, sequentialNumber=1, propositionId=propositionId1, sentences="これはテスト1です。", json="{}", transversalStateJson=self.transversalState)
        addKnowledgeRegisterHistory(stateId = 1, documentId= documentId, sequentialNumber=2, propositionId=propositionId2, sentences="これはテスト2です。", json="{}", transversalStateJson=self.transversalState)
        addKnowledgeRegisterHistory(stateId = 1, documentId= documentId, sequentialNumber=3, propositionId=propositionId3, sentences="これはテスト3です。", json="{}", transversalStateJson=self.transversalState)
        response = self.client.post("/getTotalPropositionCount",
                    headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                    json={"documentId":documentId, "count":0}
        )
        assert response.status_code == 200
        knowledgeRegisterHistoryCount = KnowledgeRegisterHistoryCount.parse_obj(response.json())
        assert knowledgeRegisterHistoryCount.count == 3

        response = self.client.post("/getAnalyzedPropositionCount",
                    headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                    json={"documentId":documentId, "count":0}
        )
        assert response.status_code == 200
        knowledgeRegisterHistoryCount = KnowledgeRegisterHistoryCount.parse_obj(response.json())
        assert knowledgeRegisterHistoryCount.count == 3

    def test_latestAnalyzedState(self):
        documentId = str(uuid.uuid4())
        addDocumentAnalysisResultHistory(stateId = 1, documentId = documentId, originalFilename = "test.pdf", transversalStateJson = self.transversalState, totalSeparatedNumber=3)
        addDocumentAnalysisResultHistory(stateId = 2, documentId = documentId, originalFilename = "test.pdf", transversalStateJson = self.transversalState, totalSeparatedNumber=3)
        addDocumentAnalysisResultHistory(stateId = 3, documentId = documentId, originalFilename = "test.pdf", transversalStateJson = self.transversalState, totalSeparatedNumber=3)

        response = self.client.post("/getLatestDocumentAnalysisState",
                    headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                    json={"stateId":0, "documentId":documentId, "originalFilename": "", "totalSeparatedNumber":-1}
        )
        assert response.status_code == 200
        documentAnalysisResultHistories = parse_obj_as(List[DocumentAnalysisResultHistoryRecord], response.json())
        assert len(documentAnalysisResultHistories) == 1
        assert documentAnalysisResultHistories[0].documentId == documentId
        assert documentAnalysisResultHistories[0].stateId == 3


    def saveExcel(self, url, filename, featureId):
        with urllib.request.urlopen(url) as response:
            data = response.read() # バイト列の取得
        with open(filename, 'wb') as f:
            f.write(data)
        shutil.copy(filename,f"contents/temporaryUse/{featureId}!.xlsx" )


    def saveTsv(self, url, filename, featureId):
        with urllib.request.urlopen(url) as response:
            data = response.read() # バイト列の取得

        # 2. tempfile で一時ファイルを作成し、読み込む
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            # バイト列をファイルに書き込む
            tmp.write(data)    
            # 読み込みのためにファイルポインタを先頭に戻す
            tmp.seek(0)    
            # 一時ファイルの中身を読み込む
            content = tmp.read()
            res = from_bytes(
                content
            )    
        byte_stream = io.BytesIO(content)
        text_stream = io.TextIOWrapper(byte_stream, encoding=res.best().encoding if res.best() is not None else 'utf-8', errors='ignore')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text_stream.read().replace(",", "\t") )
        shutil.copy(filename,f"contents/temporaryUse/{featureId}!.tsv" )