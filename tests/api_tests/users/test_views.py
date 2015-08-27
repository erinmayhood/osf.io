# -*- coding: utf-8 -*-
from nose.tools import *  # flake8: noqa

from website.models import Node
from tests.base import ApiTestCase
from api.base.settings.defaults import API_BASE
from tests.factories import ProjectFactory, FolderFactory, DashboardFactory, AuthUserFactory
from website.util.sanitize import strip_html


class TestUsers(ApiTestCase):

    def setUp(self):
        super(TestUsers, self).setUp()
        self.user_one = AuthUserFactory()
        self.user_two = AuthUserFactory()

    def tearDown(self):
        super(TestUsers, self).tearDown()

    def test_returns_200(self):
        res = self.app.get('/{}users/'.format(API_BASE))
        assert_equal(res.status_code, 200)

    def test_find_user_in_users(self):
        url = "/{}users/".format(API_BASE)

        res = self.app.get(url)
        user_son = res.json['data']

        ids = [each['id'] for each in user_son]
        assert_in(self.user_two._id, ids)

    def test_all_users_in_users(self):
        url = "/{}users/".format(API_BASE)

        res = self.app.get(url)
        user_son = res.json['data']

        ids = [each['id'] for each in user_son]
        assert_in(self.user_one._id, ids)
        assert_in(self.user_two._id, ids)

    def test_find_multiple_in_users(self):
        url = "/{}users/?filter[fullname]=fred".format(API_BASE)

        res = self.app.get(url)
        user_json = res.json['data']
        ids = [each['id'] for each in user_json]
        assert_in(self.user_one._id, ids)
        assert_in(self.user_two._id, ids)

    def test_find_single_user_in_users(self):
        url = "/{}users/?filter[fullname]=my".format(API_BASE)
        self.user_one.fullname = 'My Mom'
        self.user_one.save()
        res = self.app.get(url)
        user_json = res.json['data']
        ids = [each['id'] for each in user_json]
        assert_in(self.user_one._id, ids)
        assert_not_in(self.user_two._id, ids)

    def test_find_no_user_in_users(self):
        url = "/{}users/?filter[fullname]=NotMyMom".format(API_BASE)
        res = self.app.get(url)
        user_json = res.json['data']
        ids = [each['id'] for each in user_json]
        assert_not_in(self.user_one._id, ids)
        assert_not_in(self.user_two._id, ids)


class TestUserDetail(ApiTestCase):

    def setUp(self):
        super(TestUserDetail, self).setUp()
        self.user_one = AuthUserFactory()
        self.user_one.social['twitter'] = 'howtopizza'
        self.user_one.save()

        self.user_two = AuthUserFactory()

    def tearDown(self):
        super(TestUserDetail, self).tearDown()

    def test_gets_200(self):
        url = "/{}users/{}/".format(API_BASE, self.user_one._id)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

    def test_get_correct_pk_user(self):
        url = "/{}users/{}/".format(API_BASE, self.user_one._id)
        res = self.app.get(url)
        user_json = res.json['data']
        assert_equal(user_json['fullname'], self.user_one.fullname)
        assert_equal(user_json['twitter'], 'howtopizza')

    def test_get_incorrect_pk_user_logged_in(self):
        url = "/{}users/{}/".format(API_BASE, self.user_two._id)
        res = self.app.get(url)
        user_json = res.json['data']
        assert_not_equal(user_json['fullname'], self.user_one.fullname)

    def test_get_incorrect_pk_user_not_logged_in(self):
        url = "/{}users/{}/".format(API_BASE, self.user_two._id)
        res = self.app.get(url, auth=self.user_one.auth)
        user_json = res.json['data']
        assert_not_equal(user_json['fullname'], self.user_one.fullname)
        assert_equal(user_json['fullname'], self.user_two.fullname)


