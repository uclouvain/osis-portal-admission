# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms
from django.conf import settings
from django.utils.translation import get_language, gettext_lazy as _

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.bureau_CDE import ChoixBureauCDE
from admission.contrib.enums.experience_precedente import ChoixDoctoratDejaRealise
from admission.contrib.enums.projet import ChoixLangueRedactionThese
from admission.contrib.enums.financement import (
    BourseRecherche,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.contrib.forms import EMPTY_CHOICE
from admission.services.autocomplete import AdmissionAutocompleteAPIClient
from osis_document.contrib import FileUploadField


class DoctorateAdmissionProjectForm(forms.Form):
    type_admission = forms.ChoiceField(
        label=_("Admission type"),
        choices=AdmissionType.choices(),
        widget=forms.RadioSelect,
    )
    justification = forms.CharField(
        label=_("Brief justification"),
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': _("Detail here the reasons which justify the recourse to a provisory admission.")
        }),
        required=False,
    )
    bureau_cde = forms.ChoiceField(
        label=_("Bureau"),
        choices=EMPTY_CHOICE + ChoixBureauCDE.choices(),
        required=False,
    )

    type_financement = forms.ChoiceField(
        label=_("Financing type"),
        choices=EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        required=False,
    )
    type_contrat_travail = forms.ChoiceField(
        label=_("Work contract type"),
        choices=EMPTY_CHOICE + ChoixTypeContratTravail.choices(),
        required=False,
    )
    type_contrat_travail_other = forms.CharField(
        label=_("Specify work contract"),
        required=False,
    )
    eft = forms.IntegerField(
        label=_("Full-time equivalent"),
        min_value=0,
        max_value=100,
        required=False,
    )
    bourse_recherche = forms.ChoiceField(
        label=_("Scholarship grant"),
        choices=EMPTY_CHOICE + BourseRecherche.choices(),
        required=False,
    )
    bourse_recherche_other = forms.CharField(
        label=_("Specify scholarship grant"),
        max_length=255,
        required=False,
    )
    duree_prevue = forms.IntegerField(
        label=_("Estimated time"),
        min_value=0,
        required=False,
    )
    temps_consacre = forms.IntegerField(
        label=_("Allocated time"),
        min_value=0,
        required=False,
    )

    titre_projet = forms.CharField(
        label=_("Project title"),
        required=False,
    )
    resume_projet = forms.CharField(
        label=_("Project resume"),
        required=False,
        widget=forms.Textarea,
    )
    documents_projet = FileUploadField(
        label=_("Project documents"),
        required=False,
    )
    graphe_gantt = FileUploadField(
        label=_("Gantt graph"),
        required=False,
    )
    proposition_programme_doctoral = FileUploadField(
        label=_("Doctoral project proposition"),
        required=False,
    )
    projet_formation_complementaire = FileUploadField(
        label=_("Complementary training project"),
        required=False,
    )
    langue_redaction_these = forms.ChoiceField(
        label=_("Thesis redacting language"),
        choices=ChoixLangueRedactionThese.choices(),
        initial=ChoixLangueRedactionThese.UNDECIDED.name,
        required=False,
    )
    doctorat_deja_realise = forms.ChoiceField(
        label=_("PhD already done"),
        choices=ChoixDoctoratDejaRealise.choices(),
        initial=ChoixDoctoratDejaRealise.NO.name,
        required=False,
    )
    institution = forms.CharField(
        label=_("Institution"),
        required=False,
    )
    date_soutenance = forms.DateField(
        label=_("Defense date"),
        required=False,
    )
    raison_non_soutenue = forms.CharField(
        label=_("No defense reason"),
        widget=forms.Textarea(attrs={
            'rows': 2,
        }),
        required=False,
    )

    class Media:
        js = ('dependsOn.min.js',)

    def __init__(self, hide_bureau_field=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set type_contrat_travail to OTHER if value is not from enum
        if (
                self.initial.get('type_contrat_travail')
                and self.initial['type_contrat_travail'] not in ChoixTypeContratTravail.choices()
        ):
            self.initial['type_contrat_travail_other'] = self.initial['type_contrat_travail']
            self.initial['type_contrat_travail'] = ChoixTypeContratTravail.OTHER.name

        # Set bourse_recherche to OTHER if value is not from enum
        if (
                self.initial.get('bourse_recherche')
                and self.initial['bourse_recherche'] not in BourseRecherche.choices()
        ):
            self.initial['bourse_recherche_other'] = self.initial['bourse_recherche']
            self.initial['bourse_recherche'] = BourseRecherche.OTHER.name

        # Remove Bureau if doctoral commission is not CDE
        if hide_bureau_field:
            self.fields['bureau_cde'].widget = forms.HiddenInput()


class DoctorateAdmissionProjectCreateForm(DoctorateAdmissionProjectForm):
    sector = forms.CharField(
        label=_("Sector"),
        widget=autocomplete.Select2(),
    )
    doctorate = forms.CharField(
        label=_("Doctorate"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:doctorate", forward=['sector']),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(hide_bureau_field=False, *args, **kwargs)
        self.fields['sector'].widget.choices = (
                [('', '-')]
                + [
                    (sector.sigle, "{sigle} - {intitule}".format(
                        sigle=sector.sigle,
                        intitule=sector.intitule_fr if get_language() == settings.LANGUAGE_CODE
                        else sector.intitule_en,
                    ))
                    for sector in AdmissionAutocompleteAPIClient().list_sector_dtos()
                ]
        )

        # If we have a POST value, set the doctorate
        data = kwargs.get('data', None)
        if data and data.get('doctorate'):
            # Populate doctorate choices
            doctorate = self.get_selected_doctorate(data.get('sector'), data.get('doctorate'))
            self.fields['doctorate'].widget.choices = [
                (
                    "{doctorat.sigle}-{doctorat.annee}".format(doctorat=doctorate),
                    "{sigle} - {intitule}".format(
                        sigle=doctorate.sigle,
                        intitule=doctorate.intitule_fr if get_language() == settings.LANGUAGE_CODE
                        else doctorate.intitule_en,
                    ),
                )
            ]
            # This is used in the template to make Bureau field appear
            self.doctorate_data = dict(
                id="{result.sigle}-{result.annee}".format(result=doctorate),
                sigle_entite_gestion=doctorate.sigle_entite_gestion,
            )

    @staticmethod
    def get_selected_doctorate(sector, doctorat):
        doctorats = AdmissionAutocompleteAPIClient().list_doctorat_dtos(sector)
        return next(
            d for d in doctorats
            if doctorat == "{doctorat.sigle}-{doctorat.annee}".format(doctorat=d)
        )
