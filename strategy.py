from game_info import EnemyInfo, TowerInfo, GameInfo
from math import sqrt
from visualize import visualize_map_and_points
PRE_REFRESH = 3
EXPECT_THRESHOLD = 0.3
SEG_DIST = 0.1
# DEBUG_FILE = open('debug.log', 'w')

# --- Point class for discrete map points ---
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

# --- RangeCoverageTable: 预处理每个放置点和射程的路径点覆盖 ---
class RangeCoverageTable:
    def __init__(self, placement_options, points: list[Point], max_radius=20):
        # contribs[pos_idx][radius] = list of point indices
        self.placement_options = placement_options
        self.max_radius = max_radius
        self.contribs = [{} for _ in range(len(placement_options))]
        for idx, pos in enumerate(placement_options):
            px, py = pos
            for r in range(0, max_radius + 1):
                r2 = r * r
                indices = [i for i, pt in enumerate(points) if (pt.x - px) ** 2 + (pt.y - py) ** 2 <= r2]
                self.contribs[idx][r] = indices

    def get_coverage(self, pos_idx, radius):
        r = int(radius)
        return self.contribs[pos_idx].get(r, [])
    
# --- Geometry class for computational geometry operations ---
class Geometry:
    def __init__(self, game_info: GameInfo):
        self.game_info = game_info
        self.map = game_info.map
        self.points: list[Point] = []  # List[Point]
        step = SEG_DIST
        total_len = 0.0
        segs = []
        # 预先计算每段长度和累积长度
        for i in range(len(self.map) - 1):
            p1 = self.map[i]
            p2 = self.map[i + 1]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            seg_len = sqrt(dx ** 2 + dy ** 2)
            segs.append((p1, p2, seg_len))
            total_len += seg_len

        pos = step / 2
        curr_seg = 0
        curr_seg_start = 0.0
        while pos < total_len + 1e-8:
            # 找到pos落在哪一段
            while curr_seg < len(segs) and pos > curr_seg_start + segs[curr_seg][2]:
                curr_seg_start += segs[curr_seg][2]
                curr_seg += 1
            if curr_seg >= len(segs):
                break
            p1, p2, seg_len = segs[curr_seg]
            t = (pos - curr_seg_start) / seg_len
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            self.points.append(Point(x, y))
            pos += step
        # 最后一段结尾不足step直接忽略  
        visualize_map_and_points(self.map, self.points, 'saved_map_points.png')
        # 预处理每个placement_option和0-20所有整数射程的点贡献
        self.range_table = RangeCoverageTable(game_info.placement_options, self.points, max_radius=20)

    def sum_segments_in_circle(self, pos_idx, radius):
        # 获取覆盖点下标list
        indices = self.range_table.get_coverage(pos_idx, radius)
        return len(indices) * SEG_DIST
    
class Strategy:
    def __init__(self, game_info: GameInfo):
        self.refreshed = False
        self.refresh_times = 0
        self.edamages = []
        self.geometry = Geometry(game_info)

    def get_edamages(self, atk, tower: TowerInfo, game: GameInfo):
        mul = atk
        if 'speedDown' in tower.attributes:
            mul /= tower.attributes['speedDown']
        mul /= tower.attributes['interval']

        res = []
        for idx, t in enumerate(game.placed_towers):
            if t:
                res.append(0.0)
                continue
            sumv = self.geometry.sum_segments_in_circle(idx, tower.attributes['range'])
            res.append(sumv * mul)
        return res

    def get_action(self, enemy: EnemyInfo, game: GameInfo):
        stores: list[int] = []
        for i in range(len(game.store)):
            tower_type = game.store[i]['type']
            tower = game.towers[tower_type]
            stores.append(i)

            # best_atk_spd
            if enemy.best_atk_spd[0] == 'Fast':
                if tower.attributes['interval'] >= 0.30:
                    game.store[i]['damage'] /= 2
                elif tower.attributes['interval'] <= 0.06:
                    game.store[i]['damage'] *= 1.5
            elif enemy.best_atk_spd[0] == 'Normal':
                pass
            else:
                if tower.attributes['interval'] <= 0.06:
                    game.store[i]['damage'] /= 1.5
                elif tower.attributes['interval'] >= 0.30:
                    game.store[i]['damage'] *= 2

            # type advantage
            if tower.attributes['type'] in enemy.weak:
                game.store[i]['damage'] *= 1.25
            elif tower.attributes['type'] in enemy.resist:
                game.store[i]['damage'] *= 0.8

            # slow_eff
            if enemy.slow_eff[0] == 'Resist':
                game.store[i]['damage'] *= tower.attributes.get('speedDown', 1.0)
            elif enemy.slow_eff[0] == 'Weak':
                game.store[i]['damage'] /= (tower.attributes.get('speedDown', 1.0) ** 3)

            # n_targets
            if tower.attributes['n_targets'] == -1:
                tower.attributes['n_targets'] = 6
            mul = tower.attributes['n_targets']
            if enemy.occurrence[0] == 'Double':
                mul = min(mul, 2)
            elif enemy.occurrence[0] == 'Triple':
                mul = min(mul, 3)
            elif enemy.occurrence[0] == 'Dense':
                if tower.attributes.get('bullet_range', 0):
                    tower.attributes['n_targets'] = 6
                    mul = 6
                mul = min(mul, 6)
            elif enemy.occurrence[0] == 'Sparse':
                mul = min(mul, 6)
            else: # Single
                mul = min(mul, 1)
            game.store[i]['damage'] *= mul
            
            # special_eff
            if tower.attributes['type'] in enemy.special_eff:
                game.store[i]['damage'] *= 1.54

        max_edamage = 0
        maxid = -1
        maxpl = -1
        for s in stores:
            r = self.get_edamages(game.store[s]['damage'], game.towers[game.store[s]['type']], game)
            # DEBUG_FILE.write(f'Expected damage: max: {max(r)}\n')
            # DEBUG_FILE.write(game.towers[game.store[s]['type']].attributes.__str__()+'\n')
            # DEBUG_FILE.write(str(game.store[s])+'\n')
            if game.store[s]['cost'] <= game.coins and max(r) > max_edamage:
                max_edamage = max(r)
                maxid = s
                maxpl = r.index(max(r))
        # DEBUG_FILE.write(f'MAX {max_edamage}\n')
        self.refreshed = False
        self.edamages.append(max_edamage)
        self.edamages.sort()
        if maxid == -1 or self.refresh_times < PRE_REFRESH:
            self.refresh_times += 1
            return 'refresh'
        if max_edamage < self.edamages[-1] * EXPECT_THRESHOLD:
            self.edamages.pop(-1)
            self.refresh_times += 1
            return 'refresh'
        return f"buy {maxid} {maxpl}"