#!/usr/bin/env python3
import sys
import argparse
import serial
import os
import time
import binascii

local_dir = '.'
target_dir = '/'
list_commands = ''


def initialize_commands():
    global list_commands
    list_commands = f'''
import os
import binascii
files=os.listdir("{target_dir}")
for f in files:
v = binascii.crc32(open(f,"rb").read())
print("FILE,"+f+","+str(v))
'''


class Synchronizer:
    def __init__(self, port):
        self.remote_files = {}
        self.local_files = {}
        self.ser = serial.Serial(port, baudrate=115200)
        self.reboot()

    def read_all(self):
        n = self.ser.in_waiting
        if n == 0:
            return None
        return self.ser.read(n)

    def read_all_str(self):
        data = self.read_all()
        if data:
            data = data.decode('utf-8')
        return data

    def send(self, s):
        # print(f'Sending: "{s}"')
        self.ser.write(bytes(s + '\r\n', 'utf-8'))

    def flush(self):
        self.ser.write(bytes('\r\n\r\n\r\n\r\n\r\n', 'utf-8'))

    def send_lines(self, lines):
        for line in lines.split('\n'):
            self.send(line.strip())
        self.flush()

    def reboot(self):
        # Soft reboot
        self.ser.write(b'\x04')
        time.sleep(1)
        self.read_all_str()

    def delayed_read_response(self):
        time.sleep(1)
        return self.read_all_str()

    def parse_remote_files(self, response):
        for line in response.split('\n'):
            try:
                line = line.strip()
                if line.startswith('FILE,'):
                    parts = line.split(',')
                    filename = parts[1]
                    crc = int(parts[2])
                    self.remote_files[filename] = crc
            except ValueError:
                pass

    def scan_local_files(self, files):
        for f in files:
            crc = binascii.crc32(open(os.path.join(local_dir, f), "rb").read())
            self.local_files[f] = crc

    def send_file(self, filename):
        try:
            print(f"Sending file: {filename}")
            data = open(os.path.join(local_dir, filename), 'rb').read()
            encoded = binascii.hexlify(data).decode('utf-8')
            self.send(f'with open("{target_dir}{filename}","wb") as f:')
            self.send(f'data=binascii.unhexlify("{encoded}")')
            self.send(f'f.write(data)')
            self.flush()
            self.delayed_read_response()
        except OSError:
            pass

    def sync_files(self, files):
        if len(files) == 0:
            files = os.listdir(local_dir)
        self.send_lines(list_commands)
        self.parse_remote_files(self.delayed_read_response())
        self.scan_local_files(files)
        for filename in self.local_files:
            update = False
            if filename in self.remote_files:
                if self.local_files.get(filename) != self.remote_files.get(filename):
                    update = True
            else:
                update = True
            if update:
                self.send_file(filename)
            else:
                print(f'{filename} is up to date')

    def close(self):
        self.ser.close()


def main():
    parser = argparse.ArgumentParser(description='Synchronize micropython files')
    parser.add_argument('-p', metavar='Port', type=str, required=True,
                        help='Serial port of board (e.g. COM3 or /dev/ttyUSB0)')
    parser.add_argument('-t', metavar='Target', type=str, required=False, help='Target directory, default /')
    parser.add_argument('files', metavar='File', type=str, nargs='*', help='Files to syncronize.  Default all files')
    args = parser.parse_args()
    if args.t is not None:
        global target_dir
        target_dir = args.t
        if not target_dir.endswith('/'):
            target_dir = target_dir + '/'
    initialize_commands()
    s = Synchronizer(args.p)
    s.sync_files(args.files)
    s.close()


if __name__ == '__main__':
    main()
