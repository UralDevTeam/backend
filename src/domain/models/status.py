from enum import Enum


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    VACATION = "vacation"
    SICK_LEAVE = "sickLeave"
