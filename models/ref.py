
INSTANCES_REGISTRY = {}

def register(cls, instance):
    instances = INSTANCES_REGISTRY.get(cls, [])
    instances.append(instance)
    INSTANCES_REGISTRY.update({cls: instances})


def deregister(cls, instance):
    instances = INSTANCES_REGISTRY.get(cls, [])
    instances.remove(instance)
    INSTANCES_REGISTRY.update({cls: instances})


def get_instances(cls):
    return INSTANCES_REGISTRY.get(cls, [])