#!/usr/bin/env python3
"""GR4-LUTSmith: put the look of a .cube LUT into your RICOH GR IV (firmware 1.11).

Fits the LUT to the camera's own look processing (a colour matrix, tone
curves, per-hue colour sectors and, with --after-curves, a colour mix after
the curves) and writes a firmware file that carries the result as an extra
Image Control look. With --turns, several fits from different starting points
are run and the good ones kept. Starts from the official RICOH firmware file
you downloaded yourself. A file is written only if every check passes.

Usage
  python3 gr4_lutsmith.py make     LUT.cube OFFICIAL_fwdc248b.bin [--space srgb|adobe] [--slot SLOT] [--photo DNG] [--no-hue] [--after-curves] [--turns N] [--seed S] [-o DIR]
  python3 gr4_lutsmith.py fit      LUT.cube [--space srgb|adobe] [--slot SLOT] [--photo DNG] [--no-hue] [--after-curves] [--turns N] [--seed S] [-o DIR]   (no firmware needed)
  python3 gr4_lutsmith.py build    DIR/look.json [DIR2/look.json ...] OFFICIAL_fwdc248b.bin [-o DIR]
                                   (one look per slot: high-contrast, cinema-yellow, cinema-green)
  python3 gr4_lutsmith.py preview  DIR/look.json PHOTO.DNG [-o sheet.jpg]   (needs rawpy, pillow)
  python3 gr4_lutsmith.py slots                                   (the looks yours can replace)
  python3 gr4_lutsmith.py check    ANY_fwdc248b.bin
  python3 gr4_lutsmith.py selftest OFFICIAL_fwdc248b.bin

Python 3.8 or newer with numpy. --photo and preview also need rawpy and pillow.
"""
import argparse
import base64
import hashlib
import json
import math
import struct
import sys
import zlib
from pathlib import Path

VERSION = '1.4.0'

OFFICIAL_SHA256 = 'a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f'
OFFICIAL_BYTES = 38648776

OTHER_KNOWN = {
    '4c04b48c65897f2edd028df0f5e04666ca241488c81502bae0f34e040ee454eb': 'GR4-MonoUnlock 1.0.0 (monochrome looks unlocked)',
}

# Built-in example: examples/film-1d.look.json must build to exactly this image (selftest).
SELFTEST_LOOK = 'examples/film-1d.look.json'
SELFTEST_SHA256 = 'd201add28bc3ab738bc92fcfdaafa3847bc881bfd7eecb6b7e8f331d1289f052'

HEADER, MAGIC, FOOTER_MAGIC = 128, b'RICOH\0\0\0', b'\xa5\x5a\x5a\xa5'
MAX_DISTANCE = 0x2000
LITERAL_CHUNK = 0x6000


