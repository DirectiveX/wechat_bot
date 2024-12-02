class MomentInfo:
    def __init__(self, time, message):
        self.time = time
        self.message = message

    def to_dict(self):
        return {
            "time":self.time,
            "message":self.message
        }