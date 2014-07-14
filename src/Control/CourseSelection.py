# -*- coding: UTF-8 -*-
'''
Created on Jul 13, 2014

@author: gzq
'''
import urllib
import urllib2
import cookielib
import json
import cStringIO
import datetime

import Levenshtein
from PIL import Image

import config

class CourseSelection():
    '''
    The class is created for select course.
    '''
    def __init__(self, username, password, lesson_num):
        self.username = username
        self.password = password
        self.lesson_num = lesson_num
        self.is_login = False
        self.headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36"}
        self.captcha = ""
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)
        
        # Get the module
        f_handle = open(config.DATA_FILE_NAME, "r")
        self.module_dic = {}
        try:
            self.module_dic = json.load(f_handle)
        except IOError:
            print("%s" % IOError.message)
        
        f_handle.close()
        
    def login(self):
        print("Login...\n===\n")
        
        count = 0
        success_num = 0
        print("下载验证码,二值化,分割,识别,发送登录请求,状态")
        while not self.is_login:
            # Get the login CAPTCHA
            req = urllib2.Request(config.LOGINCAPTCHAURL, headers = self.headers)
            starttime = datetime.datetime.now()
            image_response = self.opener.open(req)
            self.captcha = image_response.read()
            endtime = datetime.datetime.now()
            interval = endtime - starttime
            print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),
            captcha_content = self.captcha_reader()
            if len(captcha_content) != 4:
                print("fail")
                continue
            
            # Start to login
            data = {
                    "studentId": self.username,
                    "password": self.password,
                    "rand": captcha_content,
                    "Submit2": "提交"
                    }
            req = urllib2.Request(config.LOGINURL, urllib.urlencode(data), headers = self.headers)
            starttime = datetime.datetime.now()
            login_response = self.opener.open(req)
            endtime = datetime.datetime.now()
            interval = endtime - starttime
            print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),
            #print(login_response.geturl())
            #print("")
            if login_response.geturl() == "http://xk.fudan.edu.cn/xk/home.html":
                #self.is_login = True
                success_num += 1
                count += 1
                print("success")
            else:
                self.cj = cookielib.CookieJar()
                self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
                urllib2.install_opener(self.opener)
                count += 1
                print("fail")
                #if count > 10:
                    #break
            if count > 4:
                break
        print("total: %d, success: %d", (count, success_num))
            
    
    def captcha_reader2(self):
        starttime = datetime.datetime.now()
        # Thresholding
        #print("Start to do thresholding...")
        
        captcha_file = cStringIO.StringIO(self.captcha)
        img = Image.open(captcha_file)
        img = img.convert("RGBA")
        black_pix = range(img.size[0])
        pixdata = img.load()
        
        identify_list = []
        for y in xrange(img.size[1]):
            for x in xrange(img.size[0]):
                if pixdata[x, y][0] < 90:
                    identify_list.append(1)
                    pixdata[x, y] = (0, 0, 0, 255)
                if pixdata[x, y][1] < 136:
                    identify_list.append(1)
                    pixdata[x, y] = (0, 0, 0, 255)
                if pixdata[x, y][2] > 0:
                    identify_list.append(0)
                    pixdata[x, y] = (255, 255, 255, 255)
                else:
                    identify_list.append(1)
                    pixdata[x, y] = (0, 0, 0, 255)
        endtime = datetime.datetime.now()
        interval = endtime - starttime
        print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),        
        
       
        starttime = datetime.datetime.now()
        # Split figure
        #print("Start to split figure...")
        for x in xrange(img.size[0]):
            row_black_pix = 0
            for y in xrange(img.size[1]):
                if pixdata[x, y] == (0, 0, 0, 255):
                    row_black_pix += 1
            black_pix[x] = row_black_pix
            
        split_position = []
        for i in xrange(1, img.size[0]):
            if black_pix[i] != 0 and black_pix[i - 1] == 0:
                if len(split_position) % 2 == 0:
                    split_position.append(i)
            elif black_pix[i] == 0 and black_pix[i - 1] != 0:
                if i - 1 - split_position[-1] >= 6:
                    split_position.append(i - 1)
                    
        if split_position[1] > 17:
            self.insert_index(1, 10, 16, black_pix, split_position)
        if split_position[3] > 27:
            self.insert_index(3, 20, 26, black_pix, split_position)
        if split_position[5] > 37:
            self.insert_index(5, 30, 36, black_pix, split_position)
        
        endtime = datetime.datetime.now()
        interval = endtime - starttime
        print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),
        
        starttime = datetime.datetime.now()
        # Identify figure
        #print("Start to identify captcha")
        result = ""
        for i in range(4):
            start = split_position[i * 2] * 24
            end = (split_position[i * 2 + 1]) * 24
            
            print identify_list[start : end]
            result += self.loopfunc2(identify_list[start : end])
        
        endtime = datetime.datetime.now()
        interval = endtime - starttime
        print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),   
        #print("Total time：%.5f秒" % (interval.seconds + interval.microseconds / 1000000.0))   
        return result
    
    def captcha_reader(self):
        starttime = datetime.datetime.now()
        # Thresholding
        #print("Start to do thresholding...")
        
        captcha_file = cStringIO.StringIO(self.captcha)
        img = Image.open(captcha_file)
        img = img.convert("RGBA")
        black_pix = range(img.size[0])
        pixdata = img.load()
        
        for y in xrange(img.size[1]):
            for x in xrange(img.size[0]):
                if pixdata[x, y][0] < 90:
                    pixdata[x, y] = (0, 0, 0, 255)
                if pixdata[x, y][1] < 136:
                    pixdata[x, y] = (0, 0, 0, 255)
                if pixdata[x, y][2] > 0:
                    pixdata[x, y] = (255, 255, 255, 255)
                else:
                    pixdata[x, y] = (0, 0, 0, 255)
                
        endtime = datetime.datetime.now()
        interval = endtime - starttime
        print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),        
        
       
        starttime = datetime.datetime.now()
        # Split figure
        #print("Start to split figure...")
        for x in xrange(img.size[0]):
            row_black_pix = 0
            for y in xrange(img.size[1]):
                if pixdata[x, y] == (0, 0, 0, 255):
                    row_black_pix += 1
            black_pix[x] = row_black_pix
            
        split_position = []
        for i in xrange(1, img.size[0]):
            if black_pix[i] != 0 and black_pix[i - 1] == 0:
                if len(split_position) % 2 == 0:
                    split_position.append(i)
            elif black_pix[i] == 0 and black_pix[i - 1] != 0:
                if i - 1 - split_position[-1] >= 6:
                    split_position.append(i - 1)
                    
        if split_position[1] > 17:
            self.insert_index(1, 10, 16, black_pix, split_position)
        if split_position[3] > 27:
            self.insert_index(3, 20, 26, black_pix, split_position)
        if split_position[5] > 37:
            self.insert_index(5, 30, 36, black_pix, split_position)
        
        endtime = datetime.datetime.now()
        interval = endtime - starttime
        print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),        

 
        starttime = datetime.datetime.now()
        # Identify figure
        #print("Start to identify captcha")
        result = ""
        for i in range(4):
            identify_list = black_pix[split_position[i * 2] : split_position[i * 2 + 1]]
            for y in xrange(img.size[1]):
                col_count = 0
                for x in xrange(split_position[i * 2], split_position[i * 2 + 1]):
                    if pixdata[x, y] == (0, 0, 0, 255):
                        col_count += 1
                if col_count != 0:
                    identify_list.append(col_count)
                #col_list.append(col_count)
            #col_list = filter(lambda x : x != 0,col_list)
            #identify_list = identify_list + col_list
            
            result += self.loopfunc(identify_list)
        
        endtime = datetime.datetime.now()
        interval = endtime - starttime
        print "%.5f," % (interval.seconds + interval.microseconds / 1000000.0),   
        #print("Total time：%.5f秒" % (interval.seconds + interval.microseconds / 1000000.0))   
        return result
            
    def loopfunc2(self, identify_list):
        print identify_list
        min_distance = 10000
        min_distance_value = ""
        identify_str = "".join(str(e) for e in identify_list)
        for key in self.module_dic:
