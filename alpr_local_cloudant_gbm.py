from openalpr import Alpr
import cv2
import sys

# Global variables
#Aqui se especifica donde esta el video
VIDEO_PATH = "/home/roy/Desktop/noche.mp4"
OPENALPR_CONFIG_FILE = '/etc/openalpr/openalpr.conf'
OPENALPR_RUNTIME_DATA_DIR = '/home/roy/openalpr/runtime_data/'

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()

# openALPR library part
alpr = Alpr("us", OPENALPR_CONFIG_FILE, OPENALPR_RUNTIME_DATA_DIR)
if not alpr.is_loaded():
    print("Error loading OpenALPR")
    sys.exit(1)

STATUS = True

def resultsFilter(results):
    i = 0
    for plate in results['results']:
            i += 1
            if plate['confidence'] < 75:
                pass
            else:
                print("Plate #%d" % i + ": " + str(plate['plate']) + " " + str(plate['confidence']))

def resultsCheck(results):
    if results['results']:
        resultsFilter(results)
    else:
        pass

cap = cv2.VideoCapture(VIDEO_PATH)
while STATUS == True:
    STATUS, frame = cap.read()
    # openALPR API part
    results = alpr.recognize_ndarray(frame)
    resultsCheck(results)
    
alpr.unload()
cap.release()
cv2.destroyAllWindows()

