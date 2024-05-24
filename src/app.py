import cv2
import base64
import numpy as np
from flask_socketio import emit, SocketIO
from flask import Flask, render_template
from ultralytics import YOLO
from sort.sort import Sort
from util import get_car, read_license_plate
import time
import datetime
import torch

if torch.cuda.is_available():
    torch.cuda.set_device(0)

# app = Flask(__name__, template_folder="templates")
app = Flask(__name__, template_folder="templates",
            static_url_path='/static', static_folder='static')
sio = SocketIO(app)


class Demo:
    def __init__(self):
        self.coco_model = YOLO('yolov8n.pt', verbose=False, task='detect')
        self.coco_model.to('cuda')
        self.license_plate_detector = YOLO(
            './model/best.pt', verbose=False, task='detect')
        self.license_plate_detector.to('cuda')
        self.mot_tracker = Sort()
        #self.cap = cv2.VideoCapture('./CalleDeCoronel.mp4')
        self.cap = cv2.VideoCapture('./coronel-test.mp4')
        # 2: car, 3: motorbike, 5: bus, 6:train, 7: truck
        self.vehicles = [2, 3, 5, 6, 7]  # coco.names
        self.person = 0
        self.dog = 16
        self.ret = True
        self.frame_number = -1
        self.frames_sent = 0
        self.start_time = 0

    def formatLicensePlate(self, text: str):
        # Returns the license formatted if is a valid license

        if not text:
            return

        chars = []

        # Only alphanumeric
        for t in text:
            if t.isalnum():
                chars.append(t)
        clean_text = ''.join(chars)

        # Is valid license
        if len(clean_text) == 6:
            # TODO: Add more validation for chilean license plates
            if clean_text[-2:].isnumeric() and not clean_text[2:].isnumeric():
                return (clean_text)
        elif len(clean_text) > 6:
            clean_text = clean_text[:6]
            if clean_text[-2:].isnumeric() and not clean_text[2:].isnumeric():
                return (clean_text)
        return None

    def isReady(self):
        if self.coco_model and self.license_plate_detector and \
                self.mot_tracker and self.cap.isOpened():
            return True
        print('Not Ready')
        return False

    def getFPS(self):
        end_time = time.time()
        elapsed = end_time - self.start_time
        return int(self.frames_sent/elapsed)

    def getNextFrame(self):
        ret, frame = self.cap.read()

        if ret:
            self.frame_number += 1

            # Detect vehicles
            detections = self.coco_model(frame, verbose=False)[0]
            detections_ = []

            for detection in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection
                # If is a vehicle of interest
                if int(class_id) in self.vehicles:
                    detections_.append([x1, y1, x2, y2, score])
                    cv2.rectangle(frame, (int(x1), int(y1)),
                                  (int(x2), int(y2)), (0, 255, 0), 2)
                if int(class_id) == self.person:
                    cv2.rectangle(frame, (int(x1), int(y1)),
                                  (int(x2), int(y2)), (255, 255, 0), 2)
                if int(class_id) == self.dog:
                    cv2.rectangle(frame, (int(x1), int(y1)),
                                  (int(x2), int(y2)), (0, 255, 255), 2)

        # Track vehicles
        if not detections_ or len(detections_) == 0:
            return

        track_ids = self.mot_tracker.update(np.asarray(detections_))

        # Get the license plate of the vehicles in the frame
        license_plates = self.license_plate_detector(frame, verbose=False)[0]
        plates = 0

        for license_plate in license_plates.boxes.data.tolist():
            plates += 1
            x1, y1, x2, y2, score, class_id = license_plate

            xcar1, ycar1, xcar2, ycar2, score = get_car(
                license_plate, track_ids)

            # print(xcar1, ycar1, xcar2, ycar2, score)

            # Crop license plate
            license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]

            license_plate_crop_gray = cv2.cvtColor(
                license_plate_crop, cv2.COLOR_BGR2GRAY)

            _, license_plate_crop_threshold = cv2.threshold(
                license_plate_crop_gray, 128, 255, cv2.THRESH_BINARY_INV)

            license_plate_text, license_plate_text_score = read_license_plate(
                license_plate_crop_threshold)

            if license_plate_text is not None:
                json_data = {'car':
                             {'bbox': [
                                 xcar1, ycar1, xcar2, ycar2
                             ]},
                             'license_plate':
                             {'bbox': [x1, y1, x2, y2],
                              'text': license_plate_text,
                              'bbox_score': score,
                              'text_score': license_plate_text_score}}

            valid_license = self.formatLicensePlate(license_plate_text)

            if valid_license:
                json_detection = {
                    'license_text': valid_license,
                    'category': str(class_id),
                    'date': str(datetime.datetime.now()),
                    'frame': str(self.frame_number)
                }

                height, width = frame.shape[:2]
                _x1, _y1 = int(max(0, x1)), int(max(0, y1))
                _x2, _y2 = int(min(width, x2)), int(min(height, y2))

                w = int(_x2 - _x1)
                h = int(_y2 - _y1)

                enlarged_license = cv2.resize(
                    license_plate_crop, (int(w*3), int(h*3)),
                    interpolation=cv2.INTER_LINEAR)

                new_x2, new_y2 = int(_x1 + w*3), int(_y1 + h*3)
                if new_x2 > width:
                    new_x2 = width
                if new_y2 > height:
                    new_y2 = height
                frame[_y1:int(new_y2),
                      _x1:int(new_x2)] = enlarged_license[:int(new_y2-_y1),
                                                          :int(new_x2-_x1)]
                emit('detection', json_detection)

            self.frames_sent += 1

            cv2.rectangle(frame, (int(x1), int(y1)),
                          (int(x2), int(y2)), (255, 0, 0), 2)

            _, imgencoded = cv2.imencode('.jpg', frame)

            stringData = base64.b64encode(imgencoded).decode('utf-8')
            b64_src = 'data:image/jpeg;base64,'
            stringData = b64_src + stringData

            json_image = {
                'stringData': stringData,
                'frame': str(self.frame_number)
            }

            emit('response_back', json_image)


demo = None


@sio.on('image')
def image():
    global demo
    if demo:
        del demo
    demo = Demo()
    print('Video Requested')
    if demo and demo.isReady():
        demo.start_time = time.time()
        start_time = time.time()

        try:
            while demo.ret:
                demo.getNextFrame()
                end_time = time.time()
                if end_time - start_time > 3:
                    print(
                        f"FPS: {demo.getFPS()}")
                    start_time = end_time
        except Exception as e:
            print(f"Exception {e}")


@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    sio.run(app, debug=True)
