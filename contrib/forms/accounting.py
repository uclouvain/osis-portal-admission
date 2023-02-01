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
from typing import Set

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, ngettext
from localflavor.generic.forms import BICFormField, IBAN_MIN_LENGTH

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.accounting import (
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
    LienParente,
)
from admission.contrib.forms import RadioBooleanField, get_example_text, AdmissionFileUploadField as FileUploadField
from admission.templatetags.admission import get_academic_year
from reference.services.iban_validator import (
    IBANValidatorService,
    IBANValidatorException,
    IBANValidatorRequestException,
)


class AccountingForm(forms.Form):
    dynamic_person_concerned = '<span class="relationship">the person concerned</span>'

    # Absence of debt
    attestation_absence_dette_etablissement = FileUploadField(
        label=_('Certificate stating the absence of debts towards the institution attended during the academic year'),
        required=False,
    )

    # Reduced registration fees
    demande_allocation_d_etudes_communaute_francaise_belgique = RadioBooleanField(
        label=mark_safe(
            _(
                "Have you applied for a <a href="
                'https://allocations-etudes.cfwb.be/etudes-superieures/'
                " "
                "target='_blank'>study allowance</a> from the French Community of Belgium?"
            )
        ),
        required=False,
    )
    enfant_personnel = RadioBooleanField(
        label=_('Are you the child of a member of the staff of the UCLouvain or the Martin V entity?'),
        required=False,
    )
    attestation_enfant_personnel = FileUploadField(
        label=_('Staff child certificate'),
        required=False,
    )

    # Assimilation
    type_situation_assimilation = forms.ChoiceField(
        choices=TypeSituationAssimilation.choices(),
        label=_('Please select the first assimilation situation that applies to you'),
        required=False,
        widget=forms.RadioSelect,
    )

    # Assimilation 1
    sous_type_situation_assimilation_1 = forms.ChoiceField(
        choices=ChoixAssimilation1.choices(),
        label=_('Choose among the following proposals'),
        required=False,
        widget=forms.RadioSelect,
    )
    carte_resident_longue_duree = FileUploadField(
        label=_('Copy of both sides of the EC long-term resident card (D card)'),
        required=False,
    )
    carte_cire_sejour_illimite_etranger = FileUploadField(
        label=_(
            "Copy of both sides of the Certificate of Registration in the Register of Foreigners CIRE - unlimited stay "
            "(B card) or copy of the foreigner's card - unlimited stay (C card)"
        ),
        required=False,
    )
    carte_sejour_membre_ue = FileUploadField(
        label=_('Copy of both sides of the residence card of a family member of a European Union citizen (F card)'),
        required=False,
    )
    carte_sejour_permanent_membre_ue = FileUploadField(
        label=_(
            'Copy of both sides of the permanent residence card of a family member of a European Union citizen '
            '(F+ card)'
        ),
        required=False,
    )

    # Assimilation 2
    sous_type_situation_assimilation_2 = forms.ChoiceField(
        choices=ChoixAssimilation2.choices(),
        label=_('Choose among the following proposals'),
        required=False,
        widget=forms.RadioSelect,
    )
    carte_a_b_refugie = FileUploadField(
        label=_('Copy of both sides of the A or B card (with "refugee" written on the back of the card)'),
        required=False,
    )
    annexe_25_26_refugies_apatrides = FileUploadField(
        label=_(
            'Copy of the Annex 25 or 26 completed by the Office of the Commissioner General for Refugees and '
            'Stateless Persons'
        ),
        required=False,
    )
    attestation_immatriculation = FileUploadField(
        label=_('Copy of the registration certificate "orange card"'),
        required=False,
    )
    carte_a_b = FileUploadField(
        label=_('Copy of both sides of the A or B Card'),
        required=False,
    )
    decision_protection_subsidiaire = FileUploadField(
        label=_("Copy of the decision of the Foreigners' Office confirming the granting of subsidiary protection"),
        required=False,
    )
    decision_protection_temporaire = FileUploadField(
        label=_("Copy of the decision of the Foreigners' Office confirming the granting of temporary protection"),
        required=False,
    )

    # Assimilation 3
    sous_type_situation_assimilation_3 = forms.ChoiceField(
        choices=ChoixAssimilation3.choices(),
        label=_('Choose among the following proposals'),
        required=False,
        widget=forms.RadioSelect,
    )

    titre_sejour_3_mois_professionel = FileUploadField(
        label=_('Copy of both sides of the residence permit valid for more than 3 months'),
        required=False,
    )
    fiches_remuneration = FileUploadField(
        label=_('Copy of 6 salary slips issued in the 12 months preceding the application'),
        required=False,
    )
    titre_sejour_3_mois_remplacement = FileUploadField(
        label=_('Copy of both sides of the residence permit valid for more than 3 months'),
        required=False,
    )
    preuve_allocations_chomage_pension_indemnite = FileUploadField(
        label=_('Proof of receipt of unemployment benefit, pension or compensation from the mutual insurance company'),
        required=False,
    )

    # Assimilation 4
    attestation_cpas = FileUploadField(
        label=_('Recent certificate of support from the CPAS'),
        required=False,
    )

    # Assimilation 5
    relation_parente = forms.ChoiceField(
        choices=LienParente.choices(),
        label=_('Tick the relationship'),
        required=False,
        widget=forms.RadioSelect,
    )
    sous_type_situation_assimilation_5 = forms.ChoiceField(
        choices=ChoixAssimilation5.choices(),
        label=_('Choose among the following proposals'),
        required=False,
        widget=forms.RadioSelect,
    )
    composition_menage_acte_naissance = FileUploadField(
        label=_('Household composition, or a copy of your birth certificate'),
        required=False,
    )
    acte_tutelle = FileUploadField(
        label=_('Copy of the tutorship act authenticated by the Belgian authorities'),
        required=False,
    )
    composition_menage_acte_mariage = FileUploadField(
        label=_('Household composition or marriage certificate authenticated by the Belgian authorities'),
        required=False,
    )
    attestation_cohabitation_legale = FileUploadField(
        label=_('Certificate of legal cohabitation'),
        required=False,
    )
    carte_identite_parent = FileUploadField(
        label=mark_safe(
            _('Copy of both sides of the identity card of %(person_concerned)s')
            % {'person_concerned': dynamic_person_concerned}
        ),
        required=False,
    )
    titre_sejour_longue_duree_parent = FileUploadField(
        label=mark_safe(
            _(
                'Copy of both sides of the long-term residence permit in Belgium of %(person_concerned)s (B, C, D, F, '
                'F+ or M cards)'
            )
            % {'person_concerned': dynamic_person_concerned}
        ),
        required=False,
    )
    annexe_25_26_refugies_apatrides_decision_protection_parent = FileUploadField(
        label=mark_safe(
            _(
                "Copy of the Annex 25 or 26 or the A/B card mentioning the refugee status or copy of the decision of "
                "the Foreigners' Office confirming the temporary/subsidiary protection of %(person_concerned)s"
            )
            % {'person_concerned': dynamic_person_concerned}
        ),
        required=False,
    )
    titre_sejour_3_mois_parent = FileUploadField(
        label=mark_safe(
            _('Copy of both sides of your residence permit valid for more than 3 months of %(person_concerned)s')
            % {'person_concerned': dynamic_person_concerned}
        ),
        required=False,
    )
    fiches_remuneration_parent = FileUploadField(
        label=mark_safe(
            _(
                'Copy of the 6 salary slips issued in the 12 months preceding the application for registration or '
                'proof of receipt of unemployment benefit, pension or an indemnity from the mutual insurance company '
                'of %(person_concerned)s'
            )
            % {'person_concerned': dynamic_person_concerned}
        ),
        required=False,
    )
    attestation_cpas_parent = FileUploadField(
        label=mark_safe(
            _('Recent certificate of support from the CPAS of %(person_concerned)s')
            % {'person_concerned': dynamic_person_concerned}
        ),
        required=False,
    )

    # Assimilation 6
    sous_type_situation_assimilation_6 = forms.ChoiceField(
        choices=ChoixAssimilation6.choices(),
        label=_('Choose among the following proposals'),
        required=False,
        widget=forms.RadioSelect,
    )
    decision_bourse_cfwb = FileUploadField(
        label=_('Copy of the decision to grant the scholarship from the CFWB'),
        required=False,
    )
    attestation_boursier = FileUploadField(
        label=_(
            'Copy of the certificate of scholarship holder issued by the General Administration for '
            'Development Cooperation'
        ),
        required=False,
    )

    # Assimilation 7
    titre_identite_sejour_longue_duree_ue = FileUploadField(
        label=_(
            'Copy of both sides of the identity document proving the long-term stay in a member state of the European '
            'Union'
        ),
        required=False,
    )
    titre_sejour_belgique = FileUploadField(
        label=_('Copy of both sides of the residence permit in Belgium'),
        required=False,
    )

    # Affiliations
    affiliation_sport = forms.ChoiceField(
        label=mark_safe(
            _(
                "Do you wish to join the <a href='https://uclouvain.be/fr/etudier/sport/le-sport-uclouvain.html' "
                "target='_blank'>sports activities</a>? If so, the cost of this membership will be added to your "
                "registration fee."
            )
        ),
        widget=forms.RadioSelect,
        required=False,
    )
    etudiant_solidaire = RadioBooleanField(
        label=mark_safe(
            _(
                "Would you like to be a <a href='https://uclouvain.be/fr/decouvrir/carte-solidaire.html' "
                "target='_blank'>solidarity student</a>, a program proposed by Louvain Coopération, the NGO of "
                "UCLouvain? This affiliation will give you access to a fund for your solidarity projects. If so, the "
                "cost of this affiliation, which is 12 EUR, will be added to your registration fees."
            )
        ),
    )

    # Bank account
    type_numero_compte = forms.ChoiceField(
        choices=ChoixTypeCompteBancaire.choices(),
        label=_('Would you like to enter an account number so that we can process a refund if necessary?'),
        widget=forms.RadioSelect,
    )
    numero_compte_iban = forms.CharField(
        label=_('IBAN account number'),
        min_length=IBAN_MIN_LENGTH,
        max_length=34,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('BE43 0689 9999 9501'),
            },
        ),
        help_text=mark_safe(
            _(
                'The IBAN consists of up to 34 alphanumeric characters, corresponding to:'
                '<ul>'
                '<li>the country code (two letters)</li>'
                '<li>the check digits (two digits)</li>'
                '<li>the Basic Bank Account Number (BBAN) (up to 30 alphanumeric characters)</li>'
                '</ul>'
            )
        ),
    )
    numero_compte_autre_format = forms.CharField(
        label=_('Account number'),
        required=False,
    )
    code_bic_swift_banque = BICFormField(
        label=_('BIC/SWIFT code identifying the bank from which the account was opened'),
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('GKCC BE BB'),
            },
        ),
        help_text=mark_safe(
            _(
                'The BIC/SWIFT code consists of 8 or 11 characters, corresponding to:'
                '<ul>'
                '<li>the institution or bank code (four letters)</li>'
                '<li>the country code (two letters)</li>'
                '<li>the location code (two letters or digits)</li>'
                '<li>the branch code (optional, three letters or digits)</li>'
                '</ul>'
            )
        ),
    )
    prenom_titulaire_compte = forms.CharField(
        label=_('First name of the account holder'),
        required=False,
    )
    nom_titulaire_compte = forms.CharField(
        label=_('Last name of the account holder'),
        required=False,
    )

    def __init__(self, is_general_admission, is_doctorate_admission, with_assimilation, **kwargs):
        self.is_general_admission = is_general_admission
        self.is_doctorate_admission = is_doctorate_admission
        self.with_assimilation = with_assimilation
        self.education_site = kwargs.pop('education_site', None)
        self.has_ue_nationality = kwargs.pop('has_ue_nationality', None)
        self.last_french_community_high_education_institutes_attended = kwargs.pop(
            'last_french_community_high_education_institutes_attended',
            None,
        )
        self.valid_iban = None

        super().__init__(**kwargs)

        if self.last_french_community_high_education_institutes_attended:
            names = self.last_french_community_high_education_institutes_attended.get('names')
            academic_year = self.last_french_community_high_education_institutes_attended.get('academic_year')

            self.fields['attestation_absence_dette_etablissement'].label = ngettext(
                'Certificate stating the absence of debts towards the institution attended during the academic year'
                ' %(academic_year)s: %(names)s.',
                'Certificates stating the absence of debts towards the institutions attended during the academic year'
                ' %(academic_year)s: %(names)s.',
                len(names),
            ) % {
                'academic_year': get_academic_year(academic_year),
                'names': ', '.join(names),
            }

        if self.is_general_admission:
            self.fields['demande_allocation_d_etudes_communaute_francaise_belgique'].required = True
            self.fields['enfant_personnel'].required = True
            self.fields['affiliation_sport'].required = True

            if self.education_site:
                self.fields['affiliation_sport'].choices = ChoixAffiliationSport.choices(self.education_site)

        if self.with_assimilation:
            self.fields['type_situation_assimilation'].required = True

    class Media:
        js = (
            'js/dependsOn.min.js',
            'jquery.mask.min.js',
        )

    ASSIMILATION_FILE_FIELDS = [
        'carte_resident_longue_duree',
        'carte_cire_sejour_illimite_etranger',
        'carte_sejour_membre_ue',
        'carte_sejour_permanent_membre_ue',
        'carte_a_b_refugie',
        'annexe_25_26_refugies_apatrides',
        'attestation_immatriculation',
        'carte_a_b',
        'decision_protection_subsidiaire',
        'decision_protection_temporaire',
        'titre_sejour_3_mois_professionel',
        'fiches_remuneration',
        'titre_sejour_3_mois_remplacement',
        'preuve_allocations_chomage_pension_indemnite',
        'attestation_cpas',
        'composition_menage_acte_naissance',
        'acte_tutelle',
        'composition_menage_acte_mariage',
        'attestation_cohabitation_legale',
        'carte_identite_parent',
        'titre_sejour_longue_duree_parent',
        'annexe_25_26_refugies_apatrides_decision_protection_parent',
        'titre_sejour_3_mois_parent',
        'fiches_remuneration_parent',
        'attestation_cpas_parent',
        'decision_bourse_cfwb',
        'attestation_boursier',
        'titre_identite_sejour_longue_duree_ue',
        'titre_sejour_belgique',
    ]

    ASSIMILATION_CHOICE_FIELDS = [
        'sous_type_situation_assimilation_1',
        'sous_type_situation_assimilation_2',
        'sous_type_situation_assimilation_3',
        'relation_parente',
        'sous_type_situation_assimilation_5',
        'sous_type_situation_assimilation_6',
    ]

    ASSIMILATION_FIELD_DEPENDENCIES = {
        'type_situation_assimilation': {
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name: {
                'sous_type_situation_assimilation_1',
            },
            TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name: {
                'sous_type_situation_assimilation_2',
            },
            TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name: {
                'sous_type_situation_assimilation_3',
            },
            TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name: {
                'attestation_cpas',
            },
            TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name: {
                'relation_parente',
                'sous_type_situation_assimilation_5',
            },
            TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name: {
                'sous_type_situation_assimilation_6',
            },
            TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name: {
                'titre_identite_sejour_longue_duree_ue',
                'titre_sejour_belgique',
            },
        },
        'sous_type_situation_assimilation_1': {
            ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name: {
                'carte_resident_longue_duree',
            },
            ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name: {
                'carte_cire_sejour_illimite_etranger',
            },
            ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE.name: {
                'carte_sejour_membre_ue',
            },
            ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE.name: {
                'carte_sejour_permanent_membre_ue',
            },
        },
        'sous_type_situation_assimilation_2': {
            ChoixAssimilation2.REFUGIE.name: {
                'carte_a_b_refugie',
            },
            ChoixAssimilation2.DEMANDEUR_ASILE.name: {
                'annexe_25_26_refugies_apatrides',
                'attestation_immatriculation',
            },
            ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name: {
                'carte_a_b',
                'decision_protection_subsidiaire',
            },
            ChoixAssimilation2.PROTECTION_TEMPORAIRE.name: {
                'decision_protection_temporaire',
            },
        },
        'sous_type_situation_assimilation_3': {
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name: {
                'titre_sejour_3_mois_professionel',
                'fiches_remuneration',
            },
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name: {
                'titre_sejour_3_mois_remplacement',
                'preuve_allocations_chomage_pension_indemnite',
            },
        },
        'relation_parente': {
            LienParente.PERE.name: {
                'composition_menage_acte_naissance',
            },
            LienParente.MERE.name: {
                'composition_menage_acte_naissance',
            },
            LienParente.TUTEUR_LEGAL.name: {
                'acte_tutelle',
            },
            LienParente.CONJOINT.name: {
                'composition_menage_acte_mariage',
            },
            LienParente.COHABITANT_LEGAL.name: {
                'attestation_cohabitation_legale',
            },
        },
        'sous_type_situation_assimilation_5': {
            ChoixAssimilation5.A_NATIONALITE_UE.name: {'carte_identite_parent'},
            ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE.name: {'titre_sejour_longue_duree_parent'},
            ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name: {
                'annexe_25_26_refugies_apatrides_decision_protection_parent'
            },
            ChoixAssimilation5.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name: {
                'titre_sejour_3_mois_parent',
                'fiches_remuneration_parent',
            },
            ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name: {
                'attestation_cpas_parent',
            },
        },
        'sous_type_situation_assimilation_6': {
            ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name: {
                'decision_bourse_cfwb',
            },
            ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name: {
                'attestation_boursier',
            },
        },
    }

    @classmethod
    def get_assimilation_required_fields(cls, field_name, data) -> Set[str]:
        current_fields = cls.ASSIMILATION_FIELD_DEPENDENCIES.get(field_name, {}).get(data[field_name], set())
        new_fields = set()
        for field in current_fields:
            if field in cls.ASSIMILATION_FIELD_DEPENDENCIES:
                new_fields |= cls.get_assimilation_required_fields(field, data)
        return current_fields.union(new_fields)

    def clean_numero_compte_iban(self):
        value = self.cleaned_data.get('numero_compte_iban')
        if value:
            try:
                IBANValidatorService.validate(value)
                self.valid_iban = True
            except IBANValidatorException as e:
                self.valid_iban = False
                raise ValidationError(e.message)
            except IBANValidatorRequestException:
                pass
        return value

    def clean_attestation_absence_dette_etablissement(self):
        if not self.last_french_community_high_education_institutes_attended:
            return []
        return self.cleaned_data.get('attestation_absence_dette_etablissement')

    def clean(self):
        cleaned_data = super().clean()

        if self.is_general_admission:
            if not cleaned_data.get('enfant_personnel'):
                cleaned_data['attestation_enfant_personnel'] = []

        if self.is_general_admission or self.is_doctorate_admission:
            # Assimilation
            self.clean_assimilation_fields(cleaned_data)

        # Bank account
        self.clean_bank_fields(cleaned_data)

        return cleaned_data

    def clean_assimilation_fields(self, cleaned_data):
        assimilation_required_fields = {}

        # Can have assimilation
        if self.has_ue_nationality is False:

            if cleaned_data.get('type_situation_assimilation'):
                assimilation_required_fields = self.get_assimilation_required_fields(
                    'type_situation_assimilation',
                    cleaned_data,
                )

        for field in self.ASSIMILATION_FILE_FIELDS:
            if field not in assimilation_required_fields:
                cleaned_data[field] = []

        for field in self.ASSIMILATION_CHOICE_FIELDS:
            if field in assimilation_required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data[field] = ''

    def clean_bank_fields(self, cleaned_data):
        type_numero_banque = cleaned_data.get('type_numero_compte')
        cleaned_data['iban_valide'] = self.valid_iban

        if type_numero_banque == ChoixTypeCompteBancaire.IBAN.name:
            if not cleaned_data.get('numero_compte_iban') and 'numero_compte_iban' not in self.errors:
                self.add_error('numero_compte_iban', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['numero_compte_iban'] = ''

        if type_numero_banque == ChoixTypeCompteBancaire.AUTRE_FORMAT.name:
            if not cleaned_data.get('numero_compte_autre_format'):
                self.add_error('numero_compte_autre_format', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('code_bic_swift_banque') and 'code_bic_swift_banque' not in self.errors:
                self.add_error('code_bic_swift_banque', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['numero_compte_autre_format'] = ''
            cleaned_data['code_bic_swift_banque'] = ''

        if not type_numero_banque or type_numero_banque == ChoixTypeCompteBancaire.NON.name:
            cleaned_data['prenom_titulaire_compte'] = ''
            cleaned_data['nom_titulaire_compte'] = ''
        else:
            if not cleaned_data.get('prenom_titulaire_compte'):
                self.add_error('prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('nom_titulaire_compte'):
                self.add_error('nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
