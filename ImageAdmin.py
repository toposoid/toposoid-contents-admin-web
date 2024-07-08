import requests
import cv2
from model import KnowledgeForImage
import os
import imghdr
import shutil
import time

class ImageAdmin():
    def registImage(self, knowledgeForImage:KnowledgeForImage, isTemporaryUse = False):
        
        response = None
        # 画像を取得
        for attempt in range(3):
            try:
                response = requests.get(knowledgeForImage.imageReference.reference.originalUrlOrReference, stream=True,verify=False, timeout=(5.0, 10.0))
                break
            except requests.exceptions.ChunkedEncodingError:
                time.sleep(1)
        
        
        # 画像を一時的にファイルに保存
        with open('tmp/' + knowledgeForImage.id, 'wb') as f:
            f.write(response.content)
        
        # 画像フォーマットを取得
        fmt = imghdr.what('tmp/' + knowledgeForImage.id)

        #保存
        if knowledgeForImage.imageReference.reference.isWholeSentence:
            if isTemporaryUse:
                shutil.move('tmp/' + knowledgeForImage.id, 'contents/temporaryUse/' + knowledgeForImage.id + "." + fmt)
            else:
                shutil.move('tmp/' + knowledgeForImage.id, 'contents/images/' + knowledgeForImage.id + "." + fmt)
        else:
            # テンポラリファイル名変更
            os.rename('tmp/' + knowledgeForImage.id, 'tmp/' + knowledgeForImage.id + "." + fmt)

            image = cv2.imread('tmp/' + knowledgeForImage.id + "." + fmt)            
            #加工
            x = knowledgeForImage.imageReference.x
            y = knowledgeForImage.imageReference.y
            w = knowledgeForImage.imageReference.width
            h = knowledgeForImage.imageReference.height
            
            if isTemporaryUse:
                cv2.imwrite('contents/temporaryUse/' + knowledgeForImage.id + "." + fmt, image[y:y+h, x:x+w])
            else:
                cv2.imwrite('contents/images/' + knowledgeForImage.id + "." + fmt, image[y:y+h, x:x+w])
            #削除
            os.remove('tmp/' + knowledgeForImage.id + "." + fmt)

        if isTemporaryUse:
            knowledgeForImage.imageReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + knowledgeForImage.id + "." + fmt
        else:
            knowledgeForImage.imageReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "images/" + knowledgeForImage.id + "." + fmt

        return knowledgeForImage
