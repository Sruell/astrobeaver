# astrobeaver
Camera-GUI for astrophotography using a Raspberry Pi (3B+) and the Pi HQ Cam with a 3.5" touchscreen.

Heavily inspired by and based on Adam Baskerville's https://github.com/adambaskerville/AstroPitography and Santiago Rodriguez' https://github.com/RemovedMoney326/Hubble-Pi

# My ambition
- slim and easy solution to take astronomic videos of planets with the Pi HQ Cam on a Raspberry Pi 3B+ I had laying around
- Working 'in the field' without network connection and only powered by a simple mobile powerbank
- only basic features (no reinvention of excellent tools like firecapture or oacapture)
- yet some features specific to planetary videography that I was missing from above projects
- trying to get the most out of the limited hardware

# Features
While AstroPitography as well as Hubble-Pi offer all the basic features one could care for and full-featured tools like firecapture have all functionalities ever thinkable, I was looking for a set of features 'in between' and specific to my main interest of planetary photography.

- Choose whether high-quality H264 or raw YUV videos should be recorded
- Switch recording resolutions
- Define a **region of interest** (for H264 only) with sensible resolutions to allow for higher frame rates
- Change ISO settings (=> manipulating analog and digital gain)
- Make better use of the limited space on a 3.5" touchscreen by introducing sub-windows for some settings

# Dependencies

- Python3
- picamera >= 1.13
- Pillow >= 8.4.0
- PySimpleGUI >= 4.55.1
