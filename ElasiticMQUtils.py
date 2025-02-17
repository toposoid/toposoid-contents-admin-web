
import os
import boto3


TOPOSOID_MQ_ACCESS_KEY = os.environ["TOPOSOID_MQ_ACCESS_KEY"]
TOPOSOID_MQ_SECRET_KEY = os.environ["TOPOSOID_MQ_SECRET_KEY"]
TOPOSOID_MQ_HOST = os.environ["TOPOSOID_MQ_HOST"]
TOPOSOID_MQ_PORT = os.environ["TOPOSOID_MQ_PORT"]
TOPOSOID_MQ_REGION = os.environ["TOPOSOID_MQ_REGION"]

session = boto3.session.Session()
sqsClient = session.client(
    "sqs",
    endpoint_url=f"http://{TOPOSOID_MQ_HOST}:{TOPOSOID_MQ_PORT}",
    region_name=TOPOSOID_MQ_REGION,
    aws_access_key_id=TOPOSOID_MQ_ACCESS_KEY,
    aws_secret_access_key=TOPOSOID_MQ_SECRET_KEY,
    verify=False,
)

def sendMessage(queueName, message):
    queue_url = f"http://{TOPOSOID_MQ_HOST}:{TOPOSOID_MQ_PORT}/{queueName}"  
    response = sqsClient.send_message(QueueUrl=queue_url, MessageGroupId = "x", MessageBody=f"{message}")


def receiveMessage(queueName):
    queue_url = f"http://{TOPOSOID_MQ_HOST}:{TOPOSOID_MQ_PORT}/{queueName}" 
    response = sqsClient.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, VisibilityTimeout=10, WaitTimeSeconds=0)
    if "Messages" in response and len(response["Messages"]) > 0:
        body = response["Messages"][0]["Body"]
        sqsClient.delete_message(QueueUrl=queue_url, ReceiptHandle=response["Messages"][0]["ReceiptHandle"])
        return body
    else:
        return ""


if __name__ == "__main__":
    from ToposoidCommon.model import Document, DocumentRegistration, TransversalState
    from fastapi.encoders import jsonable_encoder
    document = Document(documentId="1", filename="fugafuga", url="hogehoge", size=0)
    transversalState = TransversalState(userId="test-user", username="guest", roleId=0, csrfToken = "")
    documentRegistration = DocumentRegistration(document=document, transversalState=transversalState)
    requestJson = str(jsonable_encoder(documentRegistration)).replace("'", "\"")
    sendMessage(os.environ["TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE"], requestJson)
    print(receiveMessage(os.environ["TOPOSOID_MQ_DOCUMENT_ANALYSIS_QUENE"]))