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
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import get_language
from django.views.generic import TemplateView

# Do not remove the following import as it is used by enum_display templatetag
from admission.contrib.enums.curriculum import *

from admission.constants import BE_ISO_CODE
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.services.reference import CountriesService, LanguageService


class DoctorateAdmissionCurriculumDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/details/curriculum.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        proposition_uuid = str(self.kwargs.get('pk', ''))

        if proposition_uuid:
            context_data['admission'] = AdmissionPropositionService.get_proposition(
                person=self.request.user.person,
                uuid=proposition_uuid,
            )

        context_data['curriculum_experiences'] = AdmissionPersonService.list_curriculum_experiences(
            person=self.request.user.person,
            uuid=proposition_uuid,
        )

        context_data['curriculum_file'] = AdmissionPersonService.retrieve_curriculum_file(
            person=self.request.user.person,
            uuid=proposition_uuid,
        )

        context_data['BE_ISO_CODE'] = BE_ISO_CODE

        self.initialize_countries_and_linguistic_regimes(context_data['curriculum_experiences'])

        return context_data

    def initialize_countries_and_linguistic_regimes(self, curriculum_experiences):
        """
        Add into each experience, the names of the country and the linguistic regime.
        """
        is_supported_language = get_language() == settings.LANGUAGE_CODE

        for experience in curriculum_experiences:

            # Initialize the country
            if experience.country:
                country = CountriesService.get_country(
                    iso_code=experience.country,
                    person=self.request.user.person,
                )
                experience.country_name = country.name if is_supported_language else country.name_en

            # Initialize the linguistic regime
            if experience.linguistic_regime:
                linguistic_regime = LanguageService.get_language(
                    code=experience.linguistic_regime,
                    person=self.request.user.person,
                )
                experience.linguistic_regime_name = (
                    linguistic_regime.name if is_supported_language else linguistic_regime.name_en
                )
