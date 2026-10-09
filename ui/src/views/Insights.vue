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
    <cv-row v-if="isConfigLoaded && !subscriptionConfigured">
      <cv-column>
        <NsInlineNotification
          kind="info"
          :title="$t('settings.subscription_required')"
          :description="$t('settings.subscription_required_description')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-else-if="isConfigLoaded && !enabled">
      <cv-column>
        <NsInlineNotification
          kind="info"
          :title="$t('insights.collector_disabled')"
          :description="$t('insights.collector_disabled_description')"
          :actionLabel="$t('insights.go_to_settings')"
          @action="goToAppPage(instanceName, 'settings')"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row v-if="!isConfigLoaded || subscriptionConfigured">
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
            :isLoading="loading.listFindings"
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
                  {{ (row.modules || []).join(", ") || "-" }}
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
      urlCheckInterval: null,
      isConfigLoaded: false,
      enabled: false,
      subscriptionConfigured: false,
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
    findingSearchText(finding) {
      return [
        this.$t("insights.severity_" + finding.severity),
        finding.title,
        finding.summary,
        finding.suggested_action,
        ...(finding.modules || []),
        ...(finding.node_refs || []).map((node) => node.fqdn),
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
      this.subscriptionConfigured = config.subscription_configured;
      this.isConfigLoaded = true;
      this.loading.getConfiguration = false;

      // findings stay readable after the collector is disabled
      if (this.subscriptionConfigured) {
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
        `${taskAction}-validation-failed-${eventId}`,
        this.listFindingsFailed
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
    listFindingsFailed(validationErrors) {
      this.findings = [];
      this.error.listFindings = this.$t(
        "insights." + validationErrors[0].error
      );
      this.loading.listFindings = false;
    },
    listFindingsCompleted(taskContext, taskResult) {
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
</style>
