#car main program that will initiate all of the files
from con_py_test import PS4Controller
from adafruit_servokit import ServoKit
import board
import busio
import numpy as np
from os import path
import csv
from camera import Camera
import string
from random import choice
import cv2
import pygame
import time
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.backend import clear_session


class Car():
    def __init__(self):
        #init
        i2cBus0 = (busio.I2C(board.SCL_1, board.SDA_1))
        self.kit = ServoKit(channels=16, i2c=i2cBus0)
        self.turn = self.kit.servo[0]
        self.turn.set_pulse_width_range(1000,2000)
        self.speed = self.kit.continuous_servo[1]
        self.frameDirectory =  '/media/marcel/New Volume/fyp/frames/'
        self.csvDirectory =  '/media/marcel/New Volume/fyp/'
        self.gear = 0.30
        self.model = load_model('resnight100_200.h5')

    def _preprocessImg(self,img):
        #setting image dimensions
        imgH = int(170/3)
        imgW = int(432/3)
        #cropping image
        img = img[70:240,0:432]
        #changing color from RGB to YUV
        img = cv2.cvtColor(img,cv2.COLOR_RGB2YUV)
        #getting image info for size reduction
        h,w,d = img.shape
        #reducing image size
        img = cv2.resize(img,(int(w/3),int(h/3)))
        #gaussian blur on image
        img = cv2.GaussianBlur(img, (3,3),0)
        img = img/255
        #reshaping image so it is complatible as an output + returning it
        return img.reshape(-1,imgH,imgW,3)
    #def _csvCheck(self):
    #    if path.exists('{}labeled_data.csv'.format(self.csvDirectory)) == False:
    #        with open('{}labeled_data.csv'.format(self.csvDirectory), 'wb') as csvfile:
    #            pass

    #driving with 2 inputs (static + given/predicted)
    def _staticDrive(self,speed,turn):
        self.turn.angle = self._turnMapping(turn)
        self.speed.throttle = self._speedReduction(speed)
        pass

    #full control of car
    def _manualDrive(self, conInput):
        self.turn.angle = self._turnMapping(axis[2])
        self.speed.throttle = self._speedReduction(axis[1])
        pass

    #maps range of turning to controller input range
    def _turnMapping(self, conInput):
        #MEMO - 171 - 46 tighter turn
        turnAngle = np.interp(conInput,[-1,1],[175,42])
        return turnAngle

    #we will need to reduce speed as it's too fast + invert steering
    def _speedReduction(self, conInput):
        #inversing controler stick
        speed = conInput * -1.0
    
        #reducing deadzone
        if speed > -0.0:
            #setting forward speed zone
            newSpeed = np.interp(speed,[-0.0,1.0],[0.70,0.72])
            #reducing speed
            finalSpeed = newSpeed * self.gear
            return finalSpeed
        elif speed < -0.0:
            #setting reverse speed zone
            newSpeed = np.interp(speed,[-0.0,-1.0],[-0.8,-0.85])
            #reducing speed
            finalSpeed = newSpeed * self.gear
            return finalSpeed
        else:
            #returning static speed (not moving = 0.00)
            return speed

    #adjusting speed of the car
    def _adjustGears(self, gearAdj):
        #setting minimum and maxium gear range
        if self.gear >= 0.2 and self.gear <= 1.0:
            self.gear = self.gear + gearAdj
            print("new gear ={}".format(self.gear))

        #making sure gear range not exceeded
        if self.gear < 0.20:
            self.gear = 0.25
        if self.gear > 1.0:
            self.gear = 1.0
        pass

    #saving data
    def _saveTrainingData(self, axis, frame):
        #generating data for creation of random string
        numbers = '123456789'
        letters = string.ascii_lowercase
        #generating random string
        nameOfFrame = ''.join(choice(letters+numbers) for i in range(25))
        #checking if image with same name exists + fix if it does
        nameOfFrame = self._checkName(nameOfFrame)
        #save frame
        cv2.imwrite(self.frameDirectory + nameOfFrame + '.jpg',frame)
        #save frame name, speed and turn to csv
        with open('{}labeled_data.csv'.format(self.csvDirectory), 'a',newline='') as csvfile:
            w = csv.writer(csvfile)
            w.writerow([nameOfFrame,axis[1],axis[2]])

    #checking duplicate frame names created
    def _checkName(self, name):
        #checking if file exists + add a random letter to it
        if path.isfile('{}{}{}'.format(self.frameDirectory,name, '.jpg')):
            letter = choice(string.ascii_lowercase)
            newName = name + letter
            return newName
        #string is unique so use it    
        else:
            return name

