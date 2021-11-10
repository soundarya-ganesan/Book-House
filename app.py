from flask_cors import cross_origin
import boto3
import os
from flask import Flask,request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import sqlite3 as sql
import boto3
import time
import sys


app = Flask(__name__)

@app.route("/")
@cross_origin()
def home():
    return render_template("index.html")

@app.route('/detect', methods=['GET', 'POST']) 
def detect():
	if request.method == 'POST':
	    file = request.files['image']
	    filename = secure_filename(file.filename)
	    file.save(os.path.join('static\\uploads', filename))
	    REGION = 'us-east-1'
	    PATH_IN_COMPUTER = os.path.join('static\\uploads', filename)
	    BUCKET_NAME = 'myproject-textract' 
	    KEY = 's3://myproject-textract/article.pdf' # file path in S3
	    s3_resource = boto3.resource('s3', region_name = REGION) 
	    s3_resource.Bucket(BUCKET_NAME).put_object(Key = KEY,Body = open(PATH_IN_COMPUTER, 'rb'))
	    print('Uploaded to bucket')

	    # S3 Document Data
	    s3BucketName = "myproject-textract"
	    documentName = "article.pdf"
	    # Function invokes
	    jobId = InvokeTextDetectJob(s3BucketName, documentName)
	    print("Started job with id: {}".format(jobId))
	    if(CheckJobComplete(jobId)):
	    	response = JobResults(jobId)
	    	f = open("static/uploads/output.txt", "w")
	    	for resultPage in response:
	    		for item in resultPage["Blocks"]:
	    			if item["BlockType"] == "LINE":
	    				f.write(item["Text"]+' ')
	    	f.close()


## Textract APIs used - "start_document_text_detection", "get_document_text_detection"
def InvokeTextDetectJob(s3BucketName, objectName):
    response = None
    client = boto3.client(service_name='textract', region_name='us-east-1', use_ssl=True)
    response = client.start_document_text_detection(
            DocumentLocation={
                      'S3Object': {
                                    'Bucket': s3BucketName,
                                    'Name': objectName
                                }
           })
    return response["JobId"]

def CheckJobComplete(jobId):
    time.sleep(5)
    client = boto3.client(service_name='textract', region_name='us-east-1', use_ssl=True)
    response = client.get_document_text_detection(JobId=jobId)
    status = response["JobStatus"]
    print("Job status: {}".format(status))
    while(status == "IN_PROGRESS"):
        time.sleep(5)
        response = client.get_document_text_detection(JobId=jobId)
        status = response["JobStatus"]
        print("Job status: {}".format(status))
    return status

def JobResults(jobId):
    pages = []
    client = boto3.client(service_name='textract',  region_name='us-east-1', use_ssl=True)
    response = client.get_document_text_detection(JobId=jobId)
 
    pages.append(response)
    print("Resultset page recieved: {}".format(len(pages)))
    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']
        while(nextToken):
            response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)
            pages.append(response)
            print("Resultset page recieved: {}".format(len(pages)))
            nextToken = None
            if('NextToken' in response):
                nextToken = response['NextToken']
    return pages


@app.route("/translate_text", methods = ["GET", "POST"])
@cross_origin()
def translate_text():
    if request.method == "POST":
        text = request.form['texttotranslate']  
        sourcelanguage = request.form['sourcelanguage']
        targetlanguage = request.form['targetlanguage']
        translate = boto3.client(service_name='translate',region_name='us-east-1') 

        result = translate.translate_text(Text=text, SourceLanguageCode=sourcelanguage,TargetLanguageCode=targetlanguage)


    return render_template("index.html",conversion=result['TranslatedText'])
    
@app.route("/speech", methods = ["GET", "POST"])
@cross_origin()
def sound():
    if request.method == "POST":
        text = request.form['texttotranslate']  
        polly = boto3.client(service_name='polly',region_name='us-east-1')  
        response = polly.synthesize_speech(OutputFormat='mp3', VoiceId='Brian',Text=text)
        file = open('static/speech.mp3', 'wb')
        file.write(response['AudioStream'].read())
        file.close()
        audiospeech=True
        
        return render_template("index.html",audiospeech=audiospeech)

@app.route("/sentiment", methods = ["GET", "POST"])
@cross_origin()
def sentiment():
    if request.method == "POST":
        text = request.form['texttotranslate']  

        comprehend = boto3.client(service_name='comprehend', region_name='us-east-1') 

        result = comprehend.detect_sentiment(Text=text, LanguageCode='en')

        return render_template("index.html",conversion1=result['Sentiment'])
    else:
        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
