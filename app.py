from flask import Flask, request, send_file, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import subprocess
import time

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
    command = ['ffmpeg', '-i', input_path, '-filter:a', f'volume={volume}', output_path]
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
    output_filename = generate_unique_filename(video.filename, "processed")
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    codec = request.json.get('codec', 'libx265')
    convert_video(input_path, output_path, codec)
    video.processed_filename = output_filename
    db.session.commit()
    return jsonify({'processed_filename': output_filename}), 200

@app.route('/lower_resolution/<int:video_id>', methods=['POST'])
def lower_resolution(video_id):
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    output_filename = generate_unique_filename(video.filename, "lowres")
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    resolution = request.json.get('resolution', '-2:480')  # -2:480 za ohranitev aspect
    change_resolution(input_path, output_path, resolution)
    video.processed_filename = output_filename
    db.session.commit()
    return jsonify({'processed_filename': output_filename}), 200


@app.route('/boost_audio/<int:video_id>', methods=['POST'])
def boost_audio_endpoint(video_id):
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    output_filename = generate_unique_filename(video.filename, "boosted")
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    volume = request.json.get('volume', '5.0')  # 5x volume
    boost_audio(input_path, output_path, volume)
    video.processed_filename = output_filename
    db.session.commit()
    return jsonify({'processed_filename': output_filename}), 200

@app.route('/download/<int:video_id>', methods=['GET'])
def download_file(video_id):
    video = Video.query.get(video_id)
    if not video or not video.processed_filename:
        return jsonify({'error': 'Processed video not found'}), 404
    filepath = os.path.join(app.config['PROCESSED_FOLDER'], video.processed_filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(debug=True)
