#Time: 4s - 5s
import requests, base64, json, cv2
from PIL import Image
from six import BytesIO
import mysql.connector as mariadb

#Global variables
#Aqui se especifica donde esta el video
VIDEO_PATH = "/home/roy/Escritorio/noche.mp4" 
#Aqui se inserta el secret key de la cuenta de openALPR
SECRET_KEY = 'sk_12e99fca9917be1d82b94ad6'

#mariadb setup
mariadb_connection = mariadb.connect(host="localhost", user='py', password='GBM.net', database='placasTest', port=3306)
cursor = mariadb_connection.cursor()

STATUS = True

def imgProc(frame):
    frame_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(frame_im)
    stream = BytesIO()
    pil_im.save(stream, format="JPEG")
    stream.seek(0)
    img_for_post = stream.read()
    img_base64 = base64.b64encode(img_for_post)
    return img_base64

def dbCheck(plates):
    for plate in plates:
        cursor.execute("SELECT * FROM placas WHERE placa='{}'".format(plate))
        records = cursor.fetchall()
        if records:
            for row in records:
                if row[5] == "Sospechoso":
                    print("El auto con numero de placa {} es sospechoso".format(plate))
                else:
                    print("El auto con numero de placa {} es no sospechoso".format(plate))

def resultsFilter(results):
    i = 0
    plates = []
    for plate in results['results']:
            i += 1
            if plate['confidence'] < 75:
                pass
            else:
                #print("Plate #%d" % i + ": " + str(plate['plate']) + " " + str(plate['confidence']))
                plates.append(plate['plate'])
    dbCheck(plates)

def resultsCheck(results):
    if results['results']:
        resultsFilter(results)
    else:
        pass

cap = cv2.VideoCapture(VIDEO_PATH)
while STATUS == True:
    STATUS, frame = cap.read()
    # openALPR API part
    url = 'https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s' % (SECRET_KEY)
    r = requests.post(url, data = imgProc(frame))
    results = json.loads(json.dumps(r.json()))
    resultsCheck(results)
    
cap.release()
cv2.destroyAllWindows()