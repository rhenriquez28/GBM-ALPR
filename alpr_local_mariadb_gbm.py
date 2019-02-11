from openalpr import Alpr
import cv2, sys, os
import mysql.connector as mariadb
from contextlib import closing
from dotenv import load_dotenv

load_dotenv()

# openALPR library part
alpr = Alpr("us", os.getenv("OPENALPR_CONFIG_FILE"), os.getenv("OPENALPR_RUNTIME_DATA_DIR"))
if not alpr.is_loaded():
    print("Error loading OpenALPR")
    sys.exit(1)

#mariadb setup
mariadb_connection = mariadb.connect(host=os.getenv("DB_HOST"),
                                     user=os.getenv("DB_USER"),
                                     password=os.getenv("DB_PASSWORD"),
                                     database=os.getenv("MARIA_DB_NAME"),
                                     port=os.getenv("DB_PORT"))

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
        cursor.execute(
            "SELECT * FROM placas WHERE placa IN ({})".format(queryStrBuilder(plates)))
        records = cursor.fetchall()
    if records:
        for row in records:
            if row[5] == "Sospechoso":
                print(
                    "El auto con numero de placa {} es sospechoso".format(row[1]))
            else:
                print(
                    "El auto con numero de placa {} es no sospechoso".format(row[1]))

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

STATUS = True
cap = cv2.VideoCapture(os.getenv("VIDEO_PATH"))
while STATUS == True:
    STATUS, frame = cap.read()
    # openALPR Library part
    results = alpr.recognize_ndarray(frame)
    resultsCheck(results)

alpr.unload()
mariadb_connection.close()
cap.release()
cv2.destroyAllWindows()

