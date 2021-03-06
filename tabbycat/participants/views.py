from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.forms import HiddenInput
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy, ungettext
from django.utils.translation import ugettext as _
from django.views.generic.base import View
from django.views.generic import FormView

from actionlog.mixins import LogActionMixin
from actionlog.models import ActionLogEntry
from adjallocation.models import DebateAdjudicator
from adjfeedback.progress import FeedbackProgressForAdjudicator, FeedbackProgressForTeam
from draw.prefetch import populate_opponents
from results.models import TeamScore
from results.prefetch import populate_confirmed_ballots, populate_wins
from tournaments.mixins import (PublicTournamentPageMixin, SingleObjectByRandomisedUrlMixin,
                                SingleObjectFromTournamentMixin, TournamentMixin)
from tournaments.models import Round
from utils.misc import redirect_tournament, reverse_tournament
from utils.mixins import CacheMixin, ModelFormSetView, SuperuserRequiredMixin, VueTableTemplateView
from utils.tables import TabbycatTableBuilder

from .models import Adjudicator, Speaker, SpeakerCategory, Team
from . import forms


class TeamSpeakersJsonView(CacheMixin, SingleObjectFromTournamentMixin, View):

    model = Team
    pk_url_kwarg = 'team_id'
    cache_timeout = settings.TAB_PAGES_CACHE_TIMEOUT

    def get(self, request, *args, **kwargs):
        team = self.get_object()
        speakers = team.speakers
        data = {i: "<li>" + speaker.name + "</li>" for i, speaker in enumerate(speakers)}
        return JsonResponse(data, safe=False)


class BaseParticipantsListView(VueTableTemplateView):

    page_title = ugettext_lazy("Participants")
    page_emoji = '🚌'

    def get_tables(self):
        t = self.get_tournament()

        adjudicators = t.adjudicator_set.select_related('institution')
        adjs_table = TabbycatTableBuilder(view=self, title="Adjudicators", sort_key="Name")
        adjs_table.add_adjudicator_columns(adjudicators)

        speakers = Speaker.objects.filter(team__tournament=t).select_related(
                'team', 'team__institution').prefetch_related('team__speaker_set', 'categories')
        speakers_table = TabbycatTableBuilder(view=self, title="Speakers", sort_key="Name")
        speakers_table.add_speaker_columns(speakers)
        speakers_table.add_team_columns([speaker.team for speaker in speakers])

        return [adjs_table, speakers_table]


class ParticipantsListView(BaseParticipantsListView, SuperuserRequiredMixin, TournamentMixin):

    template_name = 'participants_list.html'


class PublicParticipantsListView(BaseParticipantsListView, PublicTournamentPageMixin, CacheMixin):

    public_page_preference = 'public_participants'


# ==============================================================================
# Team and adjudicator record pages
# ==============================================================================

class BaseRecordView(SingleObjectFromTournamentMixin, VueTableTemplateView):

    allow_null_tournament = True

    def get_context_data(self, **kwargs):
        kwargs['admin_page'] = self.admin
        kwargs['draw_released'] = self.get_tournament().current_round.draw_status == Round.STATUS_RELEASED
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)


