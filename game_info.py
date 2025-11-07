class EnemyInfo:
    def __init__(self, name, description, weak=None, resist=None, special_eff=None, slow_eff=None, occurrence=None, best_atk_spd=None):
        self.name = name
        self.description = description
        self.best_atk_spd = best_atk_spd or []
        self.weak = weak or []
        self.resist = resist or []
        self.special_eff = special_eff or []
        self.slow_eff = slow_eff or []
        self.occurrence = occurrence or []

class TowerInfo:
    def __init__(self, attributes):
        self.attributes = attributes  # dict, e.g. {'type': 'Fire', 'range': 6, ...}

class GameInfo:
    def __init__(self):
        self.enemies = {}  # Dict[name, EnemyInfo]
        self.map = []  # List of map points, e.g. [[x, y], ...]
        self.placement_options = []  # 可放置塔的位置 List[[x, y], ...]
        self.towers = []  # List[TowerInfo]
        self.coins = 0
        self.store = []  # 当前商店内容 List[dict]
        self.round = 0

    def debug_print(self):
        print("\n\n\n")
        print("============= Game Info ==============")
        print(f"Round: {self.round}")
        print(f"Coins: {self.coins}")
        print(f"Map: {self.map}")
        print(f"Placement Options: {self.placement_options}")
        print(f"Store: {self.store}")
        print(f"Enemies(len = {len(self.enemies)}):")
        for i, (name, e) in enumerate(self.enemies.items()):
            print(f"  [{i}] Name: {name}")
            print(f"      Desc: {e.description}")
            print(f"      Best Atk Spd: {e.best_atk_spd}")
            print(f"      Weak: {e.weak}")
            print(f"      Resist: {e.resist}")
            print(f"      Special Eff: {e.special_eff}")
            print(f"      Slow Eff: {e.slow_eff}")
            print(f"      Occurrence: {e.occurrence}")
        print(f"Towers(len = {len(self.towers)}):")
        for i, t in enumerate(self.towers):
            print(f"  [{i}] Attributes: {t.attributes}")
        print("========== Game Info ends ==========\n\n\n")

    def get_tower_by_idx(self, idx):
        if 0 <= idx < len(self.towers):
            return self.towers[idx]
        return None

    def add_enemy(self, enemy: EnemyInfo):
        self.enemies[enemy.name] = enemy

    def update_enemy(self, name, best_atk_spd=None, weak=None, resist=None, special_eff=None, slow_eff=None, occurrence=None):
        assert name in self.enemies, f"Enemy {name} not found"
        enemy = self.enemies[name]
        if best_atk_spd is not None:
            enemy.best_atk_spd = best_atk_spd
        if weak is not None:
            enemy.weak = weak
        if resist is not None:
            enemy.resist = resist
        if special_eff is not None:
            enemy.special_eff = special_eff
        if slow_eff is not None:
            enemy.slow_eff = slow_eff
        if occurrence is not None:
            enemy.occurrence = occurrence

    def add_tower(self, tower: TowerInfo):
        self.towers.append(tower)

    def update_store(self, store_list):
        self.store = store_list

    def set_map(self, map_points):
        self.map = map_points

    def set_placement_options(self, options):
        self.placement_options = options

    def set_coins(self, coins):
        self.coins = coins

    def set_round(self, round_num):
        self.round = round_num