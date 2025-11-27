import matplotlib.pyplot as plt

# map_points: List[Tuple[float, float]]
# discrete_points: List[Point] (with .x, .y)
def visualize_map_and_points(map_points, discrete_points, save_path=None):
    plt.figure()
    # 画地图折线
    xs = [p[0] for p in map_points]
    ys = [p[1] for p in map_points]
    plt.plot(xs, ys, '-o', label='Map Polyline', markersize=1)

    # 画离散点
    px = [p.x for p in discrete_points]
    py = [p.y for p in discrete_points]
    plt.scatter(px, py, c='red', s=10, label='Discrete Points')

    plt.axis('equal')
    plt.legend()
    plt.title('Map and Discrete Points Visualization')
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
