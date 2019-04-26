# spider

## Python程序

### 全国彩

    # 双色球开奖更新,每周二、四、日21:13启动  21-22时每间隔5分钟执行一次,在定时内当不符合更新规则(间隔时间)则exit退出程序
    13-59/5 21-22 * * 2,4,7 python3 /usr/local/spider/collection/put_queue.py -s 8 -i 0
    
    # 福彩3D开奖更新，21:13启动  21-22时每间隔5分钟执行一次,在定时内当不符合更新规则(间隔时间)则exit退出程序
    13-59/5 21-22 * * * python3 /usr/local/spider/collection/put_queue.py -s 11 -i 0
    
    # 七乐彩开奖更新，每周一、周三、周五 21:13启动 21-22时每间隔5分钟执行一次,在定时内当不符合更新规则(间隔时间)则exit退出程序
    13-59/5 21-22 * * 1,3,5 python3 /usr/local/spider/collection/put_queue.py -s 12 -i 0
    
    # 大乐透开奖更新，每周一、周三、周六20:28启动 20-21时每间隔5分钟执行一次,在定时内当不符合更新规则(间隔时间)则exit退出程序
    28-59/5 20-21 * * 1,3,5 python3 /usr/local/spider/collection/put_queue.py -s 1 -i 0
    
    # 排列3开奖更新，每天20:28启动  20-21时每间隔5分钟执行一次,在定时内当不符合更新规则(间隔时间)则exit退出程序
    28-59/5 20-21 * * * python3 /usr/local/spider/collection/put_queue.py -s 4 -i 0
    
    # 排列5开奖更新，每天20:28启动  20-21时每间隔5分钟执行一次,在定时内当不符合更新规则(间隔时间)则exit退出程序
    28-59/5 20-21 * * * python3 /usr/local/spider/collection/put_queue.py -s 13 -i 0
    
    # 七星彩开奖更新，每周二、五、日20:28启动  20-21时每间隔5分钟执行一次,在定时内不符合更新规则(间隔时间)则exit退出程序
    28-59/5 20-21 * * 2,5,7 python3 /usr/local/spider/collection/put_queue.py -s 14 -i 0

### 高频彩/地方彩

    #提交更新  
    高频彩60秒提交一次更新队列,不符合更新要求的数据将被忽略
    python3 /usr/local/spider/collection/put_queue.py -L 2 -i 60
    低频彩60分钟提交一次更新队列,不符合更新要求的数据将被忽略
    python3 /usr/local/spider/collection/put_queue.py -L 3 -i 60
    
    #启动更新   全部彩种进行更新,间隔时间20秒,定时提交的队列为空时将忽略
    python3 /usr/local/spider/collection/update.py -o 1 -i 20
    
    #提交入库  由待提交队列获取数据,去重后进行提交入库,每2秒监听一次待提交队列
    python3 /usr/local/spider/collection/publish.py -i 2



