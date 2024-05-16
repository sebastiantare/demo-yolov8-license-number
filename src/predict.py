from ultralytics import YOLO
import cv2
from sort.sort import Sort
import numpy as np
from util import get_car, read_license_plate, write_csv

results = {}

coco_model = YOLO('yolov8n.pt', verbose=False)
license_plate_detector = YOLO('./model/best.pt', verbose=False)

mot_tracker = Sort()

cap = cv2.VideoCapture('./supercars-cut.mp4')

ret = True

vehicles = [2, 3, 5, 6, 7]  # coco.names

frame_number = -1

while ret:
    frame_number += 1
    ret, frame = cap.read()

    if ret:
        results[frame_number] = {}
        # Detect vehicles
        detections = coco_model(frame)[0]
        detections_ = []

        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            # If is a vehicle of interest
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])
                cv2.rectangle(frame, (int(x1), int(y1)),
                              (int(x2), int(y2)), (0, 255, 0), 2)

        # Track vehicles
        if len(detections_) == 0:
            continue

        track_ids = mot_tracker.update(np.asarray(detections_))

        # Get the license plate of the vehicles in the frame
        license_plates = license_plate_detector(frame)[0]
        plates = 0
        for license_plate in license_plates.boxes.data.tolist():
            plates += 1
            x1, y1, x2, y2, score, class_id = license_plate

            xcar1, ycar1, xcar2, ycar2, score = get_car(
                license_plate, track_ids)

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
                results[frame_number] = json_data

            print("LISENCE TEXT", license_plate_text)

            cv2.rectangle(frame, (int(x1), int(y1)),
                          (int(x2), int(y2)), (255, 0, 0), 2)
            cv2.imshow(f'gray_{plates}', license_plate_crop_gray)
            cv2.imshow(f'threshold_{plates}', license_plate_crop_threshold)

        cv2.imshow("image", frame)
        cv2.waitKey(0)

chilean_letters = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'M', 'N', 'A', 'E', 'I',
                   'U', 'K', 'L', 'P', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z']
"""translate_letters = {
        'O'
        }
translate_number = {

}

def cleanText(text):
"""


cv2.destroyAllWindows()
