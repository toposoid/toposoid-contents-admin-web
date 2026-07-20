
from typing import BinaryIO
import shutil
import requests
import time
import glob

class RawDataAdmin():

    def exsitTempraryUse(self, id):
        return True if len(glob.glob("contents/temporaryUse/%s.*" % (id))) > 0 else False

    def checkFile(self):
        #TODO:check File
        #TODO:checkが適切に済んだら、temporaryUseに移動される。
        return

    def getRawData(self, id, file:BinaryIO, resourceNameOrUrl:str):        
        if file is None:
            if not self.exsitTempraryUse(id):
                for attempt in range(3):
                    try:
                        header = {
                            "Accept": "*/*",
                            "Accept-Encoding": "gzip, deflate",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
                        }
                        with requests.get(resourceNameOrUrl, stream=True,verify=False, headers=header, timeout=(10.0, 10.0)) as res:
                            #一時的にファイルに保存
                            with open('tmp/' + id, "wb") as f:
                                for chunk in res.iter_content(chunk_size=1024):
                                    if chunk:
                                        f.write(chunk)
                        break
                    except requests.exceptions.ChunkedEncodingError:
                        time.sleep(1)
                self.checkFile()
        else:
            savepath = f'tmp/{id}-{resourceNameOrUrl}'
            with open(savepath, 'w+b') as buffer:
                shutil.copyfileobj(file, buffer)    
            self.checkFile()
        
