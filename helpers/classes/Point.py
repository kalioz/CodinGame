import math

class Point:
    """Class used to store a (x,y) parameters. It can be used to store points or vectors values, like movement."""

    def __init__(self, x:int, y:int):
        self.x = int(x)
        self.y = int(y)

    def outside_boundaries(self, min_point, max_point):
        return not (self.x > min_point.x and self.y > min_point.y and self.x < max_point.x and self.y < max_point.y)

    def distance(self, other, y=None):
        """Calculate the distance between the point and another point.
            usage: Point(0,0).distance(Point(1,0))
                   Point(0,0).distance(1,0)
            returns the distance as a float.
        """
        if y is None and isinstance(other, Point):
            return self.distance(other.x, other.y)
        return math.dist([self.x, self.y], [other, y])

    def near(self, other, max_allowed_distance):
        """Calculate the distance between the point and another point, and check if it is < max_allowed_distance.
            if the other is a list, it will return true if ANY element of that list is < max_allowed_distance
        """
        if isinstance(other, list):
            return any(self.distance(point, max_allowed_distance) for point in other)
        elif isinstance(other, Point):
            # check if the distance between self and point is below the max_allowed_distance
            return self.distance_point(other) < max_allowed_distance
        else:
            raise Exception("Invalid type: ", type(other))

    def calculate_position_circle(self, radius, radians):
        # calculate the position of another point if it were on a circle of radius at a degree of radians
        return self + Point(radius * math.cos(radians), radius * math.sin(radians))

    def calculate_angle(self, other):
        """return the angle in radians of the angle between self and other."""
        return math.atan2(other.y-self.y, other.x - self.x)

    def calculate_position_circle_nearest(self, radius, point):
        """calculate the position in the circle of radius R and of center self so that it is the closest to point."""
        radians = math.atan2(point.y - self.y, point.x - self.x)
        return self.calculate_position_circle(radius, radians)

    #### Class functions

    def __eq__(self, other):
        if (isinstance(other, Point)):
            return self.x == other.x and self.y == other.y
        return False

    def __repr__(self):
        return f'Point(x: {self.x}, y: {self.y})'

    def __add__(self, point):
        return Point(self.x + point.x, self.y + point.y)

    def __sub__(self, point):
        return Point(self.x - point.x, self.y - point.y)

    def __truediv__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Point(self.x / other, self.y / other)
        else:
            raise TypeError(f'Cannot multiply a Point with {type(other)}')

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Point(self.x * other, self.y * other)
        else:
            raise TypeError(f'Cannot multiply a Point with {type(other)}')

    __rmul__ = __mul__
