# connection-status
A simple tray icon that shows green/yellow/red based on ping against a url

Works on Windows, should also in Mac but must me tested.

### Compile on Windows:

```
pyinstaller --noconsole --onefile connstatus.py
```

### Compile on Mac:

Follows instructions for Mac pasted from ChatGPT

1. Install PyInstaller

```
pip install pyinstaller
```

2. Create .icns

From a .png (es. 1024x1024).

```
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
cp icon.png icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
```

3. Compile

```
pyinstaller --onefile --windowed --name "ConnStatus" --icon=icon.icns connstatus.py
```

4. Test

Drag ConnStatus.app in /Applications e start:

It should appear the green iconin the top right corner of the menu bar.

At first run should also appear a message  “Sviluppatore non verificato”:

Go to Preferenze di Sistema → Sicurezza & Privacy → Generali → Consenti comunque.

Restart it.
