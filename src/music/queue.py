class MusicQueue:
    def __init__(self):
        self.queue = []
        self.history = []
        self.loop = False
        self.volume = 0.5  # 50%
        self.autoplay = False

    def add(self, track):
        if "webpage_url" not in track and "url" in track:
            track["webpage_url"] = track["url"]
        self.queue.append(track)

    def next(self):
        if self.loop and self.history:
            return self.history[-1]

        if self.queue:
            track = self.queue.pop(0)
            self.history.append(track)
            return track

        return None
    def peek(self):
        return self.queue[0] if self.queue else None
    def back(self):
        if len(self.history) > 1:
            track = self.history[-2]
            self.queue.insert(0, self.history.pop())
            return track
        return None
    def shuffle(self):
        random.shuffle(self.queue)
