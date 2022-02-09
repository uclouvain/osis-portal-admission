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

# Do not remove the following import as it is used by enum_display templatetag
from django.utils.translation import get_language

from admission.contrib.enums.curriculum import *

from django.views.generic import TemplateView

from admission.constants import BE_ISO_CODE
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.services.reference import CountriesService, LanguageService


class DoctorateAdmissionCurriculumDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/detail_curriculum.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        proposition_uuid = str(self.kwargs.get('pk', ''))
        is_supported_language = get_language() == settings.LANGUAGE_CODE

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

        # Retrieve more information about the foreign key fields
        # Store previous data to prevent unnecessary requests
        retrieved_countries = dict()
        retrieved_linguistic_regimes = dict()

        for experience in context_data['curriculum_experiences']:

            # Initialize the country
            if experience.country:
                if experience.country in retrieved_countries:
                    experience.country = retrieved_countries.get(experience.country)
                else:
                    country = CountriesService.get_country(
                        iso_code=experience.country,
                        person=self.request.user.person,
                    )
                    experience.country_name = country.name if is_supported_language else country.name_en
                    retrieved_countries[experience.country] = experience.country_name

            # Initialize the linguistic regime
            if experience.linguistic_regime:
                if experience.linguistic_regime in retrieved_linguistic_regimes:
                    experience.linguistic_regime_name = retrieved_linguistic_regimes.get(experience.linguistic_regime)
                else:
                    linguistic_regime = LanguageService.get_language(
                        code=experience.linguistic_regime,
                        person=self.request.user.person,
                    )
                    experience.linguistic_regime_name = (
                        linguistic_regime.name if is_supported_language else linguistic_regime.name_en
                    )

        return context_data
