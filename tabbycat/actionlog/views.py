from django.contrib.humanize.templatetags.humanize import naturaltime

from utils.mixins import JsonDataResponseView, LoginRequiredMixin
from tournaments.mixins import TournamentMixin


class LatestActionsView(LoginRequiredMixin, TournamentMixin, JsonDataResponseView):

    def get_data(self):
        actions = self.get_tournament().actionlogentry_set.prefetch_related(
                'content_object').order_by('-timestamp')[:15]

        action_objects = []
        for a in actions:
            action_objects.append({
                'user': a.user.username if a.user else a.ip_address or "anonymous",
                'type': a.get_type_display(),
                'param': a.get_content_object_display(),
                'timestamp': naturaltime(a.timestamp),
            })
        return action_objects
