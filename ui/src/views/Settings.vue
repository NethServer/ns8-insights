<!--
  Copyright (C) 2026 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("settings.title") }}</h2>
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
    <cv-row v-else-if="isConfigLoaded && activeElsewhere">
      <cv-column>
        <NsInlineNotification
          kind="warning"
          :title="$t('settings.active_elsewhere')"
          :description="
            $t('settings.active_elsewhere_description', {
              instance: activeElsewhere,
            })
          "
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-skeleton-text
            v-if="loading.getConfiguration"
            :paragraph="true"
            :line-count="5"
          ></cv-skeleton-text>
          <cv-form v-else @submit.prevent="configureModule">
            <p class="toggle-description">{{ $t("settings.description") }}</p>
            <NsToggle
              value="enabled"
              :label="$t('settings.collector')"
              v-model="enabled"
              :disabled="isFormDisabled || !!activeElsewhere"
              :invalid-message="error.enabled"
              ref="enabled"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <div v-if="enabled" class="last-run">
              <span class="label">{{ $t("settings.last_run") }}</span>
              <span v-if="lastRun">{{ formatLastRun(lastRun) }}</span>
              <span v-else>{{ $t("settings.never") }}</span>
            </div>
            <cv-accordion ref="accordion" class="maxwidth mg-bottom">
              <cv-accordion-item :open="toggleAccordion[0]">
                <template slot="title">{{ $t("settings.advanced") }}</template>
                <template slot="content">
                  <NsTextInput
                    :label="$t('settings.base_url')"
                    v-model.trim="baseUrl"
                    :helper-text="$t('settings.base_url_helper')"
                    :invalid-message="error.base_url"
                    :disabled="isFormDisabled"
                    ref="base_url"
                  />
                  <NsToggle
                    value="verifyTls"
                    :label="$t('settings.verify_tls')"
                    v-model="verifyTls"
                    :disabled="isFormDisabled"
                    ref="verify_tls"
                  >
                    <template slot="text-left">{{
                      $t("settings.disabled")
                    }}</template>
                    <template slot="text-right">{{
                      $t("settings.enabled")
                    }}</template>
                  </NsToggle>
                </template>
              </cv-accordion-item>
            </cv-accordion>
            <NsInlineNotification
              v-if="error.configureModule"
              kind="error"
              :title="$t('action.configure-module')"
              :description="error.configureModule"
              :showCloseButton="false"
            />
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="isFormDisabled"
              >{{ $t("settings.save") }}</NsButton
            >
          </cv-form>
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
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

const DEFAULT_SERVER_URL = "https://insights.nethesis.it";

export default {
  name: "Settings",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      isConfigLoaded: false,
      enabled: false,
      baseUrl: DEFAULT_SERVER_URL,
      verifyTls: true,
      subscriptionConfigured: false,
      activeElsewhere: "",
      lastRun: "",
      toggleAccordion: [false],
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        enabled: "",
        base_url: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    isFormDisabled() {
      // The insights server accepts data only from subscribed machines
      return (
        this.loading.getConfiguration ||
        this.loading.configureModule ||
        !this.subscriptionConfigured
      );
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
    formatLastRun(value) {
      const date = new Date(value);
      return isNaN(date) ? value : date.toLocaleString(this.$i18n.locale);
    },
    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const taskAction = "get-configuration";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getConfigurationAborted
      );

      // register to task completion
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
        return;
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
      this.baseUrl = config.base_url;
      this.verifyTls = config.verify_tls;
      this.subscriptionConfigured = config.subscription_configured;
      this.activeElsewhere = config.active_elsewhere;
      this.lastRun = config.last_run;
      // open the advanced section when it differs from the defaults
      this.toggleAccordion = [
        this.baseUrl !== DEFAULT_SERVER_URL || !this.verifyTls,
      ];
      this.isConfigLoaded = true;
      this.loading.getConfiguration = false;
    },
    validateConfigureModule() {
      this.clearErrors(this);

      if (!/^https?:\/\/\S+$/.test(this.baseUrl)) {
        this.error.base_url = this.$t("settings.invalid_url");
        this.toggleAccordion = [true];
        this.focusElement("base_url");
        return false;
      }
      return true;
    },
    configureModuleValidationFailed(validationErrors) {
      this.loading.configureModule = false;
      let focusAlreadySet = false;

      for (const validationError of validationErrors) {
        const param = validationError.parameter;

        if (validationError.error === "active_elsewhere") {
          this.error[param] = this.$t("settings.active_elsewhere_description", {
            instance: validationError.value,
          });
        } else {
          // set i18n error message
          this.error[param] = this.$t("settings." + validationError.error);
        }

        if (!focusAlreadySet) {
          this.focusElement(param);
          focusAlreadySet = true;
        }
      }
    },
    async configureModule() {
      if (!this.validateConfigureModule()) {
        return;
      }

      this.loading.configureModule = true;
      this.error.configureModule = "";
      const taskAction = "configure-module";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.configureModuleAborted
      );

      // register to task validation
      this.core.$root.$once(
        `${taskAction}-validation-failed-${eventId}`,
        this.configureModuleValidationFailed
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.configureModuleCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            enabled: this.enabled,
            base_url: this.baseUrl,
            verify_tls: this.verifyTls,
          },
          extra: {
            title: this.$t("settings.configure_instance", {
              instance: this.instanceName,
            }),
            description: this.$t("common.processing"),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.configureModule = this.getErrorMessage(err);
        this.loading.configureModule = false;
        return;
      }
    },
    configureModuleAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.configureModule = this.$t("error.generic_error");
      this.loading.configureModule = false;
    },
    configureModuleCompleted() {
      this.loading.configureModule = false;

      // reload configuration
      this.getConfiguration();
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";

.maxwidth {
  max-width: 38rem;
}

.toggle-description {
  margin-bottom: $spacing-06;
}

.last-run {
  margin-bottom: $spacing-07;
}

.label {
  font-weight: bold;
  margin-right: $spacing-03;
}
</style>
