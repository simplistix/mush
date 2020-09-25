from typing import NewType, Union, Hashable, Callable, Any, TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .context import Context
    from .declarations import Requirements, Return
    from .requirements import Requirement

RequirementType = Union['Requirement', type, str]
Requires = Union['Requirements',
                 RequirementType,
                 List[RequirementType],
                 Tuple[RequirementType, ...]]

ReturnType = Union[type, str]
Returns = Union['Return', ReturnType, List[ReturnType], Tuple[ReturnType, ...]]

ResourceValue = NewType('ResourceValue', Any)

