#!/usr/local/bin/python2.7

import datetime
import os
import sys
import time

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from subprocess import call,PIPE,Popen

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Konrad Biegaj & Vineet Patel 
# CS568 | Fall 2020

# Automate converting C libaries into WebAssemably files
# After converted, deploy wasabi to generate an analysis without the 
# need for the manual steps.
# export WASABI_PATH=<path_to_wasabi>

class SpyC(object):

    def __init__(self, c_library=None, server_port=None):
        self.c_library      = c_library
        self.server_port    = server_port

    '''
    #Use emscripten to compile native to WebAssembly
    # emscripten produces asm.js by default, so use WASM=1 flag
    # note that this generates 3 files: 
    # - hello.wasm: actual binary
    # - hello.js: glue code for compiling and running WebAssembly in the browser, uses fetch() to get hello.wasm
    # - hello.html: website that emulates a console, includes hello.js
    '''
    def verifyCFile(self):
        if os.path.isfile(self.c_library):
            print('INFO: Checking for C file: %s' % self.c_library)
        else:
            pwd = os.getcwd()
            print('FATAL: Could not locate file: %s/%s' % (pwd, self.c_library))
            #sys.exit(1)

    def compileWasm(self):
        try:
            html = (self.c_library.split('.c')[0] + '.html')
            call(['emcc',self.c_library,'-s','WASM=1','-o',html])
            emcc = Popen(['emcc',self.c_library,'-s','WASM=1','-o',html], stdout=PIPE, stderr=PIPE)
            emcc.communicate()
            print emcc.stderr
            #sys.exit(0)
            print('INFO: WASM created: %s' % self.c_library)       
        except Exception as e:
           print('FATAL: Exception during WASM compile: %s')
           print(e)

    # Deploy wasabi against the .wasm and set var names
    def buildWasabi(self):
        pass
        try:
            html = (self.c_library.split('.c')[0] + '.html')
            self.html = html

            wasm   = (self.c_library.split('.c')[0] + '.wasm')
            self.waml = wasm

            wasabi = Popen(['wasabi',wasm], stdout=PIPE, stderr=PIPE)
            wasabi.communicate()
            print('INFO: Wasabi build complete: %s' % self.c_library)
        except Exception as e:
            print('FATAL: Exception during wasabi-wasm build: %s' % self.c_library)
            print(e)

        #Replace original binary with instrumented one and copy generated JavaScript
        pwd = os.getcwd()
        wasabi_name = (self.c_library.split('.c')[0] + '.wasabi.js')
        new_wasm = ('./out/%s' % wasm)
        new_wasabi_js = ('./out/%s' % wasabi_name)
        call(['cp', new_wasabi_js, '.'])
        call(['cp', new_wasm,'.']) 
        #cp_out = Popen(['cp',new_wasm,'.'], stdout=PIPE, stderr=PIPE)
        #cp_out.communicate()

        #OSX sed will throw an error, install gsed
        js_name = (self.c_library.split('.c')[0] + '.js')
        wasabi_name = (self.c_library.split('.c')[0] + '.wasabi.js')
        inject = ('/<script async type="text\/javascript" src="%s"><\/script>/a <script src="%s"></script>' % (js_name, wasabi_name))
        #add_code = Popen(['gsed','-i',inject, html], stdout=PIPE, stderr=PIPE)
        #add_code.communicate()
        call(['gsed','-i', inject, html])

        #Use example analysis that just logs all instructions with their inputs and results
        wasabi_path = os.environ['WASABI_PATH']
        wasabi_path = wasabi_path + '/analyses/heap-analysis.js'
        cp_js = Popen(['cp',wasabi_path,'.'], stdout=PIPE, stderr=PIPE)
        cp_js.communicate()

        #Add log-all.js into html
        inject = ('/<script src="%s"><\/script>/a <script src="heap-analysis.js"></script>' % (wasabi_name))
        #add_code = Popen(['gsed','-i',inject, html], stdout=PIPE, stderr=PIPE)
        #add_code.communicate()
        call(['gsed','-i', inject, html])

    def startServer(self):
        #python3 -m http.server 7800
        #python -m SimpleHTTPServer
        #call(['emrun','--no_browser','--port','8080','.'])
        headless_host = Popen(['emrun','--no_browser','--port','8080','.'], stdout=None, stderr=None, stdin=None)
        #emrun --no_browser --port 8080 .
        return headless_host
  
    def logJsConsole(self):
        d = DesiredCapabilities.CHROME
        #Newer google chrome syntax for loggin
        d['goog:loggingPrefs'] = { 'browser':'ALL' }
        driver = webdriver.Chrome(desired_capabilities=d)
        host = ('http://0.0.0.0:%s/%s' % (self.server_port, self.html))
        driver.get(host)

        #The driver should wait for the page to load, but saw cases 
        #where it didn't -- add sleep to get full console log
        time.sleep(10)
        data_out = []
        for entry in driver.get_log('browser'):
            print(entry['message'])
            line = str(entry['message'] + '\n')
            data_out.append(line)
        return data_out

    #TODO - Clean this up
    def getFFJSLog(self):
        d = DesiredCapabilities.FIREFOX
        d['loggingPrefs'] = { 'browser':'ALL' }
        fp = webdriver.FirefoxProfile()
        driver = webdriver.Firefox(capabilities=d,firefox_profile=fp)
        driver.get('http://0.0.0.0:%s/%s' % (self.server_port, self.html))
        pass
    
    #Write out from wasabi analysis
    def writeJson(self, out_data):
        print out_data
        #Verify output 
        if not os.path.exists('spyc_out'):
            os.makedirs('spyc_out') 
       
        timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
        analysis  = ('%s_%s_analysis.json' % (timestamp, self.c_library))
        with open('spyc_out/' +  analysis, mode='w') as outfile:
            outfile.writelines(out_data)
            #for entry in out_data:
            #    outfile.write(entry)


