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


from pydantic import BaseModel, model_validator
from typing import List, Any
from enum import Enum
from fastapi import Form
import json

from ToposoidCommon.model import KnowledgeForImage, KnowledgeForTable, Document, StatusInfo

class RegistImageContentResult(BaseModel):
    knowledgeForImage:KnowledgeForImage
    statusInfo:StatusInfo
    
class RegistTableContentResult(BaseModel):
    knowledgeForTable:KnowledgeForTable
    statusInfo:StatusInfo

class RegistDocumentContentResult(BaseModel):
    document:Document
    statusInfo:StatusInfo

