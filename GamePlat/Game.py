import pgzrun
from pygame import Rect
import math

# Configurações globais
WIDTH, HEIGHT = 800, 600
TITLE = "GamePlat"  # Nome do jogo na janela
FPS = 60
TILE_SIZE = 32
HERO_WIDTH, HERO_HEIGHT = 32, 32

# Estados do jogo
MENU, PLAYING, GAME_OVER, VICTORY, LEVEL_TRANSITION, LEVEL_SELECT = range(6)

# Cores
WHITE, BLACK, RED, GREEN, GRAY, LIGHT_BLUE = (
    (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 255, 0),
    (150, 150, 150), (173, 216, 230)
)

# Cores programáticas para plataformas
STATIC_PROGRAMMATIC_COLORS = {
    "chao_terra": (139, 69, 19),   
    "parede_tijolo": (178, 34, 34) 
}
MOVING_PROGRAMMATIC_COLORS = {
    "chao_terra": (101, 67, 33),   
    "parede_tijolo": (139, 0, 0)   
}


def tocar_musica_com_feedback(nome_da_faixa, volume=0.5):
    """Toca uma faixa de música com feedback no console."""
    global music_enabled
    if not music_enabled:
        # print(f"INFO: Música está desativada. Não tocará '{nome_da_faixa}'.") # Opcional: reativar para depuração
        return
    try:
        # print(f"INFO: Tentando tocar música: '{nome_da_faixa}'") # Opcional: reativar para depuração
        music.play(nome_da_faixa)
        music.set_volume(volume)
        # print(f"SUCESSO: Música '{nome_da_faixa}' tocando com volume {volume}.") # Opcional: reativar para depuração
    except Exception as e:
        print(f"!!! ERRO CRÍTICO ao tocar música '{nome_da_faixa}': {e}")


