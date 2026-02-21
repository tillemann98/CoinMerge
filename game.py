import pygame
import random
import sys
import json
import os

# Detect available pygame font backends to avoid repeated import errors/warnings
HAVE_PYGAME_FONT = False
HAVE_PYGAME_FREETYPE = False
try:
	import pygame.font as _pygame_font
	if hasattr(_pygame_font, 'SysFont'):
		HAVE_PYGAME_FONT = True
except Exception:
	HAVE_PYGAME_FONT = False

try:
	import pygame.freetype as _pygame_freetype
	if hasattr(_pygame_freetype, 'SysFont'):
		HAVE_PYGAME_FREETYPE = True
except Exception:
	HAVE_PYGAME_FREETYPE = False


WIDTH, HEIGHT = 1280, 720
SLOT_CAPACITY = 10
INITIAL_SLOTS = 5


class Slot:
	def __init__(self):
		self.coin = 0  # 0 means empty, otherwise coin level (1,2,...)
		self.count = 0

	def is_empty(self):
		return self.coin == 0


def format_coin_label(level):
	return f"C{level}"


def coin_value(level):
	# base value for a combined coin of given level
	return 10 * (2 ** (level - 1))


def make_button(rect, label):
	return {"rect": pygame.Rect(rect), "label": label}


# Simple 5x7 bitmap font (supports A-Z, 0-9, space, colon, and a few symbols)
BITMAP_FONT = {
	" ": [0x00,0x00,0x00,0x00,0x00,0x00,0x00],
	":": [0x00,0x18,0x18,0x00,0x00,0x18,0x18],
	"0": [0x0E,0x11,0x13,0x15,0x19,0x11,0x0E],
	"1": [0x04,0x0C,0x04,0x04,0x04,0x04,0x0E],
	"2": [0x0E,0x11,0x01,0x06,0x08,0x10,0x1F],
	"3": [0x0E,0x11,0x01,0x06,0x01,0x11,0x0E],
	"4": [0x02,0x06,0x0A,0x12,0x1F,0x02,0x02],
	"5": [0x1F,0x10,0x1E,0x01,0x01,0x11,0x0E],
	"6": [0x06,0x08,0x10,0x1E,0x11,0x11,0x0E],
	"7": [0x1F,0x11,0x02,0x04,0x04,0x04,0x04],
	"8": [0x0E,0x11,0x11,0x0E,0x11,0x11,0x0E],
	"9": [0x0E,0x11,0x11,0x0F,0x01,0x02,0x0C],
	"A": [0x0E,0x11,0x11,0x1F,0x11,0x11,0x11],
	"B": [0x1E,0x11,0x11,0x1E,0x11,0x11,0x1E],
	"C": [0x0E,0x11,0x10,0x10,0x10,0x11,0x0E],
	"D": [0x1C,0x12,0x11,0x11,0x11,0x12,0x1C],
	"E": [0x1F,0x10,0x10,0x1E,0x10,0x10,0x1F],
	"F": [0x1F,0x10,0x10,0x1E,0x10,0x10,0x10],
	"G": [0x0E,0x11,0x10,0x17,0x11,0x11,0x0F],
	"H": [0x11,0x11,0x11,0x1F,0x11,0x11,0x11],
	"I": [0x0E,0x04,0x04,0x04,0x04,0x04,0x0E],
	"J": [0x07,0x02,0x02,0x02,0x02,0x12,0x0C],
	"K": [0x11,0x12,0x14,0x18,0x14,0x12,0x11],
	"L": [0x10,0x10,0x10,0x10,0x10,0x10,0x1F],
	"M": [0x11,0x1B,0x15,0x15,0x11,0x11,0x11],
	"N": [0x11,0x19,0x15,0x13,0x11,0x11,0x11],
	"O": [0x0E,0x11,0x11,0x11,0x11,0x11,0x0E],
	"P": [0x1E,0x11,0x11,0x1E,0x10,0x10,0x10],
	"Q": [0x0E,0x11,0x11,0x11,0x15,0x12,0x0D],
	"R": [0x1E,0x11,0x11,0x1E,0x14,0x12,0x11],
	"S": [0x0F,0x10,0x10,0x0E,0x01,0x01,0x1E],
	"T": [0x1F,0x04,0x04,0x04,0x04,0x04,0x04],
	"U": [0x11,0x11,0x11,0x11,0x11,0x11,0x0E],
	"V": [0x11,0x11,0x11,0x11,0x11,0x0A,0x04],
	"W": [0x11,0x11,0x11,0x15,0x15,0x1B,0x11],
	"X": [0x11,0x11,0x0A,0x04,0x0A,0x11,0x11],
	"Y": [0x11,0x11,0x11,0x0A,0x04,0x04,0x04],
	"Z": [0x1F,0x01,0x02,0x04,0x08,0x10,0x1F],
	"-": [0x00,0x00,0x00,0x1F,0x00,0x00,0x00],
	"/": [0x01,0x02,0x04,0x08,0x10,0x00,0x00],
	"?": [0x0E,0x11,0x01,0x06,0x04,0x00,0x04],
	"%": [0x18,0x19,0x02,0x04,0x08,0x13,0x03],
}


