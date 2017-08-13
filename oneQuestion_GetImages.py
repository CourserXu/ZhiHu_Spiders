#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Required
- requests (必须)
- pillow (可选)
Info
- author : "xchaoinfo"
- email  : "xchaoinfo@qq.com"
- date   : "2016.2.4"
Update
- name   : "wangmengcn"
- email  : "eclipse_sv@163.com"
- date   : "2016.4.21"
'''
import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import os.path
try:
    from PIL import Image
except:
    pass
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter
from requests import Session

# 构造 Request headers
agent = 'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0'
headers = {
    'User-Agent': agent
}

# 使用登录cookie信息
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie 未能加载")


def get_xsrf():
    '''_xsrf 是一个动态变化的参数'''
    index_url = 'http://www.zhihu.com'
    # 获取登录时需要用到的_xsrf
    index_page = session.get(index_url, headers=headers)
    html = index_page.text
    pattern = r'name="_xsrf" value="(.*?)"'
    # 这里的_xsrf 返回的是一个list
    _xsrf = re.findall(pattern, html)
    return _xsrf[0]


# 获取验证码
def get_captcha():
    t = str(int(time.time()*1000))
    captcha_url = 'http://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=headers)
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    captcha = input("please input the captcha\n>")
    return captcha


def isLogin():
    # 通过查看用户个人信息来判断是否已经登录
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url,allow_redirects=False).status_code
    if int(x=login_code) == 200:
        return True
    else:
        return False

def login(secret, account):
    # 通过输入的用户名判断是否是手机号
    if re.match(r"^1\d{10}$", account):
        print("手机号登录 \n")
        post_url = 'http://www.zhihu.com/login/phone_num'
        postdata = {
            '_xsrf': get_xsrf(),
            'password': secret,
            'remember_me': 'true',
            'phone_num': account,
        }
    else:
        print("邮箱登录 \n")
        post_url = 'http://www.zhihu.com/login/email'
        postdata = {
            '_xsrf': get_xsrf(),
            'password': secret,
            'remember_me': 'true',
            'email': account,
        }
    try:
        # 不需要验证码直接登录成功
        login_page = session.post(post_url, data=postdata, headers=headers)
        login_code = login_page.text
        #print(login_page.status)
        print("登录成功")
        print(login_code)
    except:
        # 需要输入验证码后才能登录成功
        postdata["captcha"] = get_captcha()
        login_page = session.post(post_url, data=postdata, headers=headers)
        login_code = eval(login_page.text)
        print(login_code['msg'])
    session.cookies.save()

def getPageCode(pageUrl):
    try:
        req = session.get(pageUrl, headers=headers)
        print(req.request.headers)
        return req.text
    except urllib2.URLError as e:
        if hasattr(e, 'reason'):
            print(u"打开链接失败...", e.reason)
            return None

##def getImageUrl(pageUrl):
##    pageCode = getPageCode(pageUrl)
##    if not pageCode:
##        print("打开网页链接失败..")
##        return None
##    pattern = re.compile('<a class="author-link".*?<span title=.*?<div class="zh-summary.*?' +
##                         '<div class="zm-editable-content.*?>(.*?)</div>', re.S)
##    items = re.findall(pattern, pageCode)
##    imagesUrl = []
##    pattern = re.compile('data-actualsrc="(.*?)">', re.S)
##    for item in items:
##        urls = re.findall(pattern, item)
##        imagesUrl.extend(urls)
##    for url in imagesUrl:
##        print(url)
##    return imagesUrl
##
##def saveImagesFromUrl(pageUrl, filePath):
##    imagesUrl = getImageUrl(pageUrl)
##    if not imagesUrl:
##        print('imagesUrl is empty')
##        return
##        nameNumber = 0;
##    for image in imagesUrl:
##        suffixNum = image.rfind('.')
##        suffix = image[suffixNum:]
##        fileName = filePath + os.sep + str(nameNumber) + suffix
##        nameNumber += 1
##        print('save in: ', fileName)
##        response = requests.get(image)
##        contents = response.content
##        try:
##            with open(fileName, "wb") as pic:
##                pic.write(contents)
##        except IOError:
##            print('Io error')

def getImageUrl():
    url = "https://www.zhihu.com/node/QuestionAnswerListV2"
    method = 'next'
    size = 10
    allImageUrl = []

    #循环直至爬完整个问题的回答
    while(True):
        print ('===========offset: ', size)
        postdata = {
            'method': 'next',
            'params': '{"url_token":' + str(46435597) + ',"pagesize": "10",' +\
                      '"offset":' + str(size) + "}",
            '_xsrf':get_xsrf(),

        }
        size += 10
        page = session.post(url, headers=headers, data=postdata)
        ret = eval(page.text)
        listMsg = ret['msg']

        if not listMsg:
            print ("图片URL获取完毕, 页数: ", (size-10)/10)
            return allImageUrl
        pattern = re.compile('data-actualsrc="(.*?)">', re.S)
        for pageUrl in listMsg:
            items = re.findall(pattern, pageUrl)
            for item in items:      #这里去掉得到的图片URL中的转义字符'\\'
                imageUrl = item.replace("\\", "")
                allImageUrl.append(imageUrl)


def saveImagesFromUrl(filePath):
    imagesUrl = getImageUrl()
    #print ("图片数: ", imageUrl)????

    if not imagesUrl:
        print ('imagesUrl is empty'  )
        return
    nameNumber = 0;
    for image in imagesUrl:
        suffixNum = image.rfind('.')
        suffix = image[suffixNum:]
        fileName = filePath + os.sep + str(nameNumber) + suffix
        nameNumber += 1
        try:
            print ("图片: ", image)
            # 设置超时重试次数及超时时间单位秒
            session.mount(image, HTTPAdapter(max_retries=1))
            response = session.get(image, timeout=20)
            contents = response.content
            with open(fileName, "wb") as pic:
                pic.write(contents)

        except IOError:
            print ('Io error'  )
        except requests.exceptions.ConnectionError:
            print ('连接超时,URL: ', image  )
    print ('图片下载完毕')

if __name__ == '__main__':
    if isLogin():
        print('您已经登录')
    else:
        account = input('请输入你的用户名\n>  ')
        secret = input("请输入你的密码\n>  ")
        login(secret, account)
        #saveImagesFromUrl('https://www.zhihu.com/question/46435597', 'D:\Python\Spiders\ZhiHu\ZhiHu_Spiders\Images');
        saveImagesFromUrl('D:\Python\Spiders\ZhiHu\ZhiHu_Spiders\Images')
