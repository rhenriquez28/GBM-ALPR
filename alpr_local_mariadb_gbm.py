import tkinter
from openalpr import Alpr
import cv2, sys, os
# To use ImageTk you need to run dnf install python3-pillow-tk or apt-get install python3-pil.imagetk
import PIL.Image, PIL.ImageTk
import mysql.connector as mariadb
from contextlib import closing
from dotenv import load_dotenv
import asyncio
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

        self.ret = None
        self.frame = None
        self.video_status = True
        self.alpr_status = True
        self.alpr_thread = None
        self.result_text = tkinter.StringVar()
        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 1
        self.async_loop = asyncio.get_event_loop()

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = 960, height = 540, bg = "black")
        self.canvas.pack()
        self.text = tkinter.Label(window, textvariable = self.result_text).pack()
        self.start_btn = tkinter.Button(window, bg = "green", text = "Start", command = lambda:self.start_tasks()).pack()
        self.stop_btn = tkinter.Button(window, bg = "red", text = "Stop", command = lambda:self.stop_tasks()).pack()

        self.window.mainloop()
    
    def stop_tasks(self):
        self.alpr_status = False
        if self.async_loop.is_running():
            self.async_loop.stop()
        '''
        if not self.alpr_thread.is_alive():
            print("El thread se murio")
        '''
        #self.alpr_thread.join()
        self.video_status = False
        self.canvas.delete("all")
        

    def _asyncio_thread(self):
        self.async_loop.run_until_complete(self.do_alpr())

    def start_tasks(self):
        self.video_status = True
        self.alpr_status = True
        self.update_video()
        """ Button-Event-Handler starting the asyncio part. """
        self.alpr_thread = threading.Thread(target=self._asyncio_thread)
        self.alpr_thread.daemon = True
        self.alpr_thread.start()

    async def do_alpr(self):
        while self.alpr_status and self.video_status:
            await self.update_result()
    
    def update_video(self):
        # Get a frame from the video source
        self.ret, self.frame = self.vid.get_frame()
        if self.ret:
            resized_frame = cv2.resize(self.frame, None, fx = 0.5, fy = 0.5, interpolation = cv2.INTER_LINEAR)
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(resized_frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        else:
            self.video_status = False

        if self.video_status:
            self.window.after(self.delay, self.update_video)
    
    async def update_result(self):
        # Return a boolean success flag and the current frame converted to BGR
        if self.ret:
            results = self.alpr.recognize_plate(self.frame)
            alerts = self.db.results_check(results)
            if alerts != None:
                for alert in alerts:
                    self.result_text.set(alert)
            else:
                self.result_text.set("")

class MyVideoCapture:
    def __init__(self, video_source):
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
        self.alpr = Alpr("us", os.getenv("OPENALPR_CONFIG_FILE"), os.getenv("OPENALPR_RUNTIME_DATA_DIR"))
        if not self.alpr.is_loaded():
            print("Error loading OpenALPR")
            sys.exit(1)

    def __del__(self):
        self.alpr.unload()
    
    def recognize_plate(self, frame):
        return self.alpr.recognize_ndarray(frame)
        
class DB:
    def __init__(self):
        #mariadb setup
        self.mariadb_connection = mariadb.connect(host=os.getenv("DB_HOST"),
                                            user=os.getenv("DB_USER"),
                                            password=os.getenv("DB_PASSWORD"),
                                            database=os.getenv("MARIA_DB_NAME"),
                                            port=os.getenv("DB_PORT"))
    
    def __del__(self):
        self.mariadb_connection.close()

    def query_str_builder(self, plates):
        plates_length = len(plates)
        plate_query_str = ""
        i = 1
        for plate in plates:
            if i == plates_length:
                plate_query_str += "'" + plate + "'"
            else:
                plate_query_str += "'" + plate + "', "
            i += 1
        print (plate_query_str)
        return plate_query_str

    def db_check(self, plates):
        alerts = []
        with closing(self.mariadb_connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM placas WHERE placa IN ({})".format(self.query_str_builder(plates)))
            records = cursor.fetchall()
        if records:
            for row in records:
                if row[5] == "Sospechoso":
                    alerts.append("El auto con numero de placa {} es sospechoso".format(row[1]))
                else:
                    alerts.append("El auto con numero de placa {} es no sospechoso".format(row[1]))
            return alerts

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
        if results['results']:
            return self.results_filter(results)
        else:
            pass
    

App(tkinter.Tk(), "GBM ALPR", os.getenv("VIDEO_PATH"))