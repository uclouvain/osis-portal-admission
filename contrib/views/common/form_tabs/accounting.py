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
from django.views.generic import FormView

from admission.contrib.forms.accounting import AccountingForm
from admission.contrib.views.common.detail_tabs.accounting import BaseAdmissionAccountingView
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['DoctorateAdmissionAccountingFormView']


class DoctorateAdmissionAccountingFormView(BaseAdmissionAccountingView, WebServiceFormMixin, FormView):
    template_name = 'admission/forms/accounting.html'
    form_class = AccountingForm

    update_accounting = {
        'doctorate': AdmissionPropositionService.update_doctorate_accounting,
        'general-education': AdmissionPropositionService.update_general_accounting,
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_general_admission'] = self.is_general
        kwargs['with_assimilation'] = self.with_assimilation
        if self.is_general:
            kwargs['education_site'] = self.admission.formation.campus

        kwargs['has_ue_nationality'] = self.accounting.get('a_nationalite_ue')
        kwargs['last_french_community_high_education_institutes_attended'] = self.accounting.get(
            'derniers_etablissements_superieurs_communaute_fr_frequentes'
        )
        return kwargs

    def get_initial(self):
        return self.accounting

    def call_webservice(self, data):
        self.update_accounting[self.current_context](
            person=self.person,
            uuid=self.admission_uuid,
            data=data,
        )
