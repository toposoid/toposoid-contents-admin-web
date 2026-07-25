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


from pydantic import BaseModel
from typing import List
from enum import Enum

from ToposoidCommon.model import KnowledgeForImage, KnowledgeForTable, StatusInfo

class RegistImageContentResult(BaseModel):
    knowledgeForImage:KnowledgeForImage
    statusInfo:StatusInfo
    

class RegistTableContentResult(BaseModel):
    knowledgeForTable:KnowledgeForTable
    statusInfo:StatusInfo

class TableFileType(Enum):
    NOT_APPLICABLE = 0
    TEXT = 1
    EXCEL = 2
    EXCEL_OLD = 3

class UploadResult(BaseModel):
    url: str 