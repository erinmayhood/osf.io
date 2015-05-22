# -*- coding: utf-8 -*-
import mock
from nose.tools import *  # flake8: noqa

from framework.auth.core import Auth
from website.models import Node
from tests.base import ApiTestCase, fake
from tests.factories import UserFactory, ProjectFactory, FolderFactory, DashboardFactory, NodeFactory, PointerFactory

class TestWelcomeToApi(ApiTestCase):
    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.auth = (self.user.username, 'justapoorboy')

    def test_returns_200_for_logged_out_user(self):
        res = self.app.get('/v2/')
        assert_equal(res.status_code, 200)

    def test_returns_200_for_logged_in_user(self):
        url = '/v2/'
        res = self.app.get(url, auth=(self.auth))
        assert_equal(res.status_code, 200)

    def test_returns_current_user_info_when_logged_in(self):
        url = '/v2/'
        res = self.app.get(url, auth=(self.auth))
        assert_equal(res.json['meta']['current_user']['data']['given_name'], 'Freddie')

class TestNodeList(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.auth = (self.user.username, 'justapoorboy')

    def test_returns_200(self):
        res = self.app.get('/v2/nodes/')
        assert_equal(res.status_code, 200)

    def test_only_returns_non_deleted_public_projects(self):
        deleted = ProjectFactory(is_deleted=True)
        private = ProjectFactory(is_public=False)
        public = ProjectFactory(is_public=True)

        res = self.app.get('/v2/nodes/')
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]

        assert_in(public._id, ids)
        assert_not_in(deleted._id, ids)
        assert_not_in(private._id, ids)

        Node.remove()


class TestNodeContributorList(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()

        password = fake.password()
        self.password = password

        self.user.set_password(password)
        self.user.save()
        self.auth = (self.user.username, password)

        self.project = ProjectFactory(is_public=False)
        self.project.add_contributor(self.user)
        self.project.save()

        self.project_two = ProjectFactory(is_public=True)
        self.project_two.add_contributor(self.user)
        self.project_two.save()


    def test_must_be_contributor(self):

        non_contrib = UserFactory.build()
        pw = fake.password()
        non_contrib.set_password(pw)
        non_contrib.save()

        url = '/v2/nodes/{}/contributors/'.format(self.project._id)
        # non-authenticated
        res = self.app.get(url, expect_errors=True)
        assert_equal(res.status_code, 401)

        # non-contrib
        res = self.app.get(url, auth=(non_contrib.username, pw), expect_errors=True)
        assert_equal(res.status_code, 403)

        # contrib
        res = self.app.get(url, auth=(self.user.username, self.password))
        assert_equal(res.status_code, 200)

        url = '/v2/nodes/{}/contributors/'.format(self.project_two._id)
        # Not logged in, public
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

        # Logged in, public
        res = self.app.get(url, auth= self.auth)
        assert_equal(res.status_code, 200)

        Node.remove()


class TestNodeChildrenList(ApiTestCase):
    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.auth = (self.user.username, password)
        self.project = ProjectFactory()
        self.project.add_contributor(self.user, permissions=['read', 'write'])
        self.project.save()
        self.component = NodeFactory(parent=self.project, creator=self.user)
        self.pointer = ProjectFactory()
        self.project.add_pointer(self.pointer, auth=Auth(self.user), save=True)

        self.public_project = ProjectFactory(is_public=True)
        self.public_project.save()
        self.component = NodeFactory(parent=self.public_project, creator=self.user, is_public=True)

    def test_node_children_list_does_not_include_pointers(self):
        url = '/v2/nodes/{}/children/'.format(self.project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)

        #Not logged in
        res = self.app.get(url, expect_errors = True)
        assert_equal(res.status_code, 401)

    def test_node_children_list_does_not_include_unauthorized_projects(self):
        private_component = NodeFactory(parent=self.project)
        url = '/v2/nodes/{}/children/'.format(self.project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)

    def test_public_node_children(self):
        # logged in
        url = '/v2/nodes/{}/children/'.format(self.public_project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.status_code, 200)

        # Logged out
        res = self.app.get(url)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)


