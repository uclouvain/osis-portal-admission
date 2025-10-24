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
from dal import forward
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_document_components.widgets import HiddenFileWidget

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import HAS_DIPLOMA_CHOICES
from admission.contrib.enums.secondary_studies import (
    EDUCATIONAL_TYPES,
    BelgianCommunitiesOfEducation,
    DiplomaTypes,
    Equivalence,
    ForeignDiplomaTypes,
    GotDiploma,
)
from admission.contrib.forms import EMPTY_CHOICE
from admission.contrib.forms import AdmissionFileUploadField as FileUploadField
from admission.contrib.forms import (
    RadioBooleanField,
    autocomplete,
    get_country_initial_choices,
    get_high_school_initial_choices,
    get_language_initial_choices,
    get_past_academic_years_choices,
)
from admission.contrib.forms.specific_question import ConfigurableFormMixin
from admission.services.reference import AcademicYearService, CountriesService


def disable_fields(condition, fields, fields_to_keep_enabled_names=None):
    """
    Disable form fields if the condition is true.
    @param condition: The condition to check.
    @param fields: A dictionary of form fields.
    @param fields_to_keep_enabled_names: A set of field names to keep enabled.
    """

    if fields_to_keep_enabled_names is None:
        fields_to_keep_enabled_names = set()

    if condition:
        for field in fields:
            if field not in fields_to_keep_enabled_names:
                fields[field].disabled = True
                if isinstance(fields[field], FileUploadField):
                    fields[field].widget = HiddenFileWidget(display_visualizer=True)