class Button:
    """Representa um botão clicável na interface."""

    def __init__(self, text, x, y, width, height,
                 level_num=None, action_tag=None):
        self.rect = Rect(x, y, width, height)
        self.text = text
        self.level_num, self.action_tag = level_num, action_tag
        self.color, self.disabled_color, self.hover_color = \
            WHITE, GRAY, (220, 220, 220)
        self.is_hovered = False
        self.font_size = 24

    def draw(self, unlocked=True):
        """Desenha o botão na tela."""
        color_to_draw = self.color
        if not unlocked:
            color_to_draw = self.disabled_color
        elif self.is_hovered:
            color_to_draw = self.hover_color

        screen.draw.filled_rect(self.rect, color_to_draw)
        screen.draw.text(
            self.text,
            center=self.rect.center,
            color=BLACK,
            fontsize=self.font_size
        )

    def update_hover(self, mouse_pos):
        """Atualiza o estado de hover do botão."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)


class Hero:
    """Representa o personagem principal do jogo."""

    def __init__(self, x, y):
        self.rect = Rect(x, y, HERO_WIDTH, HERO_HEIGHT)
        self.velocity = 0
        self.current_frame = 0
        self.animation_time = 0
        self.invincible_timer = 0
        self.jump_power = -15 # Força do pulo
        self.speed = 5 # Velocidade de movimento horizontal
        self.facing = 1  # 1 para direita, -1 para esquerda
        self.on_ground = False # Está no chão?
        self.invincible = False # Está invencível?
        # Contagem de frames para cada animação
        self.animation_frames = {"idle": 4, "run": 6, "jump": 4}
        self.state = "idle" # Estado inicial
        self.health = 3 # Vida inicial

    def update(self, platforms, goal):
        """Atualiza a lógica do herói (movimento, física, colisão)."""
        global game_state
        if self.invincible: # Temporizador de invencibilidade
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        dx = 0 # Deslocamento horizontal
        previous_state = self.state # Para detectar mudança de estado e resetar animação

        # Movimento horizontal e definição de estado (run/idle)
        if keyboard.left:
            self.facing, dx = -1, -self.speed
            if self.on_ground:
                self.state = "run"
        elif keyboard.right:
            self.facing, dx = 1, self.speed
            if self.on_ground:
                self.state = "run"
        else: # Sem input horizontal
            if self.on_ground:
                self.state = "idle"

        # Reseta animação se o estado mudou enquanto no chão
        if self.state != previous_state and self.on_ground:
            self.current_frame, self.animation_time = 0, 0

        self.update_animation() # Atualiza o frame da animação
        self.rect.x += dx # Aplica movimento X

        # Física Vertical (Gravidade)
        self.velocity = min(self.velocity + 0.6, 10) # Aplica gravidade, limita velocidade de queda
        self.rect.y += self.velocity # Aplica movimento Y

        previous_on_ground = self.on_ground # Guarda se estava no chão antes das colisões
        self.on_ground = False # Assume que está no ar até colidir

        # Colisão com plataformas
        for p in platforms:
            if self.rect.colliderect(p.rect):
                is_falling_on_top = (
                    self.velocity > 0 and
                    self.rect.bottom > p.rect.top and
                    self.rect.top < p.rect.top # Verifica se o herói está acima da plataforma antes da colisão vertical
                )
                is_hitting_head = (
                    self.velocity < 0 and
                    self.rect.top < p.rect.bottom and
                    self.rect.bottom > p.rect.bottom # Verifica se o herói está abaixo
                )

                if is_falling_on_top: # Se está caindo sobre uma plataforma
                    self.rect.bottom = p.rect.top # Ajusta posição para o topo da plataforma
                    self.velocity = 0 # Para a queda
                    self.on_ground = True # Marca que está no chão
                    if not previous_on_ground: # Se acabou de aterrissar
                        self.state = "run" if keyboard.left or keyboard.right \
                                     else "idle" # Define estado baseado no input
                        self.current_frame, self.animation_time = 0, 0 # Reseta animação
                elif is_hitting_head: # Se está batendo a cabeça
                    self.rect.top = p.rect.bottom # Ajusta posição
                    self.velocity = 0 # Para o movimento para cima
                
                # Se estiver em uma plataforma móvel e no chão, acompanha o movimento dela
                if isinstance(p, MovingPlatform) and self.on_ground:
                    self.rect.x += p.speed * p.direction
        
        # Define estado de pulo se estiver no ar
        if not self.on_ground and self.state != "jump":
            self.state, self.current_frame, self.animation_time = "jump", 0, 0
        # Se estava pulando e aterrisou sem input de movimento, volta para idle
        elif self.on_ground and self.state == "jump" and \
                not (keyboard.left or keyboard.right):
            self.state, self.current_frame, self.animation_time = "idle", 0, 0

        # Verifica se alcançou o objetivo
        return self.rect.colliderect(goal.rect) and goal.active

    def jump(self):
        """Faz o herói pular se estiver no chão."""
        if self.on_ground:
            self.velocity = self.jump_power # Define velocidade vertical para o pulo
            self.on_ground = False # Marca que não está mais no chão
            if self.state != "jump": # Garante que a animação de pulo comece
                self.state, self.current_frame, self.animation_time = \
                    "jump", 0, 0
            if sounds_enabled:
                try:
                    sounds.jump.play()
                except Exception as e:
                    print(f"ERRO som pulo: {e}")

    def take_damage(self):
        """Processa o herói tomando dano."""
        global game_state
        if self.invincible or self.health <= 0: # Não toma dano se já invencível ou morto
            return
        self.health -= 1
        self.invincible, self.invincible_timer = True, FPS * 2 # Ativa invencibilidade
        if self.health <= 0: # Se a vida acabou
            game_state = GAME_OVER
            if sounds_enabled:
                try: 
                    sounds.gameover.play()
                except Exception as e:
                    print(f"ERRO som gameover: {e}")
        elif sounds_enabled: # Se ainda tem vida, toca som de dano
            try: 
                sounds.hurt.play()
            except Exception as e:
                print(f"ERRO som dano: {e}")

    def update_animation(self):
        """Atualiza o frame da animação do herói baseado no estado."""
        self.animation_time += 1
        frame_count = self.animation_frames.get(self.state, 1) # Número de frames para o estado atual
        animation_speed = 7 if self.state == "run" else 10 # Velocidade da animação
        if self.animation_time >= animation_speed:
            self.current_frame = (self.current_frame + 1) % frame_count # Próximo frame
            self.animation_time = 0 # Reseta contador

    def draw(self):
        """Desenha o herói na tela."""
        if self.invincible and (self.invincible_timer // (FPS // 10)) % 2 == 0: # Efeito de piscar
            return
        frame_image_name = f"hero/{self.state}_{self.current_frame}"
        try:
            screen.blit(frame_image_name, self.rect.topleft)
        except Exception as e: # Fallback se a imagem não for encontrada
            print(f"!!! ERRO frame herói '{frame_image_name}': {e}")
            screen.draw.filled_rect(self.rect, RED)


class Enemy:
    """Representa um inimigo no jogo."""

    def __init__(self, x, y, patrol_range, enemy_type):
        self.rect = Rect(x, y, 32, 32) # Hitbox do inimigo
        self.patrol_start_x, self.patrol_range, self.type = \
            x, patrol_range, enemy_type
        self.animation_data = { # Dados específicos de cada tipo de inimigo
            'zombie': {'frames': 2, 'speed': 1, 'height': 32},
            'bat': {'frames': 3, 'speed': 2, 'height': 32}, # Morcego pode ter comportamento aéreo
            'ice': {'frames': 2, 'speed': 1.5, 'height': 32}
        }
        self.rect.height = self.animation_data[self.type].get('height', 32) # Ajusta altura
        self.speed = self.animation_data[self.type]['speed']
        self.direction = -1 # Direção inicial (geralmente para a esquerda)
        self.current_frame = 0
        self.animation_time = 0
        self.float_time = 0 # Usado para movimento vertical do morcego
        self.alive = True # Estado do inimigo

    def take_damage(self):
        """Marca o inimigo como derrotado."""
        if self.alive:
            self.alive = False
            if sounds_enabled:
                try: 
                    sounds.enemy_death.play()
                except Exception as e:
                    print(f"ERRO som morte inimigo: {e}")

    def update(self):
        """Atualiza a lógica do inimigo (movimento, animação)."""
        if not self.alive:
            return
        
        # Movimento específico para o morcego (flutuação)
        if self.type == 'bat':
            self.float_time += 0.1
            self.rect.y += math.sin(self.float_time) * 0.5
        
        # Movimento de patrulha horizontal para todos os inimigos
        self.rect.x += self.speed * self.direction
        if self.rect.left <= self.patrol_range[0]: # Atingiu limite esquerdo
            self.rect.left, self.direction = self.patrol_range[0], 1 # Vira para direita
        elif self.rect.right >= self.patrol_range[1]: # Atingiu limite direito
            self.rect.right, self.direction = self.patrol_range[1], -1 # Vira para esquerda

        # Atualiza animação
        self.animation_time += 1
        if self.animation_time >= 15:  # Velocidade da animação do inimigo
            self.current_frame = \
                (self.current_frame + 1) % self.animation_data[self.type]['frames']
            self.animation_time = 0

    def draw(self):
        """Desenha o inimigo na tela."""
        if self.alive:
            frame_image_name = f"enemies/{self.type}_{self.current_frame}"
            try:
                screen.blit(frame_image_name, self.rect.topleft)
            except Exception as e: # Fallback se imagem não encontrada
                print(f"!!! ERRO frame inimigo '{frame_image_name}': {e}")
                screen.draw.filled_rect(self.rect, GREEN)


class Platform:
    """Representa uma plataforma (chão, parede, etc.)."""

    def __init__(self, x, y, width, height, texture_name="platform_default"):
        self.rect = Rect(x, y, width, height)
        self.texture_name = texture_name # Nome base da textura (ex: "chao_terra")

    def draw(self):
        """Desenha a plataforma, usando cor sólida ou tiles de textura."""
        # Se a textura for uma das que devem ser desenhadas com cor programática
        if self.texture_name in STATIC_PROGRAMMATIC_COLORS:
            color = STATIC_PROGRAMMATIC_COLORS[self.texture_name]
            screen.draw.filled_rect(self.rect, color)
        else: # Caso contrário, tenta desenhar com tiles de imagem
            num_tiles_x = math.ceil(self.rect.width / TILE_SIZE)
            num_tiles_y = math.ceil(self.rect.height / TILE_SIZE)

            for j_idx in range(num_tiles_y): # Itera pelas linhas de tiles
                for i_idx in range(num_tiles_x): # Itera pelas colunas de tiles
                    tile_x = self.rect.x + i_idx * TILE_SIZE
                    tile_y = self.rect.y + j_idx * TILE_SIZE
                    try:
                        # Tenta desenhar o tile da textura (ex: "images/tiles/plataforma_pedra.png")
                        screen.blit(f"tiles/{self.texture_name}", (tile_x, tile_y))
                    except Exception: # Fallback se a imagem do tile não for encontrada
                        # Calcula a área visível do tile para não desenhar fora da plataforma
                        drawable_width = min(TILE_SIZE, self.rect.right - tile_x)
                        drawable_height = min(TILE_SIZE, self.rect.bottom - tile_y)
                        if drawable_width > 0 and drawable_height > 0:
                            screen.draw.filled_rect(
                                Rect(tile_x, tile_y, drawable_width, drawable_height),
                                GRAY # Cor de fallback para tiles não encontrados
                            )


class MovingPlatform(Platform):
    """Representa uma plataforma que se move horizontal ou verticalmente."""

    def __init__(self, x, y, width, height, move_range_value, speed,
                 vertical=False, texture_name="platform_moving_default"):
        super().__init__(x, y, width, height, texture_name) # Chama construtor da classe pai
        self.move_range_value = move_range_value # Distância do movimento
        self.speed = speed # Velocidade do movimento
        self.vertical = vertical # True se o movimento for vertical
        self.original_x, self.original_y = x, y # Posições originais para cálculo do range
        self.direction = 1 # Direção inicial do movimento (1 ou -1)

    def update(self):
        """Atualiza a posição da plataforma móvel."""
        if self.vertical: # Movimento vertical
            self.rect.y += self.speed * self.direction
            # Verifica se atingiu os limites do movimento vertical
            if (self.direction == 1 and
                    self.rect.y >= self.original_y + self.move_range_value):
                self.rect.y = self.original_y + self.move_range_value # Ajusta para o limite
                self.direction = -1 # Inverte direção
            elif self.direction == -1 and self.rect.y <= self.original_y:
                self.rect.y = self.original_y # Ajusta para o limite
                self.direction = 1 # Inverte direção
        else: # Movimento horizontal
            self.rect.x += self.speed * self.direction
            # Verifica se atingiu os limites do movimento horizontal
            if (self.direction == 1 and
                    self.rect.x >= self.original_x + self.move_range_value):
                self.rect.x = self.original_x + self.move_range_value
                self.direction = -1
            elif self.direction == -1 and self.rect.x <= self.original_x:
                self.rect.x = self.original_x
                self.direction = 1

    def draw(self):
        """Desenha a plataforma móvel, com cores programáticas específicas se aplicável."""
        # Se a textura for uma das que têm cor programática para plataformas MÓVEIS
        if self.texture_name in MOVING_PROGRAMMATIC_COLORS:
            color = MOVING_PROGRAMMATIC_COLORS[self.texture_name]
            screen.draw.filled_rect(self.rect, color)
        # Senão, se for uma cor programática ESTÁTICA (fallback para móveis)
        elif self.texture_name in STATIC_PROGRAMMATIC_COLORS:
            color = STATIC_PROGRAMMATIC_COLORS[self.texture_name]
            screen.draw.filled_rect(self.rect, color)
        else: # Senão, usa a lógica de tiling da classe Platform (pai)
            super().draw()


class Goal:
    """Representa o objetivo (bandeira) do nível."""

    def __init__(self, x, y):
        self.rect = Rect(x, y, 32, 64)  # Hitbox do objetivo
        self.active = True # Objetivo está ativo?
        self.animation_frame, self.animation_time = 0, 0 # Para animação da bandeira

    def update(self):
        """Atualiza a animação do objetivo."""
        if self.active:
            self.animation_time += 1
            if self.animation_time >= 15:  # Velocidade da animação
                self.animation_frame = (self.animation_frame + 1) % 2 # Alterna entre 2 frames
                self.animation_time = 0

    def draw(self):
        """Desenha o objetivo na tela."""
        if self.active:
            try:
                # Assume imagens "flags/flag_0.png" e "flags/flag_1.png"
                screen.blit(f"flags/flag_{self.animation_frame}", self.rect.topleft)
            except Exception: # Fallback se imagem da bandeira não encontrada
                screen.draw.filled_rect(self.rect, GREEN)


class LevelSelector:
    """Gerencia a tela de seleção de níveis."""

    def __init__(self):
        self.buttons = [ # Botões para cada fase
            Button("Fase 1", WIDTH // 2 - 100, 200, 200, 50, level_num=0),
            Button("Fase 2", WIDTH // 2 - 100, 280, 200, 50, level_num=1),
            Button("Fase 3", WIDTH // 2 - 100, 360, 200, 50, level_num=2)
        ]
        self.unlocked_levels = [0] # Fase 1 (índice 0) sempre desbloqueada

    def update_unlocked(self, last_completed_level_index):
        """Desbloqueia o próximo nível após completar o anterior."""
        next_level_idx = last_completed_level_index + 1
        if (next_level_idx < len(LEVELS) and
                next_level_idx not in self.unlocked_levels):
            self.unlocked_levels.append(next_level_idx)

    def draw(self):
        """Desenha a tela de seleção de níveis."""
        screen.fill(BLACK) # Fundo preto
        screen.draw.text(
            "Selecione a Fase",
            center=(WIDTH // 2, 100), fontsize=40, color=WHITE
        )
        for btn in self.buttons: # Desenha cada botão
            if btn.level_num is not None: # Garante que é um botão de nível
                # Desenha o botão com cor normal ou desabilitada
                btn.draw(unlocked=(btn.level_num in self.unlocked_levels))

    def update_buttons_hover(self, mouse_pos):
        """Atualiza o estado de hover dos botões de seleção."""
        for btn in self.buttons:
            btn.update_hover(mouse_pos)


# Definição dos Níveis (com plataformas aéreas menores e design mais elaborado)
LEVELS = [
    {   # Fase 1
        "background": "backgrounds/level1_bg",
        "platforms": [
            (0, HEIGHT - TILE_SIZE, 8 * TILE_SIZE, TILE_SIZE, "chao_terra", "static"),
            (9 * TILE_SIZE, HEIGHT - TILE_SIZE, 8 * TILE_SIZE, TILE_SIZE, "chao_terra", "static"),
            (2 * TILE_SIZE, HEIGHT - 4 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (6 * TILE_SIZE, HEIGHT - 7 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (10 * TILE_SIZE, HEIGHT - 7 * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE, "plataforma_metal", "moving_h", 3 * TILE_SIZE, 1),
            (18 * TILE_SIZE, HEIGHT - 9 * TILE_SIZE, 4 * TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
            (17 * TILE_SIZE, HEIGHT - 4 * TILE_SIZE, TILE_SIZE, 5 * TILE_SIZE, "parede_tijolo", "static"),
        ],
        "enemies": [
            (5 * TILE_SIZE, HEIGHT - TILE_SIZE - 32, (4 * TILE_SIZE, 7 * TILE_SIZE), "zombie"),
            (11 * TILE_SIZE, HEIGHT - TILE_SIZE - 32, (10 * TILE_SIZE, 15 * TILE_SIZE), "ice"),
            (7 * TILE_SIZE, HEIGHT - 10 * TILE_SIZE, (6 * TILE_SIZE, 8 * TILE_SIZE), "bat"),
            (20 * TILE_SIZE, HEIGHT - 9 * TILE_SIZE - 32, (19 * TILE_SIZE, 22 * TILE_SIZE), "zombie"),
        ],
        "start_pos": (TILE_SIZE, HEIGHT - TILE_SIZE - HERO_HEIGHT),
        "goal": ((18 * TILE_SIZE) + (4 * TILE_SIZE // 2) - (32 // 2), HEIGHT - 9 * TILE_SIZE - 64)
    },
    {   # Fase 2
        "background": "backgrounds/level2_bg",
        "platforms": [
            (0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE, "chao_terra", "static"),
            (2 * TILE_SIZE, HEIGHT - 5 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
            (5 * TILE_SIZE, HEIGHT - 8 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
            (TILE_SIZE, HEIGHT - 11 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
            (8 * TILE_SIZE, HEIGHT - 12 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_metal", "moving_v", 4 * TILE_SIZE, 1.5),
            (12 * TILE_SIZE, HEIGHT - 8 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_metal", "moving_v", 3 * TILE_SIZE, 1),
            (16 * TILE_SIZE, HEIGHT - 10 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (18 * TILE_SIZE, HEIGHT - 12 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (20 * TILE_SIZE, HEIGHT - 14 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (WIDTH - 3 * TILE_SIZE, HEIGHT - 10 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
        ],
        "enemies": [
            (2 * TILE_SIZE + (TILE_SIZE // 2) - 16, HEIGHT - 5 * TILE_SIZE - 32, (2 * TILE_SIZE, 3 * TILE_SIZE), "ice"),
            (5 * TILE_SIZE + (TILE_SIZE // 2) - 16, HEIGHT - 8 * TILE_SIZE - 32, (5 * TILE_SIZE, 6 * TILE_SIZE), "zombie"),
            (10 * TILE_SIZE, HEIGHT - 15 * TILE_SIZE, (8 * TILE_SIZE, 14 * TILE_SIZE), "bat"),
            (17 * TILE_SIZE, HEIGHT - 6 * TILE_SIZE, (16 * TILE_SIZE, 20 * TILE_SIZE), "bat"),
        ],
        "start_pos": (TILE_SIZE, HEIGHT - TILE_SIZE - HERO_HEIGHT),
        "goal": (20 * TILE_SIZE, HEIGHT - 14 * TILE_SIZE - 64)
    },
    {   # Fase 3
        "background": "backgrounds/level3_bg",
        "platforms": [
            (TILE_SIZE, HEIGHT - 3 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
            (0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE, "chao_terra", "static"),
            (6 * TILE_SIZE, HEIGHT - 8 * TILE_SIZE, TILE_SIZE, 7 * TILE_SIZE, "parede_tijolo", "static"),
            (12 * TILE_SIZE, HEIGHT - 6 * TILE_SIZE, TILE_SIZE, 5 * TILE_SIZE, "parede_tijolo", "static"),
            (18 * TILE_SIZE, HEIGHT - 10 * TILE_SIZE, TILE_SIZE, 9 * TILE_SIZE, "parede_tijolo", "static"),
            (7 * TILE_SIZE, HEIGHT - 4 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (3 * TILE_SIZE, HEIGHT - 6 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (9 * TILE_SIZE, HEIGHT - 8 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_madeira", "static"),
            (14 * TILE_SIZE, HEIGHT - 3 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_metal", "moving_h", 2 * TILE_SIZE, 2),
            (13 * TILE_SIZE, HEIGHT - 10 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
            (20 * TILE_SIZE, HEIGHT - 12 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, "plataforma_metal", "moving_v", 4 * TILE_SIZE, 1),
            (WIDTH - 2 * TILE_SIZE, HEIGHT - 15 * TILE_SIZE, TILE_SIZE, TILE_SIZE, "plataforma_pedra", "static"),
        ],
        "enemies": [
            (TILE_SIZE, HEIGHT - TILE_SIZE - 32, (0, 5 * TILE_SIZE), "ice"),
            (8 * TILE_SIZE, HEIGHT - TILE_SIZE - 32, (7 * TILE_SIZE, 11 * TILE_SIZE), "zombie"),
            (15 * TILE_SIZE, HEIGHT - TILE_SIZE - 32, (13 * TILE_SIZE, 17 * TILE_SIZE), "ice"),
            (4 * TILE_SIZE, HEIGHT - 9 * TILE_SIZE, (3 * TILE_SIZE, 5 * TILE_SIZE), "bat"),
            (10 * TILE_SIZE, HEIGHT - 11 * TILE_SIZE, (9 * TILE_SIZE, 11 * TILE_SIZE), "bat"),
            (14 * TILE_SIZE, HEIGHT - 6 * TILE_SIZE, (13 * TILE_SIZE, 15 * TILE_SIZE), "zombie"),
            (22 * TILE_SIZE, HEIGHT - 8 * TILE_SIZE, (20 * TILE_SIZE, WIDTH - TILE_SIZE), "bat"),
        ],
        "start_pos": (1.5 * TILE_SIZE, HEIGHT - 3 * TILE_SIZE - HERO_HEIGHT), # Ajuste para caber na plataforma
        "goal": (WIDTH - 2 * TILE_SIZE + (TILE_SIZE // 2) - (32 // 2), HEIGHT - 15 * TILE_SIZE - 64)
    }
]

# Variáveis Globais do Jogo
game_state = MENU
sounds_enabled, music_enabled = True, True
current_level_index, transition_timer = 0, 0
level_selector_obj = LevelSelector()
hero, enemies, platforms, goal = None, [], [], None
background_image_name, menu_background_image = None, "backgrounds/menu_bg"
menu_buttons, mouse_pos_global = [], (0, 0)


def setup_main_menu():
    """Configura os botões do menu principal."""
    global menu_buttons
    menu_buttons.clear()
    btn_w, btn_h = 280, 50
    start_x, start_y = WIDTH // 2 - btn_w // 2, HEIGHT // 2 - 100
    menu_buttons.extend([
        Button("Começar Jogo", start_x, start_y, btn_w, btn_h, action_tag="start_game"),
        Button(f"Música: {'LIGADA' if music_enabled else 'DESLIGADA'}",
               start_x, start_y + 70, btn_w, btn_h, action_tag="toggle_music"),
        Button(f"Sons: {'LIGADOS' if sounds_enabled else 'DESLIGADOS'}",
               start_x, start_y + 140, btn_w, btn_h, action_tag="toggle_sounds"),
        Button("Sair do Jogo", start_x, start_y + 210, btn_w, btn_h, action_tag="exit_game")
    ])
    if game_state == MENU:
        tocar_musica_com_feedback("menu_theme", volume=0.8) # Volume da música do menu aumentado


def start_level(level_idx):
    """Inicia um nível específico, carregando seus dados."""
    global current_level_index, hero, enemies, platforms, goal
    global background_image_name, game_state

    if level_idx >= len(LEVELS): # Se passou do último nível, jogador venceu
        game_state = VICTORY
        if music_enabled:
            music.stop()
        if sounds_enabled:
            try:
                sounds.victory.play()
            except Exception: # Captura erro de som de vitória
                print("AVISO: Som de vitória não encontrado.")
        return

    current_level_index, level_data = level_idx, LEVELS[level_idx] # Define nível atual
    background_image_name = level_data["background"]
    hero = Hero(*level_data["start_pos"]) # Cria herói
    goal = Goal(*level_data["goal"]) # Cria objetivo

    platforms.clear() # Limpa plataformas do nível anterior
    enemies.clear() # Limpa inimigos do nível anterior

    # Cria plataformas do nível
    for p_data in level_data["platforms"]:
        x, y, w, h, tex, p_type = p_data[:6] # Desempacota dados da plataforma
        if p_type in ("moving_h", "moving_v"): # Se for plataforma móvel
            mr, spd = p_data[6], p_data[7] # Pega range e velocidade
            platforms.append(
                MovingPlatform(x, y, w, h, mr, spd,
                               vertical=(p_type == "moving_v"),
                               texture_name=tex)
            )
        else: # Plataforma estática
            platforms.append(Platform(x, y, w, h, texture_name=tex))

    # Cria inimigos do nível
    for e_data in level_data["enemies"]:
        enemies.append(Enemy(*e_data)) # Desempacota dados do inimigo

    game_state = PLAYING # Define estado do jogo como "jogando"
    if music_enabled:
        tocar_musica_com_feedback("background", volume=0.5) # Toca música de fundo do nível


def update(dt):
    """Função de atualização principal do jogo, chamada a cada frame."""
    global game_state, current_level_index, transition_timer

    if game_state == MENU:
        for btn in menu_buttons: # Atualiza hover dos botões do menu
            btn.update_hover(mouse_pos_global)
    elif game_state == LEVEL_SELECT:
        level_selector_obj.update_buttons_hover(mouse_pos_global) # Hover da seleção de nível
    elif game_state == PLAYING:
        if hero: # Atualiza herói se existir
            if hero.update(platforms, goal) and game_state == PLAYING: # Se herói alcançou objetivo
                game_state, transition_timer = LEVEL_TRANSITION, FPS * 2 # Inicia transição
                if music_enabled:
                    music.fadeout(1) # Música some gradualmente
                if sounds_enabled:
                    try:
                        sounds.level_complete.play()
                    except Exception: # Captura erro de som de nível completo
                        print("AVISO: Som nível completo com erro.")
            if hero.rect.top > HEIGHT + 100: # Se herói caiu da tela
                hero.health = 0
                hero.take_damage()

            # Colisão herói com inimigos
            for enemy in enemies:
                if (enemy.alive and hero.rect.colliderect(enemy.rect) and
                        not hero.invincible):
                    # Se herói caindo sobre o inimigo
                    if (hero.velocity > 0 and
                            hero.rect.bottom < enemy.rect.centery + 5): # Pequena margem
                        enemy.take_damage() # Inimigo morre
                        hero.velocity = hero.jump_power * 0.6 # Pequeno impulso para cima
                        hero.on_ground = False # Garante que não está mais no chão
                    else: # Colisão lateral ou por baixo
                        hero.take_damage() # Herói toma dano
        if goal: # Atualiza objetivo (animação)
            goal.update()
        # Atualiza plataformas móveis e inimigos vivos
        for item in platforms + enemies:
            if isinstance(item, MovingPlatform) or \
               (isinstance(item, Enemy) and item.alive):
                item.update()
        if hero and hero.health <= 0 and game_state != GAME_OVER: # Se vida do herói acabou
            game_state = GAME_OVER
            if music_enabled:
                music.fadeout(1)
    elif game_state == LEVEL_TRANSITION: # Tela de transição entre níveis
        transition_timer -= 1
        if transition_timer <= 0:
            level_selector_obj.update_unlocked(current_level_index) # Desbloqueia próximo
            current_level_index += 1 # Avança para o próximo nível
            start_level(current_level_index) # Inicia


def draw_playing_state():
    """Desenha os elementos da tela de jogo (estado PLAYING)."""
    try:
        screen.blit(background_image_name or "", (0, 0)) # "" para evitar erro se None
    except Exception:
        screen.fill(BLACK)

    # Ordem de desenho: plataformas, inimigos, objetivo, herói
    for item in platforms:
        item.draw()
    for enemy_item in enemies:
        if enemy_item.alive:
            enemy_item.draw()
    if goal:
        goal.draw()
    if hero:
        hero.draw()

    if hero: # Desenha HUD de vida
        screen.draw.text(
            f"Vida: {hero.health}", (10, 10),
            fontsize=30, color=WHITE, owidth=1, ocolor=BLACK
        )


def draw():
    """Função principal para desenhar tudo na tela, chamada a cada frame."""
    if game_state == MENU:
        try:
            screen.blit(menu_background_image, (0, 0))
        except Exception: # Fallback se imagem do menu não carregar
            screen.fill(LIGHT_BLUE)
        screen.draw.text(
            "GamePlat", center=(WIDTH // 2, HEIGHT // 4),
            fontsize=60, color=WHITE, owidth=1.5, ocolor=BLACK
        )
        for btn in menu_buttons:
            btn.draw()
    elif game_state == PLAYING:
        draw_playing_state() # Chama função separada para desenhar o jogo
    elif game_state == LEVEL_TRANSITION:
        screen.fill(BLACK)
        screen.draw.text(
            f"Fase {current_level_index + 1} Concluída!",
            center=(WIDTH // 2, HEIGHT // 2 - 30), fontsize=40, color=GREEN
        )
        next_level_text = (f"Próxima fase: {current_level_index + 2}"
                           if current_level_index + 1 < len(LEVELS)
                           else "Você zerou o jogo!")
        screen.draw.text(
            next_level_text, center=(WIDTH // 2, HEIGHT // 2 + 30),
            fontsize=30, color=WHITE
        )
    elif game_state == GAME_OVER:
        screen.fill(BLACK)
        screen.draw.text(
            "Game Over!", center=(WIDTH // 2, HEIGHT // 2 - 30),
            fontsize=60, color=RED
        )
        screen.draw.text(
            "Pressione R para reiniciar a fase",
            center=(WIDTH // 2, HEIGHT // 2 + 30), fontsize=30, color=WHITE
        )
        screen.draw.text(
            "Pressione M para voltar ao Menu",
            center=(WIDTH // 2, HEIGHT // 2 + 70), fontsize=30, color=WHITE
        )
    elif game_state == VICTORY:
        screen.fill(BLACK)
        screen.draw.text(
            "Vitória!", center=(WIDTH // 2, HEIGHT // 2 - 30),
            fontsize=60, color=GREEN
        )
        screen.draw.text(
            "Você completou todas as fases!",
            center=(WIDTH // 2, HEIGHT // 2 + 40), fontsize=30, color=WHITE
        )
        screen.draw.text(
            "Pressione M para voltar ao Menu",
            center=(WIDTH // 2, HEIGHT // 2 + 80), fontsize=30, color=WHITE
        )
    elif game_state == LEVEL_SELECT:
        level_selector_obj.draw()


def on_key_down(key):
    """Lida com eventos de teclas pressionadas."""
    global game_state, current_level_index

    if game_state == PLAYING and hero and (key == keys.SPACE or key == keys.UP):
        hero.jump() # Pulo
    elif game_state == GAME_OVER:
        if key == keys.R: # Reiniciar
            start_level(current_level_index)
        elif key == keys.M: # Voltar ao Menu
            game_state = MENU
            setup_main_menu()
    elif game_state == VICTORY and key == keys.M: # Voltar ao Menu
        game_state = MENU
        setup_main_menu()
    elif game_state == LEVEL_SELECT and key == keys.ESCAPE: # Voltar ao Menu da Seleção
        game_state = MENU
        setup_main_menu()


def on_mouse_down(pos, button): # Nome do parâmetro 'button' é o esperado pelo Pygame Zero
    """Lida com eventos de clique do mouse."""
    global game_state, music_enabled, sounds_enabled

    if game_state == MENU: # Interação com botões do menu principal
        for btn in menu_buttons:
            if btn.rect.collidepoint(pos): # Se o clique foi em um botão
                if btn.action_tag == "start_game":
                    game_state = LEVEL_SELECT
                    if music_enabled:
                        music.stop() # Para música do menu
                elif btn.action_tag == "toggle_music":
                    music_enabled = not music_enabled # Alterna
                    btn.text = f"Música: {'LIGADA' if music_enabled else 'DESLIGADA'}"
                    if music_enabled:
                        tocar_musica_com_feedback("menu_theme", volume=0.8)
                    else:
                        music.stop()
                elif btn.action_tag == "toggle_sounds":
                    sounds_enabled = not sounds_enabled # Alterna
                    btn.text = f"Sons: {'LIGADOS' if sounds_enabled else 'DESLIGADOS'}"
                elif btn.action_tag == "exit_game":
                    quit() # Fecha o jogo
                break  # Processa apenas um clique de botão por vez
    elif game_state == LEVEL_SELECT: # Interação com botões da seleção de nível
        for btn in level_selector_obj.buttons:
            if (btn.rect.collidepoint(pos) and
                    btn.level_num in level_selector_obj.unlocked_levels):
                if music_enabled:
                    music.stop() # Para música do menu, se estiver tocando
                start_level(btn.level_num) # Inicia o nível selecionado
                break


def on_mouse_move(pos):
    """Lida com eventos de movimento do mouse (para efeito de hover)."""
    global mouse_pos_global
    mouse_pos_global = pos


# Inicialização do Jogo
setup_main_menu() # Configura o menu ao iniciar
pgzrun.go() # Inicia o loop principal do Pygame Zero