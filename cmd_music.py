import pygame
import os
from time import sleep

class Music_List():
    def __init__(self):
        # 播放列表
        self.play_list = []
        # 默认文件夹
        top_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_dir = os.path.join(top_dir,"music")
    def get_play_list(self):
        # 开始遍历目录
        #os.walk(top=adress,topdown=True,onerror=回调函数,followinks=False)；top必选，根目录；
        #os.walk方法放回一个迭代器，迭代器每一个元素是一个三元组(root,dirs,files)；root是当前目录的地址(字符串)，dirs是该目录下子目录的名称 列表，files是改目录下文件的名称 列表
        for root, dirs, files in os.walk(self.file_dir): 
            for file in files:
                if '.mp3' in file:
                    self.play_list.append(self.file_dir + "/" + file)
        print(self.play_list)
        return self.play_list

class Music(object):
    def __init__(self):
        pygame.mixer.init()
        self.music_num = 0
        self.volume = [0.2]
        self.Music_list = Music_List().get_play_list() #获取音乐列表
        self.load_music(self.Music_list[self.music_num]) #加载第一首
        pygame.mixer.music.set_volume(self.volume[0]) #初始化音量
        self.playflag = False
        self.__listlength = len(self.Music_list)

    def load_music(self,titlt):#加载音乐
        try:
            pygame.mixer.music.load(titlt)#载入一个音频流，相当于把数据给准备好，如果该音频流已经在播放，则该函数会中断该音频刘
        except :
            pass

    def play_music(self):
        pygame.mixer.music.play() #music.play(loop=,start=)：loop=x，表示再次循环x次，-1表示无限循环，start=y秒，表示音频起始时间

    def pause_music(self):
        """暂停音乐"""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """解除暂停"""
        pygame.mixer.music.unpause()

    def next_music(self):
        self.music_num = (self.music_num+1) % self.__listlength
        self.load_music(self.Music_list[self.music_num])
        pygame.mixer.music.play()


        




