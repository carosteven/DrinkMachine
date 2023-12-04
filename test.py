from pico_i2c_lcd import I2cLcd
from machine import Pin, I2C, SPI
from utime import sleep, ticks_ms
import sdcard
import os

def getIngredients(): # Get list of liquor and mixes, assign to pumps
    pumpAssignment = ['']*8 # 8 pumps
    liquors = []
    mixes = []
    f = open('/sd/Recipes.txt', 'r')
    lines = f.readlines()
    for i in range(len(lines)):
        if "Liquor" in lines[i]:
            j=i+2
            while j < len(lines):
                words = lines[j].split('\r\n')
                words = words[0].split(None, 2)
                if len(words) == 0:
                    i = j
                    break
                else:
                    liquors.append(words[2])
                    pumpAssignment[int(words[1][0:-1])-1] = words[2]
                j+=1
        
        elif "Mix" in lines[i]:
            j=i+2
            while j < len(lines):
                words = lines[j].split('\r\n')
                words = words[0].split(None, 2)
                if len(words) == 0:
                    break
                else:
                    mixes.append(words[2])
                    print(words[2])
                    pumpAssignment[int(words[1][0:-1])-1] = words[2]
                    print(pumpAssignment)
                j+=1
            break
    f.close()
    return pumpAssignment, liquors, mixes

def getRecipes():
    recipes = {}
    f = open('/sd/Recipes.txt', 'r')
    lines = f.readlines()
    for i in range(len(lines)):
        if "Recipes" in lines[i]:
            j=i+2
            nameLine=True
            while j < len(lines):
                if nameLine:
                    name=lines[j][0:-2]
                    nameLine=False
                    tempDict={}
                
                else:
                    words = lines[j].split('\r\n')
                    words = words[0].split(None, 2)
                    if len(words) == 0 or words[0] == 'END':
                        nameLine = True
                        recipes[name]=tempDict
                    
                    else:
                        tempDict[words[2]]=float(words[0])

                j+=1
            break
    f.close()
    return recipes

def posCheck(pos, maxPos, addSub):
    maxPos = len(maxPos)-1
    if addSub:
        if pos+1 > maxPos:
            pos = 0
        else:
            pos += 1
    else:
        if pos-1 < 0:
            pos = maxPos
        else:
            pos -= 1
    return pos

def snake(char, pos):
    if pos % 4 == 3:
        if int(pos/4) % 2 == 0:
            lcd.putstr(char, 4, 1+2*int(pos/4))
        else:
            lcd.putstr(char, 2, 1+2*int(pos/4))
    else:
        if int(pos/4) % 2 == 0:
            lcd.putstr(char, pos+2, 2*int(pos/4))
        else:
            lcd.putstr(char, 4-pos, 2*int(pos/4))

def angleBar(char, pos):
    if pos < 20:
        lcd.putstr(char, 2, pos)
    if pos > 0 and pos < 21:
        lcd.putstr(char, 3, pos-1)
    if pos > 1 and pos < 22:
        lcd.putstr(char, 4, pos-2)

def updateScreen(pos, currentScreen, animation=None):
    if currentScreen == "Status":
        lcd.putstr("Making Drink...", 1, 3)
        if animation == "Boring":
            lcd.putstr('*', 2, pos)
        elif animation == "Snake":
            snake('*', pos)
        elif animation == "Angle":
            angleBar('*', pos)
    else:
        lcd.clear()
        lcd.putstr('*' + currentScreen + '*', 1, 10-int((len(currentScreen)+2)/2))
        lcd.putstr(">                  <", 3)

        lcd.putstr(choices[posCheck(pos, choices, 0)], 2, 10-int(len(choices[posCheck(pos, choices, 0)])/2))
        lcd.putstr(choices[pos], 3, 10-int(len(choices[pos])/2))
        lcd.putstr(choices[posCheck(pos, choices, 1)], 4, 10-int(len(choices[posCheck(pos, choices, 1)])/2))

def makeDrink(recipe):
    activePumps = []
    maxDur = 0
    for ingredient in recipe:
        for i in range(8):
            if pumpAssignment[i] == ingredient:
                dur = (recipe[ingredient])/FLOWRATE
                if dur > maxDur:
                    maxDur = dur
                activePumps.append([pumps[i], dur])
                '''
                if i+1 == 1:
                    activePumps.append([r1, dur])
                elif i+1 == 2:
                    activePumps.append([r2, dur])
                elif i+1 == 3:
                    activePumps.append([r3, dur])
                elif i+1 == 4:
                    activePumps.append([r4, dur])
                elif i+1 == 5:
                    activePumps.append([r5, dur])
                elif i+1 == 6:
                    activePumps.append([r6, dur])
                elif i+1 == 7:
                    activePumps.append([r7, dur])
                elif i+1 == 8:
                    activePumps.append([r8, dur])
                '''
                break
    
    for thread in activePumps:
        thread[0].low()
        
    return maxDur, activePumps

