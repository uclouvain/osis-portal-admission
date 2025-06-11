# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

import functools
import re
from contextlib import suppress
from dataclasses import dataclass
from inspect import getfullargspec
from typing import Union

from bootstrap3.forms import render_field
from bootstrap3.renderers import FieldRenderer
from bootstrap3.utils import add_css_class
from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import EMPTY_VALUES
from django.shortcuts import resolve_url
from django.template.defaultfilters import unordered_list
from django.test import override_settings
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_admission_sdk.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from osis_admission_sdk.model.membre_cadto_nested import MembreCADTONested
from osis_admission_sdk.model.promoteur_dto_nested import PromoteurDTONested

from admission.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from admission.contrib.enums import (
    ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
    IN_PROGRESS_STATUSES,
    ActorType,
    ChoixEtatSignature,
    ChoixMoyensDecouverteFormation,
    ChoixStatutPropositionContinue,
    ChoixStatutPropositionDoctorale,
    ChoixStatutPropositionGenerale,
)
from admission.contrib.enums.specific_question import (
    TYPES_ITEMS_LECTURE_SEULE,
    TypeItemFormulaire,
)
from admission.contrib.enums.training_choice import (
    ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE,
)
from admission.contrib.forms.supervision import DoctorateAdmissionMemberSupervisionForm
from admission.services.proposition import (
    BUSINESS_EXCEPTIONS_BY_TAB,
    AdmissionSupervisionService,
)
from admission.services.reference import (
    CountriesService,
    LanguageService,
    SuperiorInstituteService,
)
from admission.utils import (
    format_academic_year,
    format_school_title,
    get_uuid_value,
    to_snake_case,
)

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

    def __str__(self):
        return self.name


