# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import RedirectView

__all__ = ['AdmissionRedirectView']
__namespace__ = False

from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.templatetags.admission import can_make_action


class AdmissionRedirectView(LoadDossierViewMixin, RedirectView):
    urlpatterns = {
        'doctorate': 'doctorate/<uuid:pk>/',
        'general-education': 'general-education/<uuid:pk>/',
        'continuing-education': 'continuing-education/<uuid:pk>/',
    }

    @property
    def current_context(self):
        return self.request.resolver_match.url_name

    @property
    def pattern_name(self):
        try:
            admission = self.admission
        except PermissionDenied:
            return 'admission:list'
        namespace = self.current_context

        if namespace == 'doctorate':
            if can_make_action(admission, 'retrieve_project'):
                return f'admission:{namespace}:project'

        if can_make_action(admission, 'retrieve_person'):
            return f'admission:{namespace}:person'
        if can_make_action(admission, 'update_documents'):
            return f'admission:{namespace}:update:documents'
        if can_make_action(admission, 'pay_after_submission'):
            return f'admission:{namespace}:payment'
        if can_make_action(admission, 'pay_after_request'):
            return f'admission:{namespace}:payment'

        return 'admission:list'

    def get_redirect_url(self, *args, **kwargs):
        """
        Override get_redirect_url to not include kwargs for the listing view.
        """
        pattern_name = self.pattern_name
        if pattern_name == 'admission:list':
            url = reverse(self.pattern_name)
        else:
            url = reverse(self.pattern_name, args=args, kwargs=kwargs)

        args = self.request.META.get('QUERY_STRING', '')
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        return url
