from apps.core.constants import GROUP_ADMINISTRATIVE_OFFICER
from apps.core.permissions import (
    CanManageOrOwnUser,
    CanManageUsers,
    CanViewOrSelfUser,
    CanViewUsers,
    IsAdministrativeOfficer,
    IsOwnerOrSuperUser,
    IsStaffUser,
    IsSuperUser,
    IsSuperUserOrAdministrativeOfficer,
)

__all__ = [
    'GROUP_ADMINISTRATIVE_OFFICER',
    'CanManageOrOwnUser',
    'CanManageUsers',
    'CanViewOrSelfUser',
    'CanViewUsers',
    'IsAdministrativeOfficer',
    'IsOwnerOrSuperUser',
    'IsStaffUser',
    'IsSuperUser',
    'IsSuperUserOrAdministrativeOfficer',
]
