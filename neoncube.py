# neon_runner.py
import tkinter as tk
import random
import json
import os

WIDTH, HEIGHT = 900, 500
FPS_MS = 16
GRAVITY = 0.9
JUMP_V = -15
GROUND_H = 110
OBSTACLE_GAP_BASE = 140
SCORE_FILE = "neon_runner_highscore.json"

def load_highscore():
    try:
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, "r") as f:
                return json.load(f).get("highscore", 0)
    except:
        pass
    return 0

def save_highscore(score):
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump({"highscore": score}, f)
    except:
        pass


class Player:
    def __init__(self, canvas, x, y, w=36, h=36, color="#00FFF6"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vy = 0
        self.on_ground = False

        # glow
        self.glow = canvas.create_oval(
            self.x-14, self.y-6,
            self.x+self.w+14, self.y+self.h+6,
            fill="#00384D", outline=""
        )

        self.id = canvas.create_rectangle(
            self.x, self.y,
            self.x+self.w, self.y+self.h,
            fill=color, outline="#0FFFE6", width=2
        )

    def bbox(self):
        return self.canvas.bbox(self.id)

    def update_graphic(self):
        self.canvas.coords(self.glow,
                           self.x-14, self.y-6,
                           self.x+self.w+14, self.y+self.h+6)
        self.canvas.coords(self.id,
                           self.x, self.y,
                           self.x+self.w, self.y+self.h)

    def apply_gravity(self):
        self.vy += GRAVITY
        self.y += self.vy

        if self.y + self.h >= HEIGHT - GROUND_H:
            self.y = HEIGHT - GROUND_H - self.h
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.update_graphic()

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_V
            self.on_ground = False


class Obstacle:
    def __init__(self, canvas, x, y, w, h, speed, typ="block", color="#FF5A8F"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.typ = typ

        self.id = canvas.create_rectangle(x, y, x+w, y+h, fill=color, outline="")

        if typ != "block":
            self.top = canvas.create_rectangle(x, y, x+w, y+int(h*0.25),
                                               fill="#FFD166", outline="")
        else:
            self.top = None

    def update(self):
        dx = -self.speed
        self.x += dx
        self.canvas.move(self.id, dx, 0)
        if self.top:
            self.canvas.move(self.top, dx, 0)

        if self.x + self.w < -50:
            self.destroy()
            return False
        return True

    def bbox(self):
        return self.canvas.bbox(self.id)

    def destroy(self):
        self.canvas.delete(self.id)
        if self.top:
            self.canvas.delete(self.top)


class NeonRunner:
    def __init__(self, root):
        self.root = root
        root.title("Neon Runner")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg="#04061a", highlightthickness=0)
        self.canvas.pack()

        # Ground
        self.canvas.create_rectangle(
            0, HEIGHT-GROUND_H, WIDTH, HEIGHT,
            fill="#071126", outline=""
        )

        # Score UI
        self.hi = load_highscore()
        self.score_text = self.canvas.create_text(
            18, 12, anchor="nw",
            text="Score: 0",
            font=("Consolas", 18, "bold"),
            fill="#00FFC6"
        )
        self.hi_text = self.canvas.create_text(
            WIDTH-18, 12, anchor="ne",
            text=f"Best: {self.hi}",
            font=("Consolas", 14),
            fill="#FFD166"
        )

        # Parallax
        self.city_layers = []
        self.stars = []
        self.create_city_layers()
        self.create_stars(80)

        # Player
        px = 120
        py = HEIGHT - GROUND_H - 36
        self.player = Player(self.canvas, px, py)

        # State
        self.running = False
        self.paused = False
        self.spawn_timer = 0
        self.spawn_gap = OBSTACLE_GAP_BASE
        self.base_speed = 6
        self.score = 0
        self.obstacles = []

        # Input
        root.bind("<KeyPress>", self.key_down)
        root.bind("<KeyRelease>", self.key_up)

        # Start screen
        self.draw_start_overlay()

        self.root.after(FPS_MS, self.loop)

    # ----------------------------------------
    # START SCREEN
    # ----------------------------------------
    def draw_start_overlay(self):
        self.overlay = self.canvas.create_rectangle(
            0, 0, WIDTH, HEIGHT,
            fill="#000", stipple="gray25", outline=""
        )

        self.title_text = self.canvas.create_text(
            WIDTH/2, HEIGHT/2 - 60,
            text="NEON RUNNER",
            font=("Segoe UI", 36, "bold"),
            fill="#70D6FF"
        )

        self.start_text = self.canvas.create_text(
            WIDTH/2, HEIGHT/2 - 10,
            text="Press ENTER to Start",
            font=("Segoe UI", 16),
            fill="#EAEAEA"
        )

        self.ctrl_text = self.canvas.create_text(
            WIDTH/2, HEIGHT/2 + 40,
            text="Space / Up to Jump.   P to Pause.",
            font=("Segoe UI", 12),
            fill="#BFEAF5"
        )

        self.root.bind("<Return>", lambda e: self.start())

    def start(self):
        if self.running:
            return

        # Remove overlay + texts
        for item in [self.overlay, self.title_text, self.start_text, self.ctrl_text]:
            try:
                self.canvas.delete(item)
            except:
                pass

        # Reset game state
        self.running = True
        self.paused = False
        self.score = 0
        self.spawn_timer = 0
        self.base_speed = 6
        self.spawn_gap = OBSTACLE_GAP_BASE
        self.obstacles = []

        self.canvas.itemconfig(self.score_text, text="Score: 0")
        self.canvas.itemconfig(self.hi_text, text=f"Best: {self.hi}")

    # ----------------------------------------

    def create_city_layers(self):
        colors = ["#061020", "#091826", "#0b2230"]
        heights = [50, 80, 120]
        base = HEIGHT - GROUND_H

        for i in range(3):
            group = []
            for x in range(0, WIDTH+200, 120 + i*30):
                h = random.randint(heights[i]//2, heights[i])
                r = self.canvas.create_rectangle(
                    x, base-h, x+100, base,
                    fill=colors[i], outline=""
                )
                group.append(r)
            self.city_layers.append({"items": group, "vx": -0.4*(i+1)})

    def create_stars(self, count):
        for _ in range(count):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT-150)
            r = random.choice([1, 1, 2])

            dot = self.canvas.create_oval(
                x, y, x+r, y+r,
                fill="#9FBFFF", outline=""
            )

            self.stars.append({
                "id": dot,
                "vx": -0.08 - random.random()*0.12,
                "vy": 0.02*random.random(),
                "r": r
            })

    # ----------------------------------------

    def key_down(self, e):
        if e.keysym in ("space", "Up"):
            if self.running and not self.paused:
                self.player.jump()
        if e.keysym.lower() == "p" and self.running:
            self.paused = not self.paused
        if e.keysym == "Return" and not self.running:
            self.start()

    def key_up(self, e):
        pass

    # ----------------------------------------

    def spawn_obstacle(self):
        typ = random.choice(["block","block","spike"])
        height = random.randint(30, 80) if typ == "block" else random.randint(40, 90)
        w = random.randint(28, 60) if typ=="block" else random.randint(18, 28)
        x = WIDTH + 30
        y = HEIGHT - GROUND_H - height

        speed = self.base_speed + random.random()*1.8
        color = "#FF5A8F" if typ=="block" else "#FF8A65"

        ob = Obstacle(self.canvas, x, y, w, height, speed, typ=typ, color=color)
        self.obstacles.append(ob)

    # ----------------------------------------

    def move_city_and_stars(self):
        # stars
        for s in self.stars:
            self.canvas.move(s["id"], s["vx"], s["vy"])
            x1, y1, x2, y2 = self.canvas.coords(s["id"])
            if x2 < -10:
                nx = WIDTH + random.randint(10, 300)
                ny = random.randint(10, HEIGHT-200)
                self.canvas.coords(s["id"], nx, ny, nx+s["r"], ny+s["r"])

        # buildings
        for layer in self.city_layers:
            vx = layer["vx"] - (self.base_speed/200)
            for item in layer["items"]:
                self.canvas.move(item, vx, 0)
                x1, y1, x2, y2 = self.canvas.coords(item)
                if x2 < -120:
                    nx = WIDTH + random.randint(0, 200)
                    h = random.randint(20, 120)
                    base = HEIGHT - GROUND_H
                    self.canvas.coords(item, nx, base-h, nx+100, base)

    # ----------------------------------------

    def loop(self):
        if self.running and not self.paused:
            self.move_city_and_stars()
            self.player.apply_gravity()

            # spawn
            if self.spawn_timer % max(1, int(self.spawn_gap)) == 0:
                if len(self.obstacles) < 6:
                    self.spawn_obstacle()

            # move obstacles
            newlist = []
            for ob in self.obstacles:
                if ob.update():
                    newlist.append(ob)
            self.obstacles = newlist

            # collision
            pb = self.player.bbox()
            if pb:
                px1, py1, px2, py2 = pb
                for ob in self.obstacles:
                    ex1, ey1, ex2, ey2 = ob.bbox()
                    if not (px2 < ex1 or px1 > ex2 or py2 < ey1 or py1 > ey2):
                        self.game_over()
                        break

            # score
            for ob in self.obstacles:
                if ob.x + ob.w < self.player.x and not hasattr(ob, "counted"):
                    ob.counted = True
                    self.score += 1
                    self.canvas.itemconfig(self.score_text,
                                           text=f"Score: {self.score}")

                    if self.score % 5 == 0:
                        self.base_speed += 18
                        self.spawn_gap = max(80, self.spawn_gap -8)

            self.spawn_timer += 1

        self.root.after(FPS_MS, self.loop)

    # ----------------------------------------

    def game_over(self):
        self.running = False

        if self.score > self.hi:
            self.hi = self.score
            save_highscore(self.hi)

        overlay = self.canvas.create_rectangle(
            0, 0, WIDTH, HEIGHT,
            fill="#000", stipple="gray25", outline=""
        )

        self.canvas.create_text(
            WIDTH/2, HEIGHT/2 - 40,
            text="GAME OVER",
            font=("Segoe UI", 36, "bold"),
            fill="#FF6B6B"
        )

        self.canvas.create_text(
            WIDTH/2, HEIGHT/2,
            text=f"Score: {self.score}",
            font=("Segoe UI", 20),
            fill="#FFFFFF"
        )

        self.canvas.create_text(
            WIDTH/2, HEIGHT/2 + 44,
            text="Press Enter to Restart",
            font=("Segoe UI", 14),
            fill="#EAEAEA"
        )

        self.canvas.itemconfig(self.hi_text, text=f"Best: {self.hi}")


# ----------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    NeonRunner(root)
    root.mainloop()
