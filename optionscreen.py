# ceci n'est pas une \'{e}cran d'option

import copy
from constants import *
import pygame
import colors
import scores, lifebars, combos

def player_opt_driver(screen, configs):
  ev = (0, E_QUIT)
  start = pygame.time.get_ticks()
  clrs = [colors.color["cyan"], colors.color["yellow"]]
  menu = [
    ("Speed", "speed", [(0.25, ".25x"), (0.5, ".5x"), (1, "1x"), (1.5, "1.5x"),
                        (2, "2x"), (3, "3x"), (4, "4x"), (8, "8x")]),
    ("Steps", "transform", [(0, "Normal",), (1, "Mirror"), (2, "Left"),
                         (3, "Right"), (-1, "Shuffle"), (-2, "Random")]),
    ("Size", "size", [(0, "Off"), (1, "Tiny"), (2, "Little"), (3, "Big"),
                      (4, "Quick"), (5, "Skippy")]),
    ("Sudden", "sudden", [(0, "Off"), (1, "Hide 1"), (2, "Hide 2"),
                          (3, "Hide 3")]),
    ("Hidden", "hidden", [(0, "Off"), (1, "Hide 1"), (2, "Hide 2"),
                          (3, "Hide 3")]),
    ("Accel", "accel", [(0, "None"), (1, "Boost"), (2, "Brake")]),
    ("Scale", "scale", [(1, "Normal"), (0, "Shrink"), (2, "Grow")]),
    ("Scroll", "scrollstyle", [(0, "Normal"), (1, "Reverse"), (2, "Center")]),
    ("Jumps", "jumps", [(0, "On"), (1, "Off"), (2, "Wide")]),
    ("Spin", "spin", [(0, "Off"), (1, "On")]),
    ("Flat", "colortype", [(4, "Off"), (1, "On")]),
    ("Dark", "dark", [(0, "Off"), (1, "On")]),
    ("Holds", "holds", [(1, "On"), (0, "Off")]),
    ]

  while ((event.states[(0, E_START)] or event.states[(1, E_START)]) and
         pygame.time.get_ticks() - start < 1500): ev = event.poll()

  if event.states[(0, E_START)] or event.states[(1, E_START)]:
    op = OptionScreen(configs, "Player Options", menu, clrs)
    return op.display(screen)
  else: return True

def game_opt_driver(screen, config):
  ev = (0, E_QUIT)
  start = pygame.time.get_ticks()
  menu = [
    ("Difficulty", "diff", [(1, "Normal"), (1.5, "Easy"), (0.75, "Hard")]),
    ("Scoring", "scoring", scores.score_opt),
    ("Combos", "combo", combos.combo_opt),
    ("Lifebar", "lifebar", lifebars.lifebar_opt),
    ("Oni Life", "onilives", [(1, "1"), (3, "3"), (5, "5"), (9, "9")]),
    ("Battle", "battle", [(0, "Off"), (1, "On")]),
    ]
  clrs = [colors.color["green"]]

  while ((event.states[(0, E_SELECT)] or event.states[(1, E_SELECT)]) and
         pygame.time.get_ticks() - start < 1500): ev = event.poll()

  if event.states[(0, E_SELECT)] or event.states[(1, E_SELECT)]:
    op = OptionScreen([config], "Game Options", menu, clrs)
    op.display(screen)
    return False
  else: return True
                    
