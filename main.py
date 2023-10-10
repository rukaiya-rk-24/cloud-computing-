from flask import Flask, render_template, request, abort, send_from_directory
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
from google.cloud import storage

from google.cloud import storage, firestore

# Explicitly use service account credentials by specifying the key file path
storage_client = storage.Client.from_service_account_json('upload-image-ecdc0-c9e222e98775.json')
firestore_client = firestore.Client.from_service_account_json('upload-image-ecdc0-c9e222e98775.json')

def upload_file_to_gcs(file, filename):
    client = storage.Client()
    bucket = client.get_bucket('staging.upload-image-ecdc0.appspot.com')
    blob = bucket.blob(filename)
    blob.upload_from_string(
        file.read(),
        content_type=file.content_type
    )
    return blob.public_url
from google.cloud import firestore

def add_file_metadata_to_firestore(filename, location, size):
    db = firestore.Client()
    files_collection = db.collection('files')
    file_metadata = {
        'filename': filename,
        'location': location,
        'size': size,
    }
    files_collection.add(file_metadata)
def handle_file_upload(request):
    # ... [Your existing checks for file type, size, etc.]
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    
    # Upload file to GCS
    location = upload_file_to_gcs(file, filename)

    # Add metadata to Firestore
    add_file_metadata_to_firestore(filename, location, file.size)
    
    return 'File uploaded successfully', 200

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/images/'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # List all uploaded images
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', images=images)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

if __name__ == '__main__':
    app.run(debug=True)