class Refused(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def word_sum(data):
    if len(data) % 4:
        raise Refused('data is not 4-byte aligned')
    return sum(w for (w,) in struct.iter_unpack('<I', data)) & 0xffffffff


def decode(data, limit=256 * 1024 * 1024):
    if len(data) < 160 or data[:8] != MAGIC:
        raise Refused('not a RICOH firmware container')
    out = bytearray()
    frames = []
    cursor = HEADER
    while True:
        start = cursor
        if cursor + 2 > len(data):
            raise Refused('container: missing frame terminator')
        descriptor = int.from_bytes(data[cursor:cursor + 2], 'big')
        cursor += 2
        if descriptor == 0:
            return bytes(out), frames, cursor
        size = descriptor & 0x7fff
        end = cursor + size
        if not size or end > len(data):
            raise Refused(f'container: invalid frame at {start:#x}')
        output_start = len(out)
        if descriptor & 0x8000:
            out += data[cursor:end]
            cursor = end
        else:
            while cursor < end:
                if cursor + 2 > end:
                    raise Refused(f'container: truncated flags at {cursor:#x}')
                flags = int.from_bytes(data[cursor:cursor + 2], 'big')
                cursor += 2
                for bit in range(15, -1, -1):
                    if cursor == end:
                        break
                    if not flags & (1 << bit):
                        out.append(data[cursor])
                        cursor += 1
                        continue
                    if cursor + 2 > end:
                        raise Refused('container: truncated reference')
                    a, b = data[cursor], data[cursor + 1]
                    cursor += 2
                    distance = ((a >> 3) << 8) | b
                    length = a & 7
                    if length == 7:
                        while True:
                            if cursor >= end:
                                raise Refused('container: truncated length')
                            extension = data[cursor]
                            cursor += 1
                            length += extension
                            if extension != 255:
                                break
                    if distance == 0:
                        break
                    if distance > len(out):
                        raise Refused('container: reference before start of output')
                    count = length + 3
                    if distance >= count:
                        out += out[-distance:len(out) - distance + count]
                    else:
                        pattern = bytes(out[-distance:])
                        out += (pattern * ((count + distance - 1) // distance))[:count]
                if len(out) > limit:
                    raise Refused('container: decoded size limit exceeded')
        frames.append((start, end, output_start, len(out)))


def check_container(data, payload=None, consumed=None):
    if payload is None:
        payload, _, consumed = decode(data)
    if data[-20:-16] != FOOTER_MAGIC:
        raise Refused('container: footer magic missing')
    enc, dec = struct.unpack_from('<II', data, len(data) - 12)
    if enc != consumed - HEADER or dec != len(payload):
        raise Refused('container: size fields do not match the content')
    if word_sum(data) or word_sum(payload):
        raise Refused('container: checksum mismatch')
    return payload


def sections(payload):
    out, pos = [], 0
    while pos + 16 <= len(payload):
        tag = payload[pos:pos + 8].rstrip(b'\0')
        if not tag or not tag.isalnum() or not tag.isupper():
            break
        size = struct.unpack_from('<I', payload, pos + 12)[0]
        if pos + 16 + size > len(payload):
            break
        out.append((tag.decode(), pos + 16, pos + 16 + size))
        pos += 16 + size
    return out


def differences(a, b, block=1 << 16):
    if len(a) != len(b):
        raise Refused('length mismatch')
    out = []
    for pos in range(0, len(a), block):
        x, y = a[pos:pos + block], b[pos:pos + block]
        if x != y:
            out += [pos + i for i in range(len(x)) if x[i] != y[i]]
    return out


def rezero(payload):
    buf = bytearray(payload)
    last = struct.unpack_from('<I', buf, len(buf) - 4)[0]
    struct.pack_into('<I', buf, len(buf) - 4, (last - word_sum(buf)) & 0xffffffff)
    return bytes(buf)


def literal_frames(data):
    out = bytearray()
    for pos in range(0, len(data), LITERAL_CHUNK):
        chunk = data[pos:pos + LITERAL_CHUNK]
        out += struct.pack('>H', 0x8000 | len(chunk)) + chunk
    return bytes(out)


def rebuild(source, frames, consumed, patched, changed):
    body = bytearray()
    reemitted = 0
    for (c0, c1, d0, d1) in frames:
        if any(d0 <= c < d1 or c < d0 < c + MAX_DISTANCE for c in changed):
            body += literal_frames(patched[d0:d1])
            reemitted += 1
        else:
            body += source[c0:c1]
    body += b'\0\0'
    trailer = bytearray(source[consumed:])
    struct.pack_into('<II', trailer, len(trailer) - 12, len(body), len(patched))
    struct.pack_into('<I', trailer, len(trailer) - 4, 0)
    padding = bytes((-HEADER - len(body) - len(trailer)) % 4)
    out = bytearray(source[:HEADER] + body + padding + trailer)
    struct.pack_into('<I', out, len(out) - 4, (-word_sum(out)) & 0xffffffff)
    return bytes(out), reemitted


# ------------------------------------------------------------------ firmware data
# Fixed changes (make the extra look slot available, colour processing and default
# slider settings for it) and where the look itself goes. Exported from the
# builds that were tested on a GR IV 1.11.
_DATA = '''
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
'''
DATA = json.loads(zlib.decompress(base64.b64decode(''.join(_DATA.split()))))
LOOK = DATA['look']

# Hue sectors: the changes that turn them on and the place that takes the look's hue-sector matrices (both
# with their original bytes, which are checked).
_HUE = '''
eNrt0TtOxDAQgOG7uE4xfttcZZUicRJpCxqgQELcHe8kGGYEKy14u/FXOIks28r/prbz67qoh9PJQArRxDCoDFMA550alEk5Q66P
47AvcNpcX+Bd+nWBjh5sAhgUmNvUjeKxZy5zuszu2Di7+q6912n/7kvZ8Ox2oDW3H/jDBcJx4F9nNY6Depxens5lfa5/fL9ccPVy
E8pNYiITGM84xoqrZjQ1mendQ1AFzc3E9O4hqAWVZmZ69xDUipamML17CGpDa7MwvXsIQsPFUYGWuE8PQeh9wKdvJe7TQxDaoK8B
VPcegtAWmYaP3j0EoR2yjWF69xCE9sg1lvlnDzW+fwAfTUfe
'''
HUE = json.loads(zlib.decompress(base64.b64decode(''.join(_HUE.split()))))

# Colour after the curves: the changes that turn it on, the place that takes the look's matrices (both with
# their original bytes, which are checked), and the camera's own values for each Hue step.
_POST = '''
eNrtk7tuwzAMRf9FMw1c0RRN91cCD64faIYufQAFivx7JctJIAHJlKJLfYZLmhR4IZvfbj1+LbN7OhwYpoE9k1PojBDEkZtt9OhjOFBu
aMXuN4jJzQbfBSg4NmB5LGnQlAcBIydlySqWVaes/V5/3uvzXl/3OmNss+GB3Ov48Xaclvd4Qdm8/oL5v8brRrggFW0FV9QPSrD+cw/f
beiFUHHje8SVci+fS1peSz+mFxiZZ4urloQ8gl5fKKiDUAq2vGdqA1MKzjmKrCnK8XhTnI8DmmJC8tBcTQynH7SJIAU=
'''
POST = json.loads(zlib.decompress(base64.b64decode(''.join(_POST.split()))))

# Other slots for a personal look: the changes for each slot and the room for the looks' data, all with their
# original bytes, which are checked.
_SLOTS = '''
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
zO4wfxd4/tKKKWA/FGxPUMwVtFeF54O+BtoAPhU+8G+YVUyP03SYKvpMMAC6ueG9b7gv6gAwu82A94WeZKDvmAneFEwt8IagBmFEQoHW
jBsrCmwD1AYwxMFucBHsMpjHYThBV8HmBLsAJmPsOgEmd9CKMIuDXQAWGwxKe80bNANoA3jgCJoh4uyYQAu024LZCWYHWJWgGfKwuCJm
S5y2gBFQZiclVMEuqb1Y0GugAcAuAA0Al9qGT4MmS4FPh74PWuAGu+KG4Xf3CI8L074HzZCKhenCDniX4aKdYNtMmKRmh29oTZoCIqjg
Cr9vULf44tDfbBxgO0xnofvZCb9hyLgLhnKGIQcj1IF9gHobmtrBxAna43YeNAZMZs7D6PS4P+Ii2RMwQMDXBDuj3C40sDFu+L8J/4ZW
onUSmEKgvzj0mK4CehVG/AVq4BrZ4T5SxJJAW8G0CdUPv2uE6R2swYFv5HHWBdsE3Dd4tlRvl0D7JLAbErrAaPbAs+VaHq0ENhI0BWgm
0I0ZPqB6CjwLmDxgswRXM2ipBhoKTD+4AzQ16J0SXOvwDb21434YGLGP7VIf2yWjEoWZHZ5lQLkDngFsTjcC2C2gdCbYVRM3DECrQC+H
jhBAI0GHAd0K9QkXNXhp82ghaJGQqw8zgibyoHVA+8DkHZslEyaB1gCLGDTM9BnslAx2DtiRMOeDVrnB1oD7NNB2LWTf+0XNAV6Mv8nr
+fNfB26Jfqnt58G+j0fXBeZ2j05OzI+zA0bx8z2fb7QL8HugaoE/bsnHPdd/PHK3vuOSw/z/lFOfb5hin3Ku5zK7yh/j+TdU0CPvj98F
NsFTTlnlXM83Vgmdl1Y56z6rmJmWHGwRt85/ylnXr38au957lFXOuh88GP3xqxzQHFQO2A1POfx+6/y7PfJRVznreaEDPH+u9RzXqh9+
n+VdXuv5QTv5p7znsrs/3yat572fR8fJi8pZ1/v1XNc6D2yrp5zVPvc4y7nbeu+6nquvclY7XdL+z3nmuZ6/wYZ62rOuepb3e8pZ8rDK
tdyuq165H3E53P/y8re533E9h3XeHVc9h1XO6kdm3ResLb/ameqpcLuvfsLt3FY/jKvcye+13h+eKzztt55rtXNYz83tnNb9VjG735jV
vn3J69j9aNXvKme1r1/tcal+w+Vk7jfrvJS536xy1rdZ/eLyqxyu57zHzzNOVz+Lq57jqhceP321J7ffDGc5Zo0LmDmpnjL353w+T6vn
e3H9Gxl/YY13bv81vlc564HSqj8ex1z/XM7N9VxU/czzvcLqhzyOuf65nBJ2vzjrZ43H3b6rv4Z86kEu51r3ces7rnGXIuvLVc9Lz7Ee
4Ofc9bP6KVpc1A7reft6/5H5BZ/zbD3r2a5xAXd5rl/vtcsZZ39uXE4+69mueu9rPLCe5nJu7s/tbC+bznq26z2z2/X7lMN6Kpz9x3M5
11nP1m79+dRzV+Wks/9A/dCd+T34v+2uaJ6XVj9c/T6r9rh5/LRzXovrvqE89VxZn61xWKLqZ3mPw2Ne4/5hlv6K67zE8+dQ/WyNLxfP
eTvxOF76wK3z0qr/GlQ/u3d/ffQlv//qR6md8zLPX7Wd5Yylv3nR1K/2L6u/+1Uv/Fx11WNZA5Xro7nzve7C42VNp23pnTVeWW2XJefr
Ujrfi+fVzu2/9HxY9VzWdXU974v6eMpZ9cvz6e25vEdu+jlf1HLaS9zPLOufNe/cq93zaqd7VSHrw7bO4+v6mgftaieeT7mewqoXu0wd
7s9R6dW+9GVY7em5f6xxj94e3W+e/TmOU6+yvcH92K0eUXn48Tw6zv6c9gBjM2mVw2prPXdb/aOs5wj32Z+zPfUz2xvcj916v7Ye6LrP
9uL+nFnPc30u+5HtGbfer5ttL/L8dtjPfr2/u0+9wRXWG9t7z7/jreYLe45DV0+9weU07g9sRyz9Poayn9c4dOnUG+ttZ1v1yOMCGoT+
p2VlP4ezHlhv8PPU9f97XKzrod8c9jP3D+dOvcHllMzz+vq3W8+RlZ/CembPV2v8cDme33f3i/BWPbN/UNtp9+Z6jp979edxq3rOp93K
7TqWPmH7j82Asvr7q/U89rd/afcmtifKOW6yU36KOfvPXPU81gPEdV7m+YDtrNVfUzj7D49vthN4vuX3t3veWP2Z/ZQ1Drw/5ym2A3Y5
3K/EDzn8lHgp/6tv/+Doh2z2sB/Gft72U8Y5PrndTD3L4fmd7Zh7br3sXvpbrF+43fo6j98rrP9nO6YuvRLX+13z7M9c3hinf9oLuydb
P7E9ctjZW2/wfMZ+3NJvjeeDNS7Yj9t+qj/rxa0HS4btgFXOet60+s+19Glb7x9u1Z/tbj//0u+v635p7HUBv/rRU046+zOvG8ylV7ic
wv4v+yHLb8f91c9z4napMzkm2junYReugHvDpkb6+dPH5wSPu7VvnXDh7vM3T/jpHx8//OXzb19wpWV++o9x810vS4i5DIPhomtCwOVq
KfQiyMJbJxCm5pUTLDxT9JlAH+tw6tB/zO878Eb5uVHszze8Ln239QD3ks8lxwVF/IYHpO+Yn+/cn2/ZhO/j2SJHPDkhVsz/o0emI+0j
quNSR1CHV8d7jf/jz/mn0JH5+PDTP2AgLzrJv/46xi/CJilfs0kcLaPmzQa58skGIbRjuvNmk9yKTYK6oaTNFilJsUkQ7VSDsEmCYpPg
Jo8Jm41hgmKLIJrHlbzZJEWxRXDLOHhhi3glRzTNZbYcIRwv5YnQhmbfvxnFFsGxfV/7/vd1yglNOYStMqZikxBaqwubpJ/yC5//6psN
cnXFJkE0FTTrZpNYxSZBtG1pmy1SmmaTIJowC5skH/JIaFhbNxvDarYIqfaWL0Hjn2wRQsN7YYt4Jcf6uabIp2KT4PuXuO9fNFuE0Hhp
37+lU17w/l3K71OxSRCNdTdhk5zPny2hvdxmY1jF5qCJyeN+RWS05ckWwfoJbbM1QtNsEkRjJ2GTpFMeCS069v3zyRbJDxto7vvXqdgi
+Pxdyu9JybH/317YJP5kk9D4DGGzQUJQbBFEs8eSN5ukKLYIyrMXtojXbBLUD2bLiznlEdtvmn3/qeQPmv/Km01yKTYJ9n83N1vDTc0m
QdulC5ukn2wPR2yLvtkgRckvQovbff9uTzli3bB/3dK/TjYJykcWNkk+2SQG7w/mBbM9QlZsEUTTxjtvNsmt2CK0SZ42WyQnJSe0cRA2
STjZJMSGMnGzMYxmi2D/RcyuoPFPtgiObz83W8PPU17W+DCClj/ZJPFhIxlBk59sEUJD+31/hDC9lBPbp0n5TZV/JWILCpvkfP4UUb9P
YcPMkw3zoLUtOMCMpp+KTYJoap82W8MnzSYJND9tNolXcqz/VDcbJGm2CI6P0vb9Qb+fbBHsH03Kb16zSR4085bPk01C/Q8RSPz85mR7
EJr6AquA2QyXYpOgPM7NFolTs0nQfujCJumKTYL3v/u+/33KH/0BRuZmk1jFJsHxZdtma9im2STYf7OwSfIpj2hfQOksz0qeUf/Xe9+/
3ootYp/+laV/HXJriI0qbJJwygNe78Nmg/hwskEizZ8lbzZJUWwSrL/khS3iNZsE9bPZ8mxONkkOhCbvlfu/S/VgixDb1+fNJvGKLYLP
79pma7im5Ng+8ExNxsfJJiE289hskKjZIgQJnPv+eZ7yTGxlKb+q8ml8wvhoMj4OtgixTYewYUZVbBLSjy1vNklTbBKcX50XtohXbBIs
302Rz1NO9kOMmw0SNVuE+mfa9wf9frJFUF6k/DI1mwTrpwmbpJ1sEpp/bd9sENsVm4TYgDZvNolVbBFHbNTNFrmaZpPg/JWFTZIVmwTr
F0Yfy7uSR9S/4973H7dmk2D7pM3WMEmxSR42qrBJwsn2sMS2CpsNkoJmi6B9UPJmk5RTfmH9NWGrNMVWIfu2my3v5pQ/9ovZbBBnTjYI
QWKRs8r1fyk2Cep3sK83m2RqNgmOry5skn6ySQhGcyMbe7F5NFsE568582aTzFNObDYkVXL9Js0miTQ+NpvEKzYJ2cd1s0EuzRYJxEbM
m03STrnH9itSflHlh/iMjy2fp5zs81vYMLdiiyTy39K+/zzf77FvEJTL/W9qNglFSxA2STvZHgb1F+LK+f0VW4TYkMnnzSbxii3ysKF2
+blpNkkk/3yzSdJrbBLEzoB+MPaquCH57HaaaGwZBLSZM7zJJingar3DJsFTiE0y48MiGcQiafmOr7FJ0INzzCZBaiP+TDAgY1BsEugD
8elsxuP+lr0I+ekNrjHj/guuOcf1jevGg3Di3sJvxH/hXjxYOx6xJgSjhw+oZ497AogwJaw5fA/cI8A4FzC0cHhF7MPVhDpNuMFcmw1k
zuBaI4wO8MAb1N5FS+WXvU0MFWxseJmaDBjz8EQFVQJu+ZpULySrmwQvmcMwGe6de8Q6eJCkOUHLVLhimnohwwQhOg1xdTBFRdPuC7GJ
YM3BB+7ZQb1DhzZ3Q/RoNQOacdQBb27NhHecFRfkq5nhtqbah1UCJoMt3dpprEXzpBTrxm3BlLEI0Yf3t94PUKnOhhEXm+S217AW9VXM
YHLczUY3kIsN7hJix8ESBcMYzCybcbkqVlsafOCm9YJPLRZ8XFtDhKESbIOyGlzfU4OpCQxWG+wdrb3rbe9Z7Q3njeLtuKcdroNNnu3s
wU6LoP7bmQrT4gTTDhrC5uHgQofcD4ekCgRtQy0R+rN658cEK7HBRJRcuGFCghKvWN3VItSkczHcYEUUBz6TQ20D/hUSRsFxLg5X5HO7
HnQmhl4ow4Gn5YqvrkJ59UYWiXUtDtdadQ1ZmVBoL9X1gXDu5m54phtkD4MkOHAQ3ejVDXjGGaqbMHfOHt2kzb/hca4j0sC4vYEXstf0
tiDFBncnYLrzEyNeeFcHwjq9Q8gm0SIbUjS8nxX+4XyI1UPxPtzwbaE6QvVXdotJAt+u+hgdEoF9vGEig5uCt4X2G5hQ8D3gG4rLV4Mh
EjxYKB4ZFzDT+QInYoQTQnjC/esVfM3w3eF7wjfMSy123yp83/ANvajjHJzhu8H3hG/X/B29v+H+N9wfmRIDQbqp+gHNN6ADQMv6eWV0
P79mkwRy7TaLBEdyekYz7voTdhz+D0YnPA584P8aaAdECt0PMNETig5Gt+3wXhdtIoY4CXQAugtGO6I5rgc3DvP8VQp1vgtGJ/QasHwW
lwxHOPhJ4EuaBKMZx3yGeSnDiH1GN4xqkIORv0Y3jGi4vmYY5TQwocEvGNmgAttdTYOm7mCY45ZEHxnXLg0oEhjlwdwTRjq8wAC7cfQE
Ix0UN2j2hzUCv2FAwIM9VBTikMGwR3IXFGgNjPLLrxFvkDNhoemtb6AnkbADzk7IMOL7Tcv21wUjv0wY+bgK2hZzBDz6eRNUGKZOm+Dc
hGSGC0Z+uRdePD4aAJ4BodrFRwsWvK3txv1T24KzLV+2wchvBvpPAC2AK9RQ1oMXn/Yu5uGUQdnjgjELw2+AihjIWrvgU0Aj3AU0QnUE
5kdy3g2Na+GiCzHiqBXg5hZqJMIwr/C6Az7IMovwqfCBAYRHiMGFCh/ofhjd6AKf7KrwAY1AHg4ME8J2D/iAlkmgFcCNd2mkB8sd4VPh
A42SXQGXFz6gocqAD+iHh10Cn1HxX6AtmmsVPtDN8QDbBP0z0Bgdoya5O94ONOFil9xugHYBre7GgA8cMyJ+Gz6g2eB4Jry2JkOc8LBB
mn04Zx6B6PCSMKLgZHphMDpAIcJnevoTYDRDf/cBRiUeVwK7rl2Lb4Y2UvSxwWdGJE+DhgAjpcFnYmgktF0yKB/4TPjAAdO3xxVrsMo8
HhVG9MMzgw8c4EH61uAz4QMH2EZLK8AHOSYwpdwNPhM+cIw0QCPAZ8IHjplAC7R5aIOciTZNbBKEpYMWgAkZzFuY7+GbKHXw/zggglnf
HmNpwQcUK+2EIJ0OqjGVZROgxkDuWSG17AkeANoBp1CyCYbBda8wwMdENhWMeLCGzVVRS/SlJQLYAgXhsQYcXxPh+nShiw5uANgaMMOD
pkgYUwg0RXjYpmQHgLboODZg/odnq/AsdQQDswj4p8lAZSH0yvQLNAVGWpnwgfe4ywQNAeMc7jtAm4wB4ymgdgA7AH5PGHkGRj9capE0
B8MTBghohoC0gmQdIiFhJBP9D+4OKtaG1mgb74rdgp1jwcYBTXDZCKMVZlDwB/qyAarNyFWGUZpBW8DtbbkDzqIw+putcH6FLtkSaIAO
H+S7glHRcW0M198CMklh5MOoJiYpaBAYIHbMZmGasTM3GPFoA3QMYQA2QH/YpMgKyfBiMGfDizh3dRjt8A0XO5wIU0OiEkyuFUOjuABz
fQBNAI6fAxPLoUN7wdwM7eci2BLxxlURmP/hHglGaZpoVlQHys7ljm9jwBaAcV7hG0Y8zNZQdfD2YHdUkxwYv66V6NoNNgHoDxrdzT+s
DJiIb5j/7z4c6FiYvosboCIHaB6wLGBk3w5eF5rhgnENUxuMFGpsIiAgPceBOVtBJeLCPBgWAQqG0YEwC9BuYAuA6QbdHIaqh8kZ7AGY
WCcy2GBGvooPGT4wMgPMrcjxBRsWRjt8Knxu+IAfGz3aBfAp8OnwgVEb4fp0wQeuTw0DFiEjsMDEW57RX+Fzw8cgy4wsdV8KfPoFWgB3
7zzYCPAB+6OCZqr39GCtwti/HzsB7tV68RiKAerMw2VgKyC5ecIr3GA945kZ7IUI9oJ/mCNgH0GPApshgYYIRAYbr7FJSnyCBiygBsM1
kkKjL3QrwxsZhcVsh+43e+MsJ55o9L5QSlw+o5AY/ZXX9em1chaqkFGkuxxGG9uNAvILDePNS3irKieocpjFsNkOjJpaqJZdzrrfZPQv
l8OoXkYDXRt9RlcyGpLROcy2YRTtZLTOQsMwmpLRloPR7tdm7xxsG0YPMVuCUUiMTmK0ZY0nConRORs1yeged6KQuHxGwzPaeS7UDrN6
GJW60UP+RCHx+3P/cuVk/zCrh9F0jKIFR/xAD3H53L/GYvUwSs8pVtRmQTGKfdVr4vphdOx6L2a5cP1sdNlklC+//yrHnuUwys8yKv4+
UXn877Taa9drPcvZrKfrrJ/Nimq73v3LemW2EZfDaLi6UOGMtmNW1GZBLZQW1yuPUy6nLjQzs8wKo8LTyRq4zYmeZhTqtfplXiwHZpkV
e6LmmTVQVv9htCL3z7jek9kWzDLL+UTNM5j7iifrYquFcbLiuL7TUKj5uevpYF3w+zE6ujKqdfVHRmU2u/XK0p+rHaJCY3L7rXq51/1Y
7/C4N/dGQYaDRXKf6Gm3WA6lqXKYBrDuy+hyHu/crxqjx1e9XKvduQPy+5t2okk3i4TZVeu9ajjRprucfpbDKP/NIln13dNZP2P1111O
2fXCsWAO9CLXN6OweXxeqz/6vNliB5shrnmwuxN1vuep1Q5msf7C6n/MSmI2g10srM6w4nCWw+3A7EJmnzErabMZlpzZRTyvcTmsx/Ia
P8w+i+ZkM5TV75ldtMtxez7zi7XoX6JQr3zOl4FZjIzuj2c53A7cHy9mHzHr0G1UN8lbYZT86jd2o22f/s6sr/W86dosLPOSDdgY1etP
1Clfz/0xrfqI/DzcrOu9ud0DzxM365mNTl9sid1f9sT+kg3I7X6t/rdZGnbPN/4lypvZpqw3nGr3mM95jK8PY/XDdR9mTzILN6x6ZhZX
W/+fWL2w3uH2Sqr/MDvQrnIio5XXeet5WO90rqdVj1c9WWuN+09lNtQ5j7HeSev9WG8z+pn1TWJWLtun1zmPsd7xzLJiFs59staYTcyk
6c7ofWalLb1jVz0Gu/W/eWkvw7h4WGadWTFnP5vLnrsDs2U2e+Yoxyz2Jc8j9Tr7WVv9mcczz7PlOu36zQpc7cnzG6PamSXLaH4eX8yq
4HKYNdgYpW5PvcDsMbvqO7GdNE973LO+s2c/ZFbzXGyLmNe4v5h9rliI67k3+9hu1uayF7ZdGF6Og5ZPFmJd/YdZD3t8CEvIH6zsdT3r
Ge6/kfUms4rSZs0v/2HZq8yO537vTjY52+ls53P5Ne7pm1kkx7zLeob7L7MBmTXDbPPCbKq67efwcr6w63m5XQKzW9Uf9leYPRVWf43K
LmT9wH7lV+UUzZ46+w/rd9YP3Z7sqF2OYk81Zsn0055j/ZD6K+WEkz0VmTUYT3uO9QP3e/6zy7EneyoGZp+e8y7Pw8zm4/KZ5cJsrNtv
+/op5z7L2SzfNd7ZXtzldGa7rv686ru5c/7m/s/+61flFLbrtx2/WFIc3uEcXy/YfGc5Ygc//aed8/fkcdpONh/bebscf7J/vmKTIDbi
Dj2+zibJb59wPeimb5zwFpskH1yQZphasdkk4e0TCFPzyglEyKAQwS8oCd+FmIA3WqyQe7FC5mKFOFOvxRq5FmvkWqwR+m5Lfi/5XPJv
skkoPvdXLIgfx3lUOso+sjq+c+P/v3ogmwRG8l9/+flz/zfoobgHgZCg5zt/tAFjqyW/fmTDP9L6UcLzwxvLPzJ0+vEfX36tqBv+9ulv
n25hqEDX//nz5397fmmuyoX6Kl3CRbkUFwWxYKVveTkznzxYKGeFS2IVVwTBKSFveciKC0JYz3vL+624IJQ5JGz5VJlHEpafyuZypKK4
GojVrGbL65k5JFnCsgfhYgTFtUCs1pW3/MoqMwdhgY1wKYziUgTS5lt+n+VnT5GB++YiuK64DoQFNFuO9I6Dy0CRv7NwGbLiKmD9dCm/
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
'''
SLOT_DATA = json.loads(zlib.decompress(base64.b64decode(''.join(_SLOTS.split()))))
SLOT_NAMES = {'high-contrast': 'High Contrast', 'cinema-yellow': 'Cinema (Yellow)', 'cinema-green': 'Cinema (Green)',
              'vivid': 'Vivid', 'positive-film': 'Positive Film', 'negative-film': 'Negative Film',
              'bleach-bypass': 'Bleach Bypass', 'retro': 'Retro', 'soft-monotone': 'Soft Monotone',
              'hard-monotone': 'Hard Monotone', 'hi-contrast-bw': 'Hi-Contrast B&W',
              'mono-standard': 'Standard (monochrome)', 'mono-soft': 'Soft (monochrome)',
              'mono-solid': 'Solid (monochrome)'}
SLOT_ORDER = list(SLOT_NAMES)        # looks are placed in this order, so a set of looks always builds the same file
# what each slot replaces, whether it works in movie mode, and the extra sliders it offers
SLOT_INFO = {
    'high-contrast': ('the hidden monochrome High Contrast look', True, '-'),
    'cinema-yellow': ("RICOH's Cinema (Yellow) look", True, 'Saturation, Hue'),
    'cinema-green': ("RICOH's Cinema (Green) look", True, 'Saturation, Hue'),
    'vivid': ("RICOH's Vivid look", True, 'Saturation, Hue'),
    'positive-film': ("RICOH's Positive Film look", True, 'Saturation, Hue'),
    'negative-film': ("RICOH's Negative Film look", True, 'Saturation, Hue'),
    'bleach-bypass': ("RICOH's Bleach Bypass look", True, 'Saturation, Hue'),
    'retro': ("RICOH's Retro look", True, 'Saturation, Hue'),
    'soft-monotone': ("RICOH's Soft Monotone look", False, '-'),
    'hard-monotone': ("RICOH's Hard Monotone look", True, '-'),
    'hi-contrast-bw': ("RICOH's Hi-Contrast B&W look", True, '-'),
    'mono-standard': ('the hidden monochrome Standard look', True, '-'),
    'mono-soft': ('the hidden monochrome Soft look', False, '-'),
    'mono-solid': ('the hidden monochrome Solid look', True, '-'),
}


def slot_line(name):
    return f'{SLOT_NAMES[name]} (replaces {SLOT_INFO[name][0]})'


def list_slots(log=print):
    log(f'{"--slot":16s} {"shown as":24s} {"replaces":42s} {"movie":5s}  extra sliders')
    for name in SLOT_ORDER:
        what, movie, extra = SLOT_INFO[name]
        shown = SLOT_NAMES[name] + (' (default)' if name == DEFAULT_SLOT else '')
        log(f'{name:16s} {shown:24s} {what:42s} {"yes" if movie else "no":5s}  {extra}')
    log('Your look opens with every slider at 0 in every slot; a slot you do not use keeps its own look.')
DEFAULT_SLOT = 'high-contrast'


def matrix_hex(look):
    mat = look['matrix_q13']
    if any(abs(sum(r) - 8192) > 2 for r in mat) or max(abs(x) for r in mat for x in r) > 0x7fff:
        raise Refused('look matrix must be 3x3, Q13, rows summing to 8192')
    return struct.pack('<9h', *[x for r in mat for x in r]).hex()


def distinct_curves(curves):
    if len(curves) != 3 or any(len(c) != 256 or min(c) < 0 or max(c) > 16383 for c in curves):
        raise Refused('curves must be three lists of 256 values in 0..16383')
    distinct = []
    for c in curves:
        if list(c) not in distinct:
            distinct.append(list(c))
    if len(distinct) > 3:
        raise Refused('at most three different channel curves are supported')
    return distinct


def look_changes(look):
    """(offset, old, new, what) for one look: matrix, curve table selection, curve(s)."""
    out = [(LOOK['matrix'][0], LOOK['matrix'][1], matrix_hex(look), 'look colour matrix')]
    curves = look.get('curves')
    if not curves:                                   # no look curve: the colour look's plain tone curve
        for off, old in LOOK['select']:
            out.append((off, old, struct.pack('<I', LOOK['select_none']).hex(), 'use the plain tone curve'))
        return out
    distinct = distinct_curves(curves)
    if len(distinct) == 1:
        buf, bufs = LOOK['single'], [LOOK['single']]
    elif len(distinct) == 2:
        buf, bufs = LOOK['pair'], [LOOK['pair'], LOOK['single']]
    else:
        buf, bufs = LOOK['pair'], [LOOK['pair'], LOOK['single'], LOOK['third']]
    for off, old in LOOK['select']:
        out.append((off, old, struct.pack('<I', buf['set']).hex(), 'use the look\'s tone curves'))
    for k, (b, c) in enumerate(zip(bufs, distinct)):
        out.append((b['curve_off'], b['curve_old'], struct.pack('<256H', *c).hex(), f'tone curve {k + 1}'))
    ptrs = [bufs[distinct.index(list(c))]['curve'] for c in curves]
    if len(distinct) >= 2:
        out.append((LOOK['pair']['chan_off'], LOOK['pair']['chan_old'], struct.pack('<III', *ptrs).hex(),
                    'tone curve per colour channel'))
    return out


def hue_table_hex(q, old):
    """The look's hue-sector matrices in the size of the place that takes them."""
    import numpy as np
    q = np.array(q, int)
    if q.shape != (12, 3, 3) or np.abs(q).max() > 2047 or (q.sum(2) != 1024).any():
        raise Refused('hue sectors must be 12 matrices of 3x3 (Q10, |value| <= 2047, rows summing to 1024)')
    copies = len(old) // 2 // (12 * 9 * 4)
    table = np.repeat(q[:, None], copies, axis=1).astype('<i4').tobytes()
    if len(table) * 2 != len(old):
        raise Refused('internal: hue-sector data size')
    return table.hex()


def hue_changes(look):
    """(offset, old, new, what) for the look's 12 hue-sector matrices."""
    q = (look.get('hue_sectors') or {}).get('matrices_q10')
    if not q:
        return []
    off, old = HUE['matrices']
    return [(o, a, b, 'hue sectors') for o, a, b in HUE['fixed']] + [(off, old, hue_table_hex(q, old), 'hue sectors')]


def post_matrix_rows(target):
    """The look's values for a target matrix, exact after the camera's own rounding."""
    import itertools
    import numpy as np
    Y = np.array(HUE_YCC, np.int64)
    Yi = np.linalg.inv(Y.astype(float))
    rows = []
    for t in target:
        r0 = np.rint(8192 * np.asarray(t, float) @ Yi).astype(np.int64)
        for d in itertools.product(range(-2, 3), repeat=3):
            r = r0 + np.array(d)
            if (((r @ Y + 4096) >> 13) == t).all():
                rows.append(r)
                break
        else:
            raise Refused('internal: colour matrix after the curves cannot be represented')
    return np.array(rows)


def post_check(p):
    import numpy as np
    p = np.array(p, int)
    if p.shape != (3, 3) or (p.sum(1) != 512).any():
        raise Refused('colour matrix after the curves must be 3x3 with rows summing to 512')
    t = post_targets(p)
    if t.min() < -256 or t.max() > 255:
        raise Refused('colour matrix after the curves is out of the camera\'s range')
    return p


def post_data(p):
    """The look's nine camera matrices for colour after the curves (one per Hue step)."""
    return b''.join(struct.pack('<9i', *post_matrix_rows(t).ravel().tolist()) for t in post_targets(p))


def post_changes(look, data=None):
    """(offset, old, new, what) for the look's colour matrix after the curves (data: the slot's places)."""
    data = data or POST
    p = look.get('post_matrix_q9')
    if not p:
        return []
    p = post_check(p)
    places, data = data, post_data(p)
    off, old = places['matrices']
    if len(data) * 2 != len(old):
        raise Refused('internal: colour matrix data size')
    return [(o, a, b, 'colour matrix after the curves') for o, a, b in places['fixed']] + \
        [(off, old, data.hex(), 'colour matrix after the curves')]


DATA_WHAT = 'make the look slot available with its colour processing and defaults'


def slot_changes(look, name):
    """(offset, old, new, what) for a look on Cinema (Yellow) or Cinema (Green): the look, neutral slider defaults
    and its colour after the curves."""
    s, label = SLOT_DATA['slots'][name], SLOT_NAMES[name]
    out = [(o, a, b, f'{label}: neutral slider defaults') for o, a, b in s['defaults']]
    out.append((s['matrix'][0], s['matrix'][1], matrix_hex(look), f'{label}: look colour matrix'))
    so, sold = s['curve_switch']
    curves = look.get('curves')
    if not curves:
        out.append((so, sold, '0000', f'{label}: use the plain tone curve'))
    else:
        distinct = distinct_curves(curves)
        out.append((so, sold, '0100', f'{label}: use the look\'s tone curves (Color Tone has no effect)'))
        for k, c in enumerate(distinct):
            out.append((s['curves'][k][0], s['curves'][k][1], struct.pack('<256H', *c).hex(), f'{label}: tone curve {k + 1}'))
        po, pold = s['curve_pointers']
        ptrs = [s['curve_va'][distinct.index(list(c))] for c in curves]
        out.append((po, pold, struct.pack('<III', *ptrs).hex(), f'{label}: tone curve per colour channel'))
    q = (look.get('hue_sectors') or {}).get('matrices_q10')
    if q:
        off, old = s['hue']['table']
        out.append((off, old, hue_table_hex(q, old), f'{label}: hue sectors'))
    else:
        out += [(o, a, b, f'{label}: no hue sectors') for o, a, b in s['hue']['off']]
    return out + post_changes(look, s['post'])


class Space:
    """Room for the looks' data, filled in order; changes() gives the edits."""

    def __init__(self, segments):
        self.segs = [dict(off=o, old=bytes.fromhex(h), at=va, data=bytearray.fromhex(h), used=0)
                     for o, h, va in segments]

    def free(self):
        return sum(len(g['old']) - g['used'] for g in self.segs)

    def put(self, data, what='data'):
        n = (len(data) + 3) // 4 * 4
        for g in self.segs:
            if g['used'] + n <= len(g['old']):
                at = g['at'] + g['used']
                g['data'][g['used']:g['used'] + len(data)] = data
                g['used'] += n
                return at
        raise Refused(f'not enough room for these looks together ({what}: {len(data)} bytes, '
                      f'{self.free()} left); use fewer slots, or looks without hue sectors or colour after the curves')

    def put_at(self, at, data):
        g = next(g for g in self.segs if g['at'] <= at < g['at'] + g['used'])
        g['data'][at - g['at']:at - g['at'] + len(data)] = data

    def changes(self):
        return [(g['off'], g['old'][:g['used']].hex(), bytes(g['data'][:g['used']]).hex(), 'data for the looks')
                for g in self.segs if g['used']]


def extra_space(look, name):
    """Bytes of room a look in this slot needs."""
    z = SLOT_DATA['templates']['sizes']
    n = 0
    if look.get('curves'):
        n += z['curve'] * len(distinct_curves(look['curves'])) + z['curves_head']
    if (look.get('hue_sectors') or {}).get('matrices_q10') and 'hue_table' not in SLOT_DATA['extra'][name]:
        n += z['hue'] + z['hue_links'] + z['hue_head']
    if look.get('post_matrix_q9'):
        n += z['after']
    return n


def extra_changes(look, name, space):
    """(offset, old, new, what) for a look on one of the further slots."""
    s, label, tpl = SLOT_DATA['extra'][name], SLOT_NAMES[name], SLOT_DATA['templates']
    out = [(o, a, b, f'{label}: neutral slider defaults') for o, a, b in s['defaults']]
    out += [(o, a, b, f'{label}: a colour look with your colours only') for o, a, b in s['fixed']]
    out.append((s['matrix'][0], s['matrix'][1], matrix_hex(look), f'{label}: look colour matrix'))

    def rows(t, at, what):
        for o, a, base in s['rows'][t]:
            new = base if at is None else struct.pack('<I', at).hex()
            if new != a:
                out.append((o, a, new, f'{label}: {what}'))
    curves = look.get('curves')
    if curves:
        distinct = distinct_curves(curves)
        at = [space.put(struct.pack('<256H', *c), 'tone curve') for c in distinct]
        ptrs = [at[distinct.index(list(c))] for c in curves]
        rows('curves', space.put(bytes.fromhex(tpl['curves_head']) + struct.pack('<III', *ptrs), 'tone curves'),
             'use the look\'s tone curves')
    else:
        rows('curves', None, 'use the plain tone curve')
    q = (look.get('hue_sectors') or {}).get('matrices_q10')
    if q and 'hue_table' in s:                       # this slot has its own room for hue sectors
        off, old = s['hue_table']
        out.append((off, old, hue_table_hex(q, old), f'{label}: hue sectors'))
    elif q:
        z = tpl['sizes']
        table = space.put(bytes.fromhex(hue_table_hex(q, '00' * z['hue'])), 'hue sectors')
        links = space.put(struct.pack(f'<{z["hue_links"] // 4}I', *[table] * (z['hue_links'] // 4)), 'hue sectors')
        rows('hue', space.put(bytes.fromhex(tpl['hue_head']) + struct.pack('<I', links)
                              + bytes.fromhex(tpl['hue_tail']), 'hue sectors'), 'hue sectors')
    else:
        rows('hue', None, 'no hue sectors')
    p = look.get('post_matrix_q9')
    if p:
        data = post_data(post_check(p))
        at = space.put(bytes(tpl['after_head'] + len(data)), 'colour after the curves')
        links = tpl['after_links']
        space.put_at(at, struct.pack(f'<{len(links)}I', *[at + d for d in links]) + data)
        rows('colour', at, 'colour after the curves')
    else:
        rows('colour', None, 'colour setting')
    return out


def look_slot(look):
    name = look.get('slot') or DEFAULT_SLOT
    if name not in SLOT_NAMES:
        raise Refused(f'unknown slot {name!r}; choose one of: {", ".join(SLOT_NAMES)}')
    return name


def all_changes(looks):
    """Every change for one look, or several looks in different slots."""
    looks = [looks] if isinstance(looks, dict) else list(looks)
    names = [look_slot(lk) for lk in looks]
    if len(set(names)) != len(names):
        raise Refused('two looks for the same slot: ' + ', '.join(sorted({n for n in names if names.count(n) > 1})))
    out, taken = [], set()
    pool = SLOT_DATA['pool']
    space = Space(pool['always'] + ([] if DEFAULT_SLOT in names else pool['without-high-contrast']))
    by_name = dict(zip(names, looks))
    need = sum(extra_space(lk, n) for n, lk in by_name.items() if n in SLOT_DATA['extra'])
    if need > space.free():
        raise Refused(f'these looks need {need} bytes of room together, {space.free()} are available'
                      + ('' if DEFAULT_SLOT not in names else ' (a look on High Contrast uses part of it)')
                      + '; use fewer slots, or looks without hue sectors or colour after the curves')
    for name in SLOT_ORDER:
        lk = by_name.get(name)
        if lk is None:
            continue
        if name == DEFAULT_SLOT:
            post = post_changes(lk)
            taken |= {o for o, _, _, _ in post}
            out += look_changes(lk) + hue_changes(lk) + post
        elif name in SLOT_DATA['slots']:
            out += slot_changes(lk, name)
        else:
            out += extra_changes(lk, name, space)
    out += space.changes()
    unlock = set(SLOT_DATA['unlock'])                # without a High Contrast look, that slot stays as it was
    fixed = [(o, a, b, DATA_WHAT) for o, a, b in DATA['fixed']
             if (o in unlock or DEFAULT_SLOT in names) and o not in taken]
    return fixed + out


def make_firmware(source, looks, log=print):
    digest = sha256(source)
    if digest != OFFICIAL_SHA256 or len(source) != OFFICIAL_BYTES:
        if digest in OTHER_KNOWN:
            raise Refused(f'this is {OTHER_KNOWN[digest]}; use the official RICOH file')
        raise Refused('input is not the official RICOH GR IV 1.11 fwdc248b.bin '
                      f'(SHA-256 {digest}, expected {OFFICIAL_SHA256})')
    log('input: official RICOH GR IV 1.11 firmware (SHA-256 verified)')
    log('decoding container ...')
    payload, frames, consumed = decode(source)
    check_container(source, payload, consumed)
    secs = sections(payload)
    rtos = next((s for s in secs if s[0] == 'RTOS'), None)
    if rtos is None:
        raise Refused('payload: RTOS section not found')
    buf = bytearray(payload)
    items = all_changes(looks)
    spans = sorted((o, o + len(bytes.fromhex(a))) for o, a, _, _ in items)
    if any(b0 < a1 for (_, a1), (b0, _) in zip(spans, spans[1:])):
        raise Refused('internal: overlapping changes')
    for off, old, new, what in items:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        have = bytes(buf[off:off + len(old)])
        if have != old or len(new) != len(old):
            raise Refused(f'unexpected original bytes at {off:#x} ({what})')
        if not (rtos[1] <= off and off + len(new) <= rtos[2]):
            raise Refused(f'change at {off:#x} is outside the RTOS section')
        buf[off:off + len(new)] = new
    log(f'  {len(items)} changes applied ({sum(w != DATA_WHAT for *_, w in items)} carry your look)')
    patched = rezero(bytes(buf))
    log('rebuilding container ...')
    changed = differences(payload, patched)
    out, reemitted = rebuild(source, frames, consumed, patched, changed)
    log('verifying result ...')
    again, _, used = decode(out)
    if again != patched:
        raise Refused('verification: rebuilt container does not decode to the patched firmware')
    check_container(out, again, used)
    if out[:HEADER] != source[:HEADER]:
        raise Refused('verification: header changed')
    allowed = {i for off, old, _, _ in items for i in range(off, off + len(bytes.fromhex(old)))}
    allowed |= set(range(len(payload) - 4, len(payload)))
    stray = [i for i in changed if i not in allowed]
    if stray:
        raise Refused(f'verification: unexpected changes at {[hex(i) for i in stray[:8]]}')
    if sections(again) != secs:
        raise Refused('verification: section layout changed')
    for tag, a, b in secs:
        if tag != 'RTOS' and again[a:b] != payload[a:b]:
            raise Refused(f'verification: section {tag} changed')
    log(f'verified: {len(changed)} payload bytes changed, {reemitted} frames re-encoded, '
        f'all other sections identical')
    return out


def write_atomic(data, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / 'fwdc248b.bin'
    if target.exists():
        raise Refused(f'{target} already exists; choose another output directory or remove it')
    tmp = target.with_name('.fwdc248b.bin.tmp')
    tmp.write_bytes(data)
    if sha256(tmp.read_bytes()) != sha256(data):
        tmp.unlink()
        raise Refused('write verification failed')
    tmp.rename(target)
    return target


def identify(data, log=print):
    digest = sha256(data)
    names = {OFFICIAL_SHA256: 'official RICOH GR IV 1.11 (unmodified)', **OTHER_KNOWN}
    log(f'SHA-256  {digest}')
    log(f'bytes    {len(data)}')
    try:
        payload = check_container(data)
        log('container: valid (size fields, footer, both checksums)')
    except Refused as exc:
        log(f'container: INVALID - {exc}')
        return 2
    if digest in names:
        log(f'file     {names[digest]}')
        return 0
    def has(changes):
        return all(payload[o:o + len(bytes.fromhex(b))] == bytes.fromhex(b) for o, _, b in changes)

    def yn(x):
        return 'yes' if x else 'no'
    unlock = set(SLOT_DATA['unlock'])
    if not has([c for c in DATA['fixed'] if c[0] in unlock]):
        log('file     unknown - not the official 1.11 file and not made by GR4-LUTSmith')
        return 1
    found = []
    post = has(POST['fixed'])
    post_rows = {o for o, _, _ in POST['fixed']} if post else set()
    if has([c for c in DATA['fixed'] if c[0] not in unlock and c[0] not in post_rows]):
        m = struct.unpack_from('<9h', payload, LOOK['matrix'][0])
        found.append(f'{SLOT_NAMES[DEFAULT_SLOT]} (look matrix {[list(m[i:i + 3]) for i in (0, 3, 6)]}; '
                     f'hue sectors: {yn(has(HUE["fixed"]))}; colour after the curves: {yn(post)})')
    for name, sd in SLOT_DATA['slots'].items():
        if has(sd['defaults']):
            off, old = sd['hue']['table']
            hue = payload[off:off + len(old) // 2].hex() != old and not has(sd['hue']['off'])
            found.append(f'{SLOT_NAMES[name]} (hue sectors: {yn(hue)}; colour after the curves: '
                         f'{yn(has(sd["post"]["fixed"]))})')
    for name, sd in SLOT_DATA['extra'].items():
        if has(sd['defaults']):
            def moved(t):
                return any(payload[o:o + 4].hex() != base for o, _, base in sd['rows'][t])
            ht = sd.get('hue_table')
            hue = moved('hue') or (ht is not None and payload[ht[0]:ht[0] + len(ht[1]) // 2].hex() != ht[1])
            found.append(f'{SLOT_NAMES[name]} (hue sectors: {yn(hue)}; colour after the curves: {yn(moved("colour"))})')
    log('file     a GR4-LUTSmith firmware; ' + ('personal looks in: ' + '; '.join(found) if found else
                                                 'no personal look (hidden looks unlocked only)'))
    return 0


# ------------------------------------------------------------------ LUT files
class Lut:
    """A .cube LUT (3D, or 1D expanded per channel), values as an (n,n,n,3) array [b][g][r]."""

    def __init__(self, path):
        import numpy as np
        text = Path(path).read_text(errors='replace')
        self.sha256 = hashlib.sha256(text.encode()).hexdigest()
        head, rows, self.ignored = {}, [], []
        for line in text.splitlines():
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            tok = line.split()
            if tok[0][0].isalpha():
                key = tok[0].upper()
                if key == 'TITLE':
                    head['TITLE'] = line[5:].strip().strip('"')
                elif key in ('LUT_3D_SIZE', 'LUT_1D_SIZE'):
                    head[key] = int(tok[1])
                elif key in ('DOMAIN_MIN', 'DOMAIN_MAX'):
                    head[key] = tuple(map(float, tok[1:4]))
                elif key in ('LUT_3D_INPUT_RANGE', 'LUT_1D_INPUT_RANGE'):
                    head['DOMAIN_MIN'], head['DOMAIN_MAX'] = (float(tok[1]),) * 3, (float(tok[2]),) * 3
                else:
                    self.ignored.append(tok[0])
                continue
            if len(tok) != 3:
                raise Refused(f'{path}: invalid data row {line[:40]!r}')
            rows.append(tuple(map(float, tok)))
        v = np.array(rows, float)
        if not len(v) or not np.isfinite(v).all():
            raise Refused(f'{path}: no data or non-finite values')
        self.lo = np.array(head.get('DOMAIN_MIN', (0., 0., 0.)))
        self.hi = np.array(head.get('DOMAIN_MAX', (1., 1., 1.)))
        if 'LUT_3D_SIZE' in head and 'LUT_1D_SIZE' in head:
            raise Refused(f'{path}: combined 1D + 3D LUTs are not supported')
        if 'LUT_3D_SIZE' in head:
            n = head['LUT_3D_SIZE']
            if not 2 <= n <= 129 or len(v) != n ** 3:
                raise Refused(f'{path}: LUT_3D_SIZE {n} but {len(v)} rows')
            self.kind, self.n, self.table = '3D', n, v.reshape(n, n, n, 3)
        elif 'LUT_1D_SIZE' in head:
            n = head['LUT_1D_SIZE']
            if not 2 <= n <= 65536 or len(v) != n:
                raise Refused(f'{path}: LUT_1D_SIZE {n} but {len(v)} rows')
            g = np.linspace(0, 1, 33)
            xs = np.linspace(0, 1, n)
            x = grid(33)
            out = np.stack([np.interp(x[:, c], xs, v[:, c]) for c in range(3)], 1)
            self.kind, self.n, self.table = '1D', 33, out.reshape(33, 33, 33, 3)
        else:
            raise Refused(f'{path}: no LUT_3D_SIZE or LUT_1D_SIZE')
        self.title = head.get('TITLE', '')
        if v.min() < -0.05 or v.max() > 1.05:
            raise Refused(f'{path}: output range {v.min():.2f}..{v.max():.2f} is not 0..1; '
                          'log or scene-referred LUTs are not supported')

    def __call__(self, rgb):
        """Trilinear lookup; inputs clamped to the LUT's domain."""
        import numpy as np
        n = self.n
        p = np.clip((rgb - self.lo) / (self.hi - self.lo), 0, 1) * (n - 1)
        a = np.minimum(np.floor(p).astype(int), n - 2)
        f = p - a
        out = 0
        for dr in (0, 1):
            for dg in (0, 1):
                for db in (0, 1):
                    w = ((f[:, 0] if dr else 1 - f[:, 0]) * (f[:, 1] if dg else 1 - f[:, 1])
                         * (f[:, 2] if db else 1 - f[:, 2]))
                    out = out + w[:, None] * self.table[a[:, 2] + db, a[:, 1] + dg, a[:, 0] + dr]
        return np.clip(out, 0, 1)


def grid(n):
    import numpy as np
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')
    return np.stack([r.ravel(), gg.ravel(), b.ravel()], 1)


# ------------------------------------------------------------------ colour
SRGB_TO_ADOBE = [[366 / 512, 146 / 512, 0], [0, 1, 0], [0, 21 / 512, 491 / 512]]
ADOBE_GAMMA = 563 / 256
XYZ = [[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]]
WHITE = [0.95047, 1.0, 1.08883]


def srgb_dec(x):
    import numpy as np
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb_enc(x):
    import numpy as np
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def adobe_lut_on_srgb(lut, y):
    """Apply an Adobe RGB LUT to sRGB-encoded colours, result in sRGB (colorimetric, via linear light)."""
    import numpy as np
    m = np.array(SRGB_TO_ADOBE)
    ya = np.clip(srgb_dec(y) @ m.T, 0, 1) ** (1 / ADOBE_GAMMA)
    lin = (lut(ya) ** ADOBE_GAMMA) @ np.linalg.inv(m).T
    keep = (lin >= -1e-3).all(1) & (lin <= 1 + 1e-3).all(1)
    return srgb_enc(lin), keep


def lab(rgb):
    import numpy as np
    xyz = srgb_dec(rgb) @ np.array(XYZ).T / np.array(WHITE)
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)


def de00(l1, l2):
    """CIEDE2000 (Sharma, Wu & Dalal 2005)."""
    import numpy as np
    L1, a1, b1 = l1.T
    L2, a2, b2 = l2.T
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(C1p * C2p == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    hbp = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2,
                                                np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dth = 30 * np.exp(-((hbp - 275) / 25) ** 2)
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


# ------------------------------------------------------------------ camera model
def base_curve(name):
    import numpy as np
    return np.array(DATA['curves'][name], float) / 16384


def inverse(c, y):
    """Inverse of a base curve on its rising part: output (0..1) -> curve index."""
    import numpy as np
    top = int(np.argmax(c >= 1.0)) if (c >= 1.0).any() else 255
    xs, ys = c[:top + 1], np.arange(256.)[:top + 1]
    keep = np.concatenate([[True], np.diff(xs) > 0])
    return np.interp(np.clip(y, 0, 1), xs[keep], ys[keep])


def to_index(y):
    """Camera output of its neutral rendering (0..1) -> linear signal in curve-index units."""
    return inverse(base_curve('neutral'), y)


def compose(curve, base):
    """The camera's composition of a look curve after the base curve (integer, as the firmware)."""
    out = []
    for v in base:
        i, f = v >> 6, v & 0x3f
        if i > 0xfe:
            out.append(int(curve[255]))
        else:
            p = (int(curve[i + 1]) - int(curve[i])) * f
            out.append(int(curve[i]) + ((p + 0x3f) >> 6 if p < 0 else p >> 6))
    return out


def exported(curves):
    """The camera's final per-channel tone curves (10-bit) for a look."""
    import numpy as np
    base = [int(x) for x in DATA['curves']['slot']]
    src = [base] * 3 if not curves else [compose(c, base) for c in curves]
    return [np.minimum(np.array(s) >> 4, 1023) for s in src]


def render(v, look, bounds=None):
    """Linear signal (N,3, index units) -> what the camera writes (0..1), firmware-exact curves."""
    import numpy as np
    M = np.array(look['matrix_q13'], float) / 8192
    z = v @ M.T
    q = (look.get('hue_sectors') or {}).get('matrices_q10')
    if q:
        z = hue_apply_q(z, np.array(q), HUE_BOUNDS if bounds is None else bounds)
    ex = exported(look.get('curves'))
    out = np.stack([np.interp(np.clip(z[:, c], 0, 255), np.arange(256.), ex[c]) / 1023 for c in range(3)], 1)
    p = look.get('post_matrix_q9')
    if p:
        out = np.clip(out @ post_effective(p).T, 0, 1)
    return out


# ------------------------------------------------------------------ colour after the tone curves
# The camera can mix the colours once more after the tone curves: a 3x3 matrix P whose rows sum to 1, so greys
# stay grey. Film looks often treat colours differently in shadows and highlights; a mix after the curves can
# follow that where the colour matrix before them cannot. Every Hue step is set, each with the camera's own Hue
# change on top of the look.
POST_LIMIT = 0.98         # the camera's values beyond this are penalised while fitting (keeps them in range)
POST_PHOTO_WEIGHTS = (0.5, 2.0, 8.0)    # photo and grey weights tried, so everyday content can count for more
POST_WARM_LR = 1e-3                     # smaller steps when continuing from a fitted look


def post_hue(h):
    """The camera's own values for Hue step h (0..8, 4 = Hue 0)."""
    import numpy as np
    a, s, d = POST['hue'][h]
    return np.array([[8192, 0, 0], [0, a, s], [0, -s, d]], np.int64)


def post_targets(p_q9):
    """The camera's nine matrices (one per Hue step) for P; the look is shown at Hue 0 (step 4), the other
    steps are kept within the camera's range."""
    import numpy as np
    P = np.array(p_q9, float) / 512
    Y = np.array(HUE_YCC, np.int64)
    out = []
    for h in range(9):
        H = post_hue(h) @ Y / 8192                             # the camera's own matrix at this Hue step
        exact = H @ P
        t = np.rint(exact).astype(int)
        for r in range(3):                                     # rows keep their sums: greys stay grey
            d = int(np.rint(H[r].sum())) - t[r].sum()
            while d:
                j = int(np.argmax((exact[r] - t[r]) * np.sign(d)))
                t[r, j] += np.sign(d)
                d -= np.sign(d)
        out.append(t if h == 4 else np.clip(t, -256, 255))
    return np.array(out)


def post_effective(p_q9):
    """P as the camera really applies it at Hue 0, after rounding."""
    import numpy as np
    return np.linalg.solve(np.array(HUE_YCC, float), post_targets(p_q9)[4].astype(float))


def post_quantise(P):
    import numpy as np
    q = np.rint(np.asarray(P) * 512).astype(int)
    for r in range(3):
        q[r, r] += 512 - q[r].sum()
    t = post_targets(q)
    if t.min() < -256 or t.max() > 255:
        raise Refused(f'colour matrix after the curves is out of the camera\'s range ({t.min()}..{t.max()})')
    return q


# ------------------------------------------------------------------ fitting
START_SPREAD = dict(matrix=0.1, curve=0.25, after=0.03)   # how far a random start (turns, --seed) may lie
CHANNELS = {'single': [0, 0, 0], 'rg-b': [0, 0, 1], 'r-gb': [0, 1, 1], 'rb-g': [0, 1, 0], 'rgb': [0, 1, 2]}


def _softplus(x):
    import numpy as np
    return np.logaddexp(0, x)


class Fitter:
    """Gradient descent (Adam) on a perceptual colour difference.

    Model: out = P . C[ T(M v) ] with M a white-preserving 3x3 matrix, T the slot's
    base curve, C one, two or three free non-decreasing curves (curve mode) and, with
    post, P a colour mix after the curves (rows sum to 1; otherwise P = I). Loss per colour: a
    CIE94/CIEDE2000-style weighted Lab distance in the target's lightness/chroma/hue
    frame, sqrt'ed so it behaves like ΔE; plus a smoothness penalty on the curves.
    """

    def __init__(self, v, target, mode='single', smooth=50.0, weight=None, post=False):
        import numpy as np
        self.v, self.mode, self.smooth, self.post = v, mode, smooth, post
        w = np.ones(len(v)) if weight is None else np.asarray(weight, float)
        self.w = w / w.sum()                                          # per-colour weights, sum 1
        self.chan = CHANNELS[mode]
        lt = lab(target)
        self.lt = lt
        C = np.hypot(lt[:, 1], lt[:, 2])
        self.u = np.where(C[:, None] > 1e-6, lt[:, 1:] / np.maximum(C, 1e-6)[:, None], [1.0, 0.0])
        self.h = np.stack([-self.u[:, 1], self.u[:, 0]], 1)
        self.SL = 1 + 0.015 * (lt[:, 0] - 50) ** 2 / np.sqrt(20 + (lt[:, 0] - 50) ** 2)
        self.SC, self.SH = 1 + 0.045 * C, 1 + 0.015 * C
        self.T = base_curve('slot')
        self.Tslope = np.diff(self.T)

    def curves(self, raw):
        import numpy as np
        return np.cumsum(_softplus(raw), 1)

    def loss_grad(self, theta, raw, phi=None):
        import numpy as np
        v, N = self.v, len(self.v)
        M = np.concatenate([theta, 1 - theta.sum(1, keepdims=True)], 1)
        z = v @ M.T
        zc = np.clip(z, 0, 255)
        i = np.minimum(np.floor(zc).astype(int), 254)
        f = zc - i
        b = self.T[i] * (1 - f) + self.T[i + 1] * f
        mz = (z > 0) & (z < 255)
        Ck = self.curves(raw)
        Cc = Ck[self.chan]                                           # (3,256)
        idx = np.clip(b * 256, 0, 255)
        j = np.minimum(np.floor(idx).astype(int), 254)
        g = idx - j
        rows = np.arange(3)[None, :]
        c0, c1 = Cc[rows, j], Cc[rows, j + 1]
        out = c0 * (1 - g) + c1 * g
        mi = (b * 256 > 0) & (b * 256 < 255)
        cur = out
        if phi is not None:                                          # colour matrix after the curves
            P = np.concatenate([phi, 1 - phi.sum(1, keepdims=True)], 1)
            out = cur @ P.T
        # Lab of the prediction
        x = np.clip(out, 0, 1)
        lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
        dlin = np.where(x <= 0.04045, 1 / 12.92, 2.4 / 1.055 * ((x + 0.055) / 1.055) ** 1.4) * ((out > 0) & (out < 1))
        t = lin @ np.array(XYZ).T / np.array(WHITE)
        big = t > 216 / 24389
        F = np.where(big, np.cbrt(np.maximum(t, 1e-12)), (24389 / 27 * t + 16) / 116)
        dF = np.where(big, 1 / 3 * np.maximum(t, 1e-12) ** (-2 / 3), 24389 / 27 / 116)
        lp = np.stack([116 * F[:, 1] - 16, 500 * (F[:, 0] - F[:, 1]), 200 * (F[:, 1] - F[:, 2])], 1)
        d = lp - self.lt
        dL = d[:, 0]
        dC = (d[:, 1:] * self.u).sum(1)
        dH = (d[:, 1:] * self.h).sum(1)
        q = (dL / self.SL) ** 2 + (dC / self.SC) ** 2 + (dH / self.SH) ** 2
        e = np.sqrt(q + 1e-8)
        loss = (self.w * e).sum()
        w = self.w / (2 * e)
        gL = w * 2 * dL / self.SL ** 2
        gab = (w * 2)[:, None] * ((dC / self.SC ** 2)[:, None] * self.u + (dH / self.SH ** 2)[:, None] * self.h)
        gLab = np.concatenate([gL[:, None], gab], 1)
        J = np.array([[0, 116, 0], [500, -500, 0], [0, 200, -200]], float)
        gF = gLab @ J
        gt = gF * dF / np.array(WHITE)
        glin = gt @ np.array(XYZ)
        gout = glin * dlin
        gphi = None
        if phi is not None:
            gphi = np.stack([(gout * (cur[:, 0:1] - cur[:, 2:3])).sum(0), (gout * (cur[:, 1:2] - cur[:, 2:3])).sum(0)], 1)
            Y = np.array(HUE_YCC, float) / 256
            YP = Y @ P
            over = np.maximum(np.abs(YP) - POST_LIMIT, 0) * np.sign(YP)
            gP = Y.T @ (2 * HUE_RANGE * over)
            gphi += gP[:, :2] - gP[:, 2:3]
            loss_pen = HUE_RANGE * (over ** 2).sum()
            gout = gout @ P
        # through the look curves
        gC = np.zeros_like(Ck)
        for c in range(3):
            k = self.chan[c]
            np.add.at(gC[k], j[:, c], gout[:, c] * (1 - g[:, c]))
            np.add.at(gC[k], j[:, c] + 1, gout[:, c] * g[:, c])
        gidx = gout * (c1 - c0) * mi
        gz = gidx * 256 * self.Tslope[i] * mz
        gtheta = np.stack([(gz * (v[:, 0:1] - v[:, 2:3])).sum(0), (gz * (v[:, 1:2] - v[:, 2:3])).sum(0)], 1)
        # smoothness penalty
        D = Ck[:, 2:] - 2 * Ck[:, 1:-1] + Ck[:, :-2]
        pen = self.smooth * (D ** 2).sum(1).mean()
        gD = 2 * self.smooth * D / len(Ck)
        gC[:, 2:] += gD
        gC[:, 1:-1] -= 2 * gD
        gC[:, :-2] += gD
        sig = 1 / (1 + np.exp(-raw))
        graw = sig * np.cumsum(gC[:, ::-1], 1)[:, ::-1]
        if phi is not None:
            pen += loss_pen
        return loss + pen, loss, gtheta, graw, gphi

    def run(self, target, iters=1500, lr=5e-3, log=None, init=None, rng=None):
        """init: continue from a fitted look (same curve mode); rng: a random start (a different
        starting point for each seed) instead of the classic one; neither: the classic start."""
        import numpy as np
        v = self.v
        if init is not None:                         # continue from a fitted look (same curve mode)
            M0 = np.array(init['matrix_q13'], float) / 8192
            theta = M0[:, :2].copy()
            first = [self.chan.index(k) for k in range(max(self.chan) + 1)]
            C0 = np.array(init['curves'], float)[first] / 16384
            dd = np.clip(np.diff(np.concatenate([np.zeros((len(C0), 1)), C0], 1), axis=1), 1e-6, None)
            raw = np.log(np.expm1(dd))
            return self._descend(theta, raw, iters, lr, log)
        # least-squares start for the matrix, identity start for the curves
        inv_t = inverse(self.T, target)
        theta = np.zeros((3, 2))
        xr = v[:, :2] - v[:, 2:3]
        for c in range(3):
            theta[c] = np.linalg.lstsq(xr, inv_t[:, c] - v[:, 2], rcond=None)[0]
        if not np.isfinite(theta).all() or np.abs(theta).max() > 3:
            theta = np.array([[1., 0.], [0., 1.], [0., 0.]])
        ident = np.arange(256) / 256.0
        dd = np.clip(np.diff(np.concatenate([[0.0], ident])), 1e-6, None)
        raw = np.tile(np.log(np.expm1(dd)), (max(self.chan) + 1, 1))
        phi = None
        if rng is not None:                      # a random start around the classic one
            theta = theta + rng.normal(0, START_SPREAD['matrix'], theta.shape)
            n = max(self.chan) + 1
            g = np.exp(rng.normal(0, START_SPREAD['curve'], n))[:, None]      # a random gamma per curve
            dd = np.clip(np.diff(np.concatenate([np.zeros((n, 1)), np.tile(ident, (n, 1)) ** g], 1), axis=1), 1e-6, None)
            raw = np.log(np.expm1(dd))
            if self.post:
                phi = np.array([[1., 0.], [0., 1.], [0., 0.]]) + rng.normal(0, START_SPREAD['after'], (3, 2))
        return self._descend(theta, raw, iters, lr, log, phi)

    def _descend(self, theta, raw, iters, lr, log, phi=None):
        import numpy as np
        if self.post and phi is None:
            phi = np.array([[1., 0.], [0., 1.], [0., 0.]])
        elif not self.post:
            phi = None
        params = (theta, raw) + ((phi,) if self.post else ())
        state = [[np.zeros_like(p), np.zeros_like(p)] for p in params]
        hist = []
        for it in range(iters):
            total, loss, gt, gr, gp_ = self.loss_grad(theta, raw, phi)
            a = lr * 0.5 * (1 + math.cos(math.pi * it / iters))
            for p, gp, st in zip(params, (gt, gr, gp_), state):
                st[0] = 0.9 * st[0] + 0.1 * gp
                st[1] = 0.999 * st[1] + 0.001 * gp ** 2
                mh, vh = st[0] / (1 - 0.9 ** (it + 1)), st[1] / (1 - 0.999 ** (it + 1))
                p -= a * mh / (np.sqrt(vh) + 1e-8)
            if it % max(1, iters // 10) == 0 or it == iters - 1:
                hist.append([it, round(float(loss), 4)])
                if log:
                    log(f'    step {it:5d}  loss {loss:.4f}')
        M = np.concatenate([theta, 1 - theta.sum(1, keepdims=True)], 1)
        q = np.round(M * 8192).astype(int)
        q[:, 2] = 8192 - q[:, 0] - q[:, 1]
        Ck = np.clip(np.round(self.curves(raw) * 16384), 0, 16383).astype(int)
        Ck = np.maximum.accumulate(Ck, axis=1)
        out = dict(matrix_q13=q.tolist(), curve_mode=self.mode,
                   curves=[Ck[k].tolist() for k in self.chan], history=hist)
        if self.post:
            out['post_matrix_q9'] = post_quantise(np.concatenate([phi, 1 - phi.sum(1, keepdims=True)], 1)).tolist()
        return out


# ------------------------------------------------------------------ hue sectors
# The camera can change colours separately in 12 ranges of hue, each with its own 3x3 matrix, after the
# look matrix and before the tone curves. The fit keeps neighbouring sectors joined (no gaps between
# colours) and greys unchanged, and keeps colours near a sector edge smooth (HUE_BUDGET).
HUE_BOUNDS = [359.8, 27.4, 62.2, 92.6, 112.0, 142.8, 179.2, 211.4, 238.6, 267.2, 306.0, 326.5]
HUE_SIGMA = [1.0, 2.5, 2.5, 1.0, 1.0, 2.5, 2.5, 2.0, 1.0, 2.0, 5.0, 3.0]
HUE_YCC = [[77, 150, 29], [-43, -85, 128], [128, -107, -21]]          # /256; also for colour after the curves
HUE_KINKS = (0.3, 1, 3, 10, 30, 100)          # seam penalty, weakest first; the first within budget is used
HUE_BUDGET = dict(photo_p99=0.3, photo_max=1.0, lattice_p99=1.0)
HUE_PHOTO_WEIGHTS = (0.5, 2.0, 8.0)          # weights tried for the photo
HUE_RIDGE, HUE_LIMIT, HUE_RANGE = 0.02, 1.85, 1e3   # size penalty; matrix range limit


def _ycc():
    import numpy as np
    S = np.array(HUE_YCC, float) / 256
    return S, np.linalg.inv(S)


def hue_coords(z, bounds):
    """Sector index and position within the sector for each colour z (N,3)."""
    import numpy as np
    S, _ = _ycc()
    bounds = np.asarray(bounds, float)
    ycc = z @ S.T
    ang = np.degrees(np.arctan2(ycc[:, 2], ycc[:, 1])) % 360
    g = np.argmin((ang[:, None] - bounds[None, :]) % 360, 1)
    th0, th1 = np.radians(bounds[g]), np.radians(bounds[(g + 1) % 12])
    det = np.cos(th0) * np.sin(th1) - np.sin(th0) * np.cos(th1)
    cb, cr = ycc[:, 1], ycc[:, 2]
    return g, (cb * np.sin(th1) - cr * np.cos(th1)) / det, (cr * np.cos(th0) - cb * np.sin(th0)) / det


def hue_matrices(D, bounds=None):
    """Per-sector 3x3 matrices for the parameters D (12,3)."""
    import numpy as np
    S, _ = _ycc()
    bounds = HUE_BOUNDS if bounds is None else bounds
    out = []
    for g in range(12):
        th0, th1 = np.radians(bounds[g]), np.radians(bounds[(g + 1) % 12])
        U = np.array([[np.cos(th0), np.cos(th1)], [np.sin(th0), np.sin(th1)]])
        out.append(np.eye(3) + np.stack([D[g], D[(g + 1) % 12]], 1) @ np.linalg.inv(U) @ S[1:])
    return np.array(out)


def hue_quantise(mats):
    import numpy as np
    q = np.rint(mats * 1024).astype(int)
    for g in range(12):
        for r in range(3):
            q[g, r, r] += 1024 - q[g, r].sum()
    if np.abs(q).max() > 2047:
        raise Refused(f'hue-sector matrix value {np.abs(q).max()} is out of range')
    return q


def hue_apply_q(z, q, bounds):
    import numpy as np
    g, _, _ = hue_coords(z, bounds)
    return np.einsum('nij,nj->ni', q[g] / 1024, z)


def hue_kinks():
    """Linear map from the parameters to the smoothness penalty at each sector edge."""
    import numpy as np
    _, S_inv = _ycc()
    th = np.radians(HUE_BOUNDS)
    perp = (S_inv @ np.stack([np.zeros_like(th), -np.sin(th), np.cos(th)])).T
    cols = []
    for k in range(36):
        e = np.zeros(36)
        e[k] = 1
        M = hue_matrices(e.reshape(12, 3))
        cols.append(np.concatenate([(M[b] - M[b - 1]) @ perp[b] for b in range(12)]))
    return np.array(cols).T * np.repeat(HUE_SIGMA, 3)[:, None]


class HueFitter:
    """Adam on the same loss as Fitter, with the look's matrix and curves fixed; parameters D (12,3)."""

    def __init__(self, v, target, weight, look):
        import numpy as np
        self.f = Fitter(v, target, look['curve_mode'] if look.get('curves') else 'single', weight=weight)
        M = np.array(look['matrix_q13'], float) / 8192
        self.z = v @ M.T
        self.g, self.a, self.b = hue_coords(self.z, HUE_BOUNDS)
        cv = look.get('curves')
        self.C = np.array(cv, float) / 16384 if cv else np.tile(np.arange(256) / 256.0, (3, 1))
        pq = look.get('post_matrix_q9')
        self.P = post_effective(pq) if pq else None
        K = hue_kinks()
        self.KtK = K.T @ K
        self.B = np.array([hue_matrices(e.reshape(12, 3)).ravel() - hue_matrices(np.zeros((12, 3))).ravel()
                           for e in np.eye(36)]).T
        self.M0 = hue_matrices(np.zeros((12, 3))).ravel()
        self.kink = HUE_KINKS[0]

    def loss_grad(self, D):
        import numpy as np
        f = self.f
        z = self.z + self.a[:, None] * D[self.g] + self.b[:, None] * D[(self.g + 1) % 12]
        zc = np.clip(z, 0, 255)
        i = np.minimum(np.floor(zc).astype(int), 254)
        fr = zc - i
        bb = f.T[i] * (1 - fr) + f.T[i + 1] * fr
        mz = (z > 0) & (z < 255)
        idx = np.clip(bb * 256, 0, 255)
        j = np.minimum(np.floor(idx).astype(int), 254)
        gg = idx - j
        rows = np.arange(3)[None, :]
        c0, c1 = self.C[rows, j], self.C[rows, j + 1]
        out = c0 * (1 - gg) + c1 * gg
        mi = (bb * 256 > 0) & (bb * 256 < 255)
        if self.P is not None:
            out = out @ self.P.T
        x = np.clip(out, 0, 1)
        lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
        dlin = np.where(x <= 0.04045, 1 / 12.92, 2.4 / 1.055 * ((x + 0.055) / 1.055) ** 1.4) * ((out > 0) & (out < 1))
        t = lin @ np.array(XYZ).T / np.array(WHITE)
        big = t > 216 / 24389
        F = np.where(big, np.cbrt(np.maximum(t, 1e-12)), (24389 / 27 * t + 16) / 116)
        dF = np.where(big, 1 / 3 * np.maximum(t, 1e-12) ** (-2 / 3), 24389 / 27 / 116)
        lp = np.stack([116 * F[:, 1] - 16, 500 * (F[:, 0] - F[:, 1]), 200 * (F[:, 1] - F[:, 2])], 1)
        d = lp - f.lt
        dL, dC, dH = d[:, 0], (d[:, 1:] * f.u).sum(1), (d[:, 1:] * f.h).sum(1)
        e = np.sqrt((dL / f.SL) ** 2 + (dC / f.SC) ** 2 + (dH / f.SH) ** 2 + 1e-8)
        loss = (f.w * e).sum()
        w = f.w / (2 * e)
        gLab = np.concatenate([(w * 2 * dL / f.SL ** 2)[:, None],
                               (w * 2)[:, None] * ((dC / f.SC ** 2)[:, None] * f.u + (dH / f.SH ** 2)[:, None] * f.h)], 1)
        gout = ((gLab @ np.array([[0, 116, 0], [500, -500, 0], [0, 200, -200]], float)) * dF / np.array(WHITE)
                @ np.array(XYZ)) * dlin
        if self.P is not None:
            gout = gout @ self.P
        gz = gout * (c1 - c0) * mi * 256 * f.Tslope[i] * mz
        gD = np.zeros((12, 3))
        np.add.at(gD, self.g, self.a[:, None] * gz)
        np.add.at(gD, (self.g + 1) % 12, self.b[:, None] * gz)
        dv = D.ravel()
        pen = self.kink * (dv @ self.KtK @ dv) / 12 + HUE_RIDGE * (dv @ dv) / 12
        gpen = self.kink * 2 / 12 * (self.KtK @ dv) + HUE_RIDGE * 2 / 12 * dv
        mv = self.M0 + self.B @ dv
        over = np.maximum(np.abs(mv) - HUE_LIMIT, 0)
        pen += HUE_RANGE * (over ** 2).sum()
        gpen += self.B.T @ (HUE_RANGE * 2 * over * np.sign(mv))
        return loss + pen, loss, gD + gpen.reshape(12, 3)

    def run(self, iters=800, lr=0.02):
        import numpy as np
        D = np.zeros((12, 3))
        m1, m2 = np.zeros_like(D), np.zeros_like(D)
        for it in range(iters):
            total, loss, gD = self.loss_grad(D)
            a = lr * 0.5 * (1 + math.cos(math.pi * it / iters))
            m1 = 0.9 * m1 + 0.1 * gD
            m2 = 0.999 * m2 + 0.001 * gD ** 2
            D -= a * (m1 / (1 - 0.9 ** (it + 1))) / (np.sqrt(m2 / (1 - 0.999 ** (it + 1))) + 1e-8)
        return D


def hue_seam_risk(look, y, held):
    """How much colours near sector edges could change (ΔE00), to keep them smooth."""
    import numpy as np
    out = {}
    for name, pts in (('lattice', y), ('photo', held[0] if held else None)):
        if pts is None:
            continue
        v = to_index(pts)
        nom = lab(np.clip(render(v, look), 0, 1))
        e = np.max([de00(nom, lab(np.clip(render(v, look, np.array(HUE_BOUNDS) + sg * np.array(HUE_SIGMA)), 0, 1)))
                    for sg in (-1, 1)], 0)
        out[name] = dict(p99=round(float(np.percentile(e, 99)), 3), max=round(float(e.max()), 3))
    return out


def hue_within_budget(sr):
    ok = sr['lattice']['p99'] <= HUE_BUDGET['lattice_p99']
    if 'photo' in sr:
        ok = ok and sr['photo']['p99'] <= HUE_BUDGET['photo_p99'] and sr['photo']['max'] <= HUE_BUDGET['photo_max']
    return ok


def more_levers_ok(new, old):
    """Accept more levers only for a clear gain (whole range or ColorChecker) with nothing worse."""
    def f(s):
        return dict(e=s['e'], cc=s['cc'], grey=s['grey'], h=s.get('h'))
    n, o = f(new), f(old)
    gain = n['e'] < o['e'] * (1 - PAIR_GAIN) or n['cc'] < o['cc'] * (1 - PAIR_GAIN)
    no_worse = ((o['h'] is None or n['h'] <= o['h'] + HELD_TOL) and n['grey'] <= o['grey'] + GREY_TOL
                and n['cc'] <= o['cc'] + CC_TOL and n['e'] <= o['e'] * (1 + RANGE_TOL))
    return gain and no_worse


def fit_hue(look, v, t, weight, n_lut, y, ty, held, lut, space, iters=800, log=print):
    """Hue sectors on top of a fitted look (matrix and curves kept). Returns the hue_sectors data
    to add to the look, or None when they do not clearly help."""
    import numpy as np

    def summary(lk):
        ev = everyday(lk, lut, space)
        return dict(e=evaluate(lk, y, ty)['de00_mean'], cc=ev['colorchecker']['de00_mean'],
                    grey=ev['greys']['de00_mean'], h=evaluate(lk, *held)['de00_mean'] if held else None)
    base = summary(look)
    candidates = []
    for pw in (HUE_PHOTO_WEIGHTS if held else HUE_PHOTO_WEIGHTS[:1]):
        w = np.asarray(weight, float).copy()
        w[n_lut:] *= pw / PHOTO_WEIGHT
        hf = HueFitter(v, t, w / w.sum(), look)
        for kink in HUE_KINKS:
            hf.kink = kink
            D = hf.run(iters)
            try:
                q = hue_quantise(hue_matrices(D))
            except Refused:
                continue
            cand = dict(look, hue_sectors=dict(matrices_q10=q.tolist()))
            sr = hue_seam_risk(cand, y, held)
            if not hue_within_budget(sr):
                continue
            s = summary(cand)
            ok = more_levers_ok(s, base)
            log(f'  hue     ΔE00 {s["e"]:.3f}' + (f'  photo {s["h"]:.3f}' if s['h'] is not None else '')
                + f'  ColorChecker {s["cc"]:.3f}  greys {s["grey"]:.3f}' + ('' if ok else '  (not better)'))
            if ok:
                candidates.append((s['e'], dict(matrices_q10=q.tolist(), photo_weight=pw, seam_weight=kink,
                                                seam_risk=sr)))
            break
    if not candidates:
        log('  hue sectors: no clear gain, not used')
        return None
    return min(candidates, key=lambda c: c[0])[1]


# ------------------------------------------------------------------ scoring
HUES = {'red': (330, 30), 'orange/skin': (30, 75), 'yellow': (75, 105), 'green': (105, 180),
        'cyan': (180, 240), 'blue': (240, 290), 'purple/magenta': (290, 330)}


def score(pred, target):
    import numpy as np
    lt, lp = lab(target), lab(np.clip(pred, 0, 1))
    e = de00(lt, lp)
    C = np.hypot(lt[:, 1], lt[:, 2])
    h = np.degrees(np.arctan2(lt[:, 2], lt[:, 1])) % 360

    def band(mk):
        return round(float(e[mk].mean()), 3) if mk.sum() >= 20 else None
    r = dict(colours=int(len(e)), de00_mean=round(float(e.mean()), 3), de00_p95=round(float(np.percentile(e, 95)), 3),
             brightness_shift=round(float((lp[:, 0] - lt[:, 0]).mean()), 2),
             hue={k: band((((h >= a) | (h < b)) if a > b else ((h >= a) & (h < b))) & (C >= 10))
                  for k, (a, b) in HUES.items()})
    r['verdict'] = 'good' if r['de00_mean'] < 1 and r['de00_p95'] < 2 else \
        'approximate' if r['de00_mean'] < 2 and r['de00_p95'] < 4 else 'poor'
    return r


def evaluate(look, y, target):
    return score(render(to_index(y), look), target)


def unchanged(y, target):
    """How far the LUT is from the camera's neutral rendering (no look at all)."""
    return score(neutral(to_index(y)), target)


# ------------------------------------------------------------------ photos (optional)
def photo_signal(dng, max_side=400):
    """Linear signal of a DNG in the camera model's units (needs rawpy)."""
    import numpy as np
    try:
        import rawpy
    except ImportError:
        raise Refused('--photo / preview need rawpy and pillow: python3 -m pip install rawpy pillow')
    with rawpy.imread(str(dng)) as r:
        img = r.raw_image_visible.astype(np.float32)
        s = r.sizes
        black = np.array(r.black_level_per_channel, np.float32)
        white = float(r.white_level)
        cl = r.raw_colors_visible
        wb = np.array(r.camera_whitebalance[:3], float)
    if s.crop_height and s.crop_width:
        t, l = s.crop_top_margin, s.crop_left_margin
        img, cl = img[t:t + s.crop_height, l:l + s.crop_width], cl[t:t + s.crop_height, l:l + s.crop_width]
    img = (img - black[cl]) / (white - black[cl])
    h, w = img.shape[0] // 2 * 2, img.shape[1] // 2 * 2
    q = img[:h, :w].reshape(h // 2, 2, w // 2, 2).transpose(0, 2, 1, 3).reshape(h // 2, w // 2, 4)
    qc = cl[:2, :2].reshape(4)
    rgb = np.stack([q[..., [k for k in range(4) if qc[k] in idx]].mean(-1) for idx in ([0], [1, 3], [2])], -1)
    f = max(1, int(np.ceil(max(rgb.shape[:2]) / max_side)))
    H, W = rgb.shape[0] // f * f, rgb.shape[1] // f * f
    rgb = rgb[:H, :W].reshape(H // f, f, W // f, f, 3).mean((1, 3))
    yy, xx = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
    r2 = ((yy - rgb.shape[0] / 2) / (rgb.shape[0] / 2)) ** 2 + ((xx - rgb.shape[1] / 2) / (rgb.shape[1] / 2)) ** 2
    cam = rgb * (wb / wb[1]) * np.exp(0.18 * r2)[..., None]
    return cam @ (np.array(DATA['camera_matrix']) / 8192).T * 100.0


def neutral(v):
    """The camera's neutral rendering of a linear signal (no look)."""
    import numpy as np
    T = base_curve('neutral')
    return np.stack([np.interp(np.clip(v[..., c], 0, 255), np.arange(256.), T) for c in range(3)], -1)


def apply_lut(lut, y, space):
    if space == 'adobe':
        return adobe_lut_on_srgb(lut, y)[0]
    return lut(y)


# ------------------------------------------------------------------ fit command
PAIR_GAIN, HELD_TOL, PHOTO_GAIN = 0.10, 0.02, 0.5
PHOTO_WEIGHT = 0.5      # the photo counts half as much as the LUT's own colours, however many pixels it has
GREY_WEIGHT = 0.5       # neutral greys count half as much too: a colour cast on greys is the most visible error
GREY_TOL, CC_TOL = 0.10, 0.10            # more levers must not make greys or the ColorChecker worse by more;
                                         # these, RANGE_TOL and HELD_TOL are also the margins when comparing results
GREY_GAIN, RANGE_TOL = 0.5, 0.05         # ... and count as a gain when greys improve by 0.5 (range within 5 %)
EVERYDAY_CC, EVERYDAY_GREY, EVERYDAY_CAST = 2.0, 2.0, 2.5
# "good on everyday colours": ColorChecker mean < 2 and greys < 2 (a small visible difference at most),
# and no visible colour cast on any grey (largest a*b* difference < 2.5)

# X-Rite ColorChecker Classic, widely published sRGB values (8-bit): everyday reference colours
COLORCHECKER = [
    ('dark skin', 115, 82, 68), ('light skin', 194, 150, 130), ('blue sky', 98, 122, 157),
    ('foliage', 87, 108, 67), ('blue flower', 133, 128, 177), ('bluish green', 103, 189, 170),
    ('orange', 214, 126, 44), ('purplish blue', 80, 91, 166), ('moderate red', 193, 90, 99),
    ('purple', 94, 60, 108), ('yellow green', 157, 188, 64), ('orange yellow', 224, 163, 46),
    ('blue', 56, 61, 150), ('green', 70, 148, 73), ('red', 175, 54, 60), ('yellow', 231, 199, 31),
    ('magenta', 187, 86, 149), ('cyan', 8, 133, 161), ('white', 243, 243, 242), ('neutral 8', 200, 200, 200),
    ('neutral 6.5', 160, 160, 160), ('neutral 5', 122, 122, 121), ('neutral 3.5', 85, 85, 85), ('black', 52, 52, 52)]


def greys(n=64):
    import numpy as np
    x = np.linspace(0.02, 1.0, n)
    return np.stack([x, x, x], 1)


def everyday(look, lut, space):
    """Scores on the ColorChecker and on a neutral grey ramp (with the largest colour cast on the greys)."""
    import numpy as np
    out = {}
    for name, y in (('colorchecker', np.array([c[1:] for c in COLORCHECKER], float) / 255), ('greys', greys())):
        t = apply_lut(lut, y, space)
        lt, lp = lab(t), lab(np.clip(render(to_index(y), look), 0, 1))
        e = de00(lt, lp)
        r = dict(de00_mean=round(float(e.mean()), 3), de00_max=round(float(e.max()), 3))
        if name == 'colorchecker':
            r['worst'] = COLORCHECKER[int(e.argmax())][0]
            r['skin'] = round(float(e[:2].mean()), 3)
        else:
            r['cast_max'] = round(float(np.hypot(*(lp[:, 1:] - lt[:, 1:]).T).max()), 2)
        out[name] = r
    return out


def fit_lut(path, space='srgb', curve='auto', photo=None, iters=1500, log=print, hue=True, post=False, seed=None):
    """One turn of fitting. seed None: the classic start; a number: a random start (reproducible).
    With post, the result also carries 'after_curves': the version with colour after the curves, when it
    is better than the usual one on at least one measure."""
    import numpy as np
    rng = None if seed is None else np.random.default_rng(seed)
    lut = Lut(path)
    if lut.lo.tolist() == [0, 0, 0] and lut.hi.tolist() == [1, 1, 1]:
        y = grid(lut.n)
    else:
        y = grid(33)
    if space == 'adobe':
        t, keep = adobe_lut_on_srgb(lut, y)
        y, t = y[keep], t[keep]
    else:
        t = lut(y)
    log(f'{Path(path).name}: {lut.kind} LUT, {len(y)} colours, {space}'
        + (f' (ignored: {", ".join(sorted(set(lut.ignored)))})' if lut.ignored else ''))
    ty = t
    gy = greys()
    v = np.concatenate([to_index(y), to_index(gy)])
    t = np.concatenate([t, apply_lut(lut, gy, space)])
    weight = np.concatenate([np.ones(len(y)) / len(y), np.full(len(gy), GREY_WEIGHT / len(gy))])
    held = None
    n_fixed = len(v)
    if photo:
        img = photo_signal(photo)
        top = np.zeros(img.shape[:2], bool)
        top[: img.shape[0] // 2] = True
        pv, top = img.reshape(-1, 3), top.ravel()
        yb = neutral(pv)
        ok = (yb.max(1) < 0.98) & (yb.min(1) > 0.01)
        tb = apply_lut(lut, yb, space)
        n_photo = int((ok & top).sum())
        v = np.concatenate([v, pv[ok & top]])
        t = np.concatenate([t, tb[ok & top]])
        weight = np.concatenate([weight, np.full(n_photo, PHOTO_WEIGHT / max(n_photo, 1))])
        held = (yb[ok & ~top], tb[ok & ~top])
        log(f'  photo: {int((ok & top).sum())} pixels join the fit, {int((ok & ~top).sum())} are held out')

    def one(mode, post=False, photo_weight=PHOTO_WEIGHT, init=None):
        w = weight
        if photo_weight != PHOTO_WEIGHT:                 # the photo and the greys together (everyday content)
            w = np.asarray(weight, float).copy()
            w[n_fixed - len(gy):] *= photo_weight / PHOTO_WEIGHT
        try:
            look = Fitter(v, t, mode, weight=w, post=post).run(t, iters=iters, init=init, rng=None if init else rng,
                                                              lr=5e-3 if init is None else POST_WARM_LR)
        except Refused as exc:
            log(f'  {mode} + colour after the curves: {exc}')
            return None
        e = evaluate(look, y, ty)['de00_mean']
        h = evaluate(look, *held)['de00_mean'] if held else None
        ev = everyday(look, lut, space)
        log(f'  {mode + (f" + after (photo {photo_weight}{"" if init else ", from scratch"})" if post else ""):7s} ΔE00 {e:.3f}' + (f'  photo {h:.3f}' if h is not None else '')
            + f'  ColorChecker {ev["colorchecker"]["de00_mean"]:.3f}  greys {ev["greys"]["de00_mean"]:.3f}')
        return dict(e=e, h=h, cc=ev['colorchecker']['de00_mean'], grey=ev['greys']['de00_mean'], look=look)
    def better(new, old):
        """More levers (curves, colour after the curves) only when they clearly help (whole range,
        everyday colours or greys) and make nothing worse (photo, greys, ColorChecker, whole range)."""
        gain = (new['e'] < old['e'] * (1 - PAIR_GAIN) or new['cc'] < old['cc'] * (1 - PAIR_GAIN)
                or new['grey'] <= old['grey'] - GREY_GAIN)
        no_worse = ((old['h'] is None or new['h'] <= old['h'] + HELD_TOL) and new['grey'] <= old['grey'] + GREY_TOL
                    and new['cc'] <= old['cc'] + CC_TOL and new['e'] <= old['e'] * (1 + RANGE_TOL))
        return gain and no_worse
    if curve == 'auto':
        use = one('single')
        p = min((one(m) for m in ('rg-b', 'r-gb', 'rb-g')), key=lambda r: r['e'])
        if better(p, use):
            use = p
        t3 = one('rgb')
        if better(t3, use):
            use = t3
    elif curve == 'pair':
        use = min((one(m) for m in ('rg-b', 'r-gb', 'rb-g')), key=lambda r: r['e'])
    else:
        use = one(curve)

    def with_hue(lk):
        if hue:
            sectors = fit_hue(lk, v, t, weight, n_fixed, y, ty, held, lut, space, log=log)
            if sectors:
                lk = dict(lk, hue_sectors=sectors)
        return lk

    def summary(lk):
        ev = everyday(lk, lut, space)
        return dict(e=evaluate(lk, y, ty)['de00_mean'], h=evaluate(lk, *held)['de00_mean'] if held else None,
                    cc=ev['colorchecker']['de00_mean'], grey=ev['greys']['de00_mean'], look=lk)
    look = with_hue(use['look'])
    alt = None
    if post:                    # a colour matrix after the curves: a second version when it improves anything
        found = []
        starts = [(pw, use['look']) for pw in (POST_PHOTO_WEIGHTS if held else POST_PHOTO_WEIGHTS[:1])]
        for pw, init in starts + [(PHOTO_WEIGHT, None)]:      # from the fitted look, and once from scratch
            p = one(use['look']['curve_mode'], post=True, photo_weight=pw, init=init)
            if p:
                found.append(p)
        pool = [p for p in found if better(p, use)] or [p for p in found if changes(p, use)[0]]
        if pool:
            final, base = summary(with_hue(min(pool, key=lambda r: r['e'])['look'])), summary(look)
            gained, lost = changes(final, base)
            if gained:
                alt = dict(look=final['look'], recommended=better(final, base), better=gained, worse=lost)
        if alt:
            log(f'  colour after the curves: better {", ".join(alt["better"])}'
                + (f'; worse {", ".join(alt["worse"])}' if alt['worse'] else '')
                + ('  (recommended)' if alt['recommended'] else ''))
        else:
            log('  colour after the curves: no gain, not kept')

    def record(lk):
        scores = dict(fit=evaluate(lk, y, ty), unchanged=unchanged(y, ty), **everyday(lk, lut, space))
        if held:
            scores['photo'] = evaluate(lk, *held)
            scores['photo_unchanged'] = unchanged(*held)
        scores['fit_score'] = fit_score(lk, v, t, weight)
        ok, why = decide(scores)
        return dict(tool=f'GR4-LUTSmith {VERSION}', seed=seed,
                    lut=dict(file=str(Path(path).resolve()), sha256=lut.sha256,
                             kind=lut.kind, title=lut.title, space=space),
                    matrix_q13=lk['matrix_q13'], curve_mode=lk['curve_mode'], curves=lk['curves'],
                    hue_sectors=lk.get('hue_sectors'), post_matrix_q9=lk.get('post_matrix_q9'),
                    scores=scores, decision=dict(build=ok, reason=why), fit=dict(iters=iters, history=lk['history']))
    out = record(look)
    if alt:
        out['after_curves'] = dict(record(alt['look']), recommended=alt['recommended'],
                                   compared=dict(better=alt['better'], worse=alt['worse']))
    return out


def fit_score(look, v, t, weight):
    """What the fit itself aims at: the weighted average ΔE00 over the LUT's colours, the greys and the part
    of the photo used for fitting (the other part of the photo stays a fair check)."""
    import numpy as np
    w = np.asarray(weight, float)
    return round(float((w * de00(lab(t), lab(np.clip(render(v, look), 0, 1)))).sum() / w.sum()), 4)


MEASURES = (('e', 'whole range'), ('cc', 'ColorChecker'), ('grey', 'greys'), ('h', 'photo'))


def changes(new, old):
    """Measures that got clearly better / worse: by more than RANGE_TOL (relative), CC_TOL, GREY_TOL or HELD_TOL."""
    tol = dict(e=old['e'] * RANGE_TOL, cc=CC_TOL, grey=GREY_TOL, h=HELD_TOL)
    better = [name for k, name in MEASURES if old.get(k) is not None and new[k] < old[k] - tol[k]]
    worse = [name for k, name in MEASURES if old.get(k) is not None and new[k] > old[k] + tol[k]]
    return better, worse


def decide(scores):
    """Build when the LUT's whole colour range fits, or when everyday colours do."""
    f = scores['fit']
    if f['verdict'] != 'poor':
        return True, f'fit {f["verdict"]}'
    cc, gr = scores['colorchecker'], scores['greys']
    p, p0 = scores.get('photo'), scores.get('photo_unchanged')
    photo_ok = p is None or (p['verdict'] != 'poor' and p['de00_mean'] <= p0['de00_mean'])
    no_cast = gr['de00_mean'] < EVERYDAY_GREY and gr['cast_max'] < EVERYDAY_CAST
    if cc['de00_mean'] < EVERYDAY_CC and no_cast and photo_ok:
        return True, (f'everyday colours fit (ColorChecker {cc["de00_mean"]}, greys {gr["de00_mean"]}, '
                      f'largest cast {gr["cast_max"]}); only extreme saturated colours deviate')
    if p and p['verdict'] == 'good' and p['de00_mean'] <= PHOTO_GAIN * p0['de00_mean'] and no_cast:
        return True, f'fit poor on extreme colours, but good on your photo ({p["de00_mean"]} vs {p0["de00_mean"]})'
    return False, (f'fit poor; ColorChecker {cc["de00_mean"]}, greys {gr["de00_mean"]} '
                   f'(largest cast {gr["cast_max"]})'
                   + (f'; photo {p["de00_mean"]} vs unchanged {p0["de00_mean"]}' if p else ''))


def describe(look, log=print):
    s = look['scores']
    f = s['fit']
    log(f'  result: {f["verdict"].upper()}  (ΔE00 {f["de00_mean"]}, p95 {f["de00_p95"]}; '
        f'without the look {s["unchanged"]["de00_mean"]})')
    if 'photo' in s:
        log(f'  on your photo: ΔE00 {s["photo"]["de00_mean"]} (without the look {s["photo_unchanged"]["de00_mean"]})')
    worst = sorted(((v, k) for k, v in f['hue'].items() if v is not None), reverse=True)[:3]
    log('  hardest colours: ' + ', '.join(f'{k} {v}' for v, k in worst))
    cc, gr = s.get('colorchecker'), s.get('greys')
    if cc and gr:
        log(f'  everyday colours: ColorChecker ΔE00 {cc["de00_mean"]} (skin {cc["skin"]}, worst {cc["worst"]}); '
            f'greys {gr["de00_mean"]} (largest cast {gr["cast_max"]})')
    hs = look.get('hue_sectors')
    log(f'  for: {SLOT_NAMES.get(look.get("slot") or DEFAULT_SLOT, "?")}; curves: {look["curve_mode"]}; '
        f'hue sectors: {"yes" if hs else "no"}; '
        f'colour after the curves: {"yes" if look.get("post_matrix_q9") else "no"}; decision: {look["decision"]["reason"]}')


TURNS_DIR = 'turns'           # every kept result gets a folder here when there is more than one


def measures(rec):
    sc = rec['scores']
    return dict(e=sc['fit']['de00_mean'], cc=sc['colorchecker']['de00_mean'], grey=sc['greys']['de00_mean'],
                h=sc['photo']['de00_mean'] if 'photo' in sc else None)


def keep(kept, new):
    """The list of results worth keeping. A new result joins unless a kept one is at least as good on every
    measure; kept results that the new one beats on every measure leave the list.
    Returns (list, joined, results that left)."""
    m = measures(new)
    if any(not changes(m, measures(k))[0] for k in kept):
        return kept, False, []
    stay = [k for k in kept if changes(measures(k), m)[0]]
    return stay + [new], True, [k for k in kept if not any(k is x for x in stay)]


def result_name(rec):
    return f'turn-{rec["turn"]}' + ('-after-curves' if rec.get('post_matrix_q9') else '')


def recommended(kept):
    """The kept result the fit itself scores best (see fit_score)."""
    return min(kept, key=lambda r: r['scores']['fit_score'])


def show_kept(kept, log=print):
    best = recommended(kept)
    log(f'\n  kept results ({len(kept)}), ΔE00, lower is closer to the LUT:')
    log(f'    {"result":24s} {"whole range":>11s} {"ColorChecker":>12s} {"greys":>6s} {"photo":>6s} {"fit score":>9s}')
    for r in sorted(kept, key=lambda r: r['scores']['fit_score']):
        m = measures(r)
        log(f'    {result_name(r):24s} {m["e"]:11.2f} {m["cc"]:12.2f} {m["grey"]:6.2f} '
            + (f'{m["h"]:6.2f}' if m['h'] is not None else f'{"-":>6s}')
            + f' {r["scores"]["fit_score"]:9.3f}' + ('   recommended' if r is best else ''))
    if len(kept) > 1:
        log('  each kept result is better than every other one on at least one measure; the recommended one has\n'
            '  the best fit score. Preview them on your own photo and pick the one you like.')


def run_turns(a, n, state, post, log=print):
    """Run n more turns (post: with colour after the curves) and update state (kept list, history, seeds)."""
    import secrets
    for _ in range(n):
        k = len(state['history_turns']) + 1
        if a.seed is not None:
            seed = a.seed + k - 1
        else:
            seed = None if k == 1 else secrets.randbelow(2 ** 31)
        log(f'\nturn {k} ({"classic start" if seed is None else f"random start, seed {seed}"}'
            + (', with colour after the curves)' if post else ')'))
        res = fit_lut(a.lut, a.space, a.curve, a.photo, a.iters, hue=not a.no_hue, post=post, seed=seed)
        alt = res.pop('after_curves', None)
        state['history_turns'].append(dict(seed=seed, after_curves=post))
        for rec in (res, alt):
            if rec is None:
                continue
            for x in ('recommended', 'compared'):
                rec.pop(x, None)
            rec['turn'] = k
            rec['slot'] = a.slot
            state['kept'], joined, left = keep(state['kept'], rec)
            state['history'].append(dict(result=result_name(rec), seed=seed, kept_when_found=joined,
                                         fit_score=rec['scores']['fit_score'], **measures(rec)))
            log(f'  {result_name(rec)}: ' + ('kept' if joined else 'not kept (an earlier result is at least as good '
                                                                   'on every measure)'))
            for x in left:
                log(f'  {result_name(x)} leaves the list ({result_name(rec)} is better on every measure)')


def ask_more_turns(post):
    """Ask for more turns when someone is at the terminal. Returns (number, with colour after the curves);
    0 means stop. A plain number runs turns as the run started (post); 'a' adds turns with colour after the curves,
    'b' turns without it (before the curves only)."""
    if not sys.stdin.isatty():
        return 0, post
    while True:
        try:
            ans = input('\nMore turns? Type a number (e.g. 2), add "a" for turns with colour after the curves (2a) '
                        'or "b" for turns without it (2b); or press Enter to keep these results: ').strip().lower()
        except EOFError:
            return 0, post
        if not ans:
            return 0, post
        kind = ans[-1] if ans[-1] in 'ab' else ''
        num = ans[:-1].strip() if kind else ans
        if num.isdigit():
            return int(num), (post if not kind else kind == 'a')
        print('please type a whole number, optionally followed by a or b, or press Enter')


def load_look(path):
    look = json.loads(Path(path).read_text())
    if 'look' in look and 'matrix_q13' not in look:         # look files written by earlier tools
        look = dict(look['look'], scores=look.get('scores'))
    for k in ('matrix_q13',):
        if k not in look:
            raise Refused(f'{path}: not a look file')
    return look


# ------------------------------------------------------------------ preview
def preview(look, dng, out, lut_path=None, space='srgb'):
    import numpy as np
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise Refused('preview needs pillow: python3 -m pip install rawpy pillow')
    v = photo_signal(dng, max_side=1200)
    flat = v.reshape(-1, 3)
    panels = [neutral(flat)]
    labels = ['camera, no look']
    if lut_path and Path(lut_path).exists():
        panels.append(apply_lut(Lut(lut_path), panels[0], space))
        labels.append('LUT')
    panels.append(render(flat, look))
    labels.append('camera with the look')
    ims = [Image.fromarray((np.clip(p.reshape(v.shape), 0, 1) * 255 + 0.5).astype(np.uint8)) for p in panels]
    w, h = ims[0].size
    sheet = Image.new('RGB', (len(ims) * w + 8 * (len(ims) - 1), h + 28), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for k, (im, text) in enumerate(zip(ims, labels)):
        sheet.paste(im, (k * (w + 8), 28))
        d.text((k * (w + 8) + 6, 8), text, fill=(230, 230, 230))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=92)
    return out


# ------------------------------------------------------------------ main
def need_numpy():
    try:
        import numpy  # noqa: F401
    except ImportError:
        raise Refused('this command needs numpy: python3 -m pip install numpy')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='gr4_lutsmith.py', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', action='version', version=VERSION)
    sub = ap.add_subparsers(dest='cmd', required=True)

    def lut_args(p):
        p.add_argument('lut', type=Path, help='.cube file (3D or 1D)')
        p.add_argument('--space', choices=('srgb', 'adobe'), default='srgb',
                       help='colour space the LUT was made for (default srgb)')
        p.add_argument('--photo', type=Path, help='a DNG from your GR IV: judges the fit on real content (needs rawpy)')
        p.add_argument('--curve', choices=('auto', 'single', 'pair', 'rgb'), default='auto', help=argparse.SUPPRESS)
        p.add_argument('--no-hue', action='store_true', help='do not use hue sectors (colour changes per hue)')
        p.add_argument('--slot', choices=tuple(SLOT_NAMES), default=DEFAULT_SLOT,
                       help='which Image Control look to replace with yours (default high-contrast)')
        p.add_argument('--turns', type=int, default=1,
                       help='how many fits to run; each extra turn starts from a new random point (default 1)')
        p.add_argument('--seed', type=int, help='run turns from this seed (repeats a turn shown earlier)')
        p.add_argument('--after-curves', action='store_true',
                       help='also try a colour mix after the tone curves; keeps a second version when it helps')
        p.add_argument('--iters', type=int, default=1500, help=argparse.SUPPRESS)
    m = sub.add_parser('make', help='LUT + official firmware -> firmware with the look')
    lut_args(m)
    m.add_argument('input', type=Path, help='official RICOH fwdc248b.bin (GR IV 1.11)')
    m.add_argument('--force', action='store_true', help='build even if the fit is poor')
    m.add_argument('-o', '--output-dir', type=Path)
    f = sub.add_parser('fit', help='fit a LUT only (writes look.json)')
    lut_args(f)
    f.add_argument('-o', '--output-dir', type=Path)
    b = sub.add_parser('build', help='look.json file(s) + official firmware -> firmware with the look(s)')
    b.add_argument('looks', type=Path, nargs='+', metavar='look.json',
                   help='one look per slot (each look.json says its slot)')
    b.add_argument('input', type=Path, help='official RICOH fwdc248b.bin (GR IV 1.11)')
    b.add_argument('-o', '--output-dir', type=Path)
    p = sub.add_parser('preview', help='render a DNG with the look (needs rawpy, pillow)')
    p.add_argument('look', type=Path)
    p.add_argument('photo', type=Path)
    p.add_argument('-o', '--output', type=Path)
    sub.add_parser('slots', help='list the Image Control looks yours can replace (--slot)')
    c = sub.add_parser('check', help='identify a fwdc248b.bin and validate its container')
    c.add_argument('input', type=Path)
    s = sub.add_parser('selftest', help='build the bundled example and compare with the verified result')
    s.add_argument('input', type=Path)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)
    if sys.version_info < (3, 8):
        print('Python 3.8 or newer is required', file=sys.stderr)
        return 2
    try:
        if a.cmd == 'check':
            return identify(a.input.read_bytes())
        if a.cmd == 'slots':
            list_slots()
            return 0
        print(f'GR4-LUTSmith {VERSION}')
        if a.cmd == 'selftest':
            look = load_look(Path(__file__).resolve().parent / SELFTEST_LOOK)
            out = make_firmware(a.input.read_bytes(), look)
            ok = sha256(out) == SELFTEST_SHA256
            print(f'selftest: {"PASSED" if ok else "FAILED"} (SHA-256 {sha256(out)})')
            return 0 if ok else 1
        need_numpy()
        if a.cmd == 'preview':
            look = load_look(a.look)
            lut = look.get('lut', {})
            src = lut.get('file') if lut else None
            out = preview(look, a.photo, a.output or a.look.with_name('preview.jpg'), src, lut.get('space', 'srgb'))
            print(f'wrote {out}')
            return 0
        if a.cmd in ('make', 'fit'):
            out_dir = a.output_dir or Path('output') / a.lut.stem
            if a.cmd == 'make':
                source = a.input.read_bytes()
                if sha256(source) != OFFICIAL_SHA256:
                    make_firmware(source, dict(matrix_q13=[[8192, 0, 0], [0, 8192, 0], [0, 0, 8192]]))
                if (out_dir / 'fwdc248b.bin').exists() or (out_dir / TURNS_DIR).exists():
                    raise Refused(f'{out_dir} already has results; choose another output directory')
            if a.turns < 1:
                raise Refused('--turns must be at least 1')
            print(f'slot: {slot_line(a.slot)}')
            state = dict(kept=[], history=[], history_turns=[])
            n, post = a.turns, a.after_curves
            while n:
                run_turns(a, n, state, post)
                show_kept(state['kept'])
                n, post = ask_more_turns(a.after_curves)
            kept, best = state['kept'], recommended(state['kept'])
            print(f'\nrecommended: {result_name(best)}')
            describe(best)
            places = [(best, out_dir)]
            if len(kept) > 1:
                places += [(r, out_dir / TURNS_DIR / result_name(r)) for r in kept]
            for r, d in places:
                d.mkdir(parents=True, exist_ok=True)
                (d / 'look.json').write_text(json.dumps(r, indent=1) + '\n')
            if len(state['history']) > 1:
                (out_dir / 'turns.json').write_text(json.dumps(dict(
                    turns=[dict(turn=i + 1, **t) for i, t in enumerate(state['history_turns'])],
                    results=state['history'], kept=[result_name(r) for r in kept],
                    recommended=result_name(best)), indent=1) + '\n')
            print(f'wrote {out_dir / "look.json"}' + (f' (and {len(kept)} kept results in {out_dir / TURNS_DIR})'
                                                     if len(kept) > 1 else ''))
            if a.cmd == 'fit':
                return 0
            build = [(r, d) for r, d in places if r['decision']['build'] or a.force]
            if not build:
                raise Refused('the LUT cannot be reproduced well by the camera (see above); '
                              'use --force to build anyway')
            for r, d in places:
                if not (r['decision']['build'] or a.force):
                    print(f'not built: {d} (the camera cannot reproduce this result well; --force builds it)')
            made = {}
            for r, d in build:
                if id(r) not in made:                          # the recommended result is also in turns/
                    made[id(r)] = make_firmware(source, r)
                data = made[id(r)]
                target = write_atomic(data, d)
                print(f'wrote {target}  (SHA-256 {sha256(data)})')
            print(('Copy one of these files' if len(build) > 1 else 'Copy this file')
                  + ' to the root of the SD card and run the camera\'s firmware update.\n'
                  + f'Then choose {SLOT_NAMES[a.slot]} in Image Control: your look is there.')
            return 0
        if a.cmd == 'build':
            looks = [load_look(x) for x in a.looks]
            for x, lk in zip(a.looks, looks):
                print(f'{x}: {slot_line(look_slot(lk))}')
            out_dir = a.output_dir or a.looks[0].parent
            data = make_firmware(a.input.read_bytes(), looks)
            target = write_atomic(data, out_dir)
            print(f'wrote {target}  (SHA-256 {sha256(data)})')
            names = [SLOT_NAMES[n] for n in SLOT_ORDER if n in {look_slot(lk) for lk in looks}]
            print('Copy this file to the root of the SD card and run the camera\'s firmware update.\n'
                  + ('Then choose ' + names[0] + ' in Image Control: your look is there.' if len(names) == 1 else
                     'Your looks are on: ' + ', '.join(names) + '.'))
            return 0
    except Refused as exc:
        print(f'refused: {exc}', file=sys.stderr)
        print('nothing was written.' if a.cmd in ('make', 'build', 'selftest') else '', file=sys.stderr)
        return 1
    except OSError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
