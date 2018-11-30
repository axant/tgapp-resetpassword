# coding=utf-8
from __future__ import unicode_literals

from tw2.core import EmailValidator, ValidationError
from tgext.pluggable import app_model
from resetpassword import model


class RegisteredUserValidator(EmailValidator):
    def _validate_python(self, value, state=None):
        count, _ = model.provider.query(app_model.User,
                                        filters=dict(email_address=value))
        if count < 1:
            raise ValidationError(self.msgs.get('user_not_found', 'User not found'),
                                  self)


