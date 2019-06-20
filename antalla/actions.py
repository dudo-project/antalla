class Action:
    def __init__(self, commit=False):
        self.commit = commit

    def execute(self, session) -> int:
        """executes an action on the session and returns the number of rows affected
        """
        raise NotImplementedError()


class InsertAction(Action):
    def __init__(self, items, check_duplicates=False, commit=False):
        super().__init__(commit=commit)
        self.items = items
        self.check_duplicates = check_duplicates

    def execute(self, session):
        inserted_count = 0
        for item in set(self.items):
            if self.should_add(item, session):
                inserted_count += 1
                session.add(item)
        return inserted_count

    def should_add(self, item, session):
        if not self.check_duplicates:
            return True
        if self.check_duplicates is True:
            columns = [v.name for v in item.__table__.primary_key]
        else:
            columns = self.check_duplicates
        filters = {k: getattr(item, k) for k in columns}
        query = session.query(type(item)).filter_by(**filters).exists()
        return not session.query(query).scalar()


class UpdateAction(Action):
    def __init__(self, model, query, update, commit=False):
        super().__init__(commit=commit)
        self.model = model
        self.query = query
        self.update = update

    def execute(self, session):
        n = 0
        for instance in session.query(self.model).filter_by(**self.query):
            n += 1
            for key, value in self.update.items():
                setattr(instance, key, value)
        return n

