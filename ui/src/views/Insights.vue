<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("insights.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <p class="mg-bottom">{{ $t("insights.page_description") }}</p>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-configuration')"
          :description="error.getConfiguration"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="isConfigLoaded && !enabled">
      <cv-column>
        <cv-tile light>
          <NsEmptyState :title="$t('insights.collector_disabled')">
            <template #description>
              <div>{{ $t("insights.collector_disabled_description") }}</div>
              <NsButton
                kind="primary"
                :icon="Settings20"
                class="mg-top-lg"
                @click="goToAppPage(instanceName, 'settings')"
                >{{ $t("insights.go_to_settings") }}
              </NsButton>
            </template>
          </NsEmptyState>
        </cv-tile>
      </cv-column>
    </cv-row>
    <cv-row v-else-if="!error.getConfiguration">
      <cv-column>
        <cv-tile light>
          <div class="toolbar">
            <div class="search">
              <cv-search
                v-model="searchFilter"
                :placeholder="$t('insights.search')"
                :label="$t('insights.search')"
                :clear-aria-label="core.$t('common.clear_search')"
              ></cv-search>
            </div>
            <div class="status-filter">
              <cv-select
                v-model="statusFilter"
                :label="$t('insights.status_filter')"
                :disabled="loading.listFindings"
              >
                <cv-select-option
                  v-for="opt in statusOptions"
                  :key="opt"
                  :value="opt"
                  >{{ $t("insights.status_" + opt) }}</cv-select-option
                >
              </cv-select>
            </div>
            <NsButton
              kind="secondary"
              :icon="Restart20"
              :disabled="loading.listFindings"
              @click="listFindings"
              >{{ $t("insights.refresh") }}
            </NsButton>
          </div>
          <NsDataTable
            :allRows="filteredFindings"
            :columns="i18nTableColumns"
            :rawColumns="tableColumns"
            :sortable="true"
            :pageSizes="[10, 25, 50, 100]"
            :isSearchable="false"
            :noSearchResultsLabel="core.$t('common.no_search_results')"
            :noSearchResultsDescription="
              core.$t('common.no_search_results_description')
            "
            :isLoading="loading.getConfiguration || loading.listFindings"
            :skeletonRows="5"
            :isErrorShown="!!error.listFindings"
            :errorTitle="$t('action.list-findings')"
            :errorDescription="error.listFindings"
            :itemsPerPageLabel="core.$t('pagination.items_per_page')"
            :rangeOfTotalItemsLabel="core.$t('pagination.range_of_total_items')"
            :ofTotalPagesLabel="core.$t('pagination.of_total_pages')"
            :backwardText="core.$t('pagination.previous_page')"
            :forwardText="core.$t('pagination.next_page')"
            :pageNumberLabel="core.$t('pagination.page_number')"
            @updatePage="tablePage = $event"
          >
            <template slot="empty-state">
              <NsEmptyState
                v-if="searchFilter.trim()"
                :title="$t('insights.no_findings_filtered')"
              >
                <template #description>
                  <div>
                    {{ $t("insights.no_findings_filtered_description") }}
                  </div>
                </template>
              </NsEmptyState>
              <NsEmptyState v-else :title="$t('insights.no_findings')">
                <template #description>
                  <div>{{ $t("insights.no_findings_description") }}</div>
                </template>
              </NsEmptyState>
            </template>
            <template slot="data">
              <cv-data-table-row
                v-for="row in tablePage"
                :key="row.id"
                :value="row.id"
              >
                <cv-data-table-cell>
                  <NsTag
                    :kind="severityTagKind(row.severity)"
                    :label="$t('insights.severity_' + row.severity)"
                  />
                </cv-data-table-cell>
                <cv-data-table-cell class="title-cell">
                  <div class="finding-title">{{ row.title }}</div>
                  <NsTag
                    v-if="row.security"
                    kind="purple"
                    size="sm"
                    :label="$t('insights.security')"
                  />
                  <NsTag
                    v-if="row.status === 'stale'"
                    kind="gray"
                    size="sm"
                    :label="$t('insights.status_stale')"
                  />
                </cv-data-table-cell>
                <cv-data-table-cell class="text-cell">
                  {{ row.summary }}
                </cv-data-table-cell>
                <cv-data-table-cell class="text-cell">
                  {{ row.suggested_action }}
                  <div v-if="row.doc_ref">
                    <cv-link :href="row.doc_ref" target="_blank" rel="noopener">
                      {{ $t("insights.documentation") }}
                    </cv-link>
                  </div>
                </cv-data-table-cell>
                <cv-data-table-cell>
                  {{ formatModules(row) }}
                </cv-data-table-cell>
                <cv-data-table-cell>
                  {{ formatNodes(row) }}
                </cv-data-table-cell>
                <cv-data-table-cell>
                  <span :title="formatDateTime(row.last_seen)">
                    {{
                      formatDateDistance(row.last_seen, new Date(), {
                        addSuffix: true,
                      })
                    }}
                  </span>
                </cv-data-table-cell>
                <template slot="expandedContent">
                  <div class="finding-details">
                    <div class="details-grid">
                      <div>
                        <div class="details-label">
                          {{ $t("insights.first_seen") }}
                        </div>
                        <div>{{ formatDateTime(row.first_seen) }}</div>
                      </div>
                      <div>
                        <div class="details-label">
                          {{ $t("insights.last_seen") }}
                        </div>
                        <div>{{ formatDateTime(row.last_seen) }}</div>
                      </div>
                      <div v-if="row.reopened_at">
                        <div class="details-label">
                          {{ $t("insights.reopened_at") }}
                        </div>
                        <div>{{ formatDateTime(row.reopened_at) }}</div>
                      </div>
                      <div>
                        <div class="details-label">
                          {{ $t("insights.occurrence_count") }}
                        </div>
                        <div>{{ row.occurrence_count || 1 }}</div>
                      </div>
                    </div>
                    <div class="details-label">
                      {{ $t("insights.evidence") }}
                    </div>
                    <pre
                      v-if="row.evidence && row.evidence.length"
                      class="evidence"
                      >{{ row.evidence.join("\n") }}</pre
                    >
                    <div v-else>{{ $t("insights.no_evidence") }}</div>
                  </div>
                </template>
              </cv-data-table-row>
            </template>
          </NsDataTable>
        </cv-tile>
      </cv-column>
    </cv-row>
  </cv-grid>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  DateTimeService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";
import Restart20 from "@carbon/icons-vue/es/restart/20";
import Settings20 from "@carbon/icons-vue/es/settings/20";

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

export default {
  name: "Insights",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    DateTimeService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("insights.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "insights",
      },
      Restart20,
      Settings20,
      urlCheckInterval: null,
      isConfigLoaded: false,
      enabled: false,
      findings: [],
      searchFilter: "",
      statusFilter: "open",
      statusOptions: ["open", "stale", "all"],
      tablePage: [],
      tableColumns: [
        "severity",
        "title",
        "summary",
        "suggested_action",
        "modules",
        "nodes",
        "last_seen",
      ],
      loading: {
        getConfiguration: false,
        listFindings: false,
      },
      error: {
        getConfiguration: "",
        listFindings: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    i18nTableColumns() {
      return this.tableColumns.map((column) =>
        this.$t("insights.col_" + column)
      );
    },
    filteredFindings() {
      const q = this.searchFilter.trim().toLowerCase();
      if (!q) {
        return this.findings;
      }
      return this.findings.filter((finding) =>
        this.findingSearchText(finding).includes(q)
      );
    },
  },
  watch: {
    statusFilter() {
      this.listFindings();
    },
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
  },
  created() {
    this.getConfiguration();
  },
  methods: {
    formatDateTime(value) {
      return new Date(value).toLocaleString(this.$i18n.locale);
    },
    severityTagKind(severity) {
      switch (severity) {
        case "critical":
          return "red";
        case "high":
          return "magenta";
        case "medium":
          return "warm-gray";
        default:
          return "blue";
      }
    },
    formatModules(finding) {
      // an empty module name means the host itself, e.g. sshd
      const modules = (finding.modules || []).map(
        (module) => module || this.$t("insights.host")
      );
      return modules.join(", ") || "-";
    },
    nodeNames(finding) {
      if (finding.node_refs && finding.node_refs.length) {
        return finding.node_refs.map(
          (node) =>
            node.fqdn || this.$t("insights.node_n", { id: node.node_id })
        );
      }
      return (finding.nodes || []).map((id) =>
        this.$t("insights.node_n", { id })
      );
    },
    formatNodes(finding) {
      return this.nodeNames(finding).join(", ") || "-";
    },
    findingSearchText(finding) {
      return [
        this.$t("insights.severity_" + finding.severity),
        finding.title,
        finding.summary,
        finding.suggested_action,
        finding.security ? this.$t("insights.security") : "",
        this.formatModules(finding),
        ...this.nodeNames(finding),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
    },
    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const taskAction = "get-configuration";
      const eventId = this.getUuid();

      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getConfigurationAborted
      );
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getConfigurationCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.getConfiguration = this.getErrorMessage(err);
        this.loading.getConfiguration = false;
      }
    },
    getConfigurationAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getConfiguration = this.$t("error.generic_error");
      this.loading.getConfiguration = false;
    },
    getConfigurationCompleted(taskContext, taskResult) {
      const config = taskResult.output;
      this.enabled = config.enabled;
      this.isConfigLoaded = true;
      this.loading.getConfiguration = false;

      // findings stay readable after the collector is disabled
      if (this.enabled) {
        this.listFindings();
      }
    },
    async listFindings() {
      this.error.listFindings = "";
      this.loading.listFindings = true;
      const taskAction = "list-findings";
      const eventId = this.getUuid();

      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.listFindingsAborted
      );
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.listFindingsCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: { status: this.statusFilter },
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.listFindings = this.getErrorMessage(err);
        this.loading.listFindings = false;
      }
    },
    listFindingsAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.listFindings = this.$t("error.generic_error");
      this.loading.listFindings = false;
    },
    listFindingsCompleted(taskContext, taskResult) {
      if (taskResult.output.error) {
        this.findings = [];
        this.error.listFindings = this.$t(
          "insights." + taskResult.output.error
        );
        this.loading.listFindings = false;
        return;
      }
      // the server already sorts; keep the order stable on our side too
      this.findings = [...taskResult.output.findings].sort(
        (a, b) =>
          (SEVERITY_ORDER[a.severity] ?? 9) -
            (SEVERITY_ORDER[b.severity] ?? 9) || b.last_seen - a.last_seen
      );
      this.loading.listFindings = false;
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: $spacing-05;
  margin-bottom: $spacing-05;
}

.search {
  flex: 2;
  min-width: 14rem;
}

.status-filter {
  flex: 1;
  min-width: 10rem;
}

.finding-title {
  font-weight: bold;
}

.text-cell {
  max-width: 28rem;
  white-space: normal;
}

.finding-details {
  padding: $spacing-03 0 $spacing-05;
}

.details-grid {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-05 $spacing-07;
  margin-bottom: $spacing-05;
}

.details-label {
  font-weight: bold;
  margin-bottom: $spacing-02;
}

.evidence {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.75rem;
  white-space: pre;
  overflow-x: auto;
  max-width: 100%;
  padding: $spacing-03;
  background-color: rgba(128, 128, 128, 0.12);
}
</style>