class TestUserNodes(ApiTestCase):

    def setUp(self):
        super(TestUserNodes, self).setUp()
        self.user_one = AuthUserFactory()
        self.user_one.social['twitter'] = 'howtopizza'
        self.user_one.save()

        self.user_two = AuthUserFactory()
        self.public_project_user_one = ProjectFactory(title="Public Project User One",
                                                      is_public=True,
                                                      creator=self.user_one)
        self.private_project_user_one = ProjectFactory(title="Private Project User One",
                                                       is_public=False,
                                                       creator=self.user_one)
        self.public_project_user_two = ProjectFactory(title="Public Project User Two",
                                                      is_public=True,
                                                      creator=self.user_two)
        self.private_project_user_two = ProjectFactory(title="Private Project User Two",
                                                       is_public=False,
                                                       creator=self.user_two)
        self.deleted_project_user_one = FolderFactory(title="Deleted Project User One",
                                                      is_public=False,
                                                      creator=self.user_one,
                                                      is_deleted=True)
        self.folder = FolderFactory()
        self.deleted_folder = FolderFactory(title="Deleted Folder User One",
                                            is_public=False,
                                            creator=self.user_one,
                                            is_deleted=True)
        self.dashboard = DashboardFactory()

    def tearDown(self):
        super(TestUserNodes, self).tearDown()

    def test_authorized_in_gets_200(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)

    def test_anonymous_gets_200(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

    def test_get_projects_logged_in(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.public_project_user_one._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.public_project_user_two._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)

    def test_get_projects_not_logged_in(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.public_project_user_one._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.public_project_user_two._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)

    def test_get_projects_logged_in_as_different_user(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_two._id)
        res = self.app.get(url, auth=self.user_one.auth)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.public_project_user_two._id, ids)
        assert_not_in(self.public_project_user_one._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)


