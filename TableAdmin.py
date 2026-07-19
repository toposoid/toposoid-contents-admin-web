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

from ToposoidCommon import KnowledgeForTable
import tempfile
from charset_normalizer import from_bytes
import io
import os
import shutil
import filetype
from model import TableFileType

class TableAdmin():
    def registTable(self, knowledgeForTable:KnowledgeForTable, isTemporaryUse = False):
        

        #保存
        if knowledgeForTable.tableReference.reference.isWholeSentence:
            if isTemporaryUse:
                #TODO:実装
                print("check1")
            else:
                #TODO:実装
                print("check2")
        else:
            if isTemporaryUse:
                #TODO:実装
                print("check3")
            else:
                #TODO:実装
                print("check4")
        
        if isTemporaryUse:
            knowledgeForTable.tableReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + knowledgeForTable.id + ".jpg"
        else:
            knowledgeForTable.tableReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "tables/" + knowledgeForTable.id + ".jpg"

        return knowledgeForTable

    
    def checkFileType(self, filename):
        # ファイルが存在するか確認
        if not os.path.isfile(filename):
            raise FileNotFoundError
        # filetypeライブラリでファイルの種類を推測
        kind = filetype.guess(filename)
        if kind is None:
            return TableFileType.NOT_APPLICABLE
        # MIMEタイプから分類
        mime_type = kind.mime        
        # Excelファイルかどうか
        # xlsx (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
        # xls (application/vnd.ms-excel など)
        if "excel" in mime_type or mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return TableFileType.EXCEL            
        # テキストファイルかどうか
        elif "text" in mime_type:
            return TableFileType.TEXT            
        else:
            return TableFileType.NOT_APPLICABLE



    def convertUtf8(self, filename, id):
        
        tableFileType = self.checkFileType(filename)

        #このファイルがExcelファイルかテキストファイルかを見分ける
        if tableFileType == TableFileType.EXCEL:
            #ファイルをリネームして返す
            shutil.move(filename, "%stemporaryUse/%s-%s" % (os.environ["TOPOSOID_CONTENTS_URL"], id, filename))    
            shutil.copy("%stemporaryUse/%s-%s" % (os.environ["TOPOSOID_CONTENTS_URL"], id, filename),"%stemporaryUse/%s.xlsx" % (os.environ["TOPOSOID_CONTENTS_URL"], id))
            return "%stemporaryUse/%s.xlsx" % (os.environ["TOPOSOID_CONTENTS_URL"], id)
        elif tableFileType == TableFileType.TEXT:
            ext = "." + filename.split(".")[-1]
            with open(filename, 'rb') as f:
                data = f.read() #バイトデータで読み込む
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
            tableFilename = '%s/temporaryUse/%s%s' % (os.environ["TOPOSOID_CONTENTS_URL"], id, ext)

            #削除
            os.remove(filename)
            #UTF8にコンバート            
            with open(tableFilename, 'w', encoding='utf-8') as f:
                f.write(text_stream.read())        
            return "%stemporaryUse/%s%s" % (os.environ["TOPOSOID_CONTENTS_URL"], id, ext)
        else:
            raise Exception("The only file formats accepted for the table are Excel or text files.")
        

