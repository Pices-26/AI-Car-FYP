from threading import Thread

def work1():
    for i in range(10):
        print('worker 1 is working')

def work2():
    for i in range(10):
        print('worker 2 is working')

x1 = Thread(target= work1)
x2 = Thread(target= work2)

x1.start()
x2.start()
x2.join()