# YoloV8 Car Plate Number detection

This is a demo project that uses Yolov8 and Flask to do a psudo-streaming of the processed frames with Yolo and also the detected licenses to the webpage.

I'm using Yolov8 default model for car detection, easyocr and a model I trined myself using Chilean car plates datasets from roboflow.

You can find the model here: https://github.com/sebastiantare/demo-yolov8-license-number/blob/main/src/model/best.pt

## Install

- Download a video and save it to the src folder, replace the name in the app.py.

```
python -m venv env
source env/bin/activate
pip install -r requirements
```

```
cd src
python app.py
```

Open: http://localhost:5000
