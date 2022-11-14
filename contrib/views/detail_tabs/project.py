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
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from admission.contrib.enums.projet import ChoixStatutProposition
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.organisation import EntitiesService
from admission.utils import format_entity_title


class DoctorateAdmissionProjectDetailView(LoadDossierViewMixin, TemplateView):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/details/project.html'

    def get(self, request, *args, **kwargs):
        # Always redirect to update form as long as signatures are not sent
        if (
            self.admission.statut == ChoixStatutProposition.IN_PROGRESS.name
            and 'url' in self.admission.links['update_proposition']
        ):
            return redirect('admission:doctorate:update:project', **self.kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        # There is a bug with translated strings with percent signs
        # https://docs.djangoproject.com/en/3.2/topics/i18n/translation/#troubleshooting-gettext-incorrectly-detects-python-format-in-strings-with-percent-signs
        # xgettext:no-python-format
        context_data['fte_label'] = _("Full-time equivalent (as %)")
        # xgettext:no-python-format
        context_data['allocated_time_label'] = _("Allocated time for the thesis (in %)")

        # Lookup sector label from API
        context_data['sector_label'] = [
            s.intitule
            for s in AdmissionAutocompleteService.get_sectors(self.request.user.person)
            if s.sigle == context_data['admission'].code_secteur_formation
        ][0]

        # Replace the institute uuid with the formatted name
        if context_data['admission'].institut_these:
            institute = EntitiesService.get_ucl_entity(
                person=self.request.user.person,
                uuid=context_data['admission'].institut_these,
            )
            context_data['admission'].institut_these = format_entity_title(institute)

        return context_data
