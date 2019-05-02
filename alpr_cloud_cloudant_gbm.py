#Time: 4s - 5s
import tkinter
import base64, json, cv2, os, sys
from six import BytesIO
#Conectar con una instancia de servicio de IBM Cloudant en IBM Cloud
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from cloudant.query import Query
# To use ImageTk you need to run dnf install python3-pillow-tk or apt-get install python3-pil.imagetk
import PIL.Image, PIL.ImageTk
from dotenv import load_dotenv
import requests
import threading
import time

load_dotenv()

class App:
    def __init__(self, window, window_title, video_source):
        self.window = window
        self.window.title(window_title)
        self.video_source = video_source

        self.alpr = ALPR()

        self.db = DB()
        
        # open video source
        self.vid = MyVideoCapture(video_source)
        self.first_start = False
        self.ret = None
        self.frame = None
        self.video_status = False
        self.alpr_status = False
        self.alpr_thread = threading.Thread(target=self.do_alpr)
        self.paused = False
        self.pause_cond = threading.Condition(threading.Lock())
        self.result_text = tkinter.StringVar()
        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 1
        #self.async_loop = asyncio.get_event_loop()
        self.errors = []

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = 960, height = 540, bg = "black")
        self.canvas.pack()
        tkinter.Label(window, text = "Resultados:", font = "Verdana 16 bold").pack()
        self.text = tkinter.Label(window, textvariable = self.result_text, font = "Verdana 16 bold")
        self.text.pack()
        self.start_btn = tkinter.Button(window, bg = "green", text = "Start", command = self.start_tasks).pack()
        self.stop_btn = tkinter.Button(window, bg = "red", text = "Stop", command = self.stop_tasks).pack()

        self.window.mainloop()
    
    def __del__(self):
        if self.alpr_thread.is_alive():
            self.alpr_thread.join()

    def start_tasks(self):
        # Evita que se crashee el app si el usuario da clic en Start de nuevo
        if self.video_status is True and self.alpr_status is True:
            pass
        elif not self.first_start:
            self.first_start = True
            self.start_process()
            self.alpr_thread.start()
        else:
            self.resume_alpr()
            self.start_process()
    
    def start_process(self):
        self.video_status = True
        self.alpr_status = True
        self.update_video()
    
    def stop_tasks(self):
        # Evita que se crashee el app si el usuario da clic en Stop de nuevo
        if self.video_status is False and self.alpr_status is False:
            pass
        else:
            #need to fix the closure of the thread
            self.pause_alpr()
            self.alpr_status = False
            self.video_status = False
            self.canvas.delete("all")
    
    def update_video(self):
        # Get a frame from the video source
        self.ret, self.frame = self.vid.get_frame()
        if self.ret:
            resized_frame = cv2.resize(self.frame, (960, 540))
            self.photo = PIL.ImageTk.PhotoImage(
                image=PIL.Image.fromarray(resized_frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
        else:
            self.video_status = False

        if self.video_status:
            self.window.after(self.delay, self.update_video)

    def do_alpr(self):
        while self.alpr_status and self.video_status:
            with self.pause_cond:
                while self.paused:
                    self.pause_cond.wait()
                self.results = self.alpr.recognize_plate(self.frame)
                self.records = self.db.results_check(self.results)
                if self.records != None:
                    for record, suspect in self.records:
                        if suspect is True:
                            self.text.config(fg="red")
                        else:
                            self.text.config(fg="black")

                        self.result_text.set(record)
                        time.sleep(2)
                else:
                    self.result_text.set("")

    def pause_alpr(self):
        self.paused = True
        self.pause_cond.acquire()
    
    def resume_alpr(self):
        self.paused = False
        self.pause_cond.notify()
        self.pause_cond.release()
    
class MyVideoCapture:
    def __init__(self, video_source):
        if video_source.isdigit():
            video_source = int(video_source)
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

class ALPR:
    def __init__(self):
        # openALPR library part
        self.alpr_url = "https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=us&secret_key=%s" % (os.getenv("OPENALPR_SECRET_KEY")) 
    
    def recognize_plate(self, frame):
        with requests.post(self.alpr_url, data=self.convert_frame_to_bytes(frame)) as resp:
            return Converter.json_to_dict(resp.json())

    def convert_frame_to_bytes(self, frame):
        pil_im = PIL.Image.fromarray(frame)
        stream = BytesIO()
        pil_im.save(stream, format="JPEG")
        stream.seek(0)
        img_for_post = stream.read()
        img_base64 = base64.b64encode(img_for_post)
        return img_base64
        
class DB:
    def __init__(self):
        #aquí se ponen las credenciales de servicio de la DB
        self.serviceURL = os.getenv("SERVICE_URL")
        #establecer una conexión con la instancia de servicio
        self.client = Cloudant(os.getenv("SERVICE_USERNAME"), os.getenv("SERVICE_PASSWORD"), url = self.serviceURL)
        self.client.connect()
        #crear una base de datos dentro de la instancia de servicio
        self.db = self.client[os.getenv("CLOUDANT_DB_NAME")]
    
    def __del__(self):
        self.client.disconnect()

    def db_check(self, plates):
        print("chequeando")
        suspect = None
        result_records = []
        query = Query(self.db, selector = { 'placa': { "$in": plates } })
        if query():
            for doc in query()['docs']:
                record = Converter.json_to_dict(doc)
                if record['alerta'] != "":
                    suspect = True
                    result_records.append(["Placa: {}\n Marca: {} \n Modelo: {}\n Alerta: {}"
                                           .format(record['placa'], record['marca'], record['modelo'], record['alerta']), suspect])
                else:
                    suspect = False
                    result_records.append(["Placa: {}\n Marca: {} \n Modelo: {}"
                        .format(record['placa'], record['marca'], record['modelo']), suspect])
        return result_records

    def results_filter(self, results):
        i = 0
        plates = []
        for plate in results['results']:
                i += 1
                if plate['confidence'] < 75:
                    pass
                else:
                    #print("Plate #%d" % i + ": " + str(plate['plate']) + " " + str(plate['confidence']))
                    plates.append(plate['plate'])
        return self.db_check(plates)

    def results_check(self, results):
        if results['error']:
            print("Error code: {}, {}".format(
                results['error_code'], results['error']))
            sys.exit(1)
        elif results['results']:
            return self.results_filter(results)
        else:
            pass
    
class Converter:
    @classmethod
    def json_to_dict(self, json_str):
        return json.loads(json.dumps(json_str))

#print(isinstance(, int))
App(tkinter.Tk(), "GBM ALPR", os.getenv("VIDEO_PATH"))
