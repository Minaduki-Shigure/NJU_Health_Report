import sys
import json

import requests
import js2py

from bs4 import BeautifulSoup

# 在这里填入你的统一身份认证用户名、密码和你的打卡位置
UserName = '学号'
UserPass = '密码'
UserLocation = '打卡位置'

# 如果需要，在这里修改打卡系统的终点URL，这三个URL分别是统一身份认证、获取打卡列表（其实没用上）、上报打卡信息的URL
AuthURL = 'https://authserver.nju.edu.cn/authserver/login?service=https%3A%2F%2Fehallapp.nju.edu.cn%3A443%2Fxgfw%2Fsys%2Fyqfxmrjkdkappnju%2Fapply%2FgetApplyInfoList.do'
ListURL = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do'
ReportURL = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do'

# 统一认证系统使用这个文件中的encryptAES函数对输入密码进行加盐处理
# 由于没学过密码学，只能照搬js文件
# js文件路径为https://authserver.nju.edu.cn/authserver/custom/js/encrypt.js
# 也许学校会更换这个文件导致程序失效，所以把路径放在这里
# 不过如果真换了估计整个流程也都不一样了
EncryptJS = './encrypt.js'

# 存储打卡过程中下发的的所有cookie
cookies = {}

# 打开统一认证
# 统一认证的网页会下发以下几个参数：
# pwdDefaultEncryptSalt: 用于给输入的密码加盐
# lt: 一串LT开头的字符串，需要回报给服务器，可能是用于区分会话
# dllt: 似乎用于区分登陆方式使用的是密码/验证码/微信扫码
# execcution: 未知，似乎只有'e1s1'和'e2s1'两种
# _eventId: 似乎是用于确定点击按钮后触发事件的ID？为啥要上报这个？我没学过JS，希望有大佬指正
# rmShown: 未知
# 如果密码输错了，就会要求输入验证码，这个程序不能处理验证码，所以千万别输错
authPage = requests.get(url = AuthURL)
if authPage.status_code == 200:
    # 更新cookie
    authCookie = requests.utils.dict_from_cookiejar(authPage.cookies)
    cookies.update(authCookie)

    # 调用BeautifulSoup分析网页，寻找下发的参数
    # features可以修改成其他已经装好的包，如html-parser或html5lib
    soup = BeautifulSoup(authPage.text, features = 'lxml')
    saltElem = soup.select('#pwdDefaultEncryptSalt')
    ltElem = soup.find(name = 'input', attrs = {'name': 'lt'})
    executionElem = soup.find(name = 'input', attrs = {'name': 'execution'})
    eventIdElem = soup.find(name = 'input', attrs = {'name': '_eventId'})
    rmShownElem = soup.find(name = 'input', attrs = {'name': 'rmShown'})

    # 从找到的参数中提取值
    salt = saltElem[0].attrs['value']
    lt = ltElem.attrs['value']
    execution = executionElem.attrs['value']
    eventId = eventIdElem.attrs['value']
    rmShown = rmShownElem.attrs['value']

    # 使用js2py调用统一认证的encrypt.js完成对密码的加盐操作
    jsContext = js2py.EvalJs()
    jsContext.execute(open(EncryptJS).read())
    encryptedPass = jsContext.encryptAES(UserPass, salt)
else:
    # 如果统一认证返回的状态码不是200，则panic
    print('\033[1;31;43mUnexpected response %d from AuthServer. Panic.\033[0m' % (authPage.status_code))
    print('\033[1;31;43mFailed to report health status!\033[0m')
    sys.exit()

# 回报给统一认证的登陆凭据
# 其中dllt字段直接指定为'userNamePasswordLogin'即使用账号密码登陆
# 其余字段按照下发的内容回报
authPostData = {
    'username': UserName,
    'password': encryptedPass,
    'lt': lt,
    'dllt': 'userNamePasswordLogin',
    'execution': execution,
    '_eventId': eventId,
    'rmShown': rmShown
}

# 发送POST请求进行登陆
authPost = requests.post(url = AuthURL, cookies = cookies, data = authPostData)

# 发出请求会经历两次302跳转
# 第一次302的目标是ListURL（获取打卡列表），同时提供一个ticket参数（应该是用于打卡网站的鉴权），同时下发了几个Cookie（应该是用于统一认证）
# 第二次302的目标也是ListURL（获取打卡列表），同时下发了几个cookie（应该是用于打卡网站）
# 但是我懒得去区分那些是打卡必须的cookie，所以全存下来好了
if len(authPost.history) == 0:
    # 没有跳转，证明统一认证出错了
    print('\033[1;31;43mAuthentication Failed!\033[0m')
    print('\033[1;31;43mFailed to report health status!\033[0m')
    sys.exit()
reportCookie = requests.utils.dict_from_cookiejar(authPost.history[0].cookies)
cookies.update(reportCookie)
reportCookie = requests.utils.dict_from_cookiejar(authPost.history[1].cookies)
cookies.update(reportCookie)
reportCookie = requests.utils.dict_from_cookiejar(authPost.cookies)
cookies.update(reportCookie)

# 从打卡列表中获取今天（第0项）打卡对应的WID参数
WID = json.loads(authPost.text)['data'][0]['WID']

# 打卡信息
reportData = {          # 建议把参数名称装裱成书，永世传唱
    'WID': WID,         # 打卡ID
    'CURR_LOCATION': UserLocation, # 打卡位置
    'IS_TWZC': '1',     # 体温正常
    'IS_HAS_JKQK': '1', # 健康情况正常
    'JRSKMYS': '1',     # 今日苏康码颜色
    'JZRJRSKMYS': '1'   # 居住人今日苏康码颜色
}

# 上报打卡信息
reportPage = requests.get(ReportURL, cookies = cookies, params = reportData)

if reportPage.status_code == 200:
    reportStatus = json.loads(reportPage.text)
    # 打卡服务器的返回信息有：
    # code字段：成功为'0'，失败为一长串16进制
    # msg字段：提示信息
    # data字段：似乎只有成功时有，而且是空的（至少我试的时候是）
    if reportStatus['code'] == '0':
        # 打卡成功
        print('\033[1;30;42mSuccessfully reported health status! ReportServer indicated that: %s\033[0m' % (reportStatus['msg']))
    else:
        # 打卡失败
        print('\033[1;31;43mHealth report failed! ReportServer indicated that: %s\033[0m' % (reportStatus['msg']))
        print('\033[1;31;43mFailed to report health status!\033[0m')
        sys.exit()
else:
    # 如果打卡服务器返回的状态码不是200，则panic
    print('Unexpected response %d from ReportServer. Panic.\033[0m' % (reportPage.status_code))
    print('\033[1;31;43mFailed to report health status!\033[0m')
    sys.exit()
