class Action:
    def execute(self, session) -> int:
        """executes an action on the session and returns the number of rows affected
        """
        raise NotImplementedError()


class InsertAction(Action):
    def __init__(self, items):
        self.items = items

    def execute(self, session):
        for item in self.items:
            session.add(item)
        return len(self.items)


class UpdateAction(Action):
    def __init__(self, model, query, update):
        self.model = model
        self.query = query
        self.update = update

    def execute(self, session):
        for instance in session.query(self.model).filter_by(**self.query):
            for key, value in self.update.items():
                setattr(instance, key, value)
        return 1

