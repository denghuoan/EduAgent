from pydantic import BaseModel, ValidationError


class Person(BaseModel):
    name: str
    age: int

try:
    p = Person(name='cc', age = "十八")
    print(p.age)

except ValidationError as e:
    print(e)


# 1 validation error for Person
# age
#   Input should be a valid integer, unable to parse string as an integer...