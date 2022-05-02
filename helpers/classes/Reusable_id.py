# This contains the bare code for a "reusable" class, meaning a class that will not create another object if it already exists.
# To do so, the example uses an unique id to identify the different objects - you can adapt it to what you need it to be !

class ReusableId:
    """Class enabling the reuse of the previously-created objects. the first parameters sent to the class should be a unique identifier."""

    # class wide variable
    ## tracks the entities for the duration of the program - note that currently this is NEVER cleaned up, so you might want to take care if your number of entities were to climb up.
    __entities = {}

    def __new__(cls, _id, *args, **kwargs):
        # creates or get the existing ReusableId from the tracked list
        if _id in ReusableId.__entities:
            ReusableId.__entities[_id].__is_new_instance = False
            return ReusableId.__entities[_id]
        out = object.__new__(cls)
        out.__is_new_instance = True

        out.init_instance()

        ReusableId.__entities[_id] = out

        return out

    def __init__(self, _id):
        self.id = _id

    def __eq__(self, other):
        if (isinstance(other, ReusableId)):
            return self.id == other.id
        return False

    def __repr__(self):
        return f'ReusableId(id: {self.id})'

    def init_instance(self):
        """Code that should be run when the instance is created for the first time.
            the code in __init__ will be called for each invocation of ReusableId(X), while this one will be called only on the first invocation.
            Define here (or in the subclass) variables that should be shared across different invocation, e.g. lists, ...
        """
        print("INFO: no init_instance defined - the ReusableId class might not be needed on this subclass")


class Example(ReusableId):
    def init_instance(self):
        self.positions = []

    def __init__(self, id, position):
        super().__init__(id)
        self.positions.append(position)

    def __repr__(self):
        return f'Example(id: {self.id}, positions: {self.positions})'

if __name__ == "__main__":
    u = Example(5, 9)
    v = Example(5, 10)
    print("u is v:",u is v)
    print("u: ", u)
