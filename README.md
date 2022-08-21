# waveshare-art-display

A simple Python script written for the Waveshare 2.7in e-paper display that queues image files in a shared directory and displays them every hour.

Requires Waveshare driver files epd2in7.py and epdconfig.py as well as the 04b03 font in the respective folders.
- https://github.com/waveshare/e-Paper
- https://www.dafont.com/04b-03.font

### TODOs

- Get grayscale display to work without the occasional power-cycling issue (currently only displays in black and white)
- Allow image directory to be specified via user input or config file
- Also let allowed file extensions to be read from config file
- Make compatible with other Waveshare display sizes