class GameRecorder:
    def __init__(self, game_id, record_dir="records"):
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%m%d_%H%M")
        self.filename = f"{record_dir}/game_id_{game_id}_{date_str}.record"
        self.file = open(self.filename, "w", encoding="utf-8")

    def write(self, content, debug=False):
        if isinstance(content, dict):
            import json
            self.file.write(json.dumps(content, ensure_ascii=False) + "\n")
            if debug:
                print(json.dumps(content, ensure_ascii=False) + "\n")
        else:
            self.file.write(str(content) + "\n")
            if debug:
                print(str(content) + "\n")
        self.file.flush()

    def close(self):
        self.file.close()
