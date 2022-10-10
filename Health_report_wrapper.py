# -*- coding: UTF-8 -*-

import sys
import json

import requests

EXIT_SUCCESS = 0
AUTH_ERROR = 1
AUTH_FAILED = 2
REPORT_ERROR = 3
REPORT_REJECTED = 4

def HealthReport(UserAuthCookie, UserLocation, UserLastPCR):
    # 如果需要，在这里修改打卡系统的终点URL，这三个URL分别是统一身份认证、获取打卡列表（其实没用上）、上报打卡信息的URL
    AuthURL = 'https://authserver.nju.edu.cn/authserver/login?service=https%3A%2F%2Fehallapp.nju.edu.cn%3A443%2Fxgfw%2Fsys%2Fyqfxmrjkdkappnju%2Fapply%2FgetApplyInfoList.do'
    IndexURL = 'http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.do'
    ListURL = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do'
    ReportURL = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do'

    # 模仿南京大学APP的请求头
    authHeaders = {
    'Accept': 'application/json, text/plain, */*',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 (4420986880)cpdaily/9.0.14  wisedu/9.0.14',
    'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
    'Accept-Encoding': 'gzip, deflate'
    }

    reportHeaders = {
        #'Host': 'ehallapp.nju.edu.cn',
        'Accept': 'application/json, text/plain, */*',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 (4420986880)cpdaily/9.0.14  wisedu/9.0.14',
        "X-Requested-With": "com.wisedu.cpdaily.nju",
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Referer': 'http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.html',
        'Accept-Encoding': 'gzip, deflate'
    }

    # 存储打卡过程中下发的的所有cookie
    cookies = {
        'CASTGC': UserAuthCookie # 统一认证下发的长效令牌
    }

    # 打开统一认证
    #authRequest = requests.get(url = AuthURL, headers = authHeaders, cookies = cookies)
    #authCookie = requests.utils.dict_from_cookiejar(authRequest.cookies)
    #cookies.update(authCookie)

    # 发出请求会经历两次302跳转
    # 第一次302的目标是ListURL（获取打卡列表）
    # 第二次302的目标也是ListURL（获取打卡列表），同时下发了一个短期令牌MOD_AUTH_CAS
    #if len(authRequest.history) == 0:
        # 没有跳转，证明统一认证出错了
        #return AUTH_FAILED, None
    #reportCookie = requests.utils.dict_from_cookiejar(authRequest.history[0].cookies)
    #cookies.update(reportCookie)
    #reportCookie = requests.utils.dict_from_cookiejar(authRequest.history[1].cookies)
    #cookies.update(reportCookie)
    #reportCookie = requests.utils.dict_from_cookiejar(authRequest.cookies)
    #cookies.update(reportCookie)

    # 打开打卡入口
    indexRequest = requests.get(url = IndexURL, headers = reportHeaders, cookies = cookies)

    # 2022-10-10更新
    # 发出请求会经历四次302跳转
    # 前三次302的目标是统一身份认证，并通过长效Cookie获取短期令牌
    # 最后一次302的目标也是ListURL（获取打卡列表），同时下发了一个短期令牌MOD_AUTH_CAS
    if len(indexRequest.history) == 0:
        #没有跳转，证明认证出错了
        return AUTH_FAILED, None
    reportCookie = requests.utils.dict_from_cookiejar(indexRequest.history[3].cookies)
    cookies.update(reportCookie)
    reportCookie = requests.utils.dict_from_cookiejar(indexRequest.history[2].cookies)
    cookies.update(reportCookie)
    reportCookie = requests.utils.dict_from_cookiejar(indexRequest.history[1].cookies)
    cookies.update(reportCookie)    
    reportCookie = requests.utils.dict_from_cookiejar(indexRequest.history[0].cookies)
    cookies.update(reportCookie)
    reportCookie = requests.utils.dict_from_cookiejar(indexRequest.cookies)
    cookies.update(reportCookie)

    # 使用短期令牌请求打卡列表
    listRequest = requests.get(url = ListURL, headers = reportHeaders, cookies = cookies)


    # 从打卡列表中获取今天（第0项）打卡对应的WID参数
    WID = json.loads(listRequest.text)['data'][0]['WID']

    # 打卡信息
    reportData = {          # 建议把参数名称装裱成书，永世传唱
        'WID': WID,         # 打卡ID
        'CURR_LOCATION': UserLocation, # 打卡位置
        'IS_TWZC': '1',     # 体温正常
        'IS_HAS_JKQK': '1', # 健康情况正常
        'JRSKMYS': '1',     # 今日苏康码颜色
        'JZRJRSKMYS': '1',  # 居住人今日苏康码颜色
        # 2022-4-10新增了两个字段
        'SFZJLN': '0',      # 是否最近离宁
        'ZJHSJCSJ': UserLastPCR # 最近核酸检测时间
    }

    # 上报打卡信息
    reportPage = requests.get(ReportURL, headers = reportHeaders, cookies = cookies, params = reportData)

    if reportPage.status_code == 200:
        reportStatus = json.loads(reportPage.text)
        # 打卡服务器的返回信息有：
        # code字段：成功为'0'，失败为一长串16进制
        # msg字段：提示信息
        # data字段：似乎只有成功时有，而且是空的（至少我试的时候是）
        if reportStatus['code'] == '0':
            # 打卡成功
            return EXIT_SUCCESS, reportStatus['msg']
        else:
            # 打卡失败
            return REPORT_REJECTED, reportStatus['msg']
    else:
        # 如果打卡服务器返回的状态码不是200，则panic
        return REPORT_ERROR, reportPage.status_code

if __name__ == '__main__':
    UserAuthCookie = sys.argv[1]
    UserLocation = sys.argv[2]
    UserLastPCR = sys.argv[3]

    ret, msg = HealthReport(
        UserAuthCookie = UserAuthCookie,
        UserLocation = UserLocation,
        UserLastPCR = UserLastPCR
    )

    if ret == EXIT_SUCCESS:
        returnMsg = '健康打卡成功！服务器回报：' + msg
    elif ret == AUTH_ERROR:
        returnMsg = '统一认证服务器连接失败！服务器回报：' + msg
    elif ret == AUTH_FAILED:
        returnMsg = '统一认证登陆失败！请检查凭据'
    elif ret == REPORT_ERROR:
        returnMsg = '打卡服务器连接失败！服务器回报：' + msg
    elif ret == REPORT_REJECTED:
        returnMsg = '打卡失败！服务器回报：' + msg
    else:
        returnMsg = '发生了未知错误！'

    print(returnMsg)
