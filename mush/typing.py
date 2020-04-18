from typing import NewType, Union, Hashable, Callable, Any, TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .context import Context
    from .declarations import RequiresType, ReturnsType
    from .requirements import Requirement

RequirementType = Union['Requirement', type, str]
Requires = Union['RequiresType',
                 RequirementType,
                 List[RequirementType],
                 Tuple[RequirementType, ...]]

ReturnType = Union[type, str]
Returns = Union['ReturnsType', ReturnType, List[ReturnType], Tuple[ReturnType, ...]]

ResourceKey = Union[Hashable, Callable]
ResourceValue = NewType('ResourceValue', Any)
RequirementModifier = Callable[['Requirement'], 'Requirement']
