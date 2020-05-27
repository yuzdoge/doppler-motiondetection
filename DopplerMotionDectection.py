import sys
import signal
import time 
import cmd_music
from SnRwave import *

class Doppler(AudioSpectrum):
    def __init__(self,fre=20000):
        self.wave = None
        self.detect_thread = None
        self.music = cmd_music.Music()
        AudioSpectrum.__init__(self,fre)
        
    def sent_wave(self):
        self.wave = SoundWave(self.fre)
        self.wave.sent()
        
    def detect_motion(self):
        self.detect_thread = threading.Thread(target=self.detectthread)
        self.detect_thread.start()
        self.read_audio()
        self.animate()
        

    def terminate(self):
        self.Interrupted = True
        self.detect_thread.join()
        self.wave.terminate()
        self.terminate()
    
    def detectthread(self):
        F1 = False
        F2 = False
        double = 0
        num1 = 0
        num2 = 0
        while not self.Interrupted:
            if self.gesture_flag == 0:
                if num1 >=2 and num2 < 2 and F1==True and F2==False:
                    if double < 1:
                        self.music.pause_music()
                        print('暂停')
                        double += 1
                    else:
                        self.music.next_music()
                        print('下一首')
                        double = 0
                    F1 = False
                    F2 = False
                    num1 = 0
                    num2 = 0

                elif num2 >=2 and num1 < 2 and F1==False and F2==True:
                    if not self.music.playflag:
                        self.music.play_music()
                        self.music.playflag = True
                    else:
                        double = 0
                        self.music.unpause_music()
                    print('播放')
                    F1 = False
                    F2 = False
                    num2 = 0
                    num2 = 0

            if self.gesture_flag == 1:
                F1 = True
                F2 = False
                num1 += 1

            if self.gesture_flag == 2:
                F1 = False
                F2 = True
                num2 += 1
            
            #print(num1,num2)
            time.sleep(0.03)
                
        

def signal_handler(signal,frame): 
    doppler.terminate()
    exit(0)
    print('exit')

if __name__ == "__main__":
    doppler = Doppler(fre=20000)
    doppler.sent_wave()
    doppler.detect_motion()
    signal.signal(signal.SIGINT,signal_handler)
    
            

 