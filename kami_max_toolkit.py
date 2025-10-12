#!/usr/bin/env python3
# kami_max_toolkit.py
# All-in-one toolkit: QR, Video DL, Audio stego, Image stego, Kamix Hollywood, Termux Chat
# Save as kami_max_toolkit.py and run with: python3 kami_max_toolkit.py

import os
import sys
import time
import base64
import json
import random
import socket
import threading
import struct
from pathlib import Path
from getpass import getpass
from secrets import token_bytes
import hashlib
import subprocess
import queue

# ---------------- optional imports ----------------
# Pillow for images
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_OK = True
except Exception:
    PIL_OK = False

# qrcode for generating qrcodes
try:
    import qrcode
    QRGEN_OK = True
except Exception:
    QRGEN_OK = False

# pyzbar for scanning qr images
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_OK = True
except Exception:
    PYZBAR_OK = False

# yt-dlp check
from shutil import which
YT_DLP_CMD = "yt-dlp"
YTDLP_OK = which(YT_DLP_CMD) is not None

# ffmpeg presence
FFMPEG_OK = which("ffmpeg") is not None

# --------------------------------------------------
def press_enter():
    input("\nPress Enter to continue...")

# ---------------- QR TOOL ----------------
def qr_menu():
    while True:
        print("\n=== QR Tool ===")
        print("1) Generate QR (link -> PNG)")
        print("2) Scan QR from image (PNG/JPG)")
        print("3) Emoji Hash encode/decode")
        print("4) Back to main menu")
        ch = input("Choose (1-4): ").strip()
        if ch == "1":
            if not QRGEN_OK or not PIL_OK:
                print("\n[!] qrcode or Pillow not installed. Install with:")
                print("    pip install qrcode[pil] pillow")
                press_enter()
                continue
            link = input("Enter link or text: ").strip()
            watermark = input("Watermark (optional): ").strip() or "KamixChatGPT"
            make_qr(link, watermark)
        elif ch == "2":
            if not PYZBAR_OK or not PIL_OK:
                print("\n[!] pyzbar or Pillow not installed. Install with:")
                print("    pip install pyzbar pillow")
                print("Also ensure system zbar library is present (Termux: pkg install zbar)")
                press_enter()
                continue
            path = input("Image path: ").strip()
            scan_qr_image(path)
        elif ch == "3":
            emoji_hash_menu()
        elif ch == "4":
            break
        else:
            print("Invalid choice.")

# QR generation and scanning
def make_qr(link, watermark="KamixChatGPT"):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    # watermark
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    bbox = draw.textbbox((0,0), watermark, font=font) if font else (0,0,len(watermark),1)
    text_w = bbox[2]-bbox[0]
    text_h = bbox[3]-bbox[1]
    pos = (img.size[0]-text_w-6, img.size[1]-text_h-6)
    draw.text(pos, watermark, fill=(255,0,0), font=font)
    out = "qr_code.png"
    img.save(out)
    print(f"\n✅ QR saved as {out}")

def scan_qr_image(path):
    if not os.path.exists(path):
        print("File not found.")
        return
    img = Image.open(path)
    res = pyzbar_decode(img)
    if not res:
        print("No QR code found.")
        return
    for r in res:
        try:
            data = r.data.decode("utf-8")
        except Exception:
            data = str(r.data)
        print("\n🔍 QR Data:", data)

# ---------------- Emoji Hash tool ----------------
EMOJIS = list("😀😁😂🤣😃😄😅😆😉😊😎😍🤩🤔🤨😐😑😶🙄😏😣😥😮😯😪😫😴😌😛😜🤪😝🤗🤭🤫🤥😳🥺😢😭😤😠😡🤬🤯🥵🥶🥴🥳🤠🤡🥸🤖👻💀💩🤝🙌👋🤙👍👎✌🤞✋🖐👊👏🔥🌙⭐☀🌈⚡🍎🍌🍇🍓🍒🍍🥭🍑🍉🍊🥝🥑")
def encode_text_to_emoji(text):
    b64 = base64.b64encode(text.encode()).decode()
    mapping = {}
    used = set()
    for ch in set(b64):
        e = random.choice([em for em in EMOJIS if em not in used])
        mapping[ch] = e
        used.add(e)
    emoji_seq = "".join(mapping[c] for c in b64)
    return mapping, emoji_seq