#main control
if __name__ == '__main__':
    #initializing
    psController = PS4Controller()
    psController.init()
    cam = Camera()
    car = Car()
    gearUP = 0.0005
    gearDOWN = -0.0005
    cam._startThread()
    #car._csvCheck()
    print('Main Menu')

    while True:
        #initial input for going into modes + exiting
        buttons, axis, hat = psController.listen()

        #square = data gathering
        if buttons[0]:
            print("Data Collection Mode - Full Control")
            while True:
                #get controller input
                buttons, axis, hat = psController.listen()
                car._manualDrive(axis)
                
                #if car moving record data
                if axis[1] < -0.01:
                    frame = cam._getFrame()
                    car._saveTrainingData(axis, frame)

                #gear down
                if buttons[4]:
                    car._adjustGears(gearDOWN)

                #gear up
                if buttons[5]:
                    car._adjustGears(gearUP)
                
                #exit mode - triangle
                if buttons[3]:
                    print('Main Menu')
                    break

        #x = manual drive
        if buttons[1]:
            print("Free Drive Mode")
            while True:
                #get controller input
                buttons, axis, hat = psController.listen()
                car._manualDrive(axis)
                #print("speed: ",axis[1])
                print("turn: ", axis[2])

                #gear down
                if buttons[4]:
                    car._adjustGears(gearDOWN)

                #gear up
                if buttons[5]:
                    car._adjustGears(gearUP)
                    
                #exit mode - triangle
                if buttons[3]:
                    print('Main Menu')
                    break
                
        #circle = Autopilot mode
        if buttons[2]:
            print("Autopilot Mode")
            #initial speed
            speed = -0.00
            #time.sleep(2)
            car._staticDrive(-0.00,-0.00)
            while True:
                buttons, axis, hat = psController.listen()
                #drive along with constant speed
                if speed > -0.30:
                    speed = speed - 0.01
                    pass
                
                #getting frame
                frame = cam._getFrame()
                #preprocessing frame
                img = car._preprocessImg(frame)
                #predict model
                pred = car.model.predict(img)
                #unpacking prediction
                turn = pred[0][0]
            
                #bias
                if turn > -0.30:
                    turn = -0.00

                #sending prediction + static speed
                car._staticDrive(speed,turn)

                #print(pred[0][0],speed)
                #exit mode - triangle
                if buttons[3]:
                    #reducing speed back to 0
                    while True:
                        if speed != -0.00:
                            speed = speed + 0.01
                            #if statement to bring value to 0.00 as 
                            #incrementing by 0.01 isn't always exactly 0.01
                            if speed > -0.00:
                                speed = -0.00
                            car._staticDrive(-0.00,speed)
                        else:
                            break
                    print('Main Menu')
                    break

        #right joystick press = special data gathering
        if buttons[11]:
            print('Special Data Control Mode - Static Speed')
            #initial static speed
            speed = -0.00
            car._staticDrive(-0.00,-0.00)
            time.sleep(1)
            while True:
                #controller input
                buttons, axis, hat = psController.listen()

                #incrementing speed to static value
                if speed > -0.20: 
                    speed = speed - 0.01
                #print(speed, axis[2])
                car._staticDrive(speed,axis[2])
                
                #if car moving record data
                if speed < -0.01:
                    frame = cam._getFrame()
                    car._saveTrainingData(axis, frame)

                #gear down
                if buttons[4]:
                    #print(buttons[4])
                    car._adjustGears(-0.0005)
                    #time.sleep(4)

                #gear up
                if buttons[5]:
                    car._adjustGears(0.0005)
                    #print(buttons[5])
                    #time.sleep(4)

                #exid mode - trinagle
                if buttons[3]:
                    #reducing speed back to 0
                    while True:
                        if speed != -0.00:
                            speed = speed + 0.01
                            #if statement to bring value to 0.00 as 
                            #incrementing by 0.01 isn't always exactly 0.01
                            if speed > -0.00:
                                speed = -0.00
                            car._staticDrive(axis[2],speed)
                        else:
                            break
                    print('Main Menu')
                    break
        
        #allows for safe exit so that thread wouldn't cause interferance
        if buttons[9]:
            print('Safe Exit')
            break
    #stopping camera thread
    cam._stopThread()
    clear_session()
        
        
