"""
Role permission classes (service.md section 6.8).

These only answer "does this role exist in the caller's token". Object-level
rules (own internship, assigned supervisor, hidden objects returning 404) are
enforced by queryset filtering in each view, because an object the caller may
not see must look like it does not exist.
"""

from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """Base for role checks. Subclasses set `roles`."""

    roles = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in self.roles)


class IsStudent(HasRole):
    roles = ("STUDENT",)


class IsCompany(HasRole):
    roles = ("COMPANY",)


class IsSupervisor(HasRole):
    roles = ("SUPERVISOR",)


class IsUniversityAdmin(HasRole):
    roles = ("UNIVERSITY_ADMIN",)


class IsInternshipParticipant(HasRole):
    """Any role that can see internships at all (guests cannot)."""

    roles = ("STUDENT", "COMPANY", "SUPERVISOR", "UNIVERSITY_ADMIN")
