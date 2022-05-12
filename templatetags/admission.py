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
from contextlib import suppress
from dataclasses import dataclass
from inspect import getfullargspec

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from admission.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from admission.services.proposition import BUSINESS_EXCEPTIONS_BY_TAB
from base.models.utils.utils import ChoiceEnum
from osis_admission_sdk.exceptions import ForbiddenException, NotFoundException, UnauthorizedException

register = template.Library()


class PanelNode(template.library.InclusionNode):
    def __init__(self, nodelist: dict, func, takes_context, args, kwargs, filename):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist_dict = nodelist

    def render(self, context):
        for context_name, nodelist in self.nodelist_dict.items():
            context[context_name] = nodelist.render(context)
        return super().render(context)


def register_panel(filename, takes_context=None, name=None):
    def dec(func):
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
        function_name = name or getattr(func, '_decorated_function', func).__name__

        @functools.wraps(func)
        def compile_func(parser, token):
            # {% panel %} and its arguments
            bits = token.split_contents()[1:]
            args, kwargs = template.library.parse_bits(
                parser, bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults, takes_context, function_name
            )
            nodelist_dict = {'panel_body': parser.parse(('footer', 'endpanel'))}
            token = parser.next_token()

            # {% footer %} (optional)
            if token.contents == 'footer':
                nodelist_dict['panel_footer'] = parser.parse(('endpanel',))
                parser.next_token()

            return PanelNode(nodelist_dict, func, takes_context, args, kwargs, filename)

        register.tag(function_name, compile_func)
        return func

    return dec


@dataclass(frozen=True)
class ParentTab:
    label: str
    icon: str
    name: str


PERSONAL = ParentTab(_('Personal data'), 'user', 'personal')
TAB_TREE = {
    PERSONAL: ['person', 'coordonnees'],
    ParentTab(_('Previous experience'), 'list-alt', 'experience'): ['education', 'curriculum', 'languages'],
    ParentTab(_('Doctorate'), 'graduation-cap', 'doctorate'): [
        'project',
        'cotutelle',
        'supervision',
        'confirmation-paper',
        'extension-request',
    ],
    ParentTab(_('Confirmation'), 'check-circle', 'confirm'): ['confirm'],
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
            " 'UPDATE_ACTIONS_BY_TAB' constants".format(tab_name)
        )


def get_valid_tab_tree(admission):
    """
    Return a tab tree based on the specified one but whose the tabs depending on the permissions links.
    """
    if admission:
        valid_tab_tree = {}

        # Loop over the tabs of the original tab tree
        for (parent_tab, sub_tabs) in TAB_TREE.items():
            # Get the accessible sub tabs depending on the user permissions
            valid_sub_tabs = [tab for tab in sub_tabs if _can_access_tab(admission, tab, READ_ACTIONS_BY_TAB)]
            # Only add the parent tab if at least one sub tab is allowed
            if len(valid_sub_tabs) > 0:
                valid_tab_tree[parent_tab] = valid_sub_tabs

        return valid_tab_tree

    return TAB_TREE


@register.inclusion_tag('admission/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs(context, admission=None, with_submit=False):
    match = context['request'].resolver_match
    is_form_view = match.namespaces[1:2] == ('doctorate', 'update')

    # Create a new tab tree based on the default one but depending on the permissions links
    context['tab_tree'] = get_valid_tab_tree(admission=admission)

    return {
        'active_parent': get_active_parent(match.url_name),
        'admission': admission,
        'detail_view': not is_form_view,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'with_submit': with_submit,
        **context.flatten(),
    }


SUBTAB_LABELS = {
    # Personal data
    'person': _("Identification"),
    'coordonnees': _("Contact details"),
    # Previous experience
    'education': _("Secondary studies"),
    'curriculum': _("Curriculum"),
    'languages': _("Languages knowledge"),
    # Project
    'project': _("Doctoral project"),
    'cotutelle': _("Cotutelle"),
    'supervision': _("Supervision"),
    # Confirmation
    'confirm': _("Confirmation"),
    # Confirmation paper
    'confirmation-paper': _("Confirmation paper"),
    'extension-request': _("New deadline"),
    # Others
    'training': _("Doctoral training"),
    'jury': _("Jury"),
    'private_defense': _("Private defense"),
    'public_defense': _("Public defense"),
}


@register.inclusion_tag('admission/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs(context, admission=None):
    match = context['request'].resolver_match
    is_form_view = match.namespaces[1:] == ['doctorate', 'update']

    valid_tab_tree = context.get('valid_tab_tree', get_valid_tab_tree(admission=admission))

    return {
        'subtabs': valid_tab_tree.get(get_active_parent(match.url_name), []),
        'subtab_labels': SUBTAB_LABELS,
        'admission': admission,
        'detail_view': not is_form_view,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        **context.flatten(),
    }


@register.inclusion_tag('admission/field_data.html')
def field_data(name, data=None, css_class=None, hide_empty=False, translate_data=False, inline=False):
    if isinstance(data, list):
        template_string = "{% load osis_document %}{% if files %}{% document_visualizer files %}{% endif %}"
        template_context = {'files': data}
        data = template.Template(template_string).render(template.Context(template_context))
    elif translate_data is True:
        data = _(data)

    if inline is True:
        name = _("%(label)s:") % {'label': name}
        css_class = (css_class + ' inline-field-data') if css_class else 'inline-field-data'

    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
    }


@register_panel('panel.html', takes_context=True)
def panel(context, title='', title_level=4, additional_class='', **kwargs):
    """
    Template tag for panel
    :param title: the panel title
    :param title_level: the title level
    :param additional_class: css class to add
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['title_level'] = title_level
    context['additional_class'] = additional_class
    context['attributes'] = {k.replace('_', '-'): v for k, v in kwargs.items()}
    return context


@register.simple_tag(takes_context=True)
def get_dashboard_links(context):
    from admission.services.proposition import AdmissionPropositionService

    with suppress(UnauthorizedException, NotFoundException, ForbiddenException):
        return AdmissionPropositionService.get_dashboard_links(context['request'].user.person)
    return {}


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
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value


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


@register.filter
def can_update_something(admission):
    """Return true if any update tab can be opened for this admission, otherwise return False"""
    return any(_can_access_tab(admission, tab_name, UPDATE_ACTIONS_BY_TAB) for tab_name in UPDATE_ACTIONS_BY_TAB)


@register.filter
def has_error_in_tab(admission, tab):
    """Return true if the tab (or subtab) has errors"""
    if not admission or not hasattr(admission, 'erreurs'):
        return False
    if tab not in BUSINESS_EXCEPTIONS_BY_TAB:
        children = next((children for parent, children in TAB_TREE.items() if parent.name == tab), None)
        if children is None:
            raise Exception(
                f"{tab} has no children and is not in BUSINESS_EXCEPTIONS_BY_TAB, use no_status=1 or correct name"
            )
        return any(
            erreur['status_code'] in [e.value for e in BUSINESS_EXCEPTIONS_BY_TAB[subtab]]
            for subtab in children
            for erreur in admission.erreurs
        )
    return any(
        erreur['status_code'] in [e.value for e in BUSINESS_EXCEPTIONS_BY_TAB[tab]] for erreur in admission.erreurs
    )
