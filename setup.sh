#!/bin/bash
# setup.sh - All-in-one installer for Kami Max Toolkit
# Run: bash setup.sh

echo "📦 Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "📦 Installing Termux system packages..."
TERMUX_PKGS=(python python-pip git ffmpeg zbar nano wget curl)
for pkgname in "${TERMUX_PKGS[@]}"; do
    echo "Installing $pkgname..."
    pkg install -y "$pkgname"
done

echo "✅ Termux packages installed."

echo "📦 Installing Python packages..."
PY_PKGS=(Pillow qrcode opencv-python requests cryptography pycryptodome colorama)
for p in "${PY_PKGS[@]}"; do
    echo "Installing $p..."
    pip install "$p"
done

echo "✅ Python packages installed."

echo "🎉 Setup complete! You can now run 'python3 kami_toolkit.py'"
