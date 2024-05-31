from flask import Flask, request, send_file, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import subprocess
import time
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'processed/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
db = SQLAlchemy(app)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    processed_filename = db.Column(db.String(150), nullable=True)

with app.app_context():
    db.create_all()

def generate_unique_filename(filename, prefix):
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"{prefix}_{base}_{timestamp}{ext}"

def convert_video(input_path, output_path, codec):
    command = ['ffmpeg', '-i', input_path, '-c:v', codec, output_path]
    subprocess.run(command, check=True)

def change_resolution(input_path, output_path, resolution):
    command = ['ffmpeg', '-i', input_path, '-vf', f'scale={resolution}', output_path]
    subprocess.run(command, check=True)

def boost_audio(input_path, output_path, volume):
    command = ['ffmpeg', '-i', input_path, '-filter:a', f'volume={volume}dB', output_path]
    subprocess.run(command, check=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    video = Video(filename=filename)
    db.session.add(video)
    db.session.commit()
    return jsonify({'video_id': video.id}), 200

@app.route('/process/<int:video_id>', methods=['POST'])
def process_video(video_id):
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)

    # Generate unique filenames for temporary, processed, and final processed videos
    temp_filename = generate_unique_filename(video.filename, "temp")
    temp_path = os.path.join(app.config['PROCESSED_FOLDER'], temp_filename)
    processed_filename = generate_unique_filename(video.filename, "processed")
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
    final_processed_filename = generate_unique_filename(video.filename, "final_processed")
    final_processed_path = os.path.join(app.config['PROCESSED_FOLDER'], final_processed_filename)

    data = request.json
    codec = data.get('codec', 'libx265')
    resolution = data.get('resolution', '-2:480')
    volume = data.get('volume', '5')
    bitrate = data.get('bitrate', '1000')
    crf = data.get('crf', '28')  # Default CRF value
    strip_metadata = data.get('strip_metadata', False)

    # Temporary processing step to avoid in-place editing
    change_resolution(input_path, temp_path, resolution)
    convert_video(temp_path, processed_path, codec)

    # Apply audio boost to the processed video
    boost_audio(processed_path, final_processed_path, volume)

    # Generate a new unique filename for the final encoded video
    final_encoded_filename = generate_unique_filename(video.filename, "final_encoded")
    final_encoded_path = os.path.join(app.config['PROCESSED_FOLDER'], final_encoded_filename)

    # Encode the processed video to the selected bitrate and apply CRF
    command = ['ffmpeg', '-i', final_processed_path, '-c:v', codec, '-b:v', f'{bitrate}k', '-crf', crf, final_encoded_path]

    # Optionally strip metadata
    if strip_metadata:
        command.extend(['-map_metadata', '-1'])

    subprocess.run(command, check=True)

    video.processed_filename = final_encoded_filename
    db.session.commit()
    return jsonify({'processed_filename': final_encoded_filename}), 200


@app.route('/download/<int:video_id>', methods=['GET'])
def download_file(video_id):
    video = Video.query.get(video_id)
    if not video or not video.processed_filename:
        return jsonify({'error': 'Processed video not found'}), 404
    filepath = os.path.join(app.config['PROCESSED_FOLDER'], video.processed_filename)
    response = send_file(filepath, as_attachment=True)
    # Delete upload and processed folders after download
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    shutil.rmtree(app.config['PROCESSED_FOLDER'], ignore_errors=True)
    return response

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(debug=True)
