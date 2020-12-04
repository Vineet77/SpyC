import argparse
import subprocess
from pathlib import Path
import shutil
import time

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# parse args
parser = argparse.ArgumentParser(
    description="script to speed up build process")

parser.add_argument('-c', action='store', dest='cFile',
                    help='C file to be compiled', type=str)
parser.add_argument('-e', action='store', dest='exportedFuncs',
                    help='Exported functions from the c file', type=str)
parser.add_argument('-f', action='store', dest='htmlFile', help="html file to run analysis on", type=str)

args = parser.parse_args()

# compile c
print(args.cFile)
cFilePath = Path(args.cFile)
outputJsFile = cFilePath.stem + '.js'
emccArgs = ['emcc',  '-o', outputJsFile, args.cFile, '-s', 'EXPORTED_FUNCTIONS=' +
            args.exportedFuncs, '-s', 'EXPORTED_RUNTIME_METHODS=' + '[\"ccall\",\"cwrap\"]']
# emccArgs = ['emcc',  '-o', outputJsFile, args.cFile, '-s', 'EXPORT_ALL=1', '-s', 'EXPORTED_RUNTIME_METHODS=' + '[\"ccall\",\"cwrap\"]']
print(*emccArgs)
compileFile = subprocess.run(emccArgs)

# execute wasabi to
wasmFile = cFilePath.stem + '.wasm'
wasabiArgs = ['wasabi', wasmFile]
print(*wasabiArgs)
wasabi = subprocess.run(['wasabi', wasmFile])

# replace the original wasm file with the instrumented one (generated by wasabi)
# get path to the ./out directory
instrumentedWasmFile = Path('.') / 'out' / (cFilePath.stem + '.wasm')
dstWasmFile = Path('.') / (cFilePath.stem + '.wasm')
shutil.move(src=str(instrumentedWasmFile), dst=str(dstWasmFile.absolute()))

instrumentedJsFile = Path('.') / 'out' / (cFilePath.stem + '.wasabi.js')
dstJsFile = Path('.') / (cFilePath.stem + '.wasabi.js')
shutil.move(src=str(instrumentedJsFile), dst=dstJsFile)

# run a server to serve the HTML file
server_port = '8080'
headless_server = subprocess.Popen(
    ['emrun', '--no_browser', '--port', server_port, '.'], stdout=subprocess.PIPE, stderr=None, stdin=None)


d = DesiredCapabilities.CHROME
# Newer google chrome syntax for loggin
d['goog:loggingPrefs'] = {'browser': 'ALL'}
driver = webdriver.Chrome(desired_capabilities=d)
host = ('http://0.0.0.0:%s/%s' % (server_port, args.htmlFile))
driver.get(host)

# The driver should wait for the page to load, but saw cases
# where it didn't -- add sleep to get full console log
time.sleep(5)
data_out = []
for entry in driver.get_log('browser'):
    print(entry['message'])
    line = str(entry['message'] + '\n')
    data_out.append(line)

print(data_out)

input("Press Enter to continue...")

driver.quit()
headless_server.kill()
