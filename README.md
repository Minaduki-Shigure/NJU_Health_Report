# NJU健康打卡助手
受大佬启发，因为懒得装webdriver自己瞎写的健康打卡助手。

## 运行环境
* python3
* python modules：requests、Js2Py、beautifulsoup4、lxml（lxml可换成其他包，具体代码中有指出）

## 使用方法
1. 运行`pip install -r requirements.txt`，自动安装需要的modules（或者自行手动安装）
2. 修改`Health_report.py`中`UserName`、`UserPass`和`UserLocation`三个变量为对应值。
3. 运行程序。

## 关于`Health_report_wrapper.py`
这个脚本和上一个的区别就是加了个main函数，从输入参数中获取变量的值，用法：
```plain
$ python Health_report_wrapper.py <UserName> <UserPass> <UserLocation>
```
之所以包了一层，是因为本身这个项目想做成iOS捷径（我的老SE在打卡界面定位巨慢），如果不用天天改打卡位置的话其实没必要用这个。

## 注意事项
如果密码错误，统一认证可能会要求输入验证码，这个程序不能处理验证码，所以千万别输错。   
如果输错了导致需要验证码，可以手动打开浏览器登陆一下统一认证，一般可以解决。

## 鸣谢
感谢[@StellarDragon](https://github.com/StellarDragon)大佬提供的灵感：[nju-health-report](https://github.com/StellarDragon/nju-health-report)