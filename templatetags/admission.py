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
import re
from contextlib import suppress
from dataclasses import dataclass
from inspect import getfullargspec

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

from admission.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from admission.contrib.enums import *
from admission.contrib.enums.training import StatutActivite
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
class Tab:
    name: str
    label: str
    icon: str = ''

    def __eq__(self, o) -> bool:
        if isinstance(o, Tab):
            return o.name == self.name
        return o == self.name

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)


TAB_TREES = {
    'doctorate': {
        Tab('personal', _('Personal data'), 'user'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('experience', _('Previous experience'), 'list-alt'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
            Tab('languages', _('Languages knowledge')),
        ],
        Tab('doctorate', _('Doctorate'), 'graduation-cap'): [
            Tab('project', _('Doctoral project')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Supervision')),
            Tab('confirmation-paper', _('Confirmation paper')),
            Tab('extension-request', _('New deadline')),
            Tab('training', _('Training')),
        ],
        Tab('confirmation', _('Confirmation'), 'check-circle'): [
            Tab('confirm', _('Confirmation')),
        ],
    }
}


def _get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


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


def get_valid_tab_tree(tab_tree, admission):
    """
    Return a tab tree based on the specified one but whose tabs depending on the permissions links.
    """
    if admission:
        valid_tab_tree = {}

        # Loop over the tabs of the original tab tree
        for (parent_tab, sub_tabs) in tab_tree.items():
            # Get the accessible sub tabs depending on the user permissions
            valid_sub_tabs = [tab for tab in sub_tabs if _can_access_tab(admission, tab.name, READ_ACTIONS_BY_TAB)]
            # Only add the parent tab if at least one sub tab is allowed
            if len(valid_sub_tabs) > 0:
                valid_tab_tree[parent_tab] = valid_sub_tabs

        return valid_tab_tree

    return tab_tree


@register.inclusion_tag('admission/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs(context, admission=None, with_submit=False, no_status=False):
    match = context['request'].resolver_match

    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]

    # Create a new tab tree based on the default one but depending on the permissions links
    tab_tree = TAB_TREES['doctorate']
    context['tab_tree'] = get_valid_tab_tree(tab_tree, admission)

    return {
        'active_parent': _get_active_parent(tab_tree, current_tab_name),
        'admission': admission,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'with_submit': with_submit,
        'no_status': no_status,
        **context.flatten(),
    }


def get_subtab_label(tab_name):
    return next(
        subtab for subtabs in TAB_TREES['doctorate'].values() for subtab in subtabs if subtab.name == tab_name
    ).label  # pragma : no branch


@register.simple_tag(takes_context=True)
def get_current_tab(context):
    match = context['request'].resolver_match
    current_tab_tree = TAB_TREES['doctorate']
    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]
    return next(
        (tab for subtabs in current_tab_tree.values() for tab in subtabs if tab.name == current_tab_name),
        None,
    )


@register.inclusion_tag('admission/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs(context, admission=None, no_status=False):
    match = context['request'].resolver_match

    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]

    current_tab_tree = TAB_TREES['doctorate']
    valid_tab_tree = context.get('valid_tab_tree', get_valid_tab_tree(current_tab_tree, admission))
    return {
        'subtabs': valid_tab_tree.get(_get_active_parent(current_tab_tree, current_tab_name), []),
        'admission': admission,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'no_status': no_status,
        'active_tab': current_tab_name,
        **context.flatten(),
    }


@register.inclusion_tag('admission/field_data.html')
def field_data(name, data=None, css_class=None, hide_empty=False, translate_data=False, inline=False, html_tag=''):
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
        'html_tag': html_tag,
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
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value


@register.filter
def can_read_tab(admission, tab):
    """Return true if the specified tab can be opened in reading mode for this admission, otherwise return False"""
    return _can_access_tab(admission, tab.name, READ_ACTIONS_BY_TAB)


@register.filter
def can_update_tab(admission, tab):
    """Return true if the specified tab can be opened in writing mode for this admission, otherwise return False"""
    return _can_access_tab(admission, tab.name, UPDATE_ACTIONS_BY_TAB)


@register.filter
def add_str(arg1, arg2):
    """Return the concatenation of two arguments."""
    return str(arg1) + str(arg2)


@register.filter
def has_error_in_tab(admission, tab):
    """Return true if the tab (or subtab) has errors"""
    if not admission or not hasattr(admission, 'erreurs'):
        return False
    if tab not in BUSINESS_EXCEPTIONS_BY_TAB:
        children = TAB_TREES['doctorate'].get(tab)
        if children is None:
            raise ImproperlyConfigured(
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


@register.inclusion_tag('admission/bootstrap_field_with_tooltip.html')
def bootstrap_field_with_tooltip(field, classes='', show_help=False):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
    }


@register.filter
def status_as_class(activity):
    status = activity
    if hasattr(activity, 'status'):
        status = activity.status
    elif isinstance(activity, dict):
        status = activity['status']
    return {
        StatutActivite.SOUMISE.name: "warning",
        StatutActivite.ACCEPTEE.name: "success",
        StatutActivite.REFUSEE.name: "danger",
    }.get(str(status), 'info')


@register.simple_tag
def display(*args):
    """Display args if their value is not empty, can be wrapped by parenthesis, or separated by comma or dash"""
    ret = []
    iterargs = iter(args)
    nextarg = next(iterargs)
    while nextarg != StopIteration:
        if nextarg == "(":
            reduce_wrapping = [next(iterargs, None)]
            while reduce_wrapping[-1] != ")":
                reduce_wrapping.append(next(iterargs, None))
            ret.append(reduce_wrapping_parenthesis(*reduce_wrapping[:-1]))
        elif nextarg == ",":
            ret.append(reduce_list_separated(ret.pop(), next(iterargs, None)))
        elif nextarg == "-":
            ret.append(reduce_list_separated(ret.pop(), next(iterargs, None), separator=" - "))
        elif isinstance(nextarg, str) and len(nextarg) > 1 and re.match(r'\s', nextarg[0]):
            suffixed_val = ret.pop()
            ret.append(f"{suffixed_val}{nextarg}" if suffixed_val else "")
        else:
            ret.append(SafeString(nextarg) if nextarg else '')
        nextarg = next(iterargs, StopIteration)
    return SafeString("".join(ret))


@register.simple_tag
def reduce_wrapping_parenthesis(*args):
    """Display args given their value, wrapped by parenthesis"""
    ret = display(*args)
    if ret:
        return SafeString(f"({ret})")
    return ret


@register.simple_tag
def reduce_list_separated(arg1, arg2, separator=", "):
    """Display args given their value, joined by separator"""
    if arg1 and arg2:
        return separator.join([SafeString(arg1), SafeString(arg2)])
    elif arg1:
        return SafeString(arg1)
    elif arg2:
        return SafeString(arg2)
    return ""
