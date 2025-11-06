class EnemyInfo:
    def __init__(self, name, description, weak=None, resist=None, special_eff=None, slow_eff=None, occurrence=None):
        self.name = name
        self.description = description
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
        self.enemies = []  # List[EnemyInfo]
        self.map = []  # List of map points, e.g. [[x, y], ...]
        self.placement_options = []  # 可放置塔的位置 List[[x, y], ...]
        self.towers = []  # List[TowerInfo]
        self.coins = 0
        self.store = []  # 当前商店内容 List[dict]
        self.round = 0

    def debug_print(self):
        print(f"Round: {self.round}")
        print(f"Coins: {self.coins}")
        print(f"Map: {self.map}")
        print(f"Placement Options: {self.placement_options}")
        print(f"Store: {self.store}")
        print("Enemies:")
        for i, e in enumerate(self.enemies):
            print(f"  [{i}] Name: {e.name}")
            print(f"      Desc: {e.description}")
            print(f"      Weak: {e.weak}")
            print(f"      Resist: {e.resist}")
            print(f"      Special Eff: {e.special_eff}")
            print(f"      Slow Eff: {e.slow_eff}")
            print(f"      Occurrence: {e.occurrence}")
        print("Towers:")
        for i, t in enumerate(self.towers):
            print(f"  [{i}] Attributes: {t.attributes}")

    def get_tower_by_idx(self, idx):
        if 0 <= idx < len(self.towers):
            return self.towers[idx]
        return None

    def add_enemy(self, enemy: EnemyInfo):
        self.enemies.append(enemy)

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