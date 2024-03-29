from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
import numpy as np
import cv2
from matplotlib import pyplot as plt
from shutil import copy2, copy

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#trainedImagePath = os.path.join(APP_ROOT, "train")
#UPLOAD_FOLDER = os.path.join(APP_ROOT, "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

trainedImagePath = "train"
UPLOAD_FOLDER = "uploads"

if not os.path.isdir(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

if not os.path.isdir(trainedImagePath):
        os.mkdir(trainedImagePath)

app = Flask(__name__)
#app.debug = True
app.secret_key = "super_secret_key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

## function to check allowed filetype
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

## function to check image matching and return matching values
def computeImage(img1, img2):
    # Initiate SIFT detector
    # sift = cv2.SIFT()
    sift = cv2.xfeatures2d.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1,None)
    kp2, des2 = sift.detectAndCompute(img2,None)

    # FLANN parameters
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks=200)   # or pass empty dictionary

    flann = cv2.FlannBasedMatcher(index_params,search_params)

    matches = flann.knnMatch(des1,des2,k=2)

    # Need to draw only good matches, so create a mask
    matchesMask = [[0,0] for i in range(len(matches))]

    # ratio test as per Lowe's paper
    matching_points = 0
    total_points = 0
    for i,(m,n) in enumerate(matches):
        if m.distance < 0.7*n.distance:
            matchesMask[i]=[1,0]
            matching_points = matching_points + 1
        total_points = total_points + 1

    matching_percentage = (matching_points * 100) / total_points

    return matching_percentage

## display home page and send required parameters
@app.route('/')
@app.route('/index')
def index():
    os.chmod('uploads', 777)
    os.chmod('train', 777)
    path, dirs, files = next(os.walk(trainedImagePath))
    file_count = len(files)
    image_names = os.listdir('train')
    return render_template('imageAI.html', filecount=file_count, files=files, image_names=image_names)

## upload train images as well as check for existance
@app.route("/upload", methods=['POST'])
def upload():
    #target  = os.path.join(APP_ROOT, 'uploads/')
    #trained = os.path.join(APP_ROOT, 'train/')
    target  = 'uploads/'
    trained = 'train/'
    #print(request.url)
    if not os.path.isdir(target):
            os.mkdir(target)
    else:
        flash("Couldn't create upload directory: {}".format(target))
    
    if not os.path.isdir(trained):
            os.mkdir(trained)

    if request.method == 'POST':
         # check if the post request has the file part
        if 'fileToUpload' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['fileToUpload']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            destination = target + filename #os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(destination)
            print(destination)

            ## after upload to 'uploads' folder check for duplicates
            img1 = cv2.imread(destination, 0)           # queryImage
            
            if not os.listdir("train"):
                copy2(destination, trained)
            else:
                ## Find All images from the train folder
                for file in os.listdir("train"):
                    if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg') or file.lower().endswith('.png'):
                        newImage = trained + file #os.path.join('train/', file)
                        img2 = cv2.imread(newImage, 0)     # trainImage
                        returnValue = computeImage(img1, img2)
                        
                        if returnValue >= 75 :
                            return '<h1> Image already trained.. </h1> <br/> <h3><a href="/"> Back to Home </a></h3>'
            
                copy2(destination, trained)
            return redirect(url_for('index'))
        else:
            return 'File not allowed'

    return 'Error'
    
# Function to check matched images with the big poster
@app.route("/uploaded", methods=['POST'])
def uploaded():
    #target  = os.path.join(APP_ROOT, 'uploads/')
    #trained = os.path.join(APP_ROOT, 'train/')
    target  = 'uploads/'
    trained = 'train/'   

    if not os.path.isdir(target):
            os.mkdir(target)
    else:
        flash("Couldn't create upload directory: {}".format(target))
    

    if not os.path.isdir(trained):
            os.mkdir(trained)

    if request.method == 'POST':
         # check if the post request has the file part
        if 'fileToUpload' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['fileToUpload']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            destination = target + filename #os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(destination)
            #print(destination)

            ## after upload to 'uploads' folder check for matching
            img1 = cv2.imread(destination, 0)           # queryImage
            imgList     = []
            imgValue    = []
            ## Find All images from the train folder
            for file in os.listdir("train"):
                if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg') or file.lower().endswith('.png'):
                    newImage = trained + file # os.path.join('train/', file)
                    img2 = cv2.imread(newImage, 0)     # trainImage
                    returnValue = computeImage(img2, img1)

                    if returnValue >= 1.2 :
                        imgList.append(file)
                        imgValue.append(str(round(returnValue, 2)) +'%')
                        #print(newImage)
                        #print(returnValue)
            
            ## display output 
            return render_template("output.html", image_names=imgList, returnValue=imgValue, image_upload=filename)
        else:
            return 'File not allowed'

    return 'Error'

## to display output images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

## to display Trained Images
@app.route('/train/<filename>')
def send_image(filename):
    return send_from_directory("train", filename)

@app.route('/output')
def get_gallery(imgList):
    print(imgList)
    return render_template("output.html", image_names=imgList)

# if __name__ == "__main__":
#     app.run(port=4555, debug=True)
