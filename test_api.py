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
from fastapi.testclient import TestClient
from fastapi import status
from api import app
from model import StatusInfo, RegistContentResult, TransversalState
import numpy as np
from time import sleep
import pytest
import uuid
import os
from fastapi.encoders import jsonable_encoder

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
                                    "originalUrlOrReference": "http://images.cocodataset.org/val2017/000000039769.jpg"
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
                                    "originalUrlOrReference": "http://images.cocodataset.org/train2017/000000428746.jpg"
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
                                    "originalUrlOrReference": "http://images.cocodataset.org/val2017/000000039769.jpg"
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
                                    "originalUrlOrReference": "http://images.cocodataset.org/train2017/000000428746.jpg"
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
    