# The song selector; take songs with metadata, output pretty pictures,
# let people select difficulties, and dance.

import os, string, pygame, random, copy, dance
from constants import *

import announcer, audio, colors, optionscreen, error, games

# FIXME: this needs to be moved elsewhere if we want theming
ITEM_BG = pygame.image.load(os.path.join(image_path, "ss-item-bg.png"))
FOLDER_BG = pygame.image.load(os.path.join(image_path, "ss-folder-bg.png"))
NO_BANNER = pygame.image.load(os.path.join(image_path, "no-banner.png"))
NO_BANNER.set_colorkey(NO_BANNER.get_at((0, 0)))
BACKGROUND = os.path.join(image_path, "ss-bg.png")
MOVE_SOUND = pygame.mixer.Sound(os.path.join(sound_path, "move.ogg"))
OPEN_SOUND = pygame.mixer.Sound(os.path.join(sound_path, "back.ogg"))

difficulty_colors = { "BEGINNER": colors.color["white"],
                      "LIGHT": colors.color["orange"],
                      "EASY": colors.color["orange"],
                      "BASIC": colors.color["orange"],
                      "STANDARD": colors.color["red"],
                      "STANDER": colors.color["red"], # Shit you not, 3 people.
                      "TRICK": colors.color["red"],
                      "MEDIUM": colors.color["red"],
                      "DOUBLE": colors.color["red"],
                      "ANOTHER": colors.color["red"],
                      "PARA": colors.color["red"], # This seems to be random
                      "NORMAL": colors.color["red"],
                      "MANIAC": colors.color["green"],
                      "HARD": colors.color["green"],
                      "HEAVY": colors.color["green"],
                      "HARDCORE": colors.color["purple"],
                      "SMANIAC": colors.color["purple"],
                      "S-MANIAC": colors.color["purple"], # Very common typo
                      "CHALLENGE": colors.color["purple"],
                      "CRAZY": colors.color["purple"],
                      "EXPERT": colors.color["purple"]
                      }

ITEM_SIZE = (344, 60)
ITEM_X = [240, 250, 270, 300, 340, 390, 460]
BANNER_CENTER = (133, 45)
BANNER_SIZE = (256, 80)
DIFF_BOX_SIZE = (15, 25)
DIFF_LOCATION = (8, 120)

# FIXME: DSU at some point in the future.
SORTS = {
  "subtitle": (lambda x, y: cmp(str(x.song.info["subtitle"]).lower(),
                                str(y.song.info["subtitle"]).lower())),
  "title": (lambda x, y: (cmp(x.song.info["title"].lower(),
                              y.song.info["title"].lower()) or
                          SORTS["subtitle"](x, y))),
  "artist": (lambda x, y: (cmp(x.song.info["artist"].lower(),
                               y.song.info["artist"].lower()) or
                           SORTS["title"](x, y))),
  "bpm": (lambda x, y: (cmp(x.song.info["bpm"], y.song.info["bpm"]) or
                        SORTS["title"](x, y))),
  "mix": (lambda x, y: (cmp(str(x.song.info["mix"]).lower(),
                            str(y.song.info["mix"]).lower()) or
                        SORTS["title"](x, y)))
  }

SORT_NAMES = ["mix", "title", "artist", "bpm"]

NUM_SORTS = len(SORT_NAMES)

# Make a beveled box of a specific color - used for difficulty ratings
def make_box(color):
  img = pygame.surface.Surface(DIFF_BOX_SIZE)
  light_color = colors.brighten(color)
  dark_color = colors.darken(color)
  img.fill(color)
  pygame.draw.line(img, light_color, (0,0), (0, DIFF_BOX_SIZE[1] - 1))
  pygame.draw.line(img, light_color, (0,0), (DIFF_BOX_SIZE[0] - 1, 0))
  pygame.draw.line(img, dark_color, (DIFF_BOX_SIZE[0]-1, DIFF_BOX_SIZE[1]-1),
                   (0, DIFF_BOX_SIZE[1] - 1))
  pygame.draw.line(img, dark_color, (DIFF_BOX_SIZE[0]-1, DIFF_BOX_SIZE[1]-1),
                   (DIFF_BOX_SIZE[0] - 1, 0))
  return img

