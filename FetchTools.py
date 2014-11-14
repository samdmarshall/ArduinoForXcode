import os
import urllib2
import gzip
import tarfile
import zipfile
import shutil
import time
import sys
import subprocess
from subprocess import CalledProcessError
import DMGMounter
# Globals
Arduino_zip_address = 'http://arduino.cc/download.php?f=/arduino-1.0.6-macosx.zip';
Arduino_zip_url, Arduino_zip = os.path.split(Arduino_zip_address);

Teensyduino_dmg_address = 'https://www.pjrc.com/teensy/td_120/teensyduino.dmg';
Teensyduino_dmg_url, Teensyduino_dmg = os.path.split(Teensyduino_dmg_address);

CLI_zip_address = 'https://www.pjrc.com/teensy/teensy_loader_cli.2.1.zip';
CLI_zip_url, CLI_zip = os.path.split(CLI_zip_address);
# Helper Functions
def RelativeDir(dir_name):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)),dir_name);
def GetPlatformDir():
    return RelativeDir('Arduino.platform');
def GetTmpDir():
    return RelativeDir('tmp');
def MakeDir(path):
    if os.path.exists(path) == False:
        os.mkdir(path);
def MakeTmpDir():
    MakeDir(GetTmpDir());
def make_subprocess_call(call_args):
    error = 0
    output = ''
    try:
        output = subprocess.check_output(call_args)
        error = 0
    except CalledProcessError as e:
        output = e.output
        error = e.returncode
    
    return (output, error)
def resolve_sdk_path():
    platform_path = '';
    xcrun_result = make_subprocess_call(('xcrun', '--show-sdk-path'));
    if xcrun_result[1] != 0:
        v_log('Please run Xcode first!',0, kVerboseLogLevel);
        sys.exit();
    
    platform_path = xcrun_result[0].rstrip('\n');
    return platform_path;
def CompileCLILoader(path):
    full_path = os.path.join(path, os.listdir(path)[0]);
    os.chdir(full_path);
    sdk_path = resolve_sdk_path();
    xcrun_result = make_subprocess_call(('xcrun', 'cc', '-O2', '-Wall', '-DUSE_APPLE_IOKIT', '-isysroot', sdk_path, '-o', 'teensy_loader_cli', 'teensy_loader_cli.c', '-framework', 'IOKit', '-framework', 'CoreFoundation'));
    if xcrun_result[1] != 0:
        print 'Please run Xcode first!';
        sys.exit();
    
    compiler_output = xcrun_result[0].rstrip('\n');
    if not 'error' in compiler_output:
        return os.path.join(full_path, 'teensy_loader_cli');
    else:
        print compiler_output;
        print 'Compiler error!';
        sys.exit();
def DownloadFile(address, name):
    fd = urllib2.urlopen(address);
    fd_name = os.path.join(GetTmpDir(), name);
    output = open(fd_name,'wb');
    output.write(fd.read());
    output.close();
def DownloadAddressToFile(address,file):
    tmp_path = GetTmpDir();
    try:
        print 'Downloading ' + file + '...'
        DownloadFile(address, file);
        cli_loader_path = os.path.join(tmp_path, file);
        print 'Download Complete!';
    except:
        print 'Could not find file at address!';
def UnzipPathToFile(file):
    path = os.path.join(GetTmpDir(), file);
    extract_path = os.path.join(GetTmpDir(), '.'.join(file.split('.')[:-1]));
    MakeDir(extract_path);
    zip_file = zipfile.ZipFile(path);
    zip_file.extractall(extract_path);
    return extract_path;
def MountDiskImage(file):
    path = os.path.join(GetTmpDir(), file);
    DMGMOUNTER = DMGMounter.DmgMounter();
    MOUNTPOINT = DMGMOUNTER.mount(path);
    return (DMGMOUNTER, MOUNTPOINT);
# Main
def main(argv):
    MakeTmpDir();
    # Downloading necessary tools, check if necessary
    DownloadAddressToFile(Arduino_zip_address, Arduino_zip);
    DownloadAddressToFile(Teensyduino_dmg_address, Teensyduino_dmg);
    DownloadAddressToFile(CLI_zip_address, CLI_zip);
    
    # Unpacking tools
    arduino_extracted_path = UnzipPathToFile(Arduino_zip);
    teensyduino_mount_info = MountDiskImage(Teensyduino_dmg);
    cli_extracted_path = UnzipPathToFile(CLI_zip);
    
    # copy arduino-xcode.app to /Applications
    shutil.copytree(os.path.join(arduino_extracted_path,'Arduino.app'),'/Applications/Arduino-Xcode.app');
    
    # copy teensyduino.app
    tmp_teensyduino = os.path.join(GetTmpDir(), 'teensyduino.app');
    shutil.copytree(os.path.join(teensyduino_mount_info[1], 'teensyduino.app'), tmp_teensyduino);
    
    # unmount teensyduino.dmg
    teensyduino_mount_info[0].unmount(os.path.join(GetTmpDir(), Teensyduino_dmg));
    
    # run teensyduino installer
    run_teensyduino_installer = make_subprocess_call(('open', tmp_teensyduino));
    
    # Compile loader
    loader_path = CompileCLILoader(cli_extracted_path);
    
    # wait until complete
    print 'The Arduino IDE has been copied to the /Applications folder and is named \"Arduino-Xcode.app\", tell Teensyduino to install to this copy of the Arduino application. The Teensyduino installer is proprietary and must be done manually before the tools can be extracted to the Arduino platform bundle.\n';
    raw_input('Please wait until teensyduino has finished installing, then press any key to continue...');
    
    # copy tools
    
    
    # remove arduino-xcode.app from /Applications
    shutil.rmtree('/Applications/Arduino-Xcode.app');
    
    # clean up ./tmp
    shutil.rmtree(tmp_teensyduino);
    shutil.rmtree(arduino_extracted_path);
    shutil.rmtree(cli_extracted_path);

if __name__ == "__main__":
    main(sys.argv[1:]);