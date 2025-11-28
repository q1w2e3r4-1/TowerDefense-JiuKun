from game_info import EnemyInfo, TowerInfo, GameInfo
from math import sqrt
from visualize import visualize_map_and_points
import numpy as np
import random
PRE_REFRESH = 3
EXPECT_THRESHOLD = 0.3
SEG_DIST = 0.3
SP_EFF_RATE = 1.54
NUM_DENSE = 6
PERCENTILE_THRESHOLD = 0.75
DP_SAMPLE_NUM = 500
DP_START_COINS = 60
# DEBUG_FILE = open('debug.log', 'w')

# --- Point class for discrete map points ---
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.slow_rate = 1.0
        self.has_special_eff = False
        self.total_damage = 0.0

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
        # visualize_map_and_points(self.map, self.points, 'saved_map_points.png')
        # 预处理每个placement_option和0-20所有整数射程的点贡献
        self.range_table = RangeCoverageTable(game_info.placement_options, self.points, max_radius=20)

    def sum_contribution_in_circle(self, pos_idx, radius, atk: float, slow_rate: float, is_special_eff: bool):
        # 计算某个放置点在某个射程下，覆盖的路径点贡献delta总和
        def get_old_damage(pt: Point):
            dmg = pt.total_damage
            dmg /= pt.slow_rate
            dmg *= SP_EFF_RATE if pt.has_special_eff else 1.0
            return dmg
        
        def get_new_damage(pt: Point, atk: float, slow_rate: float, is_special_eff: bool):
            dmg = pt.total_damage + atk
            dmg /= min(slow_rate, pt.slow_rate)
            dmg *= SP_EFF_RATE if (is_special_eff or pt.has_special_eff) else 1.0
            return dmg
        
        # 获取覆盖点下标list
        indices = self.range_table.get_coverage(pos_idx, radius)
        total_delta = 0.0
        for i in indices:
            pt = self.points[i]
            old_dmg = get_old_damage(pt)
            new_dmg = get_new_damage(pt, atk, slow_rate, is_special_eff)
            delta = new_dmg - old_dmg
            total_delta += delta

        return total_delta * SEG_DIST  # 乘以路径点间距作为近似积分

    def update_board(self, pos_idx, atk, range, slow_rate, is_special_eff):
        # 更新某个放置点在某个射程下，覆盖的路径点的总伤害和状态
        indices = self.range_table.get_coverage(pos_idx, range)
        for i in indices:
            pt = self.points[i]
            pt.total_damage += atk
            pt.slow_rate = min(pt.slow_rate, slow_rate)
            if is_special_eff:
                pt.has_special_eff = True
    
