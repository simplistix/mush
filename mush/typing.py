from typing import NewType, Union, Hashable, Any, TYPE_CHECKING, List, Tuple, Type, _GenericAlias

if TYPE_CHECKING:
    from .declarations import Requirements, Return
    from .requirements import Requirement

Type_ = Union[type, Type, _GenericAlias]
Identifier = Hashable

RequirementType = Union['Requirement', Type_, str]
Requires = Union['Requirements',
                 RequirementType,
                 List[RequirementType],
                 Tuple[RequirementType, ...]]

ReturnType = Union[Type_, str]
Returns = Union['Return', ReturnType, List[ReturnType], Tuple[ReturnType, ...]]

Resource = NewType('Resource', Any)
