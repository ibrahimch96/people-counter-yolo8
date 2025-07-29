import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import sqlite3
from datetime import datetime
import torch
import uuid  # Pour générer un identifiant unique par session

# Initialisation de la base de données (ajout de session_id)
def init_db():
    conn = sqlite3.connect('people_counting.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS counts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  track_id INTEGER,
                  timestamp DATETIME,
                  x1 INTEGER,
                  y1 INTEGER,
                  x2 INTEGER,
                  y2 INTEGER,
                  frame_width INTEGER,
                  frame_height INTEGER,
                  object_class TEXT,
                  session_id TEXT)''')  # <-- ajout de session_id ici
    conn.commit()
    conn.close()

# Initialisation
init_db()
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = YOLO('yolov8s.pt').to(device)
tracker = DeepSort(max_age=30, embedder_gpu=(device == 'cuda'))
counted_ids = set()

# Génération d'un session_id unique pour cette exécution
session_id = str(uuid.uuid4())
print(f"Session ID : {session_id}")

cap = cv2.VideoCapture("C:/Users/ibrahim/Downloads/TUD-Stadtmitte-raw.webm")
# cap = cv2.VideoCapture("C:/Users/oumaima/Downloads/PIE_APP/TUD-Stadtmitte-raw.webm")
# cap = cv2.VideoCapture("C:/Users/ibrahim/Downloads/PETS09-S2L1-raw.webm")
# cap = cv2.VideoCapture("C:/Users/ibrahim/Downloads/Video/IGA Supermarket.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_height, frame_width = frame.shape[:2]
    results = model(frame)
    detections = results[0].boxes.data
    person_detections = []

    for det in detections:
        x1, y1, x2, y2, conf, class_id = det.tolist()
        if int(class_id) == 0:
            bbox = [x1, y1, x2 - x1, y2 - y1]
            person_detections.append(([int(v) for v in bbox], conf, 'person'))

    tracks = tracker.update_tracks(person_detections, frame=frame)

    insert_rows = []
    timestamp_now = datetime.now()

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id
        x1, y1, x2, y2 = map(int, track.to_ltrb())

        insert_rows.append((track_id, timestamp_now, x1, y1, x2, y2,
                            frame_width, frame_height, 'person', session_id))

        if track_id not in counted_ids:
            counted_ids.add(track_id)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(frame, f'ID: {track_id}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    if insert_rows:
        conn = sqlite3.connect('people_counting.db')
        c = conn.cursor()
        c.executemany('''INSERT INTO counts 
                         (track_id, timestamp, x1, y1, x2, y2, frame_width, frame_height, object_class, session_id)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', insert_rows)
        conn.commit()
        conn.close()

    cv2.putText(frame, f'Total People: {len(counted_ids)}', (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    cv2.imshow("People Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

