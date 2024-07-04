from typing import List

from PyBean.instance import create_instance


class Property:
    def __init__(self, name, value):
        self.name: str = name
        self.value: object = value


class Properties:
    def __init__(self):
        self.properties = {}

    def set_property(self, key, value):
        self.properties[key] = value

    def get_property(self, key):
        return self.properties.get(key)

    def list_properties(self):
        return list(self.properties.keys())


class Bean:
    def __init__(self):
        self.attrib = {}
        self.instance = None
        self.__properties: List[Property] = []

    def add_property(self, prop: Property):
        self.__properties.append(prop)

    def get_properties(self) -> List[Property]:
        return self.__properties

    def create(self, class_name, application, *args, **kwargs):
        self.instance = create_instance(class_name, *args, **kwargs)
        for prop in self.__properties:
            if prop.value is not None:
                value = prop.value
                value = value_translate(value)
                exec(f"self.instance.{prop.name} = value")
            # if prop.ref is not None:
            #     instance = application.getBean(prop.ref)
            #     prop.value = instance
            #     exec(f"self.instance.{prop.name} = instance")


def value_translate(value):
    if value is None or type(value) not in [int, float, str]:
        return value
    if value.isdigit():
        value = int(value)
    elif "." in value:
        try:
            value = float(value.strip())
        except ValueError as e:
            pass
    return value
