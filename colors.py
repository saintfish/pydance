# Colors and functions for working with colors

color = {
  'red': (255, 0, 0),
  'yellow': (255, 255, 0),
  'green': (0, 255, 0),
  'cyan':(0, 255, 255),
  'blue': (0, 0, 255),
  'purple': (255, 0, 255),
  'orange': (255, 127, 0),
  'aqua': (0, 255, 127),
  'white': (255, 255, 255),
  'black': (0, 0, 0),
  'gray': (127, 127, 127)
  }

# We use these a lot, so save lookup time
WHITE = color["white"]
BLACK = color["black"]

def brighten(color, diff = 64):
  return tuple([min(x + diff, 255) for x in color])

def darken(color, diff = 64):
  return tuple([max(x - diff, 0) for x in color])

def darken_div(color, div = 3.5):
  return tuple([x / div for x in color])
