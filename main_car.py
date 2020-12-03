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

class Car():
    def __init__(self):
        #servo init
        i2c_bus0 = (busio.I2C(board.SCL_1, board.SDA_1))
        self.kit = ServoKit(channels=16, i2c=i2c_bus0)
        self.turn = self.kit.servo[0]
        self.turn.set_pulse_width_range(1000,2000)
        self.speed = self.kit.continuous_servo[1]
        self.frameDirectory = 'frames/'

        #for saving data
        #0.check if document exists
        #1.open document nd write titles


        #2.camera initialization

    def _csvCheck(self):
        if path.exists('labeled_data.csv') == False:
            with open('labeled_data.csv', 'wb') as csvfile:
                pass


    def _manualDrive(self, con_input):
        self.turn.angle = self._turnMapping(axis[2])
        self.speed.throttle = self._speedReduction(axis[1])
        pass

    #maps range of turning to controller input range
    def _turnMapping(self, con_input):
        turn_angle = np.interp(con_input,[-1,1],[175,45])
        return turn_angle

    #we will need to reduce speed as it's too fast + invert steering
    def _speedReduction(self, con_input):
        #inversing
        speed = con_input * -1.0
    
        if speed > -0.0:
            #print("forward")
            speed_new = np.interp(speed,[0.0,1.0],[0.8,1.0])
            #reducing speed if needed
            final_speed = speed_new * 1.0
            return final_speed
        elif speed < -0.0:
            #print("back")
            speed_new = np.interp(speed,[-0.0,-1.0],[-0.8,-1.0])
            #reducing speed
            final_speed = speed_new * 1.0
            return final_speed
        else:
            return speed  

    def _saveTrainingData(self, axis, frame):
        numbers = '123456789'
        letters = string.ascii_lowercase
        nameOfFrame = ''.join(choice(letters+numbers) for i in range(25))
        cv2.imwrite(self.frameDirectory + nameOfFrame + '.jpg',frame)
        with open('labeled_data.csv', 'a',newline='') as csvfile:
            w = csv.writer(csvfile)
            w.writerow([nameOfFrame,axis[1],axis[2]])



#we will need a model
if __name__ == '__main__':
    ps4_controller = PS4Controller()
    ps4_controller.init()
    cam = Camera()
    rc_car = Car()
    rc_car.turn.angle = 90
    rc_car.turn.angle = 130
    rc_car.turn.angle = 110
    print('ready')

    while True:
        buttons, axis, hat = ps4_controller.listen()
        #print(buttons)
        #rc_car.manual_drive(axis)

        #square = data gathering
        if buttons[0]:
            print("square")
            cam._startThread()
            rc_car._csvCheck()
            while True:
                buttons, axis, hat = ps4_controller.listen()
                rc_car._manualDrive(axis)
                #with 0 to -0.45 doesn't do anyting
                if axis[1] < -0.01:
                    frame = cam._getFrame()
                    rc_car._saveTrainingData(axis, frame)
                if buttons[3]:
                    cam._stopThread()
                    break

        #x = manual drive
        if buttons[1]:
            print("free drive")
            while True:
                buttons, axis, hat = ps4_controller.listen()
                rc_car._manualDrive(axis)
                print("axis: ",axis[1])
                if buttons[3]:
                    break
        
        #allows for safe exit so that thread wouldn't cause interferance
        if buttons[9]:
            break

    cam._stopThread()
        
        
