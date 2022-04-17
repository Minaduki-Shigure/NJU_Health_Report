# NJU健康打卡助手
为了解决XX教育的高新技术APP运行速度太快的问题，受大佬启发，因为懒得装webdriver自己瞎写的健康打卡助手。

## 运行环境
* python3
* python modules：requests

## 注意事项
由于2022-4-17学校强制要求统一认证时输入验证码，因此此分支使用Cookie的方式绕过。
Cookie的获取方式：打开F12开发者工具的网络标签页，并登录统一认证，在请求中的响应头找到Set-Cookie，复制其中CASTGC对应的字段即可。

## 使用方法
1. 运行`pip install -r requirements.txt`，自动安装需要的modules（或者自行手动安装）
2. 修改`Health_report.py`中`UserAuthCookie`、`UserLocation`和`UserLastPCR`三个变量为对应值。
3. 运行程序。

## 关于`Health_report_wrapper.py`
这个脚本和上一个的区别就是加了个main函数，从输入参数中获取变量的值，用法：
```plain
$ python Health_report_wrapper.py <UserAuthCookie> <UserLocation> <UserLastPCR>
```
UserLastPCR这个参数由于带有空格，需要使用\转义，比如`2022-4-11 14`应该写成`2022-4-11\ 14`。

之所以包了一层，是因为本身这个项目想做成iOS捷径（我的老SE在打卡界面定位巨慢），如果不用天天改打卡位置的话其实没必要用这个。

## 鸣谢
感谢[@StellarDragon](https://github.com/StellarDragon)大佬提供的灵感：[nju-health-report](https://github.com/StellarDragon/nju-health-report)
