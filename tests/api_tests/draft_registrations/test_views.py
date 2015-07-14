import mock
from nose.tools import *  # flake8: noqa

from api.base.settings.defaults import API_BASE

from tests.base import ApiTestCase, fake
from api.base.utils import token_creator
from website.project.model import ensure_schemas
from tests.factories import UserFactory, ProjectFactory, RegistrationFactory, DraftRegistrationFactory


class TestDraftRegistrationList(ApiTestCase):
    def setUp(self):
        super(TestDraftRegistrationList, self).setUp()
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
        self.public_draft = DraftRegistrationFactory(branched_from=self.public_project, initiator=self.user)

        self.private_project = ProjectFactory(creator=self.user, is_public=False)
        self.private_draft = DraftRegistrationFactory(branched_from=self.private_project, initiator=self.user)

        self.url = '/{}draft_registrations/'.format(API_BASE)

    def test_return_draft_registration_list_logged_out(self):
        res = self.app.get(self.url, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_return_draft_registration_list_logged_in_contributor(self):
        res = self.app.get(self.url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 2)

    def test_return_draft_registration_list_logged_in_non_contributor(self):
        res = self.app.get(self.url, auth=self.basic_auth_two)
        assert_equal(len(res.json['data']), 0)
        assert_equal(res.status_code, 200)


class TestDraftRegistrationUpdate(ApiTestCase):

    def setUp(self):
        super(TestDraftRegistrationUpdate, self).setUp()
        ensure_schemas()
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

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.private_project)
        self.private_url = '/{}draft_registrations/{}/'.format(API_BASE, self.private_draft._id)

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.public_project)
        self.public_url = '/{}draft_registrations/{}/'.format(API_BASE, self.public_draft._id)

        self.schema_name = 'OSF-Standard Pre-Data Collection Registration'
        self.registration_metadata = "{'Have you looked at the data?': 'No'}"
        self.schema_version = 1

    def test_update_node_that_is_not_registration_draft(self):
        url = '/{}draft_registrations/{}/'.format(API_BASE, self.private_project)
        res = self.app.put(url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_update_node_that_does_not_exist(self):
        url = '/{}draft_registrations/{}/'.format(API_BASE, '12345')
        res = self.app.put(url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_update_public_registration_draft_logged_out(self):
        res = self.app.put(self.public_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_public_registration_draft_logged_in(self):
        res = self.app.put(self.public_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 200)
        source = res.json['data']['branched_from']
        metadata = res.json['data']['registration_metadata']
        registration_schema = res.json['data']['registration_schema']
        assert_equal(source, self.public_project._id)
        assert_equal(metadata, self.registration_metadata)
        assert_not_equal(registration_schema, None)
        assert_equal(registration_schema, self.schema_name)

        res = self.app.put(self.public_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_private_registration_draft_logged_out(self):
        res = self.app.put(self.private_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_private_registration_draft_logged_in_contributor(self):
        res = self.app.put(self.private_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 200)
        source = res.json['data']['branched_from']
        metadata = res.json['data']['registration_metadata']
        registration_schema = res.json['data']['registration_schema']
        assert_equal(source, self.private_project._id)
        assert_equal(metadata, self.registration_metadata)
        assert_not_equal(registration_schema, None)
        assert_equal(registration_schema, self.schema_name)

    def test_update_private_registration_draft_logged_in_non_contributor(self):
        res = self.app.put(self.private_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_registration_draft_logged_in_read_only_contributor(self):
        self.private_draft.add_contributor(self.user_two, permissions=['read'])
        res = self.app.put(self.private_url, {
            'schema_name': self.schema_name,
            'registration_metadata': self.registration_metadata,
            'schema_version': self.schema_version,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestDraftRegistrationPartialUpdate(ApiTestCase):

    def setUp(self):
        super(TestDraftRegistrationPartialUpdate, self).setUp()
        ensure_schemas()
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

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.private_project)
        self.private_url = '/{}draft_registrations/{}/'.format(API_BASE, self.private_draft._id)

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.public_project)
        self.public_url = '/{}draft_registrations/{}/'.format(API_BASE, self.public_draft._id)

        self.schema_name = 'OSF-Standard Pre-Data Collection Registration'
        self.registration_metadata = "{'Have you looked at the data?': 'No'}"
        self.schema_version = 1

    def test_partial_update_node_that_is_not_registration_draft(self):
        url = '/{}draft_registrations/{}/'.format(API_BASE, self.private_project)
        res = self.app.patch(url, {
            'self.schema_name': self.schema_name,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_partial_update_node_that_does_not_exist(self):
        url = '/{}draft_registrations/{}/'.format(API_BASE, '12345')
        res = self.app.patch(url, {
            'self.schema_name': self.schema_name,
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    # TODO Handle schema version does not exist
    def test_partial_update_schema_version_does_not_exist(self):
        res = self.app.patch(self.public_url, {
            'schema_name': self.schema_name,
            'schema_version': 2
        }, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_partial_update_registration_schema_public_draft_registration_logged_in(self):
        res = self.app.patch(self.public_url, {
            'schema_name': self.schema_name,
        }, auth=self.basic_auth, expect_errors=True)
        registration_schema = res.json['data']['registration_schema']
        assert_equal(registration_schema, self.schema_name)
        assert_equal(res.status_code, 200)

        res = self.app.patch(self.public_url, {
            'schema_name': self.schema_name,
            'schema_version': self.schema_version
        }, auth=self.basic_auth, expect_errors=True)
        registration_schema = res.json['data']['registration_schema']
        assert_equal(registration_schema, self.schema_name)
        assert_equal(res.status_code, 200)

    def test_partial_update_public_draft_registration_logged_out(self):
        res = self.app.patch(self.public_url, {
            'schema_name': self.schema_name,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_public_draft_registration_logged_in(self):
        res = self.app.patch(self.public_url, {
            'registration_metadata': self.registration_metadata,
        }, auth=self.basic_auth, expect_errors=True)
        registration_metadata = res.json['data']['registration_metadata']
        assert_equal(registration_metadata, self.registration_metadata)
        assert_equal(res.status_code, 200)

        res = self.app.patch(self.public_url, {
             'registration_metadata': self.registration_metadata,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_registration_draft_logged_out(self):
        res = self.app.patch(self.private_url, {
             'registration_metadata': self.registration_metadata,
        }, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_registration_draft_logged_in_contributor(self):
        res = self.app.patch(self.private_url, {
            'registration_metadata': self.registration_metadata,
        }, auth=self.basic_auth)
        registration_metadata = res.json['data']['registration_metadata']
        assert_equal(registration_metadata, self.registration_metadata)
        assert_equal(res.status_code, 200)

    def test_partial_update_private_registration_draft_logged_in_non_contributor(self):
        res = self.app.patch(self.private_url, {
            'registration_metadata': self.registration_metadata,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_registration_draft_logged_in_read_only_contributor(self):
        self.private_draft.add_contributor(self.user_two, permissions=['read'])
        res = self.app.patch(self.private_url, {
            'registration_metadata': self.registration_metadata,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestDeleteDraftRegistration(ApiTestCase):

    def setUp(self):
        super(TestDeleteDraftRegistration, self).setUp()
        ensure_schemas()
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

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.private_project)
        self.private_url = '/{}draft_registrations/{}/'.format(API_BASE, self.private_draft._id)

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.public_project)
        self.public_url = '/{}draft_registrations/{}/'.format(API_BASE, self.public_draft._id)


    def test_delete_node_that_is_not_registration_draft(self):
        url = '/{}draft_registrations/{}/'.format(API_BASE, self.private_project)
        res = self.app.delete(url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_delete_node_that_does_not_exist(self):
        url = '/{}draft_ registrations/{}/'.format(API_BASE, '12345')
        res = self.app.delete(url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_delete_public_draft_registration_logged_out(self):
        res = self.app.delete(self.public_url, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_delete_public_draft_registration_logged_in(self):
        res = self.app.patch(self.public_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

        assert_equal(self.public_draft.is_deleted, False)
        res = self.app.delete(self.public_url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 204)
        assert_equal(self.public_draft.is_deleted, True)

    def test_delete_private_registration_draft_logged_out(self):
        res = self.app.delete(self.private_url, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_delete_private_registration_draft_logged_in_contributor(self):
        assert_equal(self.private_draft.is_deleted, False)
        res = self.app.delete(self.private_url, auth=self.basic_auth)
        assert_equal(res.status_code, 204)
        assert_equal(self.private_draft.is_deleted, True)

    def test_delete_private_registration_draft_logged_in_non_contributor(self):
        res = self.app.delete(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_delete_private_registration_draft_logged_in_read_only_contributor(self):
        self.private_draft.add_contributor(self.user_two, permissions=['read'])
        res = self.app.delete(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestRegistrationCreate(ApiTestCase):
    def setUp(self):
        ensure_schemas()
        super(TestRegistrationCreate, self).setUp()
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
        self.public_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.public_project)
        self.public_url = '/{}draft_registrations/'.format(API_BASE)
        self.public_payload = {'draft_id': self.public_draft._id}

        self.private_project = ProjectFactory(creator=self.user, is_private=True)
        self.private_draft = DraftRegistrationFactory(initiator=self.user, branched_from=self.private_project)
        self.private_url = '/{}draft_registrations/'.format(API_BASE)
        self.private_payload = {'draft_id': self.private_draft._id}


        self.registration = RegistrationFactory(project=self.public_project)

    def test_create_registration_from_node(self):
        url = '/{}draft_registrations/'.format(API_BASE)
        res = self.app.post(url, {'draft_id': self.public_project._id}, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_create_registration_from_fake_node(self):
        url = '/{}draft_registrations/'.format(API_BASE)
        res = self.app.post(url, {'draft_id': '12345'}, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_create_registration_from_registration(self):
        url = '/{}draft_registrations/'.format(API_BASE)
        res = self.app.post(url, {'draft_id':  self.registration._id}, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_create_public_registration_logged_out(self):
        res = self.app.post(self.public_url, self.public_payload, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_public_registration_logged_in(self):
        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth, expect_errors=True)
        token_url = res.json['data']['links']['confirm_register']
        assert_equal(res.status_code, 202)

        res = self.app.post(token_url, self.public_payload, auth=self.basic_auth, expect_errors = True)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], self.public_draft.title)
        assert_equal(res.json['data']['properties']['registration'], True)

    def test_create_registration_from_deleted_draft(self):
        self.public_draft.is_deleted = True
        self.public_draft.save()
        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_create_registration_with_token_from_deleted_draft(self):
        self.public_draft.is_deleted = True
        self.public_draft.save()
        token = token_creator(self.private_draft._id, self.user._id)
        url = '/{}draft_registrations/{}/'.format(API_BASE, token)
        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_invalid_token_create_registration(self):
        res = self.app.post(self.private_url, self.private_payload, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 202)
        token_url = self.private_url + "12345/"

        res = self.app.post(token_url, self.private_payload, auth=self.basic_auth, expect_errors = True)
        assert_equal(res.status_code, 400)
        assert_equal(res.json["non_field_errors"][0], "Incorrect token.")

    def test_create_private_registration_logged_out(self):
        res = self.app.post(self.private_url, self.private_payload, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_public_registration_logged_out_with_token(self):
        token = token_creator(self.public_draft._id, self.user._id)
        url = '/{}draft_registrations/{}/'.format(API_BASE, token)
        res = self.app.post(url, self.public_payload, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_private_registration_logged_out_with_token(self):
        token = token_creator(self.private_draft._id, self.user._id)
        url = '/{}draft_registrations/{}/'.format(API_BASE, token)
        res = self.app.post(url, self.private_payload, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_private_registration_logged_in_contributor(self):
        res = self.app.post(self.private_url, self.private_payload, auth=self.basic_auth, expect_errors=True)
        token_url = res.json['data']['links']['confirm_register']
        assert_equal(res.status_code, 202)

        assert_equal(self.private_draft.is_registration, False)
        res = self.app.post(token_url, self.private_payload, auth=self.basic_auth, expect_errors = True)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], self.private_draft.title)
        assert_equal(res.json['data']['properties']['registration'], True)

    def test_create_private_registration_logged_in_non_contributor(self):
        res = self.app.post(self.private_url, self.private_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_private_registration_logged_in_read_only_contributor(self):
        self.private_draft.add_contributor(self.user_two, permissions = ['read'])
        res = self.app.post(self.private_url, self.private_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)





