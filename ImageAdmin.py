import requests
import cv2
from model import KnowledgeForImage
import os
import imghdr
import shutil
import time

class ImageAdmin():
    def registImage(self, knowledgeForImage:KnowledgeForImage, isTemporaryUse = False):
                
        # 画像を取得
        for attempt in range(3):
            try:
                header = {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
                }
                with requests.get(knowledgeForImage.imageReference.reference.originalUrlOrReference, stream=True,verify=False, headers=header, timeout=(10.0, 10.0)) as res:
                    # 画像を一時的にファイルに保存
                    with open('tmp/' + knowledgeForImage.id, "wb") as f:
                        for chunk in res.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)

                break
            except requests.exceptions.ChunkedEncodingError:
                time.sleep(1)
        
        
        
        #with open('tmp/' + knowledgeForImage.id, 'wb') as f:
        #    f.write(response.content)
        
        # 画像フォーマットを取得
        fmt = imghdr.what('tmp/' + knowledgeForImage.id)

        #保存
        if knowledgeForImage.imageReference.reference.isWholeSentence:
            if isTemporaryUse:
                shutil.move('tmp/' + knowledgeForImage.id, 'contents/temporaryUse/' + knowledgeForImage.id + "-org." + fmt)
                image = cv2.imread('contents/temporaryUse/' + knowledgeForImage.id + "-org." + fmt)
                #JPEGに変換
                cv2.imwrite('contents/temporaryUse/' + knowledgeForImage.id + ".jpg" , image, [int(cv2.IMWRITE_JPEG_QUALITY), 100]) 
            else:
                shutil.move('tmp/' + knowledgeForImage.id, 'contents/images/' + knowledgeForImage.id + "-org." + fmt)
                image = cv2.imread('contents/images/' + knowledgeForImage.id + "-org." + fmt)
                #JPEGに変換
                cv2.imwrite('contents/images/' + knowledgeForImage.id + ".jpg" , image, [int(cv2.IMWRITE_JPEG_QUALITY), 100]) 
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
                #元画像
                cv2.imwrite('contents/temporaryUse/' + knowledgeForImage.id + "-org." + fmt, image[y:y+h, x:x+w])
                #JPEGに変換
                cv2.imwrite('contents/temporaryUse/' + knowledgeForImage.id + ".jpg" , image[y:y+h, x:x+w], [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            else:
                #元画像
                cv2.imwrite('contents/images/' + knowledgeForImage.id + "-org." + fmt, image[y:y+h, x:x+w])
                #JPEGに変換
                cv2.imwrite('contents/images/' + knowledgeForImage.id + ".jpg", image[y:y+h, x:x+w], [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            #削除
            os.remove('tmp/' + knowledgeForImage.id + "." + fmt)



        if isTemporaryUse:
            knowledgeForImage.imageReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + knowledgeForImage.id + ".jpg"
        else:
            knowledgeForImage.imageReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "images/" + knowledgeForImage.id + ".jpg"

        return knowledgeForImage

    def convertJpeg(self, filename, id):

        # 画像読み込み        
        image = cv2.imread(filename)
        jpegFilename = 'contents/temporaryUse/' + id + ".jpg"
        #JPEGに変換
        cv2.imwrite(jpegFilename, image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        #削除
        os.remove(filename)
        return os.environ["TOPOSOID_CONTENTS_URL"] + "temporaryUse/" + id + ".jpg"
