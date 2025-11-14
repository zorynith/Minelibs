#!/usr/bin/env python3
import hmac
import hashlib
import struct
import sys
import time
import base64

def hotp(key, counter, digits=6):
    """HMAC-Based One-Time Password"""
    key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
    counter = struct.pack('>Q', counter)
    mac = hmac.new(key, counter, hashlib.sha1).digest()
    offset = mac[-1] & 0x0f
    binary = struct.unpack('>L', mac[offset:offset+4])[0] & 0x7fffffff
    return str(binary % (10 ** digits)).zfill(digits)

def totp(key, time_step=30):
    """Time-Based One-Time Password"""
    counter = int(time.time() // time_step)
    return hotp(key, counter)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python3 one-time.py <base32密钥>")
        sys.exit(1)
    
    secret = sys.argv[1]
    print(totp(secret))