def decode_emoji_to_text(mapping, emoji_seq):
    rev = {v:k for k,v in mapping.items()}
    b64 = "".join(rev.get(e, "") for e in emoji_seq)
    while len(b64) % 4 != 0:
        b64 += "="
    try:
        return base64.b64decode(b64).decode(errors="ignore")
    except Exception:
        return ""

def emoji_hash_menu():
    while True:
        print("\n=== Emoji Hash ===")
        print("1) Encode text -> emoji hash")
        print("2) Decode emoji hash -> text")
        print("3) Back")
        ch = input("Choose (1-3): ").strip()
        if ch == "1":
            txt = input("Text to encode: ")
            mapping, seq = encode_text_to_emoji(txt)
            out = "🔑KamixChatGPT:" + json.dumps(mapping, ensure_ascii=False) + "🔑" + seq
            print("\nEmoji Hash:")
            print(out)
            press_enter()
        elif ch == "2":
            data = input("Paste emoji hash: ").strip()
            try:
                parts = data.split("🔑")
                mapping_str = parts[1].replace("KamixChatGPT:", "")
                seq = parts[2].strip()
                mapping = json.loads(mapping_str)
                dec = decode_emoji_to_text(mapping, seq)
                print("\nDecoded:", dec)
            except Exception as e:
                print("Invalid format or decode error:", e)
            press_enter()
        elif ch == "3":
            break
        else:
            print("Invalid choice.")

# ---------------- Video downloader ----------------
def video_menu():
    while True:
        print("\n=== Video Downloader ===")
        print("1) Download single URL")
        print("2) Batch download from file")
        print("3) Install instructions / Check yt-dlp")
        print("4) Back")
        ch = input("Choose (1-4): ").strip()
        if ch == "1":
            if not YTDLP_OK:
                print("\n[!] yt-dlp not found. Install via:")
                print("    pip install yt-dlp")
                press_enter(); continue
            download_single()
        elif ch == "2":
            if not YTDLP_OK:
                print("\n[!] yt-dlp not found. Install via:")
                print("    pip install yt-dlp")
                press_enter(); continue
            download_batch()
        elif ch == "3":
            print("\nInstall instructions (Termux):")
            print("pkg update -y")
            print("pkg install python ffmpeg -y")
            print("pip install --upgrade pip")
            print("pip install yt-dlp")
            press_enter()
        elif ch == "4":
            break
        else:
            print("Invalid choice.")

def choose_format():
    print("\nChoose format:")
    print("1) best    2) bestvideo+bestaudio   3) bestaudio")
    print("4) 360p    5) 480p    6) 720p    7) 1080p    8) 4K")
    c = input("Choose (1-8): ").strip()
    if c=="1": return "best"
    if c=="2": return "bestvideo+bestaudio"
    if c=="3": return "bestaudio"
    if c=="4": return "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
    if c=="5": return "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
    if c=="6": return "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    if c=="7": return "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
    if c=="8": return "bestvideo[height>=2160]+bestaudio/best[height>=2160]/best"
    return "best"

def build_yt_dlp_cmd(url, outdir, template, fmt, extra_args=None):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = str(outdir / template)
    cmd = [YT_DLP_CMD, "-o", output, "-f", fmt, url]
    if extra_args:
        cmd = [YT_DLP_CMD] + extra_args + ["-o", output, "-f", fmt, url]
    return cmd

def run_cmd(cmd):
    try:
        print("\nRunning:", " ".join(cmd))
        subprocess.run(cmd, check=True)
        print("✅ Done.")
    except FileNotFoundError:
        print("yt-dlp not found.")
    except subprocess.CalledProcessError:
        print("Download failed or cancelled.")

def download_single():
    url = input("Paste video URL: ").strip()
    if not url:
        print("Empty URL."); return
    fmt = choose_format()
    outdir = input("Output dir (default downloads): ").strip() or "downloads"
    template = input("Filename template (default %(uploader)s - %(title)s [%(id)s].%(ext)s): ").strip() or "%(uploader)s - %(title)s [%(id)s].%(ext)s"
    extra = input("Extra yt-dlp args? (leave blank): ").strip()
    extra_args = extra.split() if extra else None
    cmd = build_yt_dlp_cmd(url, outdir, template, fmt, extra_args)
    run_cmd(cmd)

