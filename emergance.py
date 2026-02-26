#!/usr/bin/env python3

import psutil
import curses
import random
from playground.cyber_punk.cyber_tui import CyberTUI, C_CYAN, C_MAGENTA, C_GREEN, C_DIM
from playground.cyber_punk.node_graph import Graph, GraphRenderer, Node, Port
from playground.network.ip import get_local_ip

g = Graph()

start_x = 1
start_y = 0
g.add_node(Node(
    id='node_a', title='Wake Up', x=start_x, y=start_y,
    value=' v1',
))

start_y=start_y+4
g.add_node(Node(
    id='node_b', title='Check Network Status', x=start_x, y=start_y,
    value=' v2',
))

start_y=start_y+4
g.add_node(Node(
    id='node_c', title='CPU', x=start_x, y=start_y,
    value='',
))

start_y=start_y+4
g.add_node(Node(
    id='node_d', title='Goal', x=start_x, y=start_y,
    value='',
))


def start():
    app = CyberTUI(tick_ms=100)
    renderer = GraphRenderer(app, g)

    app.state.update({
        'bars': [(f'CH{i}', random.uniform(10, 90)) for i in range(6)],
        'log':  [f'[{i:03d}] init ok' for i in range(30)],
        'tick': 0,
    })

    g.nodes['node_a'].value = "online..."
    g.nodes['node_b'].value = get_local_ip()


    app.watch(
        cmd       = ['fish', '../../../Software/scripts/network/sshlan.fish'],
        state_key = 'ssh_scan',
        grep      = None,
        interval  = 300,
    )

    # ── Panels ─────────────────────────────────────────────────────────────────

    @app.panel(x=0, y=0, w=0.75, h=0.8, title='Main System',
               scrollable=True, name='main')
    def panel_main(scr, box, state, scroll):
        renderer.draw(scr, box)



    @app.panel(x=0.75, y=0, w=0.25, h=0.8, title='LOG',
               title_color=C_MAGENTA, scrollable=True, name='log')
    def panel_log(scr, box, state, scroll):

        inner = box.inner()

        app.sparkline(scr, inner.y1, inner.x1, inner.w,
                      [v for _, v in state['bars']], color=C_CYAN)

        ts  = state.get('ssh_scan_ts',  '')
        err = state.get('ssh_scan_err', '')
        meta = f'last run: {ts}' + (f'  ⚠ {err[:40]}' if err else '')
        app.putch(scr, inner.y1 + 1, inner.x1, meta[:inner.w], app.attr(C_DIM))
        for i, line in enumerate(state.get('ssh_scan', [])[scroll:scroll+inner.h-2]):
            app.putch(scr, inner.y1+2+i, inner.x1, line[:inner.w], app.attr(C_GREEN))

        # inner = box.inner()
        # for i, line in enumerate(state['log'][scroll:scroll+inner.h]):
        #    app.putch(scr, inner.y1+i, inner.x1, line[:inner.w], app.attr(C_CYAN))

    @app.panel(x=0, y=0.8, w=1.0, h=0.2, title='SYSTEM LOG')
    def panel_status(scr, box, state):
        inner = box.inner()
        app.putch(scr, inner.y1,   inner.x1,
                  f'tick={state["tick"]}  '
                  f'main={app.scroll_of("main")}  log={app.scroll_of("log")}',
                  app.attr(C_CYAN))
        app.putch(scr, inner.y1+1, inner.x1,
                  '[q]quit  [↕ swipe]scroll panels  [r]randomize',
                  app.attr(C_CYAN))

    # ── Updater ────────────────────────────────────────────────────────────────

    @app.updater
    def tick(state):
        state['tick'] += 1
        if state['tick'] % 8 == 0:
            state['bars'] = [
                (l, min(100, max(0, v + random.uniform(-8, 8))))
                for l, v in state['bars']
            ]

        if state['tick'] % 15 == 0:
            g.nodes['node_c'].value = str(psutil.cpu_percent(interval=0.1))

    # ── Keybinds ───────────────────────────────────────────────────────────────

    @app.on_key('r')
    def randomize(state):
        state['bars'] = [(l, random.uniform(10, 90)) for l, _ in state['bars']]
        state['log'].append(f'[{len(state["log"]):03d}] randomized')

    app.run()


if __name__ == '__main__':
    start()
