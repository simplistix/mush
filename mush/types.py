from typing import NewType, Union, Hashable, Callable, Any

ResourceKey = NewType('ResourceKey', Union[Hashable, Callable])
ResourceValue = NewType('ResourceValue', Any)
ResourceResolver = Callable[['Context', Any], ResourceValue]
RequirementResolver = Callable[['Context'], ResourceValue]
