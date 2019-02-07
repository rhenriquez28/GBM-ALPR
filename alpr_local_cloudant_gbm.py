from openalpr import Alpr
import cv2, sys, os
from dotenv import load_dotenv
#Conectar con una instancia de servicio de IBM Cloudant en IBM Cloud
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

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

# openALPR library part
alpr = Alpr("us", os.getenv("OPENALPR_CONFIG_FILE"), os.getenv("OPENALPR_RUNTIME_DATA_DIR"))
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

cap = cv2.VideoCapture(os.getenv("VIDEO_PATH"))
while STATUS == True:
    STATUS, frame = cap.read()
    # openALPR API part
    results = alpr.recognize_ndarray(frame)
    resultsCheck(results)
    
alpr.unload()
cap.release()
cv2.destroyAllWindows()

