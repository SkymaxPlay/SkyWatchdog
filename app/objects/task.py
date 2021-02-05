class Task:
    def __init__(self, name, check_type, source):
        self.name = name
        self.check_type = check_type
        self.source = source

        self.payload = None
        self.rescue_exec = []

        self.notify = None

        self.last_check_good = True

    def rescue_mode_enabled(self):
        return self.rescue_exec
