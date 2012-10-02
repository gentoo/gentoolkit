# -*- coding: utf-8 -*-

import threading
import subprocess


class ProcessRunner(threading.Thread):
    '''
    ProcessRunner is class designed to run arbitrary command
    in background (separate thread). It's replacement for old 
    stuff.call_program function.
    
    When called program is finished, its output can be accessed
    through .stdout and .stderr fields
    '''
    
    def __init__(self, args, autorun=True):
        '''
        @param args - program name and its arguments
        @param autorun - if True, then automatically starts new thread
        ''' 

        threading.Thread.__init__(self)
        self.args = args
        self.lock = threading.Lock()
        self.stdout = ''
        self.stderr = ''
        
        if autorun:
            self.start()
            
        
        
    def run(self):
        self.lock.acquire()
        
        subp = subprocess.Popen(self.args, stdout=subprocess.PIPE, \
                                stderr=subprocess.PIPE)
        self.stdout, self.stderr = subp.communicate()
        self.lock.release()
        
        
    def is_ready(self):
        ''' Checks whether current command is finished '''
        return not self.lock.locked()
    
    
    def wait(self):
        ''' Waits until called program finishes '''
        self.lock.acquire()
        self.lock.release()




class ScanRunner(threading.Thread):
    '''
    ScanRunner is a class for calling scanelf in separate 
    thread, so several instances could be called at a time,
    and then all results could be consolidated.
    
    Consolidated output is available through .out
    '''   
    
    def __init__(self, params, files, max_args, autorun=True):
        '''
        @param params is list of parameters that should be passed into scanelf app.
        @param files list of files to scan.
        @param max_args number of files to process at once
        @param autorun automatically start new thread

        When files count is greater CMD_MAX_ARGS, then scanelf will be called
        several times.
        '''
        
        threading.Thread.__init__(self)
        self.params = params
        self.files = files
        self.max_args = max_args
        
        self.out = []
        self.lock = threading.Lock()
        
        if autorun:
            self.start()
            
            
    def run(self):
        self.lock.acquire()
        
        process_pool = []
        for i in range(0, len(self.files), self.max_args):
            process_pool.append(ProcessRunner(['scanelf'] + self.params + self.files[i:i+self.max_args]))
                
        while process_pool:
            p = process_pool.pop()
            p.wait()
            self.out += p.stdout.strip().split('\n')
            
        self.lock.release()
        
        
    def is_ready(self):
        ''' Checks whether scanning is finished '''
        return not self.lock.locked()
    
    
    def wait(self):
        ''' Waits until all scanning instances are finished '''
        self.lock.acquire()
        self.lock.release()
        
        
        