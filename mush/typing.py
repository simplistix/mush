from typing import NewType, Union, Hashable, Any, TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .declarations import Requirements, Return
    from .requirements import Requirement

RequirementType = Union['Requirement', type, str]
Requires = Union['Requirements',
                 RequirementType,
                 List[RequirementType],
                 Tuple[RequirementType, ...]]

ReturnType = Union[type, str]
Returns = Union['Return', ReturnType, List[ReturnType], Tuple[ReturnType, ...]]

Resource = NewType('Resource', Any)
Identifier = Hashable