class BaseTeamRecordView(BaseRecordView):

    model = Team
    template_name = 'team_record.html'

    def get_page_title(self):
        return _("Record for %(name)s") % {'name': self.object.long_name}

    def get_page_emoji(self):
        if self.get_tournament().pref('show_emoji'):
            return self.object.emoji

    def get_context_data(self, **kwargs):
        tournament = self.get_tournament()

        try:
            kwargs['debateteam'] = self.object.debateteam_set.select_related(
                'debate__round').prefetch_related('debate__round__motion_set').get(
                debate__round=tournament.current_round)
        except ObjectDoesNotExist:
            kwargs['debateteam'] = None

        kwargs['feedback_progress'] = FeedbackProgressForTeam(self.object, tournament)

        return super().get_context_data(**kwargs)

    def get_table(self):
        """On team record pages, the table is the results table."""
        tournament = self.get_tournament()
        teamscores = TeamScore.objects.filter(
            debate_team__team=self.object,
            ballot_submission__confirmed=True,
            debate_team__debate__round__draw_status=Round.STATUS_RELEASED
        ).select_related(
            'debate_team__debate__round'
        ).prefetch_related(
            Prefetch('debate_team__debate__debateadjudicator_set', queryset=DebateAdjudicator.objects.select_related('adjudicator__institution')),
            'debate_team__debate__debateteam_set'
        )
        if not tournament.pref('all_results_released'):
            teamscores = teamscores.filter(
                debate_team__debate__round__silent=False,
                debate_team__debate__round__seq__lt=tournament.current_round.seq
            )
        debates = [ts.debate_team.debate for ts in teamscores]
        populate_opponents([ts.debate_team for ts in teamscores])
        populate_confirmed_ballots(debates, motions=True, results=True)

        table = TabbycatTableBuilder(view=self, title="Results", sort_key="Round")
        table.add_round_column([debate.round for debate in debates])
        table.add_debate_result_by_team_columns(teamscores)
        table.add_debate_adjudicators_column(debates, show_splits=True)

        if self.admin or tournament.pref('public_motions'):
            table.add_motion_column([debate.confirmed_ballot.motion
                if debate.confirmed_ballot else None for debate in debates])

        table.add_debate_ballot_link_column(debates)

        return table


class BaseAdjudicatorRecordView(BaseRecordView):

    model = Adjudicator
    template_name = 'adjudicator_record.html'
    page_emoji = '⚖'

    def get_page_title(self):
        return _("Record for %(name)s") % {'name': self.object.name}

    def get_context_data(self, **kwargs):
        tournament = self.get_tournament()

        try:
            kwargs['debateadjudications'] = self.object.debateadjudicator_set.filter(
                debate__round=tournament.current_round
            ).select_related(
                'debate__round'
            ).prefetch_related(
                'debate__round__motion_set'
            )
        except ObjectDoesNotExist:
            kwargs['debateadjudications'] = None

        kwargs['feedback_progress'] = FeedbackProgressForAdjudicator(self.object, tournament)

        return super().get_context_data(**kwargs)

    def get_table(self):
        """On adjudicator record pages, the table is the previous debates table."""
        tournament = self.get_tournament()
        debateadjs = DebateAdjudicator.objects.filter(
            adjudicator=self.object,
            debate__round__draw_status=Round.STATUS_RELEASED
        ).select_related(
            'debate__round'
        ).prefetch_related(
            Prefetch('debate__debateadjudicator_set',
                queryset=DebateAdjudicator.objects.select_related('adjudicator__institution')),
            'debate__debateteam_set__team__speaker_set'
        )
        if not tournament.pref('all_results_released'):
            debateadjs = debateadjs.filter(
                debate__round__silent=False,
                debate__round__seq__lt=tournament.current_round.seq,
            )
        debates = [da.debate for da in debateadjs]
        populate_wins(debates)
        populate_confirmed_ballots(debates, motions=True, results=True)

        table = TabbycatTableBuilder(view=self, title=_("Previous Rounds"), sort_key="Round")
        table.add_round_column([debate.round for debate in debates])
        table.add_debate_results_columns(debates)
        table.add_debate_adjudicators_column(debates, show_splits=True, highlight_adj=self.object)

        if self.admin or tournament.pref('public_motions'):
            table.add_motion_column([debate.confirmed_ballot.motion
                if debate.confirmed_ballot else None for debate in debates])

        table.add_debate_ballot_link_column(debates)
        return table


class TeamRecordView(SuperuserRequiredMixin, BaseTeamRecordView):
    admin = True


class AdjudicatorRecordView(SuperuserRequiredMixin, BaseAdjudicatorRecordView):
    admin = True


