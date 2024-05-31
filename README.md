# VideoProcessor
Projekt pri predmetu NUKS. Enostaven Web frontend za FFMPEG, ki za delovanje uporablja Flask in SQLAlchemy. Omogoča kodiranje videa v X265, nižanje resolucije ali pa povečanje glasnosti.

## Uporaba
> docker build -t videoprocessor .

>docker run -d -p 5000:5000 videoprocessor
