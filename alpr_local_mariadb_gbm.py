import tkinter
from openalpr import Alpr
import cv2, sys, os
# To use ImageTk you eed to run dnf install python3-pillow-tk or apt-get install python3-pil.imagetk
import PIL.Image, PIL.ImageTk
import mysql.connector as mariadb
from contextlib import closing
from dotenv import load_dotenv
import asyncio
import threading

load_dotenv()

#FRAME = None

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
        self.tasks_status = True
        self.result_text = tkinter.StringVar()
        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 1
        self.async_loop = asyncio.get_event_loop()

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = 960, height = 540, bg = "black")
        self.canvas.pack()
        self.text = tkinter.Label(window, textvariable = self.result_text).pack()
        self.start_btn = tkinter.Button(window, bg = "green", text = "Start", command = lambda:self.do_tasks()).pack()
        self.stop_btn = tkinter.Button(window, bg = "red", text = "Stop").pack()

        self.window.mainloop()
    
    def _asyncio_thread(self):
        self.async_loop.run_until_complete(self.do_alpr())

    def do_tasks(self):
        self.update_video()
        """ Button-Event-Handler starting the asyncio part. """
        threading.Thread(target=self._asyncio_thread).start()

    async def do_alpr(self):
        while self.tasks_status:
            await self.update_result()
    
    def update_video(self):
        # Get a frame from the video source
        #global FRAME
        self.ret, self.frame = self.vid.get_frame()
        resized_frame = cv2.resize(self.frame, None, fx = 0.5, fy = 0.5, interpolation = cv2.INTER_LINEAR)
        if self.ret:
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(resized_frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
            #await asyncio.sleep(1)
        
        self.window.after(self.delay, self.update_video)
    
    async def update_result(self):
        #ret, frame = self.vid.get_frame()
        # Return a boolean success flag and the current frame converted to BGR
        if self.ret:
            results = self.alpr.recognize_plate(self.frame)
            self.result_text.set(self.db.results_check(results))
    
    #def start(self):
        # open video source
        #self.vid = MyVideoCapture(video_source)
        #self.alpr = ALPR()
        #self.db = DB()
        # After it is called once, the update method will be automatically called every delay milliseconds
        #self.delay = 15
        #self.update()
    
    #def stop(self):


class MyVideoCapture:
    def __init__(self, video_source):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.alpr = ALPR()
        self.db = DB()

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
            self.window.mainloop()

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

    def db_check(self, plates):
        with closing(self.mariadb_connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM placas WHERE placa IN ({})".format(self.query_str_builder(plates)))
            records = cursor.fetchall()
        if records:
            for row in records:
                if row[5] == "Sospechoso":
                    return "El auto con numero de placa {} es sospechoso".format(row[1])
                else:
                    return "El auto con numero de placa {} es no sospechoso".format(row[1])

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

'''
STATUS = True





def stream(frame):
    frame_image = PhotoImage(Image.fromarray(frame))
    vCanvas.create_image(50, 50, anchor = NE, image = frame_image)
    vCanvas.pack()

def start():
    global STATUS
    cap = cv2.VideoCapture(os.getenv("VIDEO_PATH"))
    while STATUS == True:
        STATUS, frame = cap.read()
        stream(frame)
        # openALPR Library part
        results = alpr.recognize_ndarray(frame)
        resultsCheck(results)

def stop():
    global STATUS
    STATUS = False
    alpr.unload()
    mariadb_connection.close()
    cap.release()
    cv2.destroyAllWindows()

#Tkinter setup
top = Tk()
top.geometry("1000x500")
vCanvas = Canvas(top, bg = "black", height = 250, width = 500)


if __name__ == "__main__":
    start()
    top.mainloop()
'''    
    

