<template>
  <div class="col-md-12 draw-container allocation-container">

    <allocation-actions :round-info="roundInfo"
                        :percentiles="percentileThresholds"></allocation-actions>

    <div class="row">
      <div class="vertical-spacing" id="messages-container"></div>
    </div>

    <div class="vertical-spacing">
      <draw-header :positions="roundInfo.positions">
        <div class="thead flex-cell flex-4" data-toggle="tooltip" title="Set the debate's priority (higher importances will be allocated better panels)." slot="himportance">
          <span>Priority</span>
        </div>
        <template slot="hvenue"><!-- Hide Venues --></template>
        <template slot="hpanel">
          <div :class="['thead flex-cell text-center vue-droppable-container',
                        'flex-' + (adjPositions.length > 2 ? 10 : adjPositions.length > 1 ? 8 : 12)]">
            <span>Chair</span>
          </div>
          <div v-if="adjPositions.indexOf('P') !== -1"
               :class="['thead flex-cell text-center vue-droppable-container',
                        'flex-' + (adjPositions.length > 2 ? 16: 16)]">
            <span >Panel</span>
          </div>
          <div v-if="adjPositions.indexOf('T') !== -1"
               :class="['thead flex-cell text-center vue-droppable-container',
                        'flex-' + (adjPositions.length > 2 ? 10: 16)]">
            <span >Trainees</span>
          </div>
        </template>
      </draw-header>
      <debate v-for="debate in debates" :debate="debate" :key="debate.id" :round-info="roundInfo"
              :histories="getDebateConflictables(debate, 'histories')"
              :conflicts="getDebateConflictables(debate, 'conflicts')">
        <div class="draw-cell flex-4" slot="simportance">
          <debate-importance :id="debate.id" :importance="debate.importance"></debate-importance>
        </div>
        <template slot="svenue"><!-- Hide Venues --></template>
        <template slot="spanel">
          <debate-panel :panel="debate.panel" :debate-id="debate.id"
                        :percentiles="percentileThresholds"
                        :locked="debate.locked"
                        :adj-positions="adjPositions"></debate-panel>
        </template>
      </debate>
    </div>

    <unallocated-items-container>
      <div v-for="unallocatedAdj in unallocatedAdjsByScore">
        <draggable-adjudicator :adjudicator="unallocatedAdj"
                               :percentiles="percentileThresholds"
                               :locked="unallocatedAdj.locked"></draggable-adjudicator>
      </div>
    </unallocated-items-container>

    <slide-over-item :subject="slideOverItem"></slide-over-item>

  </div>
</template>

<script>
import DrawContainerMixin from '../containers/DrawContainerMixin.vue'
import AdjudicatorMovingMixin from '../ajax/AdjudicatorMovingMixin.vue'
import HighlightableContainerMixin from '../allocations/HighlightableContainerMixin.vue'
import AllocationActions from '../allocations/AllocationActions.vue'
import DebateImportance from '../allocations/DebateImportance.vue'
import DebatePanel from '../allocations/DebatePanel.vue'
import ConflictsCoordinatorMixin from '../allocations/ConflictsCoordinatorMixin.vue'
import DraggableAdjudicator from '../draganddrops/DraggableAdjudicator.vue'

import percentile from 'stats-percentile'
import _ from 'lodash'

export default {
  mixins: [AdjudicatorMovingMixin, DrawContainerMixin,
           HighlightableContainerMixin, ConflictsCoordinatorMixin],
  components: { AllocationActions, DebateImportance, DebatePanel, DraggableAdjudicator },
  created: function() {
    this.$eventHub.$on('update-importance', this.updateImportance)
    // Watch for global conflict highlights
    this.$eventHub.$on('show-conflicts-for', this.setConflicts)
    this.$eventHub.$on('hide-conflicts-for', this.unsetConflicts)
  },
  computed: {
    unallocatedAdjsByScore: function() {
      return _.reverse(_.sortBy(this.unallocatedItems, ['score']))
    },
    allAdjudicatorsById: function() {
      return _.keyBy(this.adjudicators.concat(this.unallocatedItems), 'id')
    },
    percentileThresholds: function() {
      // For determining feedback rankings
      var allScores = _.map(this.allAdjudicatorsById, function(adj) {
        return parseFloat(adj.score)
      }).sort()
      var thresholds = []
      var letterGrades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]
      for (var i = 90; i > 10; i -= 10) {
        thresholds.push({
          'grade': letterGrades[0], 'cutoff': percentile(allScores, i), 'percentile': i
        })
        letterGrades.shift()
      }
      thresholds.push({'grade': "F", 'cutoff': 0, 'percentile': 10})
      return thresholds
    },
    adjPositions: function() {
      return this.roundInfo.adjudicatorPositions // Convenience
    }
  },
  methods: {
    getDebateConflictables(debate, type) {
      // Creates a per-debate subset of conflicts/histories for DebateConflictsMixin
      // to determine in-panel conflicts using ConflictsCoordinator
      var panellistIds = _.map(debate.panel, function(panellist) {
        return panellist.adjudicator.id
      })
      return _.pick(this[type], panellistIds)
    },
    moveToDebate(payload, assignedId, assignedPosition) {
      if (payload.debate === assignedId) {
        // Check that it isn't an in-panel move
        var thisDebate = this.debatesById[payload.debate]
        var fromPanellist = _.find(thisDebate.panel, function(panellist) {
          return panellist.adjudicator.id === payload.adjudicator;
        })
        if (assignedPosition === fromPanellist.position) {
          return // Moving to same debate/position; do nothing
        }
      }
      this.saveMove(payload.adjudicator, payload.debate, assignedId, assignedPosition)
    },
    moveToUnused(payload) {
      if (_.isUndefined(payload.debate)) {
        return // Moving to unused from unused; do nothing
      }
      this.saveMove(payload.adjudicator, payload.debate)
    },
    updateImportance: function(debateID, importance) {
      var debate = _.find(this.debates, { 'id': debateID })
      if (_.isUndefined(debate)) {
        this.ajaxError("Debate\'s importance", "", "Couldnt find debate to update")
      }
      var url = this.roundInfo.updateImportanceURL
      var message = 'debate ' + debate.id + '\'s importance'
      var payload = { debate_id: debate.id, importance: importance }
      this.ajaxSave(url, payload, message, function() {
        debate.importance = importance // Update model data
      })
    },
  }
}
</script>