# Wrap a SongItem object in a way that we can render it.
class SongItemDisplay(object):
  def __init__(self, song):
    self.song = song
    self.banner = None
    self.menuimage = None
    self.isfolder = False
    self.folder = {}

  # Do the actual rendering
  def render(self):
    info = self.song.info

    # Cache it for fast access later
    if self.banner == None:
      if info["banner"]:
        # A postcondition of file parsers is that this is a valid filename
        banner = pygame
        banner = pygame.image.load(info["banner"]).convert()
        if list(banner.get_rect().size) == [300, 200]: # KSF-style banner
          self.banner = pygame.transform.rotozoom(banner, 0, 0.4).convert()
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
        elif list(banner.get_rect().size) == [93, 92]: # Parapara-style banner
          self.banner = pygame.transform.rotozoom(banner, 0, 0.87).convert()
        elif banner.get_rect().size[0] != banner.get_rect().size[1]:
          self.banner = pygame.transform.scale(banner, BANNER_SIZE)
        else:
          # One of the older banners that we need to rotate
          # Don't scale, because it's hard to calculate and looks bad
          banner.set_colorkey(banner.get_at((0,0)), RLEACCEL)
          self.banner = pygame.transform.rotozoom(banner, -45, 1.0)
      else:
        # FIXME: We can probably generate an okay-looking banner from the
        # song metadata.
        self.banner = NO_BANNER
        self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      self.banner_rect = self.banner.get_rect()
      self.banner_rect.center = BANNER_CENTER

      rcolors = ["green", "orange", "yellow", "red", "purple", "aqua"]
      # Start with a random color, but...
      color = colors.color[rcolors[random.randint(0, len(rcolors) - 1)]]

      if info["mix"]: # ... pick a consistent mix color
        idx = hash(info["mix"].lower()) % len(rcolors)
        color = colors.color[rcolors[idx]]

      color = colors.brighten(color, 145)

      self.menuimage = pygame.surface.Surface(ITEM_SIZE)
      self.menuimage.blit(ITEM_BG, (0,0))
      songtext = FONTS[26].render(info["title"], 1, color)
      self.menuimage.blit(songtext, (10, 5))

      subtext_text = ""
      if info["subtitle"]: subtext_text += info["subtitle"] + " / "
      if info["mix"]: subtext_text += info["mix"] + " / "
      subtext_text  += "bpm: " + str(int(info["bpm"]))

      subtext = FONTS[14].render(subtext_text, 1, color)
      self.menuimage.blit(subtext, (30, 26))
      st = "by " + info["artist"]
      grouptext = FONTS[20].render(st, 1, color)
      self.menuimage.blit(grouptext, (15, 36))

# Handle previewing songs, fading in/out.
class SongPreview(object):
  def __init__(self):
    self.playing = False
    self.filename = None
    self.end_time = self.start_time = 0
    if not mainconfig["previewmusic"]:
      audio.load(os.path.join(sound_path, "menu.ogg"))
      audio.play(4, 0.0)

  def preview(self, song):
    if mainconfig["previewmusic"] and not song.isfolder:
      if len(song.song.info["preview"]) == 2:
        # A DWI/SM/dance-style preview, an offset in the song and a length
        # to play starting at the offset.
        self.start, length = song.song.info["preview"]
        self.filename = song.song.info["filename"]
      else:
        # KSF-style preview, a separate filename to play.
        self.start, length = 0, 100
        self.filename = song.song.info["preview"]
      if self.playing: audio.fadeout(500)
      self.playing = False
      self.start_time = pygame.time.get_ticks() + 500
      self.end_time = int(self.start_time + length * 1000)
    elif song.isfolder: audio.fadeout(500)

  # Python evaluates default parameters at instantiate-time or something,
  # so we can't set a default value of time = pygame.time.get_ticks() here.
  def update(self, time):
    if self.filename is None: pass
    elif time < self.start_time: pass
    elif not self.playing:
      try:
        audio.load(self.filename)
        audio.set_volume(0.01) # 0.0 stops pygame.mixer.music.
        audio.play(0, self.start)
        self.playing = True
      except: # Filename not found? Song is too short? SMPEG blows?
        audio.stop()
        self.playing = False
    elif time < self.start_time + 1000: # mixer.music can't fade in, only out.
      audio.set_volume((time - self.start_time) / 1000.0)
    elif time > self.end_time - 1000:
      audio.fadeout(1000)
      self.playing = False
      self.filename = None

