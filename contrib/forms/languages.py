# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.languages_knowledge import LanguageKnowledgeGrade
from admission.contrib.forms import get_language_initial_choices

MANDATORY_LANGUAGES = ["EN", "FR"]


class SliderWidget(forms.widgets.TextInput):
    def __init__(self, choices=None, attrs=None):
        attrs = attrs or {}
        attrs.update({
            "data-provide": "slider",
            "data-slider-ticks": json.dumps([number for number in range(1, len(choices) + 1)]),
            "data-slider-ticks-labels": json.dumps([choice.name for choice in choices]),
            "data-slider-min": "1",
            "data-slider-max": str(len(choices)),
            "data-slider-step": "1",
        })
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        return self.choices[int(data.get(name)) - 1][0]

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

    def __init__(self, *args, person=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = False
        self.fields["language"].widget.choices = get_language_initial_choices(
            self.data.get(self.add_prefix("language"), self.initial.get("language")),
            person,
        )
        if self.initial.get("language") in MANDATORY_LANGUAGES:
            self.fields["language"].disabled = True
            self.fields["language"].help_text = _("Mandatory language")


class DoctorateAdmissionLanguagesBaseFormset(forms.BaseFormSet):

    def clean(self):
        # TODO check for unicity with languages
        super().clean()

    def __init__(self, *args, initial=None, **kwargs):
        if initial is None:
            initial = list()
        for mandatory_language in MANDATORY_LANGUAGES:
            if mandatory_language not in [initial_form_data.get("language") for initial_form_data in initial]:
                initial.insert(0, {"language": mandatory_language})  # always add mandatory languages
        super().__init__(*args, initial=initial, **kwargs)


DoctorateAdmissionLanguagesKnowledgeFormSet = forms.formset_factory(
    DoctorateAdmissionLanguageForm,
    formset=DoctorateAdmissionLanguagesBaseFormset,
    extra=0,
)
