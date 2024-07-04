def create_instance(class_name, *args, **kwargs):
    # print("create name:", class_name)
    parts = class_name.split('.')
    module_name = '.'.join(parts[:-1])
    class_name = parts[-1]

    try:
        module = __import__(module_name, fromlist=[class_name])
        clazz = getattr(module, class_name)
        return clazz(*args, **kwargs)
    except ImportError as e:
        raise ImportError(f"Unable to import {module_name}: {e}")
    except AttributeError:
        raise AttributeError(f"Class {class_name} not found in {module_name}")
    except ValueError as e:
        print(e)
