# get-configuration output Schema

```txt
http://schema.nethserver.org/insights/get-configuration-output.json
```

Get the insights module configuration

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                     |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Allowed               | none                | [get-configuration-output.json](insights/get-configuration-output.json "open original schema") |

## get-configuration output Type

`object` ([get-configuration output](get-configuration-output.md))

## get-configuration output Examples

```json
{
  "enabled": true,
  "base_url": "https://insights.nethesis.it",
  "verify_tls": true,
  "log_level": "warning",
  "status": "active",
  "subscription_configured": true,
  "active_elsewhere": "",
  "last_run": "2026-10-09T12:15:42+00:00"
}
```

# get-configuration output Properties

| Property                                            | Type      | Required | Nullable       | Defined by                                                                                                                                                                                           |
| :-------------------------------------------------- | :-------- | :------- | :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [enabled](#enabled)                                 | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-enabled.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/enabled")                                 |
| [base_url](#base_url)                               | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-base_url.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/base_url")                               |
| [verify_tls](#verify_tls)                           | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-verify_tls.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/verify_tls")                           |
| [log_level](#log_level)                             | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-log_level.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/log_level")                             |
| [status](#status)                                   | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-status.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/status")                                   |
| [subscription_configured](#subscription_configured) | `boolean` | Required | cannot be null | [get-configuration output](get-configuration-output-properties-subscription_configured.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/subscription_configured") |
| [active_elsewhere](#active_elsewhere)               | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-active_elsewhere.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/active_elsewhere")               |
| [last_run](#last_run)                               | `string`  | Required | cannot be null | [get-configuration output](get-configuration-output-properties-last_run.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/last_run")                               |

## enabled



`enabled`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-enabled.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/enabled")

### enabled Type

`boolean`

## base_url



`base_url`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-base_url.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/base_url")

### base_url Type

`string`

## verify_tls



`verify_tls`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-verify_tls.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/verify_tls")

### verify_tls Type

`boolean`

## log_level

Lowest level of the collector messages written to the journal

`log_level`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-log_level.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/log_level")

### log_level Type

`string`

## status

State of the collector service

`status`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-status.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/status")

### status Type

`string`

### status Constraints

**enum**: the value of this property must be equal to one of the following values:

| Value        | Explanation |
| :----------- | :---------- |
| `"active"`   |             |
| `"failed"`   |             |
| `"inactive"` |             |

## subscription_configured

The cluster has a subscription: required to enable the collector

`subscription_configured`

* is required

* Type: `boolean`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-subscription_configured.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/subscription_configured")

### subscription_configured Type

`boolean`

## active_elsewhere

Id of another insights instance with the collector enabled, empty if none

`active_elsewhere`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-active_elsewhere.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/active_elsewhere")

### active_elsewhere Type

`string`

## last_run

Timestamp of the last bundle accepted by the server, empty if none

`last_run`

* is required

* Type: `string`

* cannot be null

* defined in: [get-configuration output](get-configuration-output-properties-last_run.md "http://schema.nethserver.org/insights/get-configuration-output.json#/properties/last_run")

### last_run Type

`string`
