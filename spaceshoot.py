import tkinter as tk
import random

WIDTH = 600
HEIGHT = 700

# ================= PARTICLE CLASS ==================
class Particle:
    def __init__(self, canvas, x, y, color, size=4):
        self.canvas = canvas
        self.id = canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")
        self.dx = random.uniform(-1.2, 1.2)
        self.dy = random.uniform(-2, 1)
        self.life = random.randint(8, 15)

    def update(self):
        self.canvas.move(self.id, self.dx, self.dy)
        self.dy += 0.05
        self.life -= 1
        return self.life > 0


# ================= GAME CLASS ==================
class Game:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Galaxy Shooter — FIXED VERSION")

        self.canvas = tk.Canvas(self.win, width=WIDTH, height=HEIGHT, bg="#010009")
        self.canvas.pack()

        # Movement flags
        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False
        self.shooting = False

        # Player
        self.player_x = WIDTH // 2
        self.player_y = 620
        self.player_speed = 8
        self.fire_rate = 200
        self.can_shoot = True

        self.player_body = self.canvas.create_polygon(
            self.player_x, self.player_y-25,     # top
            self.player_x-20, self.player_y+25,  # bottom-left
            self.player_x+20, self.player_y+25,  # bottom-right
            fill="#00eaff", outline="#00ffff", width=2
        )

        self.player_engine = self.canvas.create_oval(
            self.player_x-10, self.player_y+25,
            self.player_x+10, self.player_y+42,
            fill="#0077cc", outline=""
        )

        # Lists
        self.bullets = []
        self.enemies = []
        self.particles = []
        self.stars = []

        # Game stats
        self.level = 1
        self.score = 0
        self.enemy_speed = 3
        self.enemy_spawn_rate = 1200

        # Boss
        self.boss = None
        self.boss_active = False
        self.boss_health = 0

        self.game_over_flag = False

        self.create_starfield()

        # Controls
        self.win.bind("<KeyPress>", self.key_down)
        self.win.bind("<KeyRelease>", self.key_up)

        self.schedule_enemy()
        self.update()
        self.win.mainloop()

    # ================= CONTROLS ==================
    def key_down(self, e):
        if e.keysym in ("Left", "a", "A"): self.move_left = True
        if e.keysym in ("Right", "d", "D"): self.move_right = True
        if e.keysym in ("Up", "w", "W"): self.move_up = True
        if e.keysym in ("Down", "s", "S"): self.move_down = True
        if e.keysym == "space":
            self.shooting = True
            self.try_auto_shoot()

    def key_up(self, e):
        if e.keysym in ("Left", "a", "A"): self.move_left = False
        if e.keysym in ("Right", "d", "D"): self.move_right = False
        if e.keysym in ("Up", "w", "W"): self.move_up = False
        if e.keysym in ("Down", "s", "S"): self.move_down = False
        if e.keysym == "space": self.shooting = False

    # ================= SHOOTING ==================
    def try_auto_shoot(self):
        if self.shooting and self.can_shoot:
            self.shoot()
            self.can_shoot = False
            self.win.after(self.fire_rate, self.reset_fire)

    def shoot(self):
        b = self.canvas.create_rectangle(
            self.player_x - 3, self.player_y - 40,
            self.player_x + 3, self.player_y - 15,
            fill="yellow", outline=""
        )
        self.bullets.append(b)

    def reset_fire(self):
        self.can_shoot = True
        if self.shooting:
            self.try_auto_shoot()

    # ================= STARS ==================
    def create_starfield(self):
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            s = self.canvas.create_oval(x, y, x+size, y+size, fill="#637dff", outline="")
            self.stars.append(s)

    def update_stars(self):
        for s in self.stars:
            self.canvas.move(s, 0, 2)
            if self.canvas.coords(s)[1] > HEIGHT:
                self.canvas.move(s, 0, -HEIGHT)

    # ================= ENEMY SPAWN ==================
    def schedule_enemy(self):
        if not self.boss_active:
            self.spawn_enemy()
        self.win.after(self.enemy_spawn_rate, self.schedule_enemy)

    def spawn_enemy(self):
        x = random.randint(40, WIDTH-40)
        e = self.canvas.create_polygon(
            x, -15,
            x-22, 25,
            x+22, 25,
            fill="#ff3b3b", outline="#ff7f7f", width=2
        )
        self.enemies.append(e)

    # ================= BOSS ==================
    def spawn_boss(self):
        self.boss_active = True
        self.boss_health = 25

        self.boss = self.canvas.create_rectangle(
            200, 40, 400, 140,
            fill="#8e00ff", outline="#d580ff", width=4
        )

    # ================= EXPLOSION ==================
    def explode(self, x, y):
        for _ in range(25):
            self.particles.append(Particle(self.canvas, x, y, "orange", 6))

    # ================= MAIN LOOP ==================
    def update(self):
        if self.game_over_flag:
            return

        # MOVE PLAYER
        if self.move_left: self.player_x -= self.player_speed
        if self.move_right: self.player_x += self.player_speed
        if self.move_up: self.player_y -= self.player_speed
        if self.move_down: self.player_y += self.player_speed

        self.player_x = max(30, min(WIDTH-30, self.player_x))
        self.player_y = max(40, min(HEIGHT-40, self.player_y))

        # PERFECT CENTER CORRECTION 🔥
        body_coords = self.canvas.coords(self.player_body)
        cx = (body_coords[0] + body_coords[2] + body_coords[4]) / 3
        cy = (body_coords[1] + body_coords[3] + body_coords[5]) / 3

        dx = self.player_x - cx
        dy = self.player_y - cy

        self.canvas.move(self.player_body, dx, dy)
        self.canvas.move(self.player_engine, dx, dy)

        # ENGINE PARTICLES
        self.particles.append(Particle(self.canvas, self.player_x, self.player_y + 32, "#00aaff"))

        # BULLETS
        for b in self.bullets[:]:
            self.canvas.move(b, 0, -12)
            if self.canvas.coords(b)[1] < 0:
                self.canvas.delete(b)
                self.bullets.remove(b)

        # ENEMIES
        for e in self.enemies[:]:
            self.canvas.move(e, 0, self.enemy_speed)
            c = self.canvas.coords(e)
            ex = (c[0] + c[2] + c[4]) / 3
            ey = (c[1] + c[3] + c[5]) / 3

            if ey > HEIGHT:
                self.end_game()
                return

            for b in self.bullets[:]:
                bx1, by1, bx2, by2 = self.canvas.coords(b)
                if (bx1 < ex+25 and bx2 > ex-25 and by1 < ey+25 and by2 > ey-25):
                    self.explode(ex, ey)
                    self.canvas.delete(e)
                    self.canvas.delete(b)
                    self.enemies.remove(e)
                    self.bullets.remove(b)
                    self.score += 1

        # BOSS
        if self.score == 10 and not self.boss_active:
            self.spawn_boss()

        if self.boss_active and self.boss:
            bx1, by1, bx2, by2 = self.canvas.coords(self.boss)
            self.canvas.move(self.boss, random.choice([-2, -1, 1, 2]), 0)

            # bullet hits boss
            for b in self.bullets[:]:
                bx, by = self.canvas.coords(b)[0], self.canvas.coords(b)[1]
                if bx1 < bx < bx2 and by1 < by < by2:
                    self.canvas.delete(b)
                    self.bullets.remove(b)
                    self.boss_health -= 1

                    if self.boss_health <= 0:
                        self.explode((bx1+bx2)/2, (by1+by2)/2)
                        self.canvas.delete(self.boss)
                        self.boss = None
                        self.boss_active = False
                        self.level_up()
                        self.score += 1

        # PARTICLES
        newp = []
        for p in self.particles:
            if p.update(): newp.append(p)
            else: self.canvas.delete(p.id)
        self.particles = newp

        # STARS
        self.update_stars()

        # SCORE
        self.canvas.delete("score")
        self.canvas.create_text(
            70, 20,
            text=f"Score: {self.score}",
            fill="white",
            font=("Arial", 16),
            tag="score"
        )

        self.win.after(16, self.update)

    # ================= LEVEL ==================
    def level_up(self):
        self.level += 1
        self.enemy_speed += 1
        self.enemy_spawn_rate = max(400, self.enemy_spawn_rate - 150)

        self.canvas.create_text(
            WIDTH//2, HEIGHT//2,
            text=f"LEVEL {self.level}!",
            fill="#00ff7f",
            font=("Arial", 36, "bold"),
            tag="lvl"
        )
        self.win.after(1200, lambda: self.canvas.delete("lvl"))

    # ================= GAME OVER ==================
    def end_game(self):
        self.game_over_flag = True
        self.canvas.create_text(
            WIDTH//2, HEIGHT//2,
            text="GAME OVER",
            fill="red",
            font=("Arial", 40, "bold")
        )


Game()
