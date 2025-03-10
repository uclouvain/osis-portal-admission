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
from django.shortcuts import redirect
from django.utils.translation import gettext
from django.views.generic import FormView

from admission.contrib.enums.actor import ActorType, ChoixEtatSignature
from admission.contrib.forms.supervision import (
    ACTOR_EXTERNAL,
    EXTERNAL_FIELDS,
    DoctorateAdmissionSupervisionForm,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import (
    TAB_OF_BUSINESS_EXCEPTION,
    AdmissionSupervisionService,
)
from admission.templatetags.admission import TAB_TREES, can_read_tab

__all__ = [
    "DoctorateAdmissionSupervisionFormView",
]


class DoctorateAdmissionSupervisionFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/forms/supervision.html'
    form_class = DoctorateAdmissionSupervisionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supervision = AdmissionSupervisionService.get_supervision(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )
        context['supervision'] = supervision
        signature_conditions = AdmissionSupervisionService.get_signature_conditions(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )
        signatures_conditions_by_tab = self.format_signature_conditions(signature_conditions)
        context['signature_conditions'] = signatures_conditions_by_tab
        context['signature_conditions_number'] = len(signature_conditions)
        context['add_form'] = context.pop('form')  # Trick template to not add button
        context['all_approved'] = all(
            signature.get('statut') == ChoixEtatSignature.APPROVED.name
            for signature in supervision.get('signatures_promoteurs', []) + supervision.get('signatures_membres_ca', [])
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        kwargs['admission_status'] = self.admission.statut
        return kwargs

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if 'url' not in context['admission'].links['request_signatures']:
            return redirect('admission:doctorate:supervision', **self.kwargs)
        return self.render_to_response(context)

    def prepare_data(self, data):
        is_external = data.pop('internal_external') == ACTOR_EXTERNAL
        person = data.pop('person')
        if not is_external:
            matricule = person
            # Remove data about external actor
            data = {**data, **{f: '' for f in EXTERNAL_FIELDS}}
        else:
            matricule = ''
        return {
            'type': data['type'],
            'matricule': matricule,
            **data,
        }

    def call_webservice(self, data):
        return AdmissionSupervisionService.add_member(person=self.person, uuid=self.admission_uuid, **data)

    def format_signature_conditions(self, conditions):
        """
        Group the missing conditions by tab
        @param conditions:
        @return:
        """
        tabs_labels = {
            tab.name: tab.label
            for child_tabs in TAB_TREES['doctorate'].values()
            for tab in child_tabs
            if can_read_tab(self.admission, tab)
        }

        conditions_by_tab = {}

        for condition in conditions:
            tab_name = TAB_OF_BUSINESS_EXCEPTION.get(condition['status_code'])

            tab_label = tabs_labels.get(tab_name, gettext('Other'))

            if tab_label not in conditions_by_tab:
                conditions_by_tab[tab_label] = {}

            if condition['status_code'] not in conditions_by_tab[tab_label]:
                conditions_by_tab[tab_label][condition['status_code']] = []

            conditions_by_tab[tab_label][condition['status_code']].append(condition['detail'])

        return conditions_by_tab
