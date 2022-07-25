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
import json

from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.languages_knowledge import LanguageKnowledgeGrade
from admission.contrib.forms import get_language_initial_choices
from osis_document.contrib import FileUploadField

MANDATORY_LANGUAGES = ["EN", "FR"]


class SliderWidget(forms.widgets.TextInput):
    def __init__(self, choices=None, attrs=None):
        attrs = attrs or {}
        attrs.update(
            {
                "data-provide": "slider",
                "data-slider-ticks": json.dumps([number for number in range(1, len(choices) + 1)]),
                "data-slider-ticks-labels": json.dumps([choice.name for choice in choices]),
                "data-slider-min": "1",
                "data-slider-max": str(len(choices)),
                "data-slider-step": "1",
            }
        )
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value is None:
            return value
        return self.choices[int(value) - 1][0]

    def format_value(self, value):
        if value:
            value = str(self.choices.index((value, value)) + 1)
        else:
            value = "1"  # initialize the widget default value to "1" instead of "5" by default
        self.attrs["data-slider-value"] = value
        return value

    class Media:
        js = ("bootstrap-slider.min.js",)
        css = {
            "all": ("bootstrap-slider.min.css",),
        }


class DoctorateAdmissionLanguageForm(forms.Form):
    language = forms.CharField(
        label=_("Language"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:language"),
    )
    listening_comprehension = forms.ChoiceField(
        label=_("Please rate your listening comprehension"),
        choices=LanguageKnowledgeGrade.choices(),
        widget=SliderWidget(choices=LanguageKnowledgeGrade),
    )
    speaking_ability = forms.ChoiceField(
        label=_("Please rate your speaking ability"),
        choices=LanguageKnowledgeGrade.choices(),
        widget=SliderWidget(choices=LanguageKnowledgeGrade),
    )
    writing_ability = forms.ChoiceField(
        label=_("Please rate your writing ability"),
        choices=LanguageKnowledgeGrade.choices(),
        widget=SliderWidget(choices=LanguageKnowledgeGrade),
    )
    certificate = FileUploadField(
        label=_("Certificate of language knowledge"),
        required=False,
        max_files=1,
        mimetypes=['application/pdf'],
    )

    def __init__(self, *args, person=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = False
        self.lang_code = self.data.get(self.add_prefix("language"), self.initial.get("language"))
        self.fields["language"].widget.choices = get_language_initial_choices(self.lang_code, person)
        if self.initial.get("language") in MANDATORY_LANGUAGES:
            self.fields["language"].disabled = True
            self.fields["language"].help_text = _("Mandatory language")

    class Media:
        js = ("jquery.formset.js",)


class DoctorateAdmissionLanguagesBaseFormset(forms.BaseFormSet):
    def clean(self):
        """Check that no language have been set more than once and that mandatory languages are set."""
        if any(self.errors):
            return
        languages = [form.cleaned_data.get("language") for form in self.forms]
        if not all(language in languages for language in MANDATORY_LANGUAGES):
            raise ValidationError(_("Mandatory languages are missing."))
        duplicate_languages = set([language for language in languages if languages.count(language) > 1])
        if duplicate_languages:
            for form in self.forms:
                if form.cleaned_data.get("language") in duplicate_languages:
                    form.add_error("language", _("This language is set more than once."))
            raise ValidationError(_("You cannot fill in a language more than once, please correct the form."))

    def __init__(self, *args, initial=None, **kwargs):
        for mandatory_language in MANDATORY_LANGUAGES:
            if mandatory_language not in [initial_form_data.get("language") for initial_form_data in initial]:
                initial.insert(0, {"language": mandatory_language})  # always add mandatory languages
        super().__init__(*args, initial=initial, **kwargs)


DoctorateAdmissionLanguagesKnowledgeFormSet = forms.formset_factory(
    DoctorateAdmissionLanguageForm,
    formset=DoctorateAdmissionLanguagesBaseFormset,
    extra=0,
)
