# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from dal import forward
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
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.forms import (
    autocomplete,
    CustomDateInput,
    EMPTY_CHOICE,
    SelectOrOtherField,
    get_thesis_location_initial_choices,
    get_scholarship_choices,
    AdmissionFileUploadField as FileUploadField,
    get_language_initial_choices,
    RadioBooleanField,
)
from admission.contrib.views.autocomplete import LANGUAGE_UNDECIDED
from admission.services.autocomplete import AdmissionAutocompleteService

SCIENCE_DOCTORATE = 'SC3DP'

COMMISSION_CDSS = 'CDSS'

COMMISSIONS_CDE_CLSM = ['CDE', 'CLSM']


class DoctorateAdmissionProjectForm(forms.Form):
    justification = forms.CharField(
        label=_("Brief justification"),
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'placeholder': _("Reasons for provisional admission."),
            }
        ),
        required=False,
    )
    commission_proximite_cde = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixCommissionProximiteCDEouCLSM.choices(),
        required=False,
    )
    commission_proximite_cdss = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixCommissionProximiteCDSS.choices(),
        required=False,
    )
    sous_domaine = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixSousDomaineSciences.choices(),
        required=False,
    )

    type_financement = forms.ChoiceField(
        label=_("Current funding"),
        choices=EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        required=False,
        help_text=_(
            "If you don't have any funding yet, please choose \"Self-funding\" and explain the"
            " considered funding in the \"Comment\" area."
        ),
    )
    type_contrat_travail = SelectOrOtherField(
        label=_("Work contract type"),
        choices=EMPTY_CHOICE + ChoixTypeContratTravail.choices(),
        required=False,
        help_text=_("Specify employer and function"),
    )
    eft = forms.IntegerField(
        # xgettext:no-python-format
        label=_("Full-time equivalent (as %)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    bourse_recherche = forms.CharField(
        label=_("Research scholarship"),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name, 'scholarship_type')],
        ),
    )
    autre_bourse_recherche = forms.CharField(
        label=_("If other scholarship, specify"),
        required=False,
        max_length=255,
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
        help_text=_("Scholarship end date prior to any possible renewal."),
    )
    bourse_preuve = FileUploadField(
        label=_("Proof of scholarship"),
        required=False,
        help_text=_(
            "For example, a contract, a letter from a supervisor, or any other document showing that you have been "
            "awarded the scholarship on the dates indicated."
        ),
    )
    duree_prevue = forms.IntegerField(
        label=_("Estimated time to complete the PhD (in months)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    temps_consacre = forms.IntegerField(
        # xgettext:no-python-format
        label=_("Time allocated for thesis (in %)"),
        min_value=0,
        max_value=100,
        required=False,
    )
    est_lie_fnrs_fria_fresh_csc = RadioBooleanField(
        label=_("Is your admission request linked with a FNRS, FRIA, FRESH or CSC application?"),
        required=False,
        initial=False,
    )
    commentaire_financement = forms.CharField(
        label=_("Comment"),
        required=False,
        widget=forms.Textarea,
    )

    lieu_these = forms.CharField(
        label=_("Thesis location"),
        required=False,
        help_text=_(
            "If known, indicate the name of the laboratory, clinical department or research centre where the thesis "
            "will be carried out"
        ),
        max_length=255,
    )
    titre_projet = forms.CharField(
        label=_("Project title (max. 100 characters)"),
        required=False,
        max_length=1023,
    )
    resume_projet = forms.CharField(
        label=_("Project resume (max. 2000 characters)"),
        help_text=_("Write your resume in the language decided with your accompanying committee."),
        required=False,
        widget=forms.Textarea,
    )
    documents_projet = FileUploadField(
        label=_("PhD research project"),
        required=False,
    )
    graphe_gantt = FileUploadField(
        label=_("Gantt chart"),
        required=False,
    )
    proposition_programme_doctoral = FileUploadField(
        label=_("PhD proposal"),
        required=False,
    )
    projet_formation_complementaire = FileUploadField(
        label=_("Complementary training proposition"),
        required=False,
        help_text=_(
            "Depending on your previous experience and your research project, the PhD Committee may require you to "
            "take additional PhD training, up to a maximum of 60 credits. If so, please indicate here a proposal "
            "for additional training."
        ),
    )
    lettres_recommandation = FileUploadField(
        label=_("Letters of recommendation"),
        required=False,
    )
    langue_redaction_these = forms.CharField(
        label=_("Thesis language"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:language",
            attrs={
                "data-html": True,
            },
            forward=(forward.Const(True, 'show_top_languages'),),
        ),
        required=False,
    )

    projet_doctoral_deja_commence = RadioBooleanField(
        label=_("Has your PhD project already started?"),
        required=False,
        initial=False,
    )
    projet_doctoral_institution = forms.CharField(
        label=_("Institution"),
        required=False,
        max_length=255,
    )
    projet_doctoral_date_debut = forms.DateField(
        label=_("Work start date"),
        widget=CustomDateInput(),
        required=False,
    )
    doctorat_deja_realise = forms.ChoiceField(
        label=_("Have you previously enrolled for a PhD?"),
        choices=ChoixDoctoratDejaRealise.choices(),
        initial=ChoixDoctoratDejaRealise.NO.name,
        required=False,
        help_text=_("Indicate any completed or interrupted PhD studies in which you are no longer enrolled."),
    )
    institution = forms.CharField(
        label=_("Institution in which the PhD has been realised / started."),
        required=False,
        max_length=255,
    )
    domaine_these = forms.CharField(
        label=_("Doctorate thesis field"),
        required=False,
        max_length=255,
    )
    non_soutenue = forms.BooleanField(
        label=_("No defense"),
        required=False,
    )
    date_soutenance = forms.DateField(
        label=_("Defence date"),
        widget=CustomDateInput(),
        required=False,
    )
    raison_non_soutenue = forms.CharField(
        label=_("No defense reason"),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        max_length=255,
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

        lang_code = self.data.get(self.add_prefix("langue_redaction_these"), self.initial.get("langue_redaction_these"))
        if lang_code == LANGUAGE_UNDECIDED:
            choices = ((LANGUAGE_UNDECIDED, _('Undecided')),)
        else:
            choices = get_language_initial_choices(lang_code, self.person)
        self.fields["langue_redaction_these"].widget.choices = choices

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
