# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.additional_information import ChoixInscriptionATitre, ChoixTypeAdresseFacturation
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.forms.additional_information import ContinuingSpecificQuestionForm, GeneralSpecificQuestionForm
from admission.contrib.forms.pool_questions import PoolQuestionsForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import FormMixinWithSpecificQuestions, WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['SpecificQuestionsFormView']


class SpecificQuestionsFormView(LoadDossierViewMixin, WebServiceFormMixin, FormMixinWithSpecificQuestions, FormView):
    template_name = 'admission/forms/specific_question.html'
    tab_of_specific_questions = Onglets.INFORMATIONS_ADDITIONNELLES.name
    service_mapping = {
        'general-education': AdmissionPropositionService.update_general_specific_question,
        'continuing-education': AdmissionPropositionService.update_continuing_specific_question,
    }

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all(form.is_valid() for form in forms):
            self.service_mapping[self.current_context](
                person=self.person,
                uuid=self.admission_uuid,
                data=self.prepare_data(forms[0].cleaned_data),
            )
            if self.display_pool_questions_form:
                AdmissionPropositionService.update_pool_questions(
                    person=self.person,
                    uuid=self.admission_uuid,
                    data=forms[1].cleaned_data if self.pool_questions else {},
                )
            return HttpResponseRedirect(self.get_success_url())
        return self.form_invalid(forms)

    def call_webservice(self, data):
        # Replaced by the custom calls in post()
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        kwargs['extra_form_attrs'] = ' autocomplete="off"'
        kwargs['forms'] = self.get_forms()
        # Trick template to display form tag and buttons
        kwargs['form'] = next((form for form in kwargs['forms'] if form.visible_fields()), kwargs['forms'][0])
        kwargs['BE_ISO_CODE'] = BE_ISO_CODE
        # Put self.pool_questions first so that the API call is made and permissions are checked
        if self.pool_questions and self.display_pool_questions_form:
            kwargs['reorientation_pool_end_date'] = self.pool_questions['reorientation_pool_end_date']
            kwargs['modification_pool_end_date'] = self.pool_questions['modification_pool_end_date']
        return super().get_context_data(**kwargs)

    def get_forms(self):
        form_kwargs = self.get_form_kwargs()
        forms = [
            ContinuingSpecificQuestionForm(
                data=self.request.POST or None,
                form_item_configurations=form_kwargs['form_item_configurations'],
                person=self.person,
                initial=self.get_initial_data_for_continuing_form(),
                prefix='specific_questions',
            )
            if self.is_continuing
            else GeneralSpecificQuestionForm(
                self.request.POST or None,
                form_item_configurations=form_kwargs['form_item_configurations'],
                initial={
                    'documents_additionnels': self.admission.documents_additionnels,
                    'reponses_questions_specifiques': self.admission.reponses_questions_specifiques,
                },
                prefix='specific_questions',
            )
        ]
        if self.display_pool_questions_form and self.pool_questions:
            forms.append(
                PoolQuestionsForm(
                    self.request.POST or None,
                    initial=self.pool_questions,
                    prefix='pool_questions',
                )
            )
        return forms

    def get_initial_data_for_continuing_form(self):
        initial_data = self.admission.to_dict()
        adresse_facturation = initial_data.pop('adresse_facturation', '')
        if adresse_facturation:
            initial_data.update(
                {
                    'adresse_facturation_destinataire': adresse_facturation.get('destinataire'),
                    'street': adresse_facturation.get('rue'),
                    'street_number': adresse_facturation.get('numero_rue'),
                    'postal_box': adresse_facturation.get('boite_postale'),
                    'postal_code': adresse_facturation.get('code_postal'),
                    'city': adresse_facturation.get('ville'),
                    'country': adresse_facturation.get('pays'),
                }
            )
        return initial_data

    def prepare_data(self, value):
        if self.is_continuing:
            continuing_value = {
                'inscription_a_titre': value.get('inscription_a_titre'),
                'reponses_questions_specifiques': value.get('reponses_questions_specifiques'),
                'copie_titre_sejour': value.get('copie_titre_sejour')
                if self.admission.pays_nationalite_ue_candidat is False
                else [],
                'documents_additionnels': value.get('documents_additionnels'),
            }

            if value.get('inscription_a_titre') == ChoixInscriptionATitre.PROFESSIONNEL.name:
                for field in [
                    'nom_siege_social',
                    'numero_unique_entreprise',
                    'numero_tva_entreprise',
                    'adresse_mail_professionnelle',
                    'type_adresse_facturation',
                ]:
                    continuing_value[field] = value.get(field)

                if value.get('type_adresse_facturation') == ChoixTypeAdresseFacturation.AUTRE.name:
                    be_prefix = 'be_' if value.get('country') == BE_ISO_CODE else ''
                    continuing_value['adresse_facturation_rue'] = value.get('street')
                    continuing_value['adresse_facturation_numero_rue'] = value.get('street_number')
                    continuing_value['adresse_facturation_code_postal'] = value.get(f'{be_prefix}postal_code')
                    continuing_value['adresse_facturation_ville'] = value.get(f'{be_prefix}city')
                    continuing_value['adresse_facturation_pays'] = value.get('country')
                    continuing_value['adresse_facturation_destinataire'] = value.get('adresse_facturation_destinataire')
                    continuing_value['adresse_facturation_boite_postale'] = value.get('postal_box')
            return continuing_value

        return value

    @property
    def display_pool_questions_form(self):
        return (
            self.current_context == 'general-education'
            and self.admission.formation['type'] == TrainingType.BACHELOR.name
        )

    @cached_property
    def pool_questions(self):
        return AdmissionPropositionService.get_pool_questions(self.person, self.admission_uuid).to_dict()