class FolderDisplay(object):
  def __init__(self, name, type, numsongs):
    self.name = name
    self.type = type
    self.isfolder = True
    self.banner = None
    self.menuimage = None
    self.numsongs = numsongs

  # Folder banners can be either in rc_path/banners/sorttype/name.png, or
  # common for DWIs, mixdir/banner.png (for mixdir/songdir/song.dwi).
  def find_banner(self):
    name = self.name.encode("ascii", "ignore")
    for path in (rc_path, pyddr_path):
      filename = os.path.join(path, "banners", self.type, name + ".png")
      if os.path.exists(filename):
        banner = pygame.image.load(filename).convert()
        if banner.get_rect().size[0] != banner.get_rect().size[1]:
          self.banner = pygame.transform.scale(banner, BANNER_SIZE)
        else:
          banner.set_colorkey(banner.get_at((0,0)), RLEACCEL)
          self.banner = pygame.transform.rotate(banner, -45)
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
        break

    else:
      if self.type == "mix":
        for dir in mainconfig["songdir"].split(":"):
          dir = os.path.expanduser(dir)
          filename = os.path.join(dir, name, "banner.png")
          if os.path.exists(filename):
            banner = pygame.image.load(filename).convert()
            if banner.get_rect().size[0] != banner.get_rect().size[1]:
              self.banner = pygame.transform.scale(banner, BANNER_SIZE)
            else:
              banner.set_colorkey(banner.get_at((0,0)), RLEACCEL)
              self.banner = pygame.transform.rotate(banner, -45)
              self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
            break
        else:
          self.banner = NO_BANNER
          self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)
      else:
        self.banner = NO_BANNER
        self.banner.set_colorkey(self.banner.get_at((0,0)), RLEACCEL)

  def render(self):
    if self.banner == None:
      self.find_banner()
      self.banner_rect = self.banner.get_rect()
      self.banner_rect.center = BANNER_CENTER
      self.menuimage = pygame.surface.Surface(ITEM_SIZE)
      self.menuimage.blit(FOLDER_BG, [0, 0])
      songtext = FONTS[36].render(self.name, 1, colors.WHITE)
      if songtext.get_size()[0] > ITEM_SIZE[0] - 20:
        songtext = pygame.transform.scale(songtext, [ITEM_SIZE[0] - 20,
                                                     songtext.get_size()[1]])
      self.menuimage.blit(songtext, [10, 5])
      grouptext = FONTS[20].render("%d songs" % self.numsongs, 1, colors.WHITE)
      self.menuimage.blit(grouptext, (15, 32))