TAB_TREES = {
    'create': {
        Tab('personal', _('Personal data'), 'id-card'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('training', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('experience', _('Previous experience'), 'person-walking-luggage'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
            Tab('languages', _('Knowledge of languages')),
        ],
    },
    'doctorate': {
        Tab('personal', _('Personal data'), 'id-card'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('training-choice', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('experience', _('Previous experience'), 'person-walking-luggage'): [
            Tab('curriculum', _('Curriculum')),
            Tab('languages', _('Knowledge of languages')),
        ],
        Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
            Tab('accounting', _('Additional information')),
        ],
        Tab('doctorate', pgettext_lazy('tab name', 'Research'), 'person-chalkboard'): [
            Tab('project', pgettext_lazy('tab name', 'Research')),
            Tab('cotutelle', _('Cotutelle')),
            Tab('supervision', _('Support committee')),
        ],
        Tab('confirm-submit', _('Finalise application'), 'flag'): [
            Tab('confirm-submit', _('Confirmation and submission')),
        ],
        Tab('documents', _('Documents'), 'folder-open'): [
            Tab('documents', _('Documents')),
        ],
    },
    'general-education': {
        Tab('personal', _('Personal data'), 'id-card'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('general-education', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('experience', _('Previous experience'), 'person-walking-luggage'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
            Tab('exam', _('Exam')),
        ],
        Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
            Tab('accounting', _('Accounting')),
            Tab('specific-questions', _('Specific aspects')),
        ],
        Tab('confirm-submit', _('Finalise application'), 'flag'): [
            Tab('confirm-submit', _('Confirmation and submission')),
        ],
        Tab('documents', _('Documents'), 'folder-open'): [
            Tab('documents', _('Documents')),
        ],
    },
    'continuing-education': {
        Tab('personal', _('Personal data'), 'id-card'): [
            Tab('person', _('Identification')),
            Tab('coordonnees', _('Contact details')),
        ],
        Tab('continuing-education', _('Course choice'), 'person-chalkboard'): [
            Tab('training-choice', _('Course choice')),
        ],
        Tab('experience', _('Previous experience'), 'person-walking-luggage'): [
            Tab('education', _('Secondary studies')),
            Tab('curriculum', _('Curriculum')),
        ],
        Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
            Tab('specific-questions', _('Specific aspects')),
        ],
        Tab('confirm-submit', _('Finalise application'), 'flag'): [
            Tab('confirm-submit', _('Confirmation and submission')),
        ],
        Tab('documents', _('Documents'), 'folder-open'): [
            Tab('documents', _('Documents')),
        ],
    },
}


def _get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


@register.filter
def can_make_action(admission, action_name):
    """Return true if the specified action can be applied for this admission, otherwise return False"""
    if not admission:
        return False
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
        for parent_tab, sub_tabs in tab_tree.items():
            # Get the accessible sub tabs depending on the user permissions
            valid_sub_tabs = [tab for tab in sub_tabs if _can_access_tab(admission, tab.name, READ_ACTIONS_BY_TAB)]
            # Only add the parent tab if at least one sub tab is allowed
            if len(valid_sub_tabs) > 0:
                valid_tab_tree[parent_tab] = valid_sub_tabs

        return valid_tab_tree

    return tab_tree


def get_current_tab_name(context):
    match = context['request'].resolver_match
    namespace_size = len(match.namespaces)
    if namespace_size > 3:
        # Sub tabs - update mode (e.g: admission:doctorate:update:curriculum:experience_detail)
        return match.namespaces[3]
    if namespace_size == 3 and match.namespaces[2] != 'update':
        # Sub tabs - read mode (e.g: admission:doctorate:curriculum:experience_detail)
        return match.namespaces[2]
    # Main tabs (e.g: admission:doctorate:curriculum or admission:doctorate:update:curriculum)
    return match.url_name


@register.inclusion_tag('admission/tags/admission_tabs_bar.html', takes_context=True)
def admission_tabs(context, admission=None, with_submit=False):
    """Display current tabs given context (if with_submit=True, display the submit button within tabs)"""
    current_tab_name = get_current_tab_name(context)

    # Create a new tab tree based on the default one but depending on the permissions links
    tab_tree = get_current_tab_tree(context)
    context['tab_tree'] = get_valid_tab_tree(tab_tree, admission)

    return {
        'active_parent': _get_active_parent(tab_tree, current_tab_name),
        'admission': admission,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'with_submit': with_submit,
        'no_status': admission and admission.statut not in IN_PROGRESS_STATUSES,
        **context.flatten(),
    }


def get_subtab_label(tab_name, tab_tree_name):
    return next(
        subtab for subtabs in TAB_TREES[tab_tree_name].values() for subtab in subtabs if subtab.name == tab_name
    ).label  # pragma : no branch


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    current_tab_name = get_current_tab_name(context)
    current_tab_tree = get_current_tab_tree(context)
    return current_tab_tree.get(_get_active_parent(current_tab_tree, current_tab_name), [])


@register.simple_tag(takes_context=True)
def get_current_parent_tab(context):
    current_tab_name = get_current_tab_name(context)
    current_tab_tree = get_current_tab_tree(context)
    return _get_active_parent(current_tab_tree, current_tab_name)


@register.simple_tag(takes_context=True)
def get_current_tab(context):
    current_tab_name = get_current_tab_name(context)
    current_tab_tree = get_current_tab_tree(context)
    return next(
        (tab for subtabs in current_tab_tree.values() for tab in subtabs if tab.name == current_tab_name),
        None,
    )


@register.inclusion_tag('admission/tags/admission_subtabs_bar.html', takes_context=True)
def admission_subtabs(context, admission=None, tabs=None):
    """Display current subtabs given context (if tabs is specified, display provided tabs)"""
    current_tab_name = get_current_tab_name(context)
    return {
        'subtabs': tabs or current_subtabs(context),
        'admission': admission,
        'admission_uuid': context['view'].kwargs.get('pk', ''),
        'no_status': admission and admission.statut not in IN_PROGRESS_STATUSES,
        'active_tab': current_tab_name,
        **context.flatten(),
    }


def get_current_tab_tree(context):
    namespaces = context['request'].resolver_match.namespaces
    return TAB_TREES.get(namespaces[1])


@register.simple_tag(takes_context=True)
def get_detail_url(context, tab_name, pk, base_namespace=''):
    if not base_namespace:
        base_namespace = ':'.join(context['request'].resolver_match.namespaces[:2])
    return resolve_url('{}:{}'.format(base_namespace, tab_name), pk=pk)


@register.inclusion_tag('admission/tags/field_data.html')
def field_data(
    name,
    data=None,
    css_class=None,
    hide_empty=False,
    translate_data=False,
    inline=False,
    html_tag='',
    empty_value=_('Incomplete field'),
    tooltip=None,
):
    if isinstance(data, list):
        template_string = "{% load osis_document %}{% if files %}{% document_visualizer files %}{% endif %}"
        template_context = {'files': data}
        data = template.Template(template_string).render(template.Context(template_context))

    elif type(data) == bool:
        data = _('Yes') if data else _('No')
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
        'empty_value': empty_value,
        'tooltip': tooltip,
    }


@register_panel('admission/tags/panel.html', takes_context=True)
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
def split(string: str, delimiter=','):
    return string.split(delimiter)


@register.filter
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value


@register.filter
def can_read_tab(admission, tab):
    """Return true if the specified tab can be opened in reading mode for this admission, otherwise return False"""
    return _can_access_tab(admission, str(tab), READ_ACTIONS_BY_TAB)


@register.filter
def can_update_tab(admission, tab):
    """Return true if the specified tab can be opened in writing mode for this admission, otherwise return False"""
    return _can_access_tab(admission, str(tab), UPDATE_ACTIONS_BY_TAB)


@register.filter
def add_str(arg1, arg2):
    """Return the concatenation of two arguments."""
    return f'{arg1}{arg2}'


@register.simple_tag(takes_context=True)
def has_error_in_tab(context, admission, tab):
    """Return true if the tab (or subtab) has errors"""
    if not admission or not hasattr(admission, 'erreurs'):
        return False
    if tab not in BUSINESS_EXCEPTIONS_BY_TAB:
        children = get_current_tab_tree(context).get(tab)
        if children is None:
            raise ImproperlyConfigured(f"{tab} has no children and is not in BUSINESS_EXCEPTIONS_BY_TAB, correct name")
        return any(
            erreur['status_code'] in [e.value for e in BUSINESS_EXCEPTIONS_BY_TAB[subtab]]
            for subtab in children
            for erreur in admission.erreurs
        )
    return any(
        erreur['status_code'] in [e.value for e in BUSINESS_EXCEPTIONS_BY_TAB[tab]] for erreur in admission.erreurs
    )


@register.inclusion_tag('admission/tags/bootstrap_field_with_tooltip.html')
def bootstrap_field_with_tooltip(field, classes='', show_help=False, html_tooltip=False, label_class=''):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
        'html_tooltip': html_tooltip,
        'label_class': label_class,
    }


class NoPostWidgetRenderFieldRenderer(FieldRenderer):
    def post_widget_render(self, html):
        # Override rendering to prevent replacing <ul><li> with <div> in value
        classes = add_css_class('checkbox', self.get_size_class())
        mapping = [
            (rf'<ul id="id_{self.field.name}">\s*<li>', '<div><div class="{klass}">'.format(klass=classes)),
            (r"</label>\s*</li>\s*</ul>", "</label></div></div>"),
        ]
        for k, v in mapping:
            html = re.sub(k, v, html)
        return html


@register.simple_tag
def bootstrap_field_no_post_widget_render(field, **kwargs):
    # Override rendering to prevent bootstrap3 replacing <ul><li> with <div> in value
    with override_settings(
        BOOTSTRAP3={
            "field_renderers": {
                'default': '',
                'custom': 'admission.templatetags.admission.NoPostWidgetRenderFieldRenderer',
            }
        }
    ):
        return render_field(field, layout='custom', **kwargs)


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
            ret, val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(reduce_list_separated(val, next(iterargs, None)))
        elif nextarg in ["-", ':']:
            ret, val = ret[:-1], next(iter(ret[-1:]), '')
            ret.append(reduce_list_separated(val, next(iterargs, None), separator=f" {nextarg} "))
        elif isinstance(nextarg, str) and len(nextarg) > 1 and re.match(r'\s', nextarg[0]):
            ret, suffixed_val = ret[:-1], next(iter(ret[-1:]), '')
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


@register.filter
def status_list(admission):
    statuses = {str(admission['status'])}
    for child in admission['children']:
        statuses.add(str(child['status']))
    return ','.join(statuses)


@register.filter
def get_academic_year(year: Union[int, str]):
    """Return the academic year related to a specific year."""
    return format_academic_year(year)


@register.filter
def snake_case(value):
    return to_snake_case(str(value))


@register.simple_tag(takes_context=True)
def get_country_name(context, iso_code: str):
    """Return the country name."""
    if not iso_code:
        return ''
    translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'
    result = CountriesService.get_country(iso_code=iso_code, person=context['request'].user.person)
    return getattr(result, translated_field, '')


@register.inclusion_tag('admission/tags/multiple_field_data.html')
def multiple_field_data(configurations, data, title=_('Specific aspects')):
    """Display the answers of the specific questions based on a list of configurations and a data dictionary"""
    current_language = get_language()

    if not data:
        data = {}

    for field in configurations:
        if field.type in TYPES_ITEMS_LECTURE_SEULE:
            field['value'] = field.text.get(current_language, '')
        elif field.type == TypeItemFormulaire.DOCUMENT.name:
            field['value'] = [get_uuid_value(token) for token in data.get(field.uuid, [])]
        elif field.type == TypeItemFormulaire.SELECTION.name:
            current_value = data.get(field.uuid)
            selected_options = set(current_value) if isinstance(current_value, list) else {current_value}
            field['value'] = ', '.join(
                [value.get(current_language) for value in field['values'] if value.get('key') in selected_options]
            )
        else:
            field['value'] = data.get(field.uuid)

        field['translated_title'] = field.title.get(current_language)

    return {
        'fields': configurations,
        'title': title,
    }


@register.filter
def admission_training_type(osis_training_type: str):
    return ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(osis_training_type)


@register.filter(is_safe=False)
def default_if_none_or_empty(value, arg):
    """If value is None or empty, use given default."""
    return value if value not in EMPTY_VALUES else arg


@register.simple_tag
def interpolate(string, **kwargs):
    """Interpolate variables inside a string"""
    return string % kwargs


@register.simple_tag
def admission_status(status: str, osis_education_type: str):
    """Get the status of a specific admission"""
    admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(osis_education_type)
    status_enum = {
        'general-education': ChoixStatutPropositionGenerale,
        'continuing-education': ChoixStatutPropositionContinue,
        'doctorate': ChoixStatutPropositionDoctorale,
    }.get(admission_context)
    return status_enum.get_value(status)


@register.simple_tag(takes_context=True)
def edit_external_member_form(context, membre: Union['PromoteurDTONested', 'MembreCADTONested']):
    """Get an edit form"""
    initial = membre.to_dict()
    initial['pays'] = initial['code_pays']
    return DoctorateAdmissionMemberSupervisionForm(
        prefix=f"member-{membre.uuid}",
        person=context['user'].person,
        initial=initial,
    )


@register.filter
def diplomatic_post_name(diplomatic_post):
    """Get the name of a diplomatic post"""
    if diplomatic_post:
        return diplomatic_post.get('nom_francais' if get_language() == settings.LANGUAGE_CODE else 'nom_anglais')


@register.simple_tag
def form_fields_are_empty(form, *fields):
    """Return True if the form fields are empty."""
    return all(form[field_name].value() in form[field_name].field.empty_values for field_name in fields)


@register.simple_tag
def value_if_all(value, *conditions):
    """Return the value if all conditions are true."""
    return value if all(conditions) else ''


@register.simple_tag
def value_if_any(value, *conditions):
    """Return the value if any condition is true."""
    return value if any(conditions) else ''


@register.filter
def format_ways_to_find_out_about_the_course(proposition):
    """
    Format the list of ways to find out about the course of a proposition.
    :param proposition: The proposition
    :return: An unordered list of ways to find out about the course (including the "other" case, if any)
    """
    return unordered_list(
        [
            (
                ChoixMoyensDecouverteFormation.get_value(way)
                if way != ChoixMoyensDecouverteFormation.AUTRE.name
                else proposition.autre_moyen_decouverte_formation or ChoixMoyensDecouverteFormation.AUTRE.value
            )
            for way in proposition.moyens_decouverte_formation
        ]
    )


@register.simple_tag(takes_context=True)
def get_language_name(context, code):
    """Return the label of the language associated to the iso code."""
    if not code:
        return ''
    language = LanguageService.get_language(code=code, person=context['request'].user.person)
    if get_language() == settings.LANGUAGE_CODE:
        return language.name
    return language.name_en


@register.simple_tag(takes_context=True)
def get_superior_institute_name(context, organisation_uuid):
    """Return the label of the institute associated to the uuid."""
    if not organisation_uuid:
        return ''
    institute = SuperiorInstituteService.get_superior_institute(
        person=context['request'].user.person,
        uuid=organisation_uuid,
    )
    return mark_safe(format_school_title(institute))


@register.filter
def can_edit_supervision_member(admission, type):
    if type == ActorType.PROMOTER.name:
        return admission.get('statut') == ChoixStatutPropositionDoctorale.EN_BROUILLON.name
    elif type == ActorType.CA_MEMBER.name:
        return admission.get('statut') in [
            ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            ChoixStatutPropositionDoctorale.CA_A_COMPLETER.name,
            ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE.name,
        ]


@register.simple_tag(takes_context=True)
def is_ca_all_approved(context, admission):
    if admission.statut != ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE.name:
        return False
    supervision = AdmissionSupervisionService.get_supervision(
        person=context['request'].user.person,
        uuid=admission.uuid,
    ).to_dict()
    return all(
        signature.get('statut') == ChoixEtatSignature.APPROVED.name
        for signature in supervision.get('signatures_promoteurs', []) + supervision.get('signatures_membres_ca', [])
    )