class OptionScreen(object):

  bg = pygame.image.load(os.path.join(pyddr_path, "images", "option-bg.png"))
  bg.set_colorkey(bg.get_at([0, 0]))
  bg.set_alpha(220)

  # Players is a list of hashes, not Player objects; it should have all
  # config information set to some value already (player_config in constants)
  def __init__(self, players, title, menu, colors):
    self.players = players
    self.current = [0] * len(players)
    self.menu = menu
    self.title = title
    self.colors = colors

  def display(self, screen):
    baseimage = pygame.transform.scale(screen, (640,480))

    # Animate the menu opening
    if mainconfig['gratuitous']:
      t = pygame.time.get_ticks()
      eyecandyimage = pygame.surface.Surface((640, 480))
      while pygame.time.get_ticks() - t < 300:
        p = float(pygame.time.get_ticks() - t) / 300
        eyecandyimage.blit(baseimage, (0,0))
        scaledbg = pygame.transform.scale(OptionScreen.bg,(int(580 * p), 480))
        scaledbg.set_alpha(220)
        r = scaledbg.get_rect()
        r.center = (320, 240)
        up = eyecandyimage.blit(scaledbg, r)
        screen.blit(eyecandyimage, (0, 0))
        pygame.display.update(up)
    
    baseimage.blit(OptionScreen.bg, (30, 0))

    self.baseimage = baseimage
    
    screen.blit(baseimage, (0, 0))
    pygame.display.update()
    
    ev = E_PASS
    
    while not (ev == E_START or ev == E_QUIT or ev == E_MARK):
      self.render(screen)
      
      pid, ev = event.wait()
      pid = min(pid, len(self.current) - 1)

      if ev == E_DOWN:
        self.current[pid] = (self.current[pid] + 1) % len(self.menu)
        
      elif ev == E_UP:
        self.current[pid] = (self.current[pid] - 1) % len(self.menu)
        
      elif ev == E_LEFT:
        optname = self.menu[self.current[pid]][1]
        cur_val = self.players[pid][optname]
        values = copy.copy(self.menu[self.current[pid]][2])
        values.reverse()
        
        next = False
        for val in values:
          if next:
            self.players[pid][optname] = val[0]
            break
          elif self.players[pid][optname] == val[0]: next = True

      elif ev == E_RIGHT:
        optname = self.menu[self.current[pid]][1]
        cur_val = self.players[pid][optname]
        values = self.menu[self.current[pid]][2]

        next = False
        for val in values:
          if next:
            self.players[pid][optname] = val[0]
            break
          elif self.players[pid][optname] == val[0]: next = True

      elif ev == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

    return (ev == E_START)

  def render(self, screen):
    rect = ((45, 5), (570, 470))
    blankimage = pygame.surface.Surface(rect[1]).convert_alpha()
    blankimage.fill([0, 0, 0, 0])

    for i in range(len(self.menu)):
      color = None
      for j in range(len(self.current)):
        if i == self.current[j]:
          if not color: color = self.colors[j]
          else: color = colors.average(color, self.colors[j])
      if not color: color = colors.WHITE

      item = self.menu[i]
      name, opt, values = item
      text = FONTS[24].render(name, 1, color)
      blankimage.blit(text, (10, 70 + 28 * i))
      width = 480 / (len(values) + 1)
      for k in range(len(values)):
        color = None
        for plr in range(len(self.players)):
          self.players[plr]
          if values[k][0] == self.players[plr][opt]:
            FONTS[24].set_underline(True)
            newcolor = self.colors[plr]
            if not color: color = newcolor
            else: color = colors.average(color, newcolor)
        if not color:
            FONTS[24].set_underline(False)
            color = colors.WHITE

        text = FONTS[24].render(values[k][1], 1, color)
        blankimage.blit(text, (120 + width * k, 70 + 28 * i))

      FONTS[24].set_underline(False)

    if len(self.current) > 1:
      faketext = " / ".join([str(i+1) for i in range(len(self.current))])
      faketext = "Players: " + faketext
      textimage = pygame.surface.Surface(FONTS[16].size(faketext))
      textimage.set_colorkey(textimage.get_at((0, 0)))
      text = FONTS[16].render("Players: ", 1, colors.WHITE)
      textimage.blit(text, (0, 0))
      xpos = text.get_width()
      for i in range(len(self.current)):
        text = FONTS[16].render(str(i+1), 1, self.colors[i])
        textimage.blit(text, (xpos, 0))
        xpos += text.get_width()
        if i != len(self.current) - 1:
          text = FONTS[16].render(" / ", 1, colors.WHITE)
          textimage.blit(text, (xpos, 0))
          xpos += text.get_width()

      r = textimage.get_rect()
      r.center = (blankimage.get_rect().centerx, 450)
      blankimage.blit(textimage, r)


    text = FONTS[40].render(self.title, 1, colors.WHITE)
    blankimage.blit(text, (45, 64-text.get_height()))

    screen.blit(self.baseimage, (0, 0))
    screen.blit(blankimage, rect)
    pygame.display.update()