class TestNodeFiltering(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user_one = UserFactory.build()
        self.user_one.set_password('justapoorboy')
        self.user_one.save()
        self.auth_one = (self.user_one.username, 'justapoorboy')
        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.auth_two = (self.user_two.username, 'justapoorboy')
        self.project_one = ProjectFactory(title="Project One", is_public=True)
        self.project_two = ProjectFactory(title="Project Two", description="One Three", is_public=True)
        self.project_three = ProjectFactory(title="Three", is_public=True)
        self.private_project_user_one = ProjectFactory(title="Private Project User One", is_public=False, creator=self.user_one)
        self.private_project_user_two = ProjectFactory(title="Private Project User Two", is_public=False, creator=self.user_two)
        self.folder = FolderFactory()
        self.dashboard = DashboardFactory()

    def tearDown(self):
        ApiTestCase.tearDown(self)
        Node.remove()

    def test_get_all_projects_with_no_filter_logged_in(self):
        url = "/v2/nodes/"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_all_projects_with_no_filter_not_logged_in(self):
        url = "/v2/nodes/"

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_one_project_with_exact_filter_logged_in(self):
        url = "/v2/nodes/?filter[title]=Project%20One"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_not_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_one_project_with_exact_filter_not_logged_in(self):
        url = "/v2/nodes/?filter[title]=Project%20One"

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_not_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_some_projects_with_substring_logged_in(self):
        url = "/v2/nodes/?filter[title]=Two"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_some_projects_with_substring_not_logged_in(self):
        url = "/v2/nodes/?filter[title]=Two"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_only_public_or_my_projects_with_filter_logged_in(self):
        url = "/v2/nodes/?filter[title]=Project"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_only_public_projects_with_filter_not_logged_in(self):
        url = "/v2/nodes/?filter[title]=Project"

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_alternate_filtering_field_logged_in(self):
        url = "/v2/nodes/?filter[description]=Three"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_alternate_filtering_field_not_logged_in(self):
        url = "/v2/nodes/?filter[description]=Three"

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_incorrect_filtering_field_logged_in(self):
        # TODO Change to check for error when the functionality changes. Currently acts as though it doesn't exist
        url = "/v2/nodes/?filter[notafield]=bogus"

        res = self.app.get(url, auth=self.auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_incorrect_filtering_field_not_logged_in(self):
        # TODO Change to check for error when the functionality changes. Currently acts as though it doesn't exist
        url = "/v2/nodes/?filter[notafield]=bogus"

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)


class TestNodePointersList(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.auth = (self.user.username, 'password')
        self.project = ProjectFactory()
        self.pointer_project = ProjectFactory()
        self.project.add_pointer(self.pointer_project, auth=Auth(self.user))

        self.public_project = ProjectFactory(is_public=True)
        self.public_pointer_project = ProjectFactory(is_public=True)
        self.public_project.add_pointer(self.public_pointer_project, auth=Auth(self.user))
        self.user_two = UserFactory.build()
        self.user.set_password('password')
        self.user.save()


    def test_returns_200(self):
        url = '/v2/nodes/{}/pointers/'.format(self.project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(res.status_code, 200)

    def test_returns_node_pointers(self):
        url = '/v2/nodes/{}/pointers/'.format(self.project._id)
        res = self.app.get(url, auth=self.auth)
        res_json = res.json['data']
        assert_equal(len(res_json), 1)
        assert_in(res_json[0]['node_id'], self.pointer_project._id)

    def test_creates_node_pointer(self):
        project = ProjectFactory()
        url = '/v2/nodes/{}/pointers/'.format(self.project._id)
        payload = {'node_id': project._id}
        res = self.app.post(url, payload, auth=self.auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['node_id'], project._id)


class TestNodeContributorFiltering(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.project = ProjectFactory()
        self.password = fake.password()
        self.project.creator.set_password(self.password)
        self.project.creator.save()
        self.auth = (self.project.creator.username, self.password)

    def test_filtering_node_with_only_bibliographic_contributors(self):

        base_url = '/v2/nodes/{}/contributors/'.format(self.project._id)
        # no filter
        res = self.app.get(base_url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)

        # filter for bibliographic contributors
        url = base_url + '?filter[bibliographic]=True'
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)
        assert_true(res.json['data'][0].get('bibliographic', None))

        # filter for non-bibliographic contributors
        url = base_url + '?filter[bibliographic]=False'
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 0)

    def test_filtering_node_with_non_bibliographic_contributor(self):
        non_bibliographic_contrib = UserFactory()
        self.project.add_contributor(non_bibliographic_contrib, visible=False)
        self.project.save()

        base_url = base_url = '/v2/nodes/{}/contributors/'.format(self.project._id)

        # no filter
        res = self.app.get(base_url, auth=self.auth)
        assert_equal(len(res.json['data']), 2)

        # filter for bibliographic contributors
        url = base_url + '?filter[bibliographic]=True'
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)
        assert_true(res.json['data'][0].get('bibliographic', None))

        # filter for non-bibliographic contributors
        url = base_url + '?filter[bibliographic]=False'
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)
        assert_false(res.json['data'][0].get('bibliographic', None))