class BaseCommandAble(object):

    def setup(self):
        self.buildParser()
        self.buildOptions()
        self.buildExtraOptions()
        self.parseOptions()

        self.spyC_wasabi = SpyC(c_library=self.args.c_library, server_port=self.args.server_port,
       )

    def buildParser(self):
        self.parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    def parseOptions(self):
        self.args = self.parser.parse_args()
        #Get values from environment based on names stored in default arguments
        for option in [x for x in dir(self.args) if not x.startswith('_')]:
            env_name = getattr(self.args, option)
            if type(env_name) == str and env_name.startswith('SPYC_'):
                value = os.environ.get(env_name)
                if value is not None:
                    setattr(self.args, option, value)
                else:
                    self.parser.error("No sane value from env variable %s for '%s'" % (env_name, option))

    def buildOptions(self):
        group = self.parser.add_argument_group("SpyC Wasasbi Options",
                  "Environment variables are used by default, I.E., $SPYC_C_LIBRARY")
        group.add_argument("--c_library", dest="c_library", default='SPYC_C_LIBRARY', 
            help="C/C++ library for converstion and anaylsis")
        group.add_argument("--server_port", dest="server_port", default='SPYC_C_SERVER_PORT',
            help="The target port to host the WebAssembly html")

    def buildExtraOptions(self):
        pass

#TODO add directory walker for multiple C files
if __name__ == '__main__':
    #Build Options
    cli = BaseCommandAble()
    cli.setup()
     
    #Move to target c directory

    #Setup SpyC
    spyc = cli.spyC_wasabi
    
    spyc.verifyCFile()
    spyc.compileWasm()
    spyc.buildWasabi()

    #Host
    local_host = spyc.startServer()

    #ParseLog
    chrome_js_log = spyc.logJsConsole()
    local_host.terminate()

    #Write results
    spyc.writeJson(chrome_js_log)
