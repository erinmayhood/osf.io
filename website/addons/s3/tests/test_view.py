#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import mock
from nose.tools import *  # PEP8 asserts
#from tests.base import DbTestCase
from webtest_plus import TestApp

import website.app
from tests.base import DbTestCase
from tests.factories import ProjectFactory, AuthUserFactory
#from website.addons.s3.tests.utils import create_mock_s3
from website.addons.s3 import views
from website.addons.s3.model import AddonS3NodeSettings, AddonS3UserSettings

app = website.app.init_app(routes=True, set_backends=False,
                            settings_module="website.settings")

class TestS3Views(DbTestCase):

    def setUp(self):
        self.app = TestApp(app)
        self.user = AuthUserFactory()
        self.auth = ('test', self.user.api_keys[0]._primary_key)
        self.project = ProjectFactory(creator=self.user)
        self.project.add_addon('s3')
        self.project.creator.add_addon('s3')

        #self.s3 = s3_mock

        self.node_settings = self.project.get_addon('s3')
        # Set the node addon settings to correspond to the values of the mock repo
        #self.node_settings.user = self.s3.repo.return_value['owner']['login']
        #self.node_settings.repo = self.s3.repo.return_value['name']
        self.node_settings.save()

    def test_s3_page_no_user(self):
        s3 = AddonS3NodeSettings(user=None, s3_bucket='lul')
        res = views._page_content('873p', s3)
        assert_equals(res, {})

    def test_s3_page_no_pid(self):
        s3 = AddonS3NodeSettings(user='jimbob', s3_bucket='lul')
        res = views._page_content(None, s3)
        assert_equals(res, {})

    def test_s3_page_empty_pid(self):
        s3 = AddonS3NodeSettings(user='jimbob', s3_bucket='lul')
        res = views._page_content('', s3)
        assert_equals(res, {})

    def test_s3_page_no_auth(self):
        s3 = AddonS3NodeSettings(user='jimbob', s3_bucket='lul')
        s3.s3_node_access_key = ""
        res = views._page_content('', s3)
        assert_equals(res, {})

    @mock.patch('website.addons.s3.views.does_bucket_exist')
    @mock.patch('website.addons.s3.views._s3_create_access_key')
    @mock.patch('website.addons.s3.views.utils.adjust_cors')
    def test_s3_settings_no_bucket(self, mock_cors, mock_create_key, mock_does_bucket_exist):
        mock_does_bucket_exist.return_value = False
        mock_create_key.return_value = True
        mock_cors.return_value = True
        url = "/api/v1/project/{0}/s3/settings/".format(self.project._id)
        res = self.app.post_json(url,{})
        self.project.reload()
        assert_equals(self.node_settings.s3_bucket,None)

    @mock.patch('website.addons.s3.views.create_limited_user')
    def test_s3_create_access_key_attrs(self, mock_create_limited_user):
        mock_create_limited_user.return_value = {'access_key_id': 'Boo', 'secret_access_key': 'Riley'}
        user_settings = AddonS3UserSettings(user='Aticus-killing-mocking')
        views._s3_create_access_key(user_settings, self.node_settings)
        assert_equals(self.node_settings.s3_node_access_key,'Boo')

    @mock.patch('website.addons.s3.views.create_limited_user')
    def test_s3_create_access_key(self, mock_create_limited_user):
        mock_create_limited_user.return_value = {'access_key_id': 'Boo', 'secret_access_key': 'Riley'}
        user_settings = AddonS3UserSettings(user='Aticus-killing-mocking')
        assert_true(views._s3_create_access_key(user_settings, self.node_settings))


    def test_s3_remove_user_settings(self):
        user_settings = AddonS3UserSettings()
        user_settings.access_key = 'to-kill-a-mocking-bucket'
        #TODO finish me

    def test_download_no_file(self):
        url = "/api/v1/project/{0}/s3/fetchurl/".format(self.project._id)
        self.app.post_json(url, {},  expect_errors=True)

    #TODO fix me cant seem to be logged in.....
    @mock.patch('website.addons.s3.api.has_access')
    def test_user_settings_no_auth(self, mock_access):
        mock_access.return_value = False
        url = '/user/s3/settings/'
        rv = self.app.post_json(url, {})
        assert_equals({},rv)

    @mock.patch('website.addons.s3.views.has_access')
    def test_user_settings(self, mock_access):
        mock_access.return_value = False
        url = '/user/s3/settings/'
        self.app.post_json(url, {'access_key': 'scout', 'secret_key': 'Aticus'})
        user_settings = self.user.get_addon('s3')
        assert_equals(user_settings.access_key, 'scout')

