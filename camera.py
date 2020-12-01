from threading import Thread, Lock
import cv2

class Camera:
    def __init__(self, flip = 0, dispW = 640, dispH = 480) :
        self.flip = flip
        self.dispW = dispW
        self.dispH = dispH
        self.pipeline = 'nvarguscamerasrc !  video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method='+str(self.flip)+' ! video/x-raw, width='+str(self.dispW)+', height='+str(self.dispH)+', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
        self.videoFeed = cv2.VideoCapture(self.pipeline)
        self.ret, self.frame = self.videoFeed.read()
        self.thread = Thread(target=self._sync)
        self.on = False
        self.lock = Lock()

    def _startThread(self):
        if self.on:
            return None
        else:
            self.on = True
            self.thread.start()
        return self
    
    def _sync(self):
        while self.on:
            ret, frame = self.videoFeed.read()
            self.lock.acquire()
            self.ret, self.frame = ret, frame
            self.lock.release()

    def _stopThread(self):
        self.on = False
        self.thread.join()
        if self.thread.is_alive():
            self.thread.join()

    def _getFrame(self):
        self.lock.acquire()
        frame = self.frame.copy()
        self.lock.release()
        return frame


if __name__ == "__main__" :
    c = Camera()
    c._startThread()
    while True :
        frame = c._getFrame()
        cv2.imshow('webcam', frame)
        if cv2.waitKey(1) == ord('q') :
            break
    c._stopThread()
    cv2.destroyAllWindows()