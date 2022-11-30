# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils.functional import cached_property
from django.views.generic import TemplateView

from admission.constants import BE_ISO_CODE

# Do not remove the following import as it is used by enum_display templatetag
from admission.contrib.enums.curriculum import *
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.views.common.detail_tabs.curriculum_experiences import initialize_field_texts
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)

__all__ = ['AdmissionCurriculumDetailView']


class AdmissionCurriculumDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/doctorate/details/curriculum.html'
    service_mapping = {
        'create': AdmissionPersonService,
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    tab_of_specific_questions = Onglets.CURRICULUM.name

    @cached_property
    def curriculum(self):
        return self.service_mapping[self.current_context].get_curriculum(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        curriculum = self.curriculum

        context_data['professional_experiences'] = curriculum.professional_experiences
        context_data['educational_experiences'] = curriculum.educational_experiences
        context_data['minimal_year'] = curriculum.minimal_year

        context_data['BE_ISO_CODE'] = BE_ISO_CODE

        initialize_field_texts(self.request.user.person, context_data['educational_experiences'])

        return context_data