def download_batch():
    path = input("Path to file with URLs (one per line): ").strip()
    if not path or not os.path.exists(path):
        print("File not found."); return
    fmt = choose_format()
    outdir = input("Output dir (default downloads): ").strip() or "downloads"
    template = input("Filename template (default %(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s): ").strip() or "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s"
    extra = input("Extra yt-dlp args? (leave blank): ").strip()
    extra_args = extra.split() if extra else None
    with open(path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not urls:
        print("No URLs found."); return
    for i, url in enumerate(urls, 1):
        print(f"\n--- [{i}/{len(urls)}] {url}")
        cmd = build_yt_dlp_cmd(url, outdir, template, fmt, extra_args)
        run_cmd(cmd)

# ---------------- Audio stego (WAV LSB) ----------------
def audio_stego_menu():
    while True:
        print("\n=== Audio Stego (WAV LSB) ===")
        print("1) Embed file into WAV (or convert non-wav using ffmpeg)")
        print("2) Extract file from stego WAV")
        print("3) Back")
        ch = input("Choose (1-3): ").strip()
        if ch == "1":
            cover = input("Cover audio path (wav or other): ").strip()
            secret = input("Secret file path: ").strip()
            out = input("Output stego wav (default stego_output.wav): ").strip() or "stego_output.wav"
            embed_audio_wrapper(cover, secret, out)
        elif ch == "2":
            stego = input("Stego WAV path: ").strip()
            outdir = input("Output folder (default .): ").strip() or "."
            extract_audio(stego, outdir)
        elif ch == "3":
            break
        else:
            print("Invalid choice.")

MAGIC = b"KAMIAUD1"
def has_ffmpeg():
    return FFMPEG_OK

def convert_to_wav(src, tmp):
    cmd = ["ffmpeg", "-y", "-i", src, "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", tmp]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def bytes_to_bits(b):
    for byte in b:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1

def bits_to_bytes(bits):
    out = bytearray()
    cur = 0
    cnt = 0
    for bit in bits:
        cur = (cur << 1) | (bit & 1)
        cnt += 1
        if cnt == 8:
            out.append(cur)
            cur = 0
            cnt = 0
    return bytes(out)

def embed(cover_wav_path, secret_path, out_wav_path):
    import wave
    cover = wave.open(cover_wav_path, "rb")
    params = cover.getparams()
    nchannels, sampwidth, framerate, nframes = params.nchannels, params.sampwidth, params.framerate, params.nframes
    if sampwidth != 2:
        print("Tool expects 16-bit WAV.")
        cover.close(); return
    samples_count = nframes * nchannels
    capacity_bits = samples_count
    secret_bytes = Path(secret_path).read_bytes()
    filename = Path(secret_path).name.encode("utf-8")
    fname_len = len(filename)
    payload_len = len(secret_bytes)
    header = MAGIC + struct.pack(">I", fname_len) + filename + struct.pack(">Q", payload_len)
    payload = header + secret_bytes
    payload_bits = list(bytes_to_bits(payload))
    needed = len(payload_bits)
    if needed > capacity_bits:
        print(f"Cover too small: need {needed} bits, capacity {capacity_bits} bits.")
        cover.close(); return
    raw_frames = cover.readframes(nframes)
    cover.close()
    total_samples = nframes * nchannels
    fmt = "<" + ("h" * total_samples)
    samples = list(struct.unpack(fmt, raw_frames))
    for i, bit in enumerate(payload_bits):
        samples[i] = (samples[i] & ~1) | bit
    new_frames = struct.pack(fmt, *samples)
    outw = wave.open(out_wav_path, "wb")
    outw.setnchannels(nchannels)
    outw.setsampwidth(sampwidth)
    outw.setframerate(framerate)
    outw.writeframes(new_frames)
    outw.close()
    print(f"Embedded {secret_path} into {out_wav_path}")

def extract_audio(stego_wav_path, out_folder):
    import wave
    if not os.path.exists(stego_wav_path):
        print("File not found."); return
    wf = wave.open(stego_wav_path, "rb")
    nchannels, sampwidth, framerate, nframes = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
    if sampwidth != 2:
        print("Expecting 16-bit WAV."); wf.close(); return
    raw = wf.readframes(nframes); wf.close()
    total_samples = nframes * nchannels
    fmt = "<" + ("h" * total_samples)
    samples = list(struct.unpack(fmt, raw))
    bits = [s & 1 for s in samples]
    stream_bytes = bits_to_bytes(bits)
    if len(stream_bytes) < 8+4+8:
        print("No payload found."); return
    if stream_bytes[0:8] != MAGIC:
        print("Magic not found; no hidden data.")
        return
    idx = 8
    fname_len = struct.unpack(">I", stream_bytes[idx:idx+4])[0]; idx += 4
    filename = stream_bytes[idx:idx+fname_len].decode("utf-8"); idx += fname_len
    payload_len = struct.unpack(">Q", stream_bytes[idx:idx+8])[0]; idx += 8
    total_needed = 8 + 4 + fname_len + 8 + payload_len
    if len(stream_bytes) < total_needed:
        print("Incomplete payload.")
        return
    secret = stream_bytes[idx:idx+payload_len]
    out_path = Path(out_folder) / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(secret)
    print(f"Extracted hidden file to: {out_path}")

def embed_audio_wrapper(cover, secret, out):
    if not os.path.exists(cover):
        print("Cover not found."); return
    temp_wav = None
    used_cover = cover
    if not cover.lower().endswith(".wav"):
        if not has_ffmpeg():
            print("Cover not WAV and ffmpeg not found. Install ffmpeg or provide WAV.")
            return
        temp_wav = ".__tmp_cover.wav"
        ok = convert_to_wav(cover, temp_wav)
        if not ok:
            print("Conversion failed."); return
        used_cover = temp_wav
    try:
        embed(used_cover, secret, out)
    finally:
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)

