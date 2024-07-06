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

from pydantic import BaseModel
from typing import List
import logging
LOG = logging.getLogger(__name__)

#Status Information
class StatusInfo(BaseModel):
    status:str
    message:str

class Reference(BaseModel):
    url:str
    surface:str
    surfaceIndex: int
    isWholeSentence: bool
    originalUrlOrReference: str

class ImageReference(BaseModel):
    reference:Reference
    x:int
    y:int
    height:int
    width:int

class KnowledgeForImage(BaseModel):
    id:str
    imageReference:ImageReference

class RegistContentResult(BaseModel):
    knowledgeForImage:KnowledgeForImage
    #knowledgeForOther:knowledgeForOther, //The Other is a feature */
    statusInfo:StatusInfo

class TransversalState(BaseModel):
    username:str