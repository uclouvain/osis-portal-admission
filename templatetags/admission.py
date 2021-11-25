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
import functools
from collections import namedtuple
from inspect import getfullargspec

from django import template
from django.views.generic import FormView
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum

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
    ParentTab(_('Previous experience'), 'list-alt'): ['education', 'curriculum'],
    ParentTab(_('Doctorate'), 'graduation-cap'): ['project', 'cotutelle', 'supervision'],
}


def get_active_parent(tab_name):
    return next((parent for parent, children in TAB_TREE.items() if tab_name in children), None)


@register.inclusion_tag('admission/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs(context, admission=None):
    valid_tabs = {}  # FIXME
    return {
        'valid_tabs': valid_tabs,
        'tab_tree': TAB_TREE,
        'active_parent': get_active_parent(context['request'].resolver_match.url_name),
        'admission': admission,
        'detail_view': not isinstance(context['view'], FormView),
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'request': context['request'],
    }


@register.inclusion_tag('admission/doctorate_subtabs_bar.html', takes_context=True)
def doctorate_subtabs(context, admission=None):
    subtab_labels = {
        'person': _("Identification"),
        'coordonnees': _("Contact details"),
        'education': _("Secondary studies"),
        'curriculum': _("Curriculum"),
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
    return {
        'subtabs': TAB_TREE.get(get_active_parent(context['request'].resolver_match.url_name), []),
        'subtab_labels': subtab_labels,
        'admission': admission,
        'detail_view': not isinstance(context['view'], FormView),
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'request': context['request'],
    }


@register.inclusion_tag('admission/field_data.html')
def field_data(name, data=None, css_class=None, hide_empty=False):
    if isinstance(data, list):
        template_string = "{% load osis_document %}{% if files %}{% document_visualizer files %}{% endif %}"
        template_context = {'files': data}
        data = template.Template(template_string).render(template.Context(template_context))
    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
    }


@register_inclusion_with_body('panel.html', takes_context=True, context_name='panel_body')
def panel(context, title='', **kwargs):
    """
    Template tag for panel
    :param title: the panel title
    :type context: django.template.context.RequestContext
    """
    context['title'] = title
    context['attributes'] = kwargs
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
