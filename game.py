import pygame
import traceback
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
WORKER_COST = 1000
TIME_THIEF_COST = 500
TIME_THIEF_REDUCTION = 0.25  # seconds reduced per Time Thief purchased
# minimum possible manual deal cooldown (player-controlled)
MIN_DEAL_COOLDOWN = 0.25
DEAL_WEIGHT_DECAY = 2.0  # decay factor for deal weighting: higher -> stronger bias to small coins
# UI layout limits
MAX_SLOTS_PER_ROW = 6
# game limits
MAX_SLOTS = 18


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
	"&": [0x0E,0x11,0x0E,0x1B,0x13,0x12,0x0D],
	"(": [0x02,0x04,0x08,0x08,0x08,0x04,0x02],
	")": [0x08,0x04,0x02,0x02,0x02,0x04,0x08],
	".": [0x00,0x00,0x00,0x00,0x00,0x04,0x04],
	",": [0x00,0x00,0x00,0x00,0x00,0x04,0x08],
	";": [0x00,0x18,0x18,0x00,0x00,0x04,0x08],
	"=": [0x00,0x00,0x00,0x1F,0x00,0x1F,0x00],
	}


def render_bitmap_text(text, color=(255, 255, 255), scale=2, spacing=1):
	text = text.upper()
	rows = 7
	char_w = 5
	# sanitize params to avoid invalid Surface sizes (zero/negative)
	scale = int(scale) if isinstance(scale, (int, float)) else 2
	spacing = int(spacing) if isinstance(spacing, (int, float)) else 1
	if scale < 1:
		scale = 1
	if spacing < 0:
		spacing = 0
	# empty text -> return a tiny transparent surface
	if not text:
		height = max(1, rows * scale)
		return pygame.Surface((1, height), pygame.SRCALPHA)
	width = sum((char_w * scale) + spacing for _ in text) - spacing
	height = max(1, rows * scale)
	# clamp width to at least 1 to avoid pygame.error: Invalid resolution for Surface
	if width < 1:
		width = 1
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
	# Process combines by promoting groups from slots into new coins (distributed across slots).
	gained = 0
	# Repeat until no promotions occur (to allow cascading across slots)
	promoted_any = True
	while promoted_any:
		promoted_any = False
		for s in slots:
			if s.is_empty():
				continue
			if s.count >= SLOT_CAPACITY:
				promos = s.count // SLOT_CAPACITY
				s.count = s.count % SLOT_CAPACITY
				# create `promos` coins of level s.coin+1
				for _ in range(promos):
					target_level = s.coin + 1
					placed = add_coin_to_slots(slots, target_level)
					# if unable to place (no free slot), place the promoted coin into this slot
					if not placed:
						# overwrite this slot with the promoted coin
						s.coin = target_level
						s.count = 1
						gained += coin_value(target_level)
						promoted_any = True
					else:
						gained += coin_value(target_level)
						promoted_any = True
				# if this slot emptied, mark empty
				if s.count == 0:
					s.coin = 0
	gained = int(gained * prestige_mult)
	currency += gained
	return currency, gained


def weighted_random_coin(*args, **kwargs):
	"""Compatibility wrapper:
	- New usage: weighted_random_coin(slots, cap=...)
	- Old usage: weighted_random_coin(max_level=...)
	"""
	# detect old-style call
	max_level = kwargs.get('max_level', None)
	cap = kwargs.get('cap', None)
	slots = None
	if args:
		first = args[0]
		if isinstance(first, list):
			slots = first
		elif isinstance(first, int):
			max_level = first

	if slots is None:
		# fallback to original fixed-weight behavior when called with max_level
		if max_level is None:
			max_level = 5
		base_weights = [50, 30, 12, 6, 2]
		weights = base_weights[:max_level]
		return random.choices(range(1, len(weights) + 1), weights=weights, k=1)[0]

	# New behavior: include baseline low levels (C1-C3) plus any levels present in slots,
	# but ensure C1-C3 together have ~95% probability while higher levels share ~5%.
	# Also respect placement availability (same-level slot with room or any empty slot).
	present = {s.coin for s in slots if s.coin}
	# baseline low levels (respect cap)
	base_max = 3
	if cap is not None:
		base_max = min(base_max, cap)
	base_levels = set(range(1, base_max + 1))
	candidate_levels = sorted(present | base_levels)

	def _can_place(level):
		for s in slots:
			if s.coin == level and s.count < SLOT_CAPACITY:
				return True
		for s in slots:
			if s.is_empty():
				return True
		return False

	# filter to only placeable levels
	levels = [l for l in candidate_levels if _can_place(l)]
	# if no placeable levels remain, try to find any placeable up to cap
	if not levels:
		max_try = cap if cap is not None else max(5, max(present) if present else 3)
		found = None
		for l in range(1, max_try + 1):
			if _can_place(l):
				found = l
				break
		if found is None:
			return 1
		levels = [found]

	# Partition low (<=3) and high (>3)
	low_levels = [l for l in levels if l <= 3]
	high_levels = [l for l in levels if l > 3]

	# Desired mass percents
	LOW_MASS = 95.0
	HIGH_MASS = max(0.0, 100.0 - LOW_MASS)

	weights = []
	if low_levels:
		low_share = LOW_MASS / len(low_levels)
	else:
		low_share = 0.0

	if high_levels:
		min_high = min(high_levels)
		raw = [DEAL_WEIGHT_DECAY ** (-(l - min_high)) for l in high_levels]
		sum_raw = sum(raw)
		scaled = [(r / sum_raw) * HIGH_MASS for r in raw]
		high_map = dict(zip(high_levels, scaled))
	else:
		high_map = {}

	for l in levels:
		if l in low_levels:
			weights.append(low_share)
		else:
			weights.append(high_map.get(l, 0.0))

	return random.choices(levels, weights=weights, k=1)[0]