# ---------------- Image stego ----------------
def image_stego_menu():
    if not PIL_OK:
        print("\n[!] Pillow not installed. Install: pip install pillow")
        press_enter(); return
    while True:
        print("\n=== Image Stego ===")
        print("1) Hide file inside image (PNG)")
        print("2) Extract file from image")
        print("3) Back")
        ch = input("Choose (1-3): ").strip()
        if ch == "1":
            img = input("Cover image path (PNG): ").strip()
            secret = input("Secret file path: ").strip()
            out = input("Output image name (default stego_image.png): ").strip() or "stego_image.png"
            hide_file_in_image(img, secret, out)
        elif ch == "2":
            stego = input("Stego image path: ").strip()
            outf = input("Output file name (default extracted_secret.bin): ").strip() or "extracted_secret.bin"
            extract_file_from_image(stego, outf)
        elif ch == "3":
            break
        else:
            print("Invalid choice.")

def hide_file_in_image(image_path, secret_path, output_path="stego_image.png"):
    with open(secret_path, "rb") as f:
        secret_data = f.read()
    img = Image.open(image_path).convert("RGBA")
    pixels = list(img.getdata())
    secret_bits = ''.join(format(byte, '08b') for byte in secret_data) + "1111111111111110"
    new_pixels = []
    bit_index = 0
    for pixel in pixels:
        r, g, b, a = pixel
        if bit_index < len(secret_bits):
            r = (r & ~1) | int(secret_bits[bit_index]); bit_index += 1
        if bit_index < len(secret_bits):
            g = (g & ~1) | int(secret_bits[bit_index]); bit_index += 1
        if bit_index < len(secret_bits):
            b = (b & ~1) | int(secret_bits[bit_index]); bit_index += 1
        new_pixels.append((r, g, b, a))
    img.putdata(new_pixels)
    img.save(output_path, "PNG")
    print(f"File hidden inside {output_path}")

