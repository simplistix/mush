from typing import NewType, Union, Hashable, Any, TYPE_CHECKING, List, Tuple, Type, _GenericAlias

if TYPE_CHECKING:
    from .declarations import RequirementsDeclaration, ReturnsDeclaration
    from .requirements import Requirement

Type_ = Union[type, Type, _GenericAlias]
Identifier = Hashable

RequirementType = Union['Requirement', Type_, Identifier]
Requires = Union['RequirementDeclaraction',
                 RequirementType,
                 List[RequirementType],
                 Tuple[RequirementType, ...]]

ReturnType = Union[Type_, str]
Returns = Union['ReturnsDeclaration', ReturnType]

Resource = NewType('Resource', Any)
