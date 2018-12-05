import re
from resetpassword import model

from tgext.pluggable import app_model
from tgext.mailer import get_mailer
from .base import configure_app, create_app, flush_db_changes


URLS_RE = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


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

    def test_resetpassword_fake_url(self):
        resp = self.app.get('/resetpassword/change_password')
        resp = resp.follow()

        assert '<div class="error">Invalid password reset request</div>' in resp.text

    def test_resetpassword_reset_request(self):
        user = app_model.User(
            email_address='email@email.it',
            user_name='test',
            display_name='Test',
            password='eh'
        )
        try:
            app_model.DBSession.add(user)
        except AttributeError:
            # Ming DBSession doesn't have/require .add
            pass
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
        url = URLS_RE.findall(mailer.outbox[0].body)[0]
        resp = self.app.get(url)
        form = resp.form
        form['password'] = 'alfa'
        form['password_confirm'] = 'alfa'
        resp = form.submit()
        assert 'Password%20changed%20successfully' in resp.headers['Set-Cookie']
        _, users = model.provider.query(app_model.User)
        assert old_password != users[0].password
        resp = resp.follow()
        assert 'HELLO' in resp.text, resp.text

    def test_resetpassword_old_request(self):
        user = app_model.User(
            email_address='email@email.it',
            user_name='test',
            display_name='Test',
            password='eh'
        )
        try:
            app_model.DBSession.add(user)
        except AttributeError:
            # Ming DBSession doesn't have/require .add
            pass
        old_password = user.password
        flush_db_changes()

        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        old_date = datetime.utcnow() - relativedelta(years=3)
        import tg
        secret = tg.config.get('session.secret', tg.config.get('beaker.session.secret'))
        from itsdangerous import URLSafeSerializer
        serializer = URLSafeSerializer(secret)
        serialized_data = serializer.dumps(dict(request_date=old_date.strftime('%m/%d/%Y %H:%M'),
                                                email_address='email@email.it', password_frag='eh',
                                                redirect_to='/'))
        new_url='http://localhost/resetpassword/change_password/?data='+serialized_data
        resp = self.app.get(new_url)
        form = resp.form
        form['password'] = 'alfa'
        form['password_confirm'] = 'alfa'
        resp = form.submit()
        assert 'Password%20reset%20request%20timed%20out' in resp.headers['Set-Cookie']


    def test_resetpassword_bad_frag_password(self):
        user = app_model.User(
            email_address='email@email.it',
            user_name='test',
            display_name='Test',
            password='eh'
        )
        try:
            app_model.DBSession.add(user)
        except AttributeError:
            # Ming DBSession doesn't have/require .add
            pass
        old_password = user.password
        flush_db_changes()

        from datetime import datetime
        import tg
        secret = tg.config.get('session.secret', tg.config.get('beaker.session.secret'))
        from itsdangerous import URLSafeSerializer
        serializer = URLSafeSerializer(secret)
        serialized_data = serializer.dumps(dict(request_date=datetime.utcnow().strftime('%m/%d/%Y %H:%M'),
                                                email_address='email@email.it', password_frag='ops',
                                                redirect_to='/'))
        new_url = 'http://localhost/resetpassword/change_password/?data=' + serialized_data
        resp = self.app.get(new_url)
        form = resp.form
        form['password'] = 'alfa'
        form['password_confirm'] = 'alfa'
        resp = form.submit()
        assert 'Invalid%20password%20reset%20request' in resp.headers['Set-Cookie']


class TestResetpasswordControllerSQLA(ResetpasswordControllerTests):
    @classmethod
    def setupClass(cls):
        cls.app_config = configure_app('sqlalchemy')


class TestResetpasswordControllerMing(ResetpasswordControllerTests):
    @classmethod
    def setupClass(cls):
        cls.app_config = configure_app('ming')


class ResetpasswordControllerWithoutFormsTests(object):
    def setup(self):
        self.app = create_app(self.app_config, False)

    def test_index(self):
        resp = self.app.get('/')
        assert 'HELLO' in resp.text

    def test_resetpassword_form(self):
        resp = self.app.get('/resetpassword')

        assert 'name="email_address"' in resp.text
        assert 'action="/resetpassword/reset_request"' in resp.text


class TestResetpasswordControllerWithoutForm(ResetpasswordControllerWithoutFormsTests):
    @classmethod
    def setupClass(cls):
        cls.app_config = configure_app('sqlalchemy', create_form=False)