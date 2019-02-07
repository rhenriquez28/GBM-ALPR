from openalpr import Alpr
import cv2, sys, os, json
from dotenv import load_dotenv
#Conectar con una instancia de servicio de IBM Cloudant en IBM Cloud
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from cloudant.query import Query

load_dotenv()

# openALPR library part
alpr = Alpr("us", os.getenv("OPENALPR_CONFIG_FILE"), os.getenv("OPENALPR_RUNTIME_DATA_DIR"))
if not alpr.is_loaded():
    print("Error loading OpenALPR")
    sys.exit(1)

#aquí se ponen las credenciales de servicio de la DB
serviceURL = os.getenv("SERVICE_URL")

#establecer una conexión con la instancia de servicio
client = Cloudant(os.getenv("SERVICE_USERNAME"), os.getenv("SERVICE_PASSWORD"), url=serviceURL)
client.connect()
#crear una base de datos dentro de la instancia de servicio
db = client[os.getenv("CLOUDANT_DB_NAME")]

def jsonToDict(jsonStr):
    return json.loads(json.dumps(jsonStr))

#Llamada directa a un punto final de API de IBM Cloudant
def dbCheck(plates):
    query = Query(db, selector={ 'matricula': { "$in": plates } })
    if query():
        for doc in query()['docs']:
            results = jsonToDict(doc)
            print("El auto con placa {} tiene las siguientes alertas: {}"
            .format(results['matricula'], results['alerta']))
    else:
        pass

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
client.disconnect()
cap.release()
cv2.destroyAllWindows()

