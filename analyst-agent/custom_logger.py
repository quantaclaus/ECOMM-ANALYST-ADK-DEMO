#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
# from logging import handlers  <-- No longer need this
import secrets
import os 

class LoganLogger:

    def __init__(
        self,
        myloggername,
        myloggerpath,
        mylogfilename,
        ):
        self.extra = {'runtime_id': secrets.token_hex(8)}
        self.myloglevel = logging.DEBUG
        self.mylogformat = '%(asctime)s %(runtime_id)s %(levelname)s => %(message)s'
        # self.maxBytes = 10 * 1024 * 1024  <-- No longer needed
        # self.backupCount = 5 <-- No longer needed

        self.myloggername = myloggername
        self.myloggerpath = myloggerpath
        self.mylogfilename = mylogfilename
        self.mylogfile = self.myloggerpath + '/' + self.mylogfilename
        
        os.makedirs(self.myloggerpath, exist_ok=True)

        # --- THIS IS THE FIX ---
        # 1. We use the simpler 'FileHandler' instead of 'RotatingFileHandler'
        # 2. We set mode='w' (write) to delete the old log on startup.
        self.loghandler = \
            logging.FileHandler(self.mylogfile, mode='w')
        # --- END FIX ---
            
        self.loghandler.setFormatter(logging.Formatter(self.mylogformat))

        self.mylogger = logging.getLogger(self.myloggername)
        self.mylogger.setLevel(self.myloglevel)
        self.mylogger.addHandler(self.loghandler)
        self.mylogger = logging.LoggerAdapter(self.mylogger, self.extra)
        self.debug('loading logger: ' + myloggername + ' logger path: '
                   + myloggerpath + '/' + self.mylogfilename)

    def info(self, msg, *args, **kwargs):
        return self.mylogger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        return self.mylogger.debug(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self.mylogger.error(msg, *args, **kwargs)

    def getMyLogger(self):
        return self.mylogger