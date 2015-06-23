import mock
from nose.tools import *  # flake8: noqa

from api.base.settings.defaults import API_BASE

from tests.base import ApiTestCase, fake
from tests.factories import UserFactory, ProjectFactory, FolderFactory, RegistrationFactory, DashboardFactory, NodeFactory

class TestRegistrationList(ApiTestCase):
    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)

        self.user_two = UserFactory.build()
        self.user_two.set_password(password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, password)

        self.project = ProjectFactory(is_public=False, creator=self.user)
        self.registration_project = RegistrationFactory(creator=self.user, project=self.project)

        self.project_two = ProjectFactory(is_public=False, creator=self.user)
        self.registration_project_two = RegistrationFactory(creator=self.user, project=self.project_two)
        self.project_two.is_deleted = True
        self.registration_project_two.is_deleted = True
        self.project_two.save()
        self.registration_project_two.save()

        self.project_three = ProjectFactory(is_public=True, creator=self.user_two)
        self.registration_project_three = RegistrationFactory(creator=self.user_two, project=self.project_three)

        self.project_four = ProjectFactory(is_public=False, creator=self.user_two)
        self.registration_project_four = RegistrationFactory(creator=self.user_two, project=self.project_four)

        self.url = '/{}registrations/'.format(API_BASE)
        # TODO include registration drafts!  List all registrations should include drafts as well as reg

    def test_list_all_registrations(self):
        res = self.app.get(self.url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        ids = [each['id'] for each in res.json['data']]
        assert_in(self.registration_project._id, ids)
        assert_not_in(self.registration_project_two._id, ids)
        assert_in(self.registration_project_three._id, ids)
        assert_not_in(self.registration_project_four._id, ids)

class TestRegistrationDetail(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)

        self.user_two = UserFactory.build()
        self.user_two.set_password(password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, password)

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_registration = RegistrationFactory(creator=self.user, project=self.public_project)
        self.public_url = '/{}registrations/{}'.format(API_BASE, self.public_registration._id)

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_registration = RegistrationFactory(creator=self.user, project=self.private_project)
        self.private_url = '/{}registrations/{}'.format(API_BASE, self.private_registration._id)

        # TODO test getting registration details for registration DRAFTS

    def test_return_registration_detail_node_is_not_registration(self):
        url = '/{}registrations/{}'.format(API_BASE, self.public_project)
        res = self.app.get(url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 400)

    def test_return_registration_details_node_does_not_exist(self):
        url = '/{}registrations/{}'.format(API_BASE, '12345')
        res = self.app.get(url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_return_public_registration_details_logged_out(self):
        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.public_registration._id)
        # TODO assert registration's source?

    def test_return_public_registration_details_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.public_registration._id)

        res = self.app.get(self.public_url, auth=self.basic_auth_two)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.public_registration._id)
        # TODO assert registration's source?

    def test_return_private_registration_details_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_return_private_registration_details_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.private_registration._id)
        assert_equal(res.json['data']['description'], self.private_registration.description)

    def test_return_private_registration_details_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

class TestRegistrationUpdate(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)

        self.user_two = UserFactory.build()
        self.user_two.set_password(password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, password)

        #TODO ADD registration drafts to test.  User should only be able to update registration DRAFT, never registration.

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_registration = RegistrationFactory(creator=self.user, project=self.public_project)
        self.public_url = '/{}registrations/{}'.format(API_BASE, self.public_registration._id)

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_registration = RegistrationFactory(creator=self.user, project=self.private_project)
        self.private_url = '/{}registrations/{}'.format(API_BASE, self.private_registration._id)

        self.new_title = "Updated registration title"
        self.new_description = "Updated registration description"
        self.new_category = 'project'

    def test_update_node_that_is_not_registration_draft(self):
        url = '/{}registrations/{}'.format(API_BASE, self.private_project)
        res = self.app.put(url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 400)

    def test_update_registration(self):
        res = self.app.put(self.private_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_node_that_does_not_exist(self):
        url = '/{}registrations/{}'.format(API_BASE, '12345')
        res = self.app.put(url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_update_public_registration_draft_logged_out(self):
        res = self.app.put(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_public_registration_draft_logged_in(self):
        #TODO test updating public registration DRAFT, not registration
        res = self.app.put(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 200)

        res = self.app.put(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_private_registration_draft_logged_out(self):
        #TODO test updating private registration DRAFT, not registration
        res = self.app.put(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_private_registration_draft_logged_in_contributor(self):
        #TODO test updating private registration DRAFT, not registration
        res = self.app.put(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.public_registration._id)

    def test_update_private_registration_draft_logged_in_non_contributor(self):
        #TODO test updating private registration DRAFT, not registration
        res = self.app.put(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

class TestRegistrationPartialUpdate(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)

        self.user_two = UserFactory.build()
        self.user_two.set_password(password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, password)

        #TODO ADD registration drafts to test.  User should only be able to update registration DRAFT, never registration.

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_registration = RegistrationFactory(creator=self.user, project=self.public_project)
        self.public_url = '/{}registrations/{}'.format(API_BASE, self.public_registration._id)

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_registration = RegistrationFactory(creator=self.user, project=self.private_project)
        self.private_url = '/{}registrations/{}'.format(API_BASE, self.private_registration._id)

        self.new_title = "Updated registration title"

    def test_partial_update_node_that_is_not_registration_draft(self):
        url = '/{}registrations/{}'.format(API_BASE, self.private_project)
        res = self.app.patch(url, {
            'title': self.new_title,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 400)

    def test_partial_update_registration(self):
        res = self.app.patch(self.private_url, {
            'title': self.new_title,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_node_that_does_not_exist(self):
        url = '/{}registrations/{}'.format(API_BASE, '12345')
        res = self.app.patch(url, {
            'title': self.new_title,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_partial_update_public_registration_draft_logged_out(self):
        res = self.app.patch(self.public_url, {
            'title': self.new_title,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_public_registration_draft_logged_in(self):
        #TODO test updating public registration DRAFT, not registration
        res = self.app.patch(self.public_url, {
            'title': self.new_title,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 200)

        res = self.app.patch(self.public_url, {
            'title': self.new_title,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_registration_draft_logged_out(self):
        #TODO test updating private registration DRAFT, not registration
        res = self.app.patch(self.public_url, {
            'title': self.new_title,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_registration_draft_logged_in_contributor(self):
        #TODO test updating private registration DRAFT, not registration
        res = self.app.patch(self.public_url, {
            'title': self.new_title,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.public_registration._id)

    def test_partial_update_private_registration_draft_logged_in_non_contributor(self):
        #TODO test updating private registration DRAFT, not registration
        res = self.app.patch(self.public_url, {
            'title': self.new_title,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)



