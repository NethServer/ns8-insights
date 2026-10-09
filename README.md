# ns8-insights

NethServer 8 module that analyzes the cluster logs and reports the
problems found by the Nethesis insights service.

## Install

Instantiate the module with:

    add-module ghcr.io/nethserver/insights:latest 1

The output of the command will return the instance name.
Output example:

    {"module_id": "insights1", "image_name": "insights", "image_url": "ghcr.io/nethserver/insights:latest"}

## Uninstall

To uninstall the instance:

    remove-module --no-preserve insights1

## Running tests locally

This module uses the NS8 standard testing infrastructure. For instructions on how to run the test suite locally, refer to the [Running tests locally](https://github.com/NethServer/ns8-github-actions/blob/v1/README.md#running-tests-locally) section of the ns8-github-actions README.

## UI translation

Translated with [Weblate](https://hosted.weblate.org/projects/ns8/).

To setup the translation process:

- add [GitHub Weblate app](https://docs.weblate.org/en/latest/admin/code-hosting.html#code-hosting-github-notifications) to your repository
- add your repository to [hosted.weblate.org](https://hosted.weblate.org) or ask a NethServer developer to add it to ns8 Weblate project
