#!/usr/local/bin/python2.7

import os
import sys

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from subprocess import PIPE,Popen

# Konrad Biegaj & 
# CS568 | Fall 2020

# Automate converting C libaries into WebAssemably files
# After converted, deploy wasabi to generate an analysis without the 
# need for the manual steps.
# export WASABI_PATH=<path_to_wasabi>

class SpyC(object):

    def __init__(self, c_library=None, server_port=None):
        self.c_library = c_library
        self.server    = server_port

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
            print('FATAL: Could not locate file: %s' % self.c_library)
            sys.exit(1)

    def compileWasm(self):
        try:
            html = (self.c_library.split('.c')[0] + '.html')
            emcc = Popen(['emcc',self.c_library,'-s','WASM=1','-o',html], stdout=PIPE, stderr=PIPE)
            emcc.communicate()
            print('INFO: WASM created: %s' % self.c_library)       
        except Exception as e:
           print('FATAL: Exception during WASM compile: %s')
           print(e)

    #
    def buildWasabi(self):
        pass
        try:
            html = (self.c_library.split('.c')[0] + 'html')
            wasm   = (self.c_library.split('.c')[0] + 'wasm')
            wasabi = Popen(['wasabi',wasm], stdout=PIPE, stderr=PIPE)
            wasabi.communicate()
            print('INFO: Wasabi build complete: %s' % self.c_library)
        except Exception as e:
            print('FATAL: Exception during wasabi-wasm build: %s' % self.c_library)
            print(e)

        #Replace original binary with instrumented one and copy generated JavaScript 
        cp_out = Popen(['cp','out/*','.'], stdout=PIPE, stderr=PIPE)
        cp_out.communicate()

        #OSX sed will throw an error, install gsed
        js_name = (self.c_library.split('.c')[0] + 'js')
        wasabi_name = (self.c_library.split('.c')[0] + 'wasabi.js')
        inject = ('/<script async type="text\/javascript" src="%s"><\/script>/a <script src="%s"></script> %s' % (js_name, wasabi_name, html))
        add_code = Popen(['gsed','-i',inject], stdout=PIPE, stderr=PIPE)
        add_code.communicate()

        #Use example analysis that just logs all instructions with their inputs and results
        wasabi_path = os.environ['WASABI_PATH']
        wasabi_path = wasabi_path + '/analyses/log-all.js'
        cp_js = Popen(['cp',wasabi_path,'.'], stdout=PIPE, stderr=PIPE)
        cp_js.communicate()
        #cp /path/to/wasabi/analyses/log-all.js .

        #Add log-all.js into html
        inject = ('/<script src="%s"><\/script>/a <script src="log-all.js"></script> %s' % (wasabi_name, html))
        add_code = Popen(['gsed','-i',inject], stdout=PIPE, stderr=PIPE)
        add_code.communicate()

    def startServer(self, server):
        #python3 -m http.server 7800
        #python -m SimpleHTTPServer
        #emrun --no_browser --port 8080 .
        #firefox http://localhost:8080/hello.html
        pass

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
            if type(env_name) in (str, unicode) and env_name.startswith('SPYC_'):
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

#TODO add direcotry walker for multiple C files
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
