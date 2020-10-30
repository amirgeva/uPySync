# uPySync

Synchronization of files local vs. micropython board
Files will be compared using crc32 and updated (host -> board only) if missing or different.

Usage:
sync.py <serial device name>  [file] [file] 

_Example:_

sync.py COM3 boot.py

On windows, assuming board is on COM3, check and update only the file boot.py

_Example:_

sync.py /dev/ttyUSB0

On linux, assuming board is on /dev/ttyUSB0, check and update all files in current directory