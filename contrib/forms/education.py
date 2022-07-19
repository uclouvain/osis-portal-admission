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
from dal import autocomplete, forward
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.secondary_studies import (
    BelgianCommunitiesOfEducation,
    DiplomaResults,
    DiplomaTypes,
    EDUCATIONAL_TYPES,
    Equivalence,
    ForeignDiplomaTypes,
    GotDiploma,
)
from admission.contrib.forms import (
    get_country_initial_choices,
    get_high_school_initial_choices,
    get_language_initial_choices,
    get_past_academic_years_choices,
    EMPTY_CHOICE,
)
from admission.services.reference import CountriesService
from base.tests.factories.academic_year import get_current_year
from osis_document.contrib import FileUploadField


class DoctorateAdmissionEducationForm(forms.Form):
    got_diploma = forms.ChoiceField(
        label=_("Do you have a high school diploma?"),
        choices=GotDiploma.choices(),
        widget=forms.RadioSelect,
        required=False,
        help_text='{}<br><br>{}'.format(
            _(
                "High school in Belgium is the level of education between the end of primary school and the "
                "beginning of higher education."
            ),
            _(
                "The high school diploma is the Certificate of Higher Secondary Education (CESS). "
                "It is commonly referred to as the baccalaureate in many countries."
            ),
        ),
    )
    academic_graduation_year = forms.IntegerField(
        label=_("Please mention the academic graduation year"),
        widget=autocomplete.ListSelect2,
        required=False,
    )
    diploma_type = forms.ChoiceField(
        label=_("This is a diploma from"),
        choices=DiplomaTypes.choices(),
        widget=forms.RadioSelect,
        required=False,
    )
    high_school_diploma = FileUploadField(
        label=_("High school diploma"),
        max_files=1,
        required=False,
    )
    enrolment_certificate = FileUploadField(
        label=_("Certificate of enrolment or school attendance"),
        max_files=1,
        required=False,
    )
    first_cycle_admission_exam = FileUploadField(
        label=_("Certificate of successful completion of the admission test for the first cycle of higher education"),
        max_files=1,
        required=False,
    )

    class Media:
        js = ("js/dependsOn.min.js",)

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["academic_graduation_year"].widget.choices = get_past_academic_years_choices(person)

        belgian_diploma = self.initial.get("belgian_diploma")
        foreign_diploma = self.initial.get("foreign_diploma")
        high_school_diploma_alternative = self.initial.get("high_school_diploma_alternative")

        diploma = belgian_diploma or foreign_diploma
        # Tick the got_diploma checkbox only if there is a saved diploma
        # and select the correct related type
        if diploma:
            self.fields["got_diploma"].initial = GotDiploma.YES.name
            if diploma.get("academic_graduation_year") == get_current_year():
                self.fields["got_diploma"].initial = GotDiploma.THIS_YEAR.name
            self.fields["diploma_type"].initial = (
                DiplomaTypes.BELGIAN.name if belgian_diploma else DiplomaTypes.FOREIGN.name
            )
            self.fields["academic_graduation_year"].initial = diploma.get("academic_graduation_year")
            self.fields['high_school_diploma'].initial = diploma.get("high_school_diploma")
            self.fields['enrolment_certificate'].initial = diploma.get("enrolment_certificate")
        else:
            self.fields["got_diploma"].initial = GotDiploma.NO.name
            if high_school_diploma_alternative:
                self.fields['first_cycle_admission_exam'].initial = high_school_diploma_alternative.get(
                    "first_cycle_admission_exam"
                )

    def clean(self):
        cleaned_data = super().clean()

        got_diploma = cleaned_data.get("got_diploma")

        if got_diploma in [GotDiploma.THIS_YEAR.name, GotDiploma.YES.name]:
            diploma_type = cleaned_data.get("diploma_type")
            if got_diploma == GotDiploma.YES.name:
                if not cleaned_data.get("academic_graduation_year"):
                    self.add_error('academic_graduation_year', FIELD_REQUIRED_MESSAGE)
                if not cleaned_data.get('high_school_diploma'):
                    self.add_error("high_school_diploma", FIELD_REQUIRED_MESSAGE)

            else:
                if diploma_type == DiplomaTypes.BELGIAN.name:
                    if not cleaned_data.get("high_school_diploma") and not cleaned_data.get("enrolment_certificate"):
                        self.add_error(
                            'high_school_diploma',
                            _('Please specify either your high school diploma or your enrolment certificate'),
                        )
                        self.add_error("enrolment_certificate", "")

            if not diploma_type:
                self.add_error('diploma_type', FIELD_REQUIRED_MESSAGE)

        elif got_diploma == GotDiploma.NO.name:
            if not cleaned_data.get('first_cycle_admission_exam'):
                self.add_error('first_cycle_admission_exam', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class DoctorateAdmissionEducationBelgianDiplomaForm(forms.Form):
    community = forms.ChoiceField(
        label=_("Educational community"),
        choices=EMPTY_CHOICE + BelgianCommunitiesOfEducation.choices(),
        widget=autocomplete.ListSelect2,
    )
    educational_type = forms.ChoiceField(
        label=_("Education type"),
        choices=EMPTY_CHOICE + EDUCATIONAL_TYPES,
        widget=autocomplete.ListSelect2,
        required=False,
    )
    educational_other = forms.CharField(
        label=_("If other education type, please specify"),
        required=False,
    )
    institute = forms.CharField(
        label=_("Institute"),
        required=False,
        help_text=_("You can perform a search based on the location or postal code."),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:high-school",
            attrs={
                'data-minimum-input-length': 3,
            },
        ),
    )
    other_institute = forms.BooleanField(
        label=_("If you don't find your institute in the list, please specify"),
        required=False,
    )
    other_institute_name = forms.CharField(
        label=_("Other institute name"),
        required=False,
    )
    other_institute_address = forms.CharField(
        label=_("Other institute address"),
        required=False,
    )
    result = forms.ChoiceField(
        label=_("What result did you get?"),
        choices=DiplomaResults.choices(),
        widget=forms.RadioSelect,
    )

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['other_institute'] = bool(self.initial.get('other_institute_name'))
        self.fields['institute'].widget.choices = get_high_school_initial_choices(
            self.data.get(self.add_prefix("institute"), self.initial.get("institute")),
            person,
        )

    def clean(self):
        cleaned_data = super().clean()
        community = cleaned_data.get("community")
        educational_type = cleaned_data.get("educational_type")
        educational_other = cleaned_data.get("educational_other")

        if community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name and not (
            educational_type or educational_other
        ):
            self.add_error("educational_type", _("Educational type is required with this community of education"))

        if not cleaned_data.get("institute") and not cleaned_data.get("other_institute"):
            institute_error_msg = _("Please set one of institute or other institute fields")
            self.add_error("institute", institute_error_msg)
            self.add_error("other_institute", institute_error_msg)

        return cleaned_data


