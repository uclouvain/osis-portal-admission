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
from django import template
from django.views.generic import DetailView

from admission.utils import admission_profile_valid_tabs

register = template.Library()


@register.inclusion_tag('admission/doctorate_tabs_bar.html', takes_context=True)
def doctorate_tabs(context, admission=None):
    if admission:
        valid_tabs = {}  # FIXME
    else:
        valid_tabs = admission_profile_valid_tabs(context['user'].person)
    return {
        'valid_tabs': valid_tabs,
        'admission': admission,
        'detail_view': isinstance(context['view'], DetailView),
    }


@register.inclusion_tag('admission/field_data.html')
def field_data(name, data=None, css_class=None):
    return {
        'name': name,
        'data': data,
        'css_class': css_class,
    }
