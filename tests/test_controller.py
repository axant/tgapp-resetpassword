import tg
from tgext.pluggable import app_model
from .base import configure_app, create_app, flush_db_changes
from resetpassword import lib, model
import re
from tgext.mailer import get_mailer
find_urls = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


class ResetpasswordControllerTests(object):
    def setup(self):
        self.app = create_app(self.app_config, False)

    def test_index(self):
        resp = self.app.get('/')
        assert 'HELLO' in resp.text

    def test_resetpassword_form(self):
        resp = self.app.get('/resetpassword')

        assert 'name="email_address"' in resp.text
        assert 'action="/resetpassword/reset_request"' in resp.text

    def test_resetpassword_validation(self):
        resp = self.app.get('/resetpassword')
        form = resp.form
        assert form.action == '/resetpassword/reset_request', form.action

        form['email_address'] = 'email@email.it'
        resp = form.submit()

        assert '<span id="email_address:error">User not found</span>' in resp.text, resp.text

    def test_resetpassword_validation_empty(self):
        resp = self.app.get('/resetpassword')
        form = resp.form
        assert form.action == '/resetpassword/reset_request', form.action

        form['email_address'] = ''
        resp = form.submit()

        assert '<span id="email_address:error">Enter a value</span>' in resp.text, resp.text

    def test_resetpassword_reset_request(self):
        user = app_model.User(
            email_address='email@email.it',
            user_name='test',
            display_name='Test',
            password='eh'
        )
        app_model.DBSession.add(user)
        old_password = user.password
        flush_db_changes()

        resp = self.app.get('/resetpassword')
        form = resp.form
        assert form.action == '/resetpassword/reset_request', form.action

        form['email_address'] = 'email@email.it'
        resp = form.submit()
        ctx = resp.req.environ['paste.testing_variables']
        mailer = get_mailer(ctx['req'])

        resp = resp.follow()

        assert 'Password reset request sent' in resp.text, resp.text

        assert len(mailer.outbox) == 1, mailer.outbox
        url = find_urls.findall(mailer.outbox[0].body)[0]
        resp = self.app.get(url)
        form = resp.form
        form['password'] = 'alfa'
        form['password_confirm'] = 'alfa'
        resp = form.submit()
        assert 'Password%20changed%20successfully' in resp.headers['Set-Cookie']
        user = app_model.DBSession.query(app_model.User).all()[0]
        assert old_password != user.password
        resp = resp.follow()
        assert 'HELLO' in resp.text, resp.text

class TestResetpasswordControllerSQLA(ResetpasswordControllerTests):
    @classmethod
    def setupClass(cls):
        cls.app_config = configure_app('sqlalchemy')


#class TestResetpasswordControllerMing(ResetpasswordControllerTests):
#    @classmethod
#    def setupClass(cls):
#        cls.app_config = configure_app('ming')

