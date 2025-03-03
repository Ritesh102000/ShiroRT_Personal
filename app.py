from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from deepface import DeepFace
import os
import cv2
import numpy as np
from PIL import Image
from googleapiclient.http import MediaIoBaseDownload
# Google Drive integration with PyDrive2
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import yaml
import io
from flask import send_file
app = Flask(__name__)

# --- Face Recognition Settings ---
Captured_FOLDER = 'static/captured'
KNOWN_FOLDER = 'static/known_faces'
MAX_KNOWN_FACES = 3
os.makedirs(Captured_FOLDER, exist_ok=True)
os.makedirs(KNOWN_FOLDER, exist_ok=True)
os.environ["DEEPFACE_HOME"] = "weights"
# --- Google Drive Configuration ---
GDRIVE_FOLDER_ID = '1SAO_GDcLlRkr4LhsXBLzWMP6yvlL97dZ'

gauth = GoogleAuth()


gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile("mycreds.txt")
drive = GoogleDrive(gauth)

def upload_to_drive(filepath, filename):
    file_drive = drive.CreateFile({
        'title': filename,
        'parents': [{'id': GDRIVE_FOLDER_ID}]
    })
    file_drive.SetContentFile(filepath)
    file_drive.Upload()
    return file_drive['id']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'result': False, 'error': 'No image uploaded'})
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({'result': False, 'error': 'No selected file'})

    try:
        image_path = os.path.join(Captured_FOLDER, image.filename)
        image.save(image_path)
        known_faces = [os.path.join(KNOWN_FOLDER, f) for f in os.listdir(KNOWN_FOLDER) if f.endswith('.jpg')]

        if not known_faces:
            try:
                _ = DeepFace.analyze(img_path=image_path, actions=['gender'])
                os.rename(image_path, os.path.join(KNOWN_FOLDER, 'known_face_1.jpg'))
                return jsonify({'result': True, 'message': 'Known face registered'})
            except Exception as e:
                return jsonify({'result': False, 'error': 'No face detected'})

        for known_face in known_faces:
            try:
                result = DeepFace.verify(img1_path=image_path, img2_path=known_face)
                if result.get('verified'):
                    return jsonify({'result': True})
            except Exception as e:
                continue

        if len(known_faces) < MAX_KNOWN_FACES:
            try:
                _ = DeepFace.analyze(img_path=image_path, actions=['gender'])
                new_face_path = os.path.join(KNOWN_FOLDER, f'known_face_{len(known_faces) + 1}.jpg')
                os.rename(image_path, new_face_path)
                return jsonify({'result': True, 'message': 'New known face registered'})
            except Exception as e:
                return jsonify({'result': False, 'error': 'No face detected'})

        return jsonify({'result': False, 'error': 'Face not recognized'})

    except Exception as e:
        return jsonify({'result': False, 'error': str(e)})

@app.route('/gallery')
def gallery():
    file_list = drive.ListFile({
        'q': f"'{GDRIVE_FOLDER_ID}' in parents and trashed=false"
    }).GetList()
    images = []
    for f in file_list:
        if f['title'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image_url = f"https://drive.google.com/uc?export=view&id={f['id']}"
            images.append({'url': image_url, 'title': f['title'], 'id': f['id']})
    return render_template('gallery.html', images=images)

@app.route('/upload_new', methods=['POST'])
def upload_new():
    if 'image' not in request.files:
        return redirect(url_for('gallery'))
    
    image = request.files['image']
    if image.filename == '':
        return redirect(url_for('gallery'))

    try:
        temp_folder = 'temp'
        os.makedirs(temp_folder, exist_ok=True)
        temp_path = os.path.join(temp_folder, image.filename)
        image.save(temp_path)
        _ = upload_to_drive(temp_path, image.filename)
        os.remove(temp_path)
        return redirect(url_for('gallery'))
    except Exception as e:
        return jsonify({'result': False, 'error': str(e)})
    
@app.route('/delete', methods=['POST'])
def delete():
    file_id = request.form.get('file_id')
    try:
        file_drive = drive.CreateFile({'id': file_id})
        file_drive.Delete()
        return redirect(url_for('gallery'))
    except Exception as e:
        return jsonify({'result': False, 'error': str(e)})

# New route: Download file via proxy
@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        # Retrieve file metadata
        file_drive = drive.CreateFile({'id': file_id})
        # Create a request to download the file's media content
        request = drive.auth.service.files().get_media(fileId=file_id)
        # Create an in-memory bytes buffer
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        # Serve the file as an attachment using send_file
        return send_file(
            fh,
            as_attachment=True,
            download_name=file_drive['title'],
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'result': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
