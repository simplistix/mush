def r(base, **attrs):
    """
    helper for returning Requirement subclasses with extra attributes
    """
    base.__dict__.update(attrs)
    return base
