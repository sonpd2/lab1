from flask_admin.contrib.sqla import ModelView
from app import admin
from app import db
from app.models import User, Post, Task, Notification, Comment, Message
from flask_login import current_user
from flask_admin.menu import MenuLink

class MyModelAdminViewBase(ModelView):
    column_display_pk = True
    can_delete = True
    can_create = True
    can_export = True
    can_set_page_size = True
    can_view_details = True
    excluded_list_columns = ['password_hash']

    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.is_admin


admin.add_view(MyModelAdminViewBase(User, db.session))
admin.add_view(MyModelAdminViewBase(Post, db.session))
admin.add_view(MyModelAdminViewBase(Task, db.session))
admin.add_view(MyModelAdminViewBase(Notification, db.session))
admin.add_view(MyModelAdminViewBase(Comment, db.session))
admin.add_view(MyModelAdminViewBase(Message, db.session))

admin.add_link(MenuLink(name='Application', category='', url="/"))
admin.add_link(MenuLink(name='Logout', category='', url="/auth/logout"))
