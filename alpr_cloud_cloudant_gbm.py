#Time: 4s - 5s
import requests, base64, json, cv2, os, sys
from dotenv import load_dotenv
from PIL import Image
from six import BytesIO
#Conectar con una instancia de servicio de IBM Cloudant en IBM Cloud
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from cloudant.query import Query
#import Document

load_dotenv()

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
    if plates:
        dbCheck(plates)

def resultsCheck(results):
    if results["results"]:
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
    client.disconnect()    
    cap.release()
    cv2.destroyAllWindows()