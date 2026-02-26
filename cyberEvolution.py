from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameTui import GameTUI
from playground.tuiEngine.gameObjects.gameMatrix import Matrix
from playground.tuiEngine.gameObjects.gameTerrainGenerator import generate_terrain
from playground.tuiEngine.gameObjects.gameObject import GameObject
from playground.tuiEngine.gameObjects.gameInfoPanel import draw_info_panel

if __name__ == '__main__':
    import curses as _c

    app    = GameTUI(fps=30)

    matrix = Matrix(cols=300, rows=300)
    generate_terrain(matrix, scale=0.01, seed=42)

    class Player(GameObject):
        """@brief Player character 人."""
        def __init__(self, x, y):
            super().__init__(x, y, character='人', color='#ffffff',
                             collision=False, layer='fg',
                             description='The player character.')
        def on_key(self, key: int) -> bool:
            if   key == _c.KEY_UP:    return self.move( 0,-1)
            elif key == _c.KEY_DOWN:  return self.move( 0, 1)
            elif key == _c.KEY_LEFT:  return self.move(-1, 0)
            elif key == _c.KEY_RIGHT: return self.move( 1, 0)
            return False

    matrix.add(Player(x=150, y=150))
    app.active_matrix = matrix

    @app.panel(x=0, y=0, w=0.75, h=1.0, title='[ WORLD ]',
               border_color='#336633', title_color='#00ff88',
               matrix=matrix)
    def world(scr, inner, ctx, dt): pass

    @app.panel(x=0.75, y=0, w=0.25, h=1.0, title='[ INFO ]',
               border_color='#444466', title_color='#8888ff')
    def info_panel(scr, inner, ctx, dt):
        draw_info_panel(scr, inner, app.info)

    @app.on_key('q')
    def quit(state, dt): app.quit()

    app.run()