def render_bitmap_text(text, color=(255, 255, 255), scale=2, spacing=1):
	text = text.upper()
	rows = 7
	char_w = 5
	width = sum((char_w * scale) + spacing for _ in text) - spacing
	height = rows * scale
	surf = pygame.Surface((width, height), pygame.SRCALPHA)
	x = 0
	for ch in text:
		pattern = BITMAP_FONT.get(ch, BITMAP_FONT.get('?', BITMAP_FONT[' ']))
		for y in range(rows):
			row = pattern[y]
			for bit in range(char_w):
				if row & (1 << (char_w - 1 - bit)):
					rx = x + bit * scale
					ry = y * scale
					pygame.draw.rect(surf, color, (rx, ry, scale, scale))
		x += char_w * scale + spacing
	return surf


coin_surfaces = {}


def get_coin_surface(level):
	# cache simple generated coin icon surfaces
	if level in coin_surfaces:
		return coin_surfaces[level]
	size = 72
	surf = pygame.Surface((size, size), pygame.SRCALPHA)
	colors = [(220, 180, 60), (180, 220, 100), (160, 160, 240), (240, 160, 200), (200, 200, 200)]
	color = colors[(level - 1) % len(colors)]
	pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2)
	pygame.draw.circle(surf, (255, 255, 255), (size // 2, size // 2), size // 2, 2)
	# render the level number using whatever font rendering is available
	if HAVE_PYGAME_FONT:
		try:
			lbl = _pygame_font.SysFont(None, 28).render(str(level), True, (10, 10, 10))
			surf.blit(lbl, (size // 2 - lbl.get_width() // 2, size // 2 - lbl.get_height() // 2))
		except Exception:
			# fall through to other backends
			pass
	if HAVE_PYGAME_FREETYPE:
		try:
			lbl_surf, _ = _pygame_freetype.SysFont(None, 28).render(str(level), fgcolor=(10, 10, 10))
			surf.blit(lbl_surf, (size // 2 - lbl_surf.get_width() // 2, size // 2 - lbl_surf.get_height() // 2))
		except Exception:
			pass
	# final fallback: bitmap font
	if not HAVE_PYGAME_FONT and not HAVE_PYGAME_FREETYPE:
		try:
			bm = render_bitmap_text(str(level), color=(10, 10, 10), scale=3)
			surf.blit(bm, (size // 2 - bm.get_width() // 2, size // 2 - bm.get_height() // 2))
		except Exception:
			pass
	coin_surfaces[level] = surf
	return surf


def add_coin_to_slots(slots, level):
	# place a single coin of `level` into the first available slot
	# prefer same-level slots with space, else empty slots
	for s in slots:
		if s.coin == level and s.count < SLOT_CAPACITY:
			s.count += 1
			return True
	for s in slots:
		if s.is_empty():
			s.coin = level
			s.count = 1
			return True
	return False


def process_combines(slots, currency, prestige_mult):
	# for each slot, if count >= SLOT_CAPACITY, combine into next level
	gained = 0
	for s in slots:
		if s.is_empty():
			continue
		# while there are enough coins to promote
		while s.count >= SLOT_CAPACITY:
			carry = s.count // SLOT_CAPACITY
			s.count = s.count % SLOT_CAPACITY
			# increase coin level by carry, and award currency for each promotion
			for _ in range(carry):
				s.coin += 1
				gained += coin_value(s.coin)
		# if count dropped to zero, mark slot empty
		if s.count == 0:
			s.coin = 0
	gained = int(gained * prestige_mult)
	currency += gained
	return currency, gained


def weighted_random_coin(max_level=5):
	# weights favor lower coins; allow up to max_level
	base_weights = [50, 30, 12, 6, 2]
	weights = base_weights[:max_level]
	return random.choices(range(1, len(weights) + 1), weights=weights, k=1)[0]


def main():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Combine them!")
	clock = pygame.time.Clock()

	# robust font setup: choose available backend
	use_freetype = False
	font = None
	big_font = None
	small_font = None
	if HAVE_PYGAME_FONT:
		try:
			font = _pygame_font.SysFont(None, 22)
			big_font = _pygame_font.SysFont(None, 28)
			small_font = _pygame_font.SysFont(None, 18)
		except Exception:
			font = None
			big_font = None
			small_font = None
	if font is None and HAVE_PYGAME_FREETYPE:
		try:
			font = _pygame_freetype.SysFont(None, 24)
			big_font = _pygame_freetype.SysFont(None, 36)
			small_font = _pygame_freetype.SysFont(None, 18)
			use_freetype = True
		except Exception:
			font = None
			big_font = None
			small_font = None

	def render_text(f, text, color=(255, 255, 255)):
		# if a pygame font backend is available, use it; otherwise fallback to bitmap
		if f is None:
			return render_bitmap_text(text, color=color, scale=2)
		if use_freetype:
			try:
				surf, _ = f.render(text, fgcolor=color)
				return surf
			except Exception:
				return render_bitmap_text(text, color=color, scale=2)
		else:
			try:
				return f.render(text, True, color)
			except Exception:
				return render_bitmap_text(text, color=color, scale=2)

	slots = [Slot() for _ in range(INITIAL_SLOTS)]
	unlocked_slots = INITIAL_SLOTS
	currency = 0
	prestige_mult = 1.0
	prestige_level = 0

	# UI buttons
	btn_deal = make_button((50, 600, 160, 40), "Deal Coins")
	btn_buy_slot = make_button((230, 600, 160, 40), "Buy Slot")
	btn_prestige = make_button((410, 600, 160, 40), "Prestige")
	btn_save = make_button((50, 650, 120, 34), "Save")
	btn_load = make_button((190, 650, 120, 34), "Load")
	btn_fullscreen = make_button((350, 650, 140, 34), "Fullscreen")
	# buy coin buttons for types 1-3 (wider and more spaced to fit labels)
	btn_buy_coin = []
	buy_base_x = 600
	buy_spacing = 150
	buy_width = 140
	for i in range(3):
		btn_buy_coin.append(make_button((buy_base_x + i * buy_spacing, 600, buy_width, 40), f"Buy C{i+1}"))

	# dragging state
	dragging = False
	drag_level = None
	drag_surf = None
	drag_src = None
	drag_pos = (0, 0)

	is_fullscreen = False

	def slot_rect(index):
		slot_w = 140
		slot_h = 140
		margin = 20
		start_x = 50
		start_y = 50
		x = start_x + (index % 8) * (slot_w + margin)
		y = start_y + (index // 8) * (slot_h + margin)
		return pygame.Rect(x, y, slot_w, slot_h)

	running = True
	last_gain = 0

	while running:
		dt = clock.tick(60) / 1000.0

		# compute dynamic buy options each frame
		current_max = 0
		for s in slots:
			if s.coin > current_max:
				current_max = s.coin
		# highest purchasable is always one below current highest merged
		if current_max >= 1:
			highest_purchasable = max(1, current_max - 1)
		else:
			highest_purchasable = 1
		buy_levels = [max(1, highest_purchasable - 2), max(1, highest_purchasable - 1), highest_purchasable]

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				mx, my = event.pos
				# check for slot click to start dragging (priority)
				clicked_slot = None
				for i in range(len(slots)):
					rect = slot_rect(i)
					if rect.collidepoint((mx, my)) and i < unlocked_slots and not slots[i].is_empty():
						clicked_slot = i
						break
				if clicked_slot is not None and not dragging:
					# pick up one coin from the slot
					src = slots[clicked_slot]
					drag_level = src.coin
					src.count -= 1
					if src.count <= 0:
						src.coin = 0
					drag_surf = get_coin_surface(drag_level)
					drag_src = clicked_slot
					dragging = True
					drag_pos = event.pos
					continue
				# UI handling
				if btn_deal["rect"].collidepoint((mx, my)):
					# deal one coin per unlocked slot
					for _ in range(unlocked_slots):
						lvl = weighted_random_coin(max_level=min(5, unlocked_slots))
						add_coin_to_slots(slots, lvl)
					currency, last_gain = process_combines(slots, currency, prestige_mult)
				elif btn_buy_slot["rect"].collidepoint((mx, my)):
					cost = 100 * (2 ** (unlocked_slots - INITIAL_SLOTS))
					if currency >= cost:
						currency -= cost
						slots.append(Slot())
						unlocked_slots += 1
					# update label so price shows
					btn_buy_slot["label"] = f"Buy Slot ({cost})"
				elif btn_fullscreen["rect"].collidepoint((mx, my)):
					# toggle fullscreen
					is_fullscreen = not is_fullscreen
					if is_fullscreen:
						screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
					else:
						screen = pygame.display.set_mode((WIDTH, HEIGHT))
				elif btn_prestige["rect"].collidepoint((mx, my)):
					# simple prestige: require minimum currency and reset progress
					if unlocked_slots > INITIAL_SLOTS or currency >= 1000:
						prestige_level += 1
						prestige_mult = 1.0 + prestige_level * 0.1
						currency = 0
						slots = [Slot() for _ in range(INITIAL_SLOTS)]
						unlocked_slots = INITIAL_SLOTS
				# Save/load handlers (separate from prestige)
				elif btn_save["rect"].collidepoint((mx, my)):
					save_path = os.path.join(os.path.dirname(__file__), "save.json")
					saved = save_game(save_path, slots, unlocked_slots, currency, prestige_level)
					# no blocking UI; last_gain used to show feedback
					last_gain = 0 if saved else -1
				elif btn_load["rect"].collidepoint((mx, my)):
					save_path = os.path.join(os.path.dirname(__file__), "save.json")
					data = load_game(save_path)
					if data:
						slots = [Slot() for _ in range(data.get("unlocked_slots", INITIAL_SLOTS))]
						for i, sdata in enumerate(data.get("slots", [])):
							if i < len(slots):
								slots[i].coin = sdata.get("coin", 0)
								slots[i].count = sdata.get("count", 0)
						unlocked_slots = data.get("unlocked_slots", INITIAL_SLOTS)
						currency = data.get("currency", 0)
						prestige_level = data.get("prestige_level", 0)
						prestige_mult = 1.0 + prestige_level * 0.1
				# Buy coin buttons (always active)
				else:
					for i, b in enumerate(btn_buy_coin):
						lvl = buy_levels[i]
						cost = coin_value(lvl)
						if b["rect"].collidepoint((mx, my)):
							if currency >= cost and lvl <= highest_purchasable:
								currency -= cost
								add_coin_to_slots(slots, lvl)
								currency, last_gain = process_combines(slots, currency, prestige_mult)
			elif event.type == pygame.MOUSEMOTION:
				if dragging:
					drag_pos = event.pos
			elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
				if dragging:
					mx, my = event.pos
					target = None
					for i in range(len(slots)):
						rect = slot_rect(i)
						if rect.collidepoint((mx, my)) and i < unlocked_slots:
							target = i
							break
					# drop logic
					if target is None:
						# return to source
						if drag_src is not None and drag_src < len(slots):
							slots[drag_src].coin = drag_level if slots[drag_src].coin == 0 else slots[drag_src].coin
							slots[drag_src].count += 1
						else:
							# try to find an empty slot
							placed = False
							for s in slots:
								if s.is_empty():
									s.coin = drag_level
									s.count = 1
									placed = True
									break
							if not placed:
								# discard (shouldn't happen)
								pass
					else:
						# place into target
						t = slots[target]
						if t.is_empty():
							t.coin = drag_level
							t.count = 1
						elif t.coin == drag_level:
							# same kind: add one, then process combines
							if t.count < SLOT_CAPACITY:
								t.count += 1
							else:
								t.count += 1
							currency, last_gain = process_combines(slots, currency, prestige_mult)
						else:
							# different kind: return to source
							if drag_src is not None and drag_src < len(slots):
								slots[drag_src].count += 1
							else:
								for s in slots:
									if s.is_empty():
										s.coin = drag_level
										s.count = 1
										break
					# clear dragging state
					dragging = False
					drag_level = None
					drag_surf = None
					drag_src = None
					drag_pos = (0, 0)


		screen.fill((30, 30, 40))

		# draw slots
		slot_w = 140
		slot_h = 140
		margin = 20
		start_x = 50
		start_y = 50
		for i, s in enumerate(slots):
			x = start_x + (i % 8) * (slot_w + margin)
			y = start_y + (i // 8) * (slot_h + margin)
			rect = pygame.Rect(x, y, slot_w, slot_h)
			color = (70, 70, 90) if i < unlocked_slots else (40, 40, 50)
			pygame.draw.rect(screen, color, rect, border_radius=8)
			pygame.draw.rect(screen, (120, 120, 140), rect, 2, border_radius=8)
			if not s.is_empty():
				# draw coin icon
				surf = get_coin_surface(s.coin)
				screen.blit(surf, (x + slot_w - surf.get_width() - 8, y + 8))
				label = render_text(big_font, format_coin_label(s.coin), (240, 220, 180))
				count_text = render_text(font, f"{s.count}/{SLOT_CAPACITY}", (200, 200, 200))
				screen.blit(label, (x + 10, y + 10))
				screen.blit(count_text, (x + 10, y + 36))
			else:
				label = render_text(font, "Empty", (140, 140, 160))
				screen.blit(label, (x + 10, y + 10))

		# draw UI area
		def draw_btn(b, disabled=False):
			bg = (80, 80, 100) if disabled else (50, 100, 160)
			pygame.draw.rect(screen, bg, b["rect"], border_radius=6)
			pygame.draw.rect(screen, (200, 200, 220), b["rect"], 2, border_radius=6)
			lbl_font = small_font or font
			lbl = render_text(lbl_font, b["label"], (200, 200, 200) if disabled else (255, 255, 255))
			# center label in button
			x = b["rect"].x + (b["rect"].width - lbl.get_width()) // 2
			y = b["rect"].y + (b["rect"].height - lbl.get_height()) // 2
			screen.blit(lbl, (x, y))

		# draw bottom UI panel
		pygame.draw.rect(screen, (20, 20, 30), (0, 520, WIDTH, HEIGHT - 520))
		# update dynamic labels for buy buttons
		slot_cost = 100 * (2 ** (unlocked_slots - INITIAL_SLOTS))
		btn_buy_slot["label"] = f"Buy Slot ({slot_cost})"
		for i, b in enumerate(btn_buy_coin):
			lvl = buy_levels[i]
			cost = coin_value(lvl)
			b["label"] = f"Buy C{lvl} ({cost})"

		# draw main buttons, with disabled state when unaffordable
		draw_btn(btn_deal)
		draw_btn(btn_buy_slot, disabled=(currency < slot_cost))
		draw_btn(btn_prestige, disabled=(currency < 1000 and unlocked_slots==INITIAL_SLOTS))
		draw_btn(btn_save)
		draw_btn(btn_load)
		draw_btn(btn_fullscreen)
		for i, b in enumerate(btn_buy_coin):
			lvl = buy_levels[i]
			cost = coin_value(lvl)
			draw_btn(b, disabled=(currency < cost or lvl > highest_purchasable))

		# HUD - stacked to avoid overlap
		hud_x = 50
		hud_y = 528
		# determine line height safely via rendering a sample glyph (works with bitmap fallback)
		sample_surf = render_text(small_font or font, "A")
		line_h = sample_surf.get_height() + 6
		hud_texts = [
			f"Currency: {currency}",
			f"Prestige Lv: {prestige_level}  Mult: x{prestige_mult:.2f}",
			f"Unlocked Slots: {unlocked_slots}",
			f"Last Gain: {last_gain}",
		]
		for i, t in enumerate(hud_texts):
			surf = render_text(small_font or font, t, (220, 220, 200))
			screen.blit(surf, (hud_x + (i // 2) * 320, hud_y + (i % 2) * line_h))

		pygame.display.flip()

		# draw dragged coin on top
		if dragging and drag_surf:
			x, y = drag_pos
			screen.blit(drag_surf, (x - drag_surf.get_width() // 2, y - drag_surf.get_height() // 2))
			pygame.display.flip()

	pygame.quit()
	sys.exit()


def save_game(path, slots, unlocked_slots, currency, prestige_level):
	try:
		data = {
			"slots": [{"coin": s.coin, "count": s.count} for s in slots],
			"unlocked_slots": unlocked_slots,
			"currency": currency,
			"prestige_level": prestige_level,
		}
		with open(path, "w") as f:
			json.dump(data, f)
		return True
	except Exception:
		return False


def load_game(path):
	try:
		if not os.path.exists(path):
			return None
		with open(path, "r") as f:
			data = json.load(f)
		return data
	except Exception:
		return None


if __name__ == "__main__":
	main()