class Strategy:
    def __init__(self, game_info: GameInfo):
        self.refresh_times = 0
        self.edamages = []
        self.geometry = Geometry(game_info)
        self.tot_cost = 0
        self.history_towers = []
        self.total_dmg = 0.0
        self.num_chosen = 0
        self.need_recalc = True
        self.buffer_dmgs = []

    def get_edamages(self, atk, range, game: GameInfo, slow_rate: float, is_special_eff: bool):
        res = []
        for idx, t in enumerate(game.placed_towers):
            if t:
                res.append(0.0)
                continue
            sumv = self.geometry.sum_contribution_in_circle(idx, range, atk, slow_rate, is_special_eff)
            res.append(sumv)
        return res

    def get_damage_for_tower(self, atk, tower, enemy, game):
        # best_atk_spd
        if enemy.best_atk_spd[0] == 'Fast':
            if tower.attributes['interval'] >= 0.30:
                atk /= 2
            elif tower.attributes['interval'] <= 0.06:
                atk *= 1.5
        elif enemy.best_atk_spd[0] == 'Normal':
            pass
        else:
            if tower.attributes['interval'] <= 0.06:
                atk /= 1.5
            elif tower.attributes['interval'] >= 0.30:
                atk *= 2

        # type advantage
        if tower.attributes['type'] in enemy.weak:
            atk *= 1.25
        elif tower.attributes['type'] in enemy.resist:
            atk *= 0.8

        # slow_eff
        slow_rate = tower.attributes.get('speedDown', 1.0)
        if enemy.slow_eff[0] == 'Resist':
            slow_rate = 1.0 # immune to slow
        elif enemy.slow_eff[0] == 'Weak':
            slow_rate = tower.attributes.get('speedDown', 1.0) ** 3 

        
        # n_targets
        if tower.attributes['n_targets'] == -1:
            tower.attributes['n_targets'] = NUM_DENSE
        mul = tower.attributes['n_targets']
        if enemy.occurrence[0] == 'Double':
            mul = min(mul, 2)
        elif enemy.occurrence[0] == 'Triple':
            mul = min(mul, 3)
        elif enemy.occurrence[0] == 'Dense':
            if tower.attributes.get('bullet_range', 0):
                tower.attributes['n_targets'] = NUM_DENSE
                mul = NUM_DENSE
            mul = min(mul, NUM_DENSE)
        elif enemy.occurrence[0] == 'Sparse':
            mul = min(mul, NUM_DENSE)
        else: # Single
            mul = min(mul, 1)
        atk *= mul
        atk /= tower.attributes['interval']
        # atk *= 1 - (atk - 12) * 0.03 # cost penalty
        
        # special_eff
        is_special_eff = tower.attributes['type'] in enemy.special_eff

        r = self.get_edamages(atk, tower.attributes['range'], game, slow_rate, is_special_eff)
        return r, atk, slow_rate, is_special_eff

    def get_action(self, enemy: EnemyInfo, game: GameInfo):
        stores: list[int] = []
        max_edamage = 0
        maxid = -1
        maxpl = -1
        max_attr = {}
        shop = []

        for i in range(len(game.store)):
            tower_type = game.store[i]['type']
            tower = game.towers[tower_type]
            stores.append(i)
            self.history_towers.append(game.store[i])
            atk = game.store[i]['damage']

            r, atk, slow_rate, is_special_eff = self.get_damage_for_tower(atk, tower, enemy, game)
            shop.append( (max(r), game.store[i]['cost']) )
            self.buffer_dmgs.append(max(r))
            # print("add to shop:", i, max(r), game.store[i]['cost'])

            if game.store[i]['cost'] <= game.coins and max(r) > max_edamage:
                max_edamage = max(r)
                maxid = i
                maxpl = r.index(max(r))
                max_attr = { 'atk': atk, 'range': tower.attributes['range'], 'slow_rate': slow_rate, 'is_special_eff': is_special_eff, 'cost': game.store[i]['cost']}
        # print(f"Decided action: maxedamage={max_edamage}, maxid={maxid}, maxpl={maxpl}")

        assert len(self.history_towers) == len(self.buffer_dmgs), "History towers and buffer damages length mismatch"
        # 计算当前max_edamage的gain在history_gain中的百分位
        self.edamages.append(max_edamage)
        self.edamages.sort()
        if maxid == -1 or self.refresh_times < PRE_REFRESH:
            self.refresh_times += 1
            return 'refresh'
        
        if game.coins < DP_START_COINS:
            action, maxid, exp_score = self.plan_dp_action(enemy, game, shop, num_sample=DP_SAMPLE_NUM, num_chosen=self.num_chosen)
            # print(f"coins = {game.coins}, dp action = {action}, exp_score = {exp_score}")
            if action == 'refresh':
                self.refresh_times += 1
                return 'refresh'
            else:
                # buy
                atk = game.store[maxid]['damage']
                tower = game.towers[game.store[maxid]['type']]
                r, atk, slow_rate, is_special_eff = self.get_damage_for_tower(atk, tower, enemy, game)  
                maxpl = r.index(max(r))

                # update
                self.geometry.update_board(maxpl, atk, tower.attributes['range'], slow_rate, is_special_eff)
                self.tot_cost += game.store[maxid]['cost']
                self.total_dmg += max(r)
                self.need_recalc = True
                self.num_chosen += 1
                # print("+", max(r))
                return f"buy {maxid} {maxpl}"
        else:
            if max_edamage < self.edamages[-1] * EXPECT_THRESHOLD:
                self.edamages.pop(-1)
                self.refresh_times += 1
                return 'refresh'
            
            # buy
            self.geometry.update_board(maxpl, max_attr['atk'], max_attr['range'], max_attr['slow_rate'], max_attr['is_special_eff'])
            self.tot_cost += max_attr['cost']
            self.total_dmg += max_edamage
            self.need_recalc = True
            self.num_chosen += 1
            return f"buy {maxid} {maxpl}"

    def get_history_dmgs(self, enemy: EnemyInfo, game: GameInfo):
        if not self.need_recalc:
            return self.buffer_dmgs, self.total_dmg
        
        ret = []
        for t in self.history_towers:
            atk = t['damage']
            r, _, _, _= self.get_damage_for_tower(atk, game.towers[t['type']], enemy, game)
            ret.append(max(r))
        self.buffer_dmgs = ret
        self.need_recalc = False
        return ret, self.total_dmg
    
    def cal_gain(sekf, base_sum, delta):
        log_base = 1.008
        prev_score = np.log(base_sum + 1) / np.log(log_base)
        curr_score = np.log(base_sum + delta + 1) / np.log(log_base)
        return curr_score - prev_score
    
    def get_tower_gains(self, enemy: EnemyInfo, game: GameInfo):
        gains = []
        history_dmgs, base_sum = self.get_history_dmgs(enemy, game)
        history_dmgs = sorted(history_dmgs, reverse=True)

        for delta in history_dmgs:
            gains.append(self.cal_gain(base_sum, delta))
        return gains

    def dp_expected_score_action(self, coins, items:list[tuple], shop, num_sample=DP_SAMPLE_NUM):
        min_price = min([c for _, c in items], default=9999)
        memo = {}
        def dp(c):
            if c < min_price:
                return 0
            if c in memo:
                return memo[c]
            sample_maxes = []
            for _ in range(num_sample):
                # curr_shop_size = random.randint(16, 30)
                curr_shop_size = 20
                sampled_shop = random.sample(items, curr_shop_size)
                local_max = 0
                # 买
                for score, price in sampled_shop:
                    if price <= c:
                        total = score + dp(c - price)
                        if total > local_max:
                            local_max = total
                # 刷新
                if c > 1:
                    total = dp(c - 1)
                    if total > local_max:
                        local_max = total
                sample_maxes.append(local_max)
            avg_score = sum(sample_maxes) / num_sample if sample_maxes else 0
            memo[c] = avg_score
            return avg_score
        # 只对当前shop做决策
        best_score = -float('inf')
        best_idx = -1
        for idx, (score, price) in enumerate(shop):
            if price <= coins:
                total = score + dp(coins - price)
                # print (f"Trying buy item idx={idx} (score={score}, price={price}): total expected score(dp{coins - price}) = {dp(coins - price)}")
                if total > best_score:
                    best_score = total
                    best_idx = idx

        # print(memo)
        # print(f"Best buy idx={best_idx} with expected total score={best_score}")
        # input()
        # 尝试刷新
        if coins > 1:
            total = dp(coins - 1)
            if total > best_score:
                return 'refresh', -1, total
        return ('buy ', best_idx, best_score) if best_idx != -1 else ('refresh', -1, best_score)

    def plan_dp_action(self, enemy: EnemyInfo, game: GameInfo, shop: list[tuple], num_sample=DP_SAMPLE_NUM, num_chosen=0):
        # 1. 获取历史伤害和cost
        history_dmgs, _ = self.get_history_dmgs(enemy, game)
        costs = [t['cost'] for t in self.history_towers]
        pairs = list(zip(history_dmgs, costs))
        # 2. 删去damage最高的num_chosen个
        pairs = sorted(pairs, key=lambda x: -x[0])
        pairs = pairs[num_chosen:]
        coins = game.coins
        # 当前商店
        if coins < min([c for _, c in pairs], default=9999):
            return 'refresh', -1, 0
        action = self.dp_expected_score_action(coins, pairs, shop, num_sample=num_sample)
        # print("!!!", action)
        # print(sorted(shop))
        return action