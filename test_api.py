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
from api import app
from model import StatusInfo
import numpy as np
from time import sleep
import pytest
import uuid
import os

class TestWeaviateAPI(object):

    client = TestClient(app)
    vector = list(np.random.rand(768))
    id = ""

    @classmethod
    def setup_class(cls):    
        cls.id = str(uuid.uuid4())

    @classmethod
    def teardown_class(cls):
        os.remove('contents/images/' + cls.id + ".jpeg")
        
    def test_registImage(self): 
        
        response = self.client.post("/registImage",
                            headers={"Content-Type": "application/json"},
                            json={
                                "id": self.id,
                                "imageReference":{
                                "reference": {
                                    "url": "http://images.cocodataset.org/val2017/000000039769.jpg",
                                    "surface": "猫が",
                                    "surfaceIndex": "0",
                                    "isWholeSentence": False
                                },
                                "x": 27,
                                "y": 41,
                                "weight": 287,
                                "height": 435}
                            })
        assert response.status_code == 200
        statusInfo = StatusInfo.parse_obj(response.json())
        assert statusInfo.status == "OK"
        assert os.path.exists('contents/images/' + self.id + ".jpeg")