class HourField(forms.IntegerField):
    def __init__(self, *, max_value=None, min_value=0, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(max_value=max_value, min_value=min_value, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs['placeholder'] = ''
        return attrs


class DoctorateAdmissionEducationScheduleForm(forms.Form):
    # ancient language
    latin = HourField(label=_("Latin"))
    greek = HourField(label=_("Greek"))
    # sciences
    chemistry = HourField(label=_("Chemistry"))
    physic = HourField(label=_("Physic"))
    biology = HourField(label=_("Biology"))
    # modern languages
    german = HourField(label=_("German"))
    dutch = HourField(label=_("Dutch"))
    english = HourField(label=_("English"))
    french = HourField(label=_("French"))
    spanish = HourField(label=_("Spanish"))
    modern_languages_other_label = forms.CharField(
        label=_("Other"),
        help_text=_("If other language, please specify"),
        required=False,
        max_length=25,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    modern_languages_other_hours = HourField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    # other disciplines
    mathematics = HourField(label=_("Mathematics"))
    it = HourField(label=_("IT"))
    social_sciences = HourField(label=_("Social sciences"))
    economic_sciences = HourField(label=_("Economic sciences"))
    other_label = forms.CharField(
        label=_("Other"),
        help_text=_("If other optional domains, please specify"),
        required=False,
        max_length=25,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    other_hours = HourField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    def get_initial_for_field(self, field, field_name):
        # Set all hours fields to None if initial is 0, so that nothing is displayed in field
        if isinstance(field, HourField) and not self.initial.get(field_name):
            return None
        return super().get_initial_for_field(field, field_name)

    def clean(self):
        cleaned_data = super().clean()

        # At least a field is required
        if not any(cleaned_data.get(f) for f in self.fields):
            self.add_error(None, _("A field of the schedule must at least be set."))

        dependent_fields = [
            ("modern_languages_other_label", "modern_languages_other_hours"),
            ("other_label", "other_hours"),
        ]

        for label_field, hours_field in dependent_fields:
            label = cleaned_data.get(label_field)
            hours = cleaned_data.get(hours_field)
            if label and not hours:
                self.add_error(hours_field, _("hours are required"))
            if not label and hours:
                self.add_error(label_field, _("label is required"))

        # Set all hours fields to 0 if they have no value, because API rejects None
        for field in self.fields:
            if isinstance(self.fields[field], HourField) and not cleaned_data.get(field):
                cleaned_data[field] = 0

        return cleaned_data


class DoctorateAdmissionEducationForeignDiplomaForm(forms.Form):
    foreign_diploma_type = forms.ChoiceField(
        label=_("What diploma did you get (or will you get)?"),
        choices=ForeignDiplomaTypes.choices(),
        widget=forms.RadioSelect,
    )
    equivalence = forms.ChoiceField(
        label=_(
            "Has this diploma been subject to a decision of equivalence provided by the "
            "French-speaking community of Belgium?"
        ),
        required=False,
        choices=Equivalence.choices(),
        widget=forms.RadioSelect,
    )
    linguistic_regime = forms.CharField(
        label=_("Linguistic regime"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:language"),
        required=False,
    )
    other_linguistic_regime = forms.CharField(
        label=_("If other linguistic regime, please specify"),
        required=False,
    )
    country = forms.CharField(
        label=_("Organizing country"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:country",
            forward=[forward.Const(True, 'exclude_be')],
        ),
    )
    result = forms.ChoiceField(
        label=_("What result did you get?"),
        choices=DiplomaResults.choices(),
        widget=forms.RadioSelect,
    )
    high_school_transcript = FileUploadField(
        label=_("A transcript or your last year at high school"),
        max_files=1,
    )
    high_school_transcript_translation = FileUploadField(
        label=_(
            "A certified translation of your official transcript of marks for your final year of secondary education"
        ),
        max_files=1,
        required=False,
    )
    high_school_diploma_translation = FileUploadField(
        label=_("A certified translation of your high school diploma"),
        max_files=1,
        required=False,
    )
    enrolment_certificate_translation = FileUploadField(
        label=_("A certified translation of your certificate of enrolment or school attendance"),
        max_files=1,
        required=False,
    )
    final_equivalence_decision_not_ue = FileUploadField(
        label=_(
            "A double-sided copy of the final equivalence decision issued by the Ministry "
            "of the French Community of Belgium"
        ),
        help_text=_(
            "For any high-school diploma from a country outside the European Union, the admission request "
            "<strong>must contain the equivalence</strong> of your diploma delivered by the "
            "<a href='http://www.equivalences.cfwb.be/' target='_blank'>French Community</a> of Belgium."
        ),
        max_files=1,
        required=False,
    )
    final_equivalence_decision_ue = FileUploadField(
        label=_("A double-sided copy of the final equivalence decision"),
        help_text=_(
            "If you have a final equivalence decision issued by the "
            "<a href='http://www.equivalences.cfwb.be/' target='_blank'>French Community</a> of Belgium, you must "
            "provide a double-sided copy of this document."
        ),
        max_files=1,
        required=False,
    )
    equivalence_decision_proof = FileUploadField(
        label=_("Proof of the final equivalence decision"),
        help_text=_(
            "If you do not yet have a final equivalence decision issued by the "
            "<a href='http://www.equivalences.cfwb.be/' target='_blank'>French Community</a> of Belgium, you must "
            "provide a double-sided copy of this document as soon as possible. You are therefore asked to "
            "provide proof of the application in the meantime: receipt of the application and proof of payment, "
            "acknowledgement of receipt of the application, etc."
        ),
        max_files=1,
        required=False,
    )
    restrictive_equivalence_daes = FileUploadField(
        label=_("Diploma of Aptitude for Access to Higher Education (DAES)"),
        max_files=1,
        required=False,
    )
    restrictive_equivalence_admission_test = FileUploadField(
        label=_(
            "Certificate of successful completion of the admission test for the first "
            "cycle of higher education in case of restrictive equivalence"
        ),
        max_files=1,
        required=False,
    )

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.fields[
            'final_equivalence_decision_ue'
            if self.fields['country'].is_ue_country
            else 'final_equivalence_decision_not_ue'
        ].initial = self.initial.get('final_equivalence_decision')

    def clean(self):
        cleaned_data = super().clean()
        from admission.contrib.views.form_tabs.education import LINGUISTIC_REGIMES_WITHOUT_TRANSLATION

        if not cleaned_data.get("linguistic_regime") and not cleaned_data.get("other_linguistic_regime"):
            self.add_error("linguistic_regime", _("Please set either the linguistic regime or other field."))

        if (
            cleaned_data.get("linguistic_regime") not in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
            # Translation of transcript required depending on linguistic regime
            and not cleaned_data.get('high_school_transcript_translation')
        ):
            self.add_error("high_school_transcript_translation", FIELD_REQUIRED_MESSAGE)

        if cleaned_data.get('foreign_diploma_type') == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
            # Equivalence
            if self.fields['country'].is_ue_country:
                equivalence = cleaned_data.get('equivalence')
                if not equivalence:
                    self.add_error('equivalence', FIELD_REQUIRED_MESSAGE)
                elif equivalence == Equivalence.YES.name and not cleaned_data.get('final_equivalence_decision_ue'):
                    self.add_error('final_equivalence_decision_ue', FIELD_REQUIRED_MESSAGE)
                elif equivalence == Equivalence.PENDING.name and not cleaned_data.get('equivalence_decision_proof'):
                    self.add_error('equivalence_decision_proof', FIELD_REQUIRED_MESSAGE)
            elif not cleaned_data.get('final_equivalence_decision_not_ue'):
                self.add_error('final_equivalence_decision_not_ue', FIELD_REQUIRED_MESSAGE)

        return cleaned_data