class PublicTeamRecordView(PublicTournamentPageMixin, BaseTeamRecordView):
    public_page_preference = 'public_record'
    admin = False


class PublicAdjudicatorRecordView(PublicTournamentPageMixin, BaseAdjudicatorRecordView):
    public_page_preference = 'public_record'
    admin = False


# ==============================================================================
# Speaker categories
# ==============================================================================

class EditSpeakerCategoriesView(LogActionMixin, SuperuserRequiredMixin, TournamentMixin, ModelFormSetView):
    # The tournament is included in the form as a hidden input so that
    # uniqueness checks will work. Since this is a superuser form, they can
    # access all tournaments anyway, so tournament forgery wouldn't be a
    # security risk.

    template_name = 'speaker_categories_edit.html'
    formset_model = SpeakerCategory
    action_log_type = ActionLogEntry.ACTION_TYPE_SPEAKER_CATEGORIES_EDIT

    def get_formset_factory_kwargs(self):
        return {
            'fields': ('name', 'tournament', 'slug', 'seq', 'limit', 'public'),
            'extra': 2,
            'widgets': {
                'tournament': HiddenInput
            }
        }

    def get_formset_queryset(self):
        return SpeakerCategory.objects.filter(tournament=self.get_tournament())

    def get_formset_kwargs(self):
        return {
            'initial': [{'tournament': self.get_tournament()}] * 2,
        }

    def formset_valid(self, formset):
        result = super().formset_valid(formset)
        if self.instances:
            message = ungettext("Saved speaker category: %(list)s",
                "Saved speaker categories: %(list)s",
                len(self.instances)
            ) % {'list': ", ".join(category.name for category in self.instances)}
            messages.success(self.request, message)
        else:
            messages.success(self.request, _("No changes were made to the speaker categories."))
        if "add_more" in self.request.POST:
            return redirect_tournament('participants-speaker-categories-edit', self.get_tournament())
        return result

    def get_success_url(self, *args, **kwargs):
        return reverse_tournament('participants-list', self.get_tournament())


class EditSpeakerCategoryEligibilityFormView(LogActionMixin, SuperuserRequiredMixin, TournamentMixin, FormView):

    action_log_type = ActionLogEntry.ACTION_TYPE_SPEAKER_ELIGIBILITY_EDIT
    form_class = forms.SpeakerCategoryEligibilityForm
    template_name = 'edit_speaker_eligibility.html'

    def get_success_url(self):
        return reverse_tournament('participants-list', self.get_tournament())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.get_tournament()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Speaker category eligibility saved."))
        return super().form_valid(form)


# ==============================================================================
# Shift scheduling
# ==============================================================================

class PublicConfirmShiftView(SingleObjectByRandomisedUrlMixin, ModelFormSetView):
    # Django doesn't have a class-based view for formsets, so this implements
    # the form processing analogously to FormView, with less decomposition.
    # See also: motions.views.EditMotionsView.

    public_page_preference = 'allocation_confirmations'
    template_name = 'confirm_shifts.html'
    formset_factory_kwargs = dict(can_delete=False, extra=0, fields=['timing_confirmed'])
    model = Adjudicator
    allow_null_tournament = True
    formset_model = DebateAdjudicator

    def get_success_url(self):
        return reverse_tournament('participants-public-confirm-shift',
                self.get_tournament(), kwargs={'url_key': self.object.url_key})

    def get_formset_queryset(self):
        return self.object.debateadjudicator_set.all()

    def get_context_data(self, **kwargs):
        kwargs['adjudicator'] = self.get_object()
        return super().get_context_data(**kwargs)

    def formset_valid(self, formset):
        messages.success(self.request, _("Your shift check-ins have been saved"))
        return super().formset_valid(formset)

    def formset_invalid(self, formset):
        messages.error(self.request, _("Whoops! There was a problem with the form."))
        return super().formset_invalid(formset)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
