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
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.additional_information import ChoixInscriptionATitre, ChoixTypeAdresseFacturation
from admission.contrib.forms.coordonnees import DoctorateAdmissionAddressForm
from admission.contrib.forms.specific_question import ConfigurableFormMixin


class ContinuingSpecificQuestionForm(ConfigurableFormMixin, DoctorateAdmissionAddressForm):
    configurable_form_field_name = 'reponses_questions_specifiques'

    inscription_a_titre = forms.ChoiceField(
        choices=ChoixInscriptionATitre.choices(),
        label=_('Are you registering as'),
        required=False,
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
        label=_('Please enter your professional e-mail address'),
        required=False,
    )

    # Adresse facturation
    type_adresse_facturation = forms.ChoiceField(
        choices=ChoixTypeAdresseFacturation.verbose_choices(),
        label=_('I want the billing address to be'),
        required=False,
        widget=forms.RadioSelect,
    )
    adresse_facturation_destinataire = forms.CharField(
        label=_('For the attention of'),
        required=False,
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'jquery.mask.min.js',
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.address_can_be_empty = not (
            self.data.get(self.add_prefix('inscription_a_titre')) == ChoixInscriptionATitre.PROFESSIONNEL.name
            and self.data.get(self.add_prefix('type_adresse_facturation')) == ChoixTypeAdresseFacturation.AUTRE.name
        )
