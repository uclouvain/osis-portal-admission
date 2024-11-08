# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import translation
from django.views import View

from base.models import person
from base.views.my_osis import url_to_redirect_after_language_change


class ChangeLanguageView(LoginRequiredMixin, View):

    name = 'change_language'

    def get(self, request, *args, **kwargs):
        person.change_language(request.user, kwargs['ui_language'])
        translation.activate(kwargs['ui_language'])
        request.session[translation.LANGUAGE_SESSION_KEY] = kwargs['ui_language']
        return redirect(url_to_redirect_after_language_change(request))
