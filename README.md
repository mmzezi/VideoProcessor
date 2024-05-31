# Video processor API

Projekt pri predmetu NUKS. Enostaven Web frontend za FFMPEG, ki za delovanje uporablja Flask in SQLAlchemy. Omogoča kodiranje videa v X265, nižanje resolucije, odstranitev metapodatkov, spremembo CRF ali pa bitne hitrosti.

![alt text](https://files.catbox.moe/pqvqav.jpg)


## Uporaba
```bash
docker build -t videoprocessor .
```

```bash
docker run -d -p 5000:5000 videoprocessor
```

Do vmesnika se dostopa na 127.0.0.1:5000 (localhost).

## API Klici

1. **Upload Video**
   - **URL:** `/upload`
   - **Method:** POST
   - **Description:** Naloži video.
   - **Request Body:**
   - **Response:**
     - Success: 200 OK + JSON objekt z video ID.
     - Error: 400 Bad Request + JSON objekt z error ID.

2. **Process Video**
   - **URL:** `/process/<video_id>`
   - **Method:** POST
   - **Description:** Procesiraj video z ID.
   - **Request Body:** JSON objekt z kodekom.
   - **Response:**
     - Success: 200 OK JSON objekt, vsebuje ime datoteke.
     - Error: 404 Not Found JSON objekt, vsebuje napako.

3. **Lower Resolution**
   - **URL:** `/lower_resolution/<video_id>`
   - **Method:** POST
   - **Description:** Znižaj resolucijo videa z ID.
   - **Request Body:** JSON objekt z resolucijo (ni nujno).
   - **Response:**
     - Success: 200 OK JSON objekt, vsebuje ime datoteke.
     - Error: 404 Not Found JSON objekt, vsebuje napako.

4. **Boost Audio**
   - **URL:** `/boost_audio/<video_id>`
   - **Method:** POST
   - **Description:** Povečaj glasnost video z ID.
   - **Request Body:** JSON objekt, vsebuje nivo glasnosti (ni nujno).
   - **Response:**
     - Success: 200 OK JSON objekt, vsebuje ime datoteke.
     - Error: 404 Not Found JSON objekt, vsebuje napako.

5. **Download Processed Video**
   - **URL:** `/download/<video_id>`
   - **Method:** GET
   - **Description:** Prenesi video z ID.
   - **Response:**
     - Success: Procesiran video kot priloga.
     - Error: 404 Not Found JSON objekt, vsebuje napako.

## Avtentikacija

API ne potrebuje avtentikacije

## Primeri uporabe

### Primer 1: Naloži video

```bash
curl -X POST -F "file=@example.mp4" http://localhost:5000/upload
```

### Primer 2: Procesiraj video

```bash
curl -X POST -H "Content-Type: application/json" -d '{"codec": "libx265"}' http://localhost:5000/process/123
```

### Primer 3: Prenesi procesiran video

```bash
curl -O http://localhost:5000/download/123

```