#            less_than_fourteen = 0
#            total_num = 0
            for item in self.module_dic[key]:
#                total_num += 1
                temp_distance = Levenshtein.distance(identify_str, "".join(str(e) for e in item))
#                if temp_distance <= 13:
#                    less_than_fourteen += 1
#                if total_num == 5 and less_than_fourteen == 0:
#                    break
                if min_distance > temp_distance:
                    min_distance = temp_distance
                    min_distance_value = key
        return min_distance_value
    
    def loopfunc(self, identify_list):
        min_distance = 25
        min_distance_value = ""
        identify_str = "".join(str(e) for e in identify_list)
        for key in self.module_dic:
            less_than_fourteen = 0
            total_num = 0
            for item in self.module_dic[key]:
                total_num += 1
                temp_distance = Levenshtein.distance(identify_str, "".join(str(e) for e in item))
                if temp_distance <= 13:
                    less_than_fourteen += 1
                if total_num == 5 and less_than_fourteen == 0:
                    break
                if min_distance > temp_distance:
                    min_distance = temp_distance
                    min_distance_value = key
        return min_distance_value

    def insert_index(self, index, low, high, black_pix, split_position):
        min_index = 0
        min_value = 25
        if split_position[index] > high:
            for i in range(low, high):
                if min_value > black_pix[i]:
                    min_value = black_pix[i]
                    min_index = i
            split_position.insert(index, min_index)
            split_position.insert(index + 1, min_index + 1)
        
    def levenshtein(self, first, second):
        if len(first) > len(second):
            first,second = second,first
        if len(first) == 0:
            return len(second)
        if len(second) == 0:
            return len(first)
        first_length = len(first) + 1
        second_length = len(second) + 1
        distance_matrix = [range(second_length) for x in range(first_length)] 
        #print distance_matrix
        for i in range(1,first_length):
            for j in range(1,second_length):
                deletion = distance_matrix[i-1][j] + 1
                insertion = distance_matrix[i][j-1] + 1
                substitution = distance_matrix[i-1][j-1]
                if first[i-1] != second[j-1]:
                    substitution += 1
                distance_matrix[i][j] = min(insertion,deletion,substitution)
        #print distance_matrix
        return distance_matrix[first_length-1][second_length-1]
            
        
        