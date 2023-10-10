import requests
import cv2
from model import KnowledgeForImage
import os
import imghdr

class ImageAdmin():
    def registImage(self, knowledgeForImage:KnowledgeForImage):

        # 画像を取得
        response = requests.get(knowledgeForImage.imageReference.reference.originalUrlOrReference)
        
        # 画像を一時的にファイルに保存
        with open('tmp/' + knowledgeForImage.id, 'wb') as f:
            f.write(response.content)
        
        # 画像フォーマットを取得
        fmt = imghdr.what('tmp/' + knowledgeForImage.id)

        # テンポラリファイル名変更
        os.rename('tmp/' + knowledgeForImage.id, 'tmp/' + knowledgeForImage.id + "." + fmt)
        image = cv2.imread('tmp/' + knowledgeForImage.id + "." + fmt)
        
        #加工
        x = knowledgeForImage.imageReference.x
        y = knowledgeForImage.imageReference.y
        w = knowledgeForImage.imageReference.weight
        h = knowledgeForImage.imageReference.height

        #保存
        cv2.imwrite('contents/images/' + knowledgeForImage.id + "." + fmt, image[y:y+h, x:x+w])
        
        #削除
        os.remove('tmp/' + knowledgeForImage.id + "." + fmt)


        knowledgeForImage.imageReference.reference.url = os.environ["TOPOSOID_CONTENTS_URL"] + "images/" + knowledgeForImage.id + "." + fmt

        return knowledgeForImage