class BaseAdmissionEducationForm(ConfigurableFormMixin):
    graduated_from_high_school = forms.ChoiceField(
        label=_("Do you have a secondary school diploma?"),
        widget=forms.RadioSelect,
        help_text='{}<br><br>{}'.format(
            _(
                "Secondary education in Belgium is the level of education between the end of primary school and the "
                "beginning of higher education."
            ),
            _(
                "The secondary school diploma is the Certificat d'Enseignement Secondaire Superieur "
                "(CESS, Certificate of Higher Secondary Education). It is commonly referred to in many countries as "
                "the baccalaureat."
            ),
        ),
    )
    graduated_from_high_school_year = forms.IntegerField(
        label=_('Please indicate the academic year in which you obtained your degree'),
        widget=autocomplete.ListSelect2,
        required=False,
    )

    def __init__(self, person, is_valuated, can_update_diploma, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_update_diploma = can_update_diploma
        self.is_valuated = is_valuated
        academic_years = AcademicYearService.get_academic_years(person)
        self.current_year = AcademicYearService.get_current_academic_year(person, academic_years)
        self.fields["graduated_from_high_school_year"].widget.choices = get_past_academic_years_choices(
            person,
            current_year=self.current_year,
            academic_years=academic_years,
        )
        self.fields['graduated_from_high_school'].choices = GotDiploma.choices_with_dynamic_year(self.current_year)

        disable_fields(
            condition=self.is_valuated,
            fields={
                field: self.fields[field]
                for field in [
                    'graduated_from_high_school_year',
                    'graduated_from_high_school',
                ]
            },
        )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('graduated_from_high_school') == GotDiploma.YES.name:

            if not cleaned_data.get('graduated_from_high_school_year'):
                self.add_error('graduated_from_high_school_year', FIELD_REQUIRED_MESSAGE)

        elif cleaned_data.get('graduated_from_high_school') == GotDiploma.THIS_YEAR.name:
            cleaned_data["graduated_from_high_school_year"] = self.current_year

        else:
            cleaned_data['graduated_from_high_school_year'] = None

        return cleaned_data

    class Media:
        js = ('js/dependsOn.min.js',)


class BachelorAdmissionEducationForm(BaseAdmissionEducationForm):
    diploma_type = forms.ChoiceField(
        label=pgettext_lazy("diploma_type", "It is a diploma"),
        choices=DiplomaTypes.choices(),
        widget=forms.RadioSelect,
        required=False,
    )
    high_school_diploma = FileUploadField(
        label=_("Secondary school diploma"),
        max_files=1,
        required=False,
        help_text=_('Secondary school diploma or, if not available, a certificate of enrolment or school attendance.'),
    )
    first_cycle_admission_exam = FileUploadField(
        label=_("Certificate of passing the bachelor's course entrance exam"),
        max_files=1,
        required=False,
    )
    first_cycle_admission_exam_year = forms.TypedChoiceField(
        label=_('Year of obtaining this proof'),
        widget=autocomplete.Select2(),
        coerce=int,
        required=False,
    )

    class Media:
        js = ("js/dependsOn.min.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        belgian_diploma = self.initial.get("belgian_diploma")
        foreign_diploma = self.initial.get("foreign_diploma")
        high_school_diploma_alternative = self.initial.get("high_school_diploma_alternative")

        self.fields['first_cycle_admission_exam_year'].choices = get_past_academic_years_choices(
            kwargs['person'],
            format_label_function=lambda academic_year: str(academic_year.year + 1),
        )

        diploma = belgian_diploma or foreign_diploma
        # Select the correct diploma type if one has been saved
        if diploma:
            self.fields["diploma_type"].initial = (
                DiplomaTypes.BELGIAN.name if belgian_diploma else DiplomaTypes.FOREIGN.name
            )
            self.fields['high_school_diploma'].initial = diploma.get("high_school_diploma")
        elif high_school_diploma_alternative:
            self.fields['first_cycle_admission_exam'].initial = high_school_diploma_alternative.get("certificate")
            self.fields['first_cycle_admission_exam_year'].initial = high_school_diploma_alternative.get("year")
        disable_fields(not self.can_update_diploma, self.fields, {self.configurable_form_field_name})

    def clean(self):
        cleaned_data = super().clean()

        if (
            self.can_update_diploma
            and cleaned_data.get("graduated_from_high_school") in HAS_DIPLOMA_CHOICES
            and not cleaned_data.get("diploma_type")
        ):
            self.add_error('diploma_type', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class BachelorAdmissionEducationBelgianDiplomaForm(forms.Form):
    community = forms.ChoiceField(
        label=_("Belgian education community"),
        choices=EMPTY_CHOICE + BelgianCommunitiesOfEducation.choices(),
        widget=autocomplete.ListSelect2,
    )
    educational_type = forms.ChoiceField(
        label=_("Secondary education type"),
        choices=EMPTY_CHOICE + EDUCATIONAL_TYPES,
        widget=autocomplete.ListSelect2,
        required=False,
    )
    has_other_educational_type = forms.BooleanField(
        label=_("Other education type"),
        required=False,
    )
    educational_other = forms.CharField(
        label=_("Name of the education type"),
        required=False,
        max_length=75,
    )
    institute = forms.CharField(
        label=_("Institute"),
        required=False,
        help_text=_("You can specify the locality or postcode in your search."),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:high-school",
            attrs={
                'data-html': True,
            },
            forward=['community'],
        ),
    )
    other_institute = forms.BooleanField(
        label=_("My institute is not on this list"),
        required=False,
    )
    other_institute_name = forms.CharField(
        label=_("Other institute name"),
        required=False,
        max_length=500,
    )
    other_institute_address = forms.CharField(
        label=_("Other institute address"),
        required=False,
        max_length=500,
    )

    def __init__(self, person, is_valuated, can_update_diploma, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['other_institute'] = bool(self.initial.get('other_institute_name'))
        self.initial['has_other_educational_type'] = bool(self.initial.get('educational_other'))
        self.fields['institute'].widget.choices = get_high_school_initial_choices(
            self.data.get(self.add_prefix("institute"), self.initial.get("institute")),
            person,
        )

        disable_fields(not can_update_diploma, self.fields)

    def clean(self):
        cleaned_data = super().clean()
        community = cleaned_data.get("community")
        has_other_educational_type = cleaned_data.get("has_other_educational_type")

        if has_other_educational_type:
            cleaned_data["educational_type"] = ""
        else:
            cleaned_data["educational_other"] = ""

        if community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
            if has_other_educational_type:
                if not cleaned_data.get("educational_other"):
                    self.add_error("educational_other", FIELD_REQUIRED_MESSAGE)
            elif not cleaned_data.get("educational_type"):
                self.add_error("educational_type", FIELD_REQUIRED_MESSAGE)

        other_institute = cleaned_data.get('other_institute')
        if other_institute:
            if not cleaned_data['other_institute_name']:
                self.add_error('other_institute_name', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data['other_institute_address']:
                self.add_error('other_institute_address', FIELD_REQUIRED_MESSAGE)

        elif not cleaned_data.get("institute"):
            institute_error_msg = _("Please choose the institute or specify another institute")
            self.add_error("institute", institute_error_msg)
            self.add_error("other_institute", '')

        return cleaned_data


class BachelorAdmissionEducationForeignDiplomaForm(forms.Form):
    foreign_diploma_type = forms.ChoiceField(
        label=_("What diploma have you obtained (or will obtain)?"),
        choices=ForeignDiplomaTypes.choices(),
        widget=forms.RadioSelect,
        help_text=mark_safe(
            "- <a href='https://www.eursc.eu/fr' target='_blank'>Schola Europae</a><br>"
            "- <a href='https://www.ibo.org/fr/programmes/find-an-ib-school' target='_blank'>IBO</a>"
        ),
    )
    equivalence = forms.ChoiceField(
        label=_("Has this diploma been recognised as equivalent by the French Community of Belgium?"),
        required=False,
        choices=Equivalence.choices(),
        widget=forms.RadioSelect,
    )
    linguistic_regime = forms.CharField(
        label=_("Language regime"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:language",
        ),
        required=False,
    )
    other_linguistic_regime = forms.CharField(
        label=_("If other language regime, specify"),
        required=False,
        max_length=25,
    )
    country = forms.CharField(
        label=_("Organising country"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:country-for-education",
            forward=[forward.Field('foreign_diploma_type')],
            attrs={
                "data-html": True,
            },
        ),
    )
    high_school_transcript = FileUploadField(
        label=_("A transcript for your last year of secondary school"),
        max_files=1,
        required=False,
    )
    high_school_transcript_translation = FileUploadField(
        label=_(
            "A translation of your official transcript of marks for your final year of secondary school "
            "by a sworn translator"
        ),
        max_files=1,
        required=False,
    )
    high_school_diploma_translation = FileUploadField(
        label=_("A translation of your secondary school diploma by a sworn translator"),
        max_files=1,
        required=False,
    )
    final_equivalence_decision_not_ue = FileUploadField(
        label=_(
            "Copy of both sides of the equivalency decision by the Ministry of the French-speaking Community of Belgium"
        ),
        help_text=_(
            "For any secondary school diploma from a country outside the European Union, the application for admission "
            "<strong>must contain the equivalency</strong> of your diploma issued by the "
            "<a href='http://www.equivalences.cfwb.be/' target='_blank'>French Community</a> of Belgium."
        ),
        max_files=2,
        required=False,
    )
    has_access_diploma_to_higher_education_not_ue = RadioBooleanField(
        label=_(
            'If your equivalency decision does not give access to the desired training, do you hold your diploma of '
            'aptitude for access to higher education (DAES)?'
        ),
        required=False,
        empty_value=False,
        initial=False,
    )
    access_diploma_to_higher_education_not_ue = FileUploadField(
        label=_('Diploma of aptitude for access to higher education (DAES)'),
        help_text=(
            "<a href='{link}' target='_blank'>{link}</a>".format(
                link='https://jurys.cfwb.be/jurys-secondaires/obtenir-mon-diplome/'
                'diplome-daptitude-a-acceder-a-lenseignement-superieur-daes/'
            )
        ),
        max_files=1,
        required=False,
    )
    final_equivalence_decision_ue = FileUploadField(
        label=_(
            "Copy of both sides of the equivalency decision by the Ministry of the French-speaking Community of Belgium"
        ),
        help_text=_(
            "If you have a final equivalence decision issued by the "
            "<a href='http://www.equivalences.cfwb.be/' target='_blank'>French Community</a> of Belgium, you must "
            "provide a double-sided copy of this document."
        ),
        max_files=2,
        required=False,
    )
    has_access_diploma_to_higher_education_ue = RadioBooleanField(
        label=_(
            'If your equivalency decision does not give access to the desired training, do you hold your diploma of '
            'aptitude for access to higher education (DAES)?'
        ),
        required=False,
        empty_value=False,
        initial=False,
    )
    access_diploma_to_higher_education_ue = FileUploadField(
        label=_(
            'If your equivalency decision does not give access to the desired training, please provide your diploma of '
            'aptitude for access to higher education (DAES)'
        ),
        help_text=(
            "<a href='{link}' target='_blank'>{link}</a>".format(
                link='https://jurys.cfwb.be/jurys-secondaires/obtenir-mon-diplome/'
                'diplome-daptitude-a-acceder-a-lenseignement-superieur-daes/'
            )
        ),
        max_files=1,
        required=False,
    )
    equivalence_decision_proof = FileUploadField(
        label=_("Proof of equivalency request"),
        help_text=_(
            "If you do not yet have a final equivalency decision from the <a href='http://www.equivalences.cfwb.be/' "
            "target='_blank'>French Community</a> of Belgium, provide a copy of both sides of it as soon as you "
            "receive it. In the meantime, you will be asked to provide proof that you have indeed requested it: postal "
            "receipt and proof of payment, acknowledgement of receipt of the application, etc."
        ),
        max_files=1,
        required=False,
    )

    def __init__(self, is_med_dent_training, person, is_valuated, can_update_diploma, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_med_dent_training = is_med_dent_training

        iso_code = self.data.get(self.add_prefix("country"), self.initial.get("country"))
        country = CountriesService.get_country(iso_code=iso_code, person=person) if iso_code else None

        self.fields['country'].is_ue_country = bool(country and country.european_union)
        self.fields['country'].widget.choices = get_country_initial_choices(
            iso_code=iso_code,
            person=person,
            loaded_country=country,
        )

        self.fields['linguistic_regime'].widget.choices = get_language_initial_choices(
            self.data.get(self.add_prefix("linguistic_regime"), self.initial.get("linguistic_regime")),
            person,
        )

        disable_fields(not can_update_diploma, self.fields)

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("linguistic_regime") and not cleaned_data.get("other_linguistic_regime"):
            self.add_error("linguistic_regime", _("Please choose the language regime or specify another regime."))

        if cleaned_data.get('foreign_diploma_type') == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
            # Equivalence
            if (self.fields['country'].is_ue_country or self.is_med_dent_training) and not cleaned_data.get(
                'equivalence'
            ):
                self.add_error('equivalence', FIELD_REQUIRED_MESSAGE)

        return cleaned_data
