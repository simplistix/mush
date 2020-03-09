from typing import NewType, Union, Hashable, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context
    from .requirements import Requirement

ResourceKey = NewType('ResourceKey', Union[Hashable, Callable])
ResourceValue = NewType('ResourceValue', Any)
ResourceResolver = Callable[['Context', Any], ResourceValue]
RequirementResolver = Callable[['Context'], ResourceValue]
RequirementModifier = Callable[['Requirement'], 'Requirement']
