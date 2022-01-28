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
import functools
from collections import namedtuple
from inspect import getfullargspec

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import FormView
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum
from admission.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB

register = template.Library()


class InclusionWithBodyNode(template.library.InclusionNode):
    def __init__(self, nodelist, func, takes_context, args, kwargs, filename, context_name):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist = nodelist
        self.context_name = context_name

    def render(self, context):
        context[self.context_name] = self.nodelist.render(context)
        return super().render(context)


def register_inclusion_with_body(filename, takes_context=None, name=None, context_name='body'):
    def dec(func):
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
        function_name = name or getattr(func, '_decorated_function', func).__name__

        @functools.wraps(func)
        def compile_func(parser, token):
            bits = token.split_contents()[1:]
            args, kwargs = template.library.parse_bits(
                parser, bits, params, varargs, varkw, defaults,
                kwonly, kwonly_defaults, takes_context, function_name,
            )
            nodelist = parser.parse((f'end{function_name}',))
            parser.delete_first_token()
            return InclusionWithBodyNode(
                nodelist, func, takes_context, args, kwargs, filename, context_name
            )

        register.tag(function_name, compile_func)
        return func

    return dec


ParentTab = namedtuple('ParentTab', ['label', 'icon'])
PERSONAL = ParentTab(_('Personal data'), 'user')
TAB_TREE = {
    PERSONAL: ['person', 'coordonnees'],
    ParentTab(_('Previous experience'), 'list-alt'): ['education', 'curriculum', 'languages'],
    ParentTab(_('Doctorate'), 'graduation-cap'): ['project', 'cotutelle', 'supervision'],
}


def get_active_parent(tab_name):
    return next((parent for parent, children in TAB_TREE.items() if tab_name in children), None)


@register.filter
def can_make_action(admission, action_name):
    """Return true if the specified action can be applied for this admission, otherwise return False"""
    return 'url' in admission.links.get(action_name, {})


def _can_access_tab(admission, tab_name, actions_by_tab):
    """Return true if the specified tab can be opened for this admission, otherwise return False"""
    try:
        return can_make_action(admission, actions_by_tab[tab_name])
    except AttributeError:
        raise ImproperlyConfigured("The admission should contain the 'links' property to check tab access")
    except KeyError:
        raise ImproperlyConfigured(
            "Please check that the '{}' property is well specified in the 'READ_ACTIONS_BY_TAB' and"
            " 'UPDATE_ACTIONS_BY_TAB' constants"
            .format(tab_name)
        )


def get_valid_tab_tree(admission, original_tab_tree, is_form_view):
    """
    Return a tab tree based on the specified one but whose the tabs depending on the permissions links.
    """
    if admission:
        valid_tab_tree = {}

        # The actions depend on whether the tab is read or written only
        actions_by_tab = UPDATE_ACTIONS_BY_TAB if is_form_view else READ_ACTIONS_BY_TAB

        # Loop over the tabs of the original tab tree
        for (parent_tab, sub_tabs) in original_tab_tree.items():
            # Get the accessible sub tabs depending on the user permissions
            valid_sub_tabs = [tab for tab in sub_tabs if _can_access_tab(admission, tab, actions_by_tab)]
            # Only add the parent tab if at least one sub tab is allowed
            if len(valid_sub_tabs) > 0:
                valid_tab_tree[parent_tab] = valid_sub_tabs

        return valid_tab_tree

    else:
        return original_tab_tree


@register.inclusion_tag('admission/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs(context, admission=None):
    is_form_view = isinstance(context['view'], FormView)

    # Create a new tab tree based on the default one but depending on the permissions links
    context['valid_tab_tree'] = get_valid_tab_tree(
        admission=admission,
        original_tab_tree=TAB_TREE,
        is_form_view=is_form_view,
    )

    return {
        'tab_tree': context['valid_tab_tree'],
        'active_parent': get_active_parent(context['request'].resolver_match.url_name),
        'admission': admission,
        'detail_view': not is_form_view,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'request': context['request'],
    }


@register.inclusion_tag('admission/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs(context, admission=None):
    is_form_view = isinstance(context['view'], FormView)

    subtab_labels = {
        'person': _("Identification"),
        'coordonnees': _("Contact details"),
        'education': _("Secondary studies"),
        'curriculum': _("Curriculum"),
        'languages': _("Languages knowledge"),
        'project': _("Doctoral project"),
        'cotutelle': _("Cotutelle"),
        'supervision': _("Supervision"),
        'confirm': _("Confirmation"),
        'confirm_paper': _("Confirmation paper"),
        'training': _("Doctoral training"),
        'jury': _("Jury"),
        'private_defense': _("Private defense"),
        'public_defense': _("Public defense"),
    }
    valid_tab_tree = context.get('valid_tab_tree', get_valid_tab_tree(
        admission=admission,
        original_tab_tree=TAB_TREE,
        is_form_view=is_form_view,
    ))

    return {
        'subtabs': valid_tab_tree.get(get_active_parent(context['request'].resolver_match.url_name), []),
        'subtab_labels': subtab_labels,
        'admission': admission,
        'detail_view': not is_form_view,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'request': context['request'],
    }


@register.inclusion_tag('admission/field_data.html')
def field_data(name, data=None, css_class=None, hide_empty=False, translate_data=False):
    if isinstance(data, list):
        template_string = "{% load osis_document %}{% if files %}{% document_visualizer files %}{% endif %}"
        template_context = {'files': data}
        data = template.Template(template_string).render(template.Context(template_context))
    elif translate_data is True:
        data = _(data)
    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
    }


@register_inclusion_with_body('panel.html', takes_context=True, context_name='panel_body')
def panel(context, title='', css_class="panel panel-default", title_level=4, additional_css_class="", **kwargs):
    """
    Template tag for panel
    :param title: the panel title
    :param css_class: the panel css class
    :param title_level: the title level
    :param additional_css_class: some additional css classes
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['attributes'] = kwargs
    context['attributes']['class'] = css_class + " " + additional_css_class
    context['title_level'] = title_level
    if id:
        context['id'] = id
    return context


@register.filter
def enum_display(value, enum_name):
    if value and isinstance(value, str):
        for enum in ChoiceEnum.__subclasses__():
            if enum.__name__ == enum_name:
                return enum.get_value(value)
    return value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def can_read_tab(admission, tab_name):
    """Return true if the specified tab can be opened in reading mode for this admission, otherwise return False"""
    return _can_access_tab(admission, tab_name, READ_ACTIONS_BY_TAB)


@register.filter
def can_update_tab(admission, tab_name):
    """Return true if the specified tab can be opened in writing mode for this admission, otherwise return False"""
    return _can_access_tab(admission, tab_name, UPDATE_ACTIONS_BY_TAB)


@register.filter
def add_str(arg1, arg2):
    """Return the concatenation of two arguments."""
    return str(arg1) + str(arg2)
