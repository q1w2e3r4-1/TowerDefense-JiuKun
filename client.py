import sys
import json
import socketio
from socketio import Client
import time
import threading
import numpy as np
import argparse
import random
import traceback

from game_info import GameInfo, EnemyInfo, TowerInfo
from game_recorder import GameRecorder
from strategy import Strategy

response_event = threading.Event()
response_data = None
DEBUG = False
# ====== 配置 ======
SERVER_URL = "http://117.186.102.78:32500/"
TEAM_ID = open("team_id").readlines()[0].strip()
# 开始测试前，请将在同一文件夹下创建team_id文件，填入自己的team_id
GAME_ID = 0

# ====== 初始化客户端 ======
sio = Client(
    reconnection=True,           
    reconnection_attempts=None,  
    reconnection_delay=1,        
    reconnection_delay_max=5   
)
game_over = False
game_end = False

action_mode = 'input'

recorder = None
strategy = Strategy()
game_info = GameInfo()

@sio.event
def connect():
    recorder.write("[CLIENT] Connected to server", debug=True)
    sio.emit("begin", {"team_id": TEAM_ID, "game_id": GAME_ID})

@sio.event
def disconnect(reason = 'server disconnected'):
    global game_over
    recorder.write("[CLIENT] Disconnected: " + reason, debug=True)
    game_over = True

@sio.on("response")
def on_response(data):
    global game_over
    global response_data
    
    if "error" in data:
        print("Error:", data["error"])
        return
    
    # print(data)

    response_data = data
    response_event.set()

@sio.on("end")
def on_end(data):
    global game_end
    recorder.write("[GAME END] " + str(data), debug=DEBUG)
    if RECORD_DIR != "records": # batch mode
        with open(f"{RECORD_DIR}/score.csv", "a", encoding="utf-8") as f:
            f.write(f"{GAME_ID},{data.get('score_pred','')},{data.get('score_game','')}\n")
    game_end = True

