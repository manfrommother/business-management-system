# flake8: noqa
from sqladmin import ModelView
from app.db.models import Team, Department, TeamMember, TeamInvite, TeamNews


class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id, Team.name, Team.is_active, Team.created_at]
    column_searchable_list = [Team.name]
    column_sortable_list = [Team.name, Team.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Команда"
    name_plural = "Команды"
    icon = "fa-solid fa-users"


class DepartmentAdmin(ModelView, model=Department):
    column_list = [
        Department.id, Department.name, Department.team_id, 
        Department.parent_id, Department.head_user_id
    ]
    column_searchable_list = [Department.name]
    column_sortable_list = [Department.name]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Отдел"
    name_plural = "Отделы"
    icon = "fa-solid fa-building"


class TeamMemberAdmin(ModelView, model=TeamMember):
    column_list = [
        TeamMember.id, TeamMember.user_id, TeamMember.team_id, 
        TeamMember.department_id, TeamMember.role, TeamMember.is_active
    ]
    column_searchable_list = [TeamMember.user_id, TeamMember.role, TeamMember.job_title]
    column_sortable_list = [TeamMember.user_id, TeamMember.joined_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Участник Команды"
    name_plural = "Участники Команды"
    icon = "fa-solid fa-user-tie"


class TeamInviteAdmin(ModelView, model=TeamInvite):
    column_list = [
        TeamInvite.id, TeamInvite.code, TeamInvite.team_id, TeamInvite.email, 
        TeamInvite.role, TeamInvite.is_used, TeamInvite.expires_at
    ]
    column_searchable_list = [TeamInvite.code, TeamInvite.email]
    column_sortable_list = [TeamInvite.created_at, TeamInvite.expires_at]
    can_create = False  # Приглашения создаются через API
    can_edit = False
    can_delete = True
    can_view_details = True
    name = "Приглашение"
    name_plural = "Приглашения"
    icon = "fa-solid fa-envelope"


class TeamNewsAdmin(ModelView, model=TeamNews):
    column_list = [
        TeamNews.id, TeamNews.title, TeamNews.team_id, TeamNews.department_id, 
        TeamNews.created_by, TeamNews.is_pinned
    ]
    column_searchable_list = [TeamNews.title]
    column_sortable_list = [TeamNews.created_at, TeamNews.is_pinned]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Новость"
    name_plural = "Новости"
    icon = "fa-solid fa-newspaper" 