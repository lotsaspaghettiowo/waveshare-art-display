# simple program to queue images from a shared directory and display them on an epaper display
# requires Waveshare epd2in7.py and epdconfig.py files in ./lib and 04B_03__.TTF font in ./fonts
# https://github.com/waveshare/e-Paper
# https://www.dafont.com/04b-03.font

import sys, os, logging, traceback, time, random, math, glob, re
sys.path.append("./lib")
import epd2in7
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button
from pathlib import Path

### CONFIGURABLE STUFF ###
#TODO: accept user input for path, config file for path and allowed extensions

#path where images are located, intended for a network-shared folder
sharePath = "/mnt/share1/epaper_art/"

#allowed filetypes separated with | character, ignores everything else
fileExts = "bmp|png|jpg|jpeg|gif"

#revision number to show
versionNum = "1.0"

### SETUP STUFF ###

#assign hardware buttons
btn1 = Button(5)
btn2 = Button(6)
btn3 = Button(13)
btn4 = Button(19)

#miscellaneous setup
logging.basicConfig(level=logging.DEBUG)
font = ImageFont.truetype('./fonts/04B_03__.TTF', 8)
font2 = ImageFont.truetype('./fonts/04B_03__.TTF', 16)

#initialize EPD
epd = epd2in7.EPD()

### FUNCTION DEFINITIONS ###

#displays the image on-screen with title text in bottom left, then returns whether it was successful
#TODO: initially this used grayscale functionality but I noticed my display power-cycled at times
#TODO: for now this just displays the image in black/white
def displayImage(imgPath):
    try:
        imgFile = Image.open(imgPath)
        #if it's a png or something make transparent background white
        try:
            img = Image.new("RGBA", imgFile.size, "WHITE")
            img.paste(imgFile, (0, 0), imgFile) 
        except ValueError:
            img = imgFile
        img.convert("1")
        epd.init()
        epd.Clear(0xFF)
        canvas = Image.new("1", (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        #center image on canvas, round toward top-right as text is drawn in bottom-left
        canvas.paste(img, (math.ceil((canvas.width/2)-(img.width/2)), math.floor((canvas.height/2)-(img.height/2))))
        #draw small filename text over image
        text = os.path.basename(imgPath)
        text = os.path.splitext(text)[0]
        draw.rectangle((0, 168, 8+font.getsize(text)[0], 176), fill = 1)
        draw.text((4, 168), text, font = font, fill = 0)
        epd.display(epd.getbuffer(canvas))
        epd.sleep()
    except FileNotFoundError:
        return False
    else:
        return True

#default display for information or if something goes wrong
def displayMsg(message):
    epd.init()
    epd.Clear(0xFF)
    canvas = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(canvas)
    #draw larger text with inverted colors
    draw.rectangle((0, 160, 8+font2.getsize("["+message+"]")[0], 176), fill = 0)
    draw.text((4, 160), "["+message+"]", font = font2, fill = 1)
    epd.display(epd.getbuffer(canvas))
    epd.sleep()

#list queue out on-screen, along with help text
def displayQueue(q):
    epd.init()
    epd.Clear(0xFF)
    canvas = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(canvas)
    #draw dividing lines
    draw.line(((62, 0), (62, canvas.height)), fill = 0, width = 1)
    draw.line(((80, 0), (80, canvas.height)), fill = 0, width = 1)
    for y in range(22, 176, 22):
        draw.line(((62, y), (canvas.width, y)), fill = 0, width = 1)
    #draw the file queue
    qCount = 0
    for i in q:
        draw.text((66, (qCount*22)+4), str(qCount+1), font = font2, fill = 0)
        draw.text((84, (qCount*22)+4), os.path.basename(i), font = font2, fill = 0)
        qCount = qCount + 1
    #draw help text and version number
    draw.text((2, 4), "BTN1:", font = font2, fill = 0)
    draw.text((2, 20), "Queue", font = font2, fill = 0)
    draw.text((2, 40), "BTN2:", font = font2, fill = 0)
    draw.text((2, 56), "Next", font = font2, fill = 0)
    draw.text((2, 76), "BTN3:", font = font2, fill = 0)
    draw.text((2, 92), "Latest", font = font2, fill = 0)
    draw.text((2, 112), "BTN4:", font = font2, fill = 0)
    draw.text((2, 128), "Reload", font = font2, fill = 0)
    draw.text((4, 168), "v" + versionNum, font = font, fill = 0)
    epd.display(epd.getbuffer(canvas))
    epd.sleep()

#creates a random array of files that ignores non-images and hidden files
#edit fileExts regex above to change accepted filetypes
def generateFileQueue():
    q = glob.glob(glob.escape(sharePath)+"**/*.*", recursive=True)
    q = [i for i in q if exts.match(i)]
    random.seed() #reseed before each shuffle using system time
    random.shuffle(q)
    return q

#attempts to load the next image in the queue
def displayNextImage(q):
    imageLoaded = False
    if (len(q) != 0):
        q.pop(0)
    while (imageLoaded == False):
        try:
            imageLoaded = displayImage(q[0])
        except IndexError:
            q = generateFileQueue()
            if (len(q) == 0):
                displayMsg("No images were found")
                imageLoaded = True #finish loop
    return q

#attempts to load the most recent image on disk, falls back to current image
def displayMostRecentImg(q):
    p = glob.glob(glob.escape(sharePath)+"**/*.*", recursive=True)
    p = [i for i in p if exts.match(i)]
    imageLoaded = displayImage(max(p, key = os.path.getctime))
    if (imageLoaded == False):
        displayMsg("Most recent image not found")
        time.sleep(2)
        try:
            displayImage(fileQueue[0]) #reload current image
        except IndexError:
            displayMsg("No images were found")
    return q

### MAIN CODE ###

#init variables
fileQueue = []
currHr = -1
exts = re.compile("(?i).*\.["+fileExts+"]")

#display something of a start screen
displayMsg("Art Display v" + versionNum)
time.sleep(2)

#program loop
try:
    while True:
        #actions to do only on hour change
        if (currHr != time.strftime("%H", time.localtime())):
            currHr = time.strftime("%H", time.localtime())
            fileQueue = displayNextImage(fileQueue)
        #button actions
        if btn1.is_pressed:
            displayQueue(fileQueue)
        if btn2.is_pressed:
            fileQueue = displayNextImage(fileQueue)
        if btn3.is_pressed:
            fileQueue = displayMostRecentImg(fileQueue)
        if btn4.is_pressed:
            try:
                displayImage(fileQueue[0]) #reload current image
            except IndexError:
                False #idk don't do anything??????
        
except Exception as e:
    logging.error('exception occurred, stopping...')
    with open('logs/artdisplaylog.txt', 'a') as f:
            f.write((time.strftime('%c', time.localtime())) + '\n')
            f.write(str(e))
            f.write((traceback.format_exc()) + '\n')
    epd2in7.epdconfig.module_exit_cleanup()
    exit()
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd2in7.epdconfig.module_exit_cleanup()
    exit()