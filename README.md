# uPySync

Synchronization of files local vs. micropython board
Files will be compared using crc32 and updated (host -> board only) if missing or different.

Usage:
sync.py <serial device name>  [file] [file] 

Example:

sync.py COM3 boot.py

On windows, check and update only the file boot.py

