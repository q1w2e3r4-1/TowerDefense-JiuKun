from game_info import EnemyInfo, TowerInfo, GameInfo

class Strategy:
    @staticmethod
    def segment_length_in_circle(p1: tuple, p2: tuple, center: tuple, radius: float) -> float:
        from math import sqrt

        def point_in_circle(point, center, radius):
            px, py = point
            cx, cy = center
            return (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2

        def line_circle_intersection(p1, p2, center, radius):
            x1, y1 = p1
            x2, y2 = p2
            cx, cy = center

            dx, dy = x2 - x1, y2 - y1
            a = dx ** 2 + dy ** 2
            b = 2 * (dx * (x1 - cx) + dy * (y1 - cy))
            c = (x1 - cx) ** 2 + (y1 - cy) ** 2 - radius ** 2

            discriminant = b ** 2 - 4 * a * c
            if discriminant < 0:
                return []

            sqrt_discriminant = sqrt(discriminant)
            t1 = (-b - sqrt_discriminant) / (2 * a)
            t2 = (-b + sqrt_discriminant) / (2 * a)

            intersections = []
            if 0 <= t1 <= 1:
                intersections.append((x1 + t1 * dx, y1 + t1 * dy))
            if 0 <= t2 <= 1:
                intersections.append((x1 + t2 * dx, y1 + t2 * dy))

            return intersections

        if point_in_circle(p1, center, radius) and point_in_circle(p2, center, radius):
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            return sqrt(dx ** 2 + dy ** 2)

        intersections = line_circle_intersection(p1, p2, center, radius)
        if len(intersections) == 2:
            x1, y1 = intersections[0]
            x2, y2 = intersections[1]
            dx, dy = x2 - x1, y2 - y1
            return sqrt(dx ** 2 + dy ** 2)
        elif len(intersections) == 1:
            if point_in_circle(p1, center, radius):
                x1, y1 = p1
            else:
                x1, y1 = p2
            x2, y2 = intersections[0]
            dx, dy = x2 - x1, y2 - y1
            return sqrt(dx ** 2 + dy ** 2)
        return 0.0

    def __init__(self):
        self.refreshed = False

    def get_edamages(self, atk, tower: TowerInfo, game: GameInfo):
        mul = atk
        if 'speedDown' in tower.attributes:
            mul /= tower.attributes['speedDown']
        mul /= tower.attributes['interval']

        res = []
        for (o, t) in zip(game.placement_options, game.placed_towers):
            if t:
                res.append(0.0)
                continue
            sum = 0.0
            for _i in range(len(game.map)-1):
                p1 = game.map[_i]
                p2 = game.map[_i+1]
                sum += self.segment_length_in_circle(p1, p2, o, tower.attributes['range'])
            res.append(sum*mul)
        return res

    def get_action(self, enemy: EnemyInfo, game: GameInfo):
        weak_stores: list[int] = []
        none_stores: list[int] = []
        resist_stores: list[int] = []
        for i in range(len(game.store)):
            tower_type = game.store[i]['type']
            tower = game.towers[tower_type]
            if tower.attributes['n_targets'] <= 0:
                continue
            if tower.attributes['type'] in enemy.weak or True:
                weak_stores.append(i)
            elif tower['type'] in enemy.resist:
                resist_stores.append(i)
            else:
                none_stores.append(i)
        if not self.refreshed:
            if not weak_stores:
                self.refreshed = True
                return 'refresh'
        if not weak_stores:
            stores = none_stores if none_stores else resist_stores
        else:
            stores = weak_stores

        max_edamage = 0
        maxid = -1
        maxpl = -1
        for s in stores:
            r = self.get_edamages(game.store[s]['damage'], game.towers[game.store[s]['type']], game)
            if game.store[s]['cost'] <= game.coins and max(r) > max_edamage:
                max_edamage = max(r)
                maxid = s
                maxpl = r.index(max(r))
        self.refreshed = False
        if maxid == -1:
            return 'refresh'
        return f"buy {maxid} {maxpl}"