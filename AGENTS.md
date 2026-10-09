# Agent instructions

## What this module is

NS8 module that sends masked summaries of the cluster logs to the Nethesis
insights service and shows the findings it returns. It has no container and
no web route: the only process is `insights-collector`, a Python daemon run
on the host with the agent SDK (`runagent`).

- `imageroot/bin/insights-collector`: the whole collector, one stdlib-only
  file. It reads the cluster default Loki instance (`loki@cluster`, address
  and credentials from `module/<loki>/environment`), scrubs secrets, masks
  variable text, folds lines into templates and every 15 minutes sends a
  gzip JSON bundle to `POST <INSIGHTS_SERVER_URL>/logs/v1/bundles`, with
  HTTP Basic `system_id:auth_token` from the Redis hash
  `cluster/subscription`.
- `imageroot/pypkg/insights.py`: helpers shared by actions and events
  (subscription check, one-instance-per-cluster guard, service control).
- `imageroot/actions/`: `create-module` (defaults), `configure-module`
  (enable/disable, server URL, TLS check), `get-configuration`,
  `list-findings` (proxies `GET /logs/v1/findings` so the secret never
  reaches the browser), `restore-module`.
- `imageroot/events/`: `subscription-changed` disables the collector when
  the subscription ends; `default-instance-changed` resets the stream
  cursor when the default Loki instance changes.
- `ui/`: Vue 2 app with Status, Insights (findings table) and Settings pages.

The server lives in `nethesis/nethesis-insights` (Go); its API contract is
`docs/api/openapi.yaml` there.

## Rules that must hold

- The collector can be enabled only with a cluster subscription: the
  server accepts data only from subscribed machines. Without one, the
  Settings page shows an info banner and the form is disabled.
- Only one enabled instance per cluster: the collector reads the logs of
  the whole cluster. The image label `org.nethserver.max-per-node=1` limits
  instances per node; `configure-module` refuses to enable a second
  instance in the cluster (`find_active_elsewhere`).
- Module env keys: `INSIGHTS_ENABLED` (`0`/`1`), `INSIGHTS_SERVER_URL`,
  `INSIGHTS_VERIFY_TLS`. Server settings stay stored when disabled.
  Never store the subscription secret in the module environment.
- The daemon exits at once unless `INSIGHTS_ENABLED=1`.
- Keep `import agent` deferred inside functions in the collector, so the
  unit tests can load it without the NS8 SDK.
- When changing an action's input or output, update its
  `validate-input.json` / `validate-output.json` in the same commit.

## Build and test

- Collector unit tests: `pip install -r tests/unit/requirements.txt &&
  python -m pytest tests/unit`. Run them after any collector change.
- UI: `cd ui && yarn install && yarn lint && yarn build` (or in a
  `node:24` container, as `build-images.sh` does).
- Image: `./build-images.sh`. CI publishes
  `ghcr.io/nethserver/insights:<branch>` on every push.
- Integration: Robot Framework suites in `tests/`, run on a real NS8 node
  by the `Test module` workflow. `20__insights.robot` uses a local stub
  server (`tests/insights-stub.py`) and creates a temporary subscription
  if the test cluster has none.

## Conventions

- **Translations**: edit `ui/public/i18n/en/translation.json`; Italian
  (`it/`) is maintained here too. Other languages come from Weblate.
- **Branch names**: never use "/" in branch names. Use only chars allowed
  by container registry tags, like "-" and alphanumeric chars.
- **Commits**: conventional commit style. Short title line, 50 chars max.
  Briefly explain the rationale in one or two paragraphs, wrapped at
  column 72.
