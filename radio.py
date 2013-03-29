#!/usr/bin/python

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import subprocess

DEBUG = True

class Node:
  def __init__(self, text):
    self.mark = ''
    self.parent = None
    self.text = text
  
  def into(self):
    pass
  
  def __repr__(self):
    return 'node:' + self.text


class Folder(Node):
  def __init__(self, text, items=[]):
    Node.__init__(self, text)
    self.mark = '>'
    self.setItems(items)
  
  def setItems(self, items):
    self.items = items
    for item in self.items:
      item.parent = self


class Playlists(Folder):
  def __init__(self, radio):
    Folder.__init__(self, 'Playlists')
    self.radio = radio

  def into(self):
    print "into", repr(self)
    self.setItems([
      Playlist(playlist, self.radio) for playlist in self.radio.command('mpc lsplaylists')
    ])


class Widget(Node):
  pass


class Playlist(Widget):
  def __init__(self, text, radio):
    Node.__init__(self, text)
    self.radio = radio
  
  def run(self):
    self.radio.command('mpc clear')
    self.radio.command('mpc load ' + self.text)
    self.radio.command('mpc play')
    self.radio.command('mpc volume 70')
    
    self.radio.lcd.home()
    
    status = self.radio.command('mpc status')
    print status
    self.radio.lcd.message(status)


class App:
  ROWS = 2
  COLS = 16
  
  def __init__(self, lcd, folder):
    self.lcd = lcd
    self.folder = folder
    self.top = 0
    self.selected = 0

  
  def display(self):
    if self.top > len(self.folder.items) - self.ROWS:
      self.top = len(self.folder.items) - self.ROWS
    
    if self.top < 0:
      self.top = 0
    
    if DEBUG:
      print('------------------')
    
    str = ''
    for row in range(self.top, self.top + self.ROWS):
      if row > self.top:
        str += '\n'
      if row < len(self.folder.items):
        if row == self.selected:
          line = '-' + self.folder.items[row].text + self.folder.items[row].mark
          if len(line) < self.COLS:
            for row in range(len(line), self.COLS):
              line += ' '
          str += line
        else:
          line = ' ' + self.folder.items[row].text + self.folder.items[row].mark
          if len(line) < self.COLS:
            for row in range(len(line), self.COLS):
              line += ' '
          str += line

        if DEBUG:
          print('|'+line+'|')

    if DEBUG:
      print('------------------')

    self.lcd.home()
    self.lcd.message(str)


  def up(self):
    if self.selected == 0:
      return
    elif self.selected > self.top:
      self.selected -= 1
    else:
      self.top -= 1
      self.selected -= 1


  def down(self):
    if self.selected + 1 == len(self.folder.items):
      return
    elif self.selected < self.top + self.ROWS - 1:
      self.selected += 1
    else:
      self.top += 1
      self.selected += 1


  def left(self):
    if not isinstance(self.folder.parent, Folder):
      return 
    
    # find the current in the parent
    itemno = 0
    index = 0
    for item in self.folder.parent.items:
      if self.folder == item:
        if DEBUG:
          print 'foundit:', item
        index = itemno
      else:
          itemno += 1
    if index < len(self.folder.parent.items):
      self.folder = self.folder.parent
      self.top = index
      self.selected = index
    else:
      self.folder = self.folder.parent
      self.top = 0
      self.selected = 0


  def right(self):
    if isinstance(self.folder.items[self.selected], Folder):
      self.folder = self.folder.items[self.selected]
      self.top = 0
      self.selected = 0
      self.folder.into()
    elif isinstance(self.folder.items[self.selected], Widget):
      self.folder.items[self.selected].run()


  def select(self):
    if isinstance(self.folder.items[self.selected], Widget):
      self.folder.items[self.selected].run()


  def run(self):
    self.display()
    
    last_buttons = None

    while True:
      buttons = self.lcd.buttons()
      if last_buttons == buttons:
        continue
      last_buttons = buttons
        
      if (self.lcd.buttonPressed(self.lcd.LEFT)):
        self.left()
        self.display()

      if (self.lcd.buttonPressed(self.lcd.UP)):
        self.up()
        self.display()

      if (self.lcd.buttonPressed(self.lcd.DOWN)):
        self.down()
        self.display()

      if (self.lcd.buttonPressed(self.lcd.RIGHT)):
        self.right()
        self.display()

      if (self.lcd.buttonPressed(self.lcd.SELECT)):
        self.select()
        self.display()


class Radio(App):
  def __init__(self):
    App.__init__(self,
      Adafruit_CharLCDPlate(), 
      Folder('Pauls iRadio', (
        Playlists(self),
        Folder('bbb', (
          Node('b.1'), 
          Node('b.2'), 
          Node('b.3')
        )),
        Node('ccc'),
        Node('ddd'),
        Node('eee')
      ))
    )
  
  def command(self,cmd):
    p = subprocess.Popen(
      cmd, shell=True, bufsize=256, stdout=subprocess.PIPE
    ).stdout

    result = []
    while True:
      line = p.readline().rstrip('\n')
      if not line:
        break
      result.append(line) 
    
    return result


if __name__ == '__main__':
  Radio().run()