class TestUserRoutesNodeRoutes(ApiTestCase):

    def setUp(self):
        super(TestUserRoutesNodeRoutes, self).setUp()
        self.user_one = AuthUserFactory()
        self.user_one.social['twitter'] = 'howtopizza'
        self.user_two = AuthUserFactory()
        self.public_project_user_one = ProjectFactory(title="Public Project User One", is_public=True, creator=self.user_one)
        self.private_project_user_one = ProjectFactory(title="Private Project User One", is_public=False, creator=self.user_one)
        self.public_project_user_two = ProjectFactory(title="Public Project User Two", is_public=True, creator=self.user_two)
        self.private_project_user_two = ProjectFactory(title="Private Project User Two", is_public=False, creator=self.user_two)
        self.deleted_project_user_one = FolderFactory(title="Deleted Project User One", is_public=False, creator=self.user_one, is_deleted=True)

        self.folder = FolderFactory()
        self.deleted_folder = FolderFactory(title="Deleted Folder User One", is_public=False, creator=self.user_one, is_deleted=True)
        self.dashboard = DashboardFactory()

    def tearDown(self):
        super(TestUserRoutesNodeRoutes, self).tearDown()
        Node.remove()

    def test_get_200_path_users_me_userone_logged_in(self):
        url = "/{}users/me/".format(API_BASE)
        res = self.app.get(url, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)

    def test_get_200_path_users_me_usertwo_logged_in(self):
        url = "/{}users/me/".format(API_BASE)
        res = self.app.get(url, auth=self.user_two.auth)
        assert_equal(res.status_code, 200)

    def test_get_403_path_users_me_no_user(self):
        # TODO: change expected exception from 403 to 401 for unauthorized users

        url = "/{}users/me/".format(API_BASE)
        res = self.app.get(url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_get_404_path_users_user_id_me_user_logged_in(self):
        url = "/{}users/{}/me/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_users_user_id_me_no_user(self):
        url = "/{}users/{}/me/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_users_user_id_me_unauthorized_user(self):
        url = "/{}users/{}/me/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_two.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_200_path_users_user_id_user_logged_in(self):
        url = "/{}users/{}/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)

    def test_get_200_path_users_user_id_no_user(self):
        url = "/{}users/{}/".format(API_BASE, self.user_two._id)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

    def test_get_200_path_users_user_id_unauthorized_user(self):
        url = "/{}users/{}/".format(API_BASE, self.user_two._id)
        res = self.app.get(url, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['id'], self.user_two._id)

    def test_get_200_path_users_me_nodes_user_logged_in(self):
        url = "/{}users/me/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)

        ids = {each['id'] for each in res.json['data']}
        assert_in(self.public_project_user_one._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.public_project_user_two._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)

    def test_get_403_path_users_me_nodes_no_user(self):
        # TODO: change expected exception from 403 to 401 for unauthorized users

        url = "/{}users/me/nodes/".format(API_BASE)
        res = self.app.get(url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_get_200_path_users_user_id_nodes_user_logged_in(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)

        ids = {each['id'] for each in res.json['data']}
        assert_in(self.public_project_user_one._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.public_project_user_two._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)

    def test_get_200_path_users_user_id_nodes_no_user(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

        # an anonymous/unauthorized user can only see the public projects user_one contributes to.
        ids = {each['id'] for each in res.json['data']}
        assert_in(self.public_project_user_one._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.public_project_user_two._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)

    def test_get_200_path_users_user_id_nodes_unauthorized_user(self):
        url = "/{}users/{}/nodes/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_two.auth)
        assert_equal(res.status_code, 200)

        # an anonymous/unauthorized user can only see the public projects user_one contributes to.
        ids = {each['id'] for each in res.json['data']}
        assert_in(self.public_project_user_one._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.public_project_user_two._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.deleted_folder._id, ids)
        assert_not_in(self.deleted_project_user_one._id, ids)

    def test_get_404_path_users_user_id_nodes_me_user_logged_in(self):
        url = "/{}users/{}/nodes/me/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_users_user_id_nodes_me_unauthorized_user(self):
        url = "/{}users/{}/nodes/me/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_two.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_users_user_id_nodes_me_no_user(self):
        url = "/{}users/{}/nodes/me/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_nodes_me_user_logged_in(self):
        url = "/{}nodes/me/".format(API_BASE)
        res = self.app.get(url, auth=self.user_one.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_nodes_me_no_user(self):
        url = "/{}nodes/me/".format(API_BASE)
        res = self.app.get(url, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_nodes_user_id_user_logged_in(self):
        url = "/{}nodes/{}/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_one.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_nodes_user_id_unauthorized_user(self):
        url = "/{}nodes/{}/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, auth=self.user_two.auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_get_404_path_nodes_user_id_no_user(self):
        url = "/{}nodes/{}/".format(API_BASE, self.user_one._id)
        res = self.app.get(url, expect_errors=True)
        assert_equal(res.status_code, 404)


class TestUserUpdate(ApiTestCase):

    def setUp(self):
        super(TestUserUpdate, self).setUp()

        self.user_one = AuthUserFactory.build(
            fullname='Martin Luther King Jr.',
            given_name='Martin',
            family_name='King',
            suffix='Jr.',
            social=dict(
                github='userOneGithub',
                scholar='userOneScholar',
                personal='http://www.useronepersonalwebsite.com',
                twitter='userOneTwitter',
                linkedIn='userOneLinkedIn',
                impactStory='userOneImpactStory',
                orcid='userOneOrcid',
                researcherId='userOneResearcherId'
            )
        )
        self.user_one.save()

        self.user_one_url = "/v2/users/{}/".format(self.user_one._id)

        self.user_two = AuthUserFactory()
        self.user_two.save()

        self.new_user_one_data = {
            'id': self.user_one._id,
            'fullname': 'el-Hajj Malik el-Shabazz',
            'given_name': 'Malcolm',
            'middle_names': 'Malik el-Shabazz',
            'family_name': 'X',
            'suffix': 'Sr.',
            'gitHub': 'newGitHub',
            'scholar': 'newScholar',
            'personal_website': 'http://www.newpersonalwebsite.com',
            'twitter': 'http://www.newpersonalwebsite.com',
            'linkedIn': 'newLinkedIn',
            'impactStory': 'newImpactStory',
            'orcid': 'newOrcid',
            'researcherId': 'newResearcherId',
        }

    def tearDown(self):
        super(TestUserUpdate, self).tearDown()

    def test_patch_user_logged_out(self):
        res = self.app.patch_json(self.user_one_url, {
            'fullname': self.new_user_one_data['fullname'],
        }, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_patch_user_without_required_field(self):
        # PATCH does not require required fields
        res = self.app.patch_json(self.user_one_url, {
            'family_name': self.new_user_one_data['family_name'],
        }, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['family_name'], self.new_user_one_data['family_name'])
        self.user_one.reload()
        assert_equal(self.user_one.family_name, self.new_user_one_data['family_name'])

    def test_put_user_without_required_field(self):
        # PUT requires all required fields
        res = self.app.put_json(self.user_one_url, {
            'family_name': self.new_user_one_data['family_name'],
        }, auth=self.user_one.auth, expect_errors=True)
        assert_equal(res.status_code, 400)

    def test_partial_patch_user_logged_in(self):
        # Test to make sure new fields are patched and old fields stay the same
        res = self.app.patch_json(self.user_one_url, {
            'id': self.user_one._id,
            'fullname': 'new_fullname',
            'gitHub': 'even_newer_github',
            'suffix': 'The Millionth'
        }, auth=self.user_one.auth)
        self.user_one.reload()
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['fullname'], 'new_fullname')
        assert_equal(res.json['data']['suffix'], 'The Millionth')
        assert_equal(res.json['data']['gitHub'], 'even_newer_github')
        assert_equal(res.json['data']['given_name'], self.user_one.given_name)
        assert_equal(res.json['data']['middle_names'], self.user_one.middle_names)
        assert_equal(res.json['data']['family_name'], self.user_one.family_name)
        assert_equal(res.json['data']['personal_website'], self.user_one.social['personal'])
        assert_equal(res.json['data']['twitter'], self.user_one.social['twitter'])
        assert_equal(res.json['data']['linkedIn'], self.user_one.social['linkedIn'])
        assert_equal(res.json['data']['impactStory'], self.user_one.social['impactStory'])
        assert_equal(res.json['data']['orcid'], self.user_one.social['orcid'])
        assert_equal(res.json['data']['researcherId'], self.user_one.social['researcherId'])
        assert_equal(self.user_one.fullname, 'new_fullname')
        assert_equal(self.user_one.suffix, 'The Millionth')
        assert_equal(self.user_one.social['github'], 'even_newer_github')

    def test_partial_patch_user_logged_in(self):
        # Test to make sure new fields are patched and old fields stay the same
        res = self.app.patch_json(self.user_one_url, {
            'id': self.user_one._id,
            'fullname': 'new_fullname',
            'suffix': 'The Millionth'
        }, auth=self.user_one.auth)
        self.user_one.reload()
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['fullname'], 'new_fullname')
        assert_equal(res.json['data']['suffix'], 'The Millionth')
        assert_equal(res.json['data']['gitHub'], self.user_one.social['github'])
        assert_equal(res.json['data']['given_name'], self.user_one.given_name)
        assert_equal(res.json['data']['middle_names'], self.user_one.middle_names)
        assert_equal(res.json['data']['family_name'], self.user_one.family_name)
        assert_equal(res.json['data']['personal_website'], self.user_one.social['personal'])
        assert_equal(res.json['data']['twitter'], self.user_one.social['twitter'])
        assert_equal(res.json['data']['linkedIn'], self.user_one.social['linkedIn'])
        assert_equal(res.json['data']['impactStory'], self.user_one.social['impactStory'])
        assert_equal(res.json['data']['orcid'], self.user_one.social['orcid'])
        assert_equal(res.json['data']['researcherId'], self.user_one.social['researcherId'])
        assert_equal(self.user_one.fullname, 'new_fullname')
        assert_equal(self.user_one.suffix, 'The Millionth')
        assert_equal(self.user_one.social['github'], self.user_one.social['github'])

    def test_partial_put_user_logged_in(self):
        # Test to make sure new fields are patched and old fields stay the same
        res = self.app.put_json(self.user_one_url, {
            'id': self.user_one._id,
            'fullname': 'new_fullname',
            'gitHub': 'even_newer_github',
            'suffix': 'The Millionth'
        }, auth=self.user_one.auth)
        self.user_one.reload()
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['fullname'], 'new_fullname')
        assert_equal(res.json['data']['suffix'], 'The Millionth')
        assert_equal(res.json['data']['gitHub'], 'even_newer_github')
        assert_equal(res.json['data']['given_name'], self.user_one.given_name)
        assert_equal(res.json['data']['middle_names'], self.user_one.middle_names)
        assert_equal(res.json['data']['family_name'], self.user_one.family_name)
        assert_equal(self.user_one.fullname, 'new_fullname')
        assert_equal(self.user_one.suffix, 'The Millionth')
        assert_equal(self.user_one.social['github'], 'even_newer_github')

    def test_put_user_logged_in(self):
        # Logged in user updates their user information via put
        res = self.app.put_json(self.user_one_url, self.new_user_one_data, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['fullname'], self.new_user_one_data['fullname'])
        assert_equal(res.json['data']['given_name'], self.new_user_one_data['given_name'])
        assert_equal(res.json['data']['middle_names'], self.new_user_one_data['middle_names'])
        assert_equal(res.json['data']['family_name'], self.new_user_one_data['family_name'])
        assert_equal(res.json['data']['suffix'], self.new_user_one_data['suffix'])
        assert_equal(res.json['data']['gitHub'], self.new_user_one_data['gitHub'])
        assert_equal(res.json['data']['personal_website'], self.new_user_one_data['personal_website'])
        assert_equal(res.json['data']['twitter'], self.new_user_one_data['twitter'])
        assert_equal(res.json['data']['linkedIn'], self.new_user_one_data['linkedIn'])
        assert_equal(res.json['data']['impactStory'], self.new_user_one_data['impactStory'])
        assert_equal(res.json['data']['orcid'], self.new_user_one_data['orcid'])
        assert_equal(res.json['data']['researcherId'], self.new_user_one_data['researcherId'])
        self.user_one.reload()
        assert_equal(self.user_one.fullname, self.new_user_one_data['fullname'])
        assert_equal(self.user_one.given_name, self.new_user_one_data['given_name'])
        assert_equal(self.user_one.middle_names, self.new_user_one_data['middle_names'])
        assert_equal(self.user_one.family_name, self.new_user_one_data['family_name'])
        assert_equal(self.user_one.suffix, self.new_user_one_data['suffix'])
        assert_equal(self.user_one.social['github'], self.new_user_one_data['gitHub'])
        assert_equal(self.user_one.social['personal'], self.new_user_one_data['personal_website'])
        assert_equal(self.user_one.social['twitter'], self.new_user_one_data['twitter'])
        assert_equal(self.user_one.social['linkedIn'], self.new_user_one_data['linkedIn'])
        assert_equal(self.user_one.social['impactStory'], self.new_user_one_data['impactStory'])
        assert_equal(self.user_one.social['orcid'], self.new_user_one_data['orcid'])
        assert_equal(self.user_one.social['researcherId'], self.new_user_one_data['researcherId'])

    def test_put_user_logged_out(self):
        res = self.app.put_json(self.user_one_url, self.new_user_one_data, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_put_wrong_user(self):
        # User tries to update someone else's user information via put
        res = self.app.put_json(self.user_one_url, self.new_user_one_data, auth=self.user_two.auth, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_patch_wrong_user(self):
        # User tries to update someone else's user information via patch
        res = self.app.patch_json(self.user_one_url, {
            'fullname': self.new_user_one_data['fullname'],
        }, auth=self.user_two.auth, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)
        self.user_one.reload()
        assert_not_equal(self.user_one.fullname, self.new_user_one_data['fullname'])

    def test_update_user_sanitizes_html_properly(self):
        """Post request should update resource, and any HTML in fields should be stripped"""
        bad_fullname = 'Malcolm <strong>X</strong>'
        bad_family_name = 'X <script>alert("is")</script> a cool name'
        res = self.app.patch_json(self.user_one_url, {
            'fullname': bad_fullname,
            'family_name': bad_family_name,
        }, auth=self.user_one.auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['fullname'], strip_html(bad_fullname))
        assert_equal(res.json['data']['family_name'], strip_html(bad_family_name))


class TestDeactivatedUser(ApiTestCase):

    def setUp(self):
        super(TestDeactivatedUser, self).setUp()
        self.user = AuthUserFactory()

    def test_deactivated_user_returns_410_response(self):
        url = '/{}users/{}/'.format(API_BASE, self.user._id)
        res = self.app.get(url, auth=self.user.auth , expect_errors=False)
        assert_equal(res.status_code, 200)
        self.user.is_disabled = True
        self.user.save()
        res = self.app.get(url, auth=self.user.auth , expect_errors=True)
        assert_equal(res.status_code, 410)