class TestNodePointerDetail(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.auth = (self.user.username, 'password')
        self.project = ProjectFactory()
        self.pointer_project = ProjectFactory()
        self.pointer = self.project.add_pointer(self.pointer_project, auth=Auth(self.user), save=True)

    def test_returns_200(self):
        url = '/v2/nodes/{}/pointers/{}'.format(self.project._id, self.pointer._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(res.status_code, 200)

    def test_returns_node_pointer(self):
        url = '/v2/nodes/{}/pointers/{}'.format(self.project._id, self.pointer._id)
        res = self.app.get(url, auth=self.auth)
        res_json = res.json['data']
        assert_equal(res_json['node_id'], self.pointer_project._id)

    def test_deletes_node_pointer(self):
        url = '/v2/nodes/{}/pointers/{}'.format(self.project._id, self.pointer._id)
        res = self.app.delete(url, auth=self.auth)
        assert_equal(res.status_code, 204)
        assert_equal(len(self.project.nodes_pointer), 0)


class TestNodeFilesList(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.auth = (self.user.username, 'justapoorboy')
        self.project = ProjectFactory(creator=self.user)

    def test_returns_200(self):
        url = '/v2/nodes/{}/files/'.format(self.project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(res.status_code, 200)

    def test_returns_addon_folders(self):
        project = ProjectFactory(creator=self.user)
        user_auth = Auth(self.user)
        url = '/v2/nodes/{}/files/'.format(project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

        project.add_addon('github', auth=user_auth)
        project.save()

        res = self.app.get(url, auth=self.auth)
        data = res.json['data']
        providers = [item['provider'] for item in data]
        assert_equal(len(data), 2)
        assert_in('github', providers)
        assert_in('osfstorage', providers)

    @mock.patch('api.nodes.views.requests.get')
    def test_returns_node_files_list(self, mock_waterbutler_request):
        mock_res = mock.MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            u'data': [{
                u'contentType': None,
                u'extra': {u'downloads': 0, u'version': 1},
                u'kind': u'file',
                u'modified': None,
                u'name': u'NewFile',
                u'path': u'/',
                u'provider': u'osfstorage',
                u'size': None
            }]
        }
        mock_waterbutler_request.return_value = mock_res
        url = '/v2/nodes/{}/files/?path=%2F&provider=osfstorage'.format(self.project._id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(res.json['data'][0]['name'], 'NewFile')
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

    @mock.patch('api.nodes.views.requests.get')
    def test_handles_unauthenticated_waterbutler_request(self, mock_waterbutler_request):
        url = '/v2/nodes/{}/files/?path=%2F&provider=osfstorage'.format(self.project._id)
        mock_res = mock.MagicMock()
        mock_res.status_code = 401
        mock_waterbutler_request.return_value = mock_res
        res = self.app.get(url, auth=self.auth, expect_errors=True)
        assert_equal(res.status_code, 403)

    @mock.patch('api.nodes.views.requests.get')
    def test_handles_bad_waterbutler_request(self, mock_waterbutler_request):
        url = '/v2/nodes/{}/files/?path=%2F&provider=osfstorage'.format(self.project._id)
        mock_res = mock.MagicMock()
        mock_res.status_code = 418
        mock_res.json.return_value = {}
        mock_waterbutler_request.return_value = mock_res
        res = self.app.get(url, auth=self.auth, expect_errors=True)
        assert_equal(res.status_code, 400)


class TestNodeCreateUpdate(ApiTestCase):

    def setUp(self):
        ApiTestCase.setUp(self)
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.auth = (self.user.username, 'justapoorboy')
<<<<<<< HEAD
        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.auth_two = (self.user_two.username, 'justapoorboy')
        self.project_one = ProjectFactory(title = "Project One", is_public = True)
        self.project_two = ProjectFactory(title = "Project Two", is_public = False, creator = self.user)

    def test_cannot_create_node_when_logged_out(self):
        url = '/v2/nodes/'
        public_project = {'title': 'My public project', 'description': 'Project description', 'category' : 'project',
                          'public': True }
        private_project = {'title': 'My private project', 'description': 'Project description', 'category' : 'project',
                          'public': False }
        res1 = self.app.post_json(url, public_project, expect_errors = True)
        res2 = self.app.post_json(url, private_project, expect_errors = True)
        assert_equal(res1.status_code, 401)
        assert_equal(res2.status_code, 401)

    def test_creates_project_returns_proper_data(self):
        url = '/v2/nodes/'
        public_project = {'title': 'My public project', 'description': 'Project description', 'category' : 'project',
                          'public': True }
        private_project = {'title': 'Cool Private Project', 'description': 'A properly cool project', 'category': 'data',
                           'public': False }
        res = self.app.post_json(url, public_project, auth=self.auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], public_project['title'])
        assert_equal(res.json['data']['description'], public_project['description'])
        assert_equal(res.json['data']['category'], public_project['category'])

        res = self.app.post_json(url, private_project, auth=self.auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], private_project['title'])
        assert_equal(res.json['data']['description'], private_project['description'])
        assert_equal(res.json['data']['category'], private_project['category'])
=======
        self.url = '/v2/nodes/'
        self.title = 'Cool Project'
        self.new_title = 'Super Cool Project'
        self.description = 'A Properly Cool Project'
        self.new_description = 'An even cooler project'
        self.category = 'data'
        self.new_category = 'project'

    def test_creates_project_returns_proper_data(self):
        res = self.app.post_json(self.url, {
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'public': True,
        }, auth=self.auth)
        project_id = res.json['data']['id']
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], self.title)
        assert_equal(res.json['data']['description'], self.description)
        assert_equal(res.json['data']['category'], self.category)
>>>>>>> 782c9caf43ed4f6378e48f81d36ae29e4d1c03ee

    def test_creates_project_creates_project(self):
        res = self.app.post_json(self.url, {
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'public': True,
        }, auth=self.auth)
        project_id = res.json['data']['id']
        assert_equal(res.status_code, 201)
        url = '/v2/nodes/{}/'.format(project_id)
        res = self.app.get(url, auth=self.auth)
        assert_equal(res.json['data']['title'], self.title)
        assert_equal(res.json['data']['description'], self.description)
        assert_equal(res.json['data']['category'], self.category)

    def test_retrieve_project_details_when_logged_out(self):
        url = '/v2/nodes/{}/'.format(self.project_one._id)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.get(url, expect_errors = True)
        assert_equal(res.status_code, 401)

    def test_retrieve_private_project_when_logged_in(self):
        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.get(url, auth = self.auth)
        assert_equal(res.status_code, 200)

        res = self.app.get(url, auth = self.auth_two, expect_errors = True)
        assert_equal(res.status_code, 403)


    def test_update_project_returns_proper_data(self):
        project = self.project = ProjectFactory(
            title=self.title, description=self.description, category=self.category, is_public=True, creator=self.user)

        url = '/v2/nodes/{}/'.format(project._id)
        res = self.app.put_json(url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': True,
        }, auth=self.auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.new_description)
        assert_equal(res.json['data']['category'], self.new_category)

    def test_update_project_while_logged_out(self):
        new_title = 'Super Cool Project'
        new_description = 'An even cooler project'
        new_category = 'project'
        url = '/v2/nodes/{}/'.format(self.project_one._id)
        res = self.app.put_json(url, {
            'title': new_title,
            'description': new_description,
            'category': new_category,
            'public': True,
        }, expect_errors = True)
        assert_equal(res.status_code, 401)

        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.put_json(url, {
            'title': new_title,
            'description': new_description,
            'category': new_category,
            'public': False,
        }, expect_errors = True)
        assert_equal(res.status_code, 401)

    def test_update_private_project_while_logged_in(self):
        new_title = 'Super Cool Project'
        new_description = 'An even cooler project'
        new_category = 'project'
        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.put_json(url, {
            'title': new_title,
            'description': new_description,
            'category': new_category,
            'public': False,
        }, auth=self.auth)
        assert_equal(res.status_code, 200)

        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.put_json(url, {
            'title': new_title,
            'description': new_description,
            'category': new_category,
            'public': False,
        }, auth=self.auth_two, expect_errors = True)
        assert_equal(res.status_code, 403)

    def test_update_project_updates_project_properly(self):
        project = self.project = ProjectFactory(
            title=self.title, description=self.description, category=self.category, is_public=True, creator=self.user)

        url = '/v2/nodes/{}/'.format(project._id)
        res = self.app.put_json(url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': True,
        }, auth=self.auth)
        assert_equal(res.status_code, 200)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.new_description)
        assert_equal(res.json['data']['category'], self.new_category)

    def test_partial_update_project_returns_proper_data(self):
        project = self.project = ProjectFactory(
            title=self.title, description=self.description, category=self.category, is_public=True, creator=self.user)

        url = '/v2/nodes/{}/'.format(project._id)
        res = self.app.patch_json(url, {
            'title': self.new_title,
        }, auth=self.auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.description)
        assert_equal(res.json['data']['category'], self.category)

    def test_partial_update_project_while_logged_out(self):
        new_title = "Patching this title"
        url = '/v2/nodes/{}/'.format(self.project_one._id)
        res = self.app.patch_json(url, {'title': new_title}, expect_errors = True)
        assert_equal(res.status_code, 401)

        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.patch_json(url, {'title': new_title}, expect_errors = True)
        assert_equal(res.status_code, 401)

    def test_partial_update_private_project_while_logged_in(self):
        new_title = "Patching this title"
        url = '/v2/nodes/{}/'.format(self.project_two._id)
        res = self.app.patch_json(url, {'title': new_title}, auth = self.auth)
        assert_equal(res.status_code, 200)

        res = self.app.patch_json(url, {'title': new_title}, auth = self.auth_two, expect_errors = True)
        assert_equal(res.status_code, 403)

    def test_partial_update_project_updates_project_properly(self):
        url = '/v2/nodes/'
        title = 'Cool Project'
        description = 'A Properly Cool Project'
        new_description = 'An even cooler project'
        category = 'data'
        project = self.project = ProjectFactory(
            title=title, description=description, category=category, is_public=True, creator=self.user)

        url = '/v2/nodes/{}/'.format(project._id)
        res = self.app.patch_json(url, {
            'description': new_description,
        }, auth=self.auth)
        assert_equal(res.status_code, 200)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], title)
        assert_equal(res.json['data']['description'], new_description)
        assert_equal(res.json['data']['category'], category)