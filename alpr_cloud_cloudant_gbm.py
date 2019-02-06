#Time: 4s - 5s
import requests, base64, json, cv2
from PIL import Image
from six import BytesIO
#Conectar con una instancia de servicio de IBM Cloudant en IBM Cloud
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

#import Document

#aquí se ponen las credenciales de servicio de la DB
serviceUsername = "1b96e952-903c-4a27-be0c-b3a7111b75f2-bluemix"
servicePassword = "f1600c6ac69c32709af55045edaeea9fad1c3f778f4c28b116d2dd4f7cd8456b"
serviceURL = "https://1b96e952-903c-4a27-be0c-b3a7111b75f2-bluemix:f1600c6ac69c32709af55045edaeea9fad1c3f778f4c28b116d2dd4f7cd8456b@1b96e952-903c-4a27-be0c-b3a7111b75f2-bluemix.cloudant.com"

#establecer una conexión con la instancia de servicio
client = Cloudant(serviceUsername, servicePassword, url=serviceURL)
client.connect()

#crear una base de datos dentro de la instancia de servicio
databaseName = "databasedemo"
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



#Global variables
#Aqui se especifica donde esta el video
VIDEO_PATH = "C:/Users/kkantule/Videos/proyectos/matricula/video/noche.mp4" 
#Aqui se inserta el secret key de la cuenta de openALPR
SECRET_KEY = "sk_06c07f8736010251b5372ec1"

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

cap = cv2.VideoCapture(VIDEO_PATH)
while STATUS == True:
    STATUS, frame = cap.read()
    # openALPR API part
    url = "https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s" % (SECRET_KEY)
    r = requests.post(url, data = imgProc(frame))
    results = json.loads(json.dumps(r.json()))
    resultsCheck(results)
    
cap.release()
cv2.destroyAllWindows()