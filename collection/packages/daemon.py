#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys, os, time, atexit
from signal import SIGTERM


class Daemon(object):
    '''
    守护进程类，所谓守护进程故名思意是为了保护进程使进程可以在后台安全运行
    基本思路是使用一个父进程，然后fork一个子进程，保存子进程的pid，最后退出父进程
    再次运行代码时会根据pid文件进行检查，是否有对应进程在运行，没有的话会新启动，有的话不会新启动进程而是直接退出
    这样即使代码在后台运行，又能保证不会无限的启动进程
	
    Usage: 继承本类并重写 run() 方法
	'''

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        # 进行第二次 fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # 写入 pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        启动守护进程
        """
        # 检测 pidfile以确认守护进程是否在运行中
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        self.daemonize()
        self.run()

    def stop(self):
        '''
        停止守护进程
        '''
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        '''
        重启守护进程
        '''
        self.stop()
        self.start()

    def run(self):
        '''
        在子类中重写这个方法，然后使用 start() 或者 restart() 启动守护进程
        '''
        pass
