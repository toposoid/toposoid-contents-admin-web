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
import magic
from model import TableFileType
from xls2xlsx import XLS2XLSX
import glob
import pandas as pd

class TableAdmin():



    def saveTablePermanently(self, knowledgeForTable:KnowledgeForTable, isTemporaryUse = False):




        #既にtemporaryUseに保存されていることが前提                
        ext = "." + knowledgeForTable.tableReference.reference.url.split(".")[-1]
        #保存
        if not isTemporaryUse:
            #オリジナルファイルも含めてコピー
            for target in glob.glob("contents/temporaryUse/%s.*" % (knowledgeForTable.id)):
                shutil.copy(target, "contents/tables/")                    
            knowledgeForTable.tableReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "tables/" + knowledgeForTable.id + ext                    
        return knowledgeForTable

    
    def checkFileType(self, filename):
        # ファイルが存在するか確認
        if not os.path.isfile(filename):
            raise FileNotFoundError
        # filetypeライブラリでファイルの種類を推測
        mime = magic.from_file(filename, mime=True)
        if mime is None:
            return TableFileType.NOT_APPLICABLE
        # MIMEタイプから分類
        if mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            return TableFileType.EXCEL 
        elif mime == 'application/vnd.ms-excel':
            return TableFileType.EXCEL_OLD
        elif mime.startswith('text/'):
            return TableFileType.TEXT
        else:
            return TableFileType.NOT_APPLICABLE
        

    def convertUtf8(self, filename, id):
        
        tableFileType = self.checkFileType(filename)
        ext = "." + filename.split(".")[-1]

        #このファイルがExcelファイルかテキストファイルかを見分ける
        if tableFileType == TableFileType.EXCEL:
            #ファイルをリネームして返す
            shutil.move(filename, "contents/temporaryUse/%s-%s" % (id, filename))    
            shutil.copy("contents/temporaryUse/%s-%s" % (id, filename),"contents/temporaryUse/%s.xslx" % (id))
            return "%stemporaryUse/%s.xslx" % (os.environ["TOPOSOID_CONTENTS_URL"], id)

        if tableFileType == TableFileType.EXCEL_OLD:
            #ファイルフォーマットをxslxに変換
            shutil.move(filename, "contents/temporaryUse/%s-%s" % (id, filename))    
            x2x = XLS2XLSX("contents/temporaryUse/%s-%s" % (id, filename))
            x2x.to_xlsx("contents/temporaryUse/%s.xslx" % (id))
            #ファイルをリネームして返す
            return "%stemporaryUse/%s.xslx" % (os.environ["TOPOSOID_CONTENTS_URL"], id)
        
        elif tableFileType == TableFileType.TEXT:            
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
            tableFilename = 'contents/temporaryUse/%s%s' % (id, ext)
            #削除
            os.remove(filename)
            #UTF8にコンバート            
            with open(tableFilename, 'w', encoding='utf-8') as f:
                f.write(text_stream.read())
            
            #区切り文字を文字を自動判定
            df = pd.read_csv(tableFilename, sep=None, engine='python', header=None)

            # タブ区切り（sep='\t'）でファイルに出力
            df.to_csv("contents/temporaryUse/%s.tsv" % (id), sep='\t', index=False)  
            return "%stemporaryUse/%s.tsv" % (os.environ["TOPOSOID_CONTENTS_URL"], id)                      
        else:
            raise Exception("The only file formats accepted for the table are Excel or text files.")
                