def compute_spawn_probabilities(slots, cap=None):
	"""Return a dict level->percent for spawn probabilities given current slots.
	Mirrors the selection logic used by weighted_random_coin for the slots case.
	"""
	present = {s.coin for s in slots if s.coin}
	base_max = 3
	if cap is not None:
		base_max = min(base_max, cap)
	base_levels = set(range(1, base_max + 1))
	candidate_levels = sorted(present | base_levels)

	def _can_place(level):
		for s in slots:
			if s.coin == level and s.count < SLOT_CAPACITY:
				return True
		for s in slots:
			if s.is_empty():
				return True
		return False

	levels = [l for l in candidate_levels if _can_place(l)]
	if not levels:
		max_try = cap if cap is not None else max(5, max(present) if present else 3)
		for l in range(1, max_try + 1):
			if _can_place(l):
				levels = [l]
				break
		if not levels:
			return {1: 100.0}

	low_levels = [l for l in levels if l <= 3]
	high_levels = [l for l in levels if l > 3]

	LOW_MASS = 95.0
	HIGH_MASS = max(0.0, 100.0 - LOW_MASS)

	weights = []
	if low_levels:
		low_share = LOW_MASS / len(low_levels)
	else:
		low_share = 0.0

	if high_levels:
		min_high = min(high_levels)
		raw = [DEAL_WEIGHT_DECAY ** (-(l - min_high)) for l in high_levels]
		sum_raw = sum(raw)
		scaled = [(r / sum_raw) * HIGH_MASS for r in raw]
		high_map = dict(zip(high_levels, scaled))
	else:
		high_map = {}

	for l in levels:
		if l in low_levels:
			weights.append(low_share)
		else:
			weights.append(high_map.get(l, 0.0))

	total = sum(weights)
	if total <= 0:
		return {1: 100.0}
	probs = {l: (w / total) * 100.0 for l, w in zip(levels, weights)}
	return probs


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

	# additional font sizes used elsewhere
	try:
		small_font = _pygame_font.SysFont(None, 14) if HAVE_PYGAME_FONT else None
		big_font = _pygame_font.SysFont(None, 28) if HAVE_PYGAME_FONT else None
	except Exception:
		small_font = None
		big_font = None

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

	# wrapped text renderer: returns a surface constrained to max_width with word wrapping
	def render_text_wrapped(f, text, color, max_width, line_spacing=6):
		words = str(text).split(' ')
		lines = []
		cur = ''
		for w in words:
			if cur:
				test = cur + ' ' + w
			else:
				test = w
			# measure width
			surf_test = render_text(f, test, color)
			if surf_test.get_width() <= max_width:
				cur = test
			else:
				if cur:
					lines.append(cur)
				cur = w
		if cur:
			lines.append(cur)
		# render each line and blit onto a combined surface
		line_surfs = [render_text(f, l, color) for l in lines]
		total_h = sum(s.get_height() for s in line_surfs) + max(0, (len(line_surfs) - 1) * line_spacing)
		out = pygame.Surface((max_width, max(1, total_h)), pygame.SRCALPHA)
		y = 0
		for s in line_surfs:
			out.blit(s, (0, y))
			y += s.get_height() + line_spacing
		return out
	# UI buttons
	btn_deal = make_button((50, 600, 160, 40), "Deal Coins")
	btn_buy_slot = make_button((230, 600, 160, 40), "Buy Slot")
	btn_prestige = make_button((410, 600, 160, 40), "Prestige")
	btn_save = make_button((50, 650, 120, 34), "Save")
	btn_load = make_button((190, 650, 120, 34), "Load")
	btn_fullscreen = make_button((350, 650, 140, 34), "Fullscreen")
	# single Buy menu button (opens small popup with options)
	# buy menu positioned with equal spacing from other buttons
	btn_buy_menu = make_button((560, 600, 140, 40), "Buy Coins")
	# shift UI buttons left slightly to make room for the market chart
	btn_deal = make_button((20, 600, 160, 40), "Deal Coins")
	# Upgrades menu (replaces direct Buy Slot button)
	btn_upgrades = make_button((200, 600, 160, 40), "Upgrades")
	btn_prestige = make_button((380, 600, 160, 40), "Prestige")
	btn_save = make_button((20, 650, 120, 34), "Save")
	btn_load = make_button((160, 650, 120, 34), "Load")
	btn_fullscreen = make_button((320, 650, 140, 34), "Fullscreen")
	btn_help = make_button((480, 650, 120, 34), "Help")
	# place worker toggle in a third row (compact) to avoid overlapping chart
	btn_worker_toggle = make_button((20, 694, 140, 24), "Worker:Off")
	buy_popup = None  # {'rect':Rect, 'options':[{'rect':Rect,'level':int,'cost':int}]}
	upgrades_popup = None
	prestige_popup = None
	help_popup = None

	# game state
	slots = [Slot() for _ in range(INITIAL_SLOTS)]
	unlocked_slots = INITIAL_SLOTS
	currency = 2500
	prestige_mult = 1.0
	prestige_level = 0
	# Worker upgrade state
	worker_owned = False
	worker_enabled = False
	worker_last_deal_time = pygame.time.get_ticks() / 1000.0

	# Time Thief upgrade state (reduces cooldowns)
	time_thief_count = 0

	# dragging state
	dragging = False
	drag_level = None
	drag_surf = None
	drag_src = None
	drag_pos = (0, 0)

	is_fullscreen = False
	# sell popup when shift+clicking a slot
	sell_popup = None  # {'level': int, 'rect': Rect, 'sell1':Rect,'sell5':Rect,'sell_all':Rect}

	# market price history for chart: level -> list of recent displayed prices
	price_history = {}
	price_history_max = 80

	# recent sales history used for pricing: level -> deque of last ~1000 sale prices
	from collections import deque, defaultdict
	market_sales_history = defaultdict(lambda: deque(maxlen=1000))
	# parallel timestamps for recent sales to compute volume-driven effects
	market_sales_timestamps = defaultdict(lambda: deque(maxlen=1000))
	# how strongly player sales affect market history (higher -> bigger immediate impact)
	SELL_IMPACT_MULTIPLIER = 5

	# computed current prices (updated on actions)
	current_prices = {}

	# price update throttle (seconds) - update every 1s per request
	price_update_interval = 1.0
	last_price_update = 0.0
	# deal cooldown (base seconds)
	deal_cooldown = 5.0
	def effective_deal_cooldown():
		return max(MIN_DEAL_COOLDOWN, deal_cooldown - time_thief_count * TIME_THIEF_REDUCTION)

	def max_time_thief_count():
		# compute how many Time Thiefs can be purchased before reaching MIN_DEAL_COOLDOWN
		maxc = int((deal_cooldown - MIN_DEAL_COOLDOWN) / TIME_THIEF_REDUCTION)
		return max(0, maxc)
	last_deal_time = -9999.0

	def update_market_prices():
		# compute prices from recent sales history and recent sale volume
		max_samples = 100
		# shorten lookback so prices recover faster after a sell
		lookback_secs = 30.0
		# include levels from recent sales so chart updates even after the player no longer holds that coin
		now_ts = pygame.time.get_ticks() / 1000.0
		levels_set = set()
		for s in slots:
			if s.coin:
				levels_set.add(s.coin)
		# include any levels with recent sales history
		for k in market_sales_history.keys():
			if k:
				levels_set.add(k)
		# always include lowest few levels for display
		for i in range(1, 4):
			levels_set.add(i)
		levels = sorted(levels_set)
		for lvl in levels:
			price_hist = list(market_sales_history.get(lvl, []))
			ts_hist = list(market_sales_timestamps.get(lvl, []))
			# prefer only fairly recent sales for base price to allow faster recovery
			recent_window = lookback_secs * 2.0
			recent_samples = [p for p, t in zip(price_hist, ts_hist) if now_ts - t <= recent_window]
			if recent_samples:
				base_price = int(sum(recent_samples[-max_samples:]) / len(recent_samples[-max_samples:]))
			elif price_hist:
				# if there are historical sales but none recent, blend older average with base coin value
				older = price_hist[-max_samples:]
				older_avg = int(sum(older) / len(older))
				base_price = int(0.4 * older_avg + 0.6 * coin_value(lvl))
			else:
				base_price = coin_value(lvl)
			# compute recent sale volume in lookback window
			recent_sales_count = 0
			for t in reversed(ts_hist):
				if now_ts - t <= lookback_secs:
					recent_sales_count += 1
				else:
					break
			# demand factor decreases as recent sales increase
			demand = max(0.3, 1.2 - (recent_sales_count / (10.0 + lvl)))
			# small noise
			noise = random.uniform(-0.02, 0.02)
			price = int(base_price * demand * (1.0 + noise))
			current_prices[lvl] = max(1, price)
			# append to small chart history so chart reflects price movements
			if lvl not in price_history:
				price_history[lvl] = []
			price_history[lvl].append(current_prices[lvl])
			if len(price_history[lvl]) > price_history_max:
				price_history[lvl].pop(0)

	# misc UI/game flags
	no_moves = False
	highest_purchasable = 3

	def slot_rect(index):
		slot_w = 140
		slot_h = 140
		margin = 20
		# horizontal padding from screen edges
		left_pad = 50
		right_pad = 50
		available_width = WIDTH - left_pad - right_pad
		# compute maximum columns that fit given slot width+margin
		max_cols = max(1, int((available_width + margin) // (slot_w + margin)))
		# cap columns to a sensible maximum so rows wrap earlier on wide screens
		max_cols = min(max_cols, MAX_SLOTS_PER_ROW)
		# number of columns we'll use (don't exceed unlocked_slots)
		cols = min(max_cols, max(1, unlocked_slots))
		# ensure the computed cols actually fits in the available width
		while cols > 1 and (cols * slot_w + (cols - 1) * margin) > available_width:
			cols -= 1
		# which row and column this index is in
		row = index // cols
		col = index % cols
		# compute how many items are in this row (last row may be shorter)
		items_in_row = cols
		# if this is the last row, it might have fewer items
		total_rows = (unlocked_slots + cols - 1) // cols
		if row == total_rows - 1:
			# items remaining
			items_in_row = max(1, unlocked_slots - row * cols)
		# center the row horizontally
		row_width = items_in_row * slot_w + max(0, items_in_row - 1) * margin
		x_start = left_pad + (available_width - row_width) // 2
		x = x_start + col * (slot_w + margin)
		y = 50 + row * (slot_h + margin)
		return pygame.Rect(x, y, slot_w, slot_h)

	# helpers to detect if a coin of `level` can be placed (without mutating state)
	def can_place_level(level):
		for s in slots:
			if s.coin == level and s.count < SLOT_CAPACITY:
				return True
		for s in slots:
			if s.is_empty():
				return True
		return False

	def any_place_up_to(max_level):
		for lvl in range(1, max_level + 1):
			if can_place_level(lvl):
				return True
		return False

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

		# allow dealing to spawn coins up to one level above current_max (no hard cap)
		max_deal_level = max(3, current_max + 1, unlocked_slots)

		# detect no-move (can't place any reasonable coin and can't afford a slot)
		# make slots more expensive (higher base)
		slot_cost = 200 * (2 ** (unlocked_slots - INITIAL_SLOTS))
		has_place = any_place_up_to(max_deal_level)
		no_moves = (not has_place) and (currency < slot_cost)

		# compute supply per level (for UI counts only)
		supply = {}
		max_display_level = max(3, current_max)
		for lvl in range(1, max_display_level + 1):
			supply[lvl] = sum(s.count for s in slots if s.coin == lvl)
		# periodic backup update if there are no recorded market prices yet
		now = pygame.time.get_ticks() / 1000.0
		if not current_prices:
			update_market_prices()
		# periodic market price recalculation (every interval)
		if now - last_price_update >= price_update_interval:
			update_market_prices()
			last_price_update = now

		# sell popup state is managed via `sell_popup`; cleared by clicks elsewhere

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.MOUSEWHEEL:
				# scroll help popup content when wheel used over the popup
				if help_popup and isinstance(help_popup, dict):
					mx, my = pygame.mouse.get_pos()
					if help_popup["rect"].collidepoint((mx, my)):
						delta = -event.y * 24
						help_popup["scroll"] = max(0, help_popup.get("scroll", 0) + delta)
						continue
				# otherwise fall through
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
				# legacy wheel events: 4 = up, 5 = down
				mx, my = event.pos
				if help_popup and isinstance(help_popup, dict) and help_popup["rect"].collidepoint((mx, my)):
					delta = -24 if event.button == 4 else 24
					help_popup["scroll"] = max(0, help_popup.get("scroll", 0) + delta)
					continue
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				mx, my = event.pos
				# close sell popup when clicking anywhere outside of it
				if sell_popup and not sell_popup["rect"].collidepoint((mx, my)):
					sell_popup = None
				# if no moves, present modal actions first
				if no_moves:
					# modal button positions (centered)
					modal_w, modal_h = 520, 160
					mx0 = (WIDTH - modal_w) // 2
					my0 = (HEIGHT - modal_h) // 2
					buy_rect = pygame.Rect(mx0 + 20, my0 + 80, 140, 48)
					sell_rect = pygame.Rect(mx0 + 190, my0 + 80, 140, 48)
					restart_rect = pygame.Rect(mx0 + 360, my0 + 80, 140, 48)
					if buy_rect.collidepoint((mx, my)):
						# attempt buy slot
						if currency >= slot_cost and unlocked_slots < MAX_SLOTS:
							currency -= slot_cost
							slots.append(Slot())
							unlocked_slots += 1
						continue
					elif sell_rect.collidepoint((mx, my)):
						# sell one coin from the highest-level non-empty slot
						best = None
						for i, s in enumerate(slots):
							if not s.is_empty() and s.count > 0:
								if best is None or s.coin > slots[best].coin:
									best = i
						if best is not None:
							lvl = slots[best].coin
							slots[best].count -= 1
							if slots[best].count == 0:
								slots[best].coin = 0
							currency += coin_value(lvl) // 2
						continue
					elif restart_rect.collidepoint((mx, my)):
						# restart current run (preserve prestige)
						slots = [Slot() for _ in range(INITIAL_SLOTS)]
						unlocked_slots = INITIAL_SLOTS
						currency = 0
						last_gain = 0
						continue
				# otherwise normal click handling follows
				# handle help popup first (blocks other UI) with defensive checks
				if help_popup is not None:
					try:
						rrect = help_popup.get("rect") if isinstance(help_popup, dict) else None
						crect = help_popup.get("close") if isinstance(help_popup, dict) else None
						if rrect and rrect.collidepoint((mx, my)):
							# if clicked the close button, close; otherwise keep open
							if crect and crect.collidepoint((mx, my)):
								help_popup = None
							# keep open when clicking inside body
						else:
							# clicked outside popup -> close
							help_popup = None
						continue
					except Exception:
						print("Error handling help popup click:")
						traceback.print_exc()
						help_popup = None
						continue
				# handle prestige confirmation popup next (blocks other UI)
				if prestige_popup:
					if prestige_popup["rect"].collidepoint((mx, my)):
						# Yes/No buttons
						if prestige_popup["yes"].collidepoint((mx, my)):
							# perform prestige
							if unlocked_slots > INITIAL_SLOTS or currency >= 1000:
								prestige_level += 1
								prestige_mult = 1.0 + prestige_level * 0.1
								currency = 0
								slots = [Slot() for _ in range(INITIAL_SLOTS)]
								unlocked_slots = INITIAL_SLOTS
								last_gain = 0
							# close popup after choice
							prestige_popup = None
						elif prestige_popup["no"].collidepoint((mx, my)):
							prestige_popup = None
					else:
						# clicked outside popup -> close
						prestige_popup = None
					continue
				# check for slot click to start dragging (priority)
				clicked_slot = None
				for i in range(len(slots)):
					rect = slot_rect(i)
					if rect.collidepoint((mx, my)) and i < unlocked_slots and not slots[i].is_empty():
						clicked_slot = i
						break
				# Shift+click opens sell popup for that slot
				mods = pygame.key.get_mods()
				if clicked_slot is not None and not dragging:
					if mods & pygame.KMOD_SHIFT:
						lvl = slots[clicked_slot].coin
						# popup near slot (larger so value text and buttons don't overlap)
						rect = slot_rect(clicked_slot)
						pw, ph = 300, 64
						px = rect.x + (rect.width - pw) // 2
						py = rect.y + rect.height + 8
						r = pygame.Rect(px, py, pw, ph)
						r1 = pygame.Rect(px + 12, py + 30, 56, 26)
						r5 = pygame.Rect(px + 84, py + 30, 56, 26)
						rall = pygame.Rect(px + 156, py + 30, 132, 26)
						sell_popup = {"level": lvl, "slot": clicked_slot, "rect": r, "sell1": r1, "sell5": r5, "sell_all": rall}
						continue
					# otherwise pick up one coin from the slot for dragging
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
				if btn_deal["rect"].collidepoint((mx, my)) and not worker_enabled:
					now_click = pygame.time.get_ticks() / 1000.0
					# use effective cooldown (reduced by Time Thief purchases)
					eff_cd = effective_deal_cooldown()
					if now_click - last_deal_time >= eff_cd:
						# deal one coin per unlocked slot
						for _ in range(unlocked_slots):
							# spawn up to max_deal_level (respect cap)
							lvl = weighted_random_coin(slots, cap=min(max_deal_level, unlocked_slots + 2))
							add_coin_to_slots(slots, lvl)
						# process combines but do NOT grant currency for deal-triggered combines
						_ , _ = process_combines(slots, currency, prestige_mult)
						last_gain = 0
						last_deal_time = now_click
					else:
						# still cooling down; ignore click
						pass
				elif worker_owned and btn_worker_toggle["rect"].collidepoint((mx, my)):
					worker_enabled = not worker_enabled
					if worker_enabled:
						worker_last_deal_time = pygame.time.get_ticks() / 1000.0
					continue
				elif btn_upgrades["rect"].collidepoint((mx, my)):
					# open upgrades popup (contains Buy Slot and future upgrades)
					if upgrades_popup:
						upgrades_popup = None
					else:
						pw = 340
						# define upgrade actions in an array so we can size the popup dynamically
						actions = [
							{"action": "buy_slot", "cost": slot_cost},
							{"action": "buy_worker", "cost": WORKER_COST},
							{"action": "buy_time_thief", "cost": TIME_THIEF_COST},
							{"action": "noop", "cost": 0},
						]
						per_step = 32
						top_pad = 8
						bot_pad = 8
						ph = top_pad + len(actions) * per_step + bot_pad
						px = btn_upgrades["rect"].x
						py = btn_upgrades["rect"].y - ph - 6
						opts = []
						for i, a in enumerate(actions):
							x = px + 8
							y = py + top_pad + i * per_step
							rect = pygame.Rect(x, y, pw - 16, 28)
							opts.append({"rect": rect, "action": a["action"], "cost": a["cost"]})
						upgrades_popup = {"rect": pygame.Rect(px, py, pw, ph), "options": opts}
				elif btn_fullscreen["rect"].collidepoint((mx, my)):
					# toggle fullscreen
					is_fullscreen = not is_fullscreen
					if is_fullscreen:
						screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
					else:
						screen = pygame.display.set_mode((WIDTH, HEIGHT))
				elif btn_prestige["rect"].collidepoint((mx, my)):
					# open a confirmation modal instead of immediate prestige
					if unlocked_slots > INITIAL_SLOTS or currency >= 1000:
						pw, ph = 520, 160
						mx0 = (WIDTH - pw) // 2
						my0 = (HEIGHT - ph) // 2
						yes_rect = pygame.Rect(mx0 + 60, my0 + 100, 160, 40)
						no_rect = pygame.Rect(mx0 + 300, my0 + 100, 160, 40)
						prestige_popup = {"rect": pygame.Rect(mx0, my0, pw, ph), "yes": yes_rect, "no": no_rect}
				elif btn_help["rect"].collidepoint((mx, my)):
					# toggle help modal
					if help_popup:
						help_popup = None
					else:
						pw, ph = 640, 360
						mx0 = (WIDTH - pw) // 2
						my0 = (HEIGHT - ph) // 2
						close_rect = pygame.Rect(mx0 + pw - 120, my0 + ph - 52, 100, 40)
						help_popup = {"rect": pygame.Rect(mx0, my0, pw, ph), "close": close_rect, "scroll": 0}
				# Save/load handlers (separate from prestige)
				elif btn_save["rect"].collidepoint((mx, my)):
					save_path = os.path.join(os.path.dirname(__file__), "save.json")
					saved = save_game(save_path, slots, unlocked_slots, currency, prestige_level, worker_owned, worker_enabled, time_thief_count)
					# no blocking UI; last_gain used to show feedback
					last_gain = 0 if saved else -1
				elif btn_load["rect"].collidepoint((mx, my)):
					save_path = os.path.join(os.path.dirname(__file__), "save.json")
					data = load_game(save_path)
					if data:
						# clamp loaded unlocked_slots to MAX_SLOTS
						loaded_slots = int(data.get("unlocked_slots", INITIAL_SLOTS))
						loaded_slots = max(INITIAL_SLOTS, min(MAX_SLOTS, loaded_slots))
						slots = [Slot() for _ in range(loaded_slots)]
						for i, sdata in enumerate(data.get("slots", [])):
							if i < len(slots):
								slots[i].coin = sdata.get("coin", 0)
								slots[i].count = sdata.get("count", 0)
						unlocked_slots = loaded_slots
						currency = data.get("currency", 0)
						prestige_level = data.get("prestige_level", 0)
						prestige_mult = 1.0 + prestige_level * 0.1
						# restore worker state if present
						worker_owned = data.get("worker_owned", False)
						worker_enabled = data.get("worker_enabled", False)
						# restore Time Thief purchases if present
						time_thief_count = data.get("time_thief_count", 0)
				# Buy coin menu handling and sell-popup handling
				else:
					# Buy menu toggle
					if btn_buy_menu["rect"].collidepoint((mx, my)):
						if buy_popup:
							buy_popup = None
						else:
							# create popup with current buy_levels
							pw, ph = 240, 120
							px = btn_buy_menu["rect"].x
							py = btn_buy_menu["rect"].y - ph - 6
							opts = []
							for i, lvl in enumerate(buy_levels):
								x = px + 8
								y = py + 8 + i * 36
								rect = pygame.Rect(x, y, pw - 16, 28)
								opts.append({"rect": rect, "level": lvl, "cost": coin_value(lvl)})
							buy_popup = {"rect": pygame.Rect(px, py, pw, ph), "options": opts}
						continue
					# handle buy popup clicks: keep it open after purchases; only close when clicking outside the popup
					if buy_popup:
						# if click was inside the popup rect, handle option clicks but do not close
						if buy_popup["rect"].collidepoint((mx, my)):
							for opt in buy_popup["options"]:
								if opt["rect"].collidepoint((mx, my)):
									lvl = opt["level"]
									cost = opt["cost"]
									if currency >= cost and lvl <= highest_purchasable:
										currency -= cost
										add_coin_to_slots(slots, lvl)
										currency, last_gain = process_combines(slots, currency, prestige_mult)
										update_market_prices()
						# if click was outside the popup, close it
						else:
							buy_popup = None
					# handle upgrades popup clicks: keep it open until clicking outside
					if upgrades_popup:
						# if click inside popup, process the clicked option but do not close the popup
						if upgrades_popup["rect"].collidepoint((mx, my)):
							for opt in upgrades_popup["options"]:
								if opt["rect"].collidepoint((mx, my)):
									action = opt.get("action")
									if action == "buy_slot":
										cost = opt.get("cost", 0)
										if currency >= cost and unlocked_slots < MAX_SLOTS:
											currency -= cost
											slots.append(Slot())
											unlocked_slots += 1
											update_market_prices()
									elif action == "buy_worker":
										cost = opt.get("cost", 0)
										if currency >= cost and not worker_owned:
											currency -= cost
											worker_owned = True
											# enable worker immediately for convenience
											worker_enabled = True
											worker_last_deal_time = pygame.time.get_ticks() / 1000.0
									elif action == "buy_time_thief":
										cost = opt.get("cost", 0)
										if currency >= cost and time_thief_count < max_time_thief_count():
											currency -= cost
											time_thief_count += 1
									else:
										pass
									break
						# if click was outside the popup, close it
						else:
							upgrades_popup = None
					# handle sell popup clicks if present
					if sell_popup:
						lvl = sell_popup["level"]
						# sell 1
						if sell_popup["sell1"].collidepoint((mx, my)):
							price = current_prices.get(lvl, coin_value(lvl))
							sold = 0
							slot_idx = sell_popup.get("slot")
							if slot_idx is not None and slot_idx < len(slots):
								s = slots[slot_idx]
								if s.coin == lvl and s.count > 0:
									s.count -= 1
									if s.count == 0:
										s.coin = 0
									currency += price
									# record sale with amplified impact
									for _ in range(SELL_IMPACT_MULTIPLIER):
										market_sales_history[lvl].append(price)
									_market_now = pygame.time.get_ticks() / 1000.0
									for _ in range(SELL_IMPACT_MULTIPLIER):
										market_sales_timestamps[lvl].append(_market_now)
									sold = 1
								else:
									sold = 0
							else:
								sold = 0
							if sold:
								update_market_prices()
							# keep popup open only if the original slot still has coins of this level
							if not (slot_idx is not None and slot_idx < len(slots) and slots[slot_idx].coin == lvl and slots[slot_idx].count > 0):
								sell_popup = None
						# sell 5
						elif sell_popup["sell5"].collidepoint((mx, my)):
							price = current_prices.get(lvl, coin_value(lvl))
							sold = 0
							slot_idx = sell_popup.get("slot")
							if slot_idx is not None and slot_idx < len(slots):
								s = slots[slot_idx]
								while s.coin == lvl and s.count > 0 and sold < 5:
									s.count -= 1
									currency += price
									# append amplified entries for this sale
									for _ in range(SELL_IMPACT_MULTIPLIER):
										market_sales_history[lvl].append(price)
									_market_now = pygame.time.get_ticks() / 1000.0
									for _ in range(SELL_IMPACT_MULTIPLIER):
										market_sales_timestamps[lvl].append(_market_now)
									sold += 1
								if s.count == 0:
									s.coin = 0
							else:
								sold = 0
							if sold:
								update_market_prices()
							# keep popup open only if original slot still has coins
							if not (slot_idx is not None and slot_idx < len(slots) and slots[slot_idx].coin == lvl and slots[slot_idx].count > 0):
								sell_popup = None
						# sell all (target the selected slot only)
						elif sell_popup["sell_all"].collidepoint((mx, my)):
							price = current_prices.get(lvl, coin_value(lvl))
							total_sold = 0
							slot_idx = sell_popup.get("slot")
							if slot_idx is not None and slot_idx < len(slots):
								s = slots[slot_idx]
								if s.coin == lvl and s.count > 0:
									n = s.count
									currency += price * n
									# append amplified entries per coin sold
									for _ in range(n):
										for _ in range(SELL_IMPACT_MULTIPLIER):
											market_sales_history[lvl].append(price)
										_market_now = pygame.time.get_ticks() / 1000.0
										for _ in range(SELL_IMPACT_MULTIPLIER):
											market_sales_timestamps[lvl].append(_market_now)
									total_sold += n
									s.count = 0
									s.coin = 0
							if total_sold:
								update_market_prices()
							sell_popup = None
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


		# worker auto-deal: executes the same spawn/combine logic as the Deal button
		now_worker = pygame.time.get_ticks() / 1000.0
		if worker_owned and worker_enabled:
			# worker uses the effective cooldown (Time Thief reduces both manual and worker speeds)
			worker_interval = effective_deal_cooldown() * 2.0
			if now_worker - worker_last_deal_time >= worker_interval:
				for _ in range(unlocked_slots):
						lvl = weighted_random_coin(slots, cap=min(max_deal_level, unlocked_slots + 2))
						add_coin_to_slots(slots, lvl)
						# worker deals should not directly award currency either
						_ , _ = process_combines(slots, currency, prestige_mult)
						last_gain = 0
				worker_last_deal_time = now_worker
				update_market_prices()

		screen.fill((30, 30, 40))

		# draw slots (use slot_rect so layout/wrapping is consistent)
		for i, s in enumerate(slots):
			rect = slot_rect(i)
			color = (70, 70, 90) if i < unlocked_slots else (40, 40, 50)
			pygame.draw.rect(screen, color, rect, border_radius=8)
			pygame.draw.rect(screen, (120, 120, 140), rect, 2, border_radius=8)
			if not s.is_empty():
				# draw coin icon
				surf = get_coin_surface(s.coin)
				screen.blit(surf, (rect.x + rect.width - surf.get_width() - 8, rect.y + 8))
				label = render_text(big_font, format_coin_label(s.coin), (240, 220, 180))
				count_text = render_text(font, f"{s.count}/{SLOT_CAPACITY}", (200, 200, 200))
				screen.blit(label, (rect.x + 10, rect.y + 10))
				screen.blit(count_text, (rect.x + 10, rect.y + 36))
			else:
				label = render_text(font, "Empty", (140, 140, 160))
				screen.blit(label, (rect.x + 10, rect.y + 10))

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
		# update dynamic labels for buy slot
		slot_cost = 200 * (2 ** (unlocked_slots - INITIAL_SLOTS))
		# if upgrades popup open, refresh displayed costs
		if upgrades_popup:
			for opt in upgrades_popup["options"]:
				if opt.get("action") == "buy_slot":
					opt["cost"] = slot_cost
		# prepare buy popup options if open
		if buy_popup:
			for opt in buy_popup["options"]:
				lvl = opt["level"]
				opt["cost"] = coin_value(lvl)

		# draw small market chart at bottom-right inside the UI panel (draw first so UI overlays it)
		chart_w = 480
		chart_h = 160
		chart_x = WIDTH - chart_w - 20
		chart_y = 540
		pygame.draw.rect(screen, (18, 18, 24), (chart_x, chart_y, chart_w, chart_h))
		pygame.draw.rect(screen, (90,90,100), (chart_x, chart_y, chart_w, chart_h), 1)
		# gather levels to plot (up to 6)
		plot_levels = sorted(price_history.keys())[-6:]
		colors = [(220,180,60),(180,220,100),(160,160,240),(240,160,200),(200,200,200),(180,140,220)]
		if plot_levels:
			# find max price in history window
			mxp = max(max(price_history[l]) if price_history[l] else 1 for l in plot_levels)
			for i, lvl in enumerate(plot_levels):
				hist = price_history.get(lvl, [])
				if not hist:
					continue
				col = colors[i % len(colors)]
				n = len(hist)
				for j in range(1, n):
					x1 = chart_x + int((j-1)/price_history_max * chart_w)
					x2 = chart_x + int(j/price_history_max * chart_w)
					y1 = chart_y + chart_h - int((hist[j-1]/mxp) * (chart_h-8)) - 4
					y2 = chart_y + chart_h - int((hist[j]/mxp) * (chart_h-8)) - 4
					pygame.draw.line(screen, col, (x1,y1), (x2,y2), 2)
				# label
				lbl = render_text(small_font or font, f"C{lvl}", col)
				screen.blit(lbl, (chart_x + chart_w - 40, chart_y + 4 + i*14))

		# draw main buttons, with disabled state when unaffordable (after chart so buttons are visible)
		# draw Deal button; if cooling down show countdown as the label
		now_draw = pygame.time.get_ticks() / 1000.0
		# manual remaining (use effective cooldown)
		eff_cd = effective_deal_cooldown()
		remaining_manual = max(0.0, eff_cd - (now_draw - last_deal_time))
		# if worker is enabled, show worker countdown (worker uses double the manual cooldown)
		if worker_enabled:
			worker_interval = eff_cd * 2.0
			remaining_worker = max(0.0, worker_interval - (now_draw - worker_last_deal_time))
			orig_label = btn_deal["label"]
			btn_deal["label"] = f"{remaining_worker:.1f}s"
			draw_btn(btn_deal, disabled=True)
			btn_deal["label"] = orig_label
		else:
			deal_disabled = remaining_manual > 0.0
			if remaining_manual > 0.0:
				orig_label = btn_deal["label"]
				btn_deal["label"] = f"{remaining_manual:.1f}s"
				draw_btn(btn_deal, disabled=False)
				btn_deal["label"] = orig_label
			else:
				draw_btn(btn_deal, disabled=deal_disabled)
				# ready indicator: green border around the button when manual deal is available
				if not deal_disabled:
					pygame.draw.rect(screen, (60,200,80), btn_deal["rect"], 3, border_radius=6)
		draw_btn(btn_upgrades, disabled=(currency < slot_cost))
		draw_btn(btn_prestige, disabled=(currency < 1000 and unlocked_slots==INITIAL_SLOTS))
		draw_btn(btn_save)
		draw_btn(btn_load)
		draw_btn(btn_fullscreen)
		draw_btn(btn_help)
		draw_btn(btn_buy_menu)
		# draw worker toggle when purchased
		if worker_owned:
			btn_worker_toggle["label"] = "Worker:On" if worker_enabled else "Worker:Off"
			draw_btn(btn_worker_toggle)



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

		# show indicator if low-level coins (1-3) cannot be placed anywhere
		can_place_low = any(can_place_level(l) for l in range(1, 4))
		warn_h = 0
		if not can_place_low:
			warn = "Low-level deals blocked — sell coins or buy slots to allow them."
			ws = render_text_wrapped(small_font or font, warn, (240,140,40), 420)
			warn_h = ws.get_height()
			screen.blit(ws, (hud_x, hud_y + 2 * line_h + 6))

		# (tooltip moved to Help menu)

		# if no moves available, draw modal offering Buy Slot / Sell Coin / Restart
		if no_moves:
			modal_w, modal_h = 520, 160
			mx0 = (WIDTH - modal_w) // 2
			my0 = (HEIGHT - modal_h) // 2
			# dim background
			over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
			over.fill((0, 0, 0, 160))
			screen.blit(over, (0, 0))
			# modal box
			pygame.draw.rect(screen, (40, 40, 50), (mx0, my0, modal_w, modal_h), border_radius=8)
			pygame.draw.rect(screen, (200, 200, 220), (mx0, my0, modal_w, modal_h), 2, border_radius=8)
			msg = render_text(big_font or font, "No available moves", (230, 220, 200))
			screen.blit(msg, (mx0 + 20, my0 + 20))
			text = "Buy a slot, sell a coin, or restart to continue."
			sub = render_text_wrapped(small_font or font, text, (200, 200, 200), modal_w - 40)
			screen.blit(sub, (mx0 + 20, my0 + 56))
			# buttons
			buy_rect = pygame.Rect(mx0 + 20, my0 + 80, 140, 48)
			sell_rect = pygame.Rect(mx0 + 190, my0 + 80, 140, 48)
			restart_rect = pygame.Rect(mx0 + 360, my0 + 80, 140, 48)
			# draw buttons
			for r, lbl in ((buy_rect, "Buy Slot"), (sell_rect, "Sell Coin"), (restart_rect, "Restart")):
				# special-case Buy Slot when we've hit the global slot cap
				if lbl == "Buy Slot" and unlocked_slots >= MAX_SLOTS:
					btn_bg = (48, 48, 64)
					text_lbl = "Buy Slot (Maxed)"
					text_col = (200, 200, 200)
				else:
					btn_bg = (60, 100, 140)
					text_lbl = lbl
					text_col = (255, 255, 255)
				pygame.draw.rect(screen, btn_bg, r, border_radius=6)
				pygame.draw.rect(screen, (200, 200, 220), r, 2, border_radius=6)
				lsurf = render_text(small_font or font, text_lbl, text_col)
				screen.blit(lsurf, (r.x + (r.width - lsurf.get_width()) // 2, r.y + (r.height - lsurf.get_height()) // 2))

		# draw popups (sell / buy / upgrades) after HUD/modal so they fully overlay other UI
		if sell_popup:
			lvl = sell_popup["level"]
			price = current_prices.get(lvl, coin_value(lvl))
			pygame.draw.rect(screen, (40, 40, 50), sell_popup["rect"], border_radius=6)
			pygame.draw.rect(screen, (200,200,220), sell_popup["rect"], 2, border_radius=6)
			t = render_text(small_font or font, f"Sell C{lvl}: {price}", (220,220,220))
			screen.blit(t, (sell_popup["rect"].x + 8, sell_popup["rect"].y + 6))
			for r, lbl in ((sell_popup["sell1"], "1"), (sell_popup["sell5"], "5"), (sell_popup["sell_all"], "All")):
				pygame.draw.rect(screen, (60,100,140), r, border_radius=4)
				pygame.draw.rect(screen, (200,200,220), r, 1, border_radius=4)
				ls = render_text(small_font or font, lbl, (255,255,255))
				screen.blit(ls, (r.x + (r.width - ls.get_width())//2, r.y + (r.height - ls.get_height())//2))

		if buy_popup:
			pygame.draw.rect(screen, (36,36,44), buy_popup["rect"], border_radius=6)
			pygame.draw.rect(screen, (200,200,220), buy_popup["rect"], 2, border_radius=6)
			for opt in buy_popup["options"]:
				r = opt["rect"]
				lvl = opt["level"]
				cost = opt.get("cost", coin_value(lvl))
				disabled = (currency < cost) or (lvl > highest_purchasable)
				bg = (64,64,74) if disabled else (70,120,180)
				pygame.draw.rect(screen, bg, r, border_radius=4)
				pygame.draw.rect(screen, (200,200,220), r, 1, border_radius=4)
				lbl = f"Buy C{lvl} ({cost})"
				wrap = render_text_wrapped(small_font or font, lbl, (200,200,200) if disabled else (255,255,255), r.width - 8)
				x_off = r.x + max(0, (r.width - wrap.get_width())//2)
				y_off = r.y + max(0, (r.height - wrap.get_height())//2)
				screen.blit(wrap, (x_off, y_off))

		if upgrades_popup:
			r = upgrades_popup["rect"]
			sh = r.inflate(6,6)
			sh_surf = pygame.Surface((sh.width, sh.height))
			sh_surf.fill((8,8,12))
			screen.blit(sh_surf, (sh.x, sh.y))
			bg_surf = pygame.Surface((r.width, r.height))
			bg_surf.fill((36,36,44))
			screen.blit(bg_surf, (r.x, r.y))
			pygame.draw.rect(screen, (200,200,220), r, 2, border_radius=6)
			for opt in upgrades_popup["options"]:
				r2 = opt["rect"]
				action = opt.get("action")
				cost = opt.get("cost", 0)
				if action == "buy_slot":
					if unlocked_slots >= MAX_SLOTS:
						lbl = "Buy Slot (Maxed)"
						disabled = True
					else:
						lbl = f"Buy Slot ({cost})"
						disabled = (currency < cost)
				elif action == "buy_worker":
					lbl = f"Worker ({cost})"
					# disable if unaffordable or already owned
					disabled = (currency < cost) or worker_owned
				elif action == "buy_time_thief":
					max_tt = max_time_thief_count()
					lbl = f"Time Thief x{time_thief_count}/{max_tt} ({cost})"
					# disable if unaffordable or already at max
					disabled = (currency < cost) or (time_thief_count >= max_tt)
				else:
					lbl = "More..."
					disabled = False
				bg = (64,64,74) if disabled else (70,120,180)
				pygame.draw.rect(screen, bg, r2, border_radius=4)
				pygame.draw.rect(screen, (200,200,220), r2, 1, border_radius=4)
				wrap = render_text_wrapped(small_font or font, lbl, (200,200,200) if disabled else (255,255,255), r2.width - 16)
				y_off = r2.y + max(0, (r2.height - wrap.get_height())//2)
				screen.blit(wrap, (r2.x + 8, y_off))

		if prestige_popup:
			# dim background
			over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
			over.fill((0, 0, 0, 160))
			screen.blit(over, (0, 0))
			r = prestige_popup["rect"]
			pygame.draw.rect(screen, (40, 40, 50), (r.x, r.y, r.width, r.height), border_radius=8)
			pygame.draw.rect(screen, (200,200,220), (r.x, r.y, r.width, r.height), 2, border_radius=8)
			msg = render_text(big_font or font, "Prestige Reset?", (230,220,200))
			sub_text = "Reset progress for a prestige bonus? This cannot be undone."
			sub = render_text_wrapped(small_font or font, sub_text, (200,200,200), r.width - 40)
			screen.blit(msg, (r.x + 20, r.y + 12))
			screen.blit(sub, (r.x + 20, r.y + 52))
			# draw buttons
			y = prestige_popup["yes"]
			n = prestige_popup["no"]
			pygame.draw.rect(screen, (60,100,140), y, border_radius=6)
			pygame.draw.rect(screen, (200,200,220), y, 2, border_radius=6)
			pygame.draw.rect(screen, (100,60,60), n, border_radius=6)
			pygame.draw.rect(screen, (200,200,220), n, 2, border_radius=6)
			ys = render_text(small_font or font, "Yes, I'm sure", (255,255,255))
			ns = render_text(small_font or font, "No, not yet", (255,255,255))
			screen.blit(ys, (y.x + (y.width - ys.get_width())//2, y.y + (y.height - ys.get_height())//2))
			screen.blit(ns, (n.x + (n.width - ns.get_width())//2, n.y + (n.height - ns.get_height())//2))

		if help_popup:
			# dim background
			over = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
			over.fill((0, 0, 0, 160))
			screen.blit(over, (0, 0))
			r = help_popup["rect"]
			pygame.draw.rect(screen, (36,36,44), (r.x, r.y, r.width, r.height), border_radius=8)
			pygame.draw.rect(screen, (200,200,220), (r.x, r.y, r.width, r.height), 2, border_radius=8)
			# title
			title = render_text(big_font or font, "Help & Mechanics", (230,220,200))
			screen.blit(title, (r.x + 20, r.y + 12))
			# neat, short bullets for mechanics
			lines = [
				"- Deals create coins only (one per unlocked slot).",
				"- Sell coins to earn currency (sell popup).",
				"- Worker auto-deals every 2x manual cooldown when enabled.",
				"- Time Thief reduces cooldowns (min enforced).",
				f"- Slots cap at {MAX_SLOTS}; slot capacity = {SLOT_CAPACITY}.",
				"",
				"Spawn probabilities (current):",
			]
			# compute spawn probs with the same cap used for deals
			prob_cap = min(max(3, max((s.coin for s in slots), default=0) + 1), unlocked_slots + 2)
			probs = compute_spawn_probabilities(slots, cap=prob_cap)
			for lvl in sorted(probs.keys()):
				lines.append(f"  C{lvl}: {probs[lvl]:.1f}%")

			# Render all lines onto a clipped content surface so text never escapes the popup
			content_x = r.x + 20
			content_w = r.width - 40
			content_y = r.y + 56
			# prepare rendered line surfaces (wrapped to content width)
			line_surfs = []
			for ln in lines:
				sur = render_text_wrapped(small_font or font, ln, (200,200,200), content_w)
				line_surfs.append(sur)
			# total height of content
			total_h = sum(s.get_height() for s in line_surfs) + max(0, (len(line_surfs) - 1) * 8)
			max_content_h = r.height - (content_y - r.y) - 20
			if max_content_h < 1:
				max_content_h = 1
			# create a full content surface and blit all lines so we can scroll a viewport over it
			full_content_surf = pygame.Surface((content_w, max(1, total_h)), pygame.SRCALPHA)
			yi = 0
			for s in line_surfs:
				full_content_surf.blit(s, (0, yi))
				yi += s.get_height() + 8
			# visible viewport height inside popup
			visible_h = max(1, r.height - (content_y - r.y) - 20)
			# clamp scroll and compute viewport rect safely so it never exceeds the content surface
			scroll = int(help_popup.get("scroll", 0)) if isinstance(help_popup, dict) else 0
			# viewport height must not exceed full content height
			viewport_h = min(visible_h, full_content_surf.get_height())
			max_scroll = max(0, full_content_surf.get_height() - viewport_h)
			if scroll < 0:
				scroll = 0
			if scroll > max_scroll:
				scroll = max_scroll
			# blit visible region (safe subsurface)
			viewport = pygame.Rect(0, scroll, content_w, viewport_h)
			# when content is smaller than visible area, blit the whole content and leave remaining area empty
			if viewport_h <= 0:
				# nothing to blit
				pass
			else:
				try:
					screen.blit(full_content_surf.subsurface(viewport), (content_x, content_y))
				except ValueError:
					# fallback: blit as much as possible without using subsurface
					screen.blit(full_content_surf, (content_x, content_y))
			# draw a simple scrollbar if content overflows
			if full_content_surf.get_height() > visible_h:
				sb_x = content_x + content_w + 6
				sb_w = 8
				ratio = visible_h / full_content_surf.get_height()
				bar_h = max(int(visible_h * ratio), 8)
				if max_scroll > 0:
					bar_y = content_y + int((scroll / max_scroll) * (visible_h - bar_h))
				else:
					bar_y = content_y
				# draw track
				pygame.draw.rect(screen, (60,60,70), (sb_x, content_y, sb_w, visible_h), border_radius=4)
				# draw thumb
				pygame.draw.rect(screen, (140,140,160), (sb_x, bar_y, sb_w, bar_h), border_radius=4)
			# close button
			cr = help_popup["close"]
			pygame.draw.rect(screen, (60,100,140), cr, border_radius=6)
			pygame.draw.rect(screen, (200,200,220), cr, 2, border_radius=6)
			cs = render_text(small_font or font, "Close", (255,255,255))
			screen.blit(cs, (cr.x + (cr.width - cs.get_width())//2, cr.y + (cr.height - cs.get_height())//2))

		pygame.display.flip()

		# draw dragged coin on top
		if dragging and drag_surf:
			x, y = drag_pos
			screen.blit(drag_surf, (x - drag_surf.get_width() // 2, y - drag_surf.get_height() // 2))
			pygame.display.flip()

	pygame.quit()
	sys.exit()


def save_game(path, slots, unlocked_slots, currency, prestige_level, worker_owned=False, worker_enabled=False, time_thief_count=0):
	try:
		data = {
			"slots": [{"coin": s.coin, "count": s.count} for s in slots],
			"unlocked_slots": unlocked_slots,
			"currency": currency,
			"prestige_level": prestige_level,
			"worker_owned": bool(worker_owned),
			"worker_enabled": bool(worker_enabled),
			"time_thief_count": int(time_thief_count),
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