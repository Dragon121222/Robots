#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════╗
║  GHOST//MONITOR  —  SECTION 9 SYSTEMS    ║
╚═══════════════════════════════════════════╝
Cyberpunk/GitS system monitor. Requires: psutil
Install: pip install psutil
Run:     python3 ghost_monitor.py
Keys:    q=quit  p=sort-pid  c=sort-cpu  m=sort-mem  k=kill  TAB=focus
"""

import curses
import psutil
import time
import math
import random
import threading
import signal
import sys
from collections import deque
from datetime import datetime

# ── Palette indices ────────────────────────────────────────────────────────────
C_BG        = 0   # terminal default bg (near-black assumed)
C_CYAN      = 1   # primary: cold cyan
C_MAGENTA   = 2   # accent: hot magenta
C_GREEN     = 3   # ok/low
C_YELLOW    = 4   # warn/mid
C_RED       = 5   # crit/high
C_WHITE     = 6   # labels
C_DIM       = 7   # dim/border
C_BLUE      = 8   # secondary accent
C_ORANGE    = 9   # io accent

KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
GLITCH_CHARS = "▓▒░█▄▀■□▪▫◆◇○●"

HISTORY_LEN = 120

class GhostMonitor:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.running = True
        self.lock = threading.Lock()

        # Data history
        self.cpu_hist    = deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.mem_hist    = deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.net_send_hist = deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.net_recv_hist = deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.disk_r_hist = deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.disk_w_hist = deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)

        # Current snapshot
        self.cpu_per_core = []
        self.mem_info     = None
        self.disk_info    = None
        self.net_info     = None
        self.processes    = []
        self.uptime       = 0
        self.load_avg     = (0, 0, 0)

        # UI state
        self.proc_sort    = 'cpu'   # 'cpu' | 'mem' | 'pid' | 'name'
        self.proc_offset  = 0
        self.selected     = 0
        self.focus        = 0       # 0=procs, 1=other panels (future)
        self.tick         = 0
        self.glitch_frame = 0

        # Katakana rain state
        self.kana_cols    = {}      # col -> (row, speed, char_idx)

        # Net/disk baseline
        self._net_prev  = psutil.net_io_counters()
        self._disk_prev = psutil.disk_io_counters()
        self._prev_time = time.time()

        self._init_colors()
        self._init_kana_rain()

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(C_CYAN,    196, -1)   # will reassign below
        # Full 256-color palette
        curses.init_pair(C_CYAN,    51,  -1)   # bright cyan
        curses.init_pair(C_MAGENTA, 201, -1)   # hot magenta
        curses.init_pair(C_GREEN,   118, -1)   # neon green
        curses.init_pair(C_YELLOW,  220, -1)   # amber
        curses.init_pair(C_RED,     196, -1)   # red
        curses.init_pair(C_WHITE,   255, -1)   # near-white
        curses.init_pair(C_DIM,     238, -1)   # dark grey
        curses.init_pair(C_BLUE,    39,  -1)   # deep cyan-blue
        curses.init_pair(C_ORANGE,  214, -1)   # orange

    def _init_kana_rain(self):
        h, w = self.scr.getmaxyx()
        # Sparse columns for background effect
        for col in range(0, w, random.randint(6, 12)):
            self.kana_cols[col] = [
                random.randint(0, h),
                random.uniform(0.3, 1.0),
                random.randint(0, len(KATAKANA)-1)
            ]

    def _attr(self, pair, bold=False, dim=False):
        a = curses.color_pair(pair)
        if bold: a |= curses.A_BOLD
        if dim:  a |= curses.A_DIM
        return a

    def collect(self):
        """Background data collection thread."""
        while self.running:
            now = time.time()
            dt  = max(now - self._prev_time, 0.001)

            cpu_cores = psutil.cpu_percent(percpu=True)
            cpu_avg   = sum(cpu_cores) / len(cpu_cores)
            mem       = psutil.virtual_memory()
            disk      = psutil.disk_usage('/')
            net_cur   = psutil.net_io_counters()
            disk_cur  = psutil.disk_io_counters()

            net_send = (net_cur.bytes_sent - self._net_prev.bytes_sent) / dt
            net_recv = (net_cur.bytes_recv - self._net_prev.bytes_recv) / dt
            disk_r   = (disk_cur.read_bytes  - self._disk_prev.read_bytes)  / dt
            disk_w   = (disk_cur.write_bytes - self._disk_prev.write_bytes) / dt

            try:
                load = psutil.getloadavg()
            except AttributeError:
                load = (0, 0, 0)

            procs = []
            for p in psutil.process_iter(['pid','name','cpu_percent','memory_percent','status','username']):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            with self.lock:
                self.cpu_per_core = cpu_cores
                self.cpu_hist.append(cpu_avg)
                self.mem_hist.append(mem.percent)
                self.net_send_hist.append(net_send)
                self.net_recv_hist.append(net_recv)
                self.disk_r_hist.append(disk_r / 1024)
                self.disk_w_hist.append(disk_w / 1024)
                self.mem_info  = mem
                self.disk_info = disk
                self.net_info  = (net_send, net_recv, net_cur)
                self.processes = procs
                self.load_avg  = load
                self.uptime    = time.time() - psutil.boot_time()
                self._net_prev  = net_cur
                self._disk_prev = disk_cur
                self._prev_time = now

            time.sleep(1.0)

    # ── Drawing helpers ────────────────────────────────────────────────────────

    def safe_addstr(self, y, x, s, attr=0):
        h, w = self.scr.getmaxyx()
        if y < 0 or y >= h: return
        if x < 0: s = s[-x:]; x = 0
        if x >= w: return
        avail = w - x
        if avail <= 0: return
        try:
            self.scr.addstr(y, x, s[:avail], attr)
        except curses.error:
            pass

    def hline(self, y, x, ch, n, attr=0):
        """Draw a horizontal line. Uses addstr for Unicode chars (curses.hline only handles bytes)."""
        scr_h, scr_w = self.scr.getmaxyx()
        n = min(n, scr_w - x)
        if n <= 0 or y < 0 or y >= scr_h:
            return
        # curses.hline chokes on multibyte Unicode — always use addstr
        if isinstance(ch, str):
            self.safe_addstr(y, x, ch * n, attr)
        else:
            try:
                self.scr.hline(y, x, ch, n, attr)
            except curses.error:
                pass

    def box(self, y, x, h, w, title='', title_attr=0, border_attr=0):
        """Draw a rounded-corner box with optional title."""
        ba = border_attr or self._attr(C_DIM)
        # corners
        self.safe_addstr(y,     x,     '╔', ba)
        self.safe_addstr(y,     x+w-1, '╗', ba)
        self.safe_addstr(y+h-1, x,     '╚', ba)
        self.safe_addstr(y+h-1, x+w-1, '╝', ba)
        # top/bottom
        self.hline(y,     x+1, curses.ACS_HLINE, w-2, ba)
        self.hline(y+h-1, x+1, curses.ACS_HLINE, w-2, ba)
        # sides
        for i in range(1, h-1):
            self.safe_addstr(y+i, x,     '║', ba)
            self.safe_addstr(y+i, x+w-1, '║', ba)
        # title
        if title:
            t = f' {title} '
            tx = x + max(1, (w - len(t)) // 2)
            self.safe_addstr(y, tx, t, title_attr or self._attr(C_CYAN, bold=True))

    def bar(self, y, x, width, pct, color_pair=None):
        """Render a gradient bar: ▏▎▍▌▋▊▉█"""
        filled = int(pct / 100 * width)
        filled = min(filled, width)
        empty  = width - filled

        if color_pair is None:
            if pct < 50:   color_pair = C_GREEN
            elif pct < 80: color_pair = C_YELLOW
            else:          color_pair = C_RED

        self.safe_addstr(y, x, '█' * filled, self._attr(color_pair, bold=True))
        self.safe_addstr(y, x+filled, '░' * empty, self._attr(C_DIM))

    def sparkline(self, y, x, width, data, color_pair=C_CYAN, max_val=100):
        """8-level block sparkline from deque."""
        blocks = ' ▁▂▃▄▅▆▇█'
        pts = list(data)[-width:]
        if not pts: return
        mv = max_val or (max(pts) or 1)
        line = ''
        for v in pts:
            idx = min(int(v / mv * 8), 8)
            line += blocks[idx]
        # pad left if short
        line = line.rjust(width)
        self.safe_addstr(y, x, line, self._attr(color_pair))

    def _fmt_bytes(self, b):
        for unit in ('B','K','M','G','T'):
            if b < 1024: return f'{b:6.1f}{unit}'
            b /= 1024
        return f'{b:6.1f}P'

    def _fmt_uptime(self, secs):
        d = int(secs // 86400)
        h = int((secs % 86400) // 3600)
        m = int((secs % 3600) // 60)
        s = int(secs % 60)
        return f'{d}d {h:02d}:{m:02d}:{s:02d}'

    # ── Kana rain background ───────────────────────────────────────────────────

    def draw_kana_rain(self):
        h, w = self.scr.getmaxyx()
        if self.tick % 3 != 0: return
        for col, state in self.kana_cols.items():
            row, speed, cidx = state
            if col < w and row < h - 1:
                ch = KATAKANA[cidx % len(KATAKANA)]
                # bright head
                self.safe_addstr(int(row), col, ch, self._attr(C_CYAN, bold=True))
                # dim tail (2 rows up)
                tr = int(row) - 2
                if tr >= 0:
                    self.safe_addstr(tr, col, KATAKANA[(cidx-2) % len(KATAKANA)],
                                     self._attr(C_DIM))
                # erase further tail
                er = int(row) - 5
                if er >= 0:
                    self.safe_addstr(er, col, ' ')
            state[0] = (row + speed) % h
            state[2] = (cidx + 1) % len(KATAKANA)

    # ── Panel: Header ──────────────────────────────────────────────────────────

    def draw_header(self, y, x, w):
        now = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
        hostname = 'SECTION-9'
        try:
            import socket
            hostname = socket.gethostname().upper()[:16]
        except: pass

        # Glitch effect on title occasionally
        title = 'GHOST//MONITOR'
        if random.random() < 0.04:
            gi = random.randint(0, len(title)-1)
            title = title[:gi] + random.choice(GLITCH_CHARS) + title[gi+1:]

        self.safe_addstr(y, x, '▌', self._attr(C_MAGENTA, bold=True))
        self.safe_addstr(y, x+1, title, self._attr(C_CYAN, bold=True))
        self.safe_addstr(y, x+len(title)+2, '▐', self._attr(C_MAGENTA, bold=True))

        # Right side: hostname + time
        info = f'{hostname}  ⟨{now}⟩'
        self.safe_addstr(y, x + w - len(info) - 1, info, self._attr(C_WHITE))

        # Uptime + load
        with self.lock:
            up   = self._fmt_uptime(self.uptime)
            load = self.load_avg
        load_str = f'LOAD {load[0]:.2f} {load[1]:.2f} {load[2]:.2f}'
        self.safe_addstr(y+1, x, f'↑ {up}', self._attr(C_DIM))
        self.safe_addstr(y+1, x + w - len(load_str) - 1, load_str, self._attr(C_DIM))

        # Separator
        self.hline(y+2, x, '─', w, self._attr(C_DIM))

    # ── Panel: CPU ────────────────────────────────────────────────────────────

    def draw_cpu(self, y, x, h, w):
        with self.lock:
            cores  = self.cpu_per_core[:]
            hist   = list(self.cpu_hist)
            avg    = (sum(cores) / len(cores)) if cores else 0

        self.box(y, x, h, w, title='CPU', border_attr=self._attr(C_DIM))

        # Sparkline in top area
        spark_w = w - 4
        self.sparkline(y+1, x+2, spark_w, self.cpu_hist,
                       C_CYAN if avg < 80 else C_RED)

        # Avg bar
        pct_str = f'{avg:5.1f}%'
        self.safe_addstr(y+2, x+2, 'AVG', self._attr(C_DIM))
        bar_w = w - 10 - len(pct_str)
        self.bar(y+2, x+6, bar_w, avg)
        self.safe_addstr(y+2, x+6+bar_w+1, pct_str, self._attr(C_WHITE, bold=True))

        # Per-core grid
        cols_per_row = max(1, (w - 4) // 14)
        for i, pct in enumerate(cores):
            col = i % cols_per_row
            row = i // cols_per_row
            cy  = y + 3 + row
            cx  = x + 2 + col * 14
            if cy >= y + h - 1: break
            color = C_GREEN if pct < 50 else C_YELLOW if pct < 80 else C_RED
            core_bar_w = 7
            self.safe_addstr(cy, cx, f'C{i:<2}', self._attr(C_DIM))
            self.bar(cy, cx+3, core_bar_w, pct, color)
            self.safe_addstr(cy, cx+11, f'{pct:3.0f}', self._attr(color, bold=True))

    # ── Panel: Memory ─────────────────────────────────────────────────────────

    def draw_mem(self, y, x, h, w):
        with self.lock:
            mem = self.mem_info

        self.box(y, x, h, w, title='MEM', border_attr=self._attr(C_DIM))
        if not mem: return

        pct = mem.percent
        self.sparkline(y+1, x+2, w-4, self.mem_hist,
                       C_MAGENTA if pct < 80 else C_RED)

        rows = [
            ('USED', mem.used,      pct,              C_MAGENTA),
            ('FREE', mem.available, 100-pct,          C_GREEN),
            ('BUFF', mem.buffers if hasattr(mem,'buffers') else 0,
             (mem.buffers/mem.total*100) if hasattr(mem,'buffers') else 0, C_BLUE),
        ]
        bar_w = w - 18
        for i, (label, val, p, color) in enumerate(rows):
            ry = y + 2 + i
            if ry >= y + h - 1: break
            self.safe_addstr(ry, x+2, f'{label}', self._attr(C_DIM))
            self.bar(ry, x+7, bar_w, p, color)
            self.safe_addstr(ry, x+7+bar_w+1,
                             self._fmt_bytes(val).strip(),
                             self._attr(C_WHITE))

        # Total
        total_str = f'TOTAL {self._fmt_bytes(mem.total).strip()}'
        self.safe_addstr(y+h-2, x+2, total_str, self._attr(C_DIM))

    # ── Panel: Network ────────────────────────────────────────────────────────

    def draw_net(self, y, x, h, w):
        with self.lock:
            net = self.net_info

        self.box(y, x, h, w, title='NET', border_attr=self._attr(C_DIM))
        if not net: return

        send, recv, counters = net
        spark_w = w - 4
        half_w  = (spark_w) // 2 - 1

        # Dual sparklines
        max_bw = max(max(self.net_recv_hist, default=1),
                     max(self.net_send_hist, default=1), 1)
        self.safe_addstr(y+1, x+2, '▲', self._attr(C_ORANGE))
        self.sparkline(y+1, x+3, half_w, self.net_send_hist, C_ORANGE, max_bw)
        self.safe_addstr(y+1, x+3+half_w+1, '▼', self._attr(C_BLUE))
        self.sparkline(y+1, x+3+half_w+2, half_w, self.net_recv_hist, C_BLUE, max_bw)

        # Current rates
        self.safe_addstr(y+2, x+2,
            f'▲ {self._fmt_bytes(send).strip():>8}/s', self._attr(C_ORANGE, bold=True))
        self.safe_addstr(y+3, x+2,
            f'▼ {self._fmt_bytes(recv).strip():>8}/s', self._attr(C_BLUE, bold=True))

        # Totals
        self.safe_addstr(y+4, x+2,
            f'  TX {self._fmt_bytes(counters.bytes_sent).strip()}',
            self._attr(C_DIM))
        self.safe_addstr(y+5, x+2,
            f'  RX {self._fmt_bytes(counters.bytes_recv).strip()}',
            self._attr(C_DIM))

    # ── Panel: Disk ───────────────────────────────────────────────────────────

    def draw_disk(self, y, x, h, w):
        with self.lock:
            disk = self.disk_info

        self.box(y, x, h, w, title='DISK', border_attr=self._attr(C_DIM))
        if not disk: return

        pct = disk.percent
        bar_w = w - 4
        self.safe_addstr(y+1, x+2, '/', self._attr(C_DIM))
        self.bar(y+1, x+4, bar_w-2, pct,
                 C_GREEN if pct < 70 else C_YELLOW if pct < 90 else C_RED)

        used_str = self._fmt_bytes(disk.used).strip()
        tot_str  = self._fmt_bytes(disk.total).strip()
        self.safe_addstr(y+2, x+2,
            f'{used_str} / {tot_str}  ({pct:.1f}%)',
            self._attr(C_WHITE))

        # IO sparklines
        max_io = max(max(self.disk_r_hist, default=1),
                     max(self.disk_w_hist, default=1), 1)
        half   = (w - 5) // 2
        self.safe_addstr(y+3, x+2, 'R', self._attr(C_GREEN))
        self.sparkline(y+3, x+3, half, self.disk_r_hist, C_GREEN, max_io)
        self.safe_addstr(y+3, x+3+half+1, 'W', self._attr(C_YELLOW))
        self.sparkline(y+3, x+4+half, half, self.disk_w_hist, C_YELLOW, max_io)

        # Current KB/s
        r_kb = list(self.disk_r_hist)[-1] if self.disk_r_hist else 0
        w_kb = list(self.disk_w_hist)[-1] if self.disk_w_hist else 0
        self.safe_addstr(y+4, x+2,
            f'R {r_kb:8.1f}KB/s  W {w_kb:8.1f}KB/s',
            self._attr(C_DIM))

    # ── Panel: Process List ───────────────────────────────────────────────────

    def draw_procs(self, y, x, h, w):
        with self.lock:
            procs = sorted(
                self.processes,
                key=lambda p: (
                    -(p.get('cpu_percent') or 0) if self.proc_sort == 'cpu'
                    else -(p.get('memory_percent') or 0) if self.proc_sort == 'mem'
                    else (p.get('pid') or 0) if self.proc_sort == 'pid'
                    else (p.get('name') or '')
                )
            )
            sort_key = self.proc_sort

        self.box(y, x, h, w,
                 title=f'PROCESSES  sort:{sort_key.upper()}',
                 title_attr=self._attr(C_MAGENTA, bold=True),
                 border_attr=self._attr(C_DIM))

        # Column header
        hdr = f'{"PID":>7}  {"CPU%":>5}  {"MEM%":>5}  {"STATUS":<10}  {"NAME"}'
        self.safe_addstr(y+1, x+2, hdr[:w-4], self._attr(C_CYAN, bold=True))
        self.hline(y+2, x+1, '─', w-2, self._attr(C_DIM))

        visible = h - 4
        max_offset = max(0, len(procs) - visible)
        self.proc_offset = min(self.proc_offset, max_offset)

        for i, p in enumerate(procs[self.proc_offset:self.proc_offset+visible]):
            ry = y + 3 + i
            if ry >= y + h - 1: break

            pid    = p.get('pid') or 0
            name   = (p.get('name') or '?')[:24]
            cpu    = p.get('cpu_percent') or 0.0
            mem    = p.get('memory_percent') or 0.0
            status = (p.get('status') or '?')[:10]

            is_sel = (i + self.proc_offset) == self.selected
            base_attr = curses.A_REVERSE if is_sel else 0

            cpu_color = (C_GREEN if cpu < 20 else C_YELLOW if cpu < 60 else C_RED)
            mem_color = (C_GREEN if mem < 5  else C_YELLOW if mem < 20 else C_RED)

            line = f'{pid:>7}  {cpu:>5.1f}  {mem:>5.1f}  {status:<10}  '
            self.safe_addstr(ry, x+2, line[:w-4-len(name)],
                             self._attr(C_WHITE) | base_attr)
            # colorize cpu/mem values
            col_cpu = x + 10
            col_mem = x + 18
            if not is_sel:
                self.safe_addstr(ry, col_cpu, f'{cpu:>5.1f}', self._attr(cpu_color, bold=True))
                self.safe_addstr(ry, col_mem, f'{mem:>5.1f}', self._attr(mem_color, bold=True))

            name_x = x + 2 + len(line)
            self.safe_addstr(ry, name_x, name[:w-4-len(line)],
                             self._attr(C_CYAN) | base_attr)

        # Footer hint
        hint = ' [c]cpu [m]mem [p]pid [↑↓]scroll [k]kill [q]quit '
        self.safe_addstr(y+h-1, x + max(1,(w-len(hint))//2),
                         hint[:w-2], self._attr(C_DIM))

    # ── Main render ───────────────────────────────────────────────────────────

    def render(self):
        self.scr.erase()
        h, w = self.scr.getmaxyx()

        self.draw_kana_rain()
        self.draw_header(0, 0, w)

        # Layout: header=3 rows
        content_y = 3
        content_h = h - content_y

        # Top row: CPU | MEM  (split ~60/40)
        top_h  = max(7, content_h // 3)
        cpu_w  = max(20, (w * 6) // 10)
        mem_w  = w - cpu_w

        self.draw_cpu(content_y,       0,      top_h, cpu_w)
        self.draw_mem(content_y,       cpu_w,  top_h, mem_w)

        # Middle row: NET | DISK
        mid_y  = content_y + top_h
        mid_h  = max(7, content_h // 4)
        net_w  = w // 2
        disk_w = w - net_w

        self.draw_net( mid_y, 0,      mid_h, net_w)
        self.draw_disk(mid_y, net_w,  mid_h, disk_w)

        # Bottom: process list
        proc_y = mid_y + mid_h
        proc_h = h - proc_y
        if proc_h >= 5:
            self.draw_procs(proc_y, 0, proc_h, w)

        self.scr.refresh()

    # ── Input handling ────────────────────────────────────────────────────────

    def handle_input(self):
        self.scr.timeout(250)
        key = self.scr.getch()
        if key == -1: return

        if key in (ord('q'), ord('Q'), 27):
            self.running = False

        elif key == ord('c'):
            self.proc_sort = 'cpu'
        elif key == ord('m'):
            self.proc_sort = 'mem'
        elif key == ord('p'):
            self.proc_sort = 'pid'
        elif key == ord('n'):
            self.proc_sort = 'name'

        elif key == curses.KEY_DOWN:
            with self.lock:
                maxp = len(self.processes) - 1
            self.selected = min(self.selected + 1, maxp)
            h, _ = self.scr.getmaxyx()
            visible = max(1, h - 3 - 3 - (h//3) - (h//4) - 4)
            if self.selected >= self.proc_offset + visible:
                self.proc_offset += 1

        elif key == curses.KEY_UP:
            self.selected = max(self.selected - 1, 0)
            if self.selected < self.proc_offset:
                self.proc_offset = max(0, self.proc_offset - 1)

        elif key == ord('k'):
            with self.lock:
                procs = sorted(
                    self.processes,
                    key=lambda p: -(p.get('cpu_percent') or 0)
                )
            if 0 <= self.selected < len(procs):
                pid = procs[self.selected].get('pid')
                if pid:
                    try:
                        import os
                        os.kill(pid, signal.SIGTERM)
                    except (PermissionError, ProcessLookupError):
                        pass

    # ── Run loop ──────────────────────────────────────────────────────────────

    def run(self):
        curses.curs_set(0)
        self.scr.nodelay(False)

        collector = threading.Thread(target=self.collect, daemon=True)
        collector.start()

        # Brief init pause so first render has data
        time.sleep(0.3)

        try:
            while self.running:
                self.render()
                self.handle_input()
                self.tick += 1
        finally:
            self.running = False


def main(stdscr):
    mon = GhostMonitor(stdscr)
    mon.run()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print('\033[0m')  # reset colors
    print('// GHOST//MONITOR — DISCONNECTED //')