class SongSelect(object):
  def __init__(self, songitems, screen, gametype):
    clock = pygame.time.Clock()

    self.songs = [SongItemDisplay(s) for s in songitems
                  if s.difficulty.has_key(gametype)]

    if len(self.songs) == 0:
      error.ErrorMessage(screen,
                         ["You don't have any songs with steps",
                          "for the game mode (%s) that you" % gametype.lower(),
                          "selected.",
                          " ", "Install more songs, try a different mode,",
                          "or enable autogeneration of steps."])
      return

    # Save the list of all the songs available, since self.songs will be
    # shortened in the case of folders.
    self.all_songs = self.songs

    self.random_songs = [s for s in self.all_songs if s.song.info["valid"]]

    players = games.GAMES[gametype].players

    self.bg = pygame.image.load(BACKGROUND).convert()
    ev = (0, E_PASS)
    self.numsongs = len(self.songs)

    self.gametype = gametype
    self.player_image = []
    self.player_diffs = []
    self.player_configs = []
    self.player_diff_names = []

    # In locked modes all players must have the same difficulty.
    locked = games.GAMES[gametype].couple

    diff_name = self.songs[0].song.diff_list[self.gametype][0]

    # Set up the data for each player.
    for i in range(players):
      image_fn = os.path.join(image_path, "player%d.png" % i)
      self.player_image.append(pygame.image.load(image_fn))
      self.player_diffs.append(0)
      self.player_configs.append(copy.copy(player_config))
      self.player_diff_names.append(diff_name)

    event.set_repeat(500, 30)

    self.diff_list = []
    self.song_list = []
    self.title_list = []
    self.screen = screen

    audio.fadeout(500) # The menu music.

    pygame.display.update(self.screen.blit(self.bg, (0, 0)))
    
    self.index = 0
    preview = SongPreview()

    self.game_config = copy.copy(game_config)

    if self.numsongs > 60 and mainconfig["folders"]:
      self.set_up_folders()
      name = SORT_NAMES[mainconfig["sortmode"]]
      folder = self.folders[name].keys()[0]
      self.set_up_songlist(folder)
    else:
      self.folders = None
      self.songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]])
    self.render(True)

    while ev[1] != E_QUIT:
      loop_start_time = pygame.time.get_ticks()

      self.oldindex = self.index
      changed = False

      ev = event.poll()

      # Skip events from a player that isn't in this game.
      if ev[0] >= players: continue

      if ev[1] in [E_LEFT, E_RIGHT, E_UP, E_DOWN, E_PGUP, E_PGDN, E_MARK]:
        MOVE_SOUND.play()

      # Scroll up the menu list
      if ev[1] == E_LEFT:
        self.index = (self.index - 1) % self.numsongs

      elif ev[1] == E_PGUP:
        self.scroll_out(self.index)
        self.index = (self.index - 7) % self.numsongs

      # Down the menu list
      elif ev[1] == E_RIGHT:
        self.index = (self.index + 1) % self.numsongs
  
      elif ev[1] == E_PGDN:
        self.scroll_out(self.index)
        self.index = (self.index + 7) % self.numsongs

      # Easier difficulty
      elif ev[1] == E_UP:
        if not self.songs[self.index].isfolder:
          self.player_diffs[ev[0]] -= 1
          self.player_diffs[ev[0]] %= len(self.current_song.diff_list[gametype])
          self.player_diff_names[ev[0]] = self.current_song.diff_list[gametype][self.player_diffs[ev[0]]]
          changed = True

      # Harder difficulty
      elif ev[1] == E_DOWN:
        if not self.songs[self.index].isfolder:
          self.player_diffs[ev[0]] += 1
          self.player_diffs[ev[0]] %= len(self.current_song.diff_list[gametype])
          self.player_diff_names[ev[0]] = self.current_song.diff_list[gametype][self.player_diffs[ev[0]]]
          changed = True

      # Open up a new folder
      elif ev[1] == E_START and self.songs[self.index].isfolder:
        OPEN_SOUND.play()
        self.scroll_out(self.index)
        self.set_up_songlist(self.songs[self.index].name)
        event.empty()
        changed = True

      # Start the dancing!
      elif ev[1] == E_START:
        # If we added the current song with E_MARK earlier, don't readd it
        try: self.title_list[-1].index(self.current_song.info["title"])
        except: self.add_current_song()
        ann = announcer.Announcer(mainconfig["djtheme"])
        ann.say("menu")
        # Wait for the announcer to finish
        try:
          while ann.chan.get_busy(): pygame.time.wait(1)
        except: pass

        event.set_repeat()
        if optionscreen.player_opt_driver(screen, self.player_configs):
          audio.fadeout(500)

          dance.play(screen, zip(self.song_list, self.diff_list),
                     self.player_configs, self.game_config, gametype)

          audio.fadeout(500) # This is the just-played song

          preview = SongPreview()

          event.empty()
          self.screen.blit(self.bg, (0, 0))
          pygame.display.flip()

        event.set_repeat(500, 30)
        changed = True

        # Reset the playlist
        self.song_list = []
        self.diff_list = []
        self.title_list = []

      # Add the current song to the playlist
      elif ev[1] == E_MARK:
        if not self.songs[self.index].isfolder:
          self.add_current_song()
          changed = True

      # Remove the most recently added song
      elif ev[1] == E_UNMARK:
	if self.title_list != []:
          self.title_list.pop()
          self.diff_list.pop()
          self.song_list.pop()
          changed = True

      # Remove all songs on the playlist
      elif ev[1] == E_CLEAR:
        self.title_list = []
        self.diff_list = []
        self.song_list = []
        changed = True

      elif ev[1] == E_SELECT:
        if optionscreen.game_opt_driver(screen, self.game_config):
          self.scroll_out(self.index)
          OPEN_SOUND.play()
          if len(self.random_songs) != 0:
            s = random.choice(self.random_songs)
            if self.folders:
              self.set_up_songlist(s.folder[SORT_NAMES[mainconfig["sortmode"]]])
            self.index = self.songs.index(s)
          else:
            error.ErrorMessage(screen, ["Although you have songs, they're all",
                                        "marked as invalid, which means a",
                                        "good random one can't be chosen."])
	changed = True

      elif ev[1] == E_SORT:
        s = self.songs[self.index]
        self.scroll_out(self.index)
        mainconfig["sortmode"] = (mainconfig["sortmode"] + 1) % NUM_SORTS
        if self.folders:
          if not s.isfolder:
            self.set_up_songlist(s.folder[SORT_NAMES[mainconfig["sortmode"]]])
            self.index = self.songs.index(s)
          else:
            keys = self.folders[SORT_NAMES[mainconfig["sortmode"]]].keys()
            keys.sort()
            self.set_up_songlist(keys[0])
            self.index = 0
        else:
          self.songs.sort(SORTS[SORT_NAMES[mainconfig["sortmode"]]])
          self.index = self.songs.index(s)
          self.oldindex = self.index # We're cheating!
        changed = True

      elif ev[1] == E_FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
        changed = True

      # This has to be after events, otherwise we do stuff to the wrong song.
      if not self.songs[self.index].isfolder:
        self.current_song = self.songs[self.index].song

      if locked and ev[1] in [E_UP, E_DOWN]:
        for i in range(len(self.player_diffs)):
          self.player_diffs[i] = self.player_diffs[ev[0]]
          self.player_diff_names[i] = self.player_diff_names[ev[0]]

      if self.index != self.oldindex and not self.songs[self.index].isfolder:
        for i in range(len(self.player_diff_names)):
          name = self.player_diff_names[i]
          if name in self.current_song.diff_list[self.gametype]:
            self.player_diffs[i] = self.current_song.diff_list[self.gametype].index(name)

      preview.update(pygame.time.get_ticks())

      if self.index != self.oldindex:
        preview.preview(self.songs[self.index])
        changed = True
        if self.index == (self.oldindex + 1) % self.numsongs:
          self.scroll_down()
        elif self.index == (self.oldindex - 1) % self.numsongs:
          self.scroll_up()
        else:
          changed = True
          self.scroll_in(self.index)

      self.render(changed)
      clock.tick(20)

    audio.fadeout(500)
    pygame.time.wait(500)
    # FIXME Does this belong in the menu code? Probably.
    audio.load(os.path.join(sound_path, "menu.ogg"))
    audio.set_volume(1.0)
    audio.play(4, 0.0)
    event.set_repeat()
    player_config.update(self.player_configs[0]) # Save player 1's settings

  def render(self, changed):
    self.screen.blit(self.bg, (0,0))

    # Difficulty list rendering
    if not self.songs[self.index].isfolder:
      difficulty = self.songs[self.index].song.difficulty[self.gametype]
      diff_list = self.songs[self.index].song.diff_list[self.gametype]
    else: diff_list = []

    # The song list
    for i in range(-4, 5):
      idx = (self.index + i) % self.numsongs
      self.songs[idx].render()
      x = ITEM_X[abs(i)]
      y = 210 + i * 60
      img = self.songs[idx].menuimage
      img.set_alpha(226 - (40 * abs(i)))
      self.screen.blit(self.songs[idx].menuimage, (x,y))
        
    # The banner
    self.screen.set_clip([[5, 5], [256, 80]])
    self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)
    self.screen.set_clip()

    # Render this in "reverse" order, from bottom to top
    temp_list = copy.copy(self.title_list)
    temp_list.reverse()

    for i in range(len(temp_list)):
      txt = FONTS[14].render(temp_list[i], 1, colors.WHITE)
      self.screen.blit(txt, (10, 480 - (FONTS[14].size("I")[1] - 2) *
                               (i + 2)))

    # Sort mode
    stxt = FONTS[20].render("sort by " + SORT_NAMES[mainconfig["sortmode"]],
                              1, colors.WHITE)
    rec = stxt.get_rect()
    rec.center = (DIFF_LOCATION[0] + 90, DIFF_LOCATION[1] - 10)
    self.screen.blit(stxt, rec)
  
    i = 0
    for d in diff_list:
      # Difficulty name
      text = d.lower()

      color = colors.color["gray"]
      if difficulty_colors.has_key(d):  color = difficulty_colors[d]

      if difficulty[d] >= 10: text += " - x" + str(difficulty[d])

      text = FONTS[26].render(text.lower(), 1, colors.brighten(color, 64))
      rec = text.get_rect()
      rec.center = (DIFF_LOCATION[0] + 92, DIFF_LOCATION[1] + 25 * i + 12)
      self.screen.blit(text, rec)

      # Difficulty boxes
      if difficulty[d] < 10:
        box = make_box(colors.brighten(color, 32))
        box.set_alpha(140)

        # Active boxes
        for j in range(int(difficulty[d])):
          self.screen.blit(box, (DIFF_LOCATION[0] + 25 + 15 * j,
                                   DIFF_LOCATION[1] + 25 * i))
        # Inactive boxes
        box.set_alpha(64)
        for j in range(int(difficulty[d]), 9):
          self.screen.blit(box, (DIFF_LOCATION[0] + 25 + 15 * j,
                                   DIFF_LOCATION[1] + 25 * i))
            
      # Player selection icons
      for j in range(len(self.player_diffs)):
        if diff_list.index(d) == (self.player_diffs[j] % len(diff_list)):
          self.screen.blit(self.player_image[j],
                           (DIFF_LOCATION[0] + 10 + 140 * j,
                            DIFF_LOCATION[1] + 25 * i))
      i += 1

    pygame.display.update()

  def scroll_up(self):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 75
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 75.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-5, 5):
        idx = (self.oldindex + k) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(k)] * q + ITEM_X[abs(k + 1)] * p
        y = 210 + int(60 * (k * q + (k + 1) * p))
        img = self.songs[idx].menuimage
        img.set_alpha(226 - int(40 * (abs(k) * q + abs(k + 1) * p)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      self.screen.set_clip([[5, 5], [256, 80]])
      self.songs[self.oldindex].banner.set_alpha(256 * q)
      self.screen.blit(self.songs[self.oldindex].banner,
                       self.songs[self.oldindex].banner_rect)
      self.songs[self.index].banner.set_alpha(256 * p)
      self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)
      self.screen.set_clip()
      pygame.display.update(r)

    self.songs[self.oldindex].banner.set_alpha(256)
    self.songs[self.index].banner.set_alpha(256)

  def scroll_down(self):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 75
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 75.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 6):
        idx = (self.oldindex + k) % self.numsongs
        self.songs[idx].render()
        x = ITEM_X[abs(k)] * q + ITEM_X[abs(k - 1)] * p
        y = 210 + int(60 * (k * q + (k - 1) * p))
        img = self.songs[idx].menuimage
        img.set_alpha(226 - int(40 * (abs(k) * q + abs(k - 1) * p)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      self.screen.set_clip([[5, 5], [256, 80]])
      self.songs[self.oldindex].banner.set_alpha(256 * q)
      self.screen.blit(self.songs[self.oldindex].banner,
                       self.songs[self.oldindex].banner_rect)
      self.songs[self.index].banner.set_alpha(256 * p)
      self.screen.blit(self.songs[self.index].banner,
                       self.songs[self.index].banner_rect)
      self.screen.set_clip()
      pygame.display.update(r)

    self.songs[self.oldindex].banner.set_alpha(256)
    self.songs[self.index].banner.set_alpha(256)

  def scroll_out(self, index):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 200
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 200.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 5): # Redraw the song items
        idx = (index + k) % self.numsongs
        self.songs[idx].render()
        x = max(240 + int((866 - 240) * p) - 50 * k, ITEM_X[abs(k)])
        y = 210 + k * 60
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      pygame.display.update(r)

  def scroll_in(self, index):
    if not mainconfig["gratuitous"]: return
    r = [Rect((5, 5), (256, 80)), Rect((240, 0), (400, 480))]
    end_time = pygame.time.get_ticks() + 150
    cur_time = pygame.time.get_ticks()
    while cur_time < end_time:
      cur_time = pygame.time.get_ticks()
      q = min(1, max(0, (end_time - cur_time) / 150.0))
      p = 1 - q
      self.screen.blit(self.bg, (0,0))
      for k in range(-4, 5): # Redraw song items
        idx = (index + k) % self.numsongs
        self.songs[idx].render()
        x = max(214 + int((840 - 214) * q) - 50 * k, ITEM_X[abs(k)])
        y = 210 + k * 60
        self.songs[idx].menuimage.set_alpha(226 - (40 * abs(k)))
        self.screen.blit(self.songs[idx].menuimage, (x,y))
      pygame.display.update(r)

  def add_current_song(self):
    self.song_list.append(self.current_song.filename)
    l = len(self.current_song.diff_list[self.gametype])
    new_diff = map((lambda i: self.current_song.diff_list[self.gametype][i%l]),
                   self.player_diffs)
    self.diff_list.append(new_diff)
    # Pseudo-pretty difficulty tags for each player.
    text = self.current_song.info["title"] + " "
    for d in self.diff_list[-1]: text += "/" + d[0]
    self.title_list.append(text)

  def set_up_folders(self):
    mixnames = {}
    artists = {}
    titles = {}
    bpms = {}

    for si in self.all_songs:
      if not mixnames.has_key(si.song.info["mix"]):
        mixnames[si.song.info["mix"]] = []
      mixnames[si.song.info["mix"]].append(si)
      si.folder["mix"] = si.song.info["mix"]

      label = si.song.info["title"][0].capitalize()
      if not titles.has_key(label): titles[label] = []
      titles[label].append(si)
      si.folder["title"] = label

      label = si.song.info["artist"][0].capitalize()
      if not artists.has_key(label): artists[label] = []
      artists[label].append(si)
      si.folder["artist"] = label

      for rng in ((0, 50), (50, 100), (100, 121), (110, 120),
                  (120, 130), (130, 140), (140, 150), (150, 160), (160, 170),
                  (170, 180), (180, 190), (190, 200), (200, 225), (225, 250),
                  (250, 275), (275, 300)):
        label = "%d-%d" % rng
        if rng[0] < si.song.info["bpm"] <= rng[1]:
          if not bpms.has_key(label): bpms[label] = []
          bpms[label].append(si)
          si.folder["bpm"] = label
      if si.song.info["bpm"] >= 300:
        if not bpms.has_key("300+"): bpms["300+"] = []
        bpms["300+"].append(si)
        si.folder["bpm"] = "300+"

    self.folders = { "mix": mixnames, "title": titles,
                     "artist": artists, "bpm": bpms }

  def set_up_songlist(self, selected_folder):
    sort = SORT_NAMES[mainconfig["sortmode"]]

    songlist = self.folders[sort][selected_folder]
    folderlist = self.folders[sort].keys()

    folderlist.sort(lambda x, y: cmp(x.lower(), y.lower()))
    songlist.sort(SORTS[sort])

    new_songs = []
    for folder in folderlist:
      new_songs.append(FolderDisplay(folder, sort,
                                     len(self.folders[sort][folder])))
      if folder == selected_folder: new_songs.extend(songlist)

    self.songs = new_songs
    self.numsongs = len(self.songs)
    self.index = folderlist.index(selected_folder)
    self.oldindex = -2