def main_loop():
    global strategy
    global game_over, action_mode
    global recorder, game_info
    assert recorder is not None

    while not game_end:
        # 等待接收服务器的信息
        if not response_event.wait(timeout=1):
            continue
        response_event.clear()
        resp: dict = response_data
        # 更新游戏信息
        if resp.get("start_round"):
            recorder.write("\n\n\n\n==============================", debug=DEBUG)
            round_num = resp.get("i_round", "?")
            recorder.write(f"** New round {round_num} started **", debug=DEBUG)
            if "enemy_name" in resp:
                recorder.write(f"Enemy Name: {resp['enemy_name']}", debug=DEBUG)
            if "enemy_description" in resp:
                recorder.write(f"Enemy Description: {resp['enemy_description']}", debug=DEBUG)
            recorder.write(f"Coins: {resp.get('n_coins', '?')}", debug=DEBUG)
            # 更新game_info
            game_info.set_round(resp.get("i_round", 0))
            if "enemy_name" in resp or "enemy_description" in resp:
                enemy = EnemyInfo(
                    name=resp.get("enemy_name", ""),
                    description=resp.get("enemy_description", ""),
                    best_atk_spd=resp.get("best_atk_spd", []),
                    weak=resp.get("weak", []),
                    resist=resp.get("resist", []),
                    special_eff=resp.get("special_eff", []),
                    slow_eff=resp.get("slow_eff", []),
                    occurrence=resp.get("occurrence", [])
                )
                game_info.add_enemy(enemy)
            game_info.set_coins(resp.get("n_coins", 0))
            if 'store' in resp:
                game_info.update_store(resp['store'])
        else:
            if 'towers_list' in resp:
                recorder.write(f"Towers: {resp['towers_list']}", debug=DEBUG)
                if 'map' in resp:
                    recorder.write(f"Map: {resp['map']['map']}", debug=DEBUG)
                    recorder.write(f"Placement Options: {resp['map']['extra']}", debug=DEBUG)
                    recorder.write("==============================", debug=DEBUG)
                    game_info.set_map(resp['map'].get('map', []))
                    game_info.set_placement_options(resp['map'].get('extra', []))
                # 填充已放置塔信息
                game_info.towers = []
                for tower in resp['towers_list']:
                    attrs = dict(tower)
                    game_info.add_tower(TowerInfo(attrs))
            recorder.write(f"Coins: {resp['n_coins']}", debug=DEBUG)
            game_info.set_coins(resp.get('n_coins', 0))
            if 'store' in resp:
                recorder.write("Store: " + str(resp["store"]), debug=DEBUG)
                game_info.update_store(resp['store'])
        
        if resp.get("game_over"):
            game_info.debug_print()
            game_over = True
            recorder.write("** Game Over **", debug=DEBUG)

        if 'enemy_description' in resp:
            cmd = 'predict'
            # ====== TODO_pred: 下面可以改成自己的代码，用于提交预测结果
            label_pred = {
                'best_atk_spd': ['Normal'],
                'weak': ['Fire', 'Ice', 'Poison'],
                'resist': ['Blunt', 'Lightning'],
                'special_eff': ['Fire'],
                'slow_eff': ['Normal'],
                'occurrence': ['Triple'],
            }
            # ====== 上面可以改成自己的代码，用于提交预测结果
        else:
            if action_mode == 'input':
                if not game_over:
                    cmd = input("\nEnter action ('refresh' or 'buy item_idx bag_idx' or 'end'): ").strip()
            else:
                # ====== TODO_strategy: 下面可以改成自己的代码，用于处理决策
                if 'map' in resp:
                    game_info.set_map(resp['map']['map'])
                    game_info.set_placement_options(resp['map']['extra'])
                if 'towers_list' in resp:
                    game_info.towers = [TowerInfo(dict(tower)) for tower in resp['towers_list']]
                game_info.update_store(resp['store'])
                game_info.coins = resp['n_coins']
                if 'start_round' in resp:
                    print('Starting new round, reset strategy')
                    strategy = Strategy()
                cmd = strategy.get_action(EnemyInfo(name='', description='', **label_pred), game_info)
                # ====== 上面可以改成自己的代码，用于处理决策

        if cmd.lower() == "refresh":
            action = {"type": "refresh"}
        elif cmd.lower() == "end":
            action = {"type": "end"}
        elif cmd.lower() == "predict":
            action = {"type": "predict", "label_pred": label_pred}
            game_info.update_enemy(
                name=resp.get("enemy_name", ""),
                best_atk_spd=label_pred.get('best_atk_spd', None),
                weak=label_pred.get('weak', None),
                resist=label_pred.get('resist', None),
                special_eff=label_pred.get('special_eff', None),
                slow_eff=label_pred.get('slow_eff', None),
                occurrence=label_pred.get('occurrence', None)
            )
        elif cmd.lower().startswith("buy"):
            try:
                _, item_idx, bag_idx = cmd.split()
                action = {"type": "buy", "item_idx": int(item_idx), "bag_idx": int(bag_idx)}
                item = game_info.get_store_item(int(item_idx))
                tower_idx = item.get('type', 0)
                tower = game_info.get_tower_item(tower_idx)

                for k, v in item.items():
                    if k != 'type':
                        tower.attributes[k] = v
                tower.attributes["position"] = int(bag_idx)
                game_info.set_placed_tower_item(int(bag_idx), tower)
            except Exception as e:
                traceback.print_exc()
                print(f"Invalid buy command {cmd}. Example: buy 0 1")
                continue
        else:
            print("Unknown command")
            continue

        if not game_over:
            recorder.write("[User Action] " + str(action), debug=DEBUG)
            sio.emit("action", action)
            # game_info.print_placed_towers()

def main():    
    global game_over, action_mode
    global recorder
    # 创建记录器实例
    recorder = GameRecorder(GAME_ID, RECORD_DIR)
    
    while True:
        try:
            sio.connect(SERVER_URL)
            break 
        except socketio.exceptions.ConnectionError:
            recorder.write("Connection failed. Retrying...", debug=True)
            time.sleep(3)
  
    try:
        main_loop()
    except Exception as e:
        print(f"Exception occurred: {e}")
        traceback.print_exc()
        sio.disconnect()

    print("Client terminated")
    if recorder:
        recorder.close()

if __name__ == "__main__":
    # 测试： python client.py --game_id 0 --action auto
    parser = argparse.ArgumentParser()
    parser.add_argument("--team_id", default=None, type=str)
    parser.add_argument("--game_id", default=0, type=int) # 设置玩的游戏
    parser.add_argument("--action_mode", default='auto', type=str)
    parser.add_argument("--server_url", default=None, type=str)
    parser.add_argument("--record_dir", default="records", type=str)
    args = parser.parse_args()

    if args.team_id:
        TEAM_ID = args.team_id
    if args.game_id:
        GAME_ID = args.game_id
    if args.server_url:
        SERVER_URL = args.server_url
    action_mode = args.action_mode
    RECORD_DIR = args.record_dir

    main()

