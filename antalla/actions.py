from sqlalchemy.dialects.postgresql import insert


class Action:
    def execute(self, session) -> int:
        """executes an action on the session and returns the number of rows affected
        """
        raise NotImplementedError()


class InsertAction(Action):
    def __init__(self, items):
        super().__init__()
        self.items = items
        self.item_type = None
        if self.items:
            self.item_type = type(items[0])
            if not all(isinstance(item, self.item_type) for item in self.items):
                raise ValueError("all items should be of the same type")

    def execute(self, session):
        if not self.items:
            return 0
        values = []
        items = set(self.items)
        index_elements = self.item_type.index_elements()
        for item in items:
            data = vars(item)
            data.pop("_sa_instance_state", None)
            values.append(data)
        insert_stmt = insert(self.item_type).values(values) \
                                            .on_conflict_do_nothing(index_elements=index_elements)
        session.execute(insert_stmt)
        return len(items)


class UpdateAction(Action):
    def __init__(self, model, query, update):
        super().__init__()
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

