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
from dal import autocomplete, forward
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.experience_precedente import ChoixDoctoratDejaRealise
from admission.contrib.enums.financement import (
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.contrib.enums.projet import ChoixLangueRedactionThese
from admission.contrib.enums.proximity_commission import (
    ChoixProximityCommissionCDE,
    ChoixProximityCommissionCDSS,
    ChoixSousDomaineSciences,
)
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.forms import (
    CustomDateInput,
    EMPTY_CHOICE,
    SelectOrOtherField,
    get_thesis_location_initial_choices,
    get_scholarship_choices,
    AdmissionFileUploadField as FileUploadField,
)
from admission.services.autocomplete import AdmissionAutocompleteService

SCIENCE_DOCTORATE = 'SC3DP'

COMMISSION_CDSS = 'CDSS'

COMMISSIONS_CDE_CLSM = ['CDE', 'CLSM']


class DoctorateAdmissionProjectForm(forms.Form):
    type_admission = forms.ChoiceField(
        label=_("Admission type"),
        choices=AdmissionType.choices(),
        widget=forms.RadioSelect,
        initial=AdmissionType.ADMISSION.name,
    )
    justification = forms.CharField(
        label=_("Brief justification"),
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'placeholder': _("Detail here the reasons which justify the recourse to a provisory admission."),
            }
        ),
        required=False,
    )
    commission_proximite_cde = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixProximityCommissionCDE.choices(),
        required=False,
    )
    commission_proximite_cdss = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixProximityCommissionCDSS.choices(),
        required=False,
    )
    sous_domaine = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixSousDomaineSciences.choices(),
        required=False,
    )

    type_financement = forms.ChoiceField(
        label=_("Financing type"),
        choices=EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        required=False,
    )
    type_contrat_travail = SelectOrOtherField(
        label=_("Work contract type"),
        choices=EMPTY_CHOICE + ChoixTypeContratTravail.choices(),
        required=False,
        help_text=_("Specify the employer and your function"),
    )
    eft = forms.IntegerField(
        # xgettext:no-python-format
        label=_("Full-time equivalent (as %)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    bourse_recherche = forms.CharField(
        label=_("Scholarship grant"),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name, 'scholarship_type')],
        ),
    )
    autre_bourse_recherche = forms.CharField(
        label=_("If other scholarship, specify"),
        required=False,
    )
    bourse_date_debut = forms.DateField(
        label=_("Scholarship start date"),
        widget=CustomDateInput(),
        required=False,
    )
    bourse_date_fin = forms.DateField(
        label=_("Scholarship end date"),
        widget=CustomDateInput(),
        required=False,
    )
    bourse_preuve = FileUploadField(
        label=_("Scholarship proof"),
        required=False,
    )
    duree_prevue = forms.IntegerField(
        label=_("Estimated time to complete the doctorate (in months)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    temps_consacre = forms.IntegerField(
        # xgettext:no-python-format
        label=_("Allocated time for the thesis (in %)"),
        min_value=0,
        max_value=100,
        required=False,
    )

    lieu_these = forms.CharField(
        label=_("Thesis location"),
        required=False,
        help_text=_(
            "If known, indicate here the name of the laboratory, "
            "clinical service or research centre where the thesis will be conducted"
        ),
    )
    titre_projet = forms.CharField(
        label=_("Project title (max. 100 characters)"),
        required=False,
    )
    resume_projet = forms.CharField(
        label=_("Project resume (max. 2000 characters)"),
        required=False,
        widget=forms.Textarea,
    )
    documents_projet = FileUploadField(
        label=_("Research project"),
        required=False,
    )
    graphe_gantt = FileUploadField(
        label=_("Gantt graph"),
        required=False,
    )
    proposition_programme_doctoral = FileUploadField(
        label=_("Doctoral program proposition"),
        required=False,
    )
    projet_formation_complementaire = FileUploadField(
        label=_("Complementary training proposition"),
        required=False,
        help_text=_(
            "Depending on your previous experience and your research project, a complementary training "
            "to the doctoral training may be imposed by the DDC, for a maximum of 60 credits. If so, "
            "please indicate here a proposal for complementary training."
        ),
    )
    lettres_recommandation = FileUploadField(
        label=_("Recommendation letters"),
        required=False,
    )
    langue_redaction_these = forms.ChoiceField(
        label=_("Thesis redacting language"),
        choices=ChoixLangueRedactionThese.choices(),
        initial=ChoixLangueRedactionThese.UNDECIDED.name,
        required=False,
    )
    doctorat_deja_realise = forms.ChoiceField(
        label=_("Have you ever started or completed a PhD?"),
        choices=ChoixDoctoratDejaRealise.choices(),
        initial=ChoixDoctoratDejaRealise.NO.name,
        required=False,
        help_text=_(
            "Indicate here any previous doctoral course, completed or interrupted, "
            "in which you are no longer registered."
        ),
    )
    institution = forms.CharField(
        label=_("Institution"),
        required=False,
    )
    domaine_these = forms.CharField(
        label=_("Thesis domain"),
        required=False,
    )
    non_soutenue = forms.BooleanField(
        label=_("No defense"),
        required=False,
    )
    date_soutenance = forms.DateField(
        label=_("Defense date"),
        widget=CustomDateInput(),
        required=False,
    )
    raison_non_soutenue = forms.CharField(
        label=_("No defense reason"),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, hide_proximity_commission_fields=True, *args, **kwargs):
        self.person = getattr(self, 'person', kwargs.pop('person', None))
        super().__init__(*args, **kwargs)

        # Set proximity commission fields value from API data
        if self.initial.get('commission_proximite'):
            doctorate = self.get_selected_doctorate(
                self.initial.get('sector'),
                self.initial.get('doctorate'),
            )
            if doctorate.sigle_entite_gestion in COMMISSIONS_CDE_CLSM:
                self.initial['commission_proximite_cde'] = self.initial['commission_proximite']
            elif doctorate.sigle_entite_gestion == COMMISSION_CDSS:
                self.initial['commission_proximite_cdss'] = self.initial['commission_proximite']
            elif doctorate.sigle == SCIENCE_DOCTORATE:  # pragma: no branch
                self.initial['sous_domaine'] = self.initial['commission_proximite']

        # Hide proximity commission fields
        if hide_proximity_commission_fields:
            self.fields['commission_proximite_cde'].widget = forms.HiddenInput()
            self.fields['commission_proximite_cdss'].widget = forms.HiddenInput()
            self.fields['sous_domaine'].widget = forms.HiddenInput()

        # Add the specified thesis position in the choices of the related field
        self.fields['lieu_these'].widget.choices = get_thesis_location_initial_choices(
            self.data.get(self.add_prefix("lieu_these"), self.initial.get("lieu_these")),
        )
        if self.data.get(self.add_prefix("raison_non_soutenue"), self.initial.get("raison_non_soutenue")):
            self.fields['non_soutenue'].initial = True

        scholarship_uuid = self.data.get(self.add_prefix('bourse_recherche'), self.initial.get('bourse_recherche'))
        if scholarship_uuid:
            self.fields['bourse_recherche'].widget.choices = get_scholarship_choices(
                uuid=scholarship_uuid,
                person=self.person,
            )

    def clean(self):
        data = super().clean()

        # Some consistency checks
        if data.get('type_financement') == ChoixTypeFinancement.WORK_CONTRACT.name:
            if not data.get('type_contrat_travail'):
                self.add_error('type_contrat_travail', _("This field is required."))

            if not data.get('eft'):
                self.add_error('eft', _("This field is required."))

        elif data.get('type_financement') == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
            if data.get('bourse_recherche'):
                data['autre_bourse_recherche'] = ''
            elif data.get('autre_bourse_recherche'):
                data['bourse_recherche'] = ''
            else:
                self.add_error('bourse_recherche', _('This field is required.'))
                self.add_error('autre_bourse_recherche', '')

        if data.get('non_soutenue') and not data.get('raison_non_soutenue'):
            self.add_error('raison_non_soutenue', _("This field is required."))

        return data

    def get_selected_doctorate(self, sector, doctorat):
        doctorats = AdmissionAutocompleteService.get_doctorates(self.person, sector)
        return next(  # pragma: no branch
            d for d in doctorats if doctorat == "{doctorat.sigle}-{doctorat.annee}".format(doctorat=d)
        )
