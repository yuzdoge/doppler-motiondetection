import pyaudio
import sounddevice as sd  
import queue
import threading
import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.animation as animation 
import matplotlib.lines as line
from scipy import fftpack
from scipy import signal as sg 
import time 


class SoundWave(object): 
    def __init__(self,fre=20000):
        self.fre = fre #frequence of sinusoidalwave
        self.fs = 44100 #sampling rate
        self.sentflag = False
        self.sent_thread = None

    def sinusoidalwave(self):
        timelength = 1
        t = np.arange(self.fs*timelength)/self.fs
        y = np.sin(2*np.pi*self.fre*t)
        #y = np.vstack((y,y)).transpose()
        return y

    def sent(self):    
        if not self.sentflag:
            wave = self.sinusoidalwave()
            self.sent_thread = threading.Thread(target=self.sent_wave_thread,args=(wave,))
            self.sent_thread.start()
            self.sentflag = True

    def terminate(self):
        sd.stop()
        self.sent_thread.join()
        exit(0)

    def sent_wave_thread(self,wave):
        print('sent...')
        sd.play(data=wave,samplerate=self.fs,blocking=True,loop=True)


class AudioSpectrum(object):
    def __init__(self,fre=20000):
        #audio revalant
        self.CHANNELS = 1
        self.RATE = 44100 
        self.FORMAT = pyaudio.paInt16
        self.CHUNK = 1024 #frames_per_buffer
        self.RECORD_SECONDS = 5
        '''
        seconds*rate*format/chunk*format 意味着:seconds秒的数据一次去一个缓存块，所需的次数
        注意:这里的seconds并不是指真实录音时间
        '''
        self.stream = None
        self.audio = pyaudio.PyAudio()
        self.queue = queue.Queue()
        self.ad_rdy_ev = threading.Event()
        self.read_thread = None
        self.Interrupted = False
        self.dataflag = False

        #fft revalant
        self.DTdata = []
        self.DTfunc_len = self.CHUNK
        self.window = sg.hamming(self.DTfunc_len)

        #matplotlib revalant
        self.fre = fre
        self.fl = int((self.fre-self.fre*0.05)*self.DTfunc_len/self.RATE) #显示的最低频率
        self.fh = int((self.fre+self.fre*0.05)*self.DTfunc_len/self.RATE) #显示的最高频率
        self.fig = plt.figure('Spectrum')
        self.spectrum_ax = plt.axes(xlim=(self.fre-self.fre*0.05,self.fre+self.fre*0.05),ylim=(10,75))
        #self.spectrum_line = line.Line2D([],[]) 
        #self.spectrum_line = plt.stem([],[])
        
        self.spectrum_y_data = np.arange(0,int(self.DTfunc_len/2)+1,1) #513个点
        self.spectrum_x_data = np.arange(0,int(self.DTfunc_len/2)+1,1)*self.RATE/self.DTfunc_len #513个点
        self.x_clip = self.spectrum_x_data[self.fl:self.fh]
        self.y_clip = self.spectrum_y_data[self.fl:self.fh]

        self.gesture_flag = 0 #0：无动作; 1:远离； 2靠近
    #audio
    def open_stream(self):
        self.stream = self.audio.open(rate = self.RATE,
                                    format=self.FORMAT,
                                    channels=self.CHANNELS,
                                    frames_per_buffer=self.CHUNK,
                                    input=True,
                                    stream_callback=self.callback)
        #每读取一个buffer的流就调用一次回调函数,这是并行的
        self.stream.start_stream()
    
    def callback(self,in_data,frame_count,time_info,status):
        self.queue.put(in_data) #让数据入队列
        self.ad_rdy_ev.set() #告知audiospectrum_thread，数据已经准备好了
        if frame_count <= 0:
            return (None,pyaudio.paComplete) #表明后续无数据
        else:
            return (None,pyaudio.paContinue) #表明后续有数据
        #返回参数形式：(out_data,flag)

    def audiospectrum_thread(self):
        while not self.Interrupted and self.stream.is_active():
            self.ad_rdy_ev.wait(timeout=1) #当事件标志为False，等待0.1秒，大概0.1秒就会读取完
            if not self.queue.empty():
                self.DT_data = np.frombuffer(self.queue.get(),np.dtype('<i2'))#转成小端16bit
                self.DT_data = self.DT_data*self.window #加海明窗
                fft_temp_data = fftpack.fft(self.DT_data,self.DT_data.size,overwrite_x=True)/self.DT_data.size #overwrite_x=True能够被拓展
                self.spectrum_y_data = 20*np.log10(np.abs(fft_temp_data)[0:int(fft_temp_data.size/2)+1])
                self.y_clip = self.spectrum_y_data[self.fl:self.fh]
            self.judge()
            self.ad_rdy_ev.clear()#等待生产者置为True
    
    def read_audio(self):
        self.open_stream()
        self.read_thread = threading.Thread(target=self.audiospectrum_thread)
        self.read_thread.start()
    
    def judge(self):
        max_value = np.max(self.y_clip)
        max_location = np.argmax(self.y_clip)
        temp = self.y_clip.copy() #深拷贝不影响self.y_clip
        if (max_value>=30):
            temp[np.where(temp<20)] = 0 #消除噪声干扰
            left = temp[0:max_location] #人工调参
            right = temp[max_location+1:] #人工调参 
            left_num = len(left.nonzero()[0])
            right_num = len(right.nonzero()[0])
            #print(left_num,' ',right_num)
            if (left_num>right_num+2): #相当于调节灵敏度
                self.gesture_flag = 1
            elif (left_num<right_num-2):
                self.gesture_flag = 2
            else:
                self.gesture_flag = 0
        else:
            self.gesture_flag = 0
    
    def terminate(self):
        #self.Interrupted = True
        self.stream.stop_stream()
        self.stream.close()
        self.read_thread.join()
        self.audio.terminate()
        plt.close()
    
    # matplotlib
    def plot_init(self):
        #self.spectrum_ax.add_line(self.spectrum_line)
        self.scat = self.spectrum_ax.scatter([],[])
        return self.scat,

    def plot_update(self,i):
        #self.spectrum_line.set_xdata(x_clip)
        #self.spectrum_line.set_ydata(y_clip)
        self.scat = self.spectrum_ax.scatter(self.x_clip,self.y_clip)
        return self.scat,
    
    def animate(self):
        ani = animation.FuncAnimation(fig=self.fig,
                                      init_func=self.plot_init,
                                      func=self.plot_update,
                                      frames=1,
                                      interval=30,
                                      blit=True)
        plt.xlabel('frequence')
        plt.ylabel('20lg|H(jw)|')
        plt.show()




        
         