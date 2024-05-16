# YoloV8 Car Plate Number detection

This is a demo project that uses Yolov8 for license plate detection, cv2 for processing, easyocr for number detection and Flask to do a psudo-streaming of the processed frames to the website.

I'm using Yolov8 default model for car detection, easyocr and a model I trined myself using Chilean car plates datasets from roboflow.

You can find the model here: https://github.com/sebastiantare/demo-yolov8-license-number/blob/main/src/model/best.pt

## Install

- Download a video and save it to the src folder, replace the name in the app.py. In my case I'm using car videos from this channel: https://www.youtube.com/@CarsyTuning

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
