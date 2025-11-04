class GameRecorder:
    def __init__(self, game_id):
        import time
        self.filename = f"game_id_{game_id}_{int(time.time())}.record"
        self.file = open(self.filename, "w", encoding="utf-8")

    def write(self, content):
        if isinstance(content, dict):
            import json
            self.file.write(json.dumps(content, ensure_ascii=False) + "\n")
        else:
            self.file.write(str(content) + "\n")
        self.file.flush()

    def close(self):
        self.file.close()
