#Time: 4s - 5s
import requests, base64, json, cv2, os
from PIL import Image
from six import BytesIO
import mysql.connector as mariadb
from contextlib import closing
from dotenv import load_dotenv

load_dotenv()

#mariadb setup
mariadb_connection = mariadb.connect(host=os.getenv("DB_HOST"),
                                    user=os.getenv("DB_USER"), 
                                    password=os.getenv("DB_PASSWORD"), 
                                    database=os.getenv("MARIA_DB_NAME"), 
                                    port=os.getenv("DB_PORT"))

def jsonToDict(jsonStr):
    return json.loads(json.dumps(jsonStr))

def queryStrBuilder(plates):
    platesLength = len(plates)
    plateQueryStr = ""
    i = 1
    for plate in plates:
        if i == platesLength:
            plateQueryStr += "'" + plate + "'"
        else:
            plateQueryStr += "'" + plate + "', "
        i += 1
    return plateQueryStr

def dbCheck(plates):
    with closing(mariadb_connection.cursor()) as cursor:    
        cursor.execute("SELECT * FROM placas WHERE placa IN ({})".format(queryStrBuilder(plates)))
        records = cursor.fetchall()
    if records:
        for row in records:
            if row[5] == "Sospechoso":
                print("El auto con numero de placa {} es sospechoso".format(row[1]))
            else:
                print("El auto con numero de placa {} es no sospechoso".format(row[1]))

def imgProc(frame):
    frame_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(frame_im)
    stream = BytesIO()
    pil_im.save(stream, format="JPEG")
    stream.seek(0)
    img_for_post = stream.read()
    img_base64 = base64.b64encode(img_for_post)
    return img_base64

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

if __name__ == "__main__":
    cap = cv2.VideoCapture(os.getenv("VIDEO_PATH"))
    OPENALPR_SECRET_KEY = os.getenv("OPENALPR_SECRET_KEY")
    STATUS = True
    while STATUS == True:
        STATUS, frame = cap.read()
        # openALPR API part
        url = "https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s" % (OPENALPR_SECRET_KEY)
        r = requests.post(url, data = imgProc(frame))
        results = jsonToDict(r.json())
        resultsCheck(results)
    mariadb_connection.close()
    cap.release()
    cv2.destroyAllWindows()