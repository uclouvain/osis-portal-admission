# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from unittest.mock import Mock, patch

from django.http import HttpRequest
from django.template import Context, Template
from django.test import TestCase
from django.views.generic import FormView


class TemplateTagsTestCase(TestCase):
    def test_normal_panel(self):
        template = Template("{% load admission %}{% panel 'Coucou' %}{% endpanel %}")
        rendered = template.render(Context())
        self.assertIn('<h4 class="panel-title">', rendered)
        self.assertIn('Coucou', rendered)
        self.assertIn('<div class="panel-body">', rendered)

    def test_panel_no_title(self):
        template = Template("{% load admission %}{% panel %}{% endpanel %}")
        rendered = template.render(Context())
        self.assertNotIn('<h4 class="panel-title">', rendered)
        self.assertIn('<div class="panel-body">', rendered)

    def test_tabs(self):
        class MockedFormView(FormView):
            def __new__(cls, *args, **kwargs):
                return Mock(kwargs={}, spec=cls)

        template = Template("{% load admission %}{% doctorate_tabs %}")
        rendered = template.render(Context({
            'view': MockedFormView(),
            'request': HttpRequest()
        }))
        self.assertNotIn('confirm-paper', rendered)
        self.assertIn('/doctorates/create/', rendered)

    def test_document_list_empty(self):
        template = Template("{% load admission %}{% document_list docs %}")
        rendered = template.render(Context({'docs': []}))
        self.assertNotIn('<li>', rendered)

    @patch('osis_document.api.utils.get_remote_token', return_value='foobar')
    @patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
    def test_document_list(self, *args):
        template = Template("{% load admission %}{% document_list docs %}")
        rendered = template.render(Context({'docs': ['55375049-9d61-4c11-9f41-7460463a5ae3']}))
        self.assertIn('<li>', rendered)
        self.assertNotIn('<li>', '55375049-9d61-4c11-9f41-7460463a5ae3')
        self.assertIn('myfile', rendered)

    def test_field_data(self):
        template = Template("{% load admission %}{% field_data 'title' data 'col-md-12' %}")
        rendered = template.render(Context({'data': "content"}))
        self.assertIn('content', rendered)
        self.assertIn('title', rendered)
        self.assertIn('<dd>', rendered)
        self.assertIn('class="col-md-12"', rendered)

    @patch('osis_document.api.utils.get_remote_token', return_value='foobar')
    @patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
    def test_field_data_with_list(self, *args):
        template = Template("{% load admission %}{% field_data 'title' data %}")
        rendered = template.render(Context({'data': ['55375049-9d61-4c11-9f41-7460463a5ae3']}))
        self.assertIn('<li>', rendered)
        self.assertNotIn('<li>', '55375049-9d61-4c11-9f41-7460463a5ae3')
        self.assertIn('myfile', rendered)
