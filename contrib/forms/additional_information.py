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
from dal import autocomplete
from dal.forward import Const
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.additional_information import ChoixInscriptionATitre, ChoixTypeAdresseFacturation
from admission.contrib.forms import AdmissionFileUploadField as FileUploadField, get_diplomatic_post_initial_choices
from admission.contrib.forms.coordonnees import DoctorateAdmissionAddressForm
from admission.contrib.forms.specific_question import ConfigurableFormMixin


class GeneralSpecificQuestionForm(ConfigurableFormMixin, forms.Form):
    configurable_form_field_name = 'reponses_questions_specifiques'

    documents_additionnels = FileUploadField(
        label=_(
            'You can add any document you feel is relevant to your application '
            '(supporting documents, proof of language level, etc.).'
        ),
        required=False,
        max_files=10,
    )

    poste_diplomatique = forms.IntegerField(
        label=_('Competent diplomatic post'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:diplomatic-post',
            attrs={
                'data-html': True,
                'data-allow-clear': 'true',
            },
        ),
    )

    def __init__(self, display_visa: bool, residential_country: str, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if display_visa:
            self.fields['poste_diplomatique'].required = True

            if residential_country:
                self.fields['poste_diplomatique'].widget.forward = [Const(residential_country, 'residential_country')]

            initial_code = self.initial.get('poste_diplomatique')
            submitted_code = self.data.get(self.add_prefix('poste_diplomatique'))

            self.fields['poste_diplomatique'].choices = get_diplomatic_post_initial_choices(
                diplomatic_post_code=int(submitted_code)
                if submitted_code and submitted_code.isdigit()
                else initial_code,
                person=person,
            )
            self.fields['poste_diplomatique'].widget.choices = self.fields['poste_diplomatique'].choices
        else:
            self.fields['poste_diplomatique'].disabled = True


class ContinuingSpecificQuestionForm(ConfigurableFormMixin, DoctorateAdmissionAddressForm):
    configurable_form_field_name = 'reponses_questions_specifiques'

    copie_titre_sejour = FileUploadField(
        label=_(
            "Please provide a copy of the residence permit covering the entire course, including the assessment test "
            "(except for online courses)."
        ),
        max_files=1,
        required=False,
    )
    inscription_a_titre = forms.ChoiceField(
        choices=ChoixInscriptionATitre.choices(),
        label=_('You are registering as'),
        widget=forms.RadioSelect,
    )
    nom_siege_social = forms.CharField(
        label=_('Head office name'),
        required=False,
    )
    numero_unique_entreprise = forms.CharField(
        label=_('Unique business number'),
        required=False,
    )
    numero_tva_entreprise = forms.CharField(
        label=_('VAT number'),
        required=False,
    )
    adresse_mail_professionnelle = forms.EmailField(
        label=_('Please enter your work email address'),
        required=False,
    )

    # Adresse facturation
    type_adresse_facturation = forms.ChoiceField(
        choices=ChoixTypeAdresseFacturation.verbose_choices(),
        label=_('I would like the billing address to be'),
        required=False,
        widget=forms.RadioSelect,
    )
    adresse_facturation_destinataire = forms.CharField(
        label=_('To the attention of'),
        required=False,
    )
    documents_additionnels = FileUploadField(
        label=_(
            'You can add any document you feel is relevant to your application '
            '(supporting documents, proof of language level, etc.).'
        ),
        required=False,
        max_files=10,
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'jquery.mask.min.js',
            'admission/formatter.js',
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_coordinates_fields = (
            self.data.get(self.add_prefix('inscription_a_titre')) == ChoixInscriptionATitre.PROFESSIONNEL.name
            and self.data.get(self.add_prefix('type_adresse_facturation')) == ChoixTypeAdresseFacturation.AUTRE.name
        )

    def clean(self):
        cleaned_data = super().clean()

        enrollment_as = cleaned_data.get('inscription_a_titre')

        professional_fields = [
            'nom_siege_social',
            'numero_unique_entreprise',
            'numero_tva_entreprise',
            'adresse_mail_professionnelle',
            'type_adresse_facturation',
        ]

        if enrollment_as == ChoixInscriptionATitre.PROFESSIONNEL.name:
            for field in professional_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
        else:
            for field in professional_fields:
                cleaned_data[field] = ''

        return cleaned_data
