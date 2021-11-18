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

from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.models.utils.utils import ChoiceEnum


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

    def test_enum_value(self):
        class TestEnum(ChoiceEnum):
            FOO = "Bar"

        template = Template("{% load admission %}{{ value|enum_display:'TestEnum' }}")
        rendered = template.render(Context({
            'value': "TEST",
        }))
        self.assertEqual('TEST', rendered)

        rendered = template.render(Context({
            'value': "",
        }))
        self.assertEqual('', rendered)

        rendered = template.render(Context({
            'value': None,
        }))
        self.assertEqual('None', rendered)

        obj = Mock()
        obj.__str__ = lambda _: "obj"
        rendered = template.render(Context({
            'value': obj,
        }))
        self.assertEqual('obj', rendered)

        rendered = template.render(Context({
            'value': "FOO",
        }))
        self.assertEqual('Bar', rendered)

        template = Template("{% load admission %}{{ value|enum_display:'InexistantEnum' }}")
        rendered = template.render(Context({
            'value': "TEST",
        }))
        self.assertEqual('TEST', rendered)

    def test_tabs(self):
        class MockedFormView(FormView):
            def __new__(cls, *args, **kwargs):
                return Mock(kwargs={}, spec=cls)

        person_tab_url = '/admission/doctorates/create/person'
        template = Template("{% load admission %}{% doctorate_tabs %}")

        request = RequestFactory().get(person_tab_url)
        request.resolver_match = resolve(person_tab_url)
        rendered = template.render(Context({
            'view': MockedFormView(),
            'request': request,
        }))
        self.assertNotIn('confirm-paper', rendered)
        self.assertInHTML("""<li role="presentation" class="text-nowrap active">
            <a href="/admission/doctorates/create/person">
                <span class="fa fa-user"></span>
                {}
            </a>
        </li>""".format(_("Personal data")), rendered)

        # Should work on non-tab urls
        another_tab_url = '/admission/doctorates/55375049-9d61-4c11-9f41-7460463a5ae3/remove-member/type/matricule'
        request = RequestFactory().get(another_tab_url)
        request.resolver_match = resolve(another_tab_url)
        rendered = template.render(Context({
            'view': MockedFormView(),
            'request': request,
        }))
        self.assertInHTML("""<li role="presentation" class="text-nowrap">
            <a href="/admission/doctorates/create/person">
                <span class="fa fa-user"></span>
                {}
            </a>
        </li>""".format(_("Personal data")), rendered)

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
        self.assertIn('document-visualizer', rendered)
        self.assertNotIn('55375049-9d61-4c11-9f41-7460463a5ae3', rendered)
        self.assertIn('foobar', rendered)