def extract_file_from_image(stego_image, output_path="extracted_secret.bin"):
    img = Image.open(stego_image)
    pixels = list(img.getdata())
    bits = ""
    for pixel in pixels:
        r, g, b, a = pixel
        bits += str(r & 1); bits += str(g & 1); bits += str(b & 1)
    eof = bits.find("1111111111111110")
    if eof != -1:
        bits = bits[:eof]
    secret_bytes = bytearray()
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            secret_bytes.append(int(byte, 2))
    with open(output_path, "wb") as f:
        f.write(secret_bytes)
    print(f"Hidden file extracted as {output_path}")

# ---------------- Kamix Hollywood (simplified curses) ----------------
def kamix_hollywood_menu():
    try:
        import curses, math
    except Exception:
        print("\n[!] curses not available in this environment.")
        press_enter(); return
    def kamix_main(stdscr):
        curses.use_default_colors()
        curses.curs_set(1)
        stdscr.nodelay(True)
        stdscr.timeout(90)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        height, width = stdscr.getmaxyx()
        top_h = max(10, height-8); mid_h = 4; bot_h = 3
        win_top = curses.newwin(top_h, width, 0, 0)
        win_mid = curses.newwin(mid_h, width, top_h, 0)
        win_bot = curses.newwin(bot_h, width, top_h+mid_h, 0)
        prompt = "Kamix@Shell> "
        input_buf = ""
        top_lines = [" " * (width-2) for _ in range(top_h-2)]
        mid_lines = []
        rng = random.Random()
        # small intro
        title = "KAMIX HOLLYWOOD - Cinematic Shell"
        for i in range(6):
            stdscr.erase()
            try:
                stdscr.addstr(height//2, max(0,(width-len(title))//2), title, curses.A_BOLD | curses.color_pair(2 if i%2 else 1))
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(0.12)
        stdscr.erase(); stdscr.refresh()
        # loop
        while True:
            # generate top line
            w = width-2
            line = "".join(rng.choice("01ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%&*") if rng.random()>0.4 else " " for _ in range(w))
            top_lines.pop(0); top_lines.append(line)
            # draw
            win_top.erase(); win_top.box()
            try:
                win_top.addstr(0,2, " Kamix Hollywood (cinematic) ", curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass
            for idx, L in enumerate(top_lines):
                try:
                    win_top.addstr(1+idx, 1, L[:width-2], curses.color_pair(1))
                except curses.error:
                    pass
            win_top.refresh()
            # mid
            win_mid.erase(); win_mid.box()
            try: win_mid.addstr(0,2," System / Output ", curses.color_pair(3))
            except: pass
            visible = mid_lines[-(mid_h-2):] if mid_lines else []
            for i,L in enumerate(visible):
                try: win_mid.addstr(1+i,1, L[:width-2], curses.color_pair(4))
                except: pass
            win_mid.refresh()
            # bottom
            win_bot.erase(); win_bot.box()
            try:
                display = prompt + input_buf
                if len(display) > width-4: display = display[-(width-4):]
                win_bot.addstr(1,1, display, curses.color_pair(3))
                win_bot.move(1, 1 + len(display))
            except:
                pass
            win_bot.refresh()
            # input
            ch = stdscr.getch()
            if ch == -1:
                pass
            elif ch in (10,13):
                cmd = input_buf.strip(); input_buf = ""
                if cmd.lower() in ("exit","quit"):
                    break
                if cmd:
                    # run command and collect output lines (blocking)
                    try:
                        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        for L in p.stdout:
                            mid_lines.append(L.rstrip("\n"))
                            if len(mid_lines)>400: mid_lines.pop(0)
                        p.wait()
                        mid_lines.append(f"[Process exited with code {p.returncode}]")
                    except Exception as e:
                        mid_lines.append(f"[Error] {e}")
            elif ch in (127,8):
                input_buf = input_buf[:-1]
            elif 0 <= ch < 256:
                input_buf += chr(ch)
            time.sleep(0.02)
    try:
        import curses
        curses.wrapper(kamix_main)
    except Exception as e:
        print("Curses UI error:", e)
    press_enter()

# ---------------- Termux Secure Chat (embedded) ----------------
def termux_chat_menu():
    print("\nLaunching Termux Secure Chat v2 (menued).")
    print("This will run a lightweight menu for Host/Client/Group.")
    press_enter()
    # embed the menu and functions (adapted from provided script)
    def derive_key(pin: str, salt: bytes, iterations: int = 100_000, dklen: int = 32) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, iterations, dklen)
    def xor_bytes(data: bytes, key: bytes) -> bytes:
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    def send_json_line(sock: socket.socket, obj: dict):
        try:
            data = json.dumps(obj, ensure_ascii=False).encode('utf-8') + b'\n'
            sock.sendall(data)
        except Exception:
            pass
    def recv_lines(sock: socket.socket):
        buffer = b''
        while True:
            try:
                chunk = sock.recv(4096)
            except Exception:
                break
            if not chunk:
                if buffer:
                    yield buffer
                break
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                yield line
    # single host/client and group server/client functions (kept concise)
    def run_host_single(lhost, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((lhost, port)); s.listen(1)
        my_ip = lhost
        if my_ip == '0.0.0.0':
            try:
                t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); t.connect(("8.8.8.8",80)); my_ip = t.getsockname()[0]; t.close()
            except: my_ip = '0.0.0.0'
        print(f"[+] Listening on {my_ip}:{port}")
        conn, addr = s.accept()
        print(f"[+] Connected: {addr}")
        salt = token_bytes(16)
        send_json_line(conn, {"type":"salt","salt": base64.b64encode(salt).decode()})
        name = input("Your name: ").strip() or "Host"
        pin = getpass("Set shared PIN: ").strip()
        key = derive_key(pin, salt)
        print("[*] Chat started. /exit to quit.")
        stop_event = threading.Event()
        def recv_loop():
            for raw in recv_lines(conn):
                if stop_event.is_set(): break
                try:
                    obj = json.loads(raw.decode('utf-8', errors='ignore'))
                except: continue
                if obj.get("type") == "msg":
                    try:
                        ct = base64.b64decode(obj.get("ct")); pt = xor_bytes(ct, key).decode('utf-8', errors='ignore')
                        print(f"\n🔒 {obj.get('name')}: {pt}")
                    except:
                        print("\n[!] Corrupt or wrong PIN.")
                elif obj.get("type") == "close":
                    print("\n[!] Peer closed."); stop_event.set(); break
            stop_event.set()
        def input_loop():
            try:
                while not stop_event.is_set():
                    sline = input()
                    if sline.strip().lower() in ("/exit","/quit"):
                        send_json_line(conn, {"type":"close"}); stop_event.set(); break
                    if sline=="": continue
                    ct = xor_bytes(sline.encode('utf-8'), key)
                    send_json_line(conn, {"type":"msg","name":name,"ct": base64.b64encode(ct).decode()})
            except:
                stop_event.set()
        rt = threading.Thread(target=recv_loop, daemon=True); rt.start()
        it = threading.Thread(target=input_loop, daemon=True); it.start()
        rt.join(); it.join()
        conn.close(); s.close(); print("[*] Host chat ended.")
    def run_client_single(host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
        except Exception as e:
            print("Unable to connect:", e); return
        lines = recv_lines(sock)
        try:
            first = next(lines)
        except StopIteration:
            print("Connection closed"); sock.close(); return
        try:
            obj = json.loads(first.decode('utf-8', errors='ignore'))
        except:
            print("Invalid handshake"); sock.close(); return
        if obj.get("type")!="salt":
            print("Invalid handshake"); sock.close(); return
        salt = base64.b64decode(obj.get("salt"))
        name = input("Your name: ").strip() or "Client"
        pin = getpass("Enter shared PIN: ").strip()
        key = derive_key(pin, salt)
        print("[*] Chat started. /exit to quit.")
        stop_event = threading.Event()
        def recv_loop():
            for raw in lines:
                if stop_event.is_set(): break
                try:
                    o = json.loads(raw.decode('utf-8', errors='ignore'))
                except:
                    continue
                if o.get("type")=="msg":
                    try:
                        ct = base64.b64decode(o.get("ct")); pt = xor_bytes(ct, key).decode('utf-8', errors='ignore')
                        print(f"\n🔒 {o.get('name')}: {pt}")
                    except:
                        print("\n[!] Corrupt or wrong PIN.")
                elif o.get("type")=="close":
                    print("\n[!] Host closed."); stop_event.set(); break
            stop_event.set()
        def input_loop():
            try:
                while not stop_event.is_set():
                    sline = input()
                    if sline.strip().lower() in ("/exit","/quit"):
                        send_json_line(sock, {"type":"close"}); stop_event.set(); break
                    if sline=="": continue
                    ct = xor_bytes(sline.encode('utf-8'), key)
                    send_json_line(sock, {"type":"msg","name":name,"ct": base64.b64encode(ct).decode()})
            except:
                stop_event.set()
        rt = threading.Thread(target=recv_loop, daemon=True); rt.start()
        it = threading.Thread(target=input_loop, daemon=True); it.start()
        rt.join(); it.join()
        sock.close(); print("[*] Client ended.")
    def run_group_server(bind, port, pin, name):
        class GS:
            def __init__(self, bind, port, pin, name):
                self.bind=bind; self.port=port; self.pin=pin; self.name=name
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
                self.clients={}; self.lock=threading.Lock(); self.salt = token_bytes(16); self.running=False
            def start(self):
                self.s.bind((self.bind,self.port)); self.s.listen(50); self.running=True
                print(f"Group server on {self.bind}:{self.port}")
                threading.Thread(target=self.accept_loop, daemon=True).start()
                try:
                    while self.running:
                        line = input()
                        if line.strip().lower() in ("/exit","/quit"): self.stop(); break
                        self.broadcast_plain(self.name, line)
                except KeyboardInterrupt:
                    self.stop()
            def accept_loop(self):
                while self.running:
                    try:
                        conn, addr = self.s.accept()
                    except:
                        break
                    threading.Thread(target=self.handle_client, args=(conn,addr), daemon=True).start()
            def handle_client(self, conn, addr):
                try:
                    send_json_line(conn, {"type":"salt","salt": base64.b64encode(self.salt).decode()})
                    lines = recv_lines(conn)
                    try:
                        first = next(lines)
                    except StopIteration:
                        conn.close(); return
                    try:
                        obj = json.loads(first.decode('utf-8', errors='ignore'))
                    except:
                        conn.close(); return
                    if obj.get("type")!="join":
                        conn.close(); return
                    cname = obj.get("name") or "Anon"
                    key = derive_key(self.pin, self.salt)
                    with self.lock:
                        self.clients[conn] = {"name":cname,"key":key,"addr":addr}
                    print(f"[+] {cname} joined from {addr}")
                    self.broadcast_system(f"{cname} joined the group.")
                    for raw in lines:
                        try:
                            m = json.loads(raw.decode('utf-8', errors='ignore'))
                        except:
                            continue
                        if m.get("type")=="msg":
                            try:
                                ct = base64.b64decode(m.get("ct")); pt = xor_bytes(ct, key).decode('utf-8', errors='ignore')
                                self.broadcast_plain(m.get("name"), pt)
                            except:
                                continue
                        elif m.get("type")=="leave":
                            break
                finally:
                    with self.lock:
                        info = self.clients.pop(conn, None)
                    if info:
                        self.broadcast_system(f"{info.get('name')} left the group.")
                        print(f"[-] {info.get('name')} disconnected.")
                    try: conn.close()
                    except: pass
            def broadcast_plain(self, sender_name, plaintext):
                with self.lock:
                    conns = list(self.clients.items())
                for conn, info in conns:
                    try:
                        key = info.get("key"); ct = xor_bytes(plaintext.encode('utf-8'), key)
                        send_json_line(conn, {"type":"msg","name":sender_name,"ct": base64.b64encode(ct).decode()})
                    except:
                        with self.lock:
                            if conn in self.clients:
                                self.clients.pop(conn)
                                try: conn.close()
                                except: pass
            def broadcast_system(self, text):
                self.broadcast_plain("System", text)
            def stop(self):
                self.running=False
                try: self.s.close()
                except: pass
                with self.lock:
                    for c in list(self.clients.keys()):
                        try: send_json_line(c, {"type":"server_close"}); c.close()
                        except: pass
                    self.clients.clear()
                print("[*] Group server stopped.")
        gs = GS(bind, port, pin, name); gs.start()
    def run_group_client(host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
        except Exception as e:
            print("Could not connect:", e); return
        lines = recv_lines(sock)
        try:
            first = next(lines)
        except StopIteration:
            print("Disconnected by server"); sock.close(); return
        try:
            obj = json.loads(first.decode('utf-8', errors='ignore'))
        except:
            print("Invalid handshake"); sock.close(); return
        if obj.get("type")!="salt":
            print("Invalid handshake"); sock.close(); return
        salt = base64.b64decode(obj.get("salt"))
        name = input("Your name: ").strip() or "Anon"
        pin = getpass("Enter group PIN: ").strip()
        key = derive_key(pin, salt)
        send_json_line(sock, {"type":"join","name":name})
        print("[*] Joined group. /exit to leave.")
        stop_event = threading.Event()
        def recv_loop():
            for raw in lines:
                if stop_event.is_set(): break
                try:
                    o = json.loads(raw.decode('utf-8', errors='ignore'))
                except:
                    continue
                t = o.get("type")
                if t=="msg":
                    try:
                        ct = base64.b64decode(o.get("ct")); pt = xor_bytes(ct, key).decode('utf-8', errors='ignore')
                        print(f"\n🔒 {o.get('name')}: {pt}")
                    except:
                        print("\n[!] Corrupt or wrong PIN.")
                elif t=="server_close":
                    print("\n[!] Server closed."); stop_event.set(); break
            stop_event.set()
        def input_loop():
            try:
                while not stop_event.is_set():
                    sline = input()
                    if sline.strip().lower() in ("/exit","/quit"):
                        send_json_line(sock, {"type":"leave"}); stop_event.set(); break
                    if sline=="": continue
                    ct = xor_bytes(sline.encode('utf-8'), key)
                    send_json_line(sock, {"type":"msg","name":name,"ct": base64.b64encode(ct).decode()})
            except:
                stop_event.set()
        rt = threading.Thread(target=recv_loop, daemon=True); rt.start()
        it = threading.Thread(target=input_loop, daemon=True); it.start()
        rt.join(); it.join()
        sock.close(); print("[*] Left group.")
    # menu
    while True:
        print("\n=== Termux Secure Chat v2 ===")
        print("1) Start Chat (Host - 1:1)")
        print("2) Join Friend (Client - 1:1)")
        print("3) Start Group Server (multi-client)")
        print("4) Join Group (client)")
        print("5) Back")
        choice = input("Choose (1-5): ").strip()
        if choice == "1":
            lhost = input("LHOST (0.0.0.0): ").strip() or "0.0.0.0"
            port = int(input("Port (9000): ").strip() or "9000")
            run_host_single(lhost, port)
        elif choice == "2":
            host = input("Friend IP: ").strip() or "127.0.0.1"
            port = int(input("Port (9000): ").strip() or "9000")
            run_client_single(host, port)
        elif choice == "3":
            bind = input("Bind (0.0.0.0): ").strip() or "0.0.0.0"
            port = int(input("Port (9000): ").strip() or "9000")
            name = input("Server display name: ").strip() or "GroupHost"
            pin = getpass("Set group PIN: ").strip()
            run_group_server(bind, port, pin, name)
        elif choice == "4":
            host = input("Group server IP: ").strip() or "127.0.0.1"
            port = int(input("Port (9000): ").strip() or "9000")
            run_group_client(host, port)
        elif choice == "5":
            break
        else:
            print("Invalid.")

# ---------------- Main Menu ----------------
def main_menu():
    while True:
        print("\n=== KAMI MAX TOOLKIT ===")
        print("1) QR Code / Scanner / Hash")
        print("2) Video Downloader")
        print("3) Audio Steganography")
        print("4) Image Steganography")
        print("5) Kamix Hollywood cinematic terminal")
        print("6) Termux Secure Chat v2")
        print("7) Exit")
        choice = input("Choose (1-7): ").strip()
        if choice == "1":
            qr_menu()
        elif choice == "2":
            video_menu()
        elif choice == "3":
            audio_stego_menu()
        elif choice == "4":
            image_stego_menu()
        elif choice == "5":
            kamix_hollywood_menu()
        elif choice == "6":
            termux_chat_menu()
        elif choice == "7":
            print("Bye 👋"); break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
