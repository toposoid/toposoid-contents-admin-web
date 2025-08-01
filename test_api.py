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
from model import RegistContentResult
from ToposoidCommon.model import TransversalState, Propositions, DocumentRegistration, Document, KnowledgeRegisterHistoryCount, DocumentAnalysisResultHistoryRecord
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
import pprint

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
        
    def test_registImage(self): 
        
        response = self.client.post("/registImage",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": self.id1,
                                "imageReference":{
                                "reference": {
                                    "url": "",
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
        registContentResult = RegistContentResult.parse_obj(response.json())
        assert registContentResult.statusInfo.status == "OK"
        assert registContentResult.knowledgeForImage.imageReference.reference.url == os.environ["TOPOSOID_CONTENTS_URL"] + "images/" + self.id1 + ".jpg"
        assert os.path.exists('contents/images/' + self.id1 + "-org.jpeg")
        assert os.path.exists('contents/images/' + self.id1 + ".jpg")


    def test_registImage2(self): 
        
        response = self.client.post("/registImage",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": self.id2,
                                "imageReference":{
                                "reference": {
                                    "url": "",
                                    "surface": "",
                                    "surfaceIndex": "-1",
                                    "isWholeSentence": True,
                                    "originalUrlOrReference": "http://images.cocodataset.org/train2017/000000428746.jpg",
                                    "metaInformations": []
                                },
                                "x": 0,
                                "y": 0,
                                "width": 0,
                                "height": 0}
                            })
        assert response.status_code == 200
        registContentResult = RegistContentResult.parse_obj(response.json())
        assert registContentResult.statusInfo.status == "OK"
        assert registContentResult.knowledgeForImage.imageReference.reference.url == os.environ["TOPOSOID_CONTENTS_URL"] + "images/" + self.id2 + ".jpg"
        assert os.path.exists('contents/images/' + self.id2 + "-org.jpeg")
        assert os.path.exists('contents/images/' + self.id2 + ".jpg")

    def test_uploadTemporaryImage(self): 
        
        response = self.client.post("/uploadTemporaryImage",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": self.id1,
                                "imageReference":{
                                "reference": {
                                    "url": "",
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
        registContentResult = RegistContentResult.parse_obj(response.json())
        assert registContentResult.statusInfo.status == "OK"
        assert registContentResult.knowledgeForImage.imageReference.reference.url == os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + self.id1 + ".jpg"
        assert os.path.exists('contents/temporaryUse/' + self.id1 + "-org.jpeg")
        assert os.path.exists('contents/temporaryUse/' + self.id1 + ".jpg")

    def test_uploadTemporaryImage2(self): 
        
        response = self.client.post("/uploadTemporaryImage",
                            headers={"Content-Type": "application/json", "X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},
                            json={
                                "id": self.id2,
                                "imageReference":{
                                "reference": {
                                    "url": "",
                                    "surface": "",
                                    "surfaceIndex": "-1",
                                    "isWholeSentence": True,
                                    "originalUrlOrReference": "http://images.cocodataset.org/train2017/000000428746.jpg",
                                    "metaInformations": []
                                },
                                "x": 0,
                                "y": 0,
                                "width": 0,
                                "height": 0}
                            })
        assert response.status_code == 200
        registContentResult = RegistContentResult.parse_obj(response.json())
        assert registContentResult.statusInfo.status == "OK"
        assert registContentResult.knowledgeForImage.imageReference.reference.url == os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + self.id2 + ".jpg"
        assert os.path.exists('contents/temporaryUse/' + self.id2 + "-org.jpeg")
        assert os.path.exists('contents/temporaryUse/' + self.id2 + ".jpg")

    def test_uploadImageFile(self):
        with open("IMG_TEST.png", "rb") as f:
            response = self.client.post("/uploadImageFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": ("IMG_TEST.png", f, "image/png")})
        assert response.status_code == status.HTTP_200_OK
        print(response.json())
    
    def test_uploadDocumentFile(self):
        with open("JAPANESE_DOCUMENT_FOR_TEST.pdf", "rb") as f:
            response = self.client.post("/uploadDocumentFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": ("JAPANESE_DOCUMENT_FOR_TEST.pdf", f, "application/pdf")})
        assert response.status_code == status.HTTP_200_OK
        #pprint.pprint(response)
        document = Document.parse_obj(response.json())
        assert document.filename == "JAPANESE_DOCUMENT_FOR_TEST.pdf"
        assert os.path.exists('contents/documents/' + document.documentId + ".pdf" )
        assert os.path.exists('contents/documents/' + document.documentId + "-" + document.filename )
        documentAnalysisResultHistories = searchDocumentAnalysisResultHistoryByDocumentIdAndStateId(document.documentId, UPLOAD_COMPLETED, self.transversalState)
        assert len(documentAnalysisResultHistories) == 1
        assert documentAnalysisResultHistories[0].documentId == document.documentId
        assert documentAnalysisResultHistories[0].stateId == UPLOAD_COMPLETED
        documentRegistrationJson = receiveMessage(TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE)
        documentRegistration = DocumentRegistration.parse_raw(documentRegistrationJson)
        assert documentRegistration.document.documentId == document.documentId

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

        with open("JAPANESE_DOCUMENT_FOR_TEST.pdf", "rb") as f:
            response = self.client.post("/uploadDocumentFile", headers={"X_TOPOSOID_TRANSVERSAL_STATE": self.transversalState},files={"uploadfile": ("DOCUMENT_FOR_TEST.pdf", f, "application/pdf")})
        assert response.status_code == status.HTTP_200_OK        
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