# For the screen
i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=1000000)
I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 4, 20)

# For the sd card reader
cs=Pin(17, Pin.OUT)
cs.high()
spi=SPI(0,baudrate=40000000,sck=Pin(18),mosi=Pin(19),miso=Pin(16))
sd=sdcard.SDCard(spi,cs)
vfs=os.VfsFat(sd)
os.mount(sd, '/sd')

# For the button
position = 0
prevClkState = 1
prevDtState = 1
prevButtonState = 0
bounce = 150
time_spinDetected = ticks_ms()
clk = Pin(0, Pin.IN, Pin.PULL_UP)
dt = Pin(1, Pin.IN, Pin.PULL_UP)
button = Pin(3, Pin.IN, Pin.PULL_DOWN)
buttonRef = Pin(2, Pin.OUT)
buttonRef.high()

# For the relay
pumps = []
for i in range(8):
    pumps.append(Pin(8-i+5, Pin.OUT))
    pumps[i].high()
relayRef = Pin(5, Pin.OUT)
relayRef.high()
'''
r1 = Pin(6, Pin.OUT)
r2 = Pin(7, Pin.OUT)
r3 = Pin(8, Pin.OUT)
r4 = Pin(9, Pin.OUT)
r5 = Pin(10, Pin.OUT)
r6 = Pin(11, Pin.OUT)
r7 = Pin(12, Pin.OUT)
r8 = Pin(13, Pin.OUT)
rRef = Pin(14, Pin.OUT)

r1.high()
r2.high()
r3.high()
r4.high()
r5.high()
r6.high()
r7.high()
r8.high()
rRef.high()
'''

FLOWRATE = 4.0/70.0
maxDuration = 0
animationList = {"Boring": 20, "Snake": 40, "Angle": 22}
animation = "Angle"
time_drinkStart = 0
pumpDurations = []
drinkDone = False


recipes = getRecipes()
pumpAssignment, liquors, mixes = getIngredients()
for recipe in recipes:
    for ingredient in recipes[recipe]:
        ingredientGood = False
        for drink in pumpAssignment:
            if drink == ingredient:
                ingredientGood = True
                break
        if not ingredientGood:
            recipes.pop(recipe)
            break

choices, currentScreen = liquors, "Liquor"
updateScreen(position, currentScreen)

while True:
    if currentScreen == "Status":
        for pump in pumpDurations:
            if ticks_ms() - time_drinkStart > pump[1]*1000:
                pump[0].high()
                pumpDurations.remove(pump)
            if len(pumpDurations) == 0:
                drinkDone = True
                
        if ticks_ms() - time_drinkStart > (position+1)*(maxDuration/animationList[animation])*1000:
            position+=1
            if drinkDone:
                drinkDone = False
                position = 0
                choices, currentScreen = liquors, "Liquor"
                lcd.clear()
                lcd.putstr("Enjoy!", 2, 7)
                sleep(2.5)
            updateScreen(position, currentScreen, animation)

    else:
        if clk.value() == 0 and clk.value() != prevClkState and ticks_ms() - time_spinDetected > bounce:
            prevClkState = 0
            time_spinDetected = ticks_ms()
            if dt.value() == 0:
                position = posCheck(position, choices, 0)
                updateScreen(position, currentScreen)
                while dt.value() == 0:
                    pass

            elif dt.value() == 1:
                position = posCheck(position, choices, 1)
                updateScreen(position, currentScreen)
        else:
            prevClkState = 1
            
        if button.value():
            if prevButtonState == 0: # TODO add bounce maybe
                prevButtonState = 1
                if currentScreen == "Liquor":
                    ''' choices[position] is the selected liquor '''
                    possibleDrinks = []
                    for recipe in recipes:
                        for ingredient in recipes[recipe]:
                            if ingredient == choices[position]:
                                possibleDrinks.append(recipe)
                                break
                    '''
                    verify mixes are present **************************************************************************************
                    '''
                    
                    possibleDrinks.append("Back")
                    choices, currentScreen = possibleDrinks, "Drinks"

                elif currentScreen == "Drinks":
                    ''' choices[position] is the selected drink '''
                    if choices[position] == "Back":
                        choices, currentScreen = liquors, "Liquor"
                    
                    else:
                        currentScreen = "Status"
                        maxDuration, pumpDurations = makeDrink(recipes[choices[position]])
                        time_drinkStart = ticks_ms()
                        lcd.clear()

                position = 0
                updateScreen(position, currentScreen, animation)

        
        else:
            prevButtonState = 0

        
        
        