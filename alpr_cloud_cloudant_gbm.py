#Time: 4s - 5s
import requests, base64, json, cv2, os
from dotenv import load_dotenv
from PIL import Image
from six import BytesIO
#Conectar con una instancia de servicio de IBM Cloudant en IBM Cloud
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
#import Document

load_dotenv()

#aquí se ponen las credenciales de servicio de la DB
serviceURL = os.getenv("SERVICE_URL")

#establecer una conexión con la instancia de servicio
client = Cloudant(os.getenv("SERVICE_USERNAME"), os.getenv("SERVICE_PASSWORD"), url=serviceURL)
client.connect()

#crear una base de datos dentro de la instancia de servicio
databaseName = os.getenv("CLOUDANT_DB_NAME")
#myDatabaseDemo = client.create_database(databaseName)
#if myDatabaseDemo.exists():
#    print (""{0}" successfully created.\n".format(databaseName))

#recuperación de un documento (sin el "include_docs=true")de la DB/ con el include, recupera todo.
#result_collection = Result(myDatabaseDemo.all_docs, include_docs=True)
#print ("Retrieved minimal document:\n{0}\n".format(result_collection[0]))

#Llamada directa a un punto final de API de IBM Cloudant
def comparePlate(comPlate):
    sospechoso = comPlate
    print("sospechoso IN: "+sospechoso)

    end_point = "{0}/{1}".format(serviceURL, databaseName + "/_all_docs")
    params = {"include_docs": "true"}
    
    response = client.r_session.get(end_point, params=params)
    response = response.json()

    #x = (response["rows"][0]["doc"]["matricula"])
    #print("sospechoso DB "+x)
    #if (x==sospechoso):
    #    print("La matricula "+sospechoso+" es sospechoso")
    #else:
    #    print("no es sospechoso") 
    i =0
    for x in response: 
        
        x = (response["rows"][i]["doc"]["matricula"])
        print("sospechoso DB "+x)
        if (x==sospechoso):
            print("La matricula "+sospechoso+" es sospechoso")
        else:
            print("no es sospechoso")
        i+=1 
    return sospechoso

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

def resultsFilter(results):
    i = 0
    for plate in results["results"]:
            i += 1
            if plate["confidence"] < 90:
                pass
            else:
                matricula = (plate["plate"])
                print("La matricula capturada es: "+matricula)
                comparePlate(matricula)

def resultsCheck(results):
    if results["results"]:
        resultsFilter(results)
    else:
        pass

cap = cv2.VideoCapture(os.getenv("VIDEO_PATH"))
OPENALPR_SECRET_KEY = os.getenv("OPENALPR_SECRET_KEY")
while STATUS == True:
    STATUS, frame = cap.read()
    # openALPR API part
    url = "https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s" % (OPENALPR_SECRET_KEY)
    r = requests.post(url, data = imgProc(frame))
    results = json.loads(json.dumps(r.json()))
    resultsCheck(results)
    
cap.release()
cv2.destroyAllWindows()