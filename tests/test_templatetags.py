# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.templatetags.admission import (
    TAB_TREE,
    can_make_action,
    can_read_tab,
    can_update_tab,
    get_valid_tab_tree,
)
from base.models.utils.utils import ChoiceEnum


class TemplateTagsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        class Admission:
            def __init__(self, links=None):
                self.links = links if links is not None else {
                    'retrieve_coordinates': {
                        'url': 'my_url',
                        'method': 'GET'
                    },
                    'update_coordinates': {
                        'url': 'my_url',
                        'method': 'POST'
                    },
                    'retrieve_person': {
                        'error': 'Method not allowed',
                        'method': 'GET',
                    }
                }
        cls.Admission = Admission

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
        self.assertInHTML("""<li role="presentation" class="active">
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
        self.assertInHTML("""<li role="presentation">
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

    def test_valid_tab_tree_no_admission(self):
        # No admission is specified -> return the original tab tree
        valid_tab_tree = get_valid_tab_tree(
            admission=None,
            original_tab_tree=TAB_TREE,
            is_form_view=True,
        )
        self.assertEqual(valid_tab_tree, TAB_TREE)

    def test_valid_tab_tree_read_mode(self):
        # Only one read tab is allowed -> return it and its parent

        admission = self.Admission()

        valid_tab_tree = get_valid_tab_tree(
            admission=admission,
            original_tab_tree=TAB_TREE,
            is_form_view=True,
        )

        parent_tabs = list(valid_tab_tree.keys())

        # Check parent tabs
        self.assertEqual(len(parent_tabs), 1)
        self.assertEqual(parent_tabs[0].label, _('Personal data'))

        # Check children tabs
        self.assertIn('coordonnees', valid_tab_tree[parent_tabs[0]])

    def test_valid_tab_tree_update_mode(self):
        # Only one form tab is allowed -> return it and its parent

        admission = self.Admission()
        valid_tab_tree = get_valid_tab_tree(
            admission=admission,
            original_tab_tree=TAB_TREE,
            is_form_view=True,
        )

        parent_tabs = list(valid_tab_tree.keys())

        # Check parent tabs
        self.assertEqual(len(parent_tabs), 1)
        self.assertEqual(parent_tabs[0].label, _('Personal data'))

        # Check children tabs
        self.assertIn('coordonnees', valid_tab_tree[parent_tabs[0]])

    def test_can_make_action_valid_existing_action(self):
        # The tab action is specified in the admission as allowed -> return True
        admission = self.Admission()
        self.assertTrue(can_make_action(admission, 'retrieve_coordinates'))

    def test_can_make_action_invalid_existing_action(self):
        # The tab action is specified in the admission as not allowed -> return False
        admission = self.Admission()
        self.assertFalse(can_make_action(admission, 'retrieve_person'))

    def test_can_make_action_not_returned_action(self):
        # The tab action is not specified in the admission -> return False
        admission = self.Admission()
        self.assertFalse(can_make_action(admission, 'unknown'))

    def test_can_read_tab_valid_existing_tab(self):
        # The tab action is specified in the admission as allowed -> return True
        admission = self.Admission()
        self.assertTrue(can_read_tab(admission, 'coordonnees'))

    def test_can_read_tab_invalid_existing_tab(self):
        # The tab action is well configured as not allowed -> return False
        admission = self.Admission()
        self.assertFalse(can_read_tab(admission, 'person'))

    def test_can_read_tab_not_returned_action(self):
        # The tab action is not specified in the admission -> return False
        admission = self.Admission()
        self.assertFalse(can_read_tab(admission, 'project'))

    def test_can_read_tab_unknown_tab(self):
        # The tab action is unknown -> raise an exception
        admission = self.Admission()
        with self.assertRaisesMessage(ImproperlyConfigured, 'unknown'):
            can_read_tab(admission, 'unknown')

    def test_can_read_tab_no_admission_links(self):
        # The tab action is unknown -> raise an exception
        admission = self.Admission()
        delattr(admission, 'links')
        with self.assertRaisesMessage(ImproperlyConfigured, 'links'):
            can_read_tab(admission, 'coordonnees')

    def test_can_update_tab_valid_existing_action(self):
        # The tab action is specified in the admission as allowed -> return True
        admission = self.Admission()
        self.assertTrue(can_update_tab(admission, 'coordonnees'))
