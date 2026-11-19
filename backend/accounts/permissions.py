from rest_framework.permissions import BasePermission


class IsCorpusAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_corpus